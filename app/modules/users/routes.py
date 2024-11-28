from flask import Blueprint, render_template, request, redirect, url_for, session
import pymongo
from modules.users.models import User

users_bp_main = Blueprint('users_bp_main', __name__)
client = pymongo.MongoClient("mongodb+srv://111sapir1115:SM123456!@growwise.3xwf5.mongodb.net/?retryWrites=true&w=majority&appName=growwise")
db = client.get_database("dataGrow")

@users_bp_main.route("/home", methods=['GET'])
def Home():
    return render_template("index.html")

@users_bp_main.route("/signup", methods=['GET'])
def signup_form():
    return redirect(url_for("users_bp_main.Home"))

# @users_bp_main.route("/signup", methods=['POST'])
# def signup():
#     # קבלת נתונים מהטופס
#     username = request.form.get("username")
#     password = request.form.get("password")

#     # if not username or not password:
#     #     flash("Both username and password are required.", "error")
#     #     return redirect(url_for("users_bp_main.signup_form"))

#     # # בדיקה אם המשתמש כבר קיים
#     # existing_user = db.users.find_one({"username": username})
#     # if existing_user:
#     #     flash("Username already exists. Please choose another.", "error")
#     #     return redirect(url_for("users_bp_main.signup_form"))

#     # הוספת המשתמש לבסיס הנתונים
#     db.users.insert_one({"username": username, "password": password})
#     flash("Signup successful!", "success")
#     return redirect(url_for("users_bp_main.Home"))


@users_bp_main.route("/signup", methods=['POST'])
def signup():
    # קבלת נתונים מהטופס
    username = request.form.get("username")
    password = request.form.get("password")

    # שמירת המשתמש בבסיס הנתונים
    db.users.insert_one({"username": username, "password": password})

    # חזרה לעמוד הנוכחי
    return redirect(url_for("home")) 