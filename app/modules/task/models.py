from datetime import datetime
import uuid

class task:
    def new_task(self, data):
        # יצירת מזהה ייחודי למשימה
        task_id = str(uuid.uuid4())

        # יצירת אובייקט המשימה
        task = {
            "id": task_id,
            "giver_email": data.get("giver_email"),
            "employee_email": data.get("employee_email"),
            "task_name": data.get("task_name"),
            "task_content": data.get("task_content"),
            "due_date": data.get("due_date"),  
            "status": data.get("status", "in_progress"),  # ברירת מחדל
        }

        return task
