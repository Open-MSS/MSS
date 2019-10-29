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
from validate_email import validate_email

from mslib.mscolab.models import User, db, Change
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.sockets_manager import setup_managers
# set the project root directory as the static folder
app = Flask(__name__, static_url_path='')
app.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
app.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


def initialize_managers(app):
    sockio, cm, fm = setup_managers(app)
    # initiatializing socketio and db
    sockio.init_app(app)
    db.init_app(app)
    return (app, sockio, cm, fm)


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return user
    return False


def register_user(email, password, username):
    user = User(email, username, password)
    user_exists = User.query.filter_by(emailid=str(email)).first()
    is_valid = validate_email(email)
    if not is_valid:
        return 'False'
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


def start_server(app, sockio, cm, fm, port=8083):

    @app.route("/")
    def hello():
        return "Mscolab server"

    # ToDo setup codes in return statements

    # User related routes

    @app.route('/token', methods=["POST"])
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

    @app.route('/test_authorized')
    def authorized():
        token = request.values['token']
        user = User.verify_auth_token(token)
        if user:
            return "True"
        else:
            return "False"

    @app.route("/register", methods=["POST"])
    def user_register_handler():
        email = request.form['email']
        password = request.form['password']
        username = request.form['username']
        return register_user(email, password, username)

    @app.route('/user', methods=["GET"])
    @verify_user
    def get_user():
        return json.dumps({'user': {'id': g.user.id, 'username': g.user.username}})

    # Chat related routes
    @app.route("/messages", methods=['POST'])
    @verify_user
    def messages():
        timestamp = datetime.datetime.strptime(request.form['timestamp'], '%m %d %Y, %H:%M:%S')
        p_id = request.form.get('p_id', None)
        messages = cm.get_messages(p_id, last_timestamp=timestamp)
        return json.dumps({'messages': messages})

    # File related routes
    @app.route('/create_project', methods=["POST"])
    @verify_user
    def create_project():
        path = request.values['path']
        description = request.values['description']
        content = request.values.get('content', None)
        user = g.user
        return str(fm.create_project(path, description, user, content=content))

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
        p_id = request.form.get('p_id', 0)
        u_id = request.form.get('u_id', 0)
        username = request.form.get('username', None)
        access_level = request.form.get('access_level', None)
        user = g.user
        if u_id == 0:
            u_id = User.query.filter_by(username=username).first().id
        success = str(fm.add_permission(int(p_id), int(u_id), username, access_level, user))
        if success == "True":
            sockio.sm.join_collaborator_to_room(int(u_id), int(p_id))
            sockio.sm.emit_new_permission(int(u_id), int(p_id))
        return success

    @app.route('/revoke_permission', methods=['POST'])
    @verify_user
    def revoke_permission():
        p_id = request.form.get('p_id', 0)
        u_id = request.form.get('u_id', 0)
        username = request.form.get('username', None)
        user = g.user
        return str(fm.revoke_permission(int(p_id), int(u_id), username, user))

    @app.route('/modify_permission', methods=['POST'])
    @verify_user
    def modify_permission():
        p_id = request.form.get('p_id', 0)
        u_id = request.form.get('u_id', 0)
        username = request.form.get('username', None)
        access_level = request.form.get('access_level', None)
        user = g.user
        if username is not None:
            u_id = User.query.filter_by(username=username).first().id
        success = str(fm.update_access_level(int(p_id), int(u_id), username, access_level, user))
        if success == "True":
            sockio.sm.emit_update_permission(u_id, p_id)
        return success

    @app.route('/update_project', methods=['POST'])
    @verify_user
    def update_project():
        p_id = request.form.get('p_id', None)
        attribute = request.form['attribute']
        value = request.form['value']
        user = g.user
        return str(fm.update_project(int(p_id), attribute, value, user))

    @app.route('/project_details', methods=["GET"])
    @verify_user
    def get_project_details():
        p_id = request.form.get('p_id', None)
        user = g.user
        return json.dumps(fm.get_project_details(int(p_id), user))

    @app.route('/undo', methods=["POST"])
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

    sockio.run(app, port=port)


def main():
    from mslib.mscolab.demodata import create_data
    # create data if not created
    create_data()
    _app, sockio, cm, fm = initialize_managers(app)
    start_server(_app, sockio, cm, fm)


if __name__ == '__main__':
    main()
