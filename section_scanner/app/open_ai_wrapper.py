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

from helpers import json_from_string, OpenAi_module_models


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



def get_client(provider):
    if (OpenAi_module_models[provider]):
        return OpenAI(api_key=OpenAi_module_models[provider]["key"], base_url=OpenAi_module_models[provider]["base_url"])
    else:
        raise Exception("Provider not found")
    


from pydantic import ValidationError

def get_response_json(response, gpt_model, start_time, end_time, response_format):
    dict_response = response.to_dict()
    choice_response = dict_response["choices"][0]
    message = choice_response["message"]
    
    parsed_data = message.get("parsed")
    content = message.get("content", "")
    
    result_data = None
    
    # First try to validate the parsed data if it exists
    if parsed_data is not None:
        try:
            parsed_model = response_format.model_validate(parsed_data)
            result_data = parsed_model.model_dump()
        except ValidationError:
            parsed_data = None  # Fall back to content parsing
    
    # If parsed data was invalid or not present, try parsing content
    if parsed_data is None:
        json_result = json_from_string(content)
        if json_result is not None:
            try:
                parsed_model = response_format.model_validate(json_result)
                result_data = parsed_model.model_dump()
            except ValidationError:
                # If validation fails, fall back to the original JSON if possible
                result_data = json_result
        else:
            # If no JSON could be parsed, use the content as a string
            result_data = content
    
    # Prepare request data
    request_data = dict_response.get("usage", {})
    
    # Construct the output JSON
    output_json = {
        "result_data": result_data,
        "request_data": request_data,
        "tokens_used": request_data.get("total_tokens", 0),
        "model_used": gpt_model,
        "model_version": dict_response.get("model", ""),
        "timestamp": int(end_time),
        "delta_time_s": end_time - start_time,
    }
    
    return output_json

class DefaultOpenAiSchema(BaseModel):
    result: str

def openai_single_request(messages, response_format=False, model = False, provider=False, temperature=False):
    to_use_response_format = response_format
    if not provider:
        provider = "openai"
    
    if (not model):
        model = "gpt-4o-mini"
        
    if not temperature:
        temperature = 0.02
        
    if not response_format:
        response_format = DefaultOpenAiSchema
    
    client = get_client(provider)
    
    
    if provider in ["deepseek", "alibaba"]:
        
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
        to_use_response_format = openai.NOT_GIVEN
        
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

    if model in ['o1-mini', 'o1-preview']:
        temperature = 1
    
    start_time = time.time()
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            temperature=temperature,
            messages=messages,
            response_format=to_use_response_format,
            # max_tokens=30_000, #test image was 15k tokens
            timeout=60
        )
    except Exception as e:
        print(f"GPT request... ({provider}, {model}) ERROR", str(e))
        raise Exception(str(e))
        return False

    end_time = time.time()

    print(response.to_dict())
    reponse_json = get_response_json(response, model, start_time, end_time, response_format)

    return reponse_json
