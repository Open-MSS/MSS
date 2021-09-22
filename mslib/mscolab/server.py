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
import datetime
import secrets
import fs
import socketio
from itsdangerous import URLSafeTimedSerializer
from flask import g, jsonify, request, render_template
from flask import send_from_directory, abort, url_for
from flask_mail import Mail, Message
from flask_cors import CORS
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
mail = Mail(APP)
CORS(APP, origins=mscolab_settings.CORS_ORIGINS if hasattr(mscolab_settings, "CORS_ORIGINS") else ["*"])


# set the operation root directory as the static folder
# ToDo needs refactoring on a route without using of static folder

APP.config['MSCOLAB_DATA_DIR'] = mscolab_settings.MSCOLAB_DATA_DIR
APP.config['SQLALCHEMY_DATABASE_URI'] = mscolab_settings.SQLALCHEMY_DB_URI
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.config['UPLOAD_FOLDER'] = mscolab_settings.UPLOAD_FOLDER
APP.config['MAX_CONTENT_LENGTH'] = mscolab_settings.MAX_UPLOAD_SIZE
APP.config['SECRET_KEY'] = mscolab_settings.SECRET_KEY
APP.config['SECURITY_PASSWORD_SALT'] = mscolab_settings.SECURITY_PASSWORD_SALT
APP.config['MAIL_DEFAULT_SENDER'] = mscolab_settings.MAIL_DEFAULT_SENDER
APP.config['MAIL_SERVER'] = mscolab_settings.MAIL_SERVER
APP.config['MAIL_PORT'] = mscolab_settings.MAIL_PORT
APP.config['MAIL_USERNAME'] = mscolab_settings.MAIL_USERNAME
APP.config['MAIL_PASSWORD'] = mscolab_settings.MAIL_PASSWORD
APP.config['MAIL_USE_TLS'] = mscolab_settings.MAIL_USE_TLS
APP.config['MAIL_USE_SSL'] = mscolab_settings.MAIL_USE_SSL

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


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=APP.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
    except IOError:
        logging.debug("Can't send email to %s", to)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(APP.config['SECRET_KEY'])
    return serializer.dumps(email, salt=APP.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(APP.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=APP.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except IOError:
        return False
    return email


def initialize_managers(app):
    sockio, cm, fm = setup_managers(app)
    # initializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    db.init_app(app)
    return app, sockio, cm, fm


_app, sockio, cm, fm = initialize_managers(APP)


def check_login(emailid, password):
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user is not None:
        if mscolab_settings.USER_VERIFICATION:
            if user.confirmed:
                if user.verify_password(password):
                    return user
        else:
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
            user = User.verify_auth_token(request.args.get('token', request.form.get('token', False)))
        except TypeError:
            logging.debug("no token in request form")
            abort(404)
        if not user:
            return "False"
        else:
            # saving user details in flask.g
            if mscolab_settings.USER_VERIFICATION:
                if user.confirmed:
                    g.user = user
                    return func(*args, **kwargs)
                else:
                    return "False"
            else:
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
        if mscolab_settings.USER_VERIFICATION:
            if user.confirmed:
                token = user.generate_auth_token()
                return json.dumps({
                                  'token': token.decode('ascii'),
                                  'user': {'username': user.username, 'id': user.id}})
            else:
                return "False"
        else:
            token = user.generate_auth_token()
            return json.dumps({
                'token': token.decode('ascii'),
                'user': {'username': user.username, 'id': user.id}})
    else:
        logging.debug("Unauthorized user: %s", emailid)
        return "False"


@APP.route('/test_authorized')
def authorized():
    token = request.args.get('token', request.form.get('token'))
    user = User.verify_auth_token(token)
    if user is not None:
        if mscolab_settings.USER_VERIFICATION:
            if user.confirmed is False:
                return "False"
            else:
                return "True"
        else:
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
            if mscolab_settings.USER_VERIFICATION:
                status_code = 204
            token = generate_confirmation_token(email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('user/activate.html', username=username, confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(email, subject, html)
        return jsonify(result), status_code
    except TypeError:
        return jsonify({"success": False}), 401


@APP.route('/confirm/<token>')
def confirm_email(token):
    if mscolab_settings.USER_VERIFICATION:
        try:
            email = confirm_token(token)
        except TypeError:
            return jsonify({"success": False}), 401
        if email is False:
            return jsonify({"success": False}), 401
        user = User.query.filter_by(emailid=email).first_or_404()
        if user.confirmed:
            return render_template('user/confirmed.html', username=user.username)
        else:
            user.confirmed = True
            user.confirmed_on = datetime.datetime.now()
            db.session.add(user)
            db.session.commit()
            return render_template('user/confirmed.html', username=user.username)


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
    timestamp = request.args.get("timestamp", request.form.get("timestamp", "1970-01-01, 00:00:00"))
    op_id = request.args.get("op_id", request.form.get("op_id", None))
    chat_messages = cm.get_messages(op_id, timestamp)
    return jsonify({"messages": chat_messages})


@APP.route("/message_attachment", methods=["POST"])
@verify_user
def message_attachment():
    file_token = secrets.token_urlsafe(16)
    file = request.files['file']
    op_id = request.form.get("op_id", None)
    message_type = MessageType(int(request.form.get("message_type")))
    user = g.user
    # ToDo review
    users = fm.fetch_users_without_permission(int(op_id), user.id)
    if users is False:
        return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
    if file is not None:
        with fs.open_fs('/') as home_fs:
            file_dir = fs.path.join(APP.config['UPLOAD_FOLDER'], op_id)
            if not home_fs.exists(file_dir):
                home_fs.makedirs(file_dir)
            file_name, file_ext = file.filename.rsplit('.', 1)
            file_name = f'{file_name}-{time.strftime("%Y%m%dT%H%M%S")}-{file_token}.{file_ext}'
            file_name = secure_filename(file_name)
            file_path = fs.path.join(file_dir, file_name)
            file.save(file_path)
            static_dir = fs.path.basename(APP.config['UPLOAD_FOLDER'])
            static_file_path = fs.path.join(static_dir, op_id, file_name)
        new_message = cm.add_message(user, static_file_path, op_id, message_type)
        new_message_dict = get_message_dict(new_message)
        sockio.emit('chat-message-client', json.dumps(new_message_dict))
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
@APP.route('/create_operation', methods=["POST"])
@verify_user
def create_operation():
    path = request.form['path']
    content = request.form.get('content', None)
    description = request.form.get('description', None)
    category = request.form.get('category', "default")
    user = g.user
    r = str(fm.create_operation(path, description, user, content=content, category=category))
    if r == "True":
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return r


@APP.route('/get_operation_by_id', methods=['GET'])
@verify_user
def get_operation_by_id():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    user = g.user
    result = fm.get_file(int(op_id), user)
    if result is False:
        return "False"
    return json.dumps({"content": result})


@APP.route('/get_all_changes', methods=['GET'])
@verify_user
def get_all_changes():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    named_version = request.args.get('named_version')
    user = g.user
    result = fm.get_all_changes(int(op_id), user, named_version)
    if result is False:
        jsonify({"success": False, "message": "Some error occurred!"})
    return jsonify({"success": True, "changes": result})


@APP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    ch_id = int(request.args.get('ch_id', request.form.get('ch_id', 0)))
    result = fm.get_change_content(ch_id)
    if result is False:
        return "False"
    return jsonify({"content": result})


@APP.route('/set_version_name', methods=['POST'])
@verify_user
def set_version_name():
    ch_id = int(request.form.get('ch_id', 0))
    op_id = int(request.form.get('op_id', 0))
    version_name = request.form.get('version_name', None)
    u_id = g.user.id
    success = fm.set_version_name(ch_id, op_id, u_id, version_name)
    if success is False:
        return jsonify({"success": False, "message": "Some error occurred!"})

    return jsonify({"success": True, "message": "Successfully set version name"})


@APP.route('/authorized_users', methods=['GET'])
@verify_user
def authorized_users():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    return json.dumps({"users": fm.get_authorized_users(int(op_id))})


@APP.route('/operations', methods=['GET'])
@verify_user
def get_operations():
    user = g.user
    return json.dumps({"operations": fm.list_operations(user)})


@APP.route('/delete_operation', methods=["POST"])
@verify_user
def delete_operation():
    op_id = int(request.form.get('op_id', 0))
    user = g.user
    success = fm.delete_file(op_id, user)
    if success is False:
        return jsonify({"success": False, "message": "You don't have access for this operation!"})

    sockio.sm.emit_operation_delete(op_id)
    return jsonify({"success": True, "message": "Operation was successfully deleted!"})


@APP.route('/update_operation', methods=['POST'])
@verify_user
def update_operation():
    op_id = request.form.get('op_id', None)
    attribute = request.form['attribute']
    value = request.form['value']
    user = g.user
    return str(fm.update_operation(int(op_id), attribute, value, user))


@APP.route('/operation_details', methods=["GET"])
@verify_user
def get_operation_details():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    user = g.user
    return json.dumps(fm.get_operation_details(int(op_id), user))


@APP.route('/undo', methods=["POST"])
@verify_user
def undo_ftml():
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo(ch_id, user)
    # get op_id from change
    ch = Change.query.filter_by(id=ch_id).first()
    if result is True:
        sockio.sm.emit_file_change(ch.op_id)
    return str(result)


@APP.route("/users_without_permission", methods=["GET"])
@verify_user
def get_users_without_permission():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    users = fm.fetch_users_without_permission(int(op_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@APP.route("/users_with_permission", methods=["GET"])
@verify_user
def get_users_with_permission():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    users = fm.fetch_users_with_permission(int(op_id), u_id)
    if users is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403

    return jsonify({"success": True, "users": users}), 200


@APP.route("/add_bulk_permissions", methods=["POST"])
@verify_user
def add_bulk_permissions():
    op_id = int(request.form.get('op_id'))
    new_u_ids = json.loads(request.form.get('selected_userids', []))
    access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.add_bulk_permission(op_id, user, new_u_ids, access_level)
    if success:
        for u_id in new_u_ids:
            sockio.sm.join_collaborator_to_operation(u_id, op_id)
            sockio.sm.emit_new_permission(u_id, op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "Users successfully added!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route("/modify_bulk_permissions", methods=["POST"])
@verify_user
def modify_bulk_permissions():
    op_id = int(request.form.get('op_id'))
    u_ids = json.loads(request.form.get('selected_userids', []))
    new_access_level = request.form.get('selected_access_level')
    user = g.user
    success = fm.modify_bulk_permission(op_id, user, u_ids, new_access_level)
    if success:
        for u_id in u_ids:
            sockio.sm.emit_update_permission(u_id, op_id, access_level=new_access_level)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "User permissions successfully updated!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route("/delete_bulk_permissions", methods=["POST"])
@verify_user
def delete_bulk_permissions():
    op_id = int(request.form.get('op_id'))
    u_ids = json.loads(request.form.get('selected_userids', []))
    user = g.user
    success = fm.delete_bulk_permission(op_id, user, u_ids)
    if success:
        for u_id in u_ids:
            sockio.sm.emit_revoke_permission(u_id, op_id)
            sockio.sm.remove_collaborator_from_operation(u_id, op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "User permissions successfully deleted!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route('/import_permissions', methods=['POST'])
@verify_user
def import_permissions():
    import_op_id = int(request.form.get('import_op_id'))
    current_op_id = int(request.form.get('current_op_id'))
    user = g.user
    success, users = fm.import_permissions(import_op_id, current_op_id, user.id)
    if success:
        for u_id in users["add_users"]:
            sockio.sm.join_collaborator_to_operation(u_id, current_op_id)
            sockio.sm.emit_new_permission(u_id, current_op_id)
        for u_id in users["modify_users"]:
            sockio.sm.emit_update_permission(u_id, current_op_id)
        for u_id in users["delete_users"]:
            sockio.sm.emit_revoke_permission(u_id, current_op_id)
            sockio.sm.remove_collaborator_from_operation(u_id, current_op_id)
        sockio.sm.emit_operation_permissions_updated(user.id, current_op_id)
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
