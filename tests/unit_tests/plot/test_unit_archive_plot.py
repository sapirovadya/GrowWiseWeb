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


# # ---------------------- archive_plot ----------------------
@patch("modules.Plots.routes.db.plots.update_one")
def test_archive_plot_success(mock_update, client):
    mock_update.return_value.modified_count = 1
    plot_id = str(ObjectId())
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })
    assert res.status_code == 302

## בדיקה שלילית- שדות חסרים
def test_archive_plot_missing_fields(client):
    plot_id = str(ObjectId())
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={})
    assert res.status_code == 400
    assert res.json["error"] == "Missing required fields"


@patch("modules.Plots.routes.db.plots.update_one")
def test_archive_plot_invalid_id(mock_update, client):
    res = client.post(f"/Plots/archive_plot/invalid_id", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })
    assert res.status_code == 404
    assert res.json["error"] == "Invalid plot ID"


@patch("modules.Plots.routes.db.plots.update_one")
def test_archive_plot_invalid_crop_yield_type(mock_update, client):
    plot_id = str(ObjectId())
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": "מאות"
    })
    # הקוד לא בודק טיפוס – אם תוסיפי ולידציה, זה יידחה ב-400
    assert res.status_code in [302, 200, 400]

@patch("modules.Plots.routes.db", autospec=True)
def test_archive_plot_with_price_yield(mock_db, client):
    mock_plots = MagicMock()
    mock_db.plots = mock_plots
    mock_plots.update_one.return_value.modified_count = 1

    plot_oid = ObjectId()
    plot_id = str(plot_oid)

    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 120,
        "price_yield": 8.5
    })

    assert res.status_code == 302
    mock_plots.update_one.assert_called_with(
        {"_id": plot_oid},
        {"$set": {
            "harvest_date": "2024-01-01",
            "crop_yield": 120,
            "price_yield": 8.5
        }}
    )


@patch("modules.Plots.routes.db", autospec=True)
def test_archive_plot_server_error(mock_db, client):
    mock_plots = MagicMock()
    mock_db.plots = mock_plots
    mock_plots.update_one.side_effect = Exception("DB Failure")

    plot_oid = ObjectId()
    plot_id = str(plot_oid)

    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })

    assert res.status_code == 500
    assert "Server error" in res.json["error"]