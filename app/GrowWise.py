from flask import Flask,render_template, request, url_for, redirect,session
import pymongo
from dotenv import load_dotenv
import os
from modules.users.routes import users_bp_main
from modules.users.employee.routes import employee_bp
from modules.users.manager.routes import manager_bp
from modules.users.co_manager.routes import co_manager_bp

import json

load_dotenv()
app = Flask(__name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
app.db = client.get_database("dataGrow")

app.secret_key = os.getenv("APP_SECRET")

app.register_blueprint(users_bp_main, url_prefix='/users')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(manager_bp, url_prefix='/users/manager')
app.register_blueprint(co_manager_bp, url_prefix='/co_manager')




















def update_crops_data():
    collection = app.db["crops_options"]
    
    try:
        # קריאת הקובץ
        with open('app/static/data/crops_data.json', 'r', encoding='utf-8') as file:
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
        with open('app/static/data/crops_data.json', 'r', encoding='utf-8') as file:
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


@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    
    #update_crops_data()
    app.run(debug=True)