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

@patch("modules.Plots.routes.render_template", return_value="Rendered")
def test_track_greenhouse(mock_render, client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"
        sess["name"] = "Test Manager"
        sess["manager_email"] = "manager@test.com"
    res = client.get("/Plots/track_greenhouse")
    assert res.status_code == 200
    assert res.get_data(as_text=True) == "Rendered"