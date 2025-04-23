import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
import requests
from dotenv import load_dotenv, find_dotenv
from modules.Plots.models import Plot
import openai
from datetime import datetime, timedelta


load_dotenv(find_dotenv(), override=True)

mongo_key = os.getenv("MONGO_KEY")
weatherbit_api_key = os.getenv("WEATHER_API_KEY")  
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

weather_bp = Blueprint('weather_bp', __name__)

MODEL = "gpt-4o"
TEMPERATURE = 1
MAX_TOKENS = 200

@weather_bp.route("/", methods=["GET"])
def get_weather():
    try:
        email = session.get("email")
        role = session.get("role")

        if role == "manager":
            manager_email = email
        elif role in ["employee", "co_manager"]:
            manager_email = session.get("manager_email")
            if not manager_email:
                return jsonify({"error": "Manager email not found for user."}), 403
        else:
            return jsonify({"error": "Invalid role."}), 403

        manager = db.manager.find_one({"email": manager_email})
        if not manager:
            return jsonify({"error": "Manager not found in the database."}), 404

        city = manager.get("location")
        if not city:
            return jsonify({"error": "Location not found for the manager."}), 400

        # בדיקה אם קיימים נתונים שמורים
        weather_cache = db.weather_cache.find_one({"city": city})
        if weather_cache and "timestamp" in weather_cache:
            last_update = weather_cache["timestamp"]
            if datetime.utcnow() - last_update < timedelta(hours=1):
                return jsonify(weather_cache["data"]), 200

        current_url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={weatherbit_api_key}&lang=he"
        current_response = requests.get(current_url)
        if current_response.status_code != 200:
            return jsonify({"error": f"Failed to fetch weather data: {current_response.status_code}"}), current_response.status_code

        current_data = current_response.json().get("data", [])[0]
        temperature = current_data.get("temp", "לא זמין")
        humidity = current_data.get("rh", "לא זמין")
        wind_speed = current_data.get("wind_spd", "לא זמין")
        precipitation_now = current_data.get("precip", 0)
        weather_description = current_data.get("weather", {}).get("description", "לא זמין")
        weather_icon = current_data.get("weather", {}).get("icon", None)

        forecast_url = f"https://api.weatherbit.io/v2.0/forecast/daily?city={city}&key={weatherbit_api_key}&days=3&lang=he"
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code != 200:
            return jsonify({"error": f"Failed to fetch forecast data: {forecast_response.status_code}"}), forecast_response.status_code

        forecast_data = forecast_response.json().get("data", [])
        rain_forecast = [
            {
                "date": day["valid_date"],
                "rain_mm": day.get("precip", 0),
                "rain_probability": day.get("pop", 0)
            }
            for day in forecast_data
        ]

        response_data = {
            "city": city,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "precipitation_now": f"{precipitation_now} מ\"מ" if precipitation_now else "אין גשם כרגע",
            "weather_description": weather_description,
            "weather_icon": f"https://www.weatherbit.io/static/img/icons/{weather_icon}.png" if weather_icon else None,
            "rain_forecast": rain_forecast
        }

        # עדכון / יצירה במסד הנתונים
        db.weather_cache.update_one(
            {"city": city},
            {"$set": {
                "timestamp": datetime.utcnow(),
                "data": response_data
            }},
            upsert=True
        )

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@weather_bp.route("/irrigation_recommendation", methods=["POST"])
def irrigation_recommendation():
    try:
        email = session.get("email")
        role = session.get("role")

        if role == "manager":
            manager_email = email
        elif role in ["employee", "co_manager"]:
            manager_email = session.get("manager_email")
            if not manager_email:
                return jsonify({"error": "Manager email not found for user."}), 403
        else:
            return jsonify({"error": "Invalid role."}), 403

        manager = db.manager.find_one({"email": manager_email})
        if not manager:
            return jsonify({"error": "Manager not found in the database."}), 404

        city = manager.get("location")
        if not city:
            return jsonify({"error": "Location not found for the manager."}), 400

        crop_type = request.json.get("crop_type")
        if not crop_type:
            return jsonify({"error": "Missing required fields in the request."}), 400

        # נשלוף מהקאש אם קיים ועדכני
        weather_cache = db.weather_cache.find_one({"city": city})
        if weather_cache and "timestamp" in weather_cache:
            last_update = weather_cache["timestamp"]
            if datetime.utcnow() - last_update < timedelta(hours=1):
                data = weather_cache["data"]
                temperature = data.get("temperature")
                humidity = data.get("humidity")
                wind_speed = data.get("wind_speed")
                precipitation_now = data.get("precipitation_now").split()[0] if data.get("precipitation_now") else 0
                weather_description = data.get("weather_description")
                rain_forecast = [
                    f"{day['date']}: {day['rain_mm']} מ\"מ, {day['rain_probability']}% סיכוי לגשם"
                    for day in data.get("rain_forecast", [])
                ]
            else:
                raise ValueError("Cache too old, force API call")
        else:
            # שליפת מזג אוויר חדשה במידת הצורך
            current_url = f"https://api.weatherbit.io/v2.0/current?city={city}&key={weatherbit_api_key}&lang=he"
            forecast_url = f"https://api.weatherbit.io/v2.0/forecast/daily?city={city}&key={weatherbit_api_key}&days=3&lang=he"

            current_response = requests.get(current_url)
            forecast_response = requests.get(forecast_url)

            if current_response.status_code != 200 or forecast_response.status_code != 200:
                return jsonify({"error": "Failed to fetch weather data"}), 500

            current_data = current_response.json().get("data", [])[0]
            forecast_data = forecast_response.json().get("data", [])

            temperature = current_data.get("temp", "לא זמין")
            humidity = current_data.get("rh", "לא זמין")
            wind_speed = current_data.get("wind_spd", "לא זמין")
            precipitation_now = current_data.get("precip", 0)
            weather_description = current_data.get("weather", {}).get("description", "לא זמין")
            rain_forecast = [
                f"{day['valid_date']}: {day.get('precip', 0)} מ\"מ, {day.get('pop', 0)}% סיכוי לגשם"
                for day in forecast_data
            ]

            # שמירת קאש חדש
            db.weather_cache.update_one(
                {"city": city},
                {"$set": {
                    "timestamp": datetime.utcnow(),
                    "data": {
                        "city": city,
                        "temperature": temperature,
                        "humidity": humidity,
                        "wind_speed": wind_speed,
                        "precipitation_now": f"{precipitation_now} מ\"מ" if precipitation_now else "אין גשם כרגע",
                        "weather_description": weather_description,
                        "weather_icon": None,
                        "rain_forecast": [
                            {
                                "date": day["valid_date"],
                                "rain_mm": day.get("precip", 0),
                                "rain_probability": day.get("pop", 0)
                            }
                            for day in forecast_data
                        ]
                    }
                }},
                upsert=True
            )

        # בניית פרומפט ל־GPT
        prompt = (
            f"בהתבסס על הנתונים הבאים, תן המלצת השקיה לגידול {crop_type} בעיר {city}: \n"
            f"- טמפרטורה נוכחית: {temperature}°C\n"
            f"- לחות יחסית: {humidity}%\n"
            f"- מהירות הרוח: {wind_speed} קמ\"ש\n"
            f"- תיאור מזג האוויר: {weather_description}\n"
            f"- כמות גשם נוכחית: {precipitation_now} מ\"מ\n"
            f"- תחזית גשם לימים הקרובים:\n"
            + "\n".join(rain_forecast) +
            f"\n\n"
            f"תן המלצה מפורטת לכמות מים מומלצת להשקיה להיום,ציין את סוג הגידול ורק את מה שרלוונטי להשקיה (אין צורך לפרט על כל פרמטר אם לא נדרש) (בליטרים לכל מ\"ר) תוך התחשבות בגשם הצפוי בעתיד."
            f"אין להשתמש במילות סלנג. הכל בשפה מקצועית. "
            f"give me the output with <p> tags for the sentences "
        )

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "אתה מומחה להשקיה חכמה וחקלאות מדויקת בישראל."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        irrigation_advice = response['choices'][0]['message']['content']

        return jsonify({
            "city": city,
            "crop_type": crop_type,
            "irrigation_advice": irrigation_advice
        }), 200

    except openai.error.OpenAIError as e:
        return jsonify({"error": f"שגיאה ב-API של OpenAI: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"שגיאה כללית: {e}"}), 500

