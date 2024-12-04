from flask import Flask,render_template, request, url_for, redirect,session
import pymongo
from modules.users.routes import users_bp_main
from modules.users.employee.routes import employee_bp
from modules.users.manager.routes import manager_bp



app = Flask(__name__)
client = pymongo.MongoClient("mongodb+srv://111sapir1115:SM123456!@growwise.3xwf5.mongodb.net/?retryWrites=true&w=majority&appName=growwise")
db = client.get_database("dataGrow")

app.secret_key = "GrowWise_by_Sapir_And_May_the_best_website!"

app.register_blueprint(users_bp_main, url_prefix='/users')
app.register_blueprint(employee_bp, url_prefix='/employee')
app.register_blueprint(manager_bp, url_prefix='/manager')



@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)