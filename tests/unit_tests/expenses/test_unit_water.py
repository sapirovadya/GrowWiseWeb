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


# --- add_water ---
def test_add_water_success(client):
    login_as(client, role="manager")
    mock_data = {"price": 120, "date": "2025-04-04"}

    with patch("app.modules.expenses.routes.db.water.insert_one") as mock_insert:
        res = client.post("/water/add", json=mock_data)
        assert res.status_code == 200
        assert res.get_json()["message"] == "הרכישה נשמרה בהצלחה!"


def test_add_water_missing_fields(client):
    login_as(client, role="manager")
    res = client.post("/water/add", json={"price": 0, "date": ""})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_add_water_server_error(client):
    login_as(client, role="manager")

    mock_collection = MagicMock()
    mock_collection.insert_one.side_effect = Exception("Mock error")

    with patch.object(expenses_routes.db, "water", mock_collection):
        res = client.post("/water/add", json={"price": 50, "date": "2025-04-04"})
        assert res.status_code == 500
        assert "error" in res.get_json()


