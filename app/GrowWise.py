from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
from dotenv import load_dotenv
import os
from modules.users.routes import users_bp_main
from modules.users.employee.routes import employee_bp
from modules.users.manager.routes import manager_bp
from modules.users.co_manager.routes import co_manager_bp
from modules.users.job_seeker.routes import job_seeker_bp
from modules.users.routes import logout_bp
from modules.Plots.routes import plot_bp
from modules.task.routes import task_bp
from modules.weather.routes import weather_bp
from modules.posts.routes import posts_bp
from modules.attendance.routes import attendance_bp
from modules.supply.routes import supply_bp
from modules.expenses.routes import expenses_bp
from modules.vehicles.routes import vehicles_bp
from modules.reports.routes import reports_bp
from modules.optimal_plots.routes import optimal_bp



import json

# עדכן את הנתיב בהתאם

load_dotenv()
app = Flask(__name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
app.db = client.get_database("dataGrow")

app.secret_key = os.getenv("APP_SECRET")

app.register_blueprint(users_bp_main, url_prefix="/users")
app.register_blueprint(employee_bp, url_prefix="/employee")
app.register_blueprint(manager_bp, url_prefix="/users/manager")
app.register_blueprint(co_manager_bp, url_prefix="/co_manager")
app.register_blueprint(job_seeker_bp, url_prefix="/job_seeker")
app.register_blueprint(plot_bp, url_prefix="/Plots")
app.register_blueprint(task_bp, url_prefix="/task")
app.register_blueprint(logout_bp)
app.register_blueprint(weather_bp, url_prefix="/weather")
app.register_blueprint(posts_bp, url_prefix="/posts")
app.register_blueprint(attendance_bp, url_prefix='/attendance')
app.register_blueprint(supply_bp, url_prefix='/supply')
app.register_blueprint(expenses_bp, url_prefix='/expenses')
app.register_blueprint(vehicles_bp, url_prefix='/vehicles')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(optimal_bp, url_prefix="/optimal")


HEBREW_MONTHS = [
    "", "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
]

try:
    app.db.weather_cache.create_index("city", unique=True)
    print("Unique index on weather_cache.city created or already exists")
except Exception as e:
    print("Error creating index on weather_cache.city:", e)

def update_crops_data():
    collection = app.db["crops_options"]

    try:
        # קריאת הקובץ
        with open("app/static/data/crops_data.json", "r", encoding="utf-8") as file:
            crops_data = json.load(file)

        # מחיקת הנתונים הקיימים
        deleted_count = collection.delete_many({}).deleted_count
        print(f"{deleted_count} documents deleted from MongoDB.")

        # הוספת הנתונים המעודכנים
        for category in crops_data:
            collection.insert_one(category)
        print("New data loaded successfully into MongoDB!")
    except Exception as e:
        print(f"Error occurred while updating crops: {str(e)}")


def update_crops_data():
    collection = app.db["crops_options"]

    try:
        # קריאת הקובץ
        with open("app/static/data/crops_data.json", "r", encoding="utf-8") as file:
            crops_data = json.load(file)

        # מחיקת הנתונים הקיימים
        deleted_count = collection.delete_many({}).deleted_count
        print(f"{deleted_count} documents deleted from MongoDB.")

        # הוספת הנתונים המעודכנים
        for category in crops_data:
            collection.insert_one(category)
        print("New data loaded successfully into MongoDB!")
    except Exception as e:
        print(f"Error occurred while updating crops: {str(e)}")


def update_israel_cities():
    collection = app.db["israel_cities"]  # שם האוסף לערים בישראל

    try:
        # קריאת הקובץ JSON עם רשימת הערים
        with open("app/static/data/israel_cities.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            cities = data["israel_cities"]  # גישה לרשימת הערים בקובץ JSON

        # מחיקת הנתונים הקיימים (אם קיימים)
        deleted_count = collection.delete_many({}).deleted_count
        print(f"{deleted_count} documents deleted from MongoDB.")

        # הכנסה של כל הערים לטבלה
        collection.insert_one({"cities": cities})
        print("Israel cities updated successfully in MongoDB!")

    except Exception as e:
        print(f"Error occurred while updating Israel cities: {str(e)}")

@app.template_filter('hebrew_month')
def hebrew_month_filter(month_str):
    try:
        year, month = map(int, month_str.split('-'))
        return f"{HEBREW_MONTHS[month]} {year}"
    except:
        return month_str


@app.route("/")
def home():
    session.clear()  # מנקה את הסשן
    return render_template("index.html")


if __name__ == "__main__":
    # update_crops_data()
    # update_israel_cities()
    app.run(debug=True)
