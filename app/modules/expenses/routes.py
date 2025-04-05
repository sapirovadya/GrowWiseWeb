from flask import Blueprint, request, jsonify, session,render_template, session
import pymongo
import uuid
from datetime import datetime, timezone
import os
from dotenv import load_dotenv, find_dotenv
from modules.expenses.models import Purchase
from modules.expenses.models import Water
from modules.expenses.models import Fuel

expenses_bp = Blueprint('expenses_bp', __name__)

load_dotenv(find_dotenv())

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

@expenses_bp.route('/purchase/add', methods=['POST'])
def add_purchase():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    data = request.json
    data["email"] = session["email"]

    new_purchase = Purchase.add_purchase(data)
    return jsonify({"message": "הרכישה נשמרה", "purchase": new_purchase}), 201

@expenses_bp.route('/water/add', methods=['POST'])
def add_water():
    data = request.get_json()
    price = data.get("price")
    date = data.get("date")

    if not price or price <= 0 or not date:
        return jsonify({"error": "Invalid data"}), 400

    user_role = session.get('role')
    if user_role == "manager":
        email = session.get('email')
    else:
        email = session.get('manager_email')

    new_water = {
        "_id": str(uuid.uuid4()),
        "email": email,
        "price": price,
        "date": date
    }
    try:
        db.water.insert_one(new_water)
    except Exception as e:
        return jsonify({"error": f"שגיאת שרת: {str(e)}"}), 500  # ✅ return היה חסר

    return jsonify({"message": "הרכישה נשמרה בהצלחה!"}), 200


@expenses_bp.route('/get_vehicles', methods=['GET'])
def get_vehicles():
    if 'email' not in session:
        return jsonify({"message": "Unauthorized"}), 403

    role = session.get('role')
    email = session.get('email')

    if role == "manager":
        manager_email = email
    elif role == "co_manager":
        manager_email = session.get("manager_email")
    else:
        return jsonify({"message": "Unauthorized role"}), 403
    print(f"🔍 מחפש רכבים עבור מנהל: {manager_email}")  # Debugging

    vehicles = db.vehicles.find({"manager_email": manager_email}, {"_id": 0, "vehicle_number": 1})
    vehicle_list = [v.get("vehicle_number") for v in vehicles if v.get("vehicle_number")]
    if not vehicle_list:
        return jsonify({"message": "No vehicles found"}), 404
    print(f"✅ רכבים שנמצאו: {vehicle_list}")  # Debugging

    return jsonify(vehicle_list)

@expenses_bp.route('/add_fuel_expense', methods=['POST'])
def add_fuel_expense():
    if 'email' not in session:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    data["email"] = session.get('email')

    if not all([data.get("vehicle_number"), data.get("fuel_amount"), data.get("cost"), data.get("refuel_type")]):
        return jsonify({"message": "Missing fields"}), 400

    if data.get("refuel_type") == "דלקן" and not data.get("month"):
        return jsonify({"message": "Missing month for דלקן"}), 400

    result = Fuel.add_fuel_entry(data)
    return jsonify(result), 201