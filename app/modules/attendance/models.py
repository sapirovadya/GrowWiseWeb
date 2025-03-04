from datetime import datetime
import uuid

class attendance:
    def new_attendance(self, data):

        attendance_id = str(uuid.uuid4())

        attendance = {
            "id": attendance_id,
            "email": data.get("email"),
            "manager_email": data.get("manager_email"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "check_in": datetime.now(),
            "check_out": None,
            "total_hours": None
        }

        return attendance
