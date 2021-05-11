# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2021 by the mss team, see AUTHORS.
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
import functools
import json
import logging
import time
import secrets
import fs
import socketio
from flask import g, jsonify, request, render_template
from flask import send_from_directory, abort
from flask_httpauth import HTTPBasicAuth
from validate_email import validate_email
from werkzeug.utils import secure_filename

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Change, MessageType, User, db
from mslib.mscolab.sockets_manager import setup_managers
from mslib.mscolab.utils import create_files, get_message_dict
from mslib.utils import conditional_decorator
from mslib.index import app_loader

APP = app_loader(__name__)

# set the project root directory as the static folder
# ToDo needs refactoring on a route without using of static folder

APP.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
APP.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
APP.config['MAX_CONTENT_LENGTH'] = mscolab_settings.MAX_UPLOAD_SIZE
APP.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY

auth = HTTPBasicAuth()

try:
    from mss_mscolab_auth import mss_mscolab_auth
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
    return app, sockio, cm, fm


_app, sockio, cm, fm = initialize_managers(APP)


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user:
        if user.verify_password(password):
            return user
    return False


@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
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
        try:
            user = User.verify_auth_token(request.form.get('token', False))
        except TypeError:
            logging.debug("no token in request form")
            abort(404)
        if not user:
            return "False"
        else:
            # saving user details in flask.g
            g.user = user
            return func(*args, **kwargs)
    return wrapper


@APP.route('/')
def home():
    return render_template("/index.html")


# ToDo setup codes in return statements
@APP.route("/status")
def hello():
    return "Mscolab server"


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
    try:
        if result["success"]:
            status_code = 201
        return jsonify(result), status_code
    except TypeError:
        return jsonify({"success": False}), 401


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
@APP.route("/messages", methods=["GET"])
@verify_user
def messages():
    timestamp = request.form.get("timestamp", "1970-01-01, 00:00:00")
    p_id = request.form.get("p_id", None)
    chat_messages = cm.get_messages(p_id, timestamp)
    return jsonify({"messages": chat_messages})


@APP.route("/message_attachment", methods=["POST"])
@verify_user
def message_attachment():
    file_token = secrets.token_urlsafe(16)
    file = request.files['file']
    p_id = request.form.get("p_id", None)
    message_type = MessageType(int(request.form.get("message_type")))
    user = g.user
    users = fm.fetch_users_without_permission(int(p_id), user.id)
    if users is False:
        return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
    if file is not None:
        with fs.open_fs('/') as home_fs:
            file_dir = fs.path.join(APP.config['UPLOAD_FOLDER'], p_id)
            if not home_fs.exists(file_dir):
                home_fs.makedirs(file_dir)
            file_name, file_ext = file.filename.rsplit('.', 1)
            file_name = f'{file_name}-{time.strftime("%Y%m%dT%H%M%S")}-{file_token}.{file_ext}'
            file_name = secure_filename(file_name)
            file_path = fs.path.join(file_dir, file_name)
            file.save(file_path)
            static_dir = fs.path.basename(APP.config['UPLOAD_FOLDER'])
            static_file_path = fs.path.join(static_dir, p_id, file_name)
        new_message = cm.add_message(user, static_file_path, p_id, message_type)
        new_message_dict = get_message_dict(new_message)
        sockio.emit('chat-message-client', json.dumps(new_message_dict), room=str(p_id))
        return jsonify({"success": True, "path": static_file_path})
    return jsonify({"success": False, "message": "Could not send message. No file uploaded."})


@APP.route('/uploads/<name>/<path:filename>', methods=["GET"])
def uploads(name=None, filename=None):
    base_path = mscolab_settings.UPLOAD_FOLDER
    if name is None:
        abort(404)
    if filename is None:
        abort(404)
    return send_from_directory(fs.path.join(base_path, name), filename)


# 413: Payload Too Large
@APP.errorhandler(413)
def error413(error):
    upload_limit = APP.config['MAX_CONTENT_LENGTH'] / 1024 / 1024
    return jsonify({"success": False, "message": f"File size too large. Upload limit is {upload_limit}MB"}), 413


# File related routes
@APP.route('/create_project', methods=["POST"])
@verify_user
def create_project():
    path = request.values['path']
    description = request.values['description']
    content = request.values.get('content', None)
    user = g.user
    return str(fm.create_project(path, description, user, content=content))


@APP.route('/get_project_by_id', methods=['GET'])
@verify_user
def get_project_by_id():
    p_id = request.values.get('p_id', None)
    user = g.user
    result = fm.get_file(int(p_id), user)
    if result is False:
        return "False"
    return json.dumps({"content": result})


