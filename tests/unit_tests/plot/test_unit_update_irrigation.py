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

# # ---------------------- update_irrigation ----------------------
@patch("modules.Plots.routes.db", autospec=True)
def test_update_irrigation_success(mock_db, client):
    # הגדרת מזהה חלקה
    real_oid = ObjectId()
    plot_id_str = str(real_oid)

    # הכנת mocks לתוך mock_db
    mock_plots = MagicMock()
    mock_irrigation = MagicMock()

    mock_plots.find_one.return_value = {
        "_id": real_oid,
        "plot_name": "חלקה א",
        "sow_date": "2024-01-01",
        "total_irrigation_amount": 50,
        "manager_email": "manager@test.com"
    }
    mock_plots.update_one.return_value.modified_count = 1
    mock_irrigation.insert_one.return_value = None

    # החדרת mocks לקולקשנים בתוך db
    mock_db.plots = mock_plots
    mock_db.irrigation = mock_irrigation

    # פתיחת session של משתמש
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    # שליחת הבקשה
    res = client.post(f"/Plots/update_irrigation/{plot_id_str}", json={"irrigation_amount": 10})

    # בדיקות
    assert res.status_code == 200
    assert res.json["message"] == "Irrigation updated successfully"
    assert res.json["new_total"] == 60

## בדיקה שלילית- כמות השקייה שלילית/אפס
@patch("modules.Plots.routes.db", autospec=True)
def test_irrigation_invalid_amount(mock_db, client):
    plot_id = str(ObjectId())
    res = client.post(f"/Plots/update_irrigation/{plot_id}", json={"irrigation_amount": 0})
    assert res.status_code == 400
    assert "Invalid irrigation amount" in res.json["error"]

## בדיקה שלילית - חלקה לא תקינה
@patch("modules.Plots.routes.db")
def test_irrigation_nonexistent_plot_id(mock_db, client):
    mock_db.plots.find_one.return_value = None

    with client.session_transaction() as sess:
        sess['role'] = 'manager'
        sess['email'] = 'test@example.com'

    res = client.post("/Plots/update_irrigation/some-nonexistent-id", json={"irrigation_amount": 10})
    assert res.status_code == 404
    assert "Plot not found" in res.get_json()["error"]


## בדיקה שלילית - חלקה לא נמצאת בבסיס הנתונים
@patch("modules.Plots.routes.db", autospec=True)
def test_irrigation_plot_not_found(mock_db, client):
    plot_id = str(ObjectId())
    
    mock_db.plots = MagicMock()  # חשוב!
    mock_db.plots.find_one.return_value = None

    res = client.post(f"/Plots/update_irrigation/{plot_id}", json={"irrigation_amount": 10})
    assert res.status_code == 404
    assert "Plot not found" in res.json["error"]


## שגיאה פנימית
@patch("modules.Plots.routes.db", autospec=True)
def test_irrigation_internal_server_error(mock_db, client):
    plot_id = str(ObjectId())
    
    mock_db.plots = MagicMock()  # חשוב!
    mock_db.plots.find_one.side_effect = Exception("Simulated DB failure")

    res = client.post(f"/Plots/update_irrigation/{plot_id}", json={"irrigation_amount": 10})
    assert res.status_code == 500
    assert "Server error" in res.json["error"]
