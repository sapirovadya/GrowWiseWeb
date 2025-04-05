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

@patch("modules.Plots.routes.db", autospec=True)
def test_update_plot_future_sow_date(mock_db, client):
    plot_id = str(ObjectId())

    mock_plots = MagicMock()
    mock_plots.find_one.return_value = {
        "_id": ObjectId(), "manager_email": "manager@test.com"
    }
    mock_db.plots = mock_plots

    mock_supply = MagicMock()
    mock_supply.find_one.return_value = {"quantity": 100}
    mock_db.supply = mock_supply

    future_date = (datetime.today().replace(year=datetime.today().year + 1)).strftime("%Y-%m-%d")

    res = client.post(f"/Plots/update_plot/{plot_id}", json={
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "sow_date": future_date,
        "quantity_planted": 10
    })

    assert res.status_code == 400
    assert "תאריך עתידי" in res.json["error"]
