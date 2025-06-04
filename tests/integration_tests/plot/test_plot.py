import pytest
from flask import Flask, session, jsonify
from unittest.mock import MagicMock, patch
from bson import ObjectId
from modules.Plots.routes import plot_bp, db
import modules.Plots.routes as plot_routes
import json

@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(plot_bp, url_prefix="/plots")

    with app.test_client() as client:
        yield client

    # ניקוי נתוני בדיקה
    db.plots.delete_many({"manager_email": "manager@test.com"})
    db.plot_tasks.delete_many({"manager_email": "manager@test.com"})

def login_as_manager(client):
    with client.session_transaction() as sess:
        sess["email"] = "manager@test.com"
        sess["role"] = "manager"
        sess["manager_email"] = "manager@test.com"

def test_track_greenhouse_basic(client):
    login_as_manager(client)
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find.return_value = []
        with patch("modules.Plots.routes.render_template", return_value="rendered"):
            res = client.get("/plots/track_greenhouse")
            assert res.status_code == 200
            assert b"rendered" in res.data

def test_save_plot_basic(client):
    login_as_manager(client)
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find_one.return_value = None
        mock_db.supply.find_one.return_value = {"quantity": 100}
        mock_db.supply.update_one.return_value.modified_count = 1
        mock_db.plots.insert_one.return_value.inserted_id = ObjectId()

        res = client.post("/plots/save_plot", data={
            "plot_name": "חלקה א",
            "plot_type": "חממה",
            "square_meters": "200",
            "crop": "עגבנייה",
            "sow_date": "2024-01-01",
            "quantity_planted": "10",
            "kosher_required": "off",  # או "on" אם את רוצה לבדוק גם את זה
            "is_existing": "false"
        }, content_type="multipart/form-data")

        response_data = json.loads(res.get_data(as_text=True))
        assert res.status_code == 201
        assert "החלקה נשמרה בהצלחה!" in response_data.get("message")


def test_get_crop_categories_basic(client):
    res = client.get("/plots/get_crop_categories")
    assert res.status_code == 200
    assert b"categories" in res.data

def test_get_crops_basic(client):
    login_as_manager(client)
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.crops_options.find_one.return_value = {"values": ["עגבנייה"]}
        res = client.get("/plots/get_crops?category=ירקות")
        assert res.status_code == 200
        assert b"crops" in res.data

def test_get_plots_basic(client):
    login_as_manager(client)
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find.return_value = []
        res = client.get("/plots/get_plots")
        assert res.status_code == 200
        assert b"plots" in res.data

def test_update_irrigation_basic(client):
    login_as_manager(client)
    plot_id = ObjectId()
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find_one.return_value = {"_id": plot_id}
        mock_db.plots.update_one.return_value.modified_count = 1
        res = client.post(f"/plots/update_irrigation/{str(plot_id)}", json={"irrigation_amount": 3})
        assert res.status_code == 200
        assert res.get_json()["message"] == "Irrigation updated successfully"

def test_get_sow_dates_basic(client):
    login_as_manager(client)
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find.return_value = [{"sow_date": "2024-01-01"}]
        res = client.get("/plots/get_sow_dates?plot_name=חלקה א")
        assert res.status_code == 200
        json_data = res.get_json()
        assert "dates" in json_data

def test_update_plot_missing_field(client):
    login_as_manager(client)
    plot_id = ObjectId()
    data = {
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "quantity_planted": 10
    }
    res = client.post(f"/plots/update_plot/{str(plot_id)}", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert b"Missing field: sow_date" in res.data

def test_update_plot_quantity_exceeds_stock(client):
    login_as_manager(client)
    plot_id = ObjectId()
    data = {
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "sow_date": "2024-01-01",
        "quantity_planted": 500
    }
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.supply.find_one.return_value = {"quantity": 100}
        res = client.post(f"/plots/update_plot/{str(plot_id)}", data=data, content_type="multipart/form-data")
        assert res.status_code == 400
        response_data = json.loads(res.get_data(as_text=True))
        assert "הזנת כמות גדולה מהמלאי" in response_data.get("error")

def test_update_plot_success(client):
    login_as_manager(client)
    plot_id = ObjectId()
    data = {
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "sow_date": "2024-01-01",
        "quantity_planted": 10
    }
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find_one.return_value = {"_id": plot_id, "manager_email": "manager@test.com"}
        mock_db.supply.find_one.return_value = {"quantity": 100}
        mock_db.supply.update_one.return_value.modified_count = 1
        res = client.post(f"/plots/update_plot/{str(plot_id)}", data=data, content_type="multipart/form-data")

    assert res.status_code == 200
    assert b"Plot updated successfully" in res.data

def test_update_plot_not_found(client):
    login_as_manager(client)
    plot_id = ObjectId()
    data = {
        "crop": "עגבנייה",
        "crop_category": "ירקות",
        "sow_date": "2024-01-01",
        "quantity_planted": 10
    }
    with patch.object(plot_routes, "db") as mock_db:
        mock_db.plots.find_one.return_value = None
        res = client.post(f"/plots/update_plot/{str(plot_id)}", data=data, content_type="multipart/form-data")
    assert res.status_code == 404
    assert b"Plot not found" in res.data