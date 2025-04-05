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

# --- update_task_employees ---
def test_update_task_employees(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "updates": [{"task_id": str(ObjectId()), "employee_email": "a@b.com"}],
            "completed_tasks": [str(ObjectId())]
        })
        assert res.status_code == 200
        assert res.json["success"] is True

def test_update_task_employees_full_update(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "updates": [
                {"task_id": str(ObjectId()), "employee_email": "a@b.com"},
                {"task_id": str(ObjectId()), "employee_email": "b@c.com"}
            ],
            "completed_tasks": [str(ObjectId()), str(ObjectId())]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        # אמורים לקרוא ל־update_one 4 פעמים (2 עובדים + 2 סטטוסים)
        assert mock_update.call_count == 4


def test_update_task_employees_only_updates(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "updates": [
                {"task_id": str(ObjectId()), "employee_email": "a@b.com"}
            ]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        assert mock_update.call_count == 1


def test_update_task_employees_only_completed(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "completed_tasks": [str(ObjectId()), str(ObjectId())]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        assert mock_update.call_count == 2


def test_update_task_employees_missing_task_id(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "updates": [
                {"employee_email": "a@b.com"},  # no task_id
            ]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        # לא אמור לקרוא ל-update_one בכלל
        assert mock_update.call_count == 0


def test_update_task_employees_missing_email(client):
    with patch("modules.Plots.routes.tasks_collection.update_one") as mock_update:
        res = client.post("/Plots/update_task_employees", json={
            "updates": [
                {"task_id": str(ObjectId())}  # no employee_email
            ]
        })
        assert res.status_code == 200
        assert res.json["success"] is True
        assert mock_update.call_count == 0


def test_update_task_employees_no_json(client):
    res = client.post("/Plots/update_task_employees")  # no JSON body
    assert res.status_code == 200
    assert res.json["success"] is False
    assert "error" in res.json

def test_update_task_employees_exception(client):
    with patch("modules.Plots.routes.tasks_collection.update_one", side_effect=Exception("DB error")):
        res = client.post("/Plots/update_task_employees", json={
            "updates": [{"task_id": str(ObjectId()), "employee_email": "a@b.com"}]
        })
        assert res.status_code == 200
        assert res.json["success"] is False
        assert "DB error" in res.json["error"]