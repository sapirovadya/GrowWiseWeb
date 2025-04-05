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

# # --- archive ---
def test_archive_manager(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.db") as mock_db, \
         patch("modules.Plots.routes.render_template") as mock_render:

        mock_db.plots.find.return_value = []
        mock_render.return_value = "OK"

        res = client.get("/Plots/archive")
        assert res.status_code == 200
        assert b"OK" in res.data
        mock_db.plots.find.assert_called_once_with({"manager_email": "manager@test.com", "harvest_date": {"$ne": None}})



def test_archive_unauthorized_role(client):
    with client.session_transaction() as sess:
        sess["role"] = "employee"
        sess["email"] = "worker@test.com"

    res = client.get("/Plots/archive")
    assert res.status_code == 403


def test_archive_co_manager(client):
    with client.session_transaction() as sess:
        sess["role"] = "co_manager"
        sess["email"] = "co@test.com"
        sess["manager_email"] = "manager@test.com"

    with patch("modules.Plots.routes.db") as mock_db, \
         patch("modules.Plots.routes.render_template") as mock_render:

        mock_db.plots.find.return_value = []
        mock_render.return_value = "OK"

        res = client.get("/Plots/archive")
        assert res.status_code == 200
        assert b"OK" in res.data
        mock_db.plots.find.assert_called_once_with({"manager_email": "manager@test.com", "harvest_date": {"$ne": None}})



def test_archive_missing_session_data(client):
    # לא מכניסים role ו־email לסשן
    res = client.get("/Plots/archive")
    assert res.status_code == 403
    assert b"User is not logged in" in res.data


def test_archive_server_error(client):
    with client.session_transaction() as sess:
        sess["role"] = "manager"
        sess["email"] = "manager@test.com"

    with patch("modules.Plots.routes.db") as mock_db:
        mock_db.plots.find.side_effect = Exception("DB crashed")

        res = client.get("/Plots/archive")
        assert res.status_code == 500
        assert b"Server error: DB crashed" in res.data