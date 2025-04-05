import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
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

# # ---------------------- get_crops ----------------------
## בודק מה קורה כשמבקשים קטגוריה שלא קיימת
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_not_found(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.find_one.return_value = None  # סימולציה שאין קטגוריה
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=ירקות")
    assert res.status_code == 200
    assert res.json["crops"] == []


## לבדוק תוצאה תקינה, כשהקטגוריה קיימת ויש לה ערכים
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_success(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.find_one.return_value = {"values": ["עגבנייה", "חסה"]}
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=ירקות")
    assert res.status_code == 200
    assert "עגבנייה" in res.json["crops"]
    assert "חסה" in res.json["crops"]

## לבדוק מה קורה כששולחים בקשה בלי קטגוריה
def test_get_crops_missing_category(client):
    res = client.get("/Plots/get_crops")
    assert res.status_code == 400
    assert res.json["error"] == "Category is missing"

##  לבדוק מה קורה במצב בט נמצא קטגוריה אבל אין לה ערכים
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_no_values_field(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.find_one.return_value = {"category": "ירקות"}
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=ירקות")
    assert res.status_code == 200
    assert res.json["crops"] == []  

## לבדוק מה קורה אם יש ערך שהוא לא שייך לאף קטגוריה
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_values_not_list(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.find_one.return_value = {"values": "עגבנייה"}  # מחרוזת במקום רשימה
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=ירקות")
    assert res.status_code == 500  

##  לבדוק שהמערכת לא קורסת כשהקטגוריה כוללת תווים חריגים
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_invalid_characters_in_category(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.find_one.return_value = None
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=<script>")
    assert res.status_code == 200
    assert res.json["crops"] == []


## לבדוק שחיפוש הקטגוריה מתבצע בצורה בלתי תלויה באותיות קטנות/גדולות
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crops_case_insensitive(mock_db, client):
    mock_crops_options = MagicMock()

    def mock_find_one(query):
        category_query = query.get("category")
        if isinstance(category_query, dict):
            pattern = category_query.get("$regex")
            options = category_query.get("$options", "")
            flags = re.IGNORECASE if "i" in options else 0
            if re.match(pattern, "ירקות", flags):
                return {"values": ["עגבנייה", "חסה"]}
        return None

    mock_crops_options.find_one.side_effect = mock_find_one
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crops?category=ירקות")
    assert res.status_code == 200
    assert "עגבנייה" in res.json["crops"]