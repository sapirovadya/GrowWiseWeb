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
        import os
        plot_id = str(uuid.uuid4())

        # שליפת פרטי משתמש מה־session
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

        # נתונים מהטופס
        plot_name = request.form.get("plot_name")
        plot_type = request.form.get("plot_type")
        square_meters = float(request.form.get("square_meters", 0))

        if not plot_name or not plot_type:
            return jsonify({"error": "שם החלקה וסוג החלקה הם שדות חובה."}), 400
        if square_meters <= 0:
            return jsonify({"error": "גודל חלקה חייב להיות מספר חיובי."}), 400

        crop_category = request.form.get("crop_category", "none")
        crop_name = request.form.get("crop", "none")
        sow_date = request.form.get("sow_date", "")
        irrigation_water_type = request.form.get("irrigation_water_type", "none")
        quantity_planted_raw = request.form.get("quantity_planted")
        kosher_required = request.form.get("kosher_required") == "on"

        # שמירת הקובץ אם קיים
        kosher_certificate_path = None
        if kosher_required and 'kosher_certificate' in request.files:
            file = request.files['kosher_certificate']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{plot_id}_{file.filename}")
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # לוודא שהתיקייה קיימת
                file.save(save_path)
                kosher_certificate_path = save_path

        quantity_planted = None

        if crop_category != "none" and crop_name != "none":
            if not sow_date:
                return jsonify({"error": "נא למלא את תאריך הזריעה"}), 400

            today = datetime.today().date()
            sow_date_obj = datetime.strptime(sow_date, "%Y-%m-%d").date()
            if sow_date_obj > today:
                return jsonify({"error": "לא ניתן להזין תאריך עתידי לזריעה"}), 400

            if not quantity_planted_raw or float(quantity_planted_raw) <= 0:
                return jsonify({"error": "נא למלא כמות זריעה תקינה (בק״ג)."}), 400

            quantity_planted = float(quantity_planted_raw)

            crop_entry = db.supply.find_one({
                "email": manager_email,
                "name": crop_name,
                "category": "גידול"
            })
            if not crop_entry or crop_entry["quantity"] < quantity_planted:
                return jsonify({"error": f"הזנת כמות הגדולה מהמלאי. ניתן לשתול עד {crop_entry['quantity']} ק\"ג."}), 400

            db.supply.update_one(
                {"email": manager_email, "name": crop_name, "category": "גידול"},
                {"$inc": {"quantity": -quantity_planted}}
            )

        # יצירת רשומת חלקה
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
            "kosher_certificate": kosher_certificate_path
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
        price_yield = data.get('price_yield', None)  # אם המשתמש לא מילא - השדה יישאר None

        if not harvest_date or not crop_yield:
            return jsonify({"error": "Missing required fields"}), 400

        if not isinstance(crop_yield, (int, float)):
            return jsonify({"error": "Crop yield must be a number"}), 400

        # אין צורך ב-ObjectId
        plot = db.plots.find_one({"_id": plot_id})
        if not plot:
            return jsonify({"error": "Plot not found"}), 404

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
    try:
        plot_name = request.args.get("plot_name")
        sow_date = request.args.get("sow_date")

        plot = db.plots.find_one({"plot_name": plot_name, "sow_date": sow_date}, {"crop": 1, "crop_yield": 1})
        
        if not plot:
            return jsonify({"error": "לא נמצאו נתונים"}), 404

        return jsonify({"crop": plot.get("crop", ""), "crop_yield": plot.get("crop_yield", 0)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# עדכון מחיר לק"ג תפוקה
@plot_bp.route("/update_price_yield", methods=["POST"])
def update_price_yield():
    try:
        data = request.json
        plot_name = data.get("plot_name")
        sow_date = data.get("sow_date")
        price_yield = data.get("price_yield")

        if not plot_name or not sow_date or price_yield is None:
            raise ValueError("Missing required fields")

        price_yield = float(price_yield)

        db.plots.update_one(
            {"plot_name": plot_name, "sow_date": sow_date},
            {"$set": {"price_yield": price_yield}}
        )
        return jsonify({"message": "המחיר נשמר בהצלחה"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@plot_bp.route("/get_sow_dates", methods=["GET"])
def get_sow_dates():
    plot_name = request.args.get("plot_name")

    if not plot_name:
        return jsonify({"error": "Missing plot_name"}), 400

    try:
        dates = db.plots.find(
            {"plot_name": plot_name, "sow_date": {"$ne": None}, "price_yield": None},
            {"sow_date": 1, "_id": 0}
        )
        # הוספת סינון נוסף לוודא שאין None
        date_list = [plot["sow_date"] for plot in dates if plot.get("sow_date") is not None]

        return jsonify({"dates": date_list}), 200
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

    # שליפת העובדים הקיימים
    existing_employees_cursor = db.employee.find({
        "manager_email": manager_email,
        "is_approved": 1  # 🔥 מוסיפים רק עובדים מאושרים
    })
    existing_employees = {
        e["email"]: f'{e.get("first_name", "")} {e.get("last_name", "")}'.strip()
        for e in existing_employees_cursor
    }

    # סינון המשימות — מציג רק אם העובד קיים
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