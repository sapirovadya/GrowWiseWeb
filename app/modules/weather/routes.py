import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from modules.Plots.models import Plot
import openai
from datetime import datetime

load_dotenv(find_dotenv())

mongo_key = os.getenv("MONGO_KEY")
weatherbit_api_key = os.getenv("WEATHER_API_KEY")  # ודא שהמפתח מוגדר בקובץ .env
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

weather_bp = Blueprint('weather_bp', __name__)

@weather_bp.route("/", methods=["GET"])
def get_weather():
    try:
        manager_email = session.get("email")
        if not manager_email:
            return jsonify({"error": "Manager is not logged in."}), 403

        manager = db.manager.find_one({"email": manager_email})
        if not manager:
            return jsonify({"error": "Manager not found in the database."}), 404

        city = manager.get("location")
        if not city:
            return jsonify({"error": "Location not found for the manager."}), 400

        url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={weatherbit_api_key}&lang=he"
        response = requests.get(url)

        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch weather data: {response.status_code}"}), response.status_code

        weather_data = response.json()
        hourly_forecast = weather_data.get("data", [])
        if not hourly_forecast:
            return jsonify({"error": "No weather data available."}), 404

        first_hour = hourly_forecast[0]
        temperature = first_hour.get("temp", "לא זמין")
        humidity = first_hour.get("rh", "לא זמין")
        wind_speed = first_hour.get("wind_spd", "לא זמין")
        precipitation = first_hour.get("precip", "אין נתונים")

        return jsonify({
            "city": city,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation": f"{precipitation} מ\"מ" if precipitation else "אין צפי לגשם"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500



# @weather_bp.route("/", methods=["GET"])
# def get_weather():
#     try:
#         # שליפת מיקום מה-Session
#         manager_email = session.get("email")
#         if not manager_email:
#             return jsonify({"error": "Manager is not logged in."}), 403

#         manager = db.manager.find_one({"email": manager_email})
#         if not manager:
#             print(f"Manager Email: {manager_email}")
#             return jsonify({"error": "Manager not found in the database."}), 404

#         city = manager.get("location")
#         if not city:
#             return jsonify({"error": "Location not found for the manager."}), 400

#         # שליחת בקשה ל-OpenWeatherMap
#         api_key = os.getenv("WEATHER_API_KEY")
#         url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=he"
#         response = requests.get(url)

#         if response.status_code != 200:
#             return jsonify({"error": f"Failed to fetch weather data: {response.status_code}"}), response.status_code

#         weather_data = response.json()
#         print(weather_data)

#         # חיזוי גשם
#         rain_forecast = weather_data.get("rain", {}).get("3h", "אין נתונים")  # משקעים בשעה הקרובה

#         return jsonify({
#             "city": city,
#             "temperature": weather_data["main"]["temp"],
#             "description": weather_data["weather"][0]["description"],
#             "humidity": weather_data["main"]["humidity"],
#             "wind_speed": weather_data["wind"]["speed"],
#             "rain": rain_forecast
#         }), 200

#     except Exception as e:
#         return jsonify({"error": f"Server error: {str(e)}"}), 500
