import uuid
from datetime import datetime
import pymongo
import os
from dotenv import load_dotenv

# טוען משתני סביבה
load_dotenv()
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")
posts_collection = db["posts"]

class posts:
    @staticmethod
    def create_post(data):
        # יצירת מסמך פוסט חדש
        post = {
            "id": str(uuid.uuid4()),
            "publisher_email": data.get("publisher_email"),
            "publisher_name": data.get("publisher_name"),
            "content": data.get("content"),
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "comments": []
        }
        # הכנסת הפוסט למסד הנתונים
        result = posts_collection.insert_one(post)
        post["_id"] = str(result.inserted_id)  # המרת ObjectId למחרוזת
        return post

    @staticmethod
    def get_all_posts():
        posts_list = list(posts_collection.find().sort("created_at", -1))
        for post in posts_list:
            post["_id"] = str(post["_id"])  
        return posts_list

class Comment:
    @staticmethod
    def add_comment(data):
        post_id = data.get("post_id")
        comment = {
            "id": str(uuid.uuid4()),
            "commenter_name": data.get("commenter_name"),
            "content": data.get("content"),
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
        # הוספת התגובה לפוסט המתאים
        posts_collection.update_one({"id": post_id}, {"$push": {"comments": comment}})
        return comment
