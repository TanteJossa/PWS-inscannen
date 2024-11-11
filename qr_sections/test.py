import os
from google.cloud import vision

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./creds/toetspws-bacode.json"  # Your credentials path

def detect_micro_qr(image_path):
    try:
        client = vision.ImageAnnotatorClient()

        with open(image_path, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)

        # Use DOCUMENT_TEXT_DETECTION
        response = client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Error during detection: {response.error.message}")


        full_text = response.full_text_annotation.text  # Get the full detected text

        # Look for QR code data in the detected text (often embedded)
        #  You might need to adjust this logic depending on how the QR code 
        # data is represented in the image
        # Example: if the QR data is on its own line or has specific prefixes/suffixes

        # Simplest approach: print all detected text:
        print("Detected Text:\n", full_text)

        # More refined approach (if your QR codes have a specific format)
        # Example: Assuming QR data starts with "QR:"
        qr_data_lines = [line for line in full_text.splitlines() if line.startswith("QR:")]
        for line in qr_data_lines:
            print("Potential QR Data:", line[3:]) # Extract data after "QR:"


    except Exception as e:
        print(f"An error occurred: {e}")

detect_micro_qr('output.png')