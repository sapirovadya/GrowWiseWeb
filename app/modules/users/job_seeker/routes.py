from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from flask import flash
from modules.users.job_seeker.models import Job_Seeker

load_dotenv()

job_seeker_bp = Blueprint('job_seeker_bp', __name__, url_prefix='/job_seeker')

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

@job_seeker_bp.route("/jobseekerpage", methods=['GET'])
def job_seeker_home_page():
    if 'email' not in session:  # בדיקה אם המשתמש מחובר
        return redirect(url_for('users_bp_main.login'))  # אם לא, החזר לדף ההתחברות
    
    name = session.get('name')  # קבלת שם המנהל מה-session
    return render_template("job_seeker_home_page.html", name=name)
