import json
import os
from dotenv import load_dotenv
from typing import Any, Text, Dict, List
import pandas as pd
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .chatgpt.main import ChatGPT

# Load environment variables from .env file
load_dotenv()

class RestaurantAPI(object):
    def __init__(self):
        with open("courses.json", "r") as json_file:
            self.db = json.load(json_file)

    def fetch_restaurants(self):
        return pd.DataFrame(self.db["courses"])

    def format_restaurants(self, df) -> str:
        html = "<table style='border-collapse: collapse; border: 1px solid black;'>"
        html += "<tr><th style='border: 1px solid black;'>কোর্সের নাম</th><th style='border: 1px solid black;'>রেটিং</th><th style='border: 1px solid black;'>প্রদানকারী</th><th style='border: 1px solid black;'>সময়</th></tr>"
        for _, row in df.iterrows():
            html += f"<tr><td style='border: 1px solid black;'>{row['course_name_bn']}</td><td style='border: 1px solid black;'>{row['Rating']}</td><td style='border: 1px solid black;'>{row['provider']}</td><td style='border: 1px solid black;'>{row['time']}</td></tr>"
        html += "</table>"
        return html



restaurant_api = RestaurantAPI()

class ActionShowRestaurants(Action):
    def name(self) -> Text:
        return "action_show_restaurants"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        restaurant_api = RestaurantAPI()
        courses = restaurant_api.fetch_restaurants()
        html_table = restaurant_api.format_restaurants(courses)
        dispatcher.utter_message(text=f"নিচে কিছু কোর্সের তালিকা দেওয়া হল:\n\n{html_table}")

        return [SlotSet("results", html_table)]

class ActionRestaurantsDetail(Action):
    def name(self) -> Text:
        return "action_restaurants_detail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        chatGPT = ChatGPT()
        chatGPT.prompt = "Answer the following question, based on the data shown. " \
            "First Calculate and then answer in a complete sentence: "
        previous_results = tracker.get_slot("results")
        print(previous_results)
        question = tracker.latest_message["text"]
        answer = chatGPT.ask(previous_results, question)
        dispatcher.utter_message(text = answer)

# class ActionFallback(Action):
#     def name(self) -> Text:
#         return "action_default_fallback"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
#         chatGPT = ChatGPT()
#         chatGPT.prompt = ""
#         previous_results = ""
#         question = tracker.latest_message["text"]
#         print(question)
#         answer = chatGPT.ask(previous_results, question)
#         print(answer)
#         dispatcher.utter_message(text=answer)
#         return []
        
class ActionFallback(Action):
    def name(self):
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        user_message = tracker.latest_message.get('text')
        chat_history = self.get_chat_history(tracker)
        fallback_response = self.get_fallback_response(user_message, chat_history)
        dispatcher.utter_message(text=fallback_response)

    def get_chat_history(self, tracker):
        # Retrieve chat history from tracker
        events = tracker.events
        chat_history = []
        for event in events:
            if 'text' in event['event'] and 'user' in event['event']:
                chat_history.append(event['event']['text'])
        return chat_history

    def get_fallback_response(self, user_message, chat_history):
        # Call ChatGPT API with chat history
        chatgpt_response = self.call_chatgpt_api(user_message, chat_history)
        return chatgpt_response

    def call_chatgpt_api(self, user_message, chat_history):
        # Example code to call ChatGPT API with chat history
        url = "YOUR_CHATGPT_API_ENDPOINT"
        headers = {"Authorization": "Bearer YOUR_API_KEY"}
        data = {"chat_history": chat_history, "user_message": user_message}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get("response")
        else:
            return "I'm sorry, I couldn't understand that."
    