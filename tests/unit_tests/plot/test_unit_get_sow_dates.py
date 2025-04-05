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

# # --- get_sow_dates ---
def test_get_sow_dates_success(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.return_value = [{"sow_date": "2024-01-01"}, {"sow_date": "2024-02-01"}]
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה א")
        assert res.status_code == 200
        assert "2024-01-01" in res.json["dates"]
        assert "2024-02-01" in res.json["dates"]


def test_get_sow_dates_missing_param(client):
    res = client.get("/Plots/get_sow_dates")
    assert res.status_code == 400

def test_get_sow_dates_no_results(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.return_value = []
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה ב")
        assert res.status_code == 200
        assert res.json["dates"] == []

def test_get_sow_dates_missing_sow_field(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.return_value = [{"not_sow": "value"}]
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה ג")
        assert res.status_code == 200
        assert res.json["dates"] == []

def test_get_sow_dates_server_error(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.side_effect = Exception("DB error")
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה ד")
        assert res.status_code == 500
        assert "שגיאה בשליפת תאריכי זריעה" in res.get_json()["error"]


def test_get_sow_dates_with_none_sow_date(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.return_value = [{"sow_date": None}, {"sow_date": "2024-06-01"}]
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה ה")
        assert res.status_code == 200
        assert "2024-06-01" in res.json["dates"]
        assert None not in res.json["dates"]

def test_get_sow_dates_invalid_date_format(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.return_value = [{"sow_date": "invalid-date"}, {"sow_date": "2024-04-01"}]
        res = client.get("/Plots/get_sow_dates?plot_name=חלקה ו")
        assert res.status_code == 200
        assert "invalid-date" in res.json["dates"]  # הפונקציה לא מסננת פורמט, רק נוכחות
