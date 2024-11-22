import google.generativeai as genai
import os
import json
import base64 
from PIL import Image
import io
import typing_extensions 
import re 
from helpers import get_random_id

with open('creds/google_gemini.json', 'r') as f:
    data = json.load(f)


genai.configure(api_key=data["key"])

class DefaultResponse(typing_extensions.TypedDict):
    response: str

def google_single_image_request(tekst, base64_image, model="gemini-1.5-flash", id=get_random_id(), response_format=None):
    # 1. Remove the Data URI Prefix
    base64_image = base64_image.split(",")[1]  # Get the part after the comma

    # 2. Decode (Now with clean base64 data)
    image_data = base64.b64decode(base64_image)
    image = Image.open(io.BytesIO(image_data))
    
    # Save to a BytesIO buffer
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG") 
    img_buffer.seek(0)  # Reset the buffer to the beginning


    
    image_file = genai.upload_file(img_buffer, mime_type="image/png")    

    model = genai.GenerativeModel(model)
    print('Starting gemini request...')
    result = model.generate_content(
        [image_file, "\n\n", tekst], 
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema= response_format
        )
        
    )
    print('Starting gemini request... Done')

    
    
    image_file.delete()
    
    return result
    print(f"{result.text=}")
