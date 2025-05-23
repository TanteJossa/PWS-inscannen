import requests

from pydantic import BaseModel
import typing_extensions as typing
import json
import time
from helpers import (
    typed_dict_to_string,
    base_model_to_schema_string,
    is_localhost,
    GPT_URL
)

    
def single_request(provider=False, model=False, temperature=False, schema=False, image=False, text="", messages=False, limit_output=True):

    if not messages:
        messages = []
    


    print(f"GPT request ({provider}, {model}) ... ")

    if text:
        messages.append({
            "type": "text",
            "text": text
        })
    if image:
        messages.append({
            "type": "image",
            "image": image
        })
        
    if isinstance(schema, str):
        schema_string = schema
    elif isinstance(schema, dict):
        schema_string = json.dumps(schema)
    elif hasattr(schema, '__class__'):
        try:
            schema_string = base_model_to_schema_string(schema)
        except:
            schema_string = False
    # elif isinstance(schema, ):
    #     try:
    #         schema_string = typed_dict_to_string(schema)
    #     except:
    #         schema_string = False
    else:
        schema_string = False
    
    url = 'http://127.0.0.1:8081/gpt' if is_localhost else GPT_URL
    
    response = requests.post(url, {}, {
        "provider": provider,
        "model": model,
        "data": messages,
        "schema_string": schema_string,
        "temperature": temperature
    })
    try:
        response = response.json()
    except Exception as e:
        print('error', response.text, str(e))
        response = {'error':'json error'}
    if ('output' in response):
        print(f"GPT request ({provider}, {model}) ... Done")
        return response["output"]

    print(f"GPT request ({provider}, {model}) ... Error")


    return response