from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session,current_app, flash
import pymongo
from dotenv import load_dotenv
from datetime import datetime,timedelta
import os
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User
from modules.users.manager.models import Manager  
from modules.users.employee.models import Employee
from modules.users.co_manager.models import Co_Manager
from modules.users.job_seeker.models import Job_Seeker
from modules.task.models import task
from modules.users.models import Notification
from flask_dance.contrib.google import google
from flask_mail import Mail, Message
from pymongo import MongoClient


load_dotenv()

users_bp_main = Blueprint('users_bp_main', __name__,  url_prefix="/users")
logout_bp = Blueprint('logout_bp', __name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
cities_collection = db.israel_cities  

@users_bp_main.route("/google_login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "שגיאה באימות Google", 400

    user_info = resp.json()
    email = user_info.get("email")
    first_name = user_info.get("given_name")
    last_name = user_info.get("family_name")

    user = db.manager.find_one({"email": email})
    if user:
        session.update({
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": "manager",
            "is_google_login": True
        })
        return redirect(url_for("manager_bp.manager_home_page"))

    user = db.co_manager.find_one({"email": email})
    if user:
        if user["is_approved"] == 0:
            return jsonify({"message": "user is not approved"}), 400
        session.update({
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": "co_manager",
            "manager_email": user.get("manager_email", ""),
            "is_google_login": True
        })
        return redirect(url_for("co_manager_bp.co_manager_home_page"))

    user = db.employee.find_one({"email": email})
    if user:  
        if user["is_approved"] == 0:
            return jsonify({"message": "user is not approved"}), 400
        session.update({
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": "employee",
            "manager_email": user.get("manager_email", ""),
            "is_google_login": True
        })
        return redirect(url_for("employee_bp.employee_home_page"))

    user = db.job_seeker.find_one({"email": email})
    if user:
        session.update({
            "email": user["email"],
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "role": "job_seeker",
            "is_google_login": True
        })
        return redirect(url_for("job_seeker_bp.job_seeker_home_page"))

  
    session.update({
        "email": email,
        "first_name": first_name,
        "last_name": last_name
    })
    return redirect(url_for("users_bp_main.google_register_form"))


@users_bp_main.route("/google_register_form")
def google_register_form():
    if "email" not in session:
        return redirect(url_for("home"))
    return render_template("google_register.html", 
                           email=session["email"],
                           first_name=session["first_name"],
                           last_name=session["last_name"])


@users_bp_main.route("/google_signup", methods=["POST"])
def google_signup():
    db = current_app.db
    data = request.get_json()
    email = session.get("email")

 
    existing = (
        db.manager.find_one({"email": email}) or
        db.co_manager.find_one({"email": email}) or
        db.employee.find_one({"email": email}) or
        db.job_seeker.find_one({"email": email})
    )
    if existing:
        return jsonify({"success": False, "message": "המשתמש כבר קיים במערכת"}), 400


    role = data.get("role")
    manager_email = data.get("manager_email", "")
    location = data.get("location", "")

    user_data = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": email,
        "role": role,
        "manager_email": manager_email,
        "location": location
    }

 
    if role in ["employee", "co_manager"]:
        manager = db.manager.find_one({"email": manager_email})
        if not manager:
            return jsonify({"success": False, "message": "אימייל המנהל אינו קיים במערכת"}), 400


    if role == "manager":
        user = Manager().signup(user_data)
        db.manager.insert_one(user)
        session["role"] = "manager"
        session["manager_email"] = email

    elif role == "co_manager":
        user = Co_Manager().signup(user_data)
        db.co_manager.insert_one(user)
        db.manager.update_one({"email": manager_email}, {"$addToSet": {"co_managers": email}})
        session["role"] = "co_manager"
        session["manager_email"] = manager_email

    elif role == "employee":
        user = Employee().signup(user_data)
        db.employee.insert_one(user)
        db.manager.update_one({"email": manager_email}, {"$addToSet": {"workers": email}})
        session["role"] = "employee"
        session["manager_email"] = manager_email

    elif role == "job_seeker":
        user = Job_Seeker().signup(user_data)
        db.job_seeker.insert_one(user)
        session["role"] = "job_seeker"

    else:
        return jsonify({"success": False, "message": "תפקיד לא חוקי"}), 400


 
    session["user_id"] = user["id"]
    session["first_name"] = user["first_name"]
    session["last_name"] = user["last_name"]
    session["email"] = user["email"]
    session["is_google_login"] = True


    redirect_map = {
        "manager": "manager_bp.manager_home_page",
        "co_manager": "home",
        "employee": "home",
        "job_seeker": "home"
    }

    return jsonify({
    "success": True,
    "message": "ההרשמה הושלמה בהצלחה!",
    "redirect_url": redirect_map.get(role, url_for("home"))
})




@users_bp_main.route("/register", methods=['GET'])
def register():
    return render_template("Register.html")

@users_bp_main.route("/signup", methods=['POST'])
def signup():
    try:

        db = current_app.db
        data = request.get_json()  
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role")
        manager_email = data.get("manager_email")

        
        if not all([first_name, last_name, email, password, role]):
            return jsonify({"message": "All fields are required"}), 400

        if db.manager.find_one({"email": email}) or db.employee.find_one({"email": email}) or db.co_manager.find_one({"email": email}) or db.job_seeker.find_one({"email": email}):
            return jsonify({"message": "Email already exists. Please use a different email"}), 400

      
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
        
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        
        manager = db.manager.find_one({"email": email})
        if manager:
           
            if not check_password_hash(manager["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
          
            session['email'] = email
            session['first_name'] = manager.get('first_name')
            session['last_name'] = manager.get('last_name')
            session['role'] = 'manager'
            

            return jsonify({
                "message": "login successfuly",
                "role": "manager",
                "redirect_url": url_for('manager_bp.manager_home_page')
            }), 200
        
        co_manager = db.co_manager.find_one({"email": email})
        if co_manager:
           
            if not check_password_hash(co_manager["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
            if co_manager["is_approved"] == 0:
                return jsonify({"message": "user is not approved"}), 400

          
            session['email'] = email
            session['first_name'] = co_manager.get('first_name')
            session['last_name'] = co_manager.get('last_name')
            session['role'] = 'co_manager'
            session['manager_email'] = co_manager.get('manager_email')

            return jsonify({
                "message": "login successfuly",
                "role": "manager",
                "redirect_url": url_for('co_manager_bp.co_manager_home_page')
            }), 200


        
        employee = db.employee.find_one({"email": email})
        if employee:
           
            if not check_password_hash(employee["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400

           
            if employee["is_approved"] == 0:
                return jsonify({"message": "user is not approved"}), 400

          
            session['email'] = email
            session['role'] = 'employee'
            session['first_name'] = employee.get('first_name')
            session['last_name'] = employee.get('last_name')
            session['manager_email'] = employee.get('manager_email')

            return jsonify({
                "message": "login successfuly",
                "role": "employee",
                "redirect_url": url_for('employee_bp.employee_home_page')
            }), 200

        job_seeker = db.job_seeker.find_one({"email": email})
        if job_seeker:
           
            if not check_password_hash(job_seeker["password"], password):
                return jsonify({"message": "one of the detail is incorrect"}), 400
            
            session['email'] = email
            session['first_name'] = job_seeker.get('first_name')
            session['last_name'] = job_seeker.get('last_name')
            session['role'] = 'job_seeker'
            

            return jsonify({
                "message": "login successfuly",
                "role": "job_seeker",
                "redirect_url": url_for('job_seeker_bp.job_seeker_home_page')
            }), 200
        
       
        return jsonify({"message": "user not found"}), 400

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "שגיאה במהלך ההתחברות. נסה שוב מאוחר יותר."}), 500

@users_bp_main.route('/profile', methods=['GET'])
def profile_page():
    
    user_email = session.get('email')
    role = session.get('role')

    if role == "manager":
        user = db.manager.find_one({"email": user_email})
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('manager_bp.manager_home_page'))  
    elif role == "co_manager":
        user = db.co_manager.find_one({"email": user_email})  
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('co_manager_bp.co_manager_home_page'))  
    elif role == "employee":
        user = db.employee.find_one({"email": user_email})  
        if user:
            return render_template('profile.html', user=user)
        else:
            return redirect(url_for('employee_bp.employee_home_page'))  
    else:
        return redirect(url_for('home')) 


@users_bp_main.route('/save_profile', methods=['POST'])
def save_profile():
  
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

            db.co_manager.update_many({"manager_email": user_email}, {"$set": {"manager_email": email}})
            db.employee.update_many({"manager_email": user_email}, {"$set": {"manager_email": email}})
            
            session['email'] = email  
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

            session['email'] = email 
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

            session['email'] = email  
            return jsonify({"message": "הפרטים עודכנו בהצלחה."})
        except Exception as e:
            print(e)
            return jsonify({"message": "שגיאה בעדכון הפרטים."}), 500


@users_bp_main.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        pass
    return render_template('change_password.html')


def add_vehicle_notifications():
    try:
        today = datetime.today()

        vehicles = db.vehicles.find()

        for vehicle in vehicles:
            email = vehicle.get("manager_email")
            vehicle_number = vehicle.get("vehicle_number")          
            test_date_str = vehicle.get("test_date")
            if test_date_str:
                try:
                    test_date = datetime.strptime(test_date_str, "%Y-%m-%d") 
                    next_test_date = test_date.replace(year=test_date.year)  
                    alert_start_date = next_test_date - timedelta(days=30)  
                    if alert_start_date <= today < next_test_date:
                        content = f"טסט הרכב עם מספר {vehicle_number} עומד להסתיים בתאריך {next_test_date.strftime('%d-%m-%Y')}. נא לחדש בהקדם."
                        add_notification(email, None, content)
                except ValueError:
                    print(f"שגיאה בהמרת test_date עבור הרכב {vehicle_number}: {test_date_str}")

            insurance_date_str = vehicle.get("insurance_date")
            if insurance_date_str:
                try:
                    insurance_date = datetime.strptime(insurance_date_str, "%Y-%m-%d") 
                    next_insurance_date = insurance_date.replace(year=insurance_date.year)
                    alert_start_date = next_insurance_date - timedelta(days=30)
                    if alert_start_date <= today < next_insurance_date:
                        content = f"ביטוח הרכב עם מספר {vehicle_number} עומד להסתיים בתאריך {next_insurance_date.strftime('%d-%m-%Y')}. נא לחדש בהקדם."
                        add_notification(email, None, content)
                except ValueError:
                    print(f"שגיאה בהמרת insurance_date עבור הרכב {vehicle_number}: {insurance_date_str}")

    except Exception as e:
        print(f"Error adding vehicle notifications: {e}")

def add_month_end_notification(email):
    try:

        today = datetime(2025, 3, 31)
        tomorrow = today + timedelta(days=1)
        if tomorrow.month != today.month:
            existing = db.notifications.find_one({
                "email": email,
                "content": "יש לעבור על דיווח נוכחות עובדים",
                "created_at": {"$gte": today.replace(hour=0, minute=0, second=0), "$lt": today.replace(hour=23, minute=59, second=59)}
            })
            if not existing:
                add_notification(email, None, "לתשומת ליבך – סוף החודש הגיע. נא לבדוק ולעדכן את דיווחי הנוכחות של העובדים במערכת")
    except Exception as e:
        print(f"שגיאה ביצירת התראת סוף חודש: {e}")

def add_vehicle_management_notification(email):
    try:
        today = datetime.today()


        is_middle_of_month = today.day == 15
        is_end_of_month = (today + timedelta(days=1)).day == 1

        if is_middle_of_month or is_end_of_month:
   
            existing = db.notifications.find_one({
                "email": email,
                "content": "יש לעבור על ניהול כלי הרכב ולעדכן פרטים בהתאם.",
                "created_at": {
                    "$gte": today.replace(hour=0, minute=0, second=0),
                    "$lt": today.replace(hour=23, minute=59, second=59)
                }
            })
            if not existing:
                add_notification(email, None, "יש לעבור על ניהול כלי הרכב ולעדכן פרטים בהתאם.")

    except Exception as e:
        print(f"שגיאה ביצירת התראת ניהול כלי רכב: {e}")


@users_bp_main.route("/get_notifications", methods=["GET"])
def get_notifications():
    try:
       
        role = session.get("role")
        email = session.get("email")

        notifications = []

        today = datetime.now().isoformat()[:10]

        if role == "manager":
            add_manager_notifications(email, today)

        elif role == "employee":
            add_employee_notifications(email)

        add_vehicle_notifications()
        add_month_end_notification(email)
        add_vehicle_management_notification(email)
        

        db_notifications = db.notifications.find({"email": email}).sort("created_at", -1)
        for notification in db_notifications:
            notifications.append({
                "content": notification["content"],
                "employee_email": notification.get("employee_email"),
                "seen": notification.get("seen", False),
                "created_at": notification["created_at"].strftime("%d-%m-%Y %H:%M:%S")
            })


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
     
        employees = db.employee.find({"manager_email": email, "is_approved": 0})
        for employee in employees:
            content = f"עובד בשם {employee['first_name']} {employee['last_name']} מחכה לאישור."
            add_notification(email, employee['email'], content)

   
        co_managers = db.co_manager.find({"manager_email": email, "is_approved": 0})
        for co_manager in co_managers:
            content = f"שותף בשם {co_manager['first_name']} {co_manager['last_name']} מחכה לאישור."
            add_notification(email, co_manager['email'], content)

    
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
        
        document = cities_collection.find_one({}, {"_id": 0, "cities": 1})
        if not document or "cities" not in document:
            return jsonify({"error": "Cities data not found"}), 404

        city_list = document["cities"] 
        return jsonify(city_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@users_bp_main.route('/about', methods=['GET'])
def about_us():
    return render_template('about_us.html')

@users_bp_main.route('/logout', methods=['POST'])
def logout():
    session.clear() 
    return redirect(url_for('home'))  

@users_bp_main.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@users_bp_main.route('/info/<email>', methods=['GET'])
def get_user_info(email):
   
    collections = ["manager", "co_manager", "employee", "job_seeker"]

    user = None
    for collection_name in collections:
        collection = db[collection_name]
        user = collection.find_one({"email": email}, {"_id": 0, "first_name": 1, "last_name": 1, "role": 1, "manager_email": 1})
        if user:
            user["role"] = user.get("role", collection_name) 
            break 

    if not user:
        return jsonify({"error": "משתמש לא נמצא"}), 404

 
    role_texts = {
        "manager": "בעל משק חקלאי",
        "co_manager": "בעל משק חקלאי",
        "job_seeker": "מתנדב/מחפש עבודה",
        "employee": "עובד משק"
    }
    user["role_text"] = role_texts.get(user["role"], "משתמש רגיל")

 
    if user["role"] == "manager":
        user["location"] = db["manager"].find_one({"email": email}, {"_id": 0, "location": 1}) or {}
        user["location"] = user["location"].get("location", "לא צויין")

    
    elif user["role"] in ["co_manager", "employee"]:
        manager_email = user.get("manager_email")
        if manager_email:  
            manager = db["manager"].find_one({"email": manager_email}, {"_id": 0, "location": 1}) or {}
            user["location"] = manager.get("location", "לא צויין")

    return jsonify(user), 200



@users_bp_main.route("/forgot_password", methods=["POST"])
def forgot_password():
    from GrowWise import mail, s

    email = request.form.get("email")

    collections = {
        "manager": current_app.db["manager"],
        "co_manager": current_app.db["co_manager"],
        "employee": current_app.db["employee"],
        "job_seeker": current_app.db["job_seeker"]
    }

    user = None
    found_role = None

    for role, collection in collections.items():
        user = collection.find_one({"email": email})
        if user:
            found_role = role
            break

    if not user:
        flash("המייל לא נמצא במערכת", "danger")
        return redirect(url_for("home"))

    try:
        token = s.dumps({"email": email, "role": found_role}, salt="recover-password")
    except Exception as e:
        flash("שגיאה ביצירת קישור איפוס", "danger")
        return redirect(url_for("home"))

    try:
        link = url_for("users_bp_main.reset_password", token=token, _external=True)
    except Exception as e:
        flash("שגיאה ביצירת הקישור", "danger")
        return redirect(url_for("home"))

    msg = Message("שחזור סיסמה - GrowWisely",
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[email],
                  body=f"שלום,\n\nכדי לאפס את הסיסמה לחץ על הקישור הבא:\n{link}\n\nקישור זה בתוקף לשעה בלבד.")

    try:
        mail.send(msg)
    except Exception as e:
        flash("אירעה שגיאה בשליחת המייל. ודא שהמייל תקין.", "danger")
        return redirect(url_for("home"))

    flash("קישור לשחזור סיסמה נשלח למייל שלך", "info")
    return redirect(url_for("home"))



@users_bp_main.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    from GrowWise import s  

    try:
        data = s.loads(token, salt="recover-password", max_age=3600)
        email = data["email"]
        role = data["role"]
    except Exception as e:
        flash("הקישור אינו תקף או שפג תוקפו", "danger")
        return redirect(url_for("home"))

    collection_names = current_app.db.list_collection_names()
    if role not in collection_names:
        flash("שגיאה פנימית. לא נמצא סוג המשתמש.", "danger")
        return redirect(url_for("home"))

    collection = current_app.db[role]

    if request.method == "POST":
        new_password = request.form.get("password")
        if not new_password or len(new_password) < 6:
            flash("יש להזין סיסמה באורך של לפחות 6 תווים", "danger")
            return render_template("reset_password.html")

        hashed_password = generate_password_hash(new_password)
        result = collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

        if result.modified_count > 0:
            flash("הסיסמה עודכנה בהצלחה!", "success")
        else:
            flash("הסיסמה כבר הייתה זהה או לא בוצע שינוי", "info")

        return redirect(url_for("home"))

    return render_template("reset_password.html")

@users_bp_main.route("/update_password", methods=["POST"])
def update_password():
    try:
        data = request.get_json()
        email = session.get("email")
        role = session.get("role")

        if not email or not role:
            return jsonify({"message": "לא ניתן לאמת משתמש"}), 401

        collection = current_app.db[f"{role}"]

        hashed_password = generate_password_hash(data["password"])
        print("Trying to update password for:", email)
        result = collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
        print("Matched:", result.matched_count, "Modified:", result.modified_count)


        return jsonify({"message": "הסיסמה עודכנה בהצלחה!"}), 200

    except Exception as e:
        print("Error updating password:", str(e))
        return jsonify({"message": "אירעה שגיאה בעת עדכון הסיסמה."}), 500



