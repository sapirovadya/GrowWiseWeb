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

# # --- add_plot_task ---
def test_add_plot_task_missing_fields(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"

    res = client.post("/Plots/plot_tasks", json={})
    assert res.status_code == 400
    assert res.json["success"] is False


def test_add_plot_task_missing_some_fields(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
    
    res = client.post("/Plots/plot_tasks", json={
        "plot_id": "abc123", "task_name": "משימה"
    })
    assert res.status_code == 400
    assert res.json["success"] is False
    assert "error" in res.json

