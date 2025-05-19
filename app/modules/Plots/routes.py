from flask import Blueprint, render_template, request, redirect, url_for, jsonify,session
import pymongo
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import uuid 
from modules.Plots.models import Plot
from modules.task.models import task
import openai
from bson import ObjectId
from werkzeug.utils import secure_filename

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")
# Configuration for OpenAI
MODEL = "gpt-4o"
TEMPERATURE = 1
MAX_TOKENS = 350

UPLOAD_FOLDER = "static/uploads/kosher"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

plot_bp = Blueprint('plot_bp', __name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
tasks_collection = db["plot_tasks"]
harvest_records = {} 


# def format_date(value):
#     if isinstance(value, str):
#         try:
#             value = datetime.strptime(value, "%Y-%m-%d")
#         except:
#             return value
#     return value.strftime("%-d-%-m-%Y")

def format_date(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d")
        except:
            return value
    try:
        return value.strftime("%d-%m-%Y").lstrip("0").replace("-0", "-")
    except:
        return str(value)

plot_bp.add_app_template_filter(format_date, name='format_date')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
             f" יש להתשמש בשפה מקצועית וצכבדת בלבד. לא להשתמש בסלנג."
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
    return render_template('track_greenhouse.html', email=email, manager_email=manager_email, name=name, role=role)

@plot_bp.route("/save_plot", methods=["POST"])
def save_plot():
    try:
        plot_id = str(uuid.uuid4())

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

        plot_name = request.form.get("plot_name")
        plot_type = request.form.get("plot_type")
        square_meters = float(request.form.get("square_meters", 0))
        crop_name = request.form.get("crop", "none")
        sow_date = request.form.get("sow_date", "")
        irrigation_water_type = request.form.get("irrigation_water_type", "none")
        quantity_planted_raw = request.form.get("quantity_planted")
        kosher_required = request.form.get("kosher_required") == "on"
        is_existing = request.form.get("is_existing", "false").lower() == "true"

        if not plot_name or not plot_type:
            return jsonify({"error": "שם החלקה וסוג החלקה הם שדות חובה."}), 400
        if square_meters <= 0:
            return jsonify({"error": "גודל חלקה חייב להיות מספר חיובי."}), 400

        existing_plot = db.plots.find_one({"plot_name": plot_name, "manager_email": manager_email, "archive": False})
        if existing_plot:
            return jsonify({"error": "כבר קיימת חלקה פעילה בשם זה. יש לבחור שם אחר או לארכב את הקיימת."}), 400

        crop_category = "none"
        if crop_name != "none":
            try:
                import json
                with open("static/data/crops_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    if crop_name in entry.get("values", []):
                        crop_category = entry.get("category", "none")
                        break
            except Exception as e:
                print("⚠️ שגיאה בקריאת crops_data.json:", e)

        quantity_planted = 0
        if crop_name != "none" and crop_category != "none":
            if not sow_date:
                return jsonify({"error": "נא למלא את תאריך הזריעה"}), 400

            today = datetime.today().date()
            sow_date_obj = datetime.strptime(sow_date, "%Y-%m-%d").date()
            if sow_date_obj > today:
                return jsonify({"error": "לא ניתן להזין תאריך עתידי לזריעה"}), 400

            if is_existing:
                try:
                    quantity_planted = float(quantity_planted_raw or 0)
                except (ValueError, TypeError):
                    quantity_planted = 0
            else:
                try:
                    quantity_planted = float(quantity_planted_raw)
                    if quantity_planted <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    return jsonify({"error": "נא למלא כמות זריעה תקינה (בק\"ג)."}), 400

                crop_entry = db.supply.find_one({"email": manager_email, "name": crop_name, "category": "גידול"})
                if not crop_entry or crop_entry["quantity"] < quantity_planted:
                    return jsonify({"error": f"הזנת כמות הגדולה מהמלאי. ניתן לשתול עד {crop_entry['quantity']} ק\"ג."}), 400

                db.supply.update_one(
                    {"email": manager_email, "name": crop_name, "category": "גידול"},
                    {"$inc": {"quantity": -quantity_planted}}
                )

        kosher_certificate_path = None
        if kosher_required and 'kosher_certificate' in request.files:
            file = request.files['kosher_certificate']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{plot_id}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                file.save(save_path)
                kosher_certificate_path = save_path

        new_plot = {
            "_id": plot_id,
            "plot_name": plot_name,
            "plot_type": plot_type,
            "square_meters": square_meters,
            "manager_email": manager_email,
            "crop_category": crop_category,
            "crop": crop_name,
            "sow_date": sow_date,
            "quantity_planted": quantity_planted,
            "last_irrigation_date": None,
            "total_irrigation_amount": None,
            "harvest_date": None,
            "crop_yield": None,
            "price_yield": None,
            "irrigation_water_type": irrigation_water_type,
            "kosher_required": kosher_required,
            "kosher_certificate": kosher_certificate_path,
            "archive": False
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

    try:
        category_data = db.crops_options.find_one({"category": {"$regex": f"^{category}$", "$options": "i"}})
        
        if not category_data:
            return jsonify({"crops": []}), 200

        values = category_data.get("values", [])
        if not isinstance(values, list):
            raise TypeError("Invalid type for 'values'")

        return jsonify({"crops": values}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
   


@plot_bp.route("/get_plots", methods=["GET"])
def get_plots():
    role = session.get("role")
    email = session.get("email")

    if not role or not email:
        return jsonify({"error": "User is not logged in or missing role."}), 403
    query = {"archive": False}

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
        try:
            plot_oid = ObjectId(plot_id)
        except Exception:
            return jsonify({"error": "Invalid plot ID"}), 404

        plot = db.plots.find_one({"_id": plot_oid})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        plot["_id"] = str(plot["_id"])
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
        try:
            plot_oid = plot_id
        except Exception:
            return jsonify({"error": "Invalid plot ID"}), 404
        data = request.form
        file = request.files.get("kosher_certificate")

        required_fields = ['crop', 'sow_date', 'quantity_planted']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        crop_category = data.get('crop_category')
        if not crop_category:
            return jsonify({"error": "Missing field: crop_category"}), 400

        plot = db.plots.find_one({"_id": plot_oid})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        manager_email = plot.get("manager_email")
        crop_name = data['crop']
        crop_category = data['crop_category']
        quantity_planted = float(data['quantity_planted'])
        sow_date = data['sow_date']

        today = datetime.today().date()
        sow_date_obj = datetime.strptime(sow_date, "%Y-%m-%d").date()
        if sow_date_obj > today:
            return jsonify({"error": "לא ניתן להזין תאריך עתידי לזריעה"}), 400

        crop_entry = db.supply.find_one({"email": manager_email, "name": crop_name, "category": "גידול"})
        if not crop_entry or crop_entry["quantity"] < quantity_planted:
            return jsonify({"error": f"הזנת כמות גדולה מהמלאי. ניתן לשתול עד {crop_entry['quantity']} ק\"ג."}), 400

        db.supply.update_one(
            {"email": manager_email, "name": crop_name, "category": "גידול"},
            {"$inc": {"quantity": -quantity_planted}}
        )

        # הכנה לעדכון במסד הנתונים
        update_fields = {
            "crop_category": crop_category,
            "crop": crop_name,
            "sow_date": sow_date,
            "quantity_planted": quantity_planted,
            "kosher_required": 'kosher_required' in data,
            "irrigation_water_type": data.get('irrigation_water_type', 'none')
        }

        # אם קובץ צורף - שמור אותו
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            full_path = os.path.join(UPLOAD_FOLDER, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)  # מוודא שהתיקייה קיימת
            file.save(full_path)
            update_fields["kosher_certificate"] = full_path

        # ביצוע העדכון
        update_result = db.plots.update_one(
            {"_id": plot_oid},
            {"$set": update_fields}
        )

        if update_result.modified_count == 0:
            return jsonify({"error": "לא בוצע עדכון, ייתכן ואין שינוי"}), 400

        return jsonify({"message": "Plot updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@plot_bp.route('/upload_kosher/<plot_id>', methods=['POST'])
def upload_kosher_file(plot_id):
    file = request.files.get('kosher_certificate')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        db.plots.update_one({"_id": plot_id}, {
            "$set": {"kosher_certificate": f"{UPLOAD_FOLDER}/{filename}"}
        })
        return redirect(url_for('plot_bp.plot_details', id=plot_id))
    return "העלאה נכשלה", 400


@plot_bp.route('/update_irrigation/<plot_id>', methods=['POST'])
def update_irrigation(plot_id):
    try:
        data = request.get_json()
        irrigation_amount = data.get('irrigation_amount')
        irrigation_water_type = data.get('irrigation_water_type', 'none')

        if not irrigation_amount or not isinstance(irrigation_amount, (int, float)) or irrigation_amount <= 0:
            return jsonify({"error": "Invalid irrigation amount"}), 400

        try:
            plot_oid = plot_id
        except Exception:
            return jsonify({"error": "Invalid plot ID"}), 404

        # Fetch the plot details
        plot = db.plots.find_one({"_id": plot_oid})
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
            {"_id": plot_oid},
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
            "irrigation_water_type": irrigation_water_type,
            "Irrigation_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        db.irrigation.insert_one(new_irrigation)

        return jsonify({"message": "Irrigation updated successfully", "new_total": new_total}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@plot_bp.route('/get_plot_info/<plot_id>', methods=['GET'])
def get_plot_info(plot_id):
    try:
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        irrigation_water_type = plot.get("irrigation_water_type", "none")
        return jsonify({"irrigation_water_type": irrigation_water_type}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@plot_bp.route('/archive_plot/<plot_id>', methods=['POST'])
def archive_plot(plot_id):
    try:
        data = request.get_json()
        harvest_date = data.get('harvest_date')
        crop_yield = data.get('crop_yield')
        price_yield = data.get('price_yield', None)  # יכול להיות None

        if not harvest_date or crop_yield is None:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            crop_yield = float(crop_yield)
        except (ValueError, TypeError):
            return jsonify({"error": "Crop yield must be a number"}), 400

        # לא לזרוק שגיאה אם אין מחיר
        price_value = float(price_yield) if price_yield not in [None, ""] else None

        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        # עדכון במסד
        db.plots.update_one(
            {"_id": plot_id},
            {
                "$set": {
                    "harvest_date": harvest_date,
                    "crop_yield": crop_yield,
                    "price_yield": price_value,
                    "archive": True
                }
            }
        )
        return jsonify({"message": "החלקה הועברה לארכיון"}), 200

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
            filter_email = email
        elif role == "co_manager":
            filter_email = manager_email
        else:
            return jsonify({"error": "Unauthorized role."}), 403

        # שליפת חלקות מארכיון טבלת plots (ששדה archive=True)
        plots_archive = list(db.plots.find({"manager_email": filter_email, "archive": True}))

        # שליפת רשומות קציר ממסד הנתונים plots_yield
        plots_yield = list(db.plots_yield.find({"manager_email": filter_email}))

        # המרת ObjectId למחרוזת
        for plot in plots_archive + plots_yield:
            if "_id" in plot:
                plot["_id"] = str(plot["_id"])

        return render_template("plots_archive.html", plots=plots_archive + plots_yield)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@plot_bp.route("/get_harvested_plots", methods=["GET"])
def get_harvested_plots():
    try:
        filter_plots = {
            "harvest_date": {"$ne": None},
            "price_yield": None,
            "archive": True
        }
        filter_yield = {"price_yield": None}

        plots = list(db.plots.find(filter_plots, {"plot_name": 1, "harvest_date": 1}))
        plots_yield = list(db.plots_yield.find(filter_yield, {"plot_name": 1, "harvest_date": 1}))

        combined = plots + plots_yield
        for p in combined:
            p["_id"] = str(p["_id"]) if "_id" in p else None
        return jsonify({"plots": combined}), 200
    except Exception as e:
        return jsonify({"error": f"שגיאה בשליפת החלקות: {str(e)}"}), 500

@plot_bp.route("/get_crop_details", methods=["GET"])
def get_crop_details():
    try:
        plot_name = request.args.get("plot_name")
        harvest_date = request.args.get("sow_date")
        plot_id = request.args.get("plot_id")

        # חיפוש לפי plot_id קודם (אם קיים)
        if plot_id:
            plot = db.plots.find_one({"_id": plot_id}, {"crop": 1, "crop_yield": 1})
            if not plot:
                plot = db.plots_yield.find_one({"_id": plot_id}, {"crop": 1, "crop_yield": 1})
        else:
            plot = None

        # fallback לפי שם ותאריך קציר אם לא נמצא לפי ID
        if not plot and plot_name and harvest_date:
            query = {"plot_name": plot_name, "harvest_date": harvest_date}
            plot = db.plots.find_one(query, {"crop": 1, "crop_yield": 1})
            if not plot:
                plot = db.plots_yield.find_one(query, {"crop": 1, "crop_yield": 1})

        # עדיין לא נמצא?
        if not plot:
            return jsonify({"error": "לא נמצאו נתוני יבול לחלקה זו"}), 404

        return jsonify({
            "crop": plot.get("crop", ""),
            "crop_yield": plot.get("crop_yield") if isinstance(plot.get("crop_yield"), (int, float)) else 0
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@plot_bp.route("/update_price_yield", methods=["POST"])
def update_price_yield():
    try:
        data = request.json
        plot_id = data.get("plot_id")
        price_yield = float(data.get("price_yield"))
        
        if plot_id:
            result = db.plots.update_one(
                {"_id": ObjectId(plot_id)},
                {"$set": {"price_yield": price_yield}}
            )
            if result.matched_count == 0:
                result = db.plots_yield.update_one(
                    {"_id": ObjectId(plot_id)},
                    {"$set": {"price_yield": price_yield}}
                )
            if result.matched_count == 0:
                return jsonify({"error": "לא נמצאה חלקה עם ID מתאים"}), 404
        else:
            # fallback למקרה ישן
            plot_name = data.get("plot_name")
            harvest_date = data.get("sow_date")
            result = db.plots.update_one(
                {"plot_name": plot_name, "harvest_date": harvest_date},
                {"$set": {"price_yield": price_yield}}
            )
            if result.matched_count == 0:
                result = db.plots_yield.update_one(
                    {"plot_name": plot_name, "harvest_date": harvest_date},
                    {"$set": {"price_yield": price_yield}}
                )
            if result.matched_count == 0:
                return jsonify({"error": "לא נמצאה חלקה מתאימה לעדכון"}), 404

        return jsonify({"message": "המחיר נשמר בהצלחה"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@plot_bp.route("/get_sow_dates", methods=["GET"])
def get_sow_dates():
    plot_name = request.args.get("plot_name")
    if not plot_name:
        return jsonify({"error": "Missing plot_name"}), 400

    try:
        condition = {"plot_name": plot_name, "price_yield": None, "sow_date": {"$ne": None}}

        dates_main = db.plots.find(condition, {"sow_date": 1})
        dates_yield = db.plots_yield.find(condition, {"sow_date": 1})

        unique_dates = list(set(
            [d["sow_date"] for d in dates_main if d.get("sow_date")] +
            [d["sow_date"] for d in dates_yield if d.get("sow_date")]
        ))

        return jsonify({"dates": sorted(unique_dates)}), 200
    except Exception as e:
        return jsonify({"error": f"שגיאה בשליפת תאריכי זריעה: {str(e)}"}), 500



@plot_bp.route("/plot_tasks", methods=["POST"])
def add_plot_task():
    data = request.get_json()

    required_fields = ["plot_id", "task_name", "employee_email"]
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"success": False, "error": "יש למלא את כל השדות החובה."}), 400

    employee = db.employee.find_one({
        "email": data["employee_email"],
        "is_approved": 1
    })

    if not employee:
        return jsonify({"success": False, "error": "לא ניתן לשייך משימה לעובד שלא אושר."}), 400

    due_date = data.get("due_date")
    if due_date:
        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "error": "פורמט תאריך לא תקין."}), 400
    else:
        due_date = None

    task_data = {
        "plot_id": data["plot_id"],
        "task_name": data["task_name"],
        "task_content": data.get("task_content", ""),
        "employee_email": data["employee_email"],
        "giver_email": session.get("email"),
        "due_date": due_date,
        "status": "in_progress"
    }

    new_task_obj = task().new_task(task_data)
    new_task_obj["plot_id"] = data["plot_id"]

    inserted = tasks_collection.insert_one(new_task_obj)
    new_task_obj["_id"] = str(inserted.inserted_id)  
    return jsonify({"success": True, "message": "המשימה נוספה בהצלחה", "task": new_task_obj}), 200



@plot_bp.route("/plot_tasks/<plot_id>", methods=["GET"])
def get_plot_tasks(plot_id):
    role = session.get("role")
    user_email = session.get("email")
    manager_email = user_email if role == "manager" else session.get("manager_email")

    is_manager = role in ["manager", "co_manager"]

    query = {"plot_id": plot_id}
    if role == "employee":
        query["employee_email"] = user_email  # עובד רגיל → רואה רק את עצמו

    # שליפת כל המשימות לחלקה
    tasks = list(tasks_collection.find(query))
    for t in tasks:
        t["_id"] = str(t["_id"])

    existing_employees_cursor = db.employee.find({
        "manager_email": manager_email,
        "is_approved": 1 
    })
    existing_employees = {
        e["email"]: f'{e.get("first_name", "")} {e.get("last_name", "")}'.strip()
        for e in existing_employees_cursor
    }

    filtered_tasks = []
    for t in tasks:
        if t["employee_email"] in existing_employees:
            filtered_tasks.append(t)

    # החזרת העובדים לשיבוץ
    employees_list = [{"email": email, "name": name} for email, name in existing_employees.items()]

    return jsonify({
        "tasks": filtered_tasks,
        "is_manager": is_manager,
        "employees": employees_list
    })

@plot_bp.route("/update_task_employees", methods=["POST"])
def update_task_employees():
    try:
        data = request.get_json()
        updates = data.get("updates", [])
        completed_tasks = data.get("completed_tasks", [])

        # עדכון העובדים
        for update in updates:
            task_id = update.get("task_id")
            employee_email = update.get("employee_email")
            if task_id and employee_email:
                tasks_collection.update_one(
                    {"_id": ObjectId(task_id)},
                    {"$set": {"employee_email": employee_email}}
                )

        # עדכון סטטוס של משימות שסומנו כ"done"
        for task_id in completed_tasks:
            tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {"$set": {"status": "done"}}
            )

        return jsonify({"success": True, "message": "המשימות עודכנו בהצלחה"})

    except Exception as e:
        print("❌ שגיאה בעדכון עובדים/סטטוס:", e)
        return jsonify({"success": False, "error": str(e)})



@plot_bp.route('/harvest_plot/<plot_id>', methods=['POST'])
def harvest_plot(plot_id):
    try:
        data = request.get_json()
        crop_yield = data.get('crop_yield')
        price_yield = data.get('price_yield', None)

        try:
            crop_yield = float(crop_yield)
        except ValueError:
            return jsonify({"error": "Invalid numeric values."}), 400

        # שליפת פרטי החלקה
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

        plot_name = plot.get("plot_name")
        sow_date = plot.get("sow_date")
        harvest_date = datetime.utcnow().strftime('%Y-%m-%d')

        # שמירה לטבלת plots_yield במסד הנתונים
        yield_entry = {
            "plot_id": plot_id,
            "plot_name": plot_name,
            "harvest_date": harvest_date,
            "crop": plot.get("crop"),
            "quantity_planted": plot.get("quantity_planted"),
            "crop_yield": crop_yield,
            "price_yield": float(price_yield) if price_yield else None,
            "total_irrigation_amount": plot.get("total_irrigation_amount"),
            "sow_date": sow_date,
            "manager_email": plot.get("manager_email"),
            "source": "harvest_plot"
        }

        db.plots_yield.insert_one(yield_entry)

        # איפוס שדות בחלקה המקורית
        db.plots.update_one(
            {"_id": plot_id},
            {"$set": {
                "price_yield": None,
                "crop_yield": None,
                "harvest_date": None,
                "last_irrigation_date": None,
                "total_irrigation_amount": None
            }}
        )

        return jsonify({"message": "הקציר נשמר בהצלחה והחלקה אופסה."}), 200

    except Exception as e:
        print("Error in harvest_plot:", e)
        return jsonify({"error": "Server error."}), 500

@plot_bp.route("/get_harvest_dates", methods=["GET"])
def get_harvest_dates():
    plot_name = request.args.get("plot_name")
    if not plot_name:
        return jsonify({"error": "Missing plot_name"}), 400

    try:
        condition = {"plot_name": plot_name, "price_yield": None, "harvest_date": {"$ne": None}}
        dates_main = db.plots.find(condition, {"harvest_date": 1})
        dates_yield = db.plots_yield.find(condition, {"harvest_date": 1})

        unique_dates = list(set(
            [d["harvest_date"] for d in dates_main if d.get("harvest_date")] +
            [d["harvest_date"] for d in dates_yield if d.get("harvest_date")]
        ))

        return jsonify({"dates": sorted(unique_dates)}), 200
    except Exception as e:
        return jsonify({"error": f"שגיאה בשליפת תאריכי קציר: {str(e)}"}), 500
