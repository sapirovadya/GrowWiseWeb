import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request, session
from modules.posts import routes as post_routes
import uuid
import datetime

@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    return app

def test_delete_post_authorized(test_app):
    post_id = "abc123"
    post = {"id": post_id, "publisher_email": "a@a"}
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=post), \
             patch("modules.posts.routes.posts_collection.delete_one") as mock_del:

            response = post_routes.delete_post(post_id)
            assert response[1] == 200


def test_delete_post_not_found(test_app):
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=None):

            response = post_routes.delete_post("missing")
            assert response[1] == 404

def test_delete_post_unauthorized_user(test_app):
    post_id = "abc123"
    post = {"id": post_id, "publisher_email": "owner@example.com"}
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "other@example.com"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=post):

            response = post_routes.delete_post(post_id)
            assert response[1] == 403
            assert "אין לך הרשאה" in response[0].json["error"]


def test_delete_post_not_logged_in(test_app):
    post_id = "abc123"
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {}):
            response = post_routes.delete_post(post_id)
            assert response[1] == 401
            assert "משתמש לא מחובר" in response[0].json["error"]


def test_delete_post_db_exception(test_app):
    post_id = "abc123"
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", side_effect=Exception("DB error")):

            response = post_routes.delete_post(post_id)
            assert isinstance(response, Exception) or response[1] in [500, 502, 503]

def test_delete_post_server_error(test_app):
    post_id = "abc123"
    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", side_effect=Exception("DB failure")):

            response = post_routes.delete_post(post_id)
            assert response[1] == 500
            assert "שגיאה בשרת" in response[0].json["error"]
