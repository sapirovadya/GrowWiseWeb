from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
from modules.Plots.models import Plot
import openai
from datetime import datetime

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")
# Configuration for OpenAI
MODEL = "gpt-4o"
TEMPERATURE = 1
MAX_TOKENS = 350

plot_bp = Blueprint('plot_bp', __name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

@plot_bp.route("/growth_forecast", methods=["POST"])
def growth_forecast():

    crop = request.json.get("crop")
    plot_type = request.json.get("plot_type")
    city = "באר שבע"
    sow_date = request.json.get("sow_date")
    input_date = datetime.strptime(sow_date, '%Y-%m-%d')
    today_date = datetime.now()
    days_passed = (today_date - input_date).days



    prompt = f"כיצד אמור להיראות שתיל של {crop}, לאחר {days_passed} ימים מהשתילה, הגדל בעיר {city} באופן גידול  {plot_type}? תאר לי בעזרת גובה (במספרים), צבע (של גבעולים ועלים) ותפוקת יבול."

    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content":(
                        "אתה אגרונום, הנותן תחזית מדוייקת לחקלאים לפי מיקום ותנאי אקלים בארץ ישראל."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        forecast = response['choices'][0]['message']['content']
        return jsonify({"forecast": forecast}), 200

    except openai.error.OpenAIError as e:
        return jsonify({"error": f"שגיאה ב-API של OpenAI: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"שגיאה כללית: {e}"}), 500
    

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
            quantity_planted=data.get("quantity_planted"),

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
    query = {"harvest_date": None}  # סינון חלקות עם harvest_date == None

    if role == "manager":
        query["manager_email"] = email
    elif role in ["employee", "co_manager"]:
        manager_email = session.get("manager_email")
        if not manager_email:
            return jsonify({"error": "Manager email not found for user."}), 403
        query["manager_email"] = manager_email
    else:
        return jsonify({"error": "Invalid role."}), 403

    plots = list(db.plots.find(query))
    # המרת ObjectId למחרוזת
    for plot in plots:
        plot["_id"] = str(plot["_id"])

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


@plot_bp.route('/update_plot/<plot_id>', methods=['POST'])
def update_plot(plot_id):
    try:
        # קבלת הנתונים שנשלחו בבקשה
        data = request.get_json()

        # בדיקה האם כל הנתונים הדרושים נשלחו
        required_fields = ['crop_category', 'crop', 'sow_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # בדיקת קיום החלקה ב-DB
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        # עדכון החלקה ב-DB
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "crop_category": data['crop_category'],
                    "crop": data['crop'],
                    "sow_date": data['sow_date'],
                    "quantity_planted": data['quantity_planted']
                }
            }
        )

        return jsonify({"message": "Plot updated successfully"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


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

@plot_bp.route('/archive_plot/<plot_id>', methods=['POST'])
def archive_plot(plot_id):
    try:
        data = request.get_json()
        harvest_date = data.get('harvest_date')
        crop_yield = data.get('crop_yield')

        if not harvest_date or not crop_yield:
            return jsonify({"error": "Missing required fields"}), 400

        # עדכון החלקה בבסיס הנתונים
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "harvest_date": harvest_date,
                    "crop_yield": crop_yield
                }
            }
        )
        return jsonify({"message": "Plot archived successfully"}), 200

    except Exception as e:
        print(f"Error archiving plot: {e}")
        return jsonify({"error": "Server error"}), 500

@plot_bp.route("/archive", methods=["GET"])
def archive():
    role = session.get("role")
    email = session.get("email")
    manager_email = session.get("manager_email")

    if not role or not email:
        return jsonify({"error": "User is not logged in or missing role."}), 403

    try:
        # הגדרת הקריטריון בהתאם לתפקיד המשתמש
        if role == "manager":
            filter_criteria = {"manager_email": email, "harvest_date": {"$ne": None}}
        elif role == "co_manager":
            filter_criteria = {"manager_email": manager_email, "harvest_date": {"$ne": None}}
        else:
            return jsonify({"error": "Unauthorized role."}), 403

        # שליפת החלקות מארכיון
        archived_plots = list(db.plots.find(filter_criteria))
        for plot in archived_plots:
            plot["_id"] = str(plot["_id"])  # המרת ObjectId למחרוזת

        return render_template("plots_archive.html", plots=archived_plots)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500