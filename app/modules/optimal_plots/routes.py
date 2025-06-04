from flask import Blueprint, render_template, session, jsonify, request
import pymongo
import os
from dotenv import load_dotenv
import openai
from bson import ObjectId
from datetime import datetime
import jdatetime

load_dotenv()
optimal_bp = Blueprint("optimal_bp", __name__)
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"
TEMPERATURE = 1
MAX_TOKENS = 500

def get_season_and_date():
    today = datetime.now()
    month = today.month
    day = today.day

    # קביעת העונה (אביב או סתיו)
    if month in [3, 4, 5]:
        season = "spring"   # אביב
    elif month in [9, 10, 11]:
        season = "autumn"   # סתיו
    else:
        season = "other"    # עונות אחרות

    # המרת תאריך עברי
    heb_date = jdatetime.date.fromgregorian(date=today)
    heb_month = heb_date.month
    heb_day = heb_date.day

    # בדיקה אם אחרי ט"ו באב (15 באב)
    is_after_tu_bav = (heb_month > 5) or (heb_month == 5 and heb_day > 15)

    return {
        "date": today.strftime("%d/%m/%Y"),
        "season": season,
        "is_after_tu_bav": is_after_tu_bav
    }


@optimal_bp.route("/management", methods=["GET"])
def optimal_management_page():
    return render_template("optimal_management.html")

@optimal_bp.route("/get_inventory", methods=["GET"])
def get_inventory():
    email = session.get("email") or session.get("manager_email")
    crops = list(db.supply.find({
        "email": email,
        "category": "גידול",
        "quantity": {"$gt": 0}
    }, {"_id": 0, "name": 1, "quantity": 1}))
    return jsonify(crops)

@optimal_bp.route("/check_plot_sizes")
def check_plot_sizes():
    email = session.get("email") or session.get("manager_email")
    plots = list(db.plots.find({"email": email}))

    filled = [p for p in plots if p.get("length") and p.get("width")]
    incomplete = [p for p in plots if not p.get("length") or not p.get("width")]

    return jsonify({
        "all_filled": len(incomplete) == 0,
        "has_partial": len(filled) > 0,
        "filled_plots": filled
    })

@optimal_bp.route("/generate_plan", methods=["POST"])
def generate_plan():
    try:
        data = request.get_json()
        selected_crops = data.get("selected_crops", [])
        selected_plots = data.get("selected_plots", [])
        email = session.get("email") or session.get("manager_email")
        
        # שליפת העיר מתוך פרטי המנהל
        manager = db.manager.find_one({"email": email})
        city = manager.get("location", "לא צוינה עיר")
        
        # בדיקת נתונים
        if not selected_crops or not selected_plots:
            return jsonify({"error": "חסרים נתונים"}), 400

        # שליפת תאריך נוכחי ועונת השנה
        date_info = get_season_and_date()
        current_date = date_info["date"]
        season = date_info["season"]
        is_after_tu_bav = date_info["is_after_tu_bav"]

        # שליפת מידע על הגידולים שנבחרו
        crop_data = list(db.supply.find({
            "email": email,
            "category": "גידול",
            "name": {"$in": selected_crops}
        }, {"_id": 0, "name": 1, "quantity": 1}))

        # שליפת מידע על החלקות שנבחרו
        plot_data = []
        for p in selected_plots:
            found = db.plots.find_one({"_id": p["id"]}, {"plot_name": 1, "plot_type": 1, "square_meters": 1})
            if found:
                plot_data.append({
                    "plot_name": found["plot_name"],
                    "plot_type": p["type"],
                    "square_meters": found["square_meters"]
                })

        # הכנת נתונים לפורמט טקסטואלי
        plot_lines = "\n".join([f"{p['plot_name']} - {p['plot_type']} בגודל {p['square_meters']} דונם" for p in plot_data])
        crop_lines = "\n".join([f"{c['name']} - {c['quantity']} ק\"ג" for c in crop_data])

        # פרומפט אגרונומי מעודכן
        prompt = f"""
        אתה אגרונום מומחה בעל ניסיון של למעלה מ-20 שנה בגידול ושתילת כל סוגי הגידולים הקיימים. 
        יש להשתמש בידע קיים שלך ובעיקר באתר 
        agriteach.org.il ובכל הדפים הנמצאים בו
    
        כל תשובה שלך צריכה להיות מדויקת, מבוססת על ידע חקלאי מוסמך ואמין בלבד, ותמיד לשמור על אחידות מבנית בין תשובות דומות.

        מיקום המשק: {city}
        תאריך נוכחי: {current_date}

        חלקות או חממות זמינות לשתילה:
        {plot_lines}

        גידולים זמינים במלאי:
        {crop_lines}

        הנחיות כלליות למתן המלצה:
        - התייחס לסוג השטח (חלקה או חממה). אם הגידול לא מתאים לשטח שנבחר, ציין זאת בהמלצה בצורה ברורה. 
        - במקרה של אי-התאמה, אין צורך לפרט מעבר לכך.
        - אם השטח מתאים לגידול, יש להמשיך בהמלצה על בסיס הקטגוריות הבאות:

        הנחיות עונתיות:
        - שתילת עצים או כרמים (שתילה שאינה מזרעים) מומלצת רק לפני ט"ו באב.
        - אם התאריך הנוכחי הוא לאחר ט"ו באב ({'כן' if is_after_tu_bav else 'לא'}), ציין שיש להמתין לעונה מתאימה.
        - זריעת זרעים מומלצת בעונות האביב (מרץ–מאי) או הסתיו (ספטמבר–נובמבר).
        - העונה הנוכחית היא: {season}.

        פורמט הפלט:
        1. החזר טבלה בפורמט HTML בלבד עם העמודות הבאות:
        - שם חלקה
        - סוג גידול
        - (לא חייב להשתמש בכל המלאי אלא רק מה שמומלץ לפי גודל החלקה)כמות זרעים לזריעה (בק"ג) או מספר שתילים
        - מרחק שתילה מומלץ (במטרים)

        2. לאחר הטבלה, החזר פסקאות הסבר בפורמט HTML המפרטות את ההמלצות והסיבות לכל חלקה.

        דגשים לפורמט:
        - החזר HTML תקני בלבד, ללא שימוש בתווי Markdown או סימני קוד כמו ```html או ```.
        - שמור על מבנה טבלה קבוע גם אם הנתונים משתנים.
        - פסקאות ההסבר צריכות להיות קצרות, ממוקדות ומבוססות על עקרונות חקלאיים.
        אין להשתמש במבנים אחרים או סימונים לא סטנדרטיים.
        """


        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=500
        )

        content = response['choices'][0]['message']['content']
        return jsonify({"suggestion": content})

    except Exception as e:
        return jsonify({"error": f"שגיאה: {str(e)}"}), 500




