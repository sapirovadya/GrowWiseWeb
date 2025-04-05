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


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"

# --- get_vehicles ---
def test_get_vehicles_manager_success(client):
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
    res = client.get("/get_vehicles")
    assert res.status_code == 403


def test_get_vehicles_empty(client):
    login_as(client)
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = iter([])
    with patch("app.modules.expenses.routes.db.vehicles.find", return_value=mock_cursor):
        res = client.get("/get_vehicles")
        assert res.status_code == 404

