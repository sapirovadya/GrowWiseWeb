from flask import Blueprint, render_template, request, jsonify, session
import pymongo
from datetime import datetime
import os
from dotenv import load_dotenv
from bson import ObjectId  # תמיכה ב-ObjectId של MongoDB
from modules.vehicles.models import VehicleManagement
from modules.expenses.models import VehicleServiceHistory, VehicleTestHistory, VehicleInsuranceHistory

vehicles_bp = Blueprint('vehicles_bp', __name__, url_prefix='/vehicles')

# התחברות ל-MongoDB
load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
vehicles_collection = db["vehicles"]
service_history_collection = db["service_history"]
test_history_collection = db["test_history"]
insurance_history_collection = db["insurance_history"]

vehicles_model = VehicleManagement()
vehicles_model = VehicleManagement()
service_model = VehicleServiceHistory()
test_model = VehicleTestHistory()  
insurance_model = VehicleInsuranceHistory()

@vehicles_bp.route('/vehicles_management', methods=['GET'])
def vehicles_management_page():
    return render_template('vehicles_management.html')

@vehicles_bp.route('/add', methods=['POST'])
def add_vehicle():
    data = request.get_json()

    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    if vehicles_collection.find_one({"vehicle_number": data.get("vehicle_number")}):
        return jsonify({"error": "רכב עם מספר זה כבר קיים"}), 400

    # קבלת המייל של המשתמש המחובר
    role = session.get("role")
    if role == "manager":
        manager_email = session.get("email")
    else:
        manager_email = session.get("manager_email")

    # יצירת רכב חדש
    new_vehicle = vehicles_model.new_vehicle(data)
    new_vehicle["manager_email"] = manager_email  # ✅ שמירת המייל
    result = vehicles_collection.insert_one(new_vehicle)
    new_vehicle["_id"] = str(result.inserted_id)

    # הוספת מייל מנהל לטבלאות ההיסטוריות
    test_entry = test_model.new_test_record({
        "vehicle_number": data.get("vehicle_number"),
        "test_date": data.get("test_date"),
        "test_cost": data.get("test_cost"),
        "manager_email": manager_email  # ✅ שמירת המייל בהיסטוריה
    })
    test_history_collection.insert_one(test_entry)

    service_entry = service_model.new_service_record({
        "vehicle_number": data.get("vehicle_number"),
        "service_date": data.get("last_service_date"),
        "service_cost": data.get("service_cost"),
        "service_notes": data.get("service_notes"),
        "manager_email": manager_email  # ✅ שמירת המייל בהיסטוריה
    })
    service_history_collection.insert_one(service_entry)

    insurance_entry = insurance_model.new_insurance_record({
        "vehicle_number": data.get("vehicle_number"),
        "insurance_date": data.get("insurance_date"),
        "insurance_cost": data.get("insurance_cost"),
        "manager_email": manager_email  # ✅ שמירת המייל בהיסטוריה
    })
    insurance_history_collection.insert_one(insurance_entry)

    return jsonify({"message": "כלי הרכב נוסף בהצלחה!", "vehicle": new_vehicle}), 201




@vehicles_bp.route('/get', methods=['GET'])
def get_vehicles():

    role = session.get("role")
    if role == "manager":
        manager_email = session.get("email")
    else:
        manager_email = session.get("manager_email")

    vehicles = list(vehicles_collection.find({"manager_email": manager_email}))
    
    for vehicle in vehicles:
        vehicle["_id"] = str(vehicle["_id"])
    
    return jsonify(vehicles)

