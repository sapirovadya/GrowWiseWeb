from flask import jsonify
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime

class User:
    def signup(self, data):
        # יצירת מזהה ייחודי למשתמש
        user_id = str(uuid.uuid4())

        # הצפנת סיסמה
        hashed_password = generate_password_hash(data.get("password"))

        # יצירת אובייקט המשתמש
        user = {
            "id": user_id,
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "password": hashed_password,
            "role": data.get("role"),  # מנהל או עובד
        }

        return user


class Notification:
    def __init__(self, email,employee_email, content):
        self.id = str(uuid.uuid4())  # מזהה ייחודי להתראה
        self.email = email  # כתובת אימייל של המשתמש
        self.employee_email = employee_email
        self.content = content  # תוכן ההתראה
        self.created_at = datetime.now()  # זמן יצירת ההתראה
        self.seen = False  # סטטוס צפייה

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "employee_email": self.employee_email,
            "content": self.content,
            "created_at": self.created_at,
            "seen": self.seen
        }

