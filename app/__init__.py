from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, redirect, url_for
from flask_login import LoginManager, login_required, current_user, login_user, UserMixin

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")

login_manager = LoginManager(app)
# login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User()

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    result = "Unrecognised IP address and password."
    if app.config['ACCESS_PASSWORD'] == request.form['password']:
        login_user(User())
        return redirect(url_for('index'))

    return render_template('login.html', error = result)

@app.route('/motd/list')
@login_required
def motd():
    return "motd"

class User(UserMixin):
    def get_id(self):
        return app.config['ACCESS_PASSWORD']