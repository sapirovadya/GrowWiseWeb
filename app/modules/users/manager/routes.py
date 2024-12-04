from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import pymongo
from dotenv import load_dotenv
import os
from modules.users.manager.models import Manager

load_dotenv()

manager_bp = Blueprint('manager_bp', __name__)

# התחברות ל-MongoDB
mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
db = client.get_database("dataGrow")


@manager_bp.route("/managerpage", methods=['GET'])
def manager_home_page():
    return render_template("manager_home_page.html")