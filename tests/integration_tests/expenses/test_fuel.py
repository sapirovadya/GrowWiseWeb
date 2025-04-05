import pytest
import mongomock
from flask import Flask
from app.modules.expenses.routes import expenses_bp
import app.modules.expenses.routes as expenses_routes

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test'
    app.register_blueprint(expenses_bp)

    # מחליפים את ה-db האמיתי בפייק DB
    expenses_routes.db = mongomock.MongoClient().db
    with app.test_client() as client:
        yield client


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"
def test_add_fuel_expense_success(client):
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
    assert json_data["vehicle_number"] == "ABC123"
    assert json_data["fuel_amount"] == 40
    assert json_data["cost"] == 300
    assert json_data["refuel_type"] == "רגיל"
    assert json_data["email"] == "manager@test.com"


def test_add_fuel_expense_missing_fields(client):
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
    login_as(client)
    data = {
        "vehicle_number": "ABC123",
        "fuel_amount": 40,
        "cost": 200,
        "refuel_type": "דלקן"
    }
    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 400
