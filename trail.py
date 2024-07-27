from google.cloud import storage
import os
import mimetypes

def upload_video_to_gcs(file_path, filename):
    # Initialize the Google Cloud Storage client
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    
    # Determine the content type
    content_type, _ = mimetypes.guess_type(file_path)

    # Create a blob (object) and upload the file
    blob = bucket.blob(filename)
    with open(file_path, 'rb') as file:
        blob.upload_from_file(file, content_type=content_type)

    # Return the public URL of the uploaded file
    return blob.public_url

GCS_BUCKET_NAME = 'highlightgenerator'

if __name__ == "__main__":
    # Provide the path to your file and the desired filename in GCS
    file_path = "README.md"
    filename = "MDFile"
    print(upload_video_to_gcs(file_path, filename))
