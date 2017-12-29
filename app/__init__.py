from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, redirect, url_for, jsonify, abort, flash
from flask_login import LoginManager, login_required, current_user, login_user, UserMixin, logout_user
from flask_wtf.csrf import CSRFProtect
import psycopg2
import subprocess
import os

app = Flask(__name__)

configName = (os.environ.get("PROD") == None) and "config.DevelopmentConfig" or "config.ProductionConfig"

app.config.from_object(configName)

conn = psycopg2.connect(app.config['DATABASE_URI'])


login_manager = LoginManager(app)
login_manager.login_view = "login"

csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    return User()

@app.route('/')
@login_required
def overview(page="overview"):
    return render_template('overview.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    result = "Unrecognised IP address and password."
    if app.config['ACCESS_PASSWORD'] == request.form['password']:
        login_user(User())
        return redirect(url_for('overview'))

    return render_template('login.html', error = result)

@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('overview'))

@app.route('/notices')
@login_required
def notices():
    cur = conn.cursor()
    cur.execute("SELECT * FROM notices")
    rows = cur.fetchall()
    cur.close()
    return render_template('notices.html', notices=rows)

@app.route('/responses')
@login_required
def responses():
    cur = conn.cursor()
    cur.execute("""SELECT array_to_json(array_agg(cmds.name)) as cmds, array_to_json(groups.messages) as messages FROM
			response_commands as cmds,
			response_groups as groups
		WHERE
			cmds.group = groups.id
		GROUP BY groups.messages""")

    rows = cur.fetchall()
    cur.close()
    return render_template(
        'responses.html',
        responses=rows
    )


restart_command = "pm2 restart jacr-bot"
@app.route("/restart", methods=["POST"])
@login_required
def bot_restart():
    try:
        process = subprocess.Popen(restart_command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        if error is not None:
            flash("pm2 had an issue. Tell @qaisjp.", "error")

    except KeyboardInterrupt:
        raise
    except:
        flash("Tell @qaisjp that something bad happened.", "error")

    return redirect(url_for('overview'))

class User(UserMixin):
    def get_id(self):
        return app.config['ACCESS_PASSWORD']
