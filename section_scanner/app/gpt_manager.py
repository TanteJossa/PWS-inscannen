import requests

from pydantic import BaseModel
import typing_extensions as typing
import json
import time
from helpers import (
    typed_dict_to_string
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
    elif isinstance(schema, typing.TypedDict):
        try:
            schema_string = typed_dict_to_string(schema)
        except:
            schema_string = False
    else:
        schema_string = False
        
    
    response = requests.post('https://gpt-function-771520566941.europe-west4.run.app/gpt', {
        "provider": "deepseek",
        "model": "deepseek-sub_message",
        "data": messages,
        "schema_string": schema_string
    })
    
    if ('output' in response):
        print(f"GPT request ({provider}, {model}) ... Done")
        return response["output"]

    print(f"GPT request ({provider}, {model}) ... Error")


    return response