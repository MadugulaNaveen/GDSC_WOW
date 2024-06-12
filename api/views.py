from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
import os
from .utilities import getHighlightedVideo

def index(request):
    return render(request, "index.html", {"show": "hidden", "hide": "show"})

def getHighlights(request):
    print(request.FILES)
    if request.method == "POST" and "inputVideo" in request.FILES:
        input_video = request.FILES["inputVideo"]
        print('in the highlights')
        # Save the uploaded video to a temporary location
        temp_video_path = os.path.join(settings.MEDIA_ROOT, "temp", input_video.name)
        with open(temp_video_path, "wb+") as destination:
            for chunk in input_video.chunks():
                destination.write(chunk)
        # Define the output folder
        output_folder = os.path.join(settings.MEDIA_ROOT, "output")
        output_video = os.path.join(settings.MEDIA_ROOT, 'highlightsVideo.mp4')
        # Call the function to process the video
        getHighlightedVideo(temp_video_path, output_folder, output_video)
        # Render the response with the processed video
        return render(request, "index.html", {"show": "show", "hide": "hidden", "processed_video_path": output_video})
    else:
        return render(request, "index.html", {"show": "hidden", "hide": "show"})
