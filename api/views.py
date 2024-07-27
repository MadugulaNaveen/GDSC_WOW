from google.cloud import storage
import os
import mimetypes
from django.conf import settings
from django.shortcuts import render
from moviepy.editor import VideoFileClip
import logging
from .utilities import getHighlightedVideo

logger = logging.getLogger(__name__)

def upload_to_gcs(file_path, filename):
    client = storage.Client()
    bucket = client.bucket('GCS_BUCKET_NAME')
    content_type, _ = mimetypes.guess_type(file_path)
    blob = bucket.blob(filename)
    with open(file_path, 'rb') as file:
        blob.upload_from_file(file, content_type=content_type)
    return blob.public_url

def getHighlights(request):
    if request.method == "POST" and "inputVideo" in request.FILES:
        input_video = request.FILES["inputVideo"]
        temp_video_path = os.path.join(settings.MEDIA_ROOT, "temp", input_video.name)
        os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)
        with open(temp_video_path, "wb+") as destination:
            for chunk in input_video.chunks():
                destination.write(chunk)
        
        output_folder = os.path.join(settings.MEDIA_ROOT, "output")
        os.makedirs(output_folder, exist_ok=True)
        output_video = os.path.join(output_folder, 'highlightsVideo.mp4')
        
        try:
            getHighlightedVideo(temp_video_path, output_folder, output_video)
            input_video_url = upload_to_gcs(temp_video_path, f"videos/{input_video.name}")
            output_video_url = upload_to_gcs(output_video, "videos/highlightsVideo.mp4")
        except Exception as e:
            logger.error(f"Error in getHighlights: {e}")
            return render(request, "index.html", {"show": "hidden", "hide": "show", "error": str(e)})
        
        return render(request, "index.html", {
            "show": "show",
            "hide": "hidden",
            "processed_video_path": output_video_url,
            "original_video_path": input_video_url
        })
    else:
        return render(request, "index.html", {
            "show": "hidden",
            "hide": "show"
        })

GCS_BUCKET_NAME = 'highlightgenerator'
