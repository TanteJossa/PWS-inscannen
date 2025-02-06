import google.generativeai as genai
import os
import json
import base64 
from PIL import Image
import io
from pydantic import BaseModel
import typing_extensions 
import re 
from helpers import get_random_id, json_from_string, typed_dict_to_string
import typing
import requests

with open('creds/google_gemini.json', 'r') as f:
    data = json.load(f)
API_KEY = data["key"]


def typed_dict_to_schema(typed_dict_type: type) -> dict:
    """Converts a typing.TypedDict to a JSON Schema-like representation."""

    annotations = typing.get_type_hints(typed_dict_type)
    schema = {"type": "OBJECT", "properties": {}}

    for key, value_type in annotations.items():
        if hasattr(value_type, '__origin__') and value_type.__origin__ == list:  # Handle lists
            item_type = value_type.__args__[0]
            if hasattr(item_type, '__annotations__') : # it's a TypedDict
               schema["properties"][key] = {
                    "type": "ARRAY",
                    "items": typed_dict_to_schema(item_type)
               }
            else:
              schema["properties"][key] = {
                   "type": "ARRAY",
                  "items": {"type": get_type_name(item_type)}
                }

        elif hasattr(value_type, '__annotations__'):
            schema["properties"][key] = typed_dict_to_schema(value_type)
        else:
            schema["properties"][key] = {"type": get_type_name(value_type)}
    return schema

def get_type_name(type_hint) -> str:
     if type_hint == str:
         return "STRING"
     elif type_hint == int:
         return "INTEGER"
     elif type_hint == float:
         return "NUMBER"
     elif type_hint == bool:
         return "BOOLEAN"
     # Add more type mappings as needed
     else:
         return "UNKNOWN"  # Or raise an error for unhandled types

class DefaultGeminiSchema(typing.TypedDict):
    result: str

class DefaultGeminiSchemaPdantic(BaseModel):
    result: str

def typed_dict_to_string_alternative(data) -> str:
    """Converts any TypedDict to a formatted string.  More robust.

    Handles any TypedDict (not just Person), including those with different
    keys and types, and adds error handling in case of unexpected input.

    Args:
      data:  The TypedDict to convert.  Crucially, it uses a general
        TypedDict type hint, not a specific one like Person.

    Returns:
      A formatted string representation of the TypedDict.
    """
    try:
        # Iterate through the key-value pairs and format them.
        parts = [f"{key}: {value}" for key, value in data.items()]
        return ", ".join(parts)
    except AttributeError as e:
        return f"Error: Input is not a dictionary-like object: {e}"
    except Exception as e: #catch other potential errors.
        return f"An unexpected error occurred: {e}"

import inspect
def google_single_image_request(text, base64_image=False, model=False, temperature=False, id=get_random_id(), response_format=False, task_list=False, limit_output= True):
    genai.configure(api_key=data["key"],transport="rest")

    if not response_format:
        response_format = DefaultGeminiSchema
        
    if not model:
        model = "gemini-1.5-pro"
        # model = "gemini-2.0-flash-exp"
    if not temperature:
        temperature = 0.05

    if not task_list:
        task_list = []

        if base64_image:
            if base64_image.startswith('data:image'):
                base64_image = base64_image.split(',')[1]    

            # # 2. Decode (Now with clean base64 data)
            # image_data = base64.b64decode(base64_image)
            # image = Image.open(io.BytesIO(image_data))
            
            # # Save to a BytesIO buffer
            # img_buffer = io.BytesIO()
            # image.save(img_buffer, format="PNG") 
            # img_buffer.seek(0)  # Reset the buffer to the beginning


            
            # image_file = genai.upload_file(img_buffer, mime_type="image/png")    
            task_list.append({
                "inline_data": {
                    "mime_type":"image/png",
                    "data": base64_image
                }
            })
            task_list.append({"text": "\n\n"})

        task_list.append({"text": text})
        task_list.append({"text": "\n\n"})
        task_list.append({"text": 'return in the format of the correct schema'})

        # google_model = genai.GenerativeModel(model)
        # print('Starting gemini request...')
    
        # Generate schema dictionary
        # schema_dict = response_format.model_json_schema()

        # Convert to JSON string
        
        if (isinstance(response_format, BaseModel)):
            type_text = response_format.model_json_schema()
        elif(inspect.isclass(response_format)):
            type_text = typed_dict_to_string(response_format)
        else:
            type_text = ""

        # json_schema_str = json.dumps(response_format, indent=2)
        task_list.append(
            {
                "text": "Het JSON schema is je mag maar 1 json object genereren en je mag de keys absoluut niet veranderen: \n"+type_text
            }
        )    
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "parts":task_list
                }
            ],
            "generationConfig": {
                # "response_mime_type": "application/json",
                "temperature": temperature,
                # "topP": 0.95,
                # "response_schema": typed_dict_to_schema(response_format),
                
            }
        }   
        if limit_output:
            payload["generationConfig"]["max_output_tokens"] = 1000
        
        result = requests.post(url, headers=headers, data=json.dumps(payload))
        
        result = result.json()
        if (isinstance(result,dict) ):
            parts = result.get("candidates",[{}])[0].get("content",{}).get("parts",[])
            if (len(parts) > 0):
                part = parts[0]
                result = json_from_string(part.get("text", ""))
        
        
        
        # result = google_model.generate_content(
        #     task_list, 
        #     generation_config=genai.GenerationConfig(
        #         response_mime_type="application/json",
        #         response_schema= response_format,
        #         temperature=temperature,
        #     )
            
        # )
    except Exception as e:
        print(f"GPT request... (google, {model}) ERROR", str(e))
        raise Exception('Error in google_single_image_request: '+str(e))

    # print('Starting gemini request... Done')

    
    # if base64_image:
    
    #     image_file.delete()
    
    return result
    print(f"{result.text=}")
