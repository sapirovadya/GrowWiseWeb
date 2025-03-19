import uuid
from datetime import datetime
import pymongo
import os
from dotenv import load_dotenv

load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
purchases_collection = db["purchases"]
irrigation_collection = db["irrigation"]
water_collection = db["water"]
vehicles_collection = db["vehicles"]
vehicle_service_collection = db["vehicle_service_history"]
vehicle_test_collection = db["vehicle_test_history"]
vehicle_insurance_collection = db["vehicle_insurance_history"]

class Purchase:
    def __init__(self, email, category, name, quantity, unit_price, purchase_date=None):
        self.id = str(uuid.uuid4()) 
        self.email = email  
        self.category = category 
        self.name = name  
        self.quantity = quantity 
        self.unit_price = unit_price 
        self.purchase_date = purchase_date if purchase_date else datetime.utcnow()  # תאריך הרכישה

    def to_dict(self):
        return {
            "_id": self.id,
            "email": self.email,
            "category": self.category,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "purchase_date": self.purchase_date
        }

    @staticmethod
    def add_purchase(data):
        new_purchase = Purchase(
            email=data.get("email"),
            category=data.get("category"),
            name=data.get("name"),
            quantity=data.get("quantity"),
            unit_price=data.get("unit_price"),
            purchase_date=data.get("purchase_date")
        )
        purchases_collection.insert_one(new_purchase.to_dict())
        return new_purchase.to_dict()

class Irrigation:
    def __init__(self, email, name,sow_date, quantity_irrigation, Irrigation_date):
        self.id = str(uuid.uuid4()) 
        self.email = email
        self.name = name
        self.quantity_irrigation = quantity_irrigation
        self.sow_date = sow_date
        self.Irrigation_date = Irrigation_date if Irrigation_date else datetime.utcnow()

    def to_dict(self):
        return {
            "_id": self.id,
            "email": self.email,
            "name": self.name,
            "quantity_irrigation": self.quantity_irrigation,
            "sow_date": self.sow_date,
            "Irrigation_date": self.Irrigation_date
        }

    @staticmethod
    def add_irrigation(data):
        new_irrigation = Irrigation(
            email=data.get("email"),
            name=data.get("name"),
            quantity_irrigation=data.get("quantity_irrigation"),
            sow_date=data.get("sow_date"),
            Irrigation_date=data.get("Irrigation_date")
        )
        irrigation_collection.insert_one(new_irrigation.to_dict())
        return new_irrigation.to_dict()

class Water:
    def __init__(self, email, price, date):
        self.id = str(uuid.uuid4())  # מזהה ייחודי
        self.email = email  # כתובת אימייל של המשתמש שביצע את ההכנסה
        self.price = price  # מחיר לקו״ב 
        self.date = date if date else datetime.utcnow()  # תאריך הכנסת הנתון

    def to_dict(self):
        return {
            "_id": self.id,
            "email": self.email,
            "price": self.price,
            "date": self.date
        }

    @staticmethod
    def add_water(data):
        new_water = Water(
            email=data.get("email"),
            price=data.get("price"),
            date=data.get("date"),
        )
        water_collection.insert_one(new_water.to_dict())
        return new_water.to_dict()


class VehicleServiceHistory:
    
    def new_service_record(self, data):
        """ יצירת רשומת טיפול חדשה לכלי שטח """
        service_id = str(uuid.uuid4())
        service_record = {
            "id": service_id,
            "vehicle_number": data.get("vehicle_number"),  # מספר רכב
            "service_date": data.get("service_date"),  # תאריך טיפול
            "service_cost": data.get("service_cost"),  # עלות טיפול
            "service_notes": data.get("service_notes") or None,
            "manager_email": data.get("manager_email")

        }
        return service_record

class VehicleTestHistory:
    
    def new_test_record(self, data):
        """ יצירת רשומת טסט חדשה לכלי שטח """
        test_id = str(uuid.uuid4())
        test_record = {
            "id": test_id,
            "vehicle_number": data.get("vehicle_number"),  # מספר רכב
            "test_date": data.get("test_date"),  # תאריך חידוש טסט
            "test_cost": data.get("test_cost"),
            "manager_email": data.get("manager_email")
        }
        return test_record

class VehicleInsuranceHistory:
    
    def new_insurance_record(self, data):
        """ יצירת רשומת ביטוח חדשה לכלי שטח """
        insurance_id = str(uuid.uuid4())
        insurance_record = {
            "id": insurance_id,
            "vehicle_number": data.get("vehicle_number"),  # מספר רכב
            "insurance_date": data.get("insurance_date"),  # תאריך ביטוח
            "insurance_cost": data.get("insurance_cost"),
            "manager_email": data.get("manager_email")
        }
        return insurance_record