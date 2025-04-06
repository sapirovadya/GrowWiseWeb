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


def test_create_post_success(test_app):
    with test_app.test_request_context(json={"content": "תוכן לבדיקה"}):
        with patch("modules.posts.routes.posts.create_post") as mock_create, \
             patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}):

            mock_create.return_value = {"id": "123", "content": "תוכן לבדיקה"}
            response = post_routes.create_post()
            assert response[1] == 201
            assert response[0].json["content"] == "תוכן לבדיקה"


def test_create_post_missing_content(test_app):
    with test_app.test_request_context(json={}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}):
            response = post_routes.create_post()
            assert response[1] == 400

def test_create_post_user_not_logged_in(test_app):
    with test_app.test_request_context(json={"content": "בדיקה ללא התחברות"}):
        with patch("modules.posts.routes.session", {}):  # סימולציה של משתמש לא מחובר
            response = post_routes.create_post()
            assert response[1] == 401
            assert "משתמש לא מחובר" in response[0].json["error"]


def test_create_post_only_email_in_session(test_app):
    with test_app.test_request_context(json={"content": "בדיקה חלקית"}):
        with patch("modules.posts.routes.session", {"email": "a@a"}):
            response = post_routes.create_post()
            assert response[1] == 401
            assert "משתמש לא מחובר" in response[0].json["error"]


def test_create_post_content_with_newlines(test_app):
    content = "שורה ראשונה\nשורה שניה"
    expected = "שורה ראשונה<br>שורה שניה"
    with test_app.test_request_context(json={"content": content}):
        with patch("modules.posts.routes.posts.create_post") as mock_create, \
             patch("modules.posts.routes.session", {"email": "a@a", "first_name": "אביגיל", "last_name": "כהן"}):

            mock_create.return_value = {"id": "456", "content": expected}
            response = post_routes.create_post()
            assert response[1] == 201
            assert response[0].json["content"] == expected
