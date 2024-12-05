# import os
# import sys
# import pytest
# import mongomock


# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

# from app.GrowWise import app

# @pytest.fixture
# def client():
#     app.config["TESTING"] = True  # אפליקציה במצב בדיקות
#     app.config["SECRET_KEY"] = "test_key"

#     # שימוש בבסיס נתונים מדומה
#     app.db = mongomock.MongoClient().db

#     # יצירת Test Client
#     client = app.test_client()
#     yield client

import os
import sys
import pytest
import mongomock
from flask import Flask

# הוספת הנתיב של האפליקציה
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app.GrowWise import app as flask_app

@pytest.fixture
def app():
    # הגדרת קונפיגורציה לאפליקציה
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test_key"

    # שימוש בבסיס נתונים מדומה
    flask_app.db = mongomock.MongoClient().db

    # יצירת context של האפליקציה
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    # שימוש ב-Client עם context האפליקציה
    return app.test_client()
