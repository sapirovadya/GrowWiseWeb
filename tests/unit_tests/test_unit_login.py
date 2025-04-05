import pytest
from flask import Flask, Blueprint, jsonify
from werkzeug.security import generate_password_hash
from unittest.mock import MagicMock
from app.modules.users.routes import login

# ---------- App Fixture -----------

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test_secret"
    app.config['TESTING'] = True

    manager_bp = Blueprint('manager_bp', __name__)
    co_manager_bp = Blueprint('co_manager_bp', __name__)
    employee_bp = Blueprint('employee_bp', __name__)
    job_seeker_bp = Blueprint('job_seeker_bp', __name__)

    @manager_bp.route('/manager/home')
    def manager_home_page():
        return jsonify({"message": "Manager Home"})

    @co_manager_bp.route('/co_manager/home')
    def co_manager_home_page():
        return jsonify({"message": "Co-Manager Home"})

    @employee_bp.route('/employee/home')
    def employee_home_page():
        return jsonify({"message": "Employee Home"})

    @job_seeker_bp.route('/job_seeker/home')
    def job_seeker_home_page():
        return jsonify({"message": "Job Seeker Home"})

    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(co_manager_bp, url_prefix='/co_manager')
    app.register_blueprint(employee_bp, url_prefix='/employee')
    app.register_blueprint(job_seeker_bp, url_prefix='/job_seeker')

    return app


# ---------- בדיקות Login -----------

def test_login_manager_success_unit(mocker, app):
    with app.test_request_context(json={
        "email": "manager@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = {
            "first_name": "John",
            "password": generate_password_hash("securepassword")
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 200
        data = response.get_json()
        assert data["message"] == "login successfuly"
        assert data["role"] == "manager"
        assert "redirect_url" in data


def test_login_employee_success_unit(mocker, app):
    with app.test_request_context(json={
        "email": "employee@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = None
        mock_db.job_seeker.find_one.return_value = None
        mock_db.employee.find_one.return_value = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "employee@example.com",
            "password": generate_password_hash("securepassword"),
            "is_approved": 1,
            "manager_email": "manager@example.com"
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 200
        data = response.get_json()
        assert data["message"] == "login successfuly"
        assert data["role"] == "employee"
        assert "redirect_url" in data



def test_login_co_manager_success_unit(mocker, app):
    with app.test_request_context(json={
        "email": "co@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.employee.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = {
            "first_name": "Co",
            "password": generate_password_hash("securepassword"),
            "is_approved": 1,
            "manager_email": "manager@example.com"
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 200
        data = response.get_json()
        assert data["role"] == "manager"  # שותף מזוהה כמנהל
        assert data["message"] == "login successfuly"
        assert "redirect_url" in data


def test_login_job_seeker_success_unit(mocker, app):
    with app.test_request_context(json={
        "email": "job@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.employee.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = None
        mock_db.job_seeker.find_one.return_value = {
            "first_name": "Job",
            "password": generate_password_hash("securepassword")
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 200
        data = response.get_json()
        assert data["role"] == "job_seeker"
        assert data["message"] == "login successfuly"
        assert "redirect_url" in data


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
            response, status = login()

        assert status == 400
        data = response.get_json()
        assert data["message"] == "one of the detail is incorrect"


def test_login_user_not_found_unit(mocker, app):
    with app.test_request_context(json={
        "email": "nonexistent@example.com",
        "password": "somepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.employee.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = None
        mock_db.job_seeker.find_one.return_value = None

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 400
        data = response.get_json()
        assert data["message"] == "user not found"


def test_login_employee_not_approved_unit(mocker, app):
    with app.test_request_context(json={
        "email": "employee@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = None
        mock_db.job_seeker.find_one.return_value = None
        mock_db.employee.find_one.return_value = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "employee@example.com",
            "password": generate_password_hash("securepassword"),
            "is_approved": 0,
            "manager_email": "manager@example.com"
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 400
        data = response.get_json()
        assert data["message"] == "user is not approved"

def test_login_co_manager_not_approved_unit(mocker, app):
    with app.test_request_context(json={
        "email": "co@example.com",
        "password": "securepassword"
    }):
        mock_db = MagicMock()
        mock_db.manager.find_one.return_value = None
        mock_db.employee.find_one.return_value = None
        mock_db.co_manager.find_one.return_value = {
            "password": generate_password_hash("securepassword"),
            "is_approved": 0
        }

        with app.app_context():
            app.db = mock_db
            response, status = login()

        assert status == 400
        data = response.get_json()
        assert data["message"] == "user is not approved"
