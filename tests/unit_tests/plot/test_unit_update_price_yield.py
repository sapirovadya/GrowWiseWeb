import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
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


# --- update_price_yield ---

def test_update_price_yield_success(client):
    with patch("modules.Plots.routes.db.plots.update_one") as mock_update:
        res = client.post("/Plots/update_price_yield", json={
            "plot_name": "חלקה א",
            "sow_date": "2024-01-01",
            "price_yield": 12.5
        })
        assert res.status_code == 200
        assert res.json["message"] == "המחיר נשמר בהצלחה"


def test_update_price_yield_string_value(client):
    with patch("modules.Plots.routes.db.plots.update_one") as mock_update:
        res = client.post("/Plots/update_price_yield", json={
            "plot_name": "חלקה ב",
            "sow_date": "2024-02-02",
            "price_yield": "15.75"
        })
        assert res.status_code == 200
        assert res.json["message"] == "המחיר נשמר בהצלחה"


def test_update_price_yield_missing_price(client):
    res = client.post("/Plots/update_price_yield", json={
        "plot_name": "חלקה א",
        "sow_date": "2024-01-01"
        # missing price_yield
    })
    assert res.status_code == 500
    assert "error" in res.get_json()


def test_update_price_yield_missing_plot_name(client):
    res = client.post("/Plots/update_price_yield", json={
        "sow_date": "2024-01-01",
        "price_yield": 12.5
    })
    assert res.status_code == 500
    assert "error" in res.get_json()


def test_update_price_yield_missing_sow_date(client):
    res = client.post("/Plots/update_price_yield", json={
        "plot_name": "חלקה א",
        "price_yield": 12.5
    })
    assert res.status_code == 500
    assert "error" in res.get_json()


def test_update_price_yield_no_json(client):
    res = client.post("/Plots/update_price_yield")
    assert res.status_code == 500
    assert "error" in res.get_json()


def test_update_price_yield_exception(client):
    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.update_one.side_effect = Exception("DB error")

        res = client.post("/Plots/update_price_yield", json={
            "plot_name": "חלקה ג",
            "sow_date": "2024-03-01",
            "price_yield": 18
        })
        assert res.status_code == 500
        assert "DB error" in res.get_json()["error"]

def test_update_price_yield_invalid_price_value(client):
    res = client.post("/Plots/update_price_yield", json={
        "plot_name": "חלקה ד",
        "sow_date": "2024-04-01",
        "price_yield": "abc"
    })
    assert res.status_code == 500
    assert "error" in res.get_json()
    assert "could not convert string to float" in res.get_json()["error"]
