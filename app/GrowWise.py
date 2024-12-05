from flask import Flask,render_template, request, url_for, redirect,session
import pymongo
from dotenv import load_dotenv
import os
from modules.users.routes import users_bp_main
from modules.users.employee.routes import employee_bp
from modules.users.manager.routes import manager_bp
from modules.users.co_manager.routes import co_manager_bp


load_dotenv()
app = Flask(__name__)

mongo_key = os.getenv("MONGO_KEY")
client = pymongo.MongoClient(mongo_key)
app.db = client.get_database("dataGrow")

app.secret_key = os.getenv("APP_SECRET")

app.register_blueprint(users_bp_main, url_prefix='/users')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(manager_bp, url_prefix='/manager')
app.register_blueprint(co_manager_bp, url_prefix='/co_manager')





















@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    
    app.run(debug=True)