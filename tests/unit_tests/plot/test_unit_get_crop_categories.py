import pytest
from flask import Flask, session
from unittest.mock import patch, MagicMock
from bson import ObjectId
import json
import openai
from datetime import datetime
from modules.Plots.routes import plot_bp,db

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

# ---------------------- get_crop_categories ----------------------
@patch("modules.Plots.routes.db", autospec=True)
def test_get_crop_categories(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.distinct.return_value = ["ירקות", "פירות"]
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crop_categories")
    assert res.status_code == 200
    data = res.get_json()
    assert "categories" in data
    assert "ירקות" in data["categories"]
    assert "פירות" in data["categories"]

@patch("modules.Plots.routes.db", autospec=True)
def test_get_crop_categories_exception(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.distinct.side_effect = Exception("Database failure")
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crop_categories")
    assert res.status_code == 500
    assert "Database failure" in res.get_json()["error"]

@patch("modules.Plots.routes.db", autospec=True)
def test_get_crop_categories_empty(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.distinct.return_value = []
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crop_categories")
    assert res.status_code == 200
    assert res.get_json()["categories"] == []

@patch("modules.Plots.routes.db", autospec=True)
def test_get_crop_categories_multiple_items(mock_db, client):
    mock_crops_options = MagicMock()
    mock_crops_options.distinct.return_value = ["תבלינים", "קטניות", "עשבי תיבול"]
    mock_db.crops_options = mock_crops_options

    res = client.get("/Plots/get_crop_categories")
    assert res.status_code == 200
    data = res.get_json()
    assert data["categories"] == ["תבלינים", "קטניות", "עשבי תיבול"]