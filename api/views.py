import os
from google.cloud import storage
from django.conf import settings
from django.shortcuts import render
import logging
from .utilities import getHighlightedVideo
import tempfile

logger = logging.getLogger(__name__)

def index(request):
    return render(request, "index.html", {"show": "hidden", "hide": "show"})

def upload_to_gcs(file_path, gcs_path):
    client = storage.Client.from_service_account_json(settings.GCS_CREDENTIALS)
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(file_path)
    blob.make_public()  # Make the file public so that it can be accessed via URL
    return blob.public_url

def getHighlights(request):
    if request.method == "POST" and "inputVideo" in request.FILES:
        input_video = request.FILES["inputVideo"]
        temp_video_path = None
        
        try:
            # Save the uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_video_path = temp_file.name
                for chunk in input_video.chunks():
                    temp_file.write(chunk)

            # Upload the temporary video to GCS
            temp_video_url = upload_to_gcs(temp_video_path, f"videos/temp/{input_video.name}")
            
            # Define output video path in GCS
            output_video_path = f"videos/highlights/{input_video.name}"
            output_video_temp_path = os.path.join(tempfile.gettempdir(), 'highlightsVideo.mp4')
            
            # Process the video
            output_video_url = getHighlightedVideo(temp_video_path, tempfile.gettempdir(), output_video_temp_path)
        
        except Exception as e:
            logger.error(f"Error in getHighlights: {e}")
            return render(request, "index.html", {"show": "hidden", "hide": "show", "error": str(e)})
        
        finally:
            # Cleanup temporary files
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if output_video_temp_path and os.path.exists(output_video_temp_path):
                os.remove(output_video_temp_path)
        
        return render(request, "index.html", {
            "show": "show",
            "hide": "hidden",
            "processed_video_path": output_video_url,
            "original_video_path": temp_video_url
        })
    else:
        return render(request, "index.html", {
            "show": "hidden",
            "hide": "show"
        })

# Google Cloud Storage bucket name
GCS_BUCKET_NAME = 'highlightgenerator'
