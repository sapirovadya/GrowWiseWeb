from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import uuid  # מחולל ID ייחודיים
from modules.Plots.models import Plot
import openai
from bson import ObjectId
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
    try:
        email = session.get("email")
        role = session.get("role")
        
        # if not email:
        #     return jsonify({"error": "Manager is not logged in."}), 403

        if role == "manager":
            manager_email = email
        elif role in ["employee", "co_manager"]:
            manager_email = session.get("manager_email")
            if not manager_email:
                return jsonify({"error": "Manager email not found for user."}), 403
        else:
            return jsonify({"error": "Invalid role."}), 403

        manager = db.manager.find_one({"email": manager_email})
        if not manager:
            return jsonify({"error": "Manager not found in the database."}), 404

        city = manager.get("location")
        if not city:
            return jsonify({"error": "Location not found for the manager."}), 400

        crop = request.json.get("crop")
        plot_type = request.json.get("plot_type")
        sow_date = request.json.get("sow_date")

        if not (crop and plot_type and sow_date):
            return jsonify({"error": "Missing required fields in the request."}), 400

        input_date = datetime.strptime(sow_date, '%Y-%m-%d')
        today_date = datetime.now()
        days_passed = (today_date - input_date).days

        # בניית הפרומפט
        prompt = (
            f"כיצד אמור להיראות שתיל של {crop}, לאחר {days_passed} ימים מהשתילה, "
            f"הגדל בעיר {city} באופן גידול {plot_type}? "
            f"תאר לי בעזרת גובה (במספרים), צבע (של גבעולים ועלים) והאם הגידול אמור להפיק תוצר בהתאם ליבול (פרי או ירק וכדומה)."
            f" give me the output with <p> tags for the sentences"
            
        )

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "אתה אגרונום, הנותן תחזיות גדילה ואיך אמורים להיראות (במילולית) הגידולים באופן מדויק לחקלאים לפי מיקום ותנאי אקלים בארץ ישראל.אסור להשתמש בכוכביות ! ניתן להשתמש במספור אם יש צורך"
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
    return render_template('track_greenhouse.html', email=email, manager_email=manager_email, name=name, role=role)

@plot_bp.route("/save_plot", methods=["POST"])
def save_plot():
    try:
        plot_id =str(uuid.uuid4())
        data = request.json
        role = session.get("role")
        email = session.get("email")

        if role == "manager":
            manager_email = email
        elif role in ["employee", "co_manager"]:
            manager_email = session.get("manager_email")
        else:
            return jsonify({"error": "תפקיד לא מזוהה."}), 400

        if not manager_email:
            return jsonify({"error": "שגיאה בזיהוי מנהל המשק."}), 400

        plot_name = data.get("plot_name")
        plot_type = data.get("plot_type")
        width = data.get("width")
        length = data.get("length")

        if not plot_name or not plot_type:
            return jsonify({"error": "שם החלקה וסוג החלקה הם שדות חובה."}), 400
        if width is None or width <= 0:
            return jsonify({"error": "רוחב חייב להיות מספר חיובי."}), 400
        if length is None or length <= 0:
            return jsonify({"error": "אורך חייב להיות מספר חיובי."}), 400

        crop_category = data.get("crop_category", "none")
        crop_name = data.get("crop", "none")
        sow_date = data.get("sow_date") if crop_category != "none" and crop_name != "none" else ""
        quantity_planted = data.get("quantity_planted")

        if crop_category != "none" and crop_name != "none":
            if not sow_date:
                return jsonify({"error": "נא למלא את תאריך הזריעה"}), 400
            if not quantity_planted or quantity_planted <= 0:
                return jsonify({"error": "נא למלא כמות זריעה תקינה (בק״ג)."}), 400

            crop_entry = db.supply.find_one({"email": manager_email, "name": crop_name, "category": "גידול"})
            if not crop_entry or crop_entry["quantity"] < quantity_planted:
                return jsonify({"error": f"הזנת כמות הגדולה מהמלאי. ניתן לשתול עד {crop_entry['quantity']} ק\"ג."}), 400

            db.supply.update_one(
                {"email": manager_email, "name": crop_name, "category": "גידול"},
                {"$inc": {"quantity": -quantity_planted}}
            )
        else:
            quantity_planted = ""

        new_plot = {
            "_id": plot_id,  # שמירה כמחרוזת
            "plot_name": plot_name,
            "plot_type": plot_type,
            "width": width,
            "length": length,
            "manager_email": manager_email,
            "crop_category": crop_category,
            "crop": crop_name,
            "sow_date": sow_date,
            "quantity_planted": quantity_planted,
            "last_irrigation_date": None,
            "total_irrigation_amount": None,
            "harvest_date": None,
            "crop_yield": None,
            "price_yield": None
        }

        db.plots.insert_one(new_plot)
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


@plot_bp.route('/get_plot/<plot_id>', methods=['GET'])
def get_plot(plot_id):
    try:
        plot = db.plots.find_one({"_id": str(plot_id)})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        plot["_id"] = str(plot["_id"])  # המרת ObjectId למחרוזת
        return jsonify(plot), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@plot_bp.route('/plot_details', methods=['GET'])
def plot_details():
    plot_id = request.args.get('id') 
    if not plot_id:
        return "Plot ID is missing.", 400

    plot = db.plots.find_one({"_id": plot_id})
    if not plot:
        return "Plot not found.", 404

    return render_template('plot_details.html', plot=plot)


