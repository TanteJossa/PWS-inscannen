import requests
from helpers import (
    base64_to_png,
    png_to_base64
)
import json


response:requests.Response = requests.post(
    'http://localhost:8080/extract_red_pen', 
    
    {
        'Base64Image': png_to_base64('./input.png')
    },
    headers={
        "Content-Type": 'application/json'
    }

)
print('hi1')
base_64_data = response.json()
print('hi', base_64_data)
# base64_to_png(base_64_data, 'output.png')