import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
import openai
from datetime import datetime
from modules.Plots.routes import plot_bp,db
from unittest.mock import ANY
import re

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.config["TESTING"] = True
    app.register_blueprint(plot_bp, url_prefix="/Plots")
    for rule in app.url_map.iter_rules():
        print(rule)
    with app.test_client() as client:
        yield client

# # --- add_plot_task ---
def test_add_plot_task_missing_fields(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    res = client.post("/Plots/plot_tasks", json={})
    assert res.status_code == 400
    assert res.json["success"] is False

def test_add_plot_task_success(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.tasks_collection.insert_one") as mock_insert,          patch("modules.Plots.routes.task") as mock_task_class:
        mock_task = MagicMock()
        mock_task.new_task.return_value = {"task_name": "משימה", "employee_email": "a@b.com", "_id": ObjectId()}
        mock_task_class.return_value = mock_task
        mock_insert.return_value.inserted_id = ObjectId()
        
        res = client.post("/Plots/plot_tasks", json={
            "plot_id": "abc123", "task_name": "משימה", "employee_email": "a@b.com"
        })
        assert res.status_code == 200
        assert res.json["success"] is True

# בדיקה: שדות חובה חסרים - רק חלק מהשדות קיימים
def test_add_plot_task_missing_some_fields(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
    
    res = client.post("/Plots/plot_tasks", json={
        "plot_id": "abc123", "task_name": "משימה"
        # חסר employee_email
    })
    assert res.status_code == 400
    assert res.json["success"] is False
    assert "error" in res.json

# בדיקה: תאריך לא חוקי
def test_add_plot_task_invalid_due_date(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    res = client.post("/Plots/plot_tasks", json={
        "plot_id": "abc123",
        "task_name": "משימה",
        "employee_email": "a@b.com",
        "due_date": "2024-99-99"  # פורמט לא חוקי
    })
    assert res.status_code == 400
    assert res.json["success"] is False
    assert "פורמט תאריך" in res.json["error"]

# בדיקה: תאריך חוקי - ושהוא מתורגם נכון
def test_add_plot_task_valid_due_date(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.tasks_collection.insert_one") as mock_insert, \
         patch("modules.Plots.routes.task") as mock_task_class:

        mock_task = MagicMock()
        mock_task.new_task.return_value = {
            "task_name": "משימה",
            "employee_email": "a@b.com",
            "due_date": datetime(2024, 4, 1),
            "_id": ObjectId()
        }
        mock_task_class.return_value = mock_task
        mock_insert.return_value.inserted_id = ObjectId()

        res = client.post("/Plots/plot_tasks", json={
            "plot_id": "abc123",
            "task_name": "משימה",
            "employee_email": "a@b.com",
            "due_date": "2024-04-01"
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        assert res.json["task"]["task_name"] == "משימה"

# בדיקה: ללא due_date כלל (תקף)
def test_add_plot_task_no_due_date(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.tasks_collection.insert_one") as mock_insert, \
         patch("modules.Plots.routes.task") as mock_task_class:

        mock_task = MagicMock()
        mock_task.new_task.return_value = {
            "task_name": "משימה",
            "employee_email": "a@b.com",
            "due_date": None,
            "_id": ObjectId()
        }
        mock_task_class.return_value = mock_task
        mock_insert.return_value.inserted_id = ObjectId()

        res = client.post("/Plots/plot_tasks", json={
            "plot_id": "abc123",
            "task_name": "משימה",
            "employee_email": "a@b.com"
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        assert res.json["task"]["due_date"] is None
