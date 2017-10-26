from flask import Flask, render_template, request, redirect, url_for
from datetime import date, datetime, timedelta
from flask_login import LoginManager

app = Flask(__name__)

login_manager = LoginManager(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')

    result = request.form['username'] + ":" + request.form['password']

    return render_template('index.html', error = result)

@app.route('/motd/list')
def motd():
    return "motd"
