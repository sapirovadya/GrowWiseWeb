import pytest
from flask import Flask, session, jsonify
from unittest.mock import patch, MagicMock
from app.modules.attendance.routes import (
    attendance_bp,  # <- הוספנו את זה כדי לרשום אותו
    report_attendance, get_user_attendance, get_manager_attendance,
    manual_attendance_report, update_attendance, get_attendance_record
)


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.config["TESTING"] = True

    app.register_blueprint(attendance_bp)

    with app.test_client() as client:
        yield client

# --- report_attendance ---
def test_report_attendance_authorized_check_in(client):
    with client.session_transaction() as sess:
        sess["email"] = "employee@test.com"
        sess["role"] = "employee"
        sess["first_name"] = "Test"
        sess["last_name"] = "User"
        sess["manager_email"] = "manager@test.com"

    with patch("app.modules.attendance.routes.attendance_collection.insert_one") as mock_insert:
        res = client.post("/attendance/report", json={"action": "check_in"})
        assert res.status_code in (200, 201)
        mock_insert.assert_called_once()

def test_report_attendance_unauthorized(client):
    res = client.post("/attendance/report", json={"action": "check_in"})
    assert res.status_code == 403

# --- get_user_attendance ---
def test_get_user_attendance_records(client):
    with client.session_transaction() as sess:
        sess["email"] = "employee@test.com"
        sess["role"] = "employee"

    with patch("app.modules.attendance.routes.attendance_collection.find") as mock_find:
        mock_find.return_value = []
        res = client.get("/attendance/user_records")
        assert res.status_code == 200

# --- get_manager_attendance ---
def test_get_manager_attendance_records_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    with patch("app.modules.attendance.routes.attendance_collection.find") as mock_find:
        mock_find.return_value = []
        res = client.get("/attendance/manager_records")
        assert res.status_code == 200

def test_get_manager_attendance_records_co_manager(client):
    with client.session_transaction() as sess:
        sess["role"] = "co_manager"
        sess["manager_email"] = "manager@test.com"
        sess["email"] = "co@example.com"

    with patch("app.modules.attendance.routes.attendance_collection.find") as mock_find:
        mock_find.return_value = []
        res = client.get("/attendance/manager_records")
        assert res.status_code == 200

# --- manual_attendance_report ---
def test_manual_attendance_missing_fields(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    res = client.post("/attendance/manual_report", json={})
    assert res.status_code == 400

# --- update_attendance ---
def test_update_attendance_invalid_data(client):
    res = client.post("/attendance/update_attendance", json={})
    assert res.status_code == 403

def test_update_attendance_valid_data(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    with patch("app.modules.attendance.routes.attendance_collection.update_one") as mock_update:
        mock_update.return_value.modified_count = 1
        res = client.post("/attendance/update_attendance", json={
            "id": "605c5fddfc13ae1f3e000001",
            "check_in": "2025-04-04T07:30",
            "check_out": "2025-04-04T15:30"
        })
        assert res.status_code == 200
        mock_update.assert_called_once()

# --- get_attendance_record ---
def test_get_attendance_record_invalid(client):
    res = client.get("/attendance/get_record/invalidid")
    assert res.status_code in (400, 404, 500)
