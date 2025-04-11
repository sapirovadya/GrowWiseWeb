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

    # תיעוד זמן התחלת הבדיקות
    test_start_time = datetime.utcnow() - timedelta(seconds=1)

    with app.test_client() as client:
        yield client, test_start_time

    # ניקוי רכבים שנשמרו ע"י המנהל בבדיקות
    db.vehicles.delete_many({
        "manager_email": "manager@test.com"
    })


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"


# --- בדיקות אינטגרציה ---

def test_get_vehicles_manager_integration(client):
    client, _ = client
    login_as(client)
    db.vehicles.insert_many([
        {"vehicle_number": "ABC123", "manager_email": "manager@test.com"},
        {"vehicle_number": "XYZ999", "manager_email": "manager@test.com"}
    ])
    res = client.get("/get_vehicles")
    assert res.status_code == 200
    assert res.get_json() == ["ABC123", "XYZ999"]


def test_get_vehicles_co_manager_integration(client):
    client, _ = client
    login_as(client, role="co_manager", email="co@test.com")
    db.vehicles.insert_one({
        "vehicle_number": "CO456",
        "manager_email": "manager@test.com"
    })
    res = client.get("/get_vehicles")
    assert res.status_code == 200
    assert "CO456" in res.get_json()


def test_get_vehicles_not_found(client):
    client, _ = client
    login_as(client)
    res = client.get("/get_vehicles")
    assert res.status_code == 404


# --- בדיקות יחידה עם mock ---

from unittest.mock import patch, MagicMock
import app.modules.expenses.routes as expenses_routes

def test_get_vehicles_manager_success(client):
    client, _ = client
    login_as(client, role="manager")

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter([
        {"vehicle_number": "123"},
        {"vehicle_number": "456"}
    ])
    mock_vehicles = MagicMock()
    mock_vehicles.find.return_value = mock_cursor

    with patch.object(expenses_routes.db, "vehicles", mock_vehicles):
        res = client.get("/get_vehicles")
        assert res.status_code == 200
        assert res.get_json() == ["123", "456"]


def test_get_vehicles_co_manager_success(client):
    client, _ = client
    login_as(client, role="co_manager", email="co@test.com")

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter([
        {"vehicle_number": "111"}
    ])
    mock_vehicles = MagicMock()
    mock_vehicles.find.return_value = mock_cursor

    with patch.object(expenses_routes.db, "vehicles", mock_vehicles):
        res = client.get("/get_vehicles")
        assert res.status_code == 200
        assert res.get_json() == ["111"]


def test_get_vehicles_unauthorized(client):
    client, _ = client
    res = client.get("/get_vehicles")
    assert res.status_code == 403


def test_get_vehicles_empty(client):
    client, _ = client
    login_as(client)
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter([])

    with patch("app.modules.expenses.routes.db.vehicles.find", return_value=mock_cursor):
        res = client.get("/get_vehicles")
        assert res.status_code == 404