@APP.route('/get_all_changes', methods=['GET'])
@verify_user
def get_all_changes():
    p_id = request.values.get('p_id', None)
    named_version = request.args.get('named_version')
    user = g.user
    result = fm.get_all_changes(int(p_id), user, named_version)
    if result is False:
        jsonify({"success": False, "message": "Some error occurred!"})
    return jsonify({"success": True, "changes": result})


@APP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    ch_id = int(request.values.get('ch_id', 0))
    result = fm.get_change_content(ch_id)
    if result is False:
        return "False"
    return jsonify({"content": result})


@APP.route('/set_version_name', methods=['POST'])
@verify_user
def set_version_name():
    ch_id = int(request.form.get('ch_id', 0))
    p_id = int(request.form.get('p_id', 0))
    version_name = request.form.get('version_name', None)
    u_id = g.user.id
    success = fm.set_version_name(ch_id, p_id, u_id, version_name)
    if success is False:
        return jsonify({"success": False, "message": "Some error occurred!"})

    return jsonify({"success": True, "message": "Successfully set version name"})


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
    p_id = int(request.form.get('p_id', 0))
    user = g.user
    success = fm.delete_file(p_id, user)
    if success is False:
        return jsonify({"success": False, "message": "You don't have access for this operation!"})

    sockio.sm.emit_project_delete(p_id)
    return jsonify({"success": True, "message": "Project was successfully deleted!"})


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


@APP.route("/users_without_permission", methods=["GET"])
@verify_user
def get_users_without_permission():
    p_id = request.form.get('p_id', None)
    u_id = g.user.id
    users = fm.fetch_users_without_permission(int(p_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@APP.route("/users_with_permission", methods=["GET"])
@verify_user
def get_users_with_permission():
    p_id = request.form.get('p_id', None)
    u_id = g.user.id
    users = fm.fetch_users_with_permission(int(p_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@APP.route("/add_bulk_permissions", methods=["POST"])
@verify_user
def add_bulk_permissions():
    p_id = int(request.form.get('p_id'))
    new_u_ids = json.loads(request.form.get('selected_userids', []))
    access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.add_bulk_permission(p_id, user, new_u_ids, access_level)
    if success:
        for u_id in new_u_ids:
            sockio.sm.join_collaborator_to_room(u_id, p_id)
            sockio.sm.emit_new_permission(u_id, p_id)
        sockio.sm.emit_project_permissions_updated(user.id, p_id)
        return jsonify({"success": True, "message": "Users successfully added!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route("/modify_bulk_permissions", methods=["POST"])
@verify_user
def modify_bulk_permissions():
    p_id = int(request.form.get('p_id'))
    u_ids = json.loads(request.form.get('selected_userids', []))
    new_access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.modify_bulk_permission(p_id, user, u_ids, new_access_level)
    if success:
        for u_id in u_ids:
            sockio.sm.emit_update_permission(u_id, p_id, access_level=new_access_level)
        sockio.sm.emit_project_permissions_updated(user.id, p_id)
        return jsonify({"success": True, "message": "User permissions successfully updated!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route("/delete_bulk_permissions", methods=["POST"])
@verify_user
def delete_bulk_permissions():
    p_id = int(request.form.get('p_id'))
    u_ids = json.loads(request.form.get('selected_userids', []))
    user = g.user
    success = fm.delete_bulk_permission(p_id, user, u_ids)
    if success:
        for u_id in u_ids:
            sockio.sm.emit_revoke_permission(u_id, p_id)
            sockio.sm.remove_collaborator_from_room(u_id, p_id)
        sockio.sm.emit_project_permissions_updated(user.id, p_id)
        return jsonify({"success": True, "message": "User permissions successfully deleted!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route('/import_permissions', methods=['POST'])
@verify_user
def import_permissions():
    import_p_id = int(request.form.get('import_p_id'))
    current_p_id = int(request.form.get('current_p_id'))
    user = g.user
    success, users = fm.import_permissions(import_p_id, current_p_id, user.id)
    if success:
        for u_id in users["add_users"]:
            sockio.sm.join_collaborator_to_room(u_id, current_p_id)
            sockio.sm.emit_new_permission(u_id, current_p_id)
        for u_id in users["modify_users"]:
            sockio.sm.emit_update_permission(u_id, current_p_id)
        for u_id in users["delete_users"]:
            sockio.sm.emit_revoke_permission(u_id, current_p_id)
            sockio.sm.remove_collaborator_from_room(u_id, current_p_id)
        sockio.sm.emit_project_permissions_updated(user.id, current_p_id)
        return jsonify({"success": True})

    return jsonify({"success": False,
                    "message": "Some error occurred! Could not import permissions. Please try again."})


def start_server(app, sockio, cm, fm, port=8083):
    create_files()
    sockio.run(app, port=port)


def main():
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)

if __name__ == '__main__':
    main()
