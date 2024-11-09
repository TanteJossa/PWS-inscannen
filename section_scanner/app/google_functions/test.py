import sys
import requests
import os
from helpers import (
    base64_to_png,
    png_to_base64,
    get_random_id
)
import json

print(png_to_base64('./test_input/crop_input.png')[0:200])

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/crop', 
        
    #     json={
    #         'Base64Image': png_to_base64('./test_input/crop_input.png')
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # result = response.json()
    # if ("error" in result):
    #     print(result)
    #     exit()
    # result = result["output"]
    # base_64_data = result
    # base64_to_png(base_64_data, './test_output/crop_output.png')
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/extract_red_pen', 
        
    #     json={
    #         'Base64Image': png_to_base64('./input.png')
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # base_64_data = response.json()["output"]["clean"]
    # base64_to_png(base_64_data, 'test_output.png')
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/extract_red_pen', 
        
    #     json={
    #         'Base64Image': png_to_base64('./test_input/input.png')
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # base_64_data = response.json()["output"]["clean"]
    # base64_to_png(base_64_data, 'test_output.png')
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/detect_squares', 
        
    #     json={
    #         'Base64Image': png_to_base64('./test_input/input.png')
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # result = response.json()
    # if ("error" in result):
    #     print(result)
    #     exit()
    # result = result["output"]
        
    # base_64_data = result["image"]
    # print(result["data"])
    # base64_to_png(base_64_data, 'test_output.png')
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/extract_sections', 
        
    #     json={
    #         'Base64Image': png_to_base64('./test_input/input.png'),
    #         "square_data": [[184, 20, 44, 63], [322, 18, 43, 61], [459, 17, 43, 61], [595, 18, 43, 61], [730, 18, 43, 61], [864, 18, 43, 60], [1001, 19, 43, 61]]
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # result = response.json()
    # if ("error" in result):
    #     print(result)
    #     exit()
    # result = result["output"]
    # try:
    #     os.mkdir('./test_output')
    # except:
    #     pass
    # for section in result["sections"]:
    #     id = get_random_id()
    #     try:
    #         os.mkdir('./test_output/'+id)
    #     except:
    #         pass
        
    #     for image_name in section:
    #         base64_to_png(section[image_name], './test_output/'+id+'/'+image_name+'.png')

    
    pass

if True:
    response:requests.Response = requests.post(
        'http://localhost:8080/question_selector_info', 
        
        json={
            'Base64Image': png_to_base64('./test_input/section_selection_input.png')
        },
        headers={
            "Content-Type": 'application/json'
        }
    )
    result = response.json()
    if ("error" in result):
        print(result)
        exit()
    result = result["output"]
    print(result)
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/link_answer_sections', 
        
    #     json={
    #         'sections': [
    #             png_to_base64('./test_input/answer1_1.png'),
    #             png_to_base64('./test_input/answer3_1.png')

    #         ]
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # result = response.json()
    # if ("error" in result):
    #     print(result)
    #     exit()
    # result = result["output"]
    # base64_to_png(result, './test_output/linked_output.png')
    pass

if True:
    # response:requests.Response = requests.post(
    #     'http://localhost:8080/extract_text', 
        
    #     json={
    #         'Base64Image': png_to_base64('./test_input/test_extract_input.png')
    #     },
    #     headers={
    #         "Content-Type": 'application/json'
    #     }
    # )
    # result = response.json()
    # if ("error" in result):
    #     print(result)
    #     exit()
    # result = result["output"]
    # print(result)
    pass
