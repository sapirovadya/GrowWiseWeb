from flask import Blueprint, request, jsonify, session,render_template, session
import pymongo
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv, find_dotenv
from modules.expenses.models import Purchase
from modules.expenses.models import Water

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
    try:
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

        db.water.insert_one(new_water)

        return jsonify({"message": "הרכישה נשמרה בהצלחה!"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"שגיאת שרת: {str(e)}"}), 500
