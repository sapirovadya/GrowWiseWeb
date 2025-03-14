from datetime import datetime
import os
import uuid

class VehicleManagement:
    
    def new_vehicle(self, data):
        vehicle_id = str(uuid.uuid4())
        vehicles = {
            "id": vehicle_id,
            "vehicle_number": data.get("vehicle_number"),  
            "vehicle_type": data.get("vehicle_type"),  
            "test_date": data.get("test_date"),  
            "test_cost": data.get("test_cost"),  
            "last_service_date": data.get("last_service_date"),  
            "service_cost": data.get("service_cost"),  
            "insurance_date": data.get("insurance_date"),  
            "insurance_cost": data.get("insurance_cost"), 
            "authorized_drivers": data.get("authorized_drivers")
        }
        return vehicles


