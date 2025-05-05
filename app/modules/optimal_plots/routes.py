# modules/optimal_plots/routes.py
from flask import Blueprint, render_template, session, jsonify, request
import pymongo
import os
from dotenv import load_dotenv
import openai
from bson import ObjectId

load_dotenv()
optimal_bp = Blueprint("optimal_bp", __name__)
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"
TEMPERATURE = 1
MAX_TOKENS = 500

@optimal_bp.route("/management", methods=["GET"])
def optimal_management_page():
    return render_template("optimal_management.html")

@optimal_bp.route("/get_inventory", methods=["GET"])
def get_inventory():
    email = session.get("email") or session.get("manager_email")
    crops = list(db.supply.find({
        "email": email,
        "category": "גידול"
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
        manager = db.manager.find_one({"email": email})
        city = manager.get("location", "לא צוינה עיר")
        if not selected_crops or not selected_plots:
            return jsonify({"error": "חסרים נתונים"}), 400

        crop_data = list(db.supply.find({
            "email": email,
            "category": "גידול",
            "name": {"$in": selected_crops}
        }, {"_id": 0, "name": 1, "quantity": 1}))

        plot_data = []
        for p in selected_plots:
            found = db.plots.find_one({"_id": p["id"]}, {"plot_name": 1, "length": 1, "width": 1})
            if found:
                plot_data.append({
                    "plot_name": found["plot_name"],
                    "plot_type": p["type"],
                    "length": found["length"],
                    "width": found["width"]
                })

        plot_lines = "\n".join([f"{p['plot_name']} - {p['plot_type']} בגודל {p['length']}x{p['width']} מטר" for p in plot_data])
        crop_lines = "\n".join([f"{c['name']} - {c['quantity']} ק\"ג" for c in crop_data])
       
        prompt = f"""
        אתה אגרונום מומחה בעל ניסיון של למעלה מ-20 שנה בגידול ושתילת כל סוגי הגידולים הקיימים. כל תשובה שלך צריכה להיות מדויקת, מבוססת על ידע חקלאי מוסמך ואמין בלבד, בהתאם לשיטות הנהוגות במשרד החקלאות ובמחקר האגרונומי המעודכן ביותר.

        מיקום המשק: {city}

        רשימת חלקות או חממות זמינות לשתילה:
        {plot_lines}

        רשימת גידולים זמינים במלאי:
        {crop_lines}

        עבור כל חלקה, בצע ניתוח מקצועי של הגידול המתאים ביותר, תוך התייחסות לפרמטרים הבאים:
        1. סוג החלקה (חממה או אדמה)
        2. מיקום גיאוגרפי של המשק ({city})
        3. שטח החלקה
        4. אקלים מקומי מתאים לגידול

        בנוסף, עליך להתייחס לעיתוי בשנה בעת מתן ההמלצה:
        - שתילת עצים או כרמים (כל שתילה שאינה מתבצעת באמצעות זרעים) מומלצת רק לפני תאריך ט"ו באב (חודש אב בלוח השנה העברי). אם התאריך הנוכחי הוא לאחר ט"ו באב – יש לציין בהמלצה כי מומלץ להמתין לשתילה בעונה המתאימה, ולהימנע משתילה כעת.
        - זריעת זרעים מומלצת בעונות האביב (מרץ–מאי) או הסתיו (ספטמבר–נובמבר). אם התאריך הנוכחי אינו בעונה זו – יש לציין בהמלצה כי לא מומלץ לזרוע בתקופה זו, תוך הסבר מקצועי.

        אם אתה סבור שתנאי האקלים באזור המשק מאפשרים חריגה מהעקרונות הללו – פרט זאת בהסבר.

        אם גידול כלשהו אינו מתאים לחלקה מסוימת או למיקום הגיאוגרפי, אל תכלול אותו בטבלה. במקום זאת, הוסף טקסט הסבר מחוץ לטבלה בפורמט הבא:
        "מומלץ לא לשתול את הגידול [שם גידול] בחלקה [שם חלקה] שב-[שם עיר], מכיוון ש-[הסבר קצר]".

        לכל שתילה:
        - קבע האם יש להשתמש בזרעים או בייחורים (שתילים)
        - אם מדובר בזרעים – ציין את כמות הזרעים בקילוגרמים (ק"ג)
        - אם מדובר בייחורים – ציין רק את מספר השתילים (ללא תוספות טקסט)
        - המלץ על מרחק שתילה בין שתילים או ערוגות במטרים
        - ציין את מספר הערוגות הנדרש בהתאם לגודל החלקה והגידול

        החזר טבלה בפורמט HTML בלבד, עם העמודות הבאות:
        - שם חלקה
        - סוג גידול
        - כמות זרעים לזריעה (בק"ג) או מספר שתילים
        - מרחק שתילה מומלץ (במטרים)

        לאחר הטבלה, החזר הסברים מילוליים בפורמט HTML עבור כל חלקה, תוך שימוש במבנה קבוע לפסקה:

        בחלקה/חממה [שם חלקה] שב-[שם עיר] בשטח של [מספר] מ"ר, יש לשתול/לזרוע [סוג גידול], מכיוון ש-[הסבר מקצועי מותאם למיקום, סוג הקרקע והאקלים]. נדרשות [מספר] ערוגות, עם מרחק של [מספר] מטרים בין ערוגה לערוגה.

        יש להקפיד על ניסוח מקצועי, ברור, נטול סלנג או שפה לא תקנית.

        אין להשתמש בתווי Markdown או בסימני קוד כמו ```html או ``` – יש להחזיר HTML תקני בלבד.
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
        "length": {"$exists": True, "$type": "number", "$gt": 0},
        "width": {"$exists": True, "$type": "number", "$gt": 0}
    }, {
        "_id": 1,
        "plot_name": 1,
        "plot_type": 1,
        "length": 1,
        "width": 1
    }))

    for p in plots:
        p["_id"] = str(p["_id"])

    return jsonify(plots)
