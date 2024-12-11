from flask import jsonify
from datetime import datetime
import uuid


class Plot:
    def __init__(self, plot_name, plot_type, width, length, manager_email, crop_category="none", crop="none", sow_date=None,Last_irrigation_date=None,Total_irrigation_amount=None):
        self.id = str(uuid.uuid4())
        self.plot_name = plot_name
        self.plot_type = plot_type
        self.width = width
        self.length = length
        self.manager_email = manager_email
        self.crop_category = crop_category
        self.crop = crop
        self.sow_date = sow_date
        self.Last_irrigation_date = Last_irrigation_date 
        self.Total_irrigation_amount = Total_irrigation_amount

    def to_dict(self):
        return {
            "_id": self.id,
            "plot_name": self.plot_name,
            "plot_type": self.plot_type,
            "width": self.width,
            "length": self.length,
            "manager_email": self.manager_email,
            "crop_category": self.crop_category,
            "crop": self.crop,
            "sow_date": self.sow_date,
            "Total_irrigation_amount": self.Total_irrigation_amount,
            "Last_irrigation_date": self.Last_irrigation_date,
        }
