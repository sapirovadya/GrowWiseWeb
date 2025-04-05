import pytest
import json
from flask import Flask, session
from unittest.mock import MagicMock, patch
from bson import ObjectId
from app.modules.attendance.routes import attendance_bp
import app.modules.attendance.routes as attendance_routes


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(attendance_bp)

    with app.test_client() as client:
        yield client


def login_as_employee(client):
    with client.session_transaction() as sess:
        sess["email"] = "employee@test.com"
        sess["role"] = "employee"
        sess["first_name"] = "Test"
        sess["last_name"] = "User"
        sess["manager_email"] = "manager@test.com"


def login_as_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"


# --- דיווח נוכחות ושאילת רשומות אישיות ---
def test_full_attendance_flow_employee(client):
    login_as_employee(client)

    res = client.post("/attendance/report", json={"action": "check_in"})
    assert res.status_code in (200, 201)

    res2 = client.get("/attendance/user_records")
    assert res2.status_code == 200
    assert b"attendance_records" in res2.data


# --- דיווח ידני ושליפת כללית ---
def test_attendance_flow_manager_manual_report(client):
    login_as_manager(client)

    res = client.post("/attendance/manual_report", json={})
    assert res.status_code in (400, 422)

    res2 = client.get("/attendance/manager_records")
    assert res2.status_code == 200
    assert b"attendance_records" in res2.data


# --- עדכון רשומה קיימת ---
def test_update_attendance_record(client):
    login_as_manager(client)

    checkin = "2025-04-04T08:00"
    checkout = "2025-04-04T16:00"

    # יצירת mock ל־db ולעדכון
    mock_db = MagicMock()
    mock_db.employee.find_one.return_value = {
        "first_name": "Test",
        "last_name": "User",
        "manager_email": "manager@test.com"
    }

    mock_attendance_collection = MagicMock()
    inserted_id = ObjectId()
    mock_attendance_collection.insert_one.return_value.inserted_id = inserted_id
    mock_attendance_collection.update_one.return_value.modified_count = 1

    with patch.dict(attendance_routes.__dict__, {
        'db': mock_db,
        'attendance_collection': mock_attendance_collection
    }):
        res_create = client.post("/attendance/manual_report", json={
            "email": "employee@test.com",
            "check_in": checkin,
            "check_out": checkout
        })
        assert res_create.status_code == 200

        # שימוש ב־ID מדומה
        res_update = client.post("/attendance/update_attendance", json={
            "id": str(inserted_id),
            "check_in": "2025-04-04T07:30",
            "check_out": "2025-04-04T15:30"
        })
        assert res_update.status_code == 200
        res_json = res_update.get_json()
        assert res_json["message"] == "הדיווח עודכן בהצלחה!"

# --- שליפה בודדת לפי ID ---
def test_get_single_record_by_id(client):
    login_as_manager(client)

    mock_db = MagicMock()
    mock_db.employee.find_one.return_value = {
        "first_name": "Test",
        "last_name": "User",
        "manager_email": "manager@test.com"
    }

    with patch.dict(attendance_routes.__dict__, {'db': mock_db}):
        res_records = client.get("/attendance/manager_records")
        data = json.loads(res_records.data.decode("utf-8"))

        if not data["attendance_records"]:
            client.post("/attendance/manual_report", json={
                "email": "employee@test.com",
                "check_in": "2025-04-04T08:00",
                "check_out": "2025-04-04T16:00"
            })
            res_records = client.get("/attendance/manager_records")
            data = json.loads(res_records.data.decode("utf-8"))

        record = next((r for r in data["attendance_records"] if r["email"] == "employee@test.com"), None)
        assert record is not None

        record_id = record["_id"]

        res_single = client.get(f"/attendance/get_record/{record_id}")
        assert res_single.status_code == 200
        assert b"check_in" in res_single.data
        assert b"check_out" in res_single.data

def test_employee_check_out_flow(client):
    login_as_employee(client)

    # שלב 1: ביצוע check-in
    res_checkin = client.post("/attendance/report", json={"action": "check_in"})
    assert res_checkin.status_code == 200
    data_checkin = res_checkin.get_json()
    assert data_checkin["message"] == "שעת הכניסה נשמרה בהצלחה"

    # שלב 2: ביצוע check-out
    res_checkout = client.post("/attendance/report", json={"action": "check_out"})
    assert res_checkout.status_code == 200
    data_checkout = res_checkout.get_json()

    assert "message" in data_checkout
    assert "check_out" in data_checkout
    assert "סה\"כ" in data_checkout["message"] or "שעת היציאה נשמרה" in data_checkout["message"]

