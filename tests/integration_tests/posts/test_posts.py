import pytest
from flask import Flask, session
from modules.posts.routes import posts_bp
from modules.posts import routes as post_routes
from pymongo import MongoClient
import uuid
import datetime

# יצירת לקוח לפלאסק
@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(posts_bp, url_prefix="/posts")

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["email"] = "test@example.com"
            sess["first_name"] = "Test"
            sess["last_name"] = "User"
        yield client

    # לאחר כל בדיקה, נמחק את כל הפוסטים שהוזנו במהלך הבדיקה
    post_routes.posts_collection.delete_many({"publisher_email": "test@example.com"})


# בדיקת יצירת פוסט וקריאה לכל הפוסטים
def test_create_post_and_get_all(client):
    # יצירת פוסט חדש
    content = f"פוסט בדיקה {uuid.uuid4()}"
    res = client.post("/posts/", json={"content": content})
    assert res.status_code == 201
    post_data = res.get_json()
    assert post_data["content"] == content.replace("\n", "<br>")

    # שמירת ה-ID של הפוסט שנוצר
    post_id = post_data["id"]

    # בדיקת קבלת כל הפוסטים
    res = client.get("/posts/")
    assert res.status_code == 200
    posts = res.get_json()
    assert any(post["id"] == post_id for post in posts)

    # מחיקת הפוסט שנוצר בסיום הבדיקה
    client.delete(f"/posts/{post_id}")


# בדיקת הוספת תגובה ומחיקת תגובה
def test_add_comment_and_delete(client):
    # יצירת פוסט
    res = client.post("/posts/", json={"content": "פוסט לבדיקה עם תגובה"})
    post_id = res.get_json()["id"]

    # הוספת תגובה
    comment_content = "בדיקת תגובה"
    res = client.post("/posts/comments", json={"post_id": post_id, "content": comment_content})
    assert res.status_code == 201
    comment_id = res.get_json()["id"]

    # מחיקת תגובה
    res = client.delete(f"/posts/{post_id}/comments/{comment_id}")
    assert res.status_code == 200
    assert "success" in res.get_json()


# בדיקת מחיקת פוסט על ידי המפרסם בלבד
def test_delete_post_by_owner(client):
    res = client.post("/posts/", json={"content": "פוסט למחיקה"})
    post_id = res.get_json()["id"]

    res = client.delete(f"/posts/{post_id}")
    assert res.status_code == 200
    assert res.get_json()["success"] == "הפוסט נמחק"


# בדיקת נסיון למחוק פוסט של מישהו אחר
def test_fail_to_delete_others_post(client):
    # צור פוסט עם משתמש אחר (ללא session זהה)
    other_post = {
        "id": str(uuid.uuid4()),
        "content": "פוסט של מישהו אחר",
        "publisher_email": "other@example.com",
        "publisher_name": "מישהו אחר",
        "created_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    post_routes.posts_collection.insert_one(other_post)

    res = client.delete(f"/posts/{other_post['id']}")
    assert res.status_code == 403
    assert "אין לך הרשאה" in res.get_json()["error"]

    # ניקוי
    post_routes.posts_collection.delete_one({"id": other_post["id"]})


# בדיקת הוספת תגובה לפוסט שלא קיים
def test_add_comment_to_nonexistent_post(client):
    res = client.post("/posts/comments", json={"post_id": "not_real_id", "content": "משהו"})
    assert res.status_code == 404
    assert "הפוסט לא נמצא" in res.get_json()["error"]
import pytest
from flask import Flask, session
from modules.posts.routes import posts_bp
from modules.posts import routes as post_routes
from pymongo import MongoClient
import uuid
import datetime

# יצירת לקוח לפלאסק
@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    app.config["TESTING"] = True
    app.register_blueprint(posts_bp, url_prefix="/posts")

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["email"] = "test@example.com"
            sess["first_name"] = "Test"
            sess["last_name"] = "User"
        yield client

    # לאחר כל בדיקה, נמחק את כל הפוסטים שהוזנו במהלך הבדיקה
    post_routes.posts_collection.delete_many({"publisher_email": "test@example.com"})


# בדיקת יצירת פוסט וקריאה לכל הפוסטים
def test_create_post_and_get_all(client):
    # יצירת פוסט חדש
    content = f"פוסט בדיקה {uuid.uuid4()}"
    res = client.post("/posts/", json={"content": content})
    assert res.status_code == 201
    post_data = res.get_json()
    assert post_data["content"] == content.replace("\n", "<br>")

    # שמירת ה-ID של הפוסט שנוצר
    post_id = post_data["id"]

    # בדיקת קבלת כל הפוסטים
    res = client.get("/posts/")
    assert res.status_code == 200
    posts = res.get_json()
    assert any(post["id"] == post_id for post in posts)

    # מחיקת הפוסט שנוצר בסיום הבדיקה
    client.delete(f"/posts/{post_id}")


# בדיקת הוספת תגובה ומחיקת תגובה
def test_add_comment_and_delete(client):
    # יצירת פוסט
    res = client.post("/posts/", json={"content": "פוסט לבדיקה עם תגובה"})
    post_id = res.get_json()["id"]

    # הוספת תגובה
    comment_content = "בדיקת תגובה"
    res = client.post("/posts/comments", json={"post_id": post_id, "content": comment_content})
    assert res.status_code == 201
    comment_id = res.get_json()["id"]

    # מחיקת תגובה
    res = client.delete(f"/posts/{post_id}/comments/{comment_id}")
    assert res.status_code == 200
    assert "success" in res.get_json()


# בדיקת מחיקת פוסט על ידי המפרסם בלבד
def test_delete_post_by_owner(client):
    res = client.post("/posts/", json={"content": "פוסט למחיקה"})
    post_id = res.get_json()["id"]

    res = client.delete(f"/posts/{post_id}")
    assert res.status_code == 200
    assert res.get_json()["success"] == "הפוסט נמחק"


# בדיקת נסיון למחוק פוסט של מישהו אחר
def test_fail_to_delete_others_post(client):
    # צור פוסט עם משתמש אחר (ללא session זהה)
    other_post = {
        "id": str(uuid.uuid4()),
        "content": "פוסט של מישהו אחר",
        "publisher_email": "other@example.com",
        "publisher_name": "מישהו אחר",
        "created_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    post_routes.posts_collection.insert_one(other_post)

    res = client.delete(f"/posts/{other_post['id']}")
    assert res.status_code == 403
    assert "אין לך הרשאה" in res.get_json()["error"]

    # ניקוי
    post_routes.posts_collection.delete_one({"id": other_post["id"]})


# בדיקת הוספת תגובה לפוסט שלא קיים
def test_add_comment_to_nonexistent_post(client):
    res = client.post("/posts/comments", json={"post_id": "not_real_id", "content": "משהו"})
    assert res.status_code == 404
    assert "הפוסט לא נמצא" in res.get_json()["error"]
