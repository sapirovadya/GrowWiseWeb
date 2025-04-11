import pytest
import json
from flask import Flask, session
from datetime import datetime, timedelta
from app.modules.expenses.routes import expenses_bp, db


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(expenses_bp)

    inserted_fuel_ids = []

    # תיעוד זמן התחלת הבדיקה
    test_start_time = datetime.utcnow()

    # הוספת רכב לבדיקה (נניח שיש טבלת vehicles)
    db.vehicles.insert_one({
        "vehicle_number": "ABC123",
        "manager_email": "manager@test.com"
    })

    with app.test_client() as client:
        yield client, inserted_fuel_ids

    # מחיקת כל תיעודי fuel שנוצרו במהלך הבדיקה
    db.fuel.delete_many({
        "email": "manager@test.com",
    })

    # מחיקת הרכב
    db.vehicles.delete_many({"vehicle_number": "ABC123"})


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"


def test_add_fuel_expense_success(client):
    client, inserted_fuel_ids = client
    login_as(client)
    data = {
        "vehicle_number": "ABC123",
        "fuel_amount": 40,
        "cost": 300,
        "refuel_type": "רגיל"
    }

    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 201

    json_data = res.get_json()
    inserted_fuel_ids.append(json_data.get("_id"))  # רק אם אתה מחזיר ID

    assert json_data["vehicle_number"] == "ABC123"
    assert json_data["fuel_amount"] == 40
    assert json_data["cost"] == 300
    assert json_data["refuel_type"] == "רגיל"
    assert json_data["email"] == "manager@test.com"


def test_add_fuel_expense_missing_fields(client):
    client, _ = client
    login_as(client)
    data = {
        "vehicle_number": "ABC123",
        "fuel_amount": 40,
        "cost": None,
        "refuel_type": "רגיל"
    }

    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 400


def test_add_fuel_expense_missing_month_dalkan(client):
    client, _ = client
    login_as(client)
    data = {
        "vehicle_number": "ABC123",
        "fuel_amount": 40,
        "cost": 200,
        "refuel_type": "דלקן"
        # חסר month
    }

    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 400
