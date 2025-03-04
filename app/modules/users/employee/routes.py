from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from dotenv import load_dotenv
import os
from modules.users.employee.models import Employee



load_dotenv()

employee_bp = Blueprint('employee_bp', __name__)


# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

@employee_bp.route("/employeepage", methods=['GET'])
def employee_home_page():
    if 'email' not in session: 
        return redirect(url_for('users_bp_main.login')) 
    
    first_name = session.get('first_name') 
    return render_template("employee_home_page.html", first_name=first_name)


