from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import pymongo
from dotenv import load_dotenv
import os
from modules.users.co_manager.models import Co_Manager


load_dotenv()

co_manager_bp = Blueprint('co_manager_bp', __name__)

# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")


@co_manager_bp.route("/", methods=['GET'])
def co_manager_home_page():
    return render_template(url_for('manager_bp.manager_home_page'))