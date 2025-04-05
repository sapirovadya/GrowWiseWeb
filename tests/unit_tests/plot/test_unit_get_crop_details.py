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


# # --- get_crop_details ---
def test_get_crop_details_success(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {
            "crop": "עגבנייה",
            "crop_yield": 50
        }

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.json["crop"] == "עגבנייה"
        assert res.json["crop_yield"] == 50



def test_get_crop_details_not_found(client):
    with patch("modules.Plots.routes.db.plots.find_one") as mock_find:
        mock_find.return_value = None
        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 404

def test_get_crop_details_missing_crop_yield(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {
            "crop": "עגבנייה"
        }

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.json["crop"] == "עגבנייה"
        assert res.json["crop_yield"] == 0  # ערך ברירת מחדל


def test_get_crop_details_missing_crop_name(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {
            "crop_yield": 75
        }

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.json["crop"] == ""  # ערך ברירת מחדל
        assert res.json["crop_yield"] == 75


def test_get_crop_details_missing_all_fields(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {"plot_name": "חלקה א", "sow_date": "2024-01-01"}

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.json["crop"] == ""
        assert res.json["crop_yield"] == 0


def test_get_crop_details_missing_query_params(client):
    # בדיקה בלי query params בכלל
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = None  # לא משנה

        res = client.get("/Plots/get_crop_details")
        assert res.status_code == 404
        assert res.get_json()["error"] == "לא נמצאו נתונים"

def test_get_crop_details_only_plot_name(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = None

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א")
        assert res.status_code == 404
        assert res.get_json()["error"] == "לא נמצאו נתונים"

def test_get_crop_details_only_sow_date(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = None

        res = client.get("/Plots/get_crop_details?sow_date=2024-01-01")
        assert res.status_code == 404
        assert res.get_json()["error"] == "לא נמצאו נתונים"

def test_get_crop_details_none_crop(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {"crop": None, "crop_yield": 100}

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.get_json()["crop"] is None
        assert res.get_json()["crop_yield"] == 100

def test_get_crop_details_none_yield(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {"crop": "חסה", "crop_yield": None}

        res = client.get("/Plots/get_crop_details?plot_name=חלקה ב&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.get_json()["crop"] == "חסה"
        assert res.get_json()["crop_yield"] is None

def test_get_crop_details_yield_as_string(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.return_value = {"crop": "גזר", "crop_yield": "מאה"}

        res = client.get("/Plots/get_crop_details?plot_name=חלקה ג&sow_date=2024-01-01")
        assert res.status_code == 200
        assert res.get_json()["crop"] == "גזר"
        assert res.get_json()["crop_yield"] == "מאה"  # הפונקציה לא בודקת טיפוס ערך

def test_get_crop_details_server_error(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find_one.side_effect = Exception("DB failure")

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 500
        assert "error" in res.get_json()
        assert "DB failure" in res.get_json()["error"]


def test_get_crop_details_unexpected_exception(client):
    with patch("modules.Plots.routes.db") as mock_db:
        # גורמים לשגיאה כללית - זו עדיין תיכנס ל־except
        mock_db.plots.find_one.side_effect = Exception("Unexpected failure")

        res = client.get("/Plots/get_crop_details?plot_name=חלקה א&sow_date=2024-01-01")
        assert res.status_code == 500
        assert "error" in res.get_json()
        assert "Unexpected failure" in res.get_json()["error"]