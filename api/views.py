from google.cloud import storage
from django.conf import settings
from django.shortcuts import render
import logging
from .utilities import getHighlightedVideo
import os

logger = logging.getLogger(__name__)

def upload_to_gcs(file, gcs_path):
    client = storage.Client.from_service_account_json(settings.GS_CREDENTIALS)
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_file(file)
    blob.make_public()  # Make the file public so that it can be accessed via URL
    return blob.public_url

def getHighlights(request):
    if request.method == "POST" and "inputVideo" in request.FILES:
        input_video = request.FILES["inputVideo"]

        # Upload the temporary video to GCS
        try:
            temp_video_url = upload_to_gcs(input_video, f"videos/temp/{input_video.name}")
        except Exception as e:
            logger.error(f"Error uploading temp video to GCS: {e}")
            return render(request, "index.html", {"show": "hidden", "hide": "show", "error": f"Error uploading temp video: {e}"})

        output_video_path = f"videos/highlights/{input_video.name}"
        
        try:
            temp_video_path = os.path.join("/tmp", input_video.name)
            with open(temp_video_path, "wb+") as destination:
                for chunk in input_video.chunks():
                    destination.write(chunk)
            
            # Define output video path
            output_video = os.path.join("/tmp", 'highlightsVideo.mp4')
            
            # Process the video
            getHighlightedVideo(temp_video_path, "/tmp", output_video)
            
            # Upload the processed video to GCS
            output_video_url = upload_to_gcs(open(output_video, "rb"), output_video_path)
        except Exception as e:
            logger.error(f"Error in getHighlights: {e}")
            return render(request, "index.html", {"show": "hidden", "hide": "show", "error": str(e)})
        
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
