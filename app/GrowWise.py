from flask import Flask,render_template, request, url_for, redirect,session
import pymongo
from modules.users.routes import users_bp_main


app = Flask(__name__)
client = pymongo.MongoClient("mongodb+srv://111sapir1115:SM123456!@growwise.3xwf5.mongodb.net/?retryWrites=true&w=majority&appName=growwise")
db = client.get_database("dataGrow")


app.register_blueprint(users_bp_main, url_prefix='/users')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)