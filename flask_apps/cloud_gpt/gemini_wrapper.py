import google.generativeai as genai
import json

from helpers import json_from_string
import requests

with open('creds/google_gemini.json', 'r') as f:
    data = json.load(f)
API_KEY = data["key"]


def google_single_request(
    task_list=False,
    model=False,
    limit_output=False,
    temperature=False,
):
    genai.configure(api_key=data["key"],transport="rest")

    if not model:
        model = "gemini-2.0-flash"
        # model = "gemini-2.0-flash-exp"
    if not temperature:
        temperature = 0.05

    if not task_list:
        task_list = []
    
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
