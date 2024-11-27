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



class DefaultResponse(typing_extensions.TypedDict):
    response: str

def google_single_image_request(text, base64_image=False, model=False, temperature=False, id=get_random_id(), response_format=None):
    genai.configure(api_key=data["key"],transport="rest")

    if not model:
        model = "gemini-1.5-flash"
    if not temperature:
        temperature = 0.05
    
    task_list = []

    if base64_image:
        if base64_image.startswith('data:image'):
            base64_image = base64_image.split(',')[1]    

        # 2. Decode (Now with clean base64 data)
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        # Save to a BytesIO buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG") 
        img_buffer.seek(0)  # Reset the buffer to the beginning


        
        image_file = genai.upload_file(img_buffer, mime_type="image/png")    
        task_list.append(image_file)
        task_list.append('\n\n')

    task_list.append(text)
    task_list.append('\n\n')
    task_list.append('return in the format of the correct schema')

    google_model = genai.GenerativeModel(model)
    # print('Starting gemini request...')
    try:
        result = google_model.generate_content(
            task_list, 
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema= response_format,
                temperature=temperature,
            )
            
        )
    except Exception as e:
        print(f"GPT request... (google, {model}) ERROR", str(e))
        raise Exception(str(e))

    # print('Starting gemini request... Done')

    
    if base64_image:
    
        image_file.delete()
    
    return result
    print(f"{result.text=}")