@optimal_bp.route("/get_empty_plots", methods=["GET"])
def get_empty_plots():
    email = session.get("email") or session.get("manager_email")

    plots = list(db.plots.find({
        "manager_email": email,
        "$or": [
            {"crop_category": {"$in": ["none", "", None]}},
            {"crop": {"$in": ["none", "", None]}}
        ],
        "square_meters": {"$exists": True, "$type": "number", "$gt": 0}
    }, {
        "_id": 1,
        "plot_name": 1,
        "plot_type": 1,
        "square_meters": 1
    }))

    for p in plots:
        p["_id"] = str(p["_id"])
        p["size"] = f"{p['square_meters']} דונם"

    return jsonify(plots)


@optimal_bp.route("/update_plots", methods=["POST"])
def update_plots():
    try:
        import json  # לוודא שהייבוא קיים
        data = request.get_json()
        updates = data.get("updates", [])
        email = session.get("email") or session.get("manager_email")

        if not updates:
            return jsonify({"error": "No update data provided"}), 400

        skipped_plots = []

        for upd in updates:
            plot_name = upd.get("plot_name")
            crop = upd.get("crop")
            raw_quantity = upd.get("quantity_planted", "")

            if not plot_name or not crop:
                skipped_plots.append(plot_name or "Unnamed Plot")
                continue

            # Clean and parse quantity
            quantity_str = ''.join(c for c in raw_quantity if c.isdigit() or c == '.')
            try:
                quantity_value = float(quantity_str)
                if quantity_value <= 0:
                    skipped_plots.append(plot_name)
                    continue
            except (ValueError, TypeError):
                skipped_plots.append(plot_name)
                continue

            # Find the plot
            plot = db.plots.find_one({"plot_name": plot_name, "manager_email": email})
            if not plot:
                skipped_plots.append(plot_name)
                continue

            # Find the item in inventory
            supply_item = db.supply.find_one({
                "email": email,
                "category": "גידול",
                "name": crop
            })

            # Check if there's enough inventory
            if not supply_item or supply_item.get("quantity", 0) < quantity_value:
                skipped_plots.append(plot_name)
                continue

            # Get crop_category from JSON
            crop_category = "ירקות"
            try:
                with open("static/data/crops_data.json", "r", encoding="utf-8") as f:
                    crops_data = json.load(f)
                for entry in crops_data:
                    if crop in entry.get("values", []):
                        crop_category = entry.get("category", "ירקות")
                        break
            except Exception as e:
                print(f"⚠️ Failed to load crop category from JSON: {e}")

            # Update the plot
            db.plots.update_one(
                {"_id": plot["_id"]},
                {"$set": {
                    "crop": crop,
                    "crop_category": crop_category,
                    "quantity_planted": quantity_value,
                    "sow_date": datetime.now().strftime("%d/%m/%Y")
                }}
            )

            # Reduce inventory
            db.supply.update_one(
                {"email": email, "category": "גידול", "name": crop},
                {"$inc": {"quantity": -quantity_value}}
            )

        if skipped_plots:
            return jsonify({
                "success": True,
                "skipped": skipped_plots,
                "message": "Some plots were skipped due to invalid data or insufficient inventory."
            })

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

