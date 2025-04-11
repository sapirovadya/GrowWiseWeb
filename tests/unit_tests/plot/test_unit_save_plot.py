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
import uuid  # חשוב לוודא שזה קיים בראש הקובץ!

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(plot_bp, url_prefix="/Plots")

    test_run_id = str(uuid.uuid4())  # מזהה ריצה ייחודי

    with app.test_client() as client:
        client.test_run_id = test_run_id
        yield client

    # מחיקת כל רשומות החלקות שנוצרו ע"י המנהל
    db.plots.delete_many({"manager_email": "manager@test.com"})
    db.tasks_collection.delete_many({"employee_email": "a@b.com"})  # אם יש משימות שנוצרו


# # ---------------------- save_plot ----------------------
## בדיקת שמירת חלקה בהצלחה
@patch("modules.Plots.routes.db.supply.find_one")
@patch("modules.Plots.routes.db.supply.update_one")
@patch("modules.Plots.routes.db.plots.insert_one")
def test_save_plot_success(mock_insert, mock_update, mock_find, client):
    mock_find.return_value = {"quantity": 20}
    mock_insert.return_value.inserted_id = "new_plot_id"
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"
    res = client.post("/Plots/save_plot", json={
        "crop": "עגבנייה", "plot_category": "ירקות", "plot_name": "חלקה א",
        "plot_type": "חממה", "width": 10, "length": 20,
        "quantity_planted": 10, "sow_date": "2024-01-01"
    })
    assert res.status_code == 201
    assert res.json["message"] == "החלקה נשמרה בהצלחה!"

## מה קורה כשיש שדות חסרים
def test_save_plot_missing_fields(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"
    res = client.post("/Plots/save_plot", json={})
    assert res.status_code == 400
    assert res.json["error"] == "שם החלקה וסוג החלקה הם שדות חובה."

## בדיקת הכנסת תאריך זריעה עתידי
@patch("modules.Plots.routes.db.supply.find_one")
def test_save_plot_future_sow_date(mock_find, client):
    mock_find.return_value = {"quantity": 100}
    future_date = (datetime.today().replace(year=datetime.today().year + 1)).strftime("%Y-%m-%d")
    
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    res = client.post("/Plots/save_plot", json={
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "plot_name": "חלקה ב",
        "plot_type": "חממה",
        "width": 10,
        "length": 20,
        "quantity_planted": 10,
        "sow_date": future_date
    })

    assert res.status_code == 400
    assert "תאריך עתידי" in res.json["error"]

## בדיקה שחסר שדה ״כמות זריעה״
@patch("modules.Plots.routes.db.supply.find_one")
def test_save_plot_missing_quantity(mock_find, client):
    mock_find.return_value = {"quantity": 100}

    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    res = client.post("/Plots/save_plot", json={
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "plot_name": "חלקה ג",
        "plot_type": "חממה",
        "width": 10,
        "length": 20,
        "sow_date": "2024-01-01"
        # כמות זריעה חסרה בכוונה
    })

    assert res.status_code == 400
    assert "כמות זריעה תקינה" in res.json["error"]


## בדיקה של תפקיד לא תקף
def test_save_plot_invalid_role(client):
    with client.session_transaction() as sess:
        sess["role"] = "visitor"
        sess["email"] = "unknown@test.com"
    res = client.post("/Plots/save_plot", json={})
    assert res.status_code == 400
    assert "תפקיד לא מזוהה" in res.json["error"]