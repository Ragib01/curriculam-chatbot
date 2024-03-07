import requests
import os

class ChatGPT(object):
    def __init__(self):
        self.url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        self.prompt = ""

    def ask(self, context, question):
        content  = self.prompt + "\n\n" + context + "\n\n" + question
        body = {
            "model":self.model, 
            "messages":[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content}
            ],
            "temperature": 1,
            "max_tokens": 2048,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0 
        }
        result = requests.post(
            url=self.url,
            headers=self.headers,
            json=body,
        )
        response_json = result.json()  # Log the entire JSON response
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "No content found")