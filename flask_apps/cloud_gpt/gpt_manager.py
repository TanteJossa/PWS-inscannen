# from google.generativeai.types import GenerateContentResponse

from open_ai_wrapper import (
    openai_single_request
)
from gemini_wrapper import (
    google_single_request
)
from claude_wrapper import (  # Import the new Claude wrapper
    claude_single_request
)

import json
import time
from helpers import (
    OpenAi_module_models
)


def single_request(
    input_data=False,
    provider=False,
    model=False,
    schema_string=False,
    temperature=False,
    limit_output=False
):
    if not input_data:
        input_data = [{
            "type": "text",
            "text": "eindig dit gesprek zo snel mogelijk."
        }]
    if not provider or not model:
        provider = "google"  # A default, can be changed
        model = "gemini-2.0-flash"  # a default

    if not temperature:
        temperature = 0.1

    if schema_string:
        input_data.append({
            "type": "text",
            "text": f"Geef alleen een json object als response met de volgende structuur, gebruik precies de benaming van de keys, dus ookal is het in een andere taal:\n {schema_string}"
        })

    print(f"GPT request ({provider}, {model}) ... ")

    if provider in OpenAi_module_models.keys():

        messages = input_data
        try:
            result = openai_single_request(
                messages=messages, model=model, provider=provider, temperature=temperature)
        except:
            result = {
                "result_data": {
                    "error": "something went wrong, maybe a timeout"
                },
                "request_data": {
                "tokens_used": 0,
                "model_used": model,
                "model_version": model,
                "timestamp": 0,
                "delta_time_s": 0
            }
            }
        result_data = result["result_data"]
        request_data = result["request_data"]
        response = {
            "result": result_data,
            "tokens_used": request_data.get("total_tokens", 0),

            "model_used": result.get("model_used", "not_found"),
            "model_version": result.get("model_version", "not_found"),

            "timestamp":  result.get("timestamp", 0),
            "delta_time_s":  result.get("delta_time_s", 0),
        }

    elif provider == 'google':

        start_time = time.time()
        try:
            result = google_single_request(
                task_list=input_data,
                model=model,
                limit_output=limit_output,
                temperature=temperature
            )

            print(result)
            if ('candidates' in result):
                try:
                    result_data = json.loads(
                        result['candidates'][0]['content']['parts'][0]['text'])
                except:
                    invalid_json = result['candidates'][0]['content']['parts'][0]['text']
                    try:
                        print('Trying to repair json: ', invalid_json)
                        valid_json = invalid_json+"}"
                        result_data = json.loads(valid_json)
                    except:
                        print('Single Request Error: ', invalid_json)
                        result_data = {}
            else:
                if result:
                    result_data = result
                else:
                    result_data = {}

            if ("usageMetadata" in result and "totalTokenCount" in result["usageMetadata"]):
                token_count = int(result["usageMetadata"]["totalTokenCount"])
            else:
                token_count = 0
        except:
            result_data = {}
            token_count = 0

        end_time = time.time()
        # print(result, result.usage_metadata.total_token_count)
        response = {
            "result": result_data,
            # "spelling_corrections": result_data["spelling_corrections"],

            "tokens_used": token_count,

            "model_used": model,
            "model_version": model,
            "provider": provider,

            "timestamp":  end_time,
            "delta_time_s":  (end_time - start_time),
        }
    elif provider == 'anthropic':  # Added the Claude provider
        start_time = time.time()
        try:
            from claude_wrapper import get_claude_messages
            claude_messages = get_claude_messages(
                input_data)  # Format messages for Claude
            result = claude_single_request(
                task_list=claude_messages,
                model=model,
                limit_output=limit_output,
                temperature=temperature
            )
            # Claude doesn't directly provide token usage in the same way.  We'll estimate.
            if isinstance(result, str):
                token_count = len(result.split())  # very rough estimate.
                result_data = result
            elif isinstance(result, dict):
                token_count = 0
                if 'usage' in result and 'output_tokens' in result['usage']:
                    token_count += result['usage']['output_tokens']
                if 'usage' in result and 'input_tokens' in result['usage']:
                    token_count += result['usage']['input_tokens']
                result_data = result

            else:
                token_count = 0  # default
                result_data = {}  # default
        except Exception as e:
            print(f"Error in Claude request: {e}")
            result_data = {}
            token_count = 0

        end_time = time.time()
        response = {
            "result": result_data,
            "tokens_used": token_count,  # Estimated token count
            "model_used": model,
            "model_version": model,  # Keep model and version the same for simplicity
            "provider": provider,
            "timestamp":  end_time,
            "delta_time_s":  (end_time - start_time),
        }
    else:
        response = {"error": "[provider not found]"}

    print(f"GPT request ({provider}, {model}) ... Done")

    return response
