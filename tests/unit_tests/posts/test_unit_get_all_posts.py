import pytest
from flask import Flask, jsonify
from unittest.mock import patch
from modules.posts import routes as post_routes


@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    return app


def test_get_all_posts_success(test_app):
    mock_posts = [
        {
            "id": "1",
            "content": "פוסט ראשון",
            "created_at": "2024-01-01 10:00:00",
            "comments": [
                {"id": "c1", "content": "תגובה א", "created_at": "2024-01-02 10:00:00"},
                {"id": "c2", "content": "תגובה ב", "created_at": "2024-01-01 09:00:00"}
            ]
        },
        {
            "id": "2",
            "content": "פוסט שני",
            "created_at": "2024-01-02 10:00:00"
        }
    ]

    with test_app.test_request_context():
        with patch("modules.posts.routes.posts_collection.find") as mock_find:
            mock_find.return_value.sort.return_value = mock_posts

            res, code = post_routes.get_all_posts()
            assert code == 200
            assert isinstance(res.json, list)
            assert res.json[0]["id"] == "1"
            assert res.json[0]["comments"][0]["id"] == "c1"  # בדיקת מיון תגובות


def test_get_all_posts_no_comments(test_app):
    mock_posts = [
        {"id": "1", "content": "פוסט בלי תגובות", "created_at": "2024-01-01 10:00:00"}
    ]

    with test_app.test_request_context():
        with patch("modules.posts.routes.posts_collection.find") as mock_find:
            mock_find.return_value.sort.return_value = mock_posts

            res, code = post_routes.get_all_posts()
            assert code == 200
            assert res.json[0]["id"] == "1"
            assert "comments" not in res.json[0]


def test_get_all_posts_empty(test_app):
    with test_app.test_request_context():
        with patch("modules.posts.routes.posts_collection.find") as mock_find:
            mock_find.return_value.sort.return_value = []

            res, code = post_routes.get_all_posts()
            assert code == 200
            assert res.json == []


def test_get_all_posts_comments_unsorted(test_app):
    mock_posts = [
        {
            "id": "1",
            "content": "עם תגובות",
            "created_at": "2024-01-01 10:00:00",
            "comments": [
                {"id": "c1", "created_at": "2024-01-03 08:00:00"},
                {"id": "c2", "created_at": "2024-01-04 12:00:00"},
                {"id": "c3", "created_at": "2024-01-02 06:00:00"}
            ]
        }
    ]

    with test_app.test_request_context():
        with patch("modules.posts.routes.posts_collection.find") as mock_find:
            mock_find.return_value.sort.return_value = mock_posts

            res, code = post_routes.get_all_posts()
            assert code == 200
            sorted_ids = [c["id"] for c in res.json[0]["comments"]]
            assert sorted_ids == ["c2", "c1", "c3"]  # לפי created_at בירידה


def test_get_all_posts_exception(test_app):
    with test_app.test_request_context():
        with patch("modules.posts.routes.posts_collection.find", side_effect=Exception("DB error")):
            try:
                post_routes.get_all_posts()
            except Exception as e:
                assert str(e) == "DB error"
