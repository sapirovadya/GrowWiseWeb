from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session,current_app
import pymongo
from dotenv import load_dotenv
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User
from modules.users.manager.models import Manager  # וודא שזה הנתיב הנכון למחלקה Manager
from modules.users.employee.models import Employee
from modules.users.co_manager.models import Co_Manager
from modules.users.job_seeker.models import Job_Seeker
from modules.task.models import task
from modules.users.models import Notification



load_dotenv()

# הגדרת ה-Blueprint
users_bp_main = Blueprint('users_bp_main', __name__)
logout_bp = Blueprint('logout_bp', __name__)

# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
cities_collection = db.israel_cities  # שם האוסף


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
            return jsonify({"message": "All fields are required"}), 400

        if db.manager.find_one({"email": email}) or db.employee.find_one({"email": email}) or db.co_manager.find_one({"email": email}) or db.job_seeker.find_one({"email": email}):
            return jsonify({"message": "Email already exists. Please use a different email"}), 400

        # הצפנת סיסמה
        hashed_password = generate_password_hash(password)

        if role == "manager":
            user = Manager().signup(data)
            user["password"] = hashed_password
            db.manager.insert_one(user)
            return jsonify({"message": "תהליך רישום המנהל עבר בהצלחה"}), 200

        elif role == "employee" or role == "co_manager":
            if not manager_email:
                return jsonify({"message": "Manager email is required for workers"}), 400

            manag = db.manager.find_one({"email": manager_email, "role": "manager"})
            if not manag:
                return jsonify({"message": "Manager email not found. Please provide a valid manager email"}), 400

            if role == "employee":
                db.manager.update_one({"email": manager_email}, {"$addToSet": {"workers": email}})
                user = Employee().signup(data)
                user["password"] = hashed_password
                db.employee.insert_one(user)
                return jsonify({"message": "תהליך רישום העובד עבר בהצלחה"}), 200
            
            if role == "co_manager":
                db.manager.update_one({"email": manager_email}, {"$addToSet": {"co_managers": email}})
                user = Co_Manager().signup(data)
                user["password"] = hashed_password
                db.co_manager.insert_one(user)
                return jsonify({"message": "תהליך רישום השותף עבר בהצלחה"}), 200
        
        elif  role == "job_seeker":
            user = Job_Seeker().signup(data)
            user["password"] = hashed_password
            db.job_seeker.insert_one(user)
            return jsonify({"message": "תהליך רישום מחפש התנדבות עבר בהצלחה"}), 200

        return jsonify({"message": "Invalid role provided"}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Failed to register user. Please try again later"}), 500


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
            session['role'] = 'manager'
            

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
            session['role'] = 'co_manager'
            session['manager_email'] = co_manager.get('manager_email')

            return jsonify({
                "message": "login successfuly",
                "role": "manager",
                "redirect_url": url_for('co_manager_bp.co_manager_home_page')
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
            session['role'] = 'employee'
            session['name'] = employee.get('first_name')
            session['manager_email'] = employee.get('manager_email')

            return jsonify({
                "message": "login successfuly",
                "role": "employee",
                "redirect_url": url_for('employee_bp.employee_home_page')
            }), 200

        job_seeker = db.job_seeker.find_one({"email": email})
        if job_seeker:
            # בדיקת סיסמה
            if not check_password_hash(job_seeker["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
            session['email'] = email
            session['name'] = job_seeker.get('first_name')
            session['role'] = 'job_seeker'
            

            return jsonify({
                "message": "login successfuly",
                "role": "job_seeker",
                "redirect_url": url_for('job_seeker_bp.job_seeker_home_page')
            }), 200
        
        # אם המשתמש לא נמצא בשום collection
        return jsonify({"message": "user not found"}), 400

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "שגיאה במהלך ההתחברות. נסה שוב מאוחר יותר."}), 500

@users_bp_main.route('/profile', methods=['GET'])
def profile_page():
    # נשלוף את נתוני המשתמש מהסשן או מבסיס הנתונים
    user_email = session.get('email')
    role = session.get('role')
    if role == "manager":
        user = db.manager.find_one({"email": user_email})
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('manager_bp.manager_home_page'))
    elif role == "co_manager":
        user = db.co_manager.find_one({"email": user_email})  # נתוני המשתמש
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('co_manager_bp.co_manager_home_page'))
    else:
        user = db.employee.find_one({"email": user_email})  # נתוני המשתמש
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('employee_bp.employee_home_page'))

@users_bp_main.route('/save_profile', methods=['POST'])
def save_profile():
    # עדכון נתוני המשתמש
    role = session.get('role')
    user_email = session.get('email')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    location = request.form.get('location')

    if role == "manager":
        try:
            db.manager.update_one({"email": user_email}, {"$set": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "location": location
            }})
              # עדכון השדות "manager_email" ב-co_managers וב-workers
            db.co_manager.update_many({"manager_email": user_email}, {"$set": {"manager_email": email}})
            db.employee.update_many({"manager_email": user_email}, {"$set": {"manager_email": email}})
            
            session['email'] = email  # עדכון סשן אם האימייל השתנה
            return jsonify({"message": "הפרטים עודכנו בהצלחה."})
        except Exception as e:
            print(e)
            return jsonify({"message": "שגיאה בעדכון הפרטים."}), 500
    elif role == "co_manager":
        try:
            db.co_manager.update_one({"email": user_email}, {"$set": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }})
            db.manager.update_many({"co_managers": user_email}, {"$set": {"co_managers": email}})

            session['email'] = email  # עדכון סשן אם האימייל השתנה
            return jsonify({"message": "הפרטים עודכנו בהצלחה."})
        except Exception as e:
            print(e)
            return jsonify({"message": "שגיאה בעדכון הפרטים."}), 500
    else: 
        try:
            db.employee.update_one({"email": user_email}, {"$set": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            }})
            db.manager.update_many({"workers": user_email}, {"$set": {"workers": email}})

            session['email'] = email  # עדכון סשן אם האימייל השתנה
            return jsonify({"message": "הפרטים עודכנו בהצלחה."})
        except Exception as e:
            print(e)
            return jsonify({"message": "שגיאה בעדכון הפרטים."}), 500


