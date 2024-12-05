from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session,current_app
import pymongo
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User
from modules.users.manager.models import Manager  # וודא שזה הנתיב הנכון למחלקה Manager
from modules.users.employee.models import Employee
from modules.users.co_manager.models import Co_Manager


load_dotenv()

# הגדרת ה-Blueprint
users_bp_main = Blueprint('users_bp_main', __name__)

# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")


# הצגת טופס ההרשמה
@users_bp_main.route("/register", methods=['GET'])
def register():
    return render_template("Register.html")

@users_bp_main.route("/signup", methods=['POST'])
def signup():
    try:
        # קבלת נתונים מהטופס
        db = current_app.db
        data = request.get_json()  # קבלת הנתונים כ-JSON
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        manager_email = data.get("manager_email")

        # בדיקות שדות חובה
        if not all([first_name, last_name, email, password, role]):
            return jsonify({"message": "All fields are required!"}), 400

        if db.manager.find_one({"email": email}) or db.employee.find_one({"email": email}):
            return jsonify({"message": "Email already exists. Please use a different email."}), 400

        # הצפנת סיסמה
        hashed_password = generate_password_hash(password)

        if role == "manager":
            user = Manager().signup(data)
            user["password"] = hashed_password
            db.manager.insert_one(user)
            return jsonify({"message": "Manager registered successfully!"}), 200

        elif role == "employee" or role == "co_manager":
            if not manager_email:
                return jsonify({"message": "Manager email is required for workers!"}), 400

            manag = db.manager.find_one({"email": manager_email, "role": "manager"})
            if not manag:
                return jsonify({"message": "Manager email not found. Please provide a valid manager email."}), 400

            if role == "employee":
                db.manager.update_one({"email": manager_email}, {"$addToSet": {"workers": email}})
                user = Employee().signup(data)
                user["password"] = hashed_password
                db.employee.insert_one(user)
                return jsonify({"message": "Employee registered successfully!"}), 200
            
            if role == "co_manager":
                db.manager.update_one({"email": manager_email}, {"$addToSet": {"co_managers": email}})
                user = Co_Manager().signup(data)
                user["password"] = hashed_password
                db.co_manager.insert_one(user)
                return jsonify({"message": "Co-manager registered successfully!"}), 200
            
        return jsonify({"message": "Invalid role provided."}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Failed to register user. Please try again later."}), 500


@users_bp_main.route("/login", methods=['POST'])
def login():
    try:
        db = current_app.db 
        # קבלת נתוני התחברות
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        # בדיקה אם המשתמש קיים ב-collection של מנהלים
        manager = db.manager.find_one({"email": email})
        if manager:
            # בדיקת סיסמה
            if not check_password_hash(manager["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
            # מנהל נמצא ומאושר
            session['email'] = email
            session['name'] = manager.get('first_name')
            return jsonify({
                "message": "login successfuly",
                "role": "manager",
                "redirect_url": url_for('manager_bp.manager_home_page')
            }), 200
        
        co_manager = db.co_manager.find_one({"email": email})
        if co_manager:
            # בדיקת סיסמה
            if not check_password_hash(co_manager["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
            if co_manager["is_approved"] == 0:
                return jsonify({"message": "user is not approved"}), 400

            # מנהל נמצא ומאושר
            session['email'] = email
            session['name'] = co_manager.get('first_name')
            return jsonify({
                "message": "login successfuly",
                "role": "manager",
                "redirect_url": url_for('manager_bp.manager_home_page')
            }), 200


        # בדיקה אם המשתמש קיים ב-collection של עובדים
        employee = db.employee.find_one({"email": email})
        if employee:
            # בדיקת סיסמה
            if not check_password_hash(employee["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400

            # בדיקה אם העובד מאושר
            if employee["is_approved"] == 0:
                return jsonify({"message": "user is not approved"}), 400

            # עובד נמצא ומאושר
            session['email'] = email
            session['name'] = employee.get('first_name')
            return jsonify({
                "message": "login successfuly",
                "role": "employee",
                "redirect_url": url_for('employee_bp.employee_home_page')
            }), 200

        # אם המשתמש לא נמצא בשום collection
        return jsonify({"message": "user not found"}), 400

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "שגיאה במהלך ההתחברות. נסה שוב מאוחר יותר."}), 500
