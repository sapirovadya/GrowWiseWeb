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


@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_missing_fields(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = {"location": "תל אביב"}

    mock_db.__getitem__.side_effect = lambda name: {"manager": mock_manager_collection}[name]
    mock_db.manager = mock_manager_collection

    mock_openai.return_value = {'choices': [{'message': {'content': '<p>Test</p>'}}]}
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"
    res = client.post("/Plots/growth_forecast", json={})
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 400
    assert res.json['error'] == "Missing required fields in the request."


def test_growth_forecast_invalid_role(client):
    with client.session_transaction() as sess:
        sess["role"] = "employee"
    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 403
    assert res.json['error'] == "Manager email not found for user."

@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_valid(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = {"location": "תל אביב"}

    mock_db.__getitem__.side_effect = lambda name: {"manager": mock_manager_collection}[name]
    mock_db.manager = mock_manager_collection

    mock_openai.return_value = {
        'choices': [{'message': {'content': '<p>Forecast Result</p>'}}]
    }
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"
    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 200

@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_invalid_date_format(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = {"location": "תל אביב"}
    mock_db.manager = mock_manager_collection

    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "01-01-2024"  # פורמט שגוי
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 500
    assert "שגיאה כללית" in res.json["error"]


@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_missing_location(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = {"email": "manager@test.com"}
    mock_db.manager = mock_manager_collection

    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 400
    assert res.json['error'] == "Location not found for the manager."

@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_manager_not_found(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = None  # לא קיים
    mock_db.manager = mock_manager_collection

    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 404
    assert res.json['error'] == "Manager not found in the database."

def test_growth_forecast_illegal_role(client):
    with client.session_transaction() as sess:
        sess["email"] = "user@test.com"
        sess["role"] = "visitor"  # תפקיד לא חוקי

    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 403
    assert res.json['error'] == "Invalid role."

@patch("modules.Plots.routes.db", autospec=True)
@patch("modules.Plots.routes.openai.ChatCompletion.create")
def test_growth_forecast_openai_error(mock_openai, mock_db, client):
    mock_manager_collection = MagicMock()
    mock_manager_collection.find_one.return_value = {"location": "תל אביב"}
    mock_db.manager = mock_manager_collection

    mock_openai.side_effect = openai.error.OpenAIError("שגיאת דמה")

    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"

    res = client.post("/Plots/growth_forecast", json={
        "crop": "עגבנייה", "plot_type": "חממה", "sow_date": "2024-01-01"
    })
    print(res.status_code)
    print(res.get_data(as_text=True))
    assert res.status_code == 500
    assert "שגיאה ב-API של OpenAI" in res.json["error"]