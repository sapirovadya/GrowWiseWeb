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


def test_add_comment_success(test_app):
    post_id = "123"
    with test_app.test_request_context(json={"post_id": post_id, "content": "תגובה"}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}), \
             patch("modules.posts.routes.posts_collection.update_one") as mock_update:

            mock_update.return_value.modified_count = 1
            response = post_routes.add_comment()
            assert response[1] == 201
            assert "commenter_email" in response[0].json


def test_add_comment_not_found(test_app):
    with test_app.test_request_context(json={"post_id": "not_found", "content": "תגובה"}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}), \
             patch("modules.posts.routes.posts_collection.update_one") as mock_update:

            mock_update.return_value.modified_count = 0
            response = post_routes.add_comment()
            assert response[1] == 404

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


def test_add_comment_success(test_app):
    post_id = "123"
    with test_app.test_request_context(json={"post_id": post_id, "content": "תגובה"}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}), \
             patch("modules.posts.routes.posts_collection.update_one") as mock_update:

            mock_update.return_value.modified_count = 1
            response = post_routes.add_comment()
            assert response[1] == 201
            assert "commenter_email" in response[0].json


def test_add_comment_not_found(test_app):
    with test_app.test_request_context(json={"post_id": "not_found", "content": "תגובה"}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}), \
             patch("modules.posts.routes.posts_collection.update_one") as mock_update:

            mock_update.return_value.modified_count = 0
            response = post_routes.add_comment()
            assert response[1] == 404

def test_add_comment_missing_content(test_app):
    with test_app.test_request_context(json={"post_id": "123"}):  # חסר content
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}):
            response = post_routes.add_comment()
            assert response[1] == 400
            assert "יש לספק מזהה פוסט ותוכן תגובה" in response[0].json["error"]

def test_add_comment_missing_post_id(test_app):
    with test_app.test_request_context(json={"content": "תגובה"}):  # חסר post_id
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}):
            response = post_routes.add_comment()
            assert response[1] == 400
            assert "יש לספק מזהה פוסט ותוכן תגובה" in response[0].json["error"]

def test_add_comment_server_error(test_app):
    with test_app.test_request_context(json={"post_id": "123", "content": "תגובה"}):
        with patch("modules.posts.routes.session", {"email": "a@a", "first_name": "Test", "last_name": "User"}), \
             patch("modules.posts.routes.posts_collection.update_one", side_effect=Exception("DB Error")):
            with pytest.raises(Exception) as e_info:
                post_routes.add_comment()
            assert "DB Error" in str(e_info.value)
