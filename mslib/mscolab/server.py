# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from flask import Flask, request, g
import logging
import json
import datetime
import functools

from mslib.mscolab.models import User, db
from mslib.mscolab.conf import SQLALCHEMY_DB_URI, SECRET_KEY
from mslib.mscolab.sockets_manager import socketio as sockio, cm, fm

# set the project root directory as the static folder
app = Flask(__name__, static_url_path='')
sockio.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)


@app.route("/")
def hello():
    return "Mscolab server"

# ToDo setup codes in return statements

# User related routes


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return user
    return False


@app.route('/token', methods=["POST"])
def get_auth_token():
    emailid = request.form['emailid']
    password = request.form['password']
    user = check_login(emailid, password)
    if user:
        token = user.generate_auth_token()
        return json.dumps({'token': token.decode('ascii')})
    else:
        logging.debug("Unauthorized user: %s".format(emailid))
        return "False"


@app.route('/test_authorized')
def authorized():
    token = request.values['token']
    user = User.verify_auth_token(token)
    if user:
        return "True"
    else:
        return "False"


def register_user(email, password, username):
    user = User(email, username, password)
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return 'False'
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return 'False'
    db.session.add(user)
    db.session.commit()
    return 'True'


def verify_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = User.verify_auth_token(request.form.get('token', False))
        if not user:
            return "False"
        else:
            # saving user details in flask.g
            g.user = user
            return func(*args, **kwargs)
    return wrapper


@app.route("/register", methods=["POST"])
def user_register_handler():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    return register_user(email, password, username)


# Chat related routes

@app.route("/messages", methods=['POST'])
@verify_user
def messages():
    timestamp = datetime.datetime.strptime(request.form['timestamp'], '%m %d %Y, %H:%M:%S')
    p_id = request.form.get('p_id', None)
    messages = cm.get_messages(p_id, last_timestamp=timestamp)
    messages = list(map(lambda x:
                    {'user': x.u_id, 'time': x.created_at.strftime("%m %d %Y, %H:%M:%S"), 'text': x.text}, messages))
    return json.dumps({'messages': json.dumps(messages)})


# File related routes
@app.route('/create_project', methods=["POST"])
@verify_user
def create_project():
    path = request.values['path']
    description = request.values['description']
    user = g.user
    return str(fm.create_project(path, description, user))


@app.route('/get_project', methods=['GET'])
@verify_user
def get_project():
    p_id = request.values.get('p_id', None)
    user = g.user
    result = fm.get_file(int(p_id), user)
    if result is False:
        return "False"
    return json.dumps({"content": result})


@app.route('/get_changes', methods=['GET'])
@verify_user
def get_changes():
    p_id = request.values.get('p_id', None)
    user = g.user
    result = fm.get_changes(int(p_id), user)
    if result is False:
        return "False"
    return json.dumps({"changes": result})


@app.route('/get_change_id', methods=['GET'])
@verify_user
def get_change_by_id():
    ch_id = request.values.get('ch_id', None)
    user = g.user
    result = fm.get_change_by_id(int(ch_id), user)
    if result is False:
        return "False"
    return json.dumps({"change": result})


@app.route('/authorized_users', methods=['GET'])
@verify_user
def authorized_users():
    p_id = request.values.get('p_id', None)
    return json.dumps({"users": fm.get_authorized_users(int(p_id))})


@app.route('/projects', methods=['GET'])
@verify_user
def get_projects():
    user = g.user
    return json.dumps({"projects": fm.list_projects(user)})


@app.route('/delete_project', methods=["POST"])
@verify_user
def delete_project():
    p_id = request.form.get('p_id', None)
    user = g.user
    return str(fm.delete_file(int(p_id), user))


@app.route('/add_permission', methods=['POST'])
@verify_user
def add_permission():
    p_id = request.form.get('p_id', None)
    u_id = request.form.get('u_id', None)
    access_level = request.form.get('access_level', None)
    user = g.user
    return str(fm.add_permission(int(p_id), int(u_id), access_level, user))


@app.route('/revoke_permission', methods=['POST'])
def revoke_permission():
    p_id = request.form.get('p_id', None)
    u_id = request.form.get('u_id', None)
    user = g.user
    return str(fm.revoke_permission(int(p_id), int(u_id), user))


@app.route('/modify_permission', methods=['POST'])
def modify_permission():
    p_id = request.form.get('p_id', None)
    u_id = request.form.get('u_id', None)
    access_level = request.form['access_level']
    user = g.user
    return str(fm.update_access_level(int(p_id), int(u_id), access_level, user))


@app.route('/update_project', methods=['POST'])
def update_project():
    p_id = request.form.get('p_id', None)
    attribute = request.form['attribute']
    value = request.form['value']
    user = g.user
    return str(fm.update_project(int(p_id), attribute, value, user))


if __name__ == '__main__':
    # to be refactored during deployment
    sockio.run(app, port=8083)
