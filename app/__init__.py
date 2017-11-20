from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, redirect, url_for, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, UserMixin, logout_user
import psycopg2
import subprocess

app = Flask(__name__)

configName = (os.environ.get("PROD") == None) and "config.DevelopmentConfig" or "config.ProductionConfig"

app.config.from_object(configName)

conn = psycopg2.connect(app.config['DATABASE_URI'])


login_manager = LoginManager(app)
login_manager.login_view = "login"

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

@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/motd')
@login_required
def motd():
    cur = conn.cursor()
    cur.execute("SELECT * FROM notices")
    notices = cur.fetchall()
    cur.close()
    return render_template('motd.html', notices=notices)

restart_command = "pm2 restart jacr-bot"
@app.route("/restart")
@login_required
def bot_restart():
    try:
        process = subprocess.Popen(restart_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
    except KeyboardInterrupt:
        raise
    except:
        return "Tell @qaisjp that something bad happened."
    
    if error == None:
        return "What a success!"

    return "pm2 had an issue. Tell @qaisjp."

class User(UserMixin):
    def get_id(self):
        return app.config['ACCESS_PASSWORD']
