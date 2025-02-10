from google.generativeai.types import GenerateContentResponse

from open_ai_wrapper import (
    openai_single_request
)
from gemini_wrapper import (
    google_single_request
)

import json
import time
from helpers import (
    OpenAi_module_models
)

def get_openai_messages(input_data):
    messages = []
    for item in input_data:
        if item["type"] == "text":
            messages.append({
                "role": "user", 
                "content": item["text"]
            })
        if item["type"] == "image":
            base64_image = item["image"]
            if not base64_image.startswith('data:image'):
                base64_image = "data:image/png;base64," + base64_image    
                
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"{base64_image}"
                        }
                    }
                ]
            })
            
    return messages

def get_google_messages(input_data):
    messages = []
    for item in input_data:
        if item["type"] == "text":
            messages.append({
                "text": item["text"]
            })
        if item["type"] == "image" and "image" in item:
            base64_image = item["image"]
            if base64_image.startswith('data:image'):
                base64_image = base64_image.split(',')[1]    

            messages.append({
                "inline_data": {
                    "mime_type":"image/png",
                    "data": base64_image
                }
            })
            messages.append({"text": "\n\n"})
            
    return messages

def single_request(
        input_data=False,
        provider=False,
        model=False,
        schema_string=False,
        temperature=False,
        limit_output=False
    ):
    if not input_data:
        input_data = [{
            "type": "text",
            "text":"eindig dit gesprek zo snel mogelijk."               
        }]
    if not provider:
        provider = "google"
    if not model:
        model = "gemini-2.0-flash"
    if not temperature:
        temperature = 0.1
                
    if schema_string:
        input_data.append({
            "type": "text",
            "text": f"Geef alleen een json object als response met de volgende structuur:\n {schema_string}"
        })




    print(f"GPT request ({provider}, {model}) ... ")

    if provider in OpenAi_module_models.keys():

        messages = get_openai_messages(input_data)            
        try:
            result = openai_single_request(messages=messages, model=model, provider=provider, temperature=temperature)
        except:
            result = {"result_data": {"error": "something went wrong, maybe a timeout"}}
        result_data = result["result_data"]
        request_data = result["request_data"]
        response = {
            "result": result_data,
            "tokens_used": request_data["total_tokens"],

            "model_used": result["model_used"],
            "model_version": result["model_version"],
            
            "timestamp":  result["timestamp"],
            "delta_time_s":  result["delta_time_s"],
        }

    elif provider == 'google':
        
        start_time = time.time()
        try:
            result:GenerateContentResponse = google_single_request(
                task_list=get_google_messages(input_data),
                model=model,
                limit_output=limit_output,
                temperature=temperature
            )
            
            print(result)
            if ('candidates' in result):
                try:
                    result_data = json.loads(result['candidates'][0]['content']['parts'][0]['text'])
                except:
                    invalid_json = result['candidates'][0]['content']['parts'][0]['text']
                    try:
                        print('Trying to repair json: ',invalid_json)
                        valid_json = invalid_json+"}"
                        result_data = json.loads(valid_json)
                    except:
                        print('Single Request Error: ',invalid_json)
                        result_data = {}
            else:
                if result:
                    result_data = result
                else:
                    result_data = {}
                    
            if ("usageMetadata" in result and "totalTokenCount" in result["usageMetadata"]):
                token_count = int(result["usageMetadata"]["totalTokenCount"])
            else:
                token_count = 0
        except:
            result_data = {}
            token_count = 0



        
        end_time = time.time()
        # print(result, result.usage_metadata.total_token_count)
        response = {
            "result": result_data,
            # "spelling_corrections": result_data["spelling_corrections"],
            
            "tokens_used": token_count,

            "model_used": model,
            "model_version": model,
            "provider": provider,
            
            "timestamp":  end_time,
            "delta_time_s":  (end_time - start_time),
        }
    else: 
        response = {"error": "[provider not found]"}

    print(f"GPT request ({provider}, {model}) ... Done")

    return response