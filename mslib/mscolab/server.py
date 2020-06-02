# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2020 by the mss team, see AUTHORS.
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

from flask import Flask, request, g, jsonify
from flask_httpauth import HTTPBasicAuth
import datetime
import functools
import json
import logging
from validate_email import validate_email
import socketio

from mslib.mscolab.models import User, db, Change
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.sockets_manager import setup_managers
from mslib.utils import conditional_decorator

# set the project root directory as the static folder

APP = Flask(__name__, static_url_path='')
APP.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
APP.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
APP.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY

auth = HTTPBasicAuth()

try:
    import mss_mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mss_mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mss_mscolab_auth(object):
        allowed_users = [("mscolab", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None

# setup http auth
if mscolab_settings.__dict__.get('enable_basic_http_authentication', False):
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    import hashlib

    def authfunc(username, password):
        for u, p in mss_mscolab_auth.allowed_users:
            if (u == username) and (p == hashlib.md5(password.encode('utf-8')).hexdigest()):
                return True
        return False

    @auth.verify_password
    def verify_pw(username, password):
        if request.authorization:
            auth = request.authorization
            username = auth.username
            password = auth.password
        return authfunc(username, password)


def initialize_managers(app):
    sockio, cm, fm = setup_managers(app)
    # initiatializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    db.init_app(app)
    return (app, sockio, cm, fm)


_app, sockio, cm, fm = initialize_managers(APP)


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return user
    return False


def register_user(email, password, username):
    user = User(email, username, password)
    is_valid_username = True if username.find("@") == -1 else False
    is_valid_email = validate_email(email)
    if not is_valid_email:
        return {"success": False, "message": "Oh no, your email ID is not valid!"}
    if not is_valid_username:
        return {"success": False, "message": "Oh no, your username cannot contain @ symbol!"}
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return {"success": False, "message": "Oh no, this email ID is already taken!"}
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return {"success": False, "message": "Oh no, this username is already registered"}
    db.session.add(user)
    db.session.commit()
    return {"success": True}


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


# ToDo setup codes in return statements
@APP.route("/")
def hello():
    return "Mscolab server"


# User related routes


@APP.route('/token', methods=["POST"])
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
def get_auth_token():
    emailid = request.form['email']
    password = request.form['password']
    user = check_login(emailid, password)
    if user:
        token = user.generate_auth_token()
        return json.dumps({
                          'token': token.decode('ascii'),
                          'user': {'username': user.username, 'id': user.id}})
    else:
        logging.debug("Unauthorized user: %s", emailid)
        return "False"


@APP.route('/test_authorized')
def authorized():
    token = request.values['token']
    user = User.verify_auth_token(token)
    if user:
        return "True"
    else:
        return "False"


@APP.route("/register", methods=["POST"])
def user_register_handler():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    result = register_user(email, password, username)
    status_code = 200
    if result["success"]:
        status_code = 201
    return jsonify(result), status_code


@APP.route('/user', methods=["GET"])
@verify_user
def get_user():
    return json.dumps({'user': {'id': g.user.id, 'username': g.user.username}})


@APP.route("/delete_user", methods=["POST"])
@verify_user
def delete_user():
    user = g.user
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True}), 200


# Chat related routes
@APP.route("/messages", methods=['POST'])
@verify_user
def messages():
    timestamp = datetime.datetime.strptime(request.form['timestamp'], '%m %d %Y, %H:%M:%S')
    p_id = request.form.get('p_id', None)
    messages = cm.get_messages(p_id, last_timestamp=timestamp)
    return json.dumps({'messages': messages})


# File related routes
@APP.route('/create_project', methods=["POST"])
@verify_user
def create_project():
    path = request.values['path']
    description = request.values['description']
    content = request.values.get('content', None)
    user = g.user
    return str(fm.create_project(path, description, user, content=content))


@APP.route('/get_project', methods=['GET'])
@verify_user
def get_project():
    p_id = request.values.get('p_id', None)
    user = g.user
    result = fm.get_file(int(p_id), user)
    if result is False:
        return "False"
    return json.dumps({"content": result})


