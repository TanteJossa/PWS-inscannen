from openai import OpenAI
import openai
import time

from helpers import json_from_string, OpenAi_module_models


def get_client(provider):
    if (OpenAi_module_models[provider]):
        return OpenAI(api_key=OpenAi_module_models[provider]["key"], base_url=OpenAi_module_models[provider]["base_url"])
    else:
        raise Exception("Provider not found")
    
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


from pydantic import ValidationError

def get_response_json(response, gpt_model, start_time, end_time):
    dict_response = response.to_dict()
    choice_response = dict_response["choices"][0]
    message = choice_response["message"]
    
    parsed_data = message.get("parsed")
    content = message.get("content", "")
    
    result_data = None
    
    # First try to validate the parsed data if it exists
    if parsed_data is not None:
        # try:
        #     parsed_model = response_format.model_validate(parsed_data)
        #     result_data = parsed_model.model_dump()
        # except ValidationError:
        parsed_data = None  # Fall back to content parsing
    
    # If parsed data was invalid or not present, try parsing content
    if parsed_data is None:
        json_result = json_from_string(content)
        if json_result is not None:
            # try:
            #     parsed_model = response_format.model_validate(json_result)
            #     result_data = parsed_model.model_dump()
            # except ValidationError:
            #     # If validation fails, fall back to the original JSON if possible
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


def openai_single_request(messages, response_format=False, model = False, provider=False, temperature=False):
    to_use_response_format = response_format
    if not provider:
        provider = "openai"
    
    if (not model):
        model = "gpt-4o-mini"
        
    if not temperature:
        temperature = 0.02
        

    client = get_client(provider)
    
    messages = get_openai_messages(messages)
    
    to_use_response_format = openai.NOT_GIVEN
        
    if model == 'deepseek-reasoner' or provider in ["groq"]:
        all_text = ""
        for message in messages:
            content = message.get("content", "")
            # for sub_message in message["content"]:
            if (isinstance(content, str)):
                all_text += content + '\n'
                # all_text += sub_message + '\n'
            # else:
                
        messages = [{
            "role": "user",
            "content": all_text
        }]
        
    if model in ['o1-mini', 'o1-preview']:
        temperature = 1
    
    start_time = time.time()
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            temperature=temperature,
            messages=messages,
            response_format=to_use_response_format, #currently always none
            # max_tokens=30_000, #test image was 15k tokens
            timeout=60
        )
    except Exception as e:
        print(f"GPT request... ({provider}, {model}) ERROR", str(e))
        raise Exception(str(e))
        return False

    end_time = time.time()

    reponse_json = get_response_json(response, model, start_time, end_time)

    return reponse_json
