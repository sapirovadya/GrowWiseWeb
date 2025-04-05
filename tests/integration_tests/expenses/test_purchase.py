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


def test_add_purchase_integration(client):
    login_as(client)
    res = client.post("/purchase/add", json={"item": "tractor", "price": 5000})
    assert res.status_code == 201
    assert res.get_json()["message"] == "הרכישה נשמרה"