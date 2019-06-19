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

from flask import Flask, request, jsonify
import logging
import json
import datetime

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
    return("Mscolab server")

# ToDo setup codes in return statements

# User related routes


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return(user)
    return(False)


@app.route('/token', methods=["POST"])
def get_auth_token():
    emailid = request.form['emailid']
    password = request.form['password']
    user = check_login(emailid, password)
    if user:
        token = user.generate_auth_token()
        return(jsonify({'token': token.decode('ascii')}))
    else:
        logging.debug("Unauthorized user: %s".format(emailid))
        return("False")


@app.route('/test_authorized')
def authorized():
    token = request.values['token']
    user = User.verify_auth_token(token)
    if user:
        return("True")
    else:
        return("False")


def register_user(email, password, username):
    user = User(email, username, password)
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return('False')
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return('False')
    db.session.add(user)
    db.session.commit()
    return('True')


@app.route("/register", methods=["POST"])
def user_register_handler():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    return(register_user(email, password, username))

# Chat related routes


@app.route("/messages", methods=['POST'])
def messages():
    token = request.form['token']
    timestamp = datetime.datetime.strptime(request.form['timestamp'], '%m %d %Y, %H:%M:%S')
    p_id = request.form['p_id']
    user = User.verify_auth_token(token)
    if user:
        messages = cm.get_messages(p_id, last_timestamp=timestamp)
    else:
        return("False")
    messages = list(map(lambda x:
                    {'user': x.u_id, 'time': x.created_at.strftime("%m %d %Y, %H:%M:%S"), 'text': x.text}, messages))
    return(jsonify({'messages': json.dumps(messages)}))


# File related routes
@app.route('/create_project', methods=["POST"])
def create_project():
    token = request.values['token']
    path = request.values['path']
    description = request.values['description']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.create_project(path, description, user)))


@app.route('/get_project', methods=['GET'])
def get_project():
    token = request.values['token']
    p_id = request.values['p_id']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    result = fm.get_file(int(p_id), user)
    if result is False:
        return("False")
    return(json.dumps({"content": result}))


@app.route('/authorized_users', methods=['GET'])
def authorized_users():
    token = request.values['token']
    p_id = request.values['p_id']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(json.dumps({"users": fm.get_authorized_users(int(p_id))}))


@app.route('/projects', methods=['GET'])
def get_projects():
    token = request.values['token']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(json.dumps({"projects": fm.list_projects(user)}))


@app.route('/delete_project', methods=["POST"])
def delete_project():
    token = request.form['token']
    p_id = request.form['p_id']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.delete_file(int(p_id), user)))


@app.route('/add_permission', methods=['POST'])
def add_permission():
    token = request.form['token']
    p_id = request.form['p_id']
    u_id = request.form['u_id']
    access_level = request.form['access_level']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.add_permission(int(p_id), int(u_id), access_level, user)))


@app.route('/revoke_permission', methods=['POST'])
def revoke_permission():
    token = request.form['token']
    p_id = request.form['p_id']
    u_id = request.form['u_id']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.revoke_permission(int(p_id), int(u_id), user)))


@app.route('/modify_permission', methods=['POST'])
def modify_permission():
    token = request.form['token']
    p_id = request.form['p_id']
    u_id = request.form['u_id']
    access_level = request.form['access_level']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.update_access_level(int(p_id), int(u_id), access_level, user)))


@app.route('/update_project', methods=['POST'])
def update_project():
    token = request.form['token']
    p_id = request.form['p_id']
    attribute = request.form['attribute']
    value = request.form['value']
    user = User.verify_auth_token(token)
    if not user:
        return("False")
    return(str(fm.update_project(int(p_id), attribute, value, user)))


if __name__ == '__main__':
    # to be refactored during deployment
    sockio.run(app, port=8083)
