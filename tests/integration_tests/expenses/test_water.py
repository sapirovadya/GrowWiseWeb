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



def test_add_water_integration(client):
    login_as(client)
    res = client.post("/water/add", json={"price": 100, "date": "2025-04-04"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "הרכישה נשמרה בהצלחה!"


def test_add_water_invalid_data(client):
    login_as(client)
    res = client.post("/water/add", json={"price": 0, "date": ""})
    assert res.status_code == 400
