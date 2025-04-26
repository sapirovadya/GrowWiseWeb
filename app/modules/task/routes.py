from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv
import os
from modules.task.models import task


task_bp = Blueprint('task_bp', __name__, url_prefix='/task')

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

@task_bp.route('/tasks', methods=['POST'])
def save_task():
    email = session["email"]
    role = session["role"]
    if role == "manager":
        try:
            # קריאת הנתונים מהבקשה
            task_data = request.get_json()

            # יצירת משימה חדשה
            new_task = task().new_task({
                "giver_email": email,
                "employee_email": task_data.get("employee_email"),
                "task_name": task_data.get("task_name"),
                "task_content": task_data.get("task_content"),
                "due_date": task_data.get("due_date"),
                "status": "in_progress"  # ברירת מחדל
            })

            # שמירה בבסיס הנתונים
            db.task.insert_one(new_task)

            return jsonify({"message": "המשימה נשמרה בהצלחה."})
        except Exception as e:
            print(f"Error saving task: {e}")
            return jsonify({"message": "שגיאה בשמירת המשימה."}), 500
    if role == "co_manager":
        try:
            # קריאת הנתונים מהבקשה
            task_data = request.get_json()

            # יצירת משימה חדשה
            new_task = task().new_task({
                "giver_email": session.get("manager_email"),
                "employee_email": task_data.get("employee_email"),
                "task_name": task_data.get("task_name"),
                "task_content": task_data.get("task_content"),
                "due_date": task_data.get("due_date"),
                "status": "in_progress"  # ברירת מחדל
            })

            # שמירה בבסיס הנתונים
            db.task.insert_one(new_task)

            return jsonify({"message": "המשימה נשמרה בהצלחה."})
        except Exception as e:
            print(f"Error saving task: {e}")
            return jsonify({"message": "שגיאה בשמירת המשימה."}), 500

@task_bp.route('/alltasks', methods=['GET'])
def get_tasks():
    if 'email' not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 401

    user_email = session['email']
    role = session['role']

    if role in ["manager", "co_manager"]:
        # אם מנהל — משתמש ב-manger_email של עצמו
        manager_email = user_email if role == "manager" else session.get("manager_email")

        tasks = list(db["task"].find({"giver_email": manager_email}))

        # שליפת עובדים קיימים בלבד
        existing_employees_cursor = db["employee"].find({})
        existing_emails = {emp["email"]: f"{emp['first_name']} {emp['last_name']}" for emp in existing_employees_cursor}

        result = []
        for task in tasks:
            employee_email = task.get("employee_email")
            # מציגים רק אם העובד עדיין קיים
            if employee_email in existing_emails:
                result.append({
                    "employee_name": existing_emails[employee_email],
                    "task_name": task["task_name"],
                    "task_content": task["task_content"],
                    "due_date": task["due_date"],
                    "status": task["status"]
                })

        return jsonify(result)

    elif role == "employee":
        tasks = list(db["task"].find({"employee_email": user_email}))

        result = []
        for task in tasks:
            result.append({
                "employee_name": "אתה",
                "task_name": task["task_name"],
                "task_content": task["task_content"],
                "due_date": task["due_date"],
                "status": task["status"]
            })

        return jsonify(result)


@task_bp.route('/alltasks.html', methods=['GET'])
def render_all_tasks():
    return render_template('all_tasks.html')