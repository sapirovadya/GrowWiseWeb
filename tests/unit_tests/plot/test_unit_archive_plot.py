import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
import json
from modules.Plots.routes import plot_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.config["TESTING"] = True
    app.register_blueprint(plot_bp, url_prefix="/Plots")
    with app.test_client() as client:
        yield client

# ---------------------- archive_plot ----------------------

@patch("modules.Plots.routes.db.plots.update_one")
@patch("modules.Plots.routes.db.plots.find_one")
def test_archive_plot_success(mock_find, mock_update, client):
    mock_update.return_value.modified_count = 1
    mock_find.return_value = {"_id": "06806ef3-3789-4247-b3be-ca036f58fd4b"}

    plot_id = "06806ef3-3789-4247-b3be-ca036f58fd4b"
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })

    assert res.status_code == 200
    assert res.json["message"] == "החלקה הועברה לארכיון"


def test_archive_plot_missing_fields(client):
    plot_id = "06806ef3-3789-4247-b3be-ca036f58fd4b"
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={})
    assert res.status_code == 400
    assert res.json["error"] == "Missing required fields"


@patch("modules.Plots.routes.db.plots.find_one")
def test_archive_plot_invalid_id(mock_find, client):
    mock_find.return_value = None
    plot_id = "invalid-id"
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })
    assert res.status_code == 404
    assert res.json["error"] == "Plot not found"


@patch("modules.Plots.routes.db.plots.find_one")
def test_archive_plot_invalid_crop_yield_type(mock_find, client):
    mock_find.return_value = {"_id": "06806ef3-3789-4247-b3be-ca036f58fd4b"}

    plot_id = "06806ef3-3789-4247-b3be-ca036f58fd4b"
    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": "מאות"
    })
    assert res.status_code == 400
    assert "Crop yield must be a number" in res.json["error"]


@patch("modules.Plots.routes.db", autospec=True)
def test_archive_plot_with_price_yield(mock_db, client):
    plot_id = "06806ef3-3789-4247-b3be-ca036f58fd4b"

    mock_plots = MagicMock()
    mock_db.plots = mock_plots
    mock_plots.find_one.return_value = {"_id": plot_id}
    mock_plots.update_one.return_value.modified_count = 1

    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 120,
        "price_yield": 8.5
    })

    assert res.status_code == 200
    assert res.json["message"] == "החלקה הועברה לארכיון"
    mock_plots.update_one.assert_called_with(
        {"_id": plot_id},
        {"$set": {
            "harvest_date": "2024-01-01",
            "crop_yield": 120,
            "price_yield": 8.5
        }}
    )


@patch("modules.Plots.routes.db", autospec=True)
def test_archive_plot_server_error(mock_db, client):
    plot_id = "06806ef3-3789-4247-b3be-ca036f58fd4b"

    mock_plots = MagicMock()
    mock_db.plots = mock_plots
    mock_plots.find_one.return_value = {"_id": plot_id}
    mock_plots.update_one.side_effect = Exception("DB Failure")

    res = client.post(f"/Plots/archive_plot/{plot_id}", json={
        "harvest_date": "2024-01-01",
        "crop_yield": 100
    })

    assert res.status_code == 500
    assert "Server error" in res.json["error"]
