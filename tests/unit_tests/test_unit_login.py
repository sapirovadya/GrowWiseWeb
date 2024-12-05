from app.modules.users.routes import login
import pytest
from unittest.mock import MagicMock
from werkzeug.security import generate_password_hash
from flask import Flask, Blueprint, jsonify

@pytest.fixture
def app():
    """יוצר אפליקציית Flask לבדיקה."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "test_secret"

    # רישום Blueprints מדומים
    manager_bp = Blueprint('manager_bp', __name__)
    employee_bp = Blueprint('employee_bp', __name__)

    @manager_bp.route('/manager/home')
    def manager_home_page():
        return jsonify({"message": "Manager Home"})

    @employee_bp.route('/employee/home')
    def employee_home_page():
        return jsonify({"message": "Employee Home"})

    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(employee_bp, url_prefix='/employee')

    return app

# בדיקת התחברות מוצלחת של מנהל
def test_login_manager_success_unit(mocker, app):
    with app.test_request_context(json={
        "email": "manager@example.com",
        "password": "securepassword"
    }):
        # יצירת mock של בסיס נתונים
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = {
            "first_name": "John",
            "password": generate_password_hash("securepassword")
        }

        # הוספת db ל-context של האפליקציה
        with app.app_context():
            app.db = mock_db
            response = login()

        # בדיקות
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "login successfuly"
        assert data["role"] == "manager"
        assert "redirect_url" in data

# בדיקת התחברות עם סיסמה שגויה
def test_login_incorrect_password_unit(mocker, app):
    with app.test_request_context(json={
        "email": "manager@example.com",
        "password": "wrongpassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = {
            "password": generate_password_hash("securepassword")
        }

        with app.app_context():
            app.db = mock_db
            response = login()

        assert response.status_code == 400
        data = response.get_json()
        assert data["message"] == "one of the detail is incorrect"

# בדיקת התחברות עם אימייל שלא קיים
def test_login_user_not_found_unit(mocker, app):
    with app.test_request_context(json={
        "email": "nonexistent@example.com",
        "password": "somepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.employee.find_one.return_value = None

        with app.app_context():
            app.db = mock_db
            response = login()

        assert response.status_code == 400
        data = response.get_json()
        assert data["message"] == "user not found"

# בדיקת התחברות של עובד שלא אושר
def test_login_employee_not_approved_unit(mocker, app):
    with app.test_request_context(json={
        "email": "employee@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.employee.find_one.return_value = {
            "password": generate_password_hash("securepassword"),
            "is_approved": 0
        }

        with app.app_context():
            app.db = mock_db
            response = login()

        assert response.status_code == 400
        data = response.get_json()
        assert data["message"] == "user is not approved"
