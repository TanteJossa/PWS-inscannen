import requests

from pydantic import BaseModel
import typing_extensions as typing
import json
import time
from helpers import (
    typed_dict_to_string,
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
    elif isinstance(schema, BaseModel):
        try:
            schema_string = schema.model_json_schema()
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
        "schema_string": schema_string
    })
    response = response.json()
    if ('output' in response):
        print(f"GPT request ({provider}, {model}) ... Done")
        return response["output"]

    print(f"GPT request ({provider}, {model}) ... Error")


    return response