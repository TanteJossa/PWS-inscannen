from openai import OpenAI
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



def get_client():
    with open("creds/openaikey.json", "r") as f:
        openai_key = json.load(f)["key"]
    

    openai_client = OpenAI(api_key=openai_key)
    
    return openai_client

def get_response_json(response, gpt_model, start_time, end_time):
    
    dict_response = response.to_dict()
    choice_response = dict_response["choices"][0]
    result_data = choice_response["message"]["parsed"]
    request_data = dict_response["usage"]

    output_json = {
        "result_data": result_data,
        "request_data": request_data,

        "tokens_used": request_data["total_tokens"],

        "model_used": gpt_model,
        "model_version": dict_response["model"],
        
        "timestamp": int(end_time),
        "delta_time_s": end_time - start_time,
    }


    return output_json


def single_request(messages, response_format):
    
    openai_client = get_client()
    
    gpt_model = "gpt-4o-mini"

    start_time = time.time()

    print("GPT request... ")
    
    try:
        response = openai_client.beta.chat.completions.parse(
            model=gpt_model,
            temperature=0.05,
            messages=messages,
            response_format=response_format,
            # max_tokens=30_000, #test image was 15k tokens
            timeout=14
        )
    except Exception as e:
        print("GPT request... ERROR")
        raise Exception(str(e))
        return False
    print("GPT request... Done")

    end_time = time.time()


    reponse_json = get_response_json(response, gpt_model, start_time, end_time)

    return reponse_json

# def batch_request(api_requests):
#     openai_client = get_client()
    
#     gpt_model = "gpt-4o-mini"

#     request_id = uuid.uuid4()

#     start_time = time.time()

#     print("GPT request... ")
#     request_data = []
    
#     for (i, api_request) in enumerate(api_requests):
#         request_data.append({
#             "custom_id": "request-"+i, 
#             "method": "POST", 
#             "url": "/v1/chat/completions", 
#             "body": api_request
#         })
    
    
#     with open("batchinput.jsonl", "w") as f:
#         f.write(request_data)
    
#     input_file = openai_client.files.create(
#         file=open("batchinput.jsonl", "rb"),
#         purpose="batch"
#     )
    
#     try:
#         batch_input_file_id = input_file.id

#         batch_data = openai_client.batches.create(
#             input_file_id=batch_input_file_id,
#             endpoint="/v1/chat/completions",
#             completion_window="h",
#             metadata={
#                 "description": "nightly eval job"
#             }
#         )
#     except:
#         print("GPT request... ERROR")
#         return False
    
#     with open('./batch/'+request_id+'.json', 'w') as f:
#         f.write(batch_data)
    
#     print("GPT request... Done")

#     end_time = time.time()

#     # # from pprint import pprint
#     # # pprint(response)
#     # json_output_path = current_path + r"/single_request_json_output"


#     # try:
#     #     os.makedirs(json_output_path)
#     # except:
#     #     pass

#     # student_json_output_path = json_output_path + "/"
#     # # + student + "/sections" 
#     # try:
#     #     os.makedirs(student_json_output_path)
#     # except:
#     #     pass

#     # # TODO: choose better name
#     # #  currently using the original image file name
#     # image_json_output_path = student_json_output_path #+ "/" + image_name
#     # try:
#     #     os.makedirs(image_json_output_path)
#     # except:
#     #     pass

#     # # copy image here
#     # # copy_image(input_image_path, image_json_output_path)
        

#     # json_output_path = image_json_output_path + "/" + gpt_model + "_result.json"

#     # reponse_json = get_response_json(response, gpt_model, start_time, end_time)

#     # with open(json_output_path, "w") as outfile:
#     #     outfile.write(reponse_json)
        
#     # print("Written to file "+json_output_path)




# scan_section(student, image_name)
