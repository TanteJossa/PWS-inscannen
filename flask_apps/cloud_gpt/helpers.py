import uuid
import json

def get_random_id():
    return str(uuid.uuid4())

def json_from_string(s:str):
    # Find the first '{' and last '}' in the string
    first_brace = s.find('{')
    last_brace = s.rfind('}')
    
    # Check if braces exist and are correctly ordered
    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        return None
    
    # Extract the substring between the first '{' and last '}'
    json_str = s[first_brace : last_brace + 1]

    try:
        # Parse the JSON string
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 

with open("creds/openaikey.json", "r") as f:
    openai_key = json.load(f)["key2"]
with open("creds/deepseek.json", "r") as f:
    deepseek_key = json.load(f)["key"]
with open("creds/alibaba.json", "r") as f:
    alibaba_key = json.load(f)["key"]
with open("creds/groq.json", "r") as f:
    groq_key = json.load(f)["key"]

OpenAi_module_models = {
    "openai": {
        "base_url": None,
        "key": openai_key
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "key": deepseek_key
    },
    "alibaba": {
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "key": alibaba_key
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key": groq_key
    }
}
