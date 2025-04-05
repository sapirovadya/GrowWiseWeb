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


# # --- get_plots ---
def test_get_plots_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    mock_plots = [
        {"_id": ObjectId(), "plot_name": "חלקה א", "harvest_date": None, "manager_email": "manager@test.com"}
    ]

    with patch("modules.Plots.routes.db.plots.find") as mock_find:
        mock_find.return_value = mock_plots
        res = client.get("/Plots/get_plots")
        assert res.status_code == 200
        assert "plots" in res.json

def test_get_plots_co_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "partner@test.com"
        sess["role"] = "co_manager"
        sess["manager_email"] = "manager@test.com"

    mock_plots = [
        {"_id": ObjectId(), "plot_name": "חלקה ב", "harvest_date": None, "manager_email": "manager@test.com"}
    ]

    with patch("modules.Plots.routes.db.plots.find") as mock_find:
        mock_find.return_value = mock_plots
        res = client.get("/Plots/get_plots")
        assert res.status_code == 200
        assert "plots" in res.json

def test_get_plots_employee_missing_manager_email(client):
    with client.session_transaction() as sess:
        sess["email"] = "employee@test.com"
        sess["role"] = "employee"
        # לא נשלח manager_email

    res = client.get("/Plots/get_plots")
    assert res.status_code == 403
    assert "Manager email not found" in res.json["error"]

def test_get_plots_no_session(client):
    res = client.get("/Plots/get_plots")
    assert res.status_code == 403
    assert "User is not logged in" in res.json["error"]

def test_get_plots_invalid_role(client):
    with client.session_transaction() as sess:
        sess["email"] = "unknown@test.com"
        sess["role"] = "visitor"  # תפקיד לא קיים

    res = client.get("/Plots/get_plots")
    assert res.status_code == 403
    assert "Invalid role" in res.json["error"]

@patch("modules.Plots.routes.db", autospec=True)
def test_get_plots_id_is_string(mock_db, client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    obj_id = ObjectId()

    # יצירת mock לקולקציה db.plots
    mock_plots_collection = MagicMock()
    mock_plots_collection.find.return_value = [
        {"_id": obj_id, "plot_name": "חלקה ג", "harvest_date": None, "manager_email": "manager@test.com"}
    ]
    mock_db.plots = mock_plots_collection

    res = client.get("/Plots/get_plots")
    assert res.status_code == 200
    assert isinstance(res.json["plots"][0]["_id"], str)
    assert res.json["plots"][0]["_id"] == str(obj_id)