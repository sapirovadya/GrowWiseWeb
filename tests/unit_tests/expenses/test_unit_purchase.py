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


# --- add_purchase ---
def test_add_purchase_success(client):
    login_as(client, role="manager")
    mock_data = {"item": "tractor", "price": 1000}

    with patch.object(expenses_routes.Purchase, "add_purchase", return_value=mock_data):
        res = client.post("/purchase/add", json=mock_data)
        assert res.status_code == 201
        assert res.get_json()["message"] == "הרכישה נשמרה"


def test_add_purchase_unauthorized(client):
    res = client.post("/purchase/add", json={})
    assert res.status_code == 403