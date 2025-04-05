import pytest
from flask import json

def test_manager_signup_success(client):
    response = client.post('/users/signup', json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "securepassword",
        "role": "manager"
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "תהליך רישום המנהל עבר בהצלחה"

    manager = client.application.db.manager.find_one({"email": "john.doe@example.com"})
    assert manager is not None
    assert manager["first_name"] == "John"


def test_employee_signup_success(client):
    client.application.db.manager.insert_one({
        "first_name": "Manager",
        "last_name": "Doe",
        "email": "manager@example.com",
        "password": "securepassword",
        "role": "manager"
    })

    response = client.post('/users/signup', json={
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "password": "securepassword",
        "role": "employee",
        "manager_email": "manager@example.com"
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "תהליך רישום העובד עבר בהצלחה"

    employee = client.application.db.employee.find_one({"email": "jane.doe@example.com"})
    assert employee is not None
    assert employee["first_name"] == "Jane"


# בדיקות שליליות
def test_signup_missing_fields(client):
    response = client.post('/users/signup', json={
        "first_name": "John",
        # "last_name" is missing
        "email": "john.doe@example.com",
        "password": "securepassword",
        "role": "manager"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "All fields are required"


def test_signup_email_already_exists(client):
    # הוספת משתמש עם אותו אימייל
    client.application.db.manager.insert_one({
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "securepassword",
        "role": "manager"
    })

    response = client.post('/users/signup', json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "securepassword",
        "role": "manager"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Email already exists. Please use a different email"


def test_signup_invalid_role(client):
    response = client.post('/users/signup', json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "securepassword",
        "role": "invalid_role"  # תפקיד לא חוקי
    })

    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Invalid role provided"


def test_signup_employee_missing_manager_email(client):
    response = client.post('/users/signup', json={
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "password": "securepassword",
        "role": "employee"
        # חסר manager_email
    })

    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Manager email is required for workers"


def test_signup_employee_invalid_manager_email(client):
    response = client.post('/users/signup', json={
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "password": "securepassword",
        "role": "employee",
        "manager_email": "nonexistent.manager@example.com"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert data["message"] == "Manager email not found. Please provide a valid manager email"
