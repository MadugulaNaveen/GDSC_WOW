from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def create_clippings(video_path, time_frames, output_folder):

    for i, (start_time, end_time) in enumerate(time_frames):
        output_path = f"{output_folder}/clip_{i+1}.mp4"
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=output_path)
        print(f"Clip {i+1} created: {output_path}")

# Example usage
video_path = "D:\GDSC_WOW\vid.mp4"
time_frames = [(0,1),(2,5),(6,7)]  # List of (start_time, end_time) in seconds
output_folder = "D:\GDSC_WOW\output"

create_clippings(video_path, time_frames, output_folder)