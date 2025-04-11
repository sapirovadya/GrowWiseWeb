import pytest
import json
from flask import Flask, session
from bson import ObjectId
from datetime import datetime,timedelta
from app.modules.attendance.routes import attendance_bp, attendance_collection, db

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(attendance_bp)

    from app.modules.attendance.routes import db, attendance_collection

    inserted_ids = []
    test_employee = {
        "email": "employee@test.com",
        "first_name": "Test",
        "last_name": "User",
        "manager_email": "manager@test.com"
    }

    db.employee.insert_one(test_employee)

    # תיעוד זמן התחלת הבדיקות
    test_start_time = datetime.utcnow() - timedelta(seconds=1)

    with app.test_client() as client:
        yield client, inserted_ids

    # מחיקת כל הרשומות שנוצרו ע"י המייל הזה בבדיקות (ולא רק לפי inserted_ids)
    attendance_collection.delete_many({
        "email": "employee@test.com"
    })

    db.employee.delete_one({"email": "employee@test.com"})


# התחברות כעובד
def login_as_employee(client):
    with client.session_transaction() as sess:
        sess["email"] = "employee@test.com"
        sess["role"] = "employee"
        sess["first_name"] = "Test"
        sess["last_name"] = "User"
        sess["manager_email"] = "manager@test.com"


# התחברות כמנהל
def login_as_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"


# --- דיווח נוכחות ושאילת רשומות אישיות ---
def test_full_attendance_flow_employee(client):
    client, inserted_ids = client
    login_as_employee(client)

    res = client.post("/attendance/report", json={"action": "check_in"})
    assert res.status_code in (200, 201)
    data = res.get_json()
    inserted_id = data.get("inserted_id")
    if inserted_id:
        inserted_ids.append(ObjectId(inserted_id))

    res2 = client.get("/attendance/user_records")
    assert res2.status_code == 200
    assert b"attendance_records" in res2.data


# --- דיווח ידני ושליפת כללית ---
def test_attendance_flow_manager_manual_report(client):
    client, inserted_ids = client
    login_as_manager(client)

    res = client.post("/attendance/manual_report", json={})
    assert res.status_code in (400, 422)

    res2 = client.get("/attendance/manager_records")
    assert res2.status_code == 200
    assert b"attendance_records" in res2.data


# --- עדכון רשומה קיימת ---
def test_update_attendance_record(client):
    client, inserted_ids = client
    login_as_manager(client)

    checkin = "2025-04-04T08:00"
    checkout = "2025-04-04T16:00"

    res_create = client.post("/attendance/manual_report", json={
        "email": "employee@test.com",
        "check_in": checkin,
        "check_out": checkout
    })
    assert res_create.status_code == 200
    inserted_id = res_create.get_json().get("inserted_id")
    if inserted_id:
        inserted_ids.append(ObjectId(inserted_id))

    res_update = client.post("/attendance/update_attendance", json={
        "id": inserted_id,
        "check_in": "2025-04-04T07:30",
        "check_out": "2025-04-04T15:30"
    })
    assert res_update.status_code == 200
    res_json = res_update.get_json()
    assert res_json["message"] == "הדיווח עודכן בהצלחה!"


# --- שליפה בודדת לפי ID ---
def test_get_single_record_by_id(client):
    client, inserted_ids = client
    login_as_manager(client)

    res = client.post("/attendance/manual_report", json={
        "email": "employee@test.com",
        "check_in": "2025-04-04T08:00",
        "check_out": "2025-04-04T16:00"
    })
    assert res.status_code == 200
    inserted_id = res.get_json().get("inserted_id")
    assert inserted_id is not None
    inserted_ids.append(ObjectId(inserted_id))

    res_single = client.get(f"/attendance/get_record/{inserted_id}")
    assert res_single.status_code == 200
    assert b"check_in" in res_single.data
    assert b"check_out" in res_single.data


# --- תהליך Check-in ו־Check-out לעובד ---
def test_employee_check_out_flow(client):
    client, inserted_ids = client
    login_as_employee(client)

    # Check-in
    res_checkin = client.post("/attendance/report", json={"action": "check_in"})
    assert res_checkin.status_code == 200
    data_checkin = res_checkin.get_json()
    assert data_checkin["message"] == "שעת הכניסה נשמרה בהצלחה"
    inserted_id = data_checkin.get("inserted_id")
    if inserted_id:
        inserted_ids.append(ObjectId(inserted_id))

    # Check-out
    res_checkout = client.post("/attendance/report", json={"action": "check_out"})
    assert res_checkout.status_code == 200
    data_checkout = res_checkout.get_json()
    assert "message" in data_checkout
    assert "check_out" in data_checkout
    assert "סה\"כ" in data_checkout["message"] or "שעת היציאה נשמרה" in data_checkout["message"]
