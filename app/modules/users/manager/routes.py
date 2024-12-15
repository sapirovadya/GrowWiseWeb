from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from flask import flash
from modules.users.manager.models import Manager
from modules.Plots.models import Plot


load_dotenv()

manager_bp = Blueprint('manager_bp', __name__, url_prefix='/users/manager')

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

@manager_bp.route("/myteam", methods=['GET'])
def get_employees_list():
    email = session.get('email')  # אימייל של המנהל המחובר
    role = session.get('role')  # אימייל של המנהל המחובר
    if role == "manager":
        # שאיבת נתונים של עובדי employee ו-co_manager השייכים למנהל המחובר
        employees = db.employee.find({"manager_email": email})
        co_managers = db.co_manager.find({"manager_email": email})

        # המרת הנתונים לרשימה, כולל כל השדות הדרושים
        employee_list = [
            {
                "id": str(emp["_id"]),
                "first_name": emp["first_name"],
                "last_name": emp["last_name"],
                "email": emp.get("email", ""),
                "role": emp.get("role", ""),
                "is_approved": emp.get("is_approved", 0)
            }
            for emp in employees
        ]

        co_manager_list = [
            {
                "id": str(cm["_id"]),
                "first_name": cm["first_name"],
                "last_name": cm["last_name"],
                "email": cm.get("email", ""),
                "role": cm.get("role", "co_manager"),
                "is_approved": cm.get("is_approved", 0)
            }
            for cm in co_managers
        ]

        # איחוד הרשימות
        combined_list = employee_list + co_manager_list

        # שליחת הנתונים לדף ה-HTML
        return render_template('my_team.html', employees=combined_list)
    else:
        manager_email = session.get('manager_email')
        employees = db.employee.find({"manager_email": manager_email})
        co_managers = db.co_manager.find({"manager_email": manager_email})

        # המרת הנתונים לרשימה, כולל כל השדות הדרושים
        employee_list = [
            {
                "id": str(emp["_id"]),
                "first_name": emp["first_name"],
                "last_name": emp["last_name"],
                "email": emp.get("email", ""),
                "role": emp.get("role", ""),
                "is_approved": emp.get("is_approved", 0)
            }
            for emp in employees
        ]

        co_manager_list = [
            {
                "id": str(cm["_id"]),
                "first_name": cm["first_name"],
                "last_name": cm["last_name"],
                "email": cm.get("email", ""),
                "role": cm.get("role", "co_manager"),
                "is_approved": cm.get("is_approved", 0)
            }
            for cm in co_managers
        ]

        # איחוד הרשימות
        combined_list = employee_list + co_manager_list

        # שליחת הנתונים לדף ה-HTML
        return render_template('my_team.html', employees=combined_list)

# פונקציה לשינוי is_approved ל-1
@manager_bp.route('/approve_user/<user_id>', methods=['POST'])
def approve_user(user_id):
    try:
        # עדכון שדה is_approved ל-1
        result = db.employee.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_approved': 1}})
        if result.matched_count > 0:
            return jsonify({'message': 'המשתמש אושר בהצלחה'}), 200
        else:
            return jsonify({'message': 'שגיאה: משתמש לא נמצא'}), 404
    except Exception as e:
        return jsonify({'message': 'שגיאה בשרת', 'error': str(e)}), 500

# פונקציה למחיקת משתמש
@manager_bp.route('/reject_user/<user_id>', methods=['DELETE'])
def reject_user(user_id):
    try:
        # מחיקת משתמש מבסיס הנתונים
        result = db.employee.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'המשתמש הוסר בהצלחה'}), 200
        else:
            return jsonify({'message': 'שגיאה: משתמש לא נמצא'}), 404
    except Exception as e:
        return jsonify({'message': 'שגיאה בשרת', 'error': str(e)}), 500

@manager_bp.route('/deleteuser/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        result = db.employee.delete_one({'_id': ObjectId(user_id)})
        if result.deleted_count > 0:
            return jsonify({'message': 'המשתמש הוסר בהצלחה'}), 200
        else:
            return jsonify({'message': 'שגיאה: משתמש לא נמצא'}), 404
    except Exception as e:
        return jsonify({'message': 'שגיאה בשרת', 'error': str(e)}), 500