@vehicles_bp.route('/delete/<vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    result = vehicles_collection.delete_one({"_id": object_id})
    
    if result.deleted_count == 0:
        return jsonify({"error": "רכב לא נמצא"}), 404

    return jsonify({"message": "כלי השטח נמחק בהצלחה!"})


@vehicles_bp.route('/update/<vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    result = vehicles_collection.update_one({"_id": object_id}, {"$set": data})

    if result.modified_count == 0:
        return jsonify({"message": "לא בוצע עדכון, ייתכן שהרכב לא קיים"}), 404

    return jsonify({"message": "פרטי הרכב עודכנו בהצלחה!"})


@vehicles_bp.route('/update_test/<vehicle_id>', methods=['PUT'])
def update_test(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    vehicle = vehicles_collection.find_one({"_id": object_id})
    if not vehicle:
        return jsonify({"error": "הרכב לא נמצא"}), 404

    vehicle_number = vehicle.get("vehicle_number")
    manager_email = vehicle.get("manager_email")  # ✅ שמירת מייל מנהל

    test_entry = {
        "vehicle_number": vehicle_number,
        "test_date": data.get("test_date"),
        "test_cost": data.get("test_cost"),
        "manager_email": manager_email  # ✅ שמירת מייל בטבלה
    }
    test_history_collection.insert_one(test_entry)

    vehicles_collection.update_one(
        {"_id": object_id},
        {"$set": {"test_date": data.get("test_date"), "test_cost": data.get("test_cost")}}
    )

    return jsonify({"message": "פרטי הטסט עודכנו בהצלחה!"})



@vehicles_bp.route('/update_service/<vehicle_id>', methods=['PUT'])
def update_service(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    vehicle = vehicles_collection.find_one({"_id": object_id})
    if not vehicle:
        return jsonify({"error": "הרכב לא נמצא"}), 404

    vehicle_number = vehicle.get("vehicle_number")
    manager_email = vehicle.get("manager_email")  # ✅ שמירת מייל מנהל

    service_entry = {
        "vehicle_number": vehicle_number,
        "service_date": data.get("service_date"),
        "service_cost": data.get("service_cost"),
        "service_notes": data.get("service_notes"),
        "manager_email": manager_email  # ✅ שמירת מייל בטבלה
    }
    service_history_collection.insert_one(service_entry)

    vehicles_collection.update_one(
        {"_id": object_id},
        {"$set": {"last_service_date": data.get("service_date"), "service_cost": data.get("service_cost")}}
    )

    return jsonify({"message": "פרטי הטיפול עודכנו בהצלחה!"})


@vehicles_bp.route('/update_insurance/<vehicle_id>', methods=['PUT'])
def update_insurance(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    vehicle = vehicles_collection.find_one({"_id": object_id})
    if not vehicle:
        return jsonify({"error": "הרכב לא נמצא"}), 404

    vehicle_number = vehicle.get("vehicle_number")
    manager_email = vehicle.get("manager_email")  # ✅ שמירת מייל מנהל

    insurance_entry = {
        "vehicle_number": vehicle_number,
        "insurance_date": data.get("insurance_date"),
        "insurance_cost": data.get("insurance_cost"),
        "manager_email": manager_email  # ✅ שמירת מייל בטבלה
    }
    insurance_history_collection.insert_one(insurance_entry)

    vehicles_collection.update_one(
        {"_id": object_id},
        {"$set": {"insurance_date": data.get("insurance_date"), "insurance_cost": data.get("insurance_cost")}}
    )

    return jsonify({"message": "פרטי הביטוח עודכנו בהצלחה!"})

@vehicles_bp.route('/update_km/<vehicle_id>', methods=['PUT'])
def update_km_workhours(vehicle_id):
    try:
        object_id = ObjectId(vehicle_id)
    except:
        return jsonify({"error": "מזהה לא תקין"}), 400

    data = request.json
    if data is None:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    # שליפת הרכב הקיים
    vehicle = vehicles_collection.find_one({"_id": object_id})
    if not vehicle:
        return jsonify({"error": "הרכב לא נמצא"}), 404

    current_km = vehicle.get("Km_WorkHours") or 0

    if not data.get("Km_WorkHours"):
        # אם המשתמש רצה לאפס את השדה
        update_data = {
            "Km_WorkHours": None,
            "Km_WorkHours_update_date": None
        }
    else:
        try:
            added_km = float(data["Km_WorkHours"])
        except ValueError:
            return jsonify({"error": "קלט לא תקין"}), 400

        new_km = float(current_km) + added_km

        update_data = {
            "Km_WorkHours": new_km,
            "Km_WorkHours_update_date": datetime.now().strftime("%d/%m/%Y")
        }

    result = vehicles_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )

    if result.modified_count == 0:
        return jsonify({"message": "לא בוצע עדכון"}), 404

    return jsonify({"message": "ק\"מ/שעות עבודה עודכנו בהצלחה!"})
