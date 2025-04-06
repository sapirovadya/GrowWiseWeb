from flask import request, jsonify, Blueprint, render_template, session
from modules.posts.models import posts, Comment, posts_collection 
import uuid 
from datetime import datetime 


posts_bp = Blueprint('posts_bp', __name__)

@posts_bp.route('/social_feed')
def social_feed():
    return render_template('social_feed.html')  

@posts_bp.route('/', methods=['GET'])
def get_all_posts():
    all_posts = list(posts_collection.find({}, {"_id": 0}).sort("created_at", -1))

    for post in all_posts:
        if "comments" in post:
            post["comments"].sort(key=lambda c: c["created_at"], reverse=True)  
    return jsonify(all_posts), 200



@posts_bp.route('/', methods=['POST'])
def create_post():
    if "email" not in session or "first_name" not in session or "last_name" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 401
    
    data = request.get_json()
    if not data.get("content"):
        return jsonify({"error": "תוכן הפוסט חסר"}), 400

    user_email = session["email"]
    user_name = f"{session['first_name']} {session['last_name']}"  

    data["content"] = data["content"].replace("\n", "<br>")
    data["publisher_email"] = user_email
    data["publisher_name"] = user_name

    new_post = posts.create_post(data)
    return jsonify(new_post), 201

@posts_bp.route('/comments', methods=['POST'])
def add_comment():
    if "email" not in session or "first_name" not in session or "last_name" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 401

    data = request.get_json()
    if not data.get("post_id") or not data.get("content"):
        return jsonify({"error": "יש לספק מזהה פוסט ותוכן תגובה"}), 400

    commenter_name = f"{session['first_name']} {session['last_name']}"
    commenter_email = session["email"] 

    new_comment = {
        "id": str(uuid.uuid4()),
        "commenter_name": commenter_name,
        "commenter_email": commenter_email,  
        "content": data["content"],
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    result = posts_collection.update_one(
        {"id": data["post_id"]},
        {"$push": {"comments": new_comment}}
    )

    if result.modified_count == 0:
        return jsonify({"error": "הפוסט לא נמצא"}), 404

    return jsonify(new_comment), 201


@posts_bp.route('/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 401
    try:
        post = posts_collection.find_one({"id": post_id})
        if not post:
            return jsonify({"error": "הפוסט לא נמצא"}), 404

        if post["publisher_email"] != session["email"]:
            return jsonify({"error": "אין לך הרשאה למחוק פוסט זה"}), 403

        posts_collection.delete_one({"id": post_id})
        return jsonify({"success": "הפוסט נמחק"}), 200
    except Exception as e:
        return jsonify({"error": f"שגיאה בשרת: {str(e)}"}), 500

@posts_bp.route('/<post_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    if "email" not in session:
        return jsonify({"error": "משתמש לא מחובר"}), 401

    post = posts_collection.find_one({"id": post_id})
    if not post:
        return jsonify({"error": "הפוסט לא נמצא"}), 404

    comment_index = next((i for i, c in enumerate(post.get("comments", [])) if c["id"] == comment_id), None)

    if comment_index is None:
        return jsonify({"error": "התגובה לא נמצאה"}), 404

    comment = post["comments"][comment_index]

    # שינוי כאן, המפתח היה comסmenter_email והיה צריך להיות commenter_email
    if comment["commenter_email"] != session["email"]:
        return jsonify({"error": "אין לך הרשאה למחוק תגובה זו"}), 403

    posts_collection.update_one(
        {"id": post_id},
        {"$pull": {"comments": {"id": comment_id}}}
    )

    return jsonify({"success": "התגובה נמחקה"}), 200
