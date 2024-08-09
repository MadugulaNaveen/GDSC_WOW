import os
import time
import tempfile
import re
import google.generativeai as genai
from google.cloud import storage
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.fx import fadein, fadeout
from django.conf import settings
import google
# Configure Gemini API key
genai.configure(api_key=os.getenv("GEMINIAPIKEY"))

# Google Cloud Storage bucket name
GCS_BUCKET_NAME = 'highlightgenerator'

# Google Cloud Storage configuration
def upload_to_gcs(file_path, gcs_path):
    client = storage.Client.from_service_account_json(settings.GCS_CREDENTIALS)
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(file_path)
    blob.make_public()  # Make the file public so that it can be accessed via URL
    return blob.public_url

def download_from_gcs(video_path, local_path):
    client = storage.Client.from_service_account_json(os.getenv("GCS_CREDENTIALS"))
    bucket_name = "highlightgenerator"  # Your GCS bucket name
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(video_path)
    
    if not blob.exists():
        print(f"Error: The object {video_path} does not exist in bucket {bucket_name}.")
        return None
    
    try:
        blob.download_to_filename(local_path)
        print(f"Downloaded {video_path} to {local_path}")
    except google.api_core.exceptions.NotFound as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(10)
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    print()

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Extract time frames from text
def extract_time_frames(text):
    time_ranges = re.findall(r'(\d+:\d+)\s*-\s*(\d+:\d+)', text)
    time_frames = []
    for start, end in time_ranges:
        start_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(start.split(":"))))
        end_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(end.split(":"))))
        time_frames.append((start_seconds, end_seconds))
    return time_frames

# Create clips with transitions
def create_clippings_with_transitions(video_path, time_frames, output_folder, transition_duration=1):
    os.makedirs(output_folder, exist_ok=True)
    
    for i, (start_time, end_time) in enumerate(time_frames):
        output_path = os.path.join(output_folder, f"clip_{i+1}.mp4")
        subclip = VideoFileClip(video_path).subclip(start_time, end_time)

        if i > 0:
            transition_duration = min(transition_duration, subclip.duration / 2)
            subclip = fadein.fadein(subclip, duration=transition_duration)
        if i < len(time_frames) - 1:
            transition_duration = min(transition_duration, subclip.duration / 2)
            subclip = fadeout.fadeout(subclip, duration=transition_duration)

        try:
            subclip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
            print(f"Clip {i+1} created: {output_path}")
        except Exception as e:
            print(f"Error creating clip {i+1}: {e}")

# Merge all clips to get the final video
def merge_videos_from_folder(folder_path, output_path):
    video_files = [f for f in os.listdir(folder_path) if f.endswith(('mp4', 'avi', 'mov', 'mkv'))]
    video_files.sort()

    video_clips = []
    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        try:
            clip = VideoFileClip(video_path)
            video_clips.append(clip)
        except Exception as e:
            print(f"Error loading {video_path}: {e}")

    if not video_clips:
        print("No valid video files found in the specified folder.")
        return

    try:
        final_clip = concatenate_videoclips(video_clips, method="compose")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.mp4", remove_temp=False)
    except Exception as e:
        print(f"Error during concatenation or writing the video file: {e}")

def getHighlightedVideo(video_path, output_folder, output_video):
    # Create temporary directories and paths
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_video_path = os.path.join(temp_dir, os.path.basename(video_path))

        # Download video from GCS
        download_from_gcs(video_path, temp_video_path)

        # Upload the video to Gemini
        gemini_file = upload_to_gemini(temp_video_path, mime_type="video/mp4")

        # Wait for the file to be processed
        wait_for_files_active([gemini_file])

        # Start a chat session with Gemini
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        gemini_file,
                    ],
                },
            ]
        )

        # Send the message and get the response
        response = chat_session.send_message(
            "Extract the most important highlights from the video and provide the start and end time frames of each important highlight. The total time of the highlights must be less than 20 seconds. Provide the output in the form of a list."
        )

        # Extract the time frames from the response
        text = response.text
        time_frames = extract_time_frames(text)

        # Create clips based on the time frames
        create_clippings_with_transitions(temp_video_path, time_frames, temp_dir)

        # Merge all the clips to create the final video
        final_video_path = os.path.join(temp_dir, "final_highlight_video.mp4")
        merge_videos_from_folder(temp_dir, final_video_path)

        # Upload the final video to GCS
        final_video_url = upload_to_gcs(final_video_path, output_video)

        return final_video_url

# Example usage
video_gcs_path = "path/to/input/video.mp4"
output_gcs_path = "path/to/output/final_highlight_video.mp4"
output_folder = "output_folder"

highlight_video_url = getHighlightedVideo(video_gcs_path, output_folder, output_gcs_path)
print(f"Highlighted video available at: {highlight_video_url}")
