from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz
from modules.attendance.models import attendance
from bson import ObjectId

attendance_bp = Blueprint('attendance_bp', __name__, url_prefix='/attendance')

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
attendance_collection = db.attendance
attendance_model = attendance()

@attendance_bp.route('/report_page', methods=['GET'])
def report_attendance_page():
    return render_template('attendance.html')


@attendance_bp.route('/report', methods=['POST'])
def report_attendance():

    if 'email' not in session or session.get('role') != 'employee':
        return jsonify({'message': 'גישה נדחתה'}), 403

    data = request.json
    employee_email = session['email']
    first_name = session.get('first_name')
    last_name = session.get('last_name')
    manager_email = session.get('manager_email')
    action = data.get('action')

    if action == 'check_in':
        check_in_time = datetime.now() #convert time
        new_attendance = {
            "email": employee_email,
            "manager_email": manager_email,
            "first_name": first_name,
            "last_name": last_name,
            "check_in": check_in_time, 
            "check_out": None,
            "total_hours": None
        }
        result = attendance_collection.insert_one(new_attendance)
        return jsonify({
            'message': 'שעת הכניסה נשמרה בהצלחה',
            'check_in': check_in_time,
            'inserted_id': str(result.inserted_id)
        })


    elif action == 'check_out':
        last_record = attendance_collection.find_one({"email": employee_email, "check_out": None})

        if not last_record:
            return jsonify({'message': 'לא נמצאה כניסה פתוחה'})

        check_out_time = datetime.now()
        check_in_time = last_record["check_in"]
        total_hours = (check_out_time - check_in_time).total_seconds() / 3600.0

        attendance_collection.update_one(
            {"_id": last_record["_id"]},
            {"$set": {"check_out": check_out_time, "total_hours": round(total_hours, 2)}}
        )

        return jsonify({'message': f'שעת היציאה נשמרה, סה"כ {total_hours:.2f} שעות עבודה', 'check_out': check_out_time})

    return jsonify({'message': 'פעולה לא חוקית'}), 400



@attendance_bp.route('/user_records', methods=['GET'])
def get_user_attendance():
    if 'email' not in session or session.get('role') != 'employee':
        return jsonify({'message': 'גישה נדחתה'}), 403

    employee_email = session['email']

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # records = list(attendance_collection.find({"email": employee_email}, {"_id": 0}))
    
    records = list(attendance_collection.find({
        "email": employee_email,
        "check_in": {
            "$gte": datetime(current_year, current_month, 1), 
            "$lt": datetime(current_year, current_month + 1, 1) if current_month < 12 
                else datetime(current_year + 1, 1, 1)
        }
    }))
    
    for record in records:
        record['_id'] = str(record['_id'])
        if "check_in" in record and record["check_in"]:
            record["check_in"] = record["check_in"].strftime("%Y-%m-%d %H:%M:%S")
        if "check_out" in record and record["check_out"]:
            record["check_out"] = record["check_out"].strftime("%Y-%m-%d %H:%M:%S")


    return jsonify({'attendance_records': records})

@attendance_bp.route('/manager_records', methods=['GET'])
def get_manager_attendance():
    if 'email' not in session or session.get('role') not in ['manager', 'co_manager']:
        return jsonify({'message': 'גישה נדחתה'}), 403

    if session['role'] == 'manager':
        manager_email = session['email']
    
    elif session['role'] == 'co_manager':
        manager_email = session.get('manager_email') 

    # קבלת התאריך של היום
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # records = list(attendance_collection.find({"manager_email": manager_email}))

    records = list(attendance_collection.find({
            "manager_email": manager_email,
            "check_in": {
                "$gte": datetime(current_year, current_month, 1), 
                "$lt": datetime(current_year, current_month + 1, 1) if current_month < 12 
                    else datetime(current_year + 1, 1, 1)
            }
        }))

    for record in records:
        record['_id'] = str(record['_id'])
        if "check_in" in record and record["check_in"]:
            record["check_in"] = record["check_in"].strftime("%d/%m/%Y %H:%M")
        if "check_out" in record and record["check_out"]:
            record["check_out"] = record["check_out"].strftime("%d/%m/%Y %H:%M")


    return jsonify({'attendance_records': records})


