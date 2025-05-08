from flask import Blueprint, request, jsonify, session,render_template
from modules.supply.models import Supply
import pymongo
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from modules.expenses.models import Sale

load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
supply_collection = db["supply"] 

supply_bp = Blueprint('supply_bp', __name__, url_prefix="/supply")

@supply_bp.route('/supply-inventory')
def supply_inventory():
    return render_template('/supply/supply_inventory.html')

@supply_bp.route('/supply-inventory-seeds')
def supply_inventory_seeds():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    user_email = session["email"]
    manager_email = session.get("manager_email", "")

    query_email = user_email if session["role"] in ["manager"] else manager_email

    supply_items = list(supply_collection.find(
        {"email": query_email, "category": "גידול"}, 
        {"_id": 0, "name": 1, "quantity": 1}
    ))

    return render_template('/supply/supply_seeds.html', supplies=supply_items)

@supply_bp.route('/supply-inventory-pesticides')
def supply_inventory_pesticides():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    user_email = session["email"]
    manager_email = session.get("manager_email", "")

    query_email = user_email if session["role"] in ["manager"] else manager_email

    supply_items = list(supply_collection.find(
        {"email": query_email, "category": "הדברה"}, 
        {"_id": 0, "name": 1, "quantity": 1}
    ))
    return render_template('/supply/supply_pesticides.html', supplies=supply_items)

@supply_bp.route('/supply-inventory-general')
def supply_inventory_general():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    user_email = session["email"]
    manager_email = session.get("manager_email", "")

    # בדיקה אם המשתמש הוא מנהל או עובד
    query_email = user_email if session["role"] in ["manager"] else manager_email

    # שליפת כל המוצרים שבהם category == "גידול"
    supply_items = list(supply_collection.find(
        {"email": query_email, "category": "מוצר כללי"}, 
        {"_id": 0, "name": 1, "quantity": 1}
    ))
    return render_template('/supply/supply_general.html', supplies=supply_items)

@supply_bp.route('/add', methods=['POST'])
def add_supply():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    data = request.json
    email = session["email"]
    category = data.get("category")
    name = data.get("name")
    quantity = float(data.get("quantity"))
    existing_supply = supply_collection.find_one({"email": email, "category": category, "name": name})

    if existing_supply:
        return jsonify({
            "error": "מוצר זה קיים במלאי, אם ברצונך לשנות את הכמות אנא עדכן זאת בטבלה."
        }), 400  

    new_supply = Supply.add_supply(data)
    return jsonify({"message": "המוצר נוסף בהצלחה", "supply": new_supply}), 201


@supply_bp.route('/get_quantity', methods=['GET'])
def get_quantity():
    product_name = request.args.get("name")
    category = request.args.get("category")
    email = session.get("email") or session.get("manager_email")

    if not product_name or not category:
        return jsonify({"error": "שם מוצר או קטגוריה חסרים"}), 400

    supply_entry = supply_collection.find_one({
        "email": email,
        "name": product_name,
        "category": category
    })

    if not supply_entry:
        return jsonify({"error": "המוצר לא נמצא במלאי"}), 404

    return jsonify({"quantity": supply_entry.get("quantity", 0)}), 200


@supply_bp.route('/update_quantity', methods=['POST'])
def update_quantity():
    data = request.json
    crop_name = data.get("crop_name")
    quantity_used = float(data.get("quantity_used", 0))

    email = session.get("email") or session.get("manager_email")

    crop_entry = db.supply.find_one({"email": email, "name": crop_name, "category": "גידול"})
    if not crop_entry or crop_entry["quantity"] < quantity_used:
        return jsonify({"error": "אין מספיק כמות במלאי לעדכון"}), 400

    db.supply.update_one(
        {"email": email, "name": crop_name, "category": "גידול"},
        {"$inc": {"quantity": -quantity_used}}
    )

    return jsonify({"message": "כמות עודכנה בהצלחה"}), 200


@supply_bp.route("/available_crops", methods=['GET'])
def get_available_crops():
    try:
        if session.get("role") == "manager":
            email = session.get("email")
        else:
            email = session.get("manager_email")

        crops = list(db.supply.find({"email": email, "category": "גידול"}, {"_id": 0, "name": 1, "quantity": 1}))
        return jsonify(crops), 200
    except Exception as e:
        return jsonify({"error": f"שגיאת שרת: {str(e)}"}), 500

@supply_bp.route('/get_category', methods=['GET'])
def get_category():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    product_name = request.args.get("name")
    email = session.get("email") or session.get("manager_email")

    supply_entry = supply_collection.find_one({"email": email, "name": product_name})
    if not supply_entry:
        return jsonify({"error": "המוצר לא נמצא"}), 404

    return jsonify({"category": supply_entry.get("category", "")}), 200

@supply_bp.route('/update_supply_quantity', methods=['POST'])
def update_supply_quantity():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    data = request.json
    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    quantity_to_add = float(data.get("quantity", 0))

    email = session.get("email") or session.get("manager_email")

    if not name or not category:
        print("⚠️ שם או קטגוריה חסרים!")
        return jsonify({"error": "שם או קטגוריה חסרים"}), 400

    supply_entry = supply_collection.find_one({
        "email": email,
        "name": {"$regex": f"^{name}$", "$options": "i"},
        "category": category
    })

    if not supply_entry:
        return jsonify({"error": "המוצר לא נמצא במלאי"}), 404

    result = supply_collection.update_one(
        {"email": email, "name": {"$regex": f"^{name}$", "$options": "i"}, "category": category},
        {"$inc": {"quantity": quantity_to_add}}
    )

    if result.modified_count == 0:
        return jsonify({"error": "המוצר לא נמצא במלאי"}), 404

    return jsonify({"message": "כמות עודכנה בהצלחה"}), 200

    
@supply_bp.route("/add_sale", methods=["POST"])
def add_sale():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    data = request.get_json()
    email = session.get("email") or session.get("manager_email")
    name = data.get("name")
    quantity = float(data.get("quantity", 0))
    unit_price = float(data.get("unit_price", 0))
    sale_date_str = data.get("sale_date")

    if not name or quantity <= 0 or unit_price <= 0 or not sale_date_str:
        return jsonify({"error": "יש להזין את כל השדות החיוניים"}), 400

    try:
        sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({"error": "פורמט תאריך לא תקין"}), 400

    sale_data = {
        "email": email,
        "name": name,
        "quantity": quantity,
        "unit_price": unit_price,
        "sale_date": sale_date
    }

    Sale.add_sale(sale_data)

    supply_collection.update_one(
        {"email": email, "name": name},
        {"$inc": {"quantity": -quantity}}
    )

    return jsonify({"message": "המכירה נשמרה בהצלחה"}), 200


@supply_bp.route("/update_inventory_quantity", methods=["POST"])
def update_inventory_quantity():
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 403

    data = request.get_json()
    name = data.get("name")
    new_quantity = float(data.get("new_quantity", -1))

    if not name or new_quantity < 0:
        return jsonify({"error": "ערך כמות לא תקין"}), 400

    email = session.get("email") if session.get("role") == "manager" else session.get("manager_email")

    result = supply_collection.update_one(
        {"email": email, "name": name},
        {"$set": {"quantity": new_quantity}}
    )

    if result.modified_count == 0:
        return jsonify({"error": "המוצר לא נמצא או שהכמות לא השתנתה"}), 404

    return jsonify({"message": "הכמות עודכנה בהצלחה"}), 200