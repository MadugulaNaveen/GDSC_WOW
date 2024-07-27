import os
import time

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINIAPIKEY"))

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
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
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
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
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

# TODO Make these files available on the local file system
# You may need to update the file paths





import re
# EXTRACTS THE TIMEFRAMES INTO LIST OF TIMEFRAMES
def extract_time_frames(text):
    # Regular expression to find all time ranges
    time_ranges = re.findall(r'(\d+:\d+)\s*-\s*(\d+:\d+)', text)

    # Convert the time ranges into a list of tuples
    time_frames = []
    for start, end in time_ranges:
        start_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(start.split(":"))))
        end_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(end.split(":"))))
        time_frames.append((start_seconds, end_seconds))
    
    return time_frames

from moviepy.video.fx import fadein, fadeout
from moviepy.editor import VideoFileClip

# CREATES CLIPS BASED ON THE TIMEFRAMES
def create_clippings_with_transitions(video_path, time_frames, output_folder, transition_duration=1):
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    for i, (start_time, end_time) in enumerate(time_frames):
        output_path = os.path.join(output_folder, f"clip_{i+1}.mp4")
        subclip = VideoFileClip(video_path).subclip(start_time, end_time)

        # Apply fade in and fade out effects for smooth transition
        if i > 0:
            transition_duration = min(transition_duration, subclip.duration / 2)
            subclip = fadein.fadein(subclip, duration=transition_duration)
        if i < len(time_frames) - 1:
            transition_duration = min(transition_duration, subclip.duration / 2)
            subclip = fadeout.fadeout(subclip, duration=transition_duration)

        subclip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
        print(f"Clip {i+1} created: {output_path}")
        
        
        
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
import imageio_ffmpeg as ffmpeg

#MERGES ALL THE CLIPS TO GET THE FINAL VIDEO 
def merge_videos_from_folder(folder_path, output_path):
    # Ensure that imageio-ffmpeg is used
    os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg.get_ffmpeg_exe()

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

        
        
def getHighlightedVideo(videoPath,outputFolder,outputVideo):
    files = [upload_to_gemini(videoPath, mime_type="video/mp4"),]
    
    # Some files have a processing delay. Wait for them to be ready.
    wait_for_files_active(files)

    chat_session = model.start_chat(
    history=[
        {
        "role": "user",
        "parts": [
            files[0],
        ],
        },
    ]
    )

    response = chat_session.send_message("Extract the most important highlights from the video and provide the of start and end time frames of each important highlight and provide only the most important timeframes and not their description and the total time of the highlights must be less than 20-20 seconds.Provide the output in the form of list")

    # The new text with time frames
    text = response.text

    # Extract the time frames from the text
    time_frames = extract_time_frames(text)
    
    video_path = videoPath
    time_frames = time_frames  # Assuming you have extracted time_frames earlier
    clips_folder = outputFolder
    transition_duration = 1  # Duration of transition effects in seconds

    create_clippings_with_transitions(video_path, time_frames, clips_folder, transition_duration)
    
    folder_path = clips_folder # Replace with the path to your folder containing video files
    output_path = outputVideo  # Replace with the desired output file path

    merge_videos_from_folder(folder_path, output_path)