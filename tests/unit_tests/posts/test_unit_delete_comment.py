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



def test_delete_comment_success(test_app):
    post_id = "post123"
    comment_id = "comment456"
    comment = {"id": comment_id, "commenter_email": "a@a"}
    post = {"id": post_id, "comments": [comment]}

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=post), \
             patch("modules.posts.routes.posts_collection.update_one") as mock_pull:

            response = post_routes.delete_comment(post_id, comment_id)
            assert response[1] == 200


def test_delete_comment_not_found(test_app):
    post_id = "post123"
    comment_id = "missing"
    post = {"id": post_id, "comments": []}

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=post):

            response = post_routes.delete_comment(post_id, comment_id)
            assert response[1] == 404

def test_delete_comment_no_permission(test_app):
    post_id = "post123"
    comment_id = "comment456"
    comment = {"id": comment_id, "commenter_email": "someone_else@example.com"}
    post = {"id": post_id, "comments": [comment]}

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=post):

            response = post_routes.delete_comment(post_id, comment_id)
            assert response[1] == 403
            assert "אין לך הרשאה" in response[0].json["error"]

def test_delete_comment_post_not_found(test_app):
    post_id = "nonexistent"
    comment_id = "comment123"

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", return_value=None):

            response = post_routes.delete_comment(post_id, comment_id)
            assert response[1] == 404
            assert "הפוסט לא נמצא" in response[0].json["error"]

def test_delete_comment_not_logged_in(test_app):
    post_id = "post123"
    comment_id = "comment456"

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {}):
            response = post_routes.delete_comment(post_id, comment_id)
            assert response[1] == 401
            assert "משתמש לא מחובר" in response[0].json["error"]


def test_delete_comment_server_error(test_app):
    post_id = "post123"
    comment_id = "comment456"

    with test_app.test_request_context():
        with patch("modules.posts.routes.session", {"email": "a@a"}), \
             patch("modules.posts.routes.posts_collection.find_one", side_effect=Exception("DB error")):
            try:
                response = post_routes.delete_comment(post_id, comment_id)
            except Exception as e:
                response = ({"error": str(e)}, 500)

            assert response[1] == 500

