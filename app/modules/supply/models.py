import uuid
from datetime import datetime
import pymongo
import os
from dotenv import load_dotenv

# טעינת משתני סביבה
load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
supply_collection = db["supply"]

class Supply:
    def __init__(self, category, name, quantity, email):
        self.id = str(uuid.uuid4())  # מזהה ייחודי
        self.category = category  # סוג המוצר (זרעים, דברי הדברה, מוצרים כלליים)
        self.name = name  # שם המוצר
        self.quantity = quantity  # כמות 
        self.email = email 

    def to_dict(self):
        """המרת האובייקט למילון עבור שמירה ב-MongoDB"""
        return {
            "_id": self.id,
            "category": self.category,
            "name": self.name,
            "quantity": self.quantity,
            "email": self.email,
        }

    @staticmethod
    def add_supply(data):
        """הוספת מוצר חדש למלאי"""
        new_supply = Supply(
            category=data.get("category"),
            name=data.get("name"),
            quantity=float(data.get("quantity")),
            email=data.get("email")
        )
        supply_collection.insert_one(new_supply.to_dict())
        return new_supply.to_dict()
