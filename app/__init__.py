from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, redirect, url_for, jsonify, abort, flash, g
from flask_login import LoginManager, login_required, current_user, login_user, UserMixin, logout_user
from flask_wtf.csrf import CSRFProtect
import psycopg2
import subprocess
import os

app = Flask(__name__)

configName = (os.environ.get("PROD") == None) and "config.DevelopmentConfig" or "config.ProductionConfig"

app.config.from_object(configName)

def get_db():
    if not hasattr(g, 'db'):
        g.db = psycopg2.connect(app.config['DATABASE_URI'])
    return g.db

login_manager = LoginManager(app)
login_manager.login_view = "login"

csrf = CSRFProtect(app)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

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
    cur = get_db().cursor()
    cur.execute("SELECT * FROM notices ORDER BY title ASC")
    rows = cur.fetchall()
    cur.close()
    return render_template('notices.html', notices=rows)

@app.route('/notices', methods=['PUT'])
@app.route('/notices/<int:id>', methods=['DELETE', 'PUT'])
@login_required
def notices_update(id=None):
    cur = get_db().cursor()
    status = "success"
    code = 200
    message = ""
    data = None

    try:
        if request.method == "PUT" and id is None:
            # Insert a row
            cur.execute(
                """INSERT INTO notices(title, message) VALUES (%s, %s) RETURNING id""",
                (request.form["title"], request.form["body"])
            )
            rows = cur.fetchall()
            data = {'id': rows[0][0]}
        elif request.method == "PUT":
            cur.execute(
                """update notices set (title, message) = (%s, %s) where id=%s""",
                (request.form['title'], request.form['body'], id)
            )

            if cur.rowcount < 1:
                status = "error"
                message = "Notice does not exist. Try creating a new one."
                code = 400
        elif request.method == "DELETE":
            cur.execute(
                """delete from notices where id = %s""",
                (id,)
            )

            if cur.rowcount < 1:
                status = "error"
                message = "Notice does not exist or already deleted."
                code = 400
    except psycopg2.IntegrityError:
        status = "error"
        message = "A notice with that title already exists."
        code = 400

    get_db().commit()
    cur.close()
    return jsonify({
        "data": data,
        "message": message,
        "status": status
    }), code

@app.route('/responses')
@login_required
def responses():
    cur = get_db().cursor()
    cur.execute("""SELECT groups.id as group_id, array_to_json(array_agg(cmds.name)) as cmds, array_to_json(groups.messages) as messages FROM
			response_commands as cmds,
			response_groups as groups
		WHERE
			cmds.group = groups.id
		GROUP BY groups.messages, groups.id""")

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
        if error is None:
            flash("A bot restart has been requested.", "info")
        else:
            flash("pm2 had an issue. Tell @qaisjp.", "error")

    except KeyboardInterrupt:
        raise
    except:
        flash("Tell @qaisjp that something bad happened.", "error")

    return redirect(url_for('overview'))

class User(UserMixin):
    def get_id(self):
        return app.config['ACCESS_PASSWORD']