@attendance_bp.route('/manager_page', methods=['GET'])
def attendance_manager_page():
    if 'email' not in session or session.get('role') not in ['manager', 'co_manager']:
        return redirect(url_for('users_bp_main.login'))
    
    return render_template('attendance_manager.html')


@attendance_bp.route('/employees_list', methods=['GET'])
def get_employees_list():
    if 'email' not in session or session.get('role') not in ['manager', 'co_manager']:
        return jsonify({'message': 'גישה נדחתה'}), 403

    manager_email = session['email'] if session['role'] == 'manager' else session.get('manager_email')

    employees = list(db.employee.find(
        {
            "manager_email": manager_email,
            "is_approved": 1
        },
        {"_id": 0, "email": 1, "first_name": 1, "last_name": 1}
    ))

    return jsonify({'employees': employees})



@attendance_bp.route('/manual_report', methods=['POST'])
def manual_attendance_report():
    if 'email' not in session or session.get('role') not in ['manager', 'co_manager']:
        return jsonify({'message': 'גישה נדחתה'}), 403

    data = request.json
    employee_email = data.get('email')
    check_in_time = data.get('check_in')
    check_out_time = data.get('check_out')

    if not employee_email or not check_in_time or not check_out_time:
        return jsonify({'message': 'נא לספק את כל הנתונים'}), 400

    check_in_time = datetime.fromisoformat(check_in_time).replace(tzinfo=pytz.utc)
    check_out_time = datetime.fromisoformat(check_out_time).replace(tzinfo=pytz.utc)
    total_hours = (check_out_time - check_in_time).total_seconds() / 3600.0

    employee = db.employee.find_one({"email": employee_email}, {"_id": 0, "first_name": 1, "last_name": 1, "manager_email": 1})
    if not employee:
        return jsonify({'message': 'העובד לא נמצא'}), 404

    new_attendance = {
        "email": employee_email,
        "manager_email": employee.get("manager_email"),
        "first_name": employee.get("first_name"),
        "last_name": employee.get("last_name"),
        "check_in": check_in_time,
        "check_out": check_out_time,
        "total_hours": round(total_hours, 2)
    }

    result = attendance_collection.insert_one(new_attendance)
    return jsonify({'message': 'הדיווח נשמר בהצלחה!', 'inserted_id': str(result.inserted_id)})




@attendance_bp.route('/update_attendance', methods=['POST'])
def update_attendance():
    if 'email' not in session or session.get('role') not in ['manager', 'co_manager']:
        return jsonify({'message': 'גישה נדחתה'}), 403

    data = request.json
    attendance_id = data.get('id')
    check_in_time = data.get('check_in')
    check_out_time = data.get('check_out')

    if not attendance_id or not check_in_time or not check_out_time:
        return jsonify({'message': 'נתונים חסרים'}), 400

    try:
        print(f"Received ID: {attendance_id}")
        print(f"Check-in: {check_in_time}, Check-out: {check_out_time}")

        check_in_time = datetime.fromisoformat(check_in_time)
        check_out_time = datetime.fromisoformat(check_out_time)

        total_hours = (check_out_time - check_in_time).total_seconds() / 3600.0

        result = attendance_collection.update_one(
            {"_id": ObjectId(attendance_id)},
            {"$set": {"check_in": check_in_time, "check_out": check_out_time, "total_hours": round(total_hours, 2)}}
        )

        if result.modified_count == 0:
            return jsonify({'message': 'לא בוצע עדכון, ייתכן שהנתון לא קיים'}), 404

        return jsonify({'message': 'הדיווח עודכן בהצלחה!'})

    except ValueError as ve:
        return jsonify({'message': f'שגיאה בפורמט התאריך: {str(ve)}'}), 400
    except Exception as e:
        return jsonify({'message': f'שגיאה בעדכון הנתונים: {str(e)}'}), 500


@attendance_bp.route('/get_record/<record_id>', methods=['GET'])
def get_attendance_record(record_id):
    try:
        record = attendance_collection.find_one({"_id": ObjectId(record_id)})
        if not record:
            return jsonify({"error": "רשומה לא נמצאה"}), 404

        return jsonify({
            "check_in": record["check_in"].strftime("%Y-%m-%dT%H:%M"),
            "check_out": record["check_out"].strftime("%Y-%m-%dT%H:%M")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

