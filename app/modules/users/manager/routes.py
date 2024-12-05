from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from dotenv import load_dotenv
import os
from modules.users.manager.models import Manager

load_dotenv()

manager_bp = Blueprint('manager_bp', __name__)

# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")


# @manager_bp.route("/managerpage", methods=['GET'])
# def manager_home_page():
#     return render_template("manager_home_page.html")

@manager_bp.route("/managerpage", methods=['GET'])
def manager_home_page():
    if 'email' not in session:  # בדיקה אם המשתמש מחובר
        return redirect(url_for('users_bp_main.login'))  # אם לא, החזר לדף ההתחברות
    
    name = session.get('name')  # קבלת שם המנהל מה-session
    return render_template("manager_home_page.html", name=name)


@manager_bp.route("/track_greenhouse", methods=['GET'])
def track_greenhouse():
    # if 'email' not in session:  # בדיקה אם המשתמש מחובר
    #     return redirect(url_for('users_bp_main.login'))  # אם לא, החזר לדף ההתחברות
    return render_template("track_greenhouse.html")  # הצגת הדף של מעקב חממות