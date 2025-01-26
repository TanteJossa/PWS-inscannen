from openai import OpenAI
import openai
import base64
import tiktoken
import json
from PIL import Image
import math
from io import BytesIO
import os
import shutil
import time
import uuid
from pydantic import BaseModel
import re

from helpers import json_from_string


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613"):
    """Returns the number of tokens used by a list of messages."""
    #   https://github.com/openai/tiktoken?tab=readme-ov-file#-tiktoken
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
        
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for data_value in message["content"]:
            if (data_value["type"] == "text"):
                data = data_value["text"]
            
            if (data_value["type"] == "image_url"):
                data = data_value["image_url"]["url"]    
            if (data):
                num_tokens += len(encoding.encode(data))
            # if data_value["type"] == "name":  # if there's a name, the role is omitted
            #     num_tokens += -1  # role is always required and always 1 token
    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


def copy_image(image_path, target_path):
    shutil.copy(image_path, target_path)



def get_openai_client():
    with open("creds/openaikey.json", "r") as f:
        openai_key = json.load(f)["key2"]
    

    openai_client = OpenAI(api_key=openai_key)
    
    return openai_client

def get_deepseek_client():
    with open("creds/deepseek.json", "r") as f:
        deepseek_key = json.load(f)["key"]
    

    deepseek_client = OpenAI(api_key=deepseek_key,base_url="https://api.deepseek.com")
    
    return deepseek_client

def get_response_json(response, gpt_model, start_time, end_time):
    
    dict_response = response.to_dict()
    choice_response = dict_response["choices"][0]
    if (choice_response["message"]["parsed"]):
        result_data = choice_response["message"]["parsed"]
    else:
        try:
            json_result = json_from_string(choice_response["message"]["content"])
            if (json_result):
                result_data = json_result
            else:
                raise Exception("No json result found")
        except:
            result_data = choice_response["message"]["content"]
                
    request_data = dict_response["usage"]

    output_json = {
        "result_data": result_data,
        "request_data": request_data,

        "tokens_used": request_data["total_tokens"],

        "model_used": gpt_model,
        "model_version": dict_response["model"],
        
        "timestamp": int(end_time),
        "delta_time_s": end_time - start_time ,
    }


    return output_json

class DefaultOpenAiSchema(BaseModel):
    result: str

def openai_single_request(messages, response_format=False, model = False, provider="openai", temperature=False):
    if (not model):
        model = "gpt-4o-mini"
        
    if not temperature:
        temperature = 0.02
        
    if not response_format:
        response_format = DefaultOpenAiSchema
    
    if provider == "openai":
        client = get_openai_client()
    elif provider == "deepseek":
        client = get_deepseek_client()
        
        # Generate schema dictionary
        schema_dict = response_format.model_json_schema()

        # Convert to JSON string
        json_schema_str = json.dumps(schema_dict, indent=2)
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Het JSON schema is: \n"+json_schema_str
                },
            ]
        })
        response_format = {"type": "json_object"}
        
        if model == 'deepseek-reasoner':
            all_text = ""
            for message in messages:
                for sub_message in message["content"]:
                    if (sub_message["type"] == "text"):
                        all_text += sub_message["text"] + '\n'
            messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": all_text
                }]
            }]
            response_format = openai.NOT_GIVEN
    start_time = time.time()

    if model in ['o1-mini', 'o1-preview']:
        temperature = 1
    
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            temperature=temperature,
            messages=messages,
            response_format=response_format,
            # max_tokens=30_000, #test image was 15k tokens
            timeout=60
        )
    except Exception as e:
        print(f"GPT request... ({provider}, {model}) ERROR", str(e))
        raise Exception(str(e))
        return False

    end_time = time.time()

    print(response.to_dict())
    reponse_json = get_response_json(response, model, start_time, end_time)

    return reponse_json
