import pytest
from werkzeug.security import generate_password_hash


def test_login_manager_success(client):
    # הוספת מנהל מדומה לבסיס הנתונים
    client.application.db.manager.insert_one({
        "first_name": "John",
        "last_name": "Doe",
        "email": "manager@example.com",
        "password": generate_password_hash("securepassword"),
        "role": "manager"
    })
    
    # ניסיון התחברות עם פרטי המנהל
    response = client.post('/users/login', json={
        "email": "manager@example.com",
        "password": "securepassword"
    })
    
    
    data = response.get_json()
    # בדיקת תגובה
    assert response.status_code == 200
    assert data["message"] == "login successfuly"
    assert data["role"] == "manager"
    assert data["redirect_url"] == "/users/manager/managerpage"

def test_login_employee_success(client):
    # הוספת עובד מדומה לבסיס הנתונים
    client.application.db.employee.insert_one({
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "employee@example.com",
        "password": generate_password_hash("securepassword"),
        "role": "employee",
        "is_approved": 1  # העובד מאושר
    })

    # ניסיון התחברות עם פרטי העובד
    response = client.post('/users/login', json={
        "email": "employee@example.com",
        "password": "securepassword"
    })

    # בדיקת תגובה
    data = response.get_json()
    assert response.status_code == 200
    assert data["message"] == "login successfuly"
    assert data["role"] == "employee"
    assert data["redirect_url"] == "/employee/employeepage"


def test_login_incorrect_password(client):
    # הוספת משתמש מדומה לבסיס הנתונים
    client.application.db.manager.insert_one({
        "email": "manager@example.com",
        "password": generate_password_hash("securepassword"),
        "role": "manager"
    })

    # ניסיון התחברות עם סיסמה שגויה
    response = client.post('/users/login', json={
        "email": "manager@example.com",
        "password": "wrongpassword"
    })

    # בדיקת תגובה
    data = response.get_json()
    assert response.status_code == 400
    assert data["message"] == "one of the detail is incorrect"


def test_login_user_not_found(client):
    # ניסיון התחברות עם אימייל שלא קיים בבסיס הנתונים
    response = client.post('/users/login', json={
        "email": "nonexistent@example.com",
        "password": "somepassword"
    })

    # בדיקת תגובה
    data = response.get_json()
    assert response.status_code == 400
    assert data["message"] == "user not found"


def test_login_employee_not_approved(client):
    # הוספת עובד מדומה שאינו מאושר
    client.application.db.employee.insert_one({
        "email": "employee@example.com",
        "password": generate_password_hash("securepassword"),
        "role": "employee",
        "is_approved": 0  # העובד לא מאושר
    })

    # ניסיון התחברות
    response = client.post('/users/login', json={
        "email": "employee@example.com",
        "password": "securepassword"
    })

    # בדיקת תגובה
    data = response.get_json()
    assert response.status_code == 400
    assert data["message"] == "user is not approved"
