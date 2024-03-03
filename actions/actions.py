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
        self.db = pd.read_csv("restaurants.csv")

    def fetch_restaurants(self):
        return self.db.head()

    def format_restaurants(self, df, header=True) -> Text:
        return df.to_csv(index=False, header=header)


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

    def ask(self, restaurants, question):
        content  = self.prompt + "\n\n" + restaurants + "\n\n" + question
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
        restaurants = restaurant_api.fetch_restaurants()
        results = restaurant_api.format_restaurants(restaurants)
        readable = restaurant_api.format_restaurants(restaurants[['Restaurants', 'Rating']], header=False)
        dispatcher.utter_message(text=f"Here are some restaurants:\n\n{readable}")

        return [SlotSet("results", results)]


class ActionRestaurantsDetail(Action):
    def name(self) -> Text:
        return "action_restaurants_detail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        chatGPT = ChatGPT()
        previous_results = tracker.get_slot("results")
        question = tracker.latest_message["text"]
        answer = chatGPT.ask(previous_results, question)
        dispatcher.utter_message(text = answer)