import json
import os
from dotenv import load_dotenv
from typing import Any, Text, Dict, List
import pandas as pd
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

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

class ChatGPT(object):
    def __init__(self):
        self.url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
        }
        self.prompt = "Answer the following question, based on the data shown. " \
            "Answer in a complete sentence and don't say anything else."

    def ask(self, courses, question):
        print(courses, question)
        content  = self.prompt + "\n\n" + courses + "\n\n" + question
        body = {
            "model":self.model, 
            "messages":[{"role": "user", "content": content}]
        }
        result = requests.post(
            url=self.url,
            headers=self.headers,
            json=body,
        )
        response_json = result.json()  # Log the entire JSON response
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "No content found")

restaurant_api = RestaurantAPI()
chatGPT = ChatGPT()

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
        previous_results = tracker.get_slot("results")
        print(previous_results)
        question = tracker.latest_message["text"]
        answer = chatGPT.ask(previous_results, question)
        dispatcher.utter_message(text = answer)

class ActionFallback(Action):
    def name(self) -> Text:
        return "action_agri_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        chatGPT = ChatGPT()
        question = tracker.latest_message["text"]
        answer = chatGPT.ask(question)
        dispatcher.utter_message(text=answer)
        return []
    
# class ActionAgriFaq(Action):

#     def name(self) -> Text:
#         return "action_agri_faq"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#         # print(tracker.latest_message)
        
#         # to get intent of user message
#         _intent=tracker.latest_message['intent'].get('name')
#         print("Intent of user message predicted by Rasa ",_intent)

#         print(tracker.latest_message['text']) # to get user typed message 

#         intent_found = json.dumps(tracker.latest_message['response_selector'][_intent]['ranking'][0]['intent_response_key'], indent=4)
        
#         # confidence of retrieval intent we found
#         retrieval_intent_confidence = tracker.latest_message['response_selector'][_intent]['response']['confidence']*100
#         print(f"retrieval_intent_confidence we found was {retrieval_intent_confidence}")

#         if retrieval_intent_confidence < 100:
#             if "category-1" in _intent:
#                 print("Custom Fallback for category-1 can be implemented here")
#                 dispatcher.utter_message(text="Custom Fallback for category-1 can be implemented here")
#             elif "category-2" in _intent:
#                 print("Custom Fallback for category-2 can be implemented here")
#                 dispatcher.utter_message(text="Custom Fallback for category-2 can be implemented here")
#             return []
#         #used eval to remove quotes around the string
#         intent_found = f'utter_{eval(intent_found)}'
#         print('after adding utter we found -- ', intent_found)
#         dispatcher.utter_message(response = intent_found) # use response for defining intent name
        
#         return [] # setting slot values