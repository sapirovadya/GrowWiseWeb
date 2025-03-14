from flask import Blueprint, render_template, request, jsonify
import pymongo
import os
from dotenv import load_dotenv
from bson import ObjectId  # תמיכה ב-ObjectId של MongoDB
from modules.vehicles.models import VehicleManagement

vehicles_bp = Blueprint('vehicles_bp', __name__, url_prefix='/vehicles')

# התחברות ל-MongoDB
load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
vehicles_collection = db["vehicles"]

# יצירת מופע של ניהול כלי שטח
vehicles_model = VehicleManagement()

@vehicles_bp.route('/vehicles_management', methods=['GET'])
def vehicles_management_page():
    return render_template('vehicles_management.html')

@vehicles_bp.route('/add', methods=['POST'])
def add_vehicle():
    data = request.get_json()  # בלי force=True
    
    if not data:
        return jsonify({"error": "לא התקבלו נתונים"}), 400

    if vehicles_collection.find_one({"vehicle_number": data.get("vehicle_number")}):
        return jsonify({"error": "רכב עם מספר זה כבר קיים"}), 400

    new_vehicle = vehicles_model.new_vehicle(data)
    result = vehicles_collection.insert_one(new_vehicle)
    new_vehicle["_id"] = str(result.inserted_id)

    return jsonify({"message": "כלי השטח נוסף בהצלחה!", "vehicle": new_vehicle}), 201


@vehicles_bp.route('/get', methods=['GET'])
def get_vehicles():
    vehicles = list(vehicles_collection.find({}))
    
    # המרת ObjectId למחרוזת JSON
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
