import os

def process_image(image_path):
    # Placeholder function to process image input
    print(f"Processing image: {image_path}")
    # Add your image processing code here
    return "Image processed successfully."

def process_text(text):
    # Placeholder function to process text input
    print(f"Processing text: {text}")
    # Add your text processing code here
    return "Text processed successfully."

def process_speech(speech_path):
    # Placeholder function to process speech input
    print(f"Processing speech: {speech_path}")
    # Add your speech processing code here
    return "Speech processed successfully."

def detect_input_type(input_data):
    # Check if input_data is a file path and determine the file extension
    if os.path.isfile(input_data):
        file_extension = os.path.splitext(input_data)[1].lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
            return 'image'
        elif file_extension in ['.txt']:
            return 'text'
        elif file_extension in ['.wav', '.mp3', '.flac']:
            return 'speech'
        else:
            return 'unknown'
    else:
        # If it's not a file path, assume it's a text input directly
        return 'text'

def handle_input(input_data):
    input_type = detect_input_type(input_data)
    if input_type == 'image':
        return process_image(input_data)
    elif input_type == 'text':
        return process_text(input_data)
    elif input_type == 'speech':
        return process_speech(input_data)
    else:
        return "Invalid input type."

# Example usage:
input_data_image = "path/to/image.jpg"
input_data_text = "This is a sample text."  # Direct text input
input_data_speech = "path/to/speech.wav"

# Process the inputs
print(handle_input(input_data_image))
print(handle_input(input_data_text))  # Assuming you can handle direct text input differently if needed
print(handle_input(input_data_speech))
