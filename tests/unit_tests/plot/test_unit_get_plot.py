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


# # --- get_plot ---
@patch.object(db, "plots")
@patch.object(db, "supply")  # נדרש כי יש שימוש ב־db.supply בשליחת גידולים זמינים
def test_get_plot_success(mock_supply, mock_plots, client):
    plot_oid = ObjectId()
    mock_plots.find_one.return_value = {
        "_id": plot_oid,
        "plot_name": "חלקה ב",
        "manager_email": "manager@test.com"
    }

    mock_supply.find.return_value = [{"name": "עגבנייה"}]

    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    res = client.get(f"/Plots/get_plot/{str(plot_oid)}")

    assert res.status_code == 200
    assert "plot" in res.json
    assert res.json["plot"]["plot_name"] == "חלקה ב"
    assert res.json["plot"]["_id"] == str(plot_oid)
    assert "available_crops" in res.json
    assert res.json["available_crops"] == ["עגבנייה"]



def test_get_plot_not_found(client):
    plot_id = str(ObjectId())
    with patch("modules.Plots.routes.db.plots.find_one") as mock_find:
        mock_find.return_value = None
        res = client.get(f"/Plots/get_plot/{plot_id}")
        assert res.status_code == 404
        assert "error" in res.json



@patch("modules.Plots.routes.db", autospec=True)
def test_get_plot_internal_server_error(mock_db, client):
    plot_oid = ObjectId()

    mock_plots_collection = MagicMock()
    mock_plots_collection.find_one.side_effect = Exception("DB Failure")
    mock_db.plots = mock_plots_collection

    res = client.get(f"/Plots/get_plot/{str(plot_oid)}")
    assert res.status_code == 500
    assert "Server error" in res.json["error"]

