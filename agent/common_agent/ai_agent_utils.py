from agent.common_agent import tokanize, api_key
import openai
from openai import OpenAI
import base64
# In ai_agent_utils.py
import threading
import sqlite3


tokanizeclass = tokanize.TokenTracker()

def initialize_client():
    config ={}
    config["OPENAI_API_KEY"] = api_key.OPENAI_API_KEY
    config["ORG_ID"] = api_key.ORG_ID
    config["PROJECT_ID"] = api_key.PROJECT_ID

    #config = dotenv_values(".env")
    client = openai.OpenAI(
        api_key=config["OPENAI_API_KEY"],
        organization=config["ORG_ID"],
        project=config["PROJECT_ID"],
    )
    return client



thread_local = threading.local()

def get_thread_local_connection():
    if not hasattr(thread_local, 'db_connection'):
        thread_local.db_connection = sqlite3.connect('your_database.db')
    return thread_local.db_connection

def combine(dext, content, openai=False, db_connection=None):

    if openai:
        return open_ai_text(dext, content)
    else:
        return deepSeek(dext, content)

def deepSeek(text, content):
    import requests
    if tokanizeclass.stop_server() == False:
        return "Server is stopped"
    API_KEY = api_key.DEEPSEEK_API_KEY

    # Base URL
    API_URL = "https://api.deepseek.com/v1/chat/completions"

    # Your API Key

    # Headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Data payload
    data = {
        "model": "deepseek-chat",  # For DeepSeek-V3
        "messages": [
            {"role": "system", "content": content},
            {"role": "user", "content": text}
        ],
        "stream": False
    }

    # Make the request
    response = requests.post(API_URL, headers=headers, json=data)

    # Check the response
    if response.status_code == 200:
        #print(response.json())
        json_data = response.json()
        content = json_data['choices'][0]['message']['content']
        id = json_data['id']
        input_tokens = json_data['usage']['prompt_tokens']  # Modify based on actual DeepSeek API response
        output_tokens = json_data['usage']['completion_tokens']  # Modify based on actual DeepSeek API response
        total_tokens = json_data['usage']['total_tokens']  # Modify based on actual DeepSeek API response
        tokanizeclass.add_transaction(id, input_tokens, output_tokens, total_tokens, text)

        return content
    else:
        print(f"Error {response.status_code}: {response.text}")


def open_ai_text(dext, content, model="gpt-4o-mini", max_tokens=300):
    client = OpenAI(api_key=api_key.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": content},
            {"role": "user", "content": dext}
        ],
        max_tokens=max_tokens
    )
    response_json = response.model_dump()
    response_text = response.choices[0].message.content
    return response_json, response_text


def open_ai_image(image_path, prompt):
    # Encode image to base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    client = OpenAI(api_key=api_key.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )

    # Convert entire response to JSON
    response_json = response.model_dump()  # This converts the entire object to dict
    return response_json