@users_bp_main.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        # לוגיקה לשינוי סיסמה
        pass
    return render_template('change_password.html')


@users_bp_main.route("/get_notifications", methods=["GET"])
def get_notifications():
    try:
        # שליפת המידע מהסשן
        role = session.get("role")
        email = session.get("email")

        # רשימת ההתראות
        notifications = []

        # בדיקת תאריך נוכחי
        today = datetime.now().isoformat()[:10]

        # לוגיקה להוספת התראות חדשות לפי תפקיד
        if role == "manager":
            add_manager_notifications(email, today)

        elif role == "employee":
            add_employee_notifications(email)

        # שליפת התראות קיימות מהמנוע ומיון לפי זמן יצירתן
        db_notifications = db.notifications.find({"email": email}).sort("created_at", -1)
        for notification in db_notifications:
            notifications.append({
                "content": notification["content"],
                "employee_email": notification.get("employee_email"),
                "seen": notification.get("seen", False),
                "created_at": notification["created_at"].strftime("%d-%m-%Y %H:%M:%S")
            })

        # ספירת התראות חדשות (לא נצפו)
        new_notifications_count = db.notifications.count_documents({"email": email, "seen": False})

        return jsonify({
            "notifications": notifications,
            "new_notifications_count": new_notifications_count
        }), 200

    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({"notifications": [], "message": "שגיאה בטעינת ההתראות."}), 500

def add_manager_notifications(email, today):
    """לוגיקה להוספת התראות חדשות למנהלים"""
    try:
        # התראות על עובדים שטרם אושרו
        employees = db.employee.find({"manager_email": email, "is_approved": 0})
        for employee in employees:
            content = f"עובד בשם {employee['first_name']} {employee['last_name']} מחכה לאישור."
            add_notification(email, employee['email'], content)

        # התראות על שותפים שטרם אושרו
        co_managers = db.co_manager.find({"manager_email": email, "is_approved": 0})
        for co_manager in co_managers:
            content = f"שותף בשם {co_manager['first_name']} {co_manager['last_name']} מחכה לאישור."
            add_notification(email, co_manager['email'], content)

        # התראות על משימות שעבר זמנן
        overdue_tasks = db.task.find({
            "giver_email": email,
            "status": "in_progress",
            "due_date": {"$lt": today}
        })
        for task in overdue_tasks:
            content = f"ישנה משימה שטרם בוצעה ועבר התאריך המוגדר לביצועה\nנושא: {task['task_name']}."
            add_notification(email, task["employee_email"], content)

    except Exception as e:
        print(f"Error adding manager notifications: {e}")


def add_employee_notifications(email):
    try:
        # התראות על משימות חדשות
        assigned_tasks = db.task.find({
            "employee_email": email,
            "status": "in_progress"
        })
        for task in assigned_tasks:
            content = f"נוספה לך משימה חדשה\nנושא: {task['task_name']}."
            add_notification(email, task["employee_email"], content)
    except Exception as e:
        print(f"Error adding employee notifications: {e}")

def add_notification(email, employee_email, content):
    """הוספת התראה חדשה אם אינה קיימת"""
    try:
        existing_notification = db.notifications.find_one({
            "email": email,
            "employee_email": employee_email,
            "content": content
        })
        if not existing_notification:
            notification = Notification(email, employee_email, content)
            db.notifications.insert_one(notification.to_dict())
    except Exception as e:
        print(f"Error adding notification: {e}")

@users_bp_main.route("/mark_notifications_seen", methods=["POST"])
def mark_notifications_seen():
    email = session.get("email")
    try:
        db.notifications.update_many(
            {"email": email, "seen": False},
            {"$set": {"seen": True}}
        )
        return jsonify({"message": "Notifications marked as seen"}), 200
    except Exception as e:
        print(f"Error marking notifications as seen: {e}")
        return jsonify({"message": "Failed to mark notifications as seen"}), 500


@users_bp_main.route('/get_cities', methods=['GET'])
def get_cities():
    try:
        # שליפת המסמך הראשון באוסף שמכיל את המערך 'cities'
        document = cities_collection.find_one({}, {"_id": 0, "cities": 1})
        if not document or "cities" not in document:
            return jsonify({"error": "Cities data not found"}), 404

        city_list = document["cities"]  # שליפת רשימת הערים מתוך המערך
        return jsonify(city_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@users_bp_main.route('/about', methods=['GET'])
def about_us():
    return render_template('about_us.html')

@users_bp_main.route('/logout', methods=['POST'])
def logout():
    session.clear()  # מנקה את הסשן
    return redirect(url_for('home'))  # מפנה לדף הבית

@users_bp_main.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')