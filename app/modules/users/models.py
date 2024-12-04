from flask import jsonify
from werkzeug.security import generate_password_hash
import uuid

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
            # "manager_email": data.get("manager_email") if data.get("role") == "worker" else None,
            # "is_approved": 0  # ברירת מחדל: לא מאושר
        }

        return user
