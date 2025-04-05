import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
import openai
from datetime import datetime
from modules.Plots.routes import plot_bp,db
from modules.Plots import routes as plot_routes
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


# # --- get_plot_tasks ---
def test_get_plot_tasks_as_employee(client):
    with client.session_transaction() as sess:
        sess["role"] = "employee"
        sess["email"] = "employee@test.com"

    with patch("modules.Plots.routes.tasks_collection.find") as mock_find:
        mock_find.return_value = [{"_id": ObjectId(), "plot_id": "abc", "employee_email": "employee@test.com"}]
        res = client.get("/Plots/plot_tasks/abc")
        assert res.status_code == 200
        assert "tasks" in res.json

def test_get_plot_tasks_as_manager(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.tasks_collection.find") as mock_tasks_find:
        mock_tasks_find.return_value = [
            {"_id": ObjectId(), "plot_id": "abc", "employee_email": "worker@test.com"}
        ]

        # משתמשים ב־patch.dict כדי לשנות את db.employee
        fake_employees = [
            {"email": "worker@test.com", "first_name": "Worker", "last_name": "One"}
        ]

        # פאטצ' לדאטאבייס עצמו ולא רק לפונקציה
        with patch.object(plot_routes.db, "employee") as mock_employee_collection:
            mock_employee_collection.find.return_value = fake_employees

            res = client.get("/Plots/plot_tasks/abc")
            assert res.status_code == 200
            assert res.json["is_manager"] is True
            assert len(res.json["employees"]) == 1
            assert res.json["employees"][0]["name"] == "Worker One"



def test_get_plot_tasks_as_co_manager(client):
    from modules.Plots import routes as plot_routes

    with client.session_transaction() as sess:
        sess["role"] = "co_manager"
        sess["email"] = "co@test.com"
        sess["manager_email"] = "manager@test.com"

    with patch("modules.Plots.routes.tasks_collection.find") as mock_tasks_find:
        mock_tasks_find.return_value = [
            {"_id": ObjectId(), "plot_id": "abc", "employee_email": "worker@test.com"}
        ]

        fake_employees = [
            {"email": "worker@test.com", "first_name": "Worker", "last_name": "Two"}
        ]

        with patch.object(plot_routes.db, "employee") as mock_employee_collection:
            mock_employee_collection.find.return_value = fake_employees

            res = client.get("/Plots/plot_tasks/abc")
            assert res.status_code == 200
            assert res.json["is_manager"] is True
            assert len(res.json["employees"]) == 1
            assert res.json["employees"][0]["name"] == "Worker Two"


def test_get_plot_tasks_employee_sees_own_only(client):
    with client.session_transaction() as sess:
        sess["role"] = "employee"
        sess["email"] = "employee@test.com"

    with patch("modules.Plots.routes.tasks_collection.find") as mock_find:
        mock_find.return_value = [
            {"_id": ObjectId(), "plot_id": "abc", "employee_email": "employee@test.com"},
            {"_id": ObjectId(), "plot_id": "abc", "employee_email": "other@test.com"}  # לא אמור להחזיר
        ]
        res = client.get("/Plots/plot_tasks/abc")
        assert res.status_code == 200
        assert res.json["is_manager"] is False
        assert isinstance(res.json["tasks"], list)
        assert "employees" in res.json
        assert res.json["employees"] == []  # עובד לא רואה רשימת עובדים


def test_get_plot_tasks_no_session(client):
    with patch("modules.Plots.routes.tasks_collection.find") as mock_find:
        mock_find.return_value = []
        res = client.get("/Plots/plot_tasks/abc")
        assert res.status_code == 200
        assert res.json["is_manager"] is False
        assert res.json["employees"] == []

def test_get_plot_tasks_no_tasks_found(client):
    with client.session_transaction() as sess:
        sess["role"] = "employee"
        sess["email"] = "employee@test.com"

    with patch("modules.Plots.routes.tasks_collection.find") as mock_find:
        mock_find.return_value = []
        res = client.get("/Plots/plot_tasks/abc")
        assert res.status_code == 200
        assert res.json["tasks"] == []