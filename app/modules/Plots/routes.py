from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv
import os
from modules.Plots.models import Plot


load_dotenv()

plot_bp = Blueprint('plot_bp', __name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")


@plot_bp.route("/track_greenhouse", methods=['GET'])
def track_greenhouse():
    email = session.get('email')
    manager_email = session.get('manager_email')
    name = session.get('name')
    role = session.get('role')
    print(email)
    print(manager_email)
    print(role)
    # כאן ניתן להשתמש בנתונים או להעביר אותם ל-Template
    return render_template('track_greenhouse.html', email=email, manager_email=manager_email, name=name, role=role)

@plot_bp.route("/save_plot", methods=["POST"])
def save_plot():
    data = request.form

    # בדיקת שדות חובה
    required_fields = ["plot_name", "plot_type", "width", "length"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({"error": f"שדות חסרים: {', '.join(missing_fields)}"}), 400

    # בדיקת קיום role ו-email ב-session
    if "role" not in session or "email" not in session:
        return jsonify({"error": "משתמש לא מחובר או שאין לו תפקיד מתאים."}), 403

    try:
        # קביעת אימייל של המנהל
        role = session["role"]
        if role == "manager":
            manager_email = session["email"]
        elif role in ["employee", "co_manager"]:
            manager_email = session.get("manager_email")
        else:
            return jsonify({"error": "תפקיד לא מזוהה."}), 400

        if not manager_email:
            return jsonify({"error": "שגיאה בזיהוי מנהל המשק."}), 400

        # יצירת אובייקט Plot חדש
        new_plot = Plot(
            plot_name=data.get("plot_name"),
            plot_type=data.get("plot_type"),
            width=float(data.get("width")),
            length=float(data.get("length")),
            manager_email=manager_email,
            crop_category=data.get("crop_category", "none"),
            crop=data.get("crop", "none"),
            sow_date=data.get("sow_date"),
        )

        # שמירה ל-DB
        db.plots.insert_one(new_plot.to_dict())
        return jsonify({"message": "החלקה נשמרה בהצלחה!"}), 201

    except Exception as e:
        return jsonify({"error": f"שגיאה ביצירת חלקה: {str(e)}"}), 500

@plot_bp.route("/get_crop_categories", methods=['GET'])
def get_crop_categories():
    try:
        categories = db.crops_options.distinct("category")
        return jsonify({"categories": categories}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@plot_bp.route("/get_crops", methods=['GET'])
def get_crops():
    category = request.args.get('category')
    if not category:
        return jsonify({"error": "Category is missing"}), 400

    # שליפת הנתונים מה-DB
    category_data = db.crops_options.find_one({"category": category})
    if not category_data:
        return jsonify({"crops": []}), 200

    return jsonify({"crops": category_data["values"]}), 200


@plot_bp.route("/get_plots", methods=["GET"])
def get_plots():
    role = session.get("role")
    email = session.get("email")

    if not role or not email:
        return jsonify({"error": "User is not logged in or missing role."}), 403

    if role == "manager":
        plots = list(db.plots.find({"manager_email": email}))
    elif role in ["employee", "co_manager"]:
        manager_email = session.get("manager_email")
        if not manager_email:
            return jsonify({"error": "Manager email not found for user."}), 403
        plots = list(db.plots.find({"manager_email": manager_email}))
    else:
        return jsonify({"error": "Invalid role."}), 403

    # המרת החלקות לרשימה ניתנת לשליחה ל-JSON
    for plot in plots:
        plot["_id"] = str(plot["_id"])  # המרת ObjectId למחרוזת

    return jsonify({"plots": plots}), 200









@plot_bp.route('/plot_details', methods=['GET'])
def plot_details():
    plot_id = request.args.get('id')  # קבלת ה-ID מה-URL
    if not plot_id:
        return "Plot ID is missing.", 400

    # שליפת הנתונים מהמסד
    plot = db.plots.find_one({"_id": plot_id})
    if not plot:
        return "Plot not found.", 404

    # המרת הנתונים לפורמט JSON או העברת המידע לעמוד HTML
    return render_template('plot_details.html', plot=plot)


@plot_bp.route('/update_irrigation/<plot_id>', methods=['POST'])
def update_irrigation(plot_id):
    try:
        # בדיקת ID תקין
        print(f"Received plot ID: {plot_id}")
        data = request.get_json()
        irrigation_amount = data.get('irrigation_amount')

        if not irrigation_amount or not isinstance(irrigation_amount, (int, float)) or irrigation_amount <= 0:
            return jsonify({"error": "Invalid irrigation amount"}), 400

        # בדיקה אם החלקה קיימת
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        # חישוב סכום השקיה חדש
        current_total = plot.get('total_irrigation_amount', 0)
        if current_total is None:
            current_total = 0
        new_total = current_total + irrigation_amount

        # עדכון DB
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "total_irrigation_amount": new_total,
                    "last_irrigation_date": datetime.now().strftime('%Y-%m-%d')
                }
            }
        )

        return jsonify({"message": "Irrigation updated successfully", "new_total": new_total}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500