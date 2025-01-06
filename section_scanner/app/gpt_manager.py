from google.generativeai.types import GenerateContentResponse

from open_ai_wrapper import (
    openai_single_request
)
from gemini_wrapper import (
    google_single_image_request
)
from pydantic import BaseModel
import typing_extensions as typing
import json
import time

from fix_busted_json import repair_json


    
def single_request(provider=False, model=False, temperature=False, schema=False, image=False, text="", messages=False, limit_output=True):
    if not provider:
        provider = "google"


    print(f"GPT request ({provider}, {model}) ... ")



    if provider == 'openai':

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                                    # de vraagnummers moeten getallen zijn
                                    # als een vraagnummer een letter heeft, bijvoorbeeld 1a of 2c
                                    # noteer dat dan al volgt: 1.a en 2.c dus, {getal}.{letter}
                    },
                    {
                        "type": "text",
                        "text": "Geef antwoord in JSON zoals in een aangegeven schema staat"    
                    },
                ]
            },
        ]
        
        if (image):
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"{image}"
                        }
                    }
                ]
            })
            
            
        result = openai_single_request(messages=messages, response_format=schema, model=model, temperature=temperature)
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

    if provider == 'google':
        
        start_time = time.time()
        
        result:GenerateContentResponse = google_single_image_request(
            text=text,
            base64_image=image,
            model=model,
            id=id,
            response_format=schema,
            task_list=messages,
            limit_output=limit_output
        )
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

    print(f"GPT request ({provider}, {model}) ... Done")

    return response