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

    # ניקוי רכישות לפי מייל ותאריך
    db.purchases.delete_many({
        "email": "manager@test.com",
    })


def login_as(client, role="manager", email="manager@test.com"):
    with client.session_transaction() as sess:
        sess["role"] = role
        sess["email"] = email
        if role == "co_manager":
            sess["manager_email"] = "manager@test.com"


# בדיקת שמירה מוצלחת
def test_add_purchase_integration(client):
    client, _ = client
    login_as(client)
    res = client.post("/purchase/add", json={
        "category": "tools",
        "name": "tractor",
        "quantity": 1,
        "unit_price": 5000,
        "purchase_date": datetime.utcnow().isoformat()
    })
    assert res.status_code == 201
    assert res.get_json()["message"] == "הרכישה נשמרה"


# בדיקת חוסר הרשאות
def test_add_purchase_unauthorized(client):
    client, _ = client
    res = client.post("/purchase/add", json={})
    assert res.status_code == 403


# בדיקת יחידה עם מוקאינג
from unittest.mock import patch
import app.modules.expenses.routes as expenses_routes

def test_add_purchase_success_unit(client):
    client, _ = client
    login_as(client)

    mock_data = {
        "category": "tools",
        "name": "tractor",
        "quantity": 1,
        "unit_price": 1000,
        "purchase_date": datetime.utcnow().isoformat()
    }

    with patch.object(expenses_routes.Purchase, "add_purchase", return_value=mock_data):
        res = client.post("/purchase/add", json=mock_data)
        assert res.status_code == 201
        assert res.get_json()["message"] == "הרכישה נשמרה"
