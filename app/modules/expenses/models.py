import uuid
from datetime import datetime, timezone
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
fuel_collection = db["fuel"]
equipment_sales_collection = db["equipment_sales"]

class Purchase:
    def __init__(self, email, category, name, quantity, unit_price, purchase_date=None):
        self.id = str(uuid.uuid4()) 
        self.email = email  
        self.category = category 
        self.name = name  
        self.quantity = quantity 
        self.unit_price = unit_price 
        self.purchase_date = purchase_date if purchase_date else datetime.now(timezone.utc)  # תאריך הרכישה

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
        self.Irrigation_date = Irrigation_date if Irrigation_date else datetime.now(timezone.utc)

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
        self.date = date if date else datetime.now(timezone.utc)  # תאריך הכנסת הנתון

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


class Fuel:
    def __init__(self, email, vehicle_number, refuel_type, refuel_date, month=None, fuel_amount=None, cost=None):
        self.id = str(uuid.uuid4()) 
        self.email = email
        self.vehicle_number = vehicle_number
        self.refuel_type = refuel_type  
        self.refuel_date = refuel_date
        self.month = month  
        self.fuel_amount = fuel_amount
        self.cost = cost
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "_id": self.id,
            "email": self.email,
            "vehicle_number": self.vehicle_number,
            "refuel_type": self.refuel_type,
            "refuel_date": self.refuel_date,
            "month": self.month,
            "fuel_amount": self.fuel_amount,
            "cost": self.cost,
            "created_at": self.created_at,
        }

    @staticmethod
    def add_fuel_entry(data):
        new_entry = Fuel(
            email=data.get("email"),
            vehicle_number=data.get("vehicle_number"),
            refuel_type=data.get("refuel_type"),
            refuel_date=data.get("refuel_date"),
            month=data.get("month"),
            fuel_amount=data.get("fuel_amount"),
            cost=data.get("cost"),
        )
        fuel_collection.insert_one(new_entry.to_dict())
        return new_entry.to_dict()

class Sale:
    def __init__(self, email, name, quantity, unit_price, sale_date=None):
        self.id = str(uuid.uuid4())
        self.email = email
        self.name = name
        self.quantity = quantity
        self.unit_price = unit_price
        self.sale_date = sale_date if sale_date else datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "_id": self.id,
            "email": self.email,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "sale_date": self.sale_date
        }

    @staticmethod
    def add_sale(data):
        new_sale = Sale(
            email=data.get("email"),
            name=data.get("name"),
            quantity=data.get("quantity"),
            unit_price=data.get("unit_price"),
            sale_date=data.get("sale_date")
        )
        equipment_sales_collection.insert_one(new_sale.to_dict())
        return new_sale.to_dict()