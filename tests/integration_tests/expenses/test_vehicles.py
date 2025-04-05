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

def test_get_vehicles_manager_integration(client):
    login_as(client)
    expenses_routes.db.vehicles.insert_many([
        {"vehicle_number": "ABC123", "manager_email": "manager@test.com"},
        {"vehicle_number": "XYZ999", "manager_email": "manager@test.com"}
    ])
    res = client.get("/get_vehicles")
    assert res.status_code == 200
    assert res.get_json() == ["ABC123", "XYZ999"]


def test_get_vehicles_co_manager_integration(client):
    login_as(client, role="co_manager", email="co@test.com")
    expenses_routes.db.vehicles.insert_one({
        "vehicle_number": "CO456",
        "manager_email": "manager@test.com"
    })
    res = client.get("/get_vehicles")
    assert res.status_code == 200
    assert "CO456" in res.get_json()


def test_get_vehicles_not_found(client):
    login_as(client)
    res = client.get("/get_vehicles")
    assert res.status_code == 404