@APP.route('/get_changes', methods=['GET'])
@verify_user
def get_changes():
    p_id = request.values.get('p_id', None)
    user = g.user
    result = fm.get_changes(int(p_id), user)
    if result is False:
        return "False"
    return json.dumps({"changes": result})


@APP.route('/get_change_id', methods=['GET'])
@verify_user
def get_change_by_id():
    ch_id = request.values.get('ch_id', None)
    user = g.user
    result = fm.get_change_by_id(int(ch_id), user)
    if result is False:
        return "False"
    return json.dumps({"change": result})


@APP.route('/authorized_users', methods=['GET'])
@verify_user
def authorized_users():
    p_id = request.values.get('p_id', None)
    return json.dumps({"users": fm.get_authorized_users(int(p_id))})


@APP.route('/projects', methods=['GET'])
@verify_user
def get_projects():
    user = g.user
    return json.dumps({"projects": fm.list_projects(user)})


@APP.route('/delete_project', methods=["POST"])
@verify_user
def delete_project():
    p_id = request.form.get('p_id', None)
    user = g.user
    return str(fm.delete_file(int(p_id), user))


@APP.route('/add_permission', methods=['POST'])
@verify_user
def add_permission():
    p_id = request.form.get('p_id', 0)
    u_id = request.form.get('u_id', 0)
    username = request.form.get('username', None)
    access_level = request.form.get('access_level', None)
    user = g.user
    if u_id == 0:
        user_v = User.query.filter((User.username == username) | (User.emailid == username)).first()
        if user_v is None:
            return "False"
        u_id = user_v.id
    success = str(fm.add_permission(int(p_id), int(u_id), username, access_level, user))
    if success == "True":
        sockio.sm.join_collaborator_to_room(int(u_id), int(p_id))
        sockio.sm.emit_new_permission(int(u_id), int(p_id))
    return success


@APP.route('/revoke_permission', methods=['POST'])
@verify_user
def revoke_permission():
    p_id = request.form.get('p_id', 0)
    u_id = request.form.get('u_id', 0)
    username = request.form.get('username', None)
    user = g.user
    if u_id == 0:
        user_v = User.query.filter_by(username=username).first()
        if user_v is None:
            return "False"
        u_id = user_v.id
    success = str(fm.revoke_permission(int(p_id), int(u_id), username, user))
    if success:
        sockio.sm.emit_revoke_permission(int(u_id), int(p_id))
        sockio.sm.remove_collaborator_from_room(int(u_id), int(p_id))
    return success


@APP.route('/modify_permission', methods=['POST'])
@verify_user
def modify_permission():
    p_id = request.form.get('p_id', 0)
    u_id = request.form.get('u_id', 0)
    username = request.form.get('username', None)
    access_level = request.form.get('access_level', None)
    user = g.user
    if u_id == 0:
        user_v = User.query.filter((User.username == username) | (User.emailid == username)).first()
        if user_v is None:
            return "False"
        u_id = user_v.id
    success = str(fm.update_access_level(int(p_id), int(u_id), username, access_level, user))
    if success == "True":
        sockio.sm.emit_update_permission(u_id, p_id)
    return success


@APP.route('/update_project', methods=['POST'])
@verify_user
def update_project():
    p_id = request.form.get('p_id', None)
    attribute = request.form['attribute']
    value = request.form['value']
    user = g.user
    return str(fm.update_project(int(p_id), attribute, value, user))


@APP.route('/project_details', methods=["GET"])
@verify_user
def get_project_details():
    p_id = request.form.get('p_id', None)
    user = g.user
    return json.dumps(fm.get_project_details(int(p_id), user))


@APP.route('/undo', methods=["POST"])
@verify_user
def undo_ftml():
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo(ch_id, user)
    # get p_id from change
    ch = Change.query.filter_by(id=ch_id).first()
    if result is True:
        sockio.sm.emit_file_change(ch.p_id)
    return str(result)


def start_server(app, sockio, cm, fm, port=8083):
    sockio.run(app, port=port)


def main():
    from mslib.mscolab.demodata import create_data
    # create data if not created
    create_data()
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)

if __name__ == '__main__':
    main()
