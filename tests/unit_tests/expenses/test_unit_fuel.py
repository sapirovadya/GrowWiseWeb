import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from app.modules.expenses.routes import expenses_bp
import app.modules.expenses.routes as expenses_routes


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = 'test'
    app.config['TESTING'] = True
    app.register_blueprint(expenses_bp)
    with app.test_client() as client:
        yield client
    expenses_routes.db.fuel.delete_many({"email": "manager@test.com"})


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"

# --- add_fuel_expense ---
def test_add_fuel_expense_success(client):
    login_as(client)
    data = {
        "vehicle_number": "123",
        "fuel_amount": 50,
        "cost": 200,
        "refuel_type": "רגיל"
    }

    with patch.object(expenses_routes.Fuel, "add_fuel_entry", return_value={"message": "Success!"}):
        res = client.post("/add_fuel_expense", json=data)
        assert res.status_code == 201
        assert res.get_json()["message"] == "Success!"


def test_add_fuel_expense_missing_fields(client):
    login_as(client)
    data = {
        "vehicle_number": "123",
        "fuel_amount": 50,
        "cost": None,
        "refuel_type": "רגיל"
    }
    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 400


def test_add_fuel_expense_missing_month_for_dalkan(client):
    login_as(client)
    data = {
        "vehicle_number": "123",
        "fuel_amount": 50,
        "cost": 150,
        "refuel_type": "דלקן"
    }
    res = client.post("/add_fuel_expense", json=data)
    assert res.status_code == 400
    assert "Missing month" in res.get_json()["message"]


def test_add_fuel_expense_unauthorized(client):
    res = client.post("/add_fuel_expense", json={})
    assert res.status_code == 403
