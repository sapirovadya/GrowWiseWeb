from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import pymongo
from modules.users.employee.models import Employee

employee_bp = Blueprint('employee_bp', __name__)

# התחברות ל-MongoDB
client = pymongo.MongoClient("mongodb+srv://111sapir1115:SM123456!@growwise.3xwf5.mongodb.net/?retryWrites=true&w=majority&tls=true")
db = client.get_database("dataGrow")

@employee_bp.route("/employeepage", methods=['GET'])
def employee_home_page():
    return render_template("employee_home_page.html")