@plot_bp.route('/update_plot/<plot_id>', methods=['POST'])
def update_plot(plot_id):
    try:
        data = request.get_json()
        print(f"🔍 קיבלנו נתונים: {data}")  

        required_fields = ['crop', 'sow_date', 'quantity_planted']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        manager_email = plot.get("manager_email")
        crop_name = data['crop']
        crop_category = data['crop_category']
        quantity_planted = data['quantity_planted']

        crop_entry = db.supply.find_one({"email": manager_email, "name": crop_name, "category": "גידול"})
        if not crop_entry or crop_entry["quantity"] < quantity_planted:
            return jsonify({"error": f"הזנת כמות גדולה מהמלאי. ניתן לשתול עד {crop_entry['quantity']} ק\"ג."}), 400

        db.supply.update_one(
            {"email": manager_email, "name": crop_name, "category": "גידול"},
            {"$inc": {"quantity": -quantity_planted}}
        )

        update_result = db.plots.update_one(
            {"_id": plot_id},
            {"$set": {
                "crop_category": str(data["crop_category"]), 
                "crop": data['crop'],
                "sow_date": data['sow_date'],
                "quantity_planted": quantity_planted
            }}
        )

        if update_result.modified_count == 0:
            return jsonify({"error": "לא בוצע עדכון, ייתכן ואין שינוי"}), 400

        return jsonify({"message": "Plot updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@plot_bp.route('/update_irrigation/<plot_id>', methods=['POST'])
def update_irrigation(plot_id):
    try:
        data = request.get_json()
        irrigation_amount = data.get('irrigation_amount')

        if not irrigation_amount or not isinstance(irrigation_amount, (int, float)) or irrigation_amount <= 0:
            return jsonify({"error": "Invalid irrigation amount"}), 400

        # Fetch the plot details
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        # Determine the email to store
        user_role = session.get('role')
        if user_role == "manager":
            email = session.get('email')
        else:
            email = plot.get('manager_email')

        # Get plot name and sow date
        plot_name = plot.get('plot_name')
        sow_date = plot.get('sow_date')

        # Update the total irrigation amount
        current_total = plot.get('total_irrigation_amount', 0) or 0
        new_total = current_total + irrigation_amount

        # Update the plot with new irrigation data
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "total_irrigation_amount": new_total,
                    "last_irrigation_date": datetime.utcnow().strftime('%Y-%m-%d')
                }
            }
        )

        # Create a new irrigation record
        new_irrigation = {
            "_id": str(uuid.uuid4()),
            "email": email,
            "name": plot_name,
            "sow_date": sow_date,
            "quantity_irrigation": irrigation_amount,
            "Irrigation_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        db.irrigation.insert_one(new_irrigation)

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
        price_yield = data.get('price_yield', None)  # אם המשתמש לא מילא - השדה יישאר None

        if not harvest_date or not crop_yield:
            return jsonify({"error": "Missing required fields"}), 400

        # עדכון החלקה בבסיס הנתונים
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "harvest_date": harvest_date,
                    "crop_yield": crop_yield,       
                    "price_yield": price_yield  # שמירת המחיר רק אם הוזן
                }
            }
        )
        return redirect(url_for('plot_bp.track_greenhouse'))

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


@plot_bp.route("/get_harvested_plots", methods=["GET"])
def get_harvested_plots():
    try:
        # שליפת שמות חלקות ייחודיים שעומדים בתנאים
        unique_plot_names = db.plots.distinct("plot_name", {"harvest_date": {"$ne": None}, "price_yield": None})

        # יצירת רשימה עם החלקות והוספת harvest_date (נשלוף רק את ה-harvest_date הראשון שנמצא לכל חלקה)
        plots = []
        for plot_name in unique_plot_names:
            plot = db.plots.find_one(
                {"plot_name": plot_name, "harvest_date": {"$ne": None}, "price_yield": None},
                {"plot_name": 1, "harvest_date": 1, "_id": 0}
            )
            if plot:
                plots.append(plot)

        return jsonify({"plots": plots}), 200

    except Exception as e:
        return jsonify({"error": f"שגיאה בשליפת החלקות: {str(e)}"}), 500


@plot_bp.route("/get_crop_details", methods=["GET"])
def get_crop_details():
    plot_name = request.args.get("plot_name")
    sow_date = request.args.get("sow_date")

    plot = db.plots.find_one({"plot_name": plot_name, "sow_date": sow_date}, {"crop": 1, "crop_yield": 1})
    
    if not plot:
        return jsonify({"error": "לא נמצאו נתונים"}), 404

    return jsonify({"crop": plot.get("crop", ""), "crop_yield": plot.get("crop_yield", 0)})

# עדכון מחיר לק"ג תפוקה
@plot_bp.route("/update_price_yield", methods=["POST"])
def update_price_yield():
    data = request.json
    plot_name = data.get("plot_name")
    sow_date = data.get("sow_date")
    price_yield = float(data.get("price_yield"))

    db.plots.update_one({"plot_name": plot_name, "sow_date": sow_date}, {"$set": {"price_yield": price_yield}})
    return jsonify({"message": "המחיר נשמר בהצלחה"})

@plot_bp.route("/get_sow_dates", methods=["GET"])
def get_sow_dates():
    plot_name = request.args.get("plot_name")

    if not plot_name:
        return jsonify({"error": "Missing plot_name"}), 400

    try:
        dates = db.plots.find({"plot_name": plot_name, "sow_date": {"$ne": None}, "price_yield": None}, {"sow_date": 1, "_id": 0})
        date_list = [plot["sow_date"] for plot in dates if "sow_date" in plot]

        return jsonify({"dates": date_list}), 200
    except Exception as e:
        return jsonify({"error": f"שגיאה בשליפת תאריכי זריעה: {str(e)}"}), 500

