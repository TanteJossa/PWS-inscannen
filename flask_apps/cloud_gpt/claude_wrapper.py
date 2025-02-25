import anthropic
import json
# Assuming this helper function works for Claude's JSON responses too
from helpers import json_from_string

# Load API key from a JSON file
with open('creds/anthropic_claude.json', 'r') as f:  # Changed file path
    data = json.load(f)
API_KEY = data["key"]

client = anthropic.Anthropic(api_key=API_KEY)


def get_claude_messages(input_data):
    """
    Formats input data into a list of messages suitable for Claude.
    Handles text and image inputs.
    """
    messages = []
    for item in input_data:
        if item["type"] == "text":
            # Claude uses role-based messages
            messages.append({"role": "user", "content": item["text"]})
        elif item["type"] == "image" and "image" in item:
            base64_image = item["image"]
            if base64_image.startswith('data:image'):
                base64_image = base64_image.split(',')[1]

            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",  # Or "image/jpeg" if appropriate
                            "data": base64_image,
                        },
                    },
                ],
            })

    return messages


def claude_single_request(
    task_list=False,
    model=False,
    limit_output=False,
    temperature=False,
):
    """
    Sends a single request to the Claude API.

    Args:
        task_list:  A list of message dictionaries, as formatted by get_claude_messages.
        model: The Claude model name (e.g., "claude-3-opus-20240229").
        limit_output: Boolean, whether to limit the output token count.
        temperature:  The sampling temperature (0.0 to 1.0).

    Returns:
        A dictionary containing the parsed JSON response from Claude, or the raw
        text content if JSON parsing fails.
    """

    if not model:
        model = "claude-3-opus-20240229"  # A good default Claude 3 model
    if not temperature:
        temperature = 0.05  # Low temperature for more deterministic outputs

    if not task_list:
        task_list = []

    try:

        if len(task_list) > 1 and isinstance(task_list[-1], dict) and task_list[-1]["content"] and isinstance(task_list[-1]["content"], list) and task_list[-1]["content"][0]["type"] == "image":
            messages = task_list[:-1] + [
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": "Here is the image, please process it according to the previous instructions."
                        }, 
                        task_list[-1]["content"][0]
                    ]
                }
            ]

        else:
            messages = task_list

        # Claude has a high context window.  Limit only if requested.
        max_tokens = 1000 if limit_output else 4096

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
            # system="",  # Optional: Use a system prompt if needed
            # response_format = "json", # Removed due to errors, handle below
        )

        # Attempt to parse the response as JSON
        try:
            result = json_from_string(response.content[0].text)

        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, return the raw text content
            print("Claude JSON parsing failed, returning raw text.")
            result = response.content[0].text

    except Exception as e:
        print(f"Claude request... ({model}) ERROR", str(e))
        raise Exception('Error in claude_single_request: ' + str(e))

    return result
