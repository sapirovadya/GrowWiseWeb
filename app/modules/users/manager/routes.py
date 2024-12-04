from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import pymongo
from modules.users.manager.models import Manager

manager_bp = Blueprint('manager_bp', __name__)

# התחברות ל-MongoDB
client = pymongo.MongoClient("mongodb+srv://111sapir1115:SM123456!@growwise.3xwf5.mongodb.net/?retryWrites=true&w=majority&tls=true")
db = client.get_database("dataGrow")


@manager_bp.route("/managerpage", methods=['GET'])
def manager_home_page():
    return render_template("manager_home_page.html")