# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2023 by the MSS team, see AUTHORS.
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
import os
import socketio
import sqlalchemy.exc
import werkzeug

from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import g, jsonify, request, render_template, flash
from flask import send_from_directory, abort, url_for
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth
from validate_email import validate_email
from werkzeug.utils import secure_filename

from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.models import Change, MessageType, User, Operation, db
from mslib.mscolab.sockets_manager import setup_managers
from mslib.mscolab.utils import create_files, get_message_dict
from mslib.utils import conditional_decorator
from mslib.index import create_app
from mslib.mscolab.forms import ResetRequestForm, ResetPasswordForm


APP = create_app(__name__)
mail = Mail(APP)
CORS(APP, origins=mscolab_settings.CORS_ORIGINS if hasattr(mscolab_settings, "CORS_ORIGINS") else ["*"])
migrate = Migrate(APP, db, render_as_batch=True)
auth = HTTPBasicAuth()

try:
    from mscolab_auth import mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mscolab_auth(object):
        allowed_users = [("mscolab", "add_md5_digest_of_PASSWORD_here"),
                         ("add_new_user_here", "add_md5_digest_of_PASSWORD_here")]
        __file__ = None

# setup http auth
if mscolab_settings.__dict__.get('enable_basic_http_authentication', False):
    logging.debug("Enabling basic HTTP authentication. Username and "
                  "password required to access the service.")
    import hashlib

    def authfunc(username, password):
        for u, p in mscolab_auth.allowed_users:
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
    if APP.config['MAIL_DEFAULT_SENDER'] is not None:
        msg = Message(
            subject,
            recipients=[to],
            html=template,
            sender=APP.config['MAIL_DEFAULT_SENDER']
        )
        try:
            mail.send(msg)
        except IOError:
            logging.error("Can't send email to %s", to)
    else:
        logging.debug("setup user verification by email")


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
    except (IOError, BadSignature):
        return False
    return email


def initialize_managers(app):
    sockio, cm, fm = setup_managers(app)
    # initializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    # db.init_app(app)
    return app, sockio, cm, fm


_app, sockio, cm, fm = initialize_managers(APP)


def check_login(emailid, password):
    try:
        user = User.query.filter_by(emailid=str(emailid)).first()
    except sqlalchemy.exc.OperationalError as ex:
        logging.debug("Problem in the database (%ex), likly version client different", ex)
        return False
    if user is not None:
        if mscolab_settings.MAIL_ENABLED:
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
            if mscolab_settings.MAIL_ENABLED:
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
    if request.authorization is not None:
        if mscolab_settings.__dict__.get('enable_basic_http_authentication', False):
            auth.login_required()
            return "Mscolab server"
        return "Mscolab server"
    else:
        return "Mscolab server"


@APP.route('/token', methods=["POST"])
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
def get_auth_token():
    emailid = request.form['email']
    password = request.form['password']
    user = check_login(emailid, password)
    if user:
        if mscolab_settings.MAIL_ENABLED:
            if user.confirmed:
                token = user.generate_auth_token()
                return json.dumps({
                    'token': token,
                    'user': {'username': user.username, 'id': user.id}})
            else:
                return "False"
        else:
            token = user.generate_auth_token()
            return json.dumps({
                'token': token,
                'user': {'username': user.username, 'id': user.id}})
    else:
        logging.debug("Unauthorized user: %s", emailid)
        return "False"


@APP.route('/test_authorized')
def authorized():
    token = request.args.get('token', request.form.get('token'))
    user = User.verify_auth_token(token)
    if user is not None:
        if mscolab_settings.MAIL_ENABLED:
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
            if mscolab_settings.MAIL_ENABLED:
                status_code = 204
                token = generate_confirmation_token(email)
                confirm_url = url_for('confirm_email', token=token, _external=True)
                html = render_template('user/activate.html', username=username, confirm_url=confirm_url)
                subject = "MSColab Please confirm your email"
                send_email(email, subject, html)
    except TypeError:
        result, status_code = {"success": False}, 401
    return jsonify(result), status_code


@APP.route('/confirm/<token>')
def confirm_email(token):
    if mscolab_settings.MAIL_ENABLED:
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
    """
    delete own account
    """
    # ToDo rename to delete_own_account
    user = g.user
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True}), 200


# Chat related routes
@APP.route("/messages", methods=["GET"])
@verify_user
def messages():
    # ToDo maybe move is_member part to file_manager
    user = g.user
    op_id = request.args.get("op_id", request.form.get("op_id", None))
    if fm.is_member(user.id, op_id):
        timestamp = request.args.get("timestamp", request.form.get("timestamp", "1970-01-01, 00:00:00"))
        chat_messages = cm.get_messages(op_id, timestamp)
        return jsonify({"messages": chat_messages})
    return "False"


@APP.route("/message_attachment", methods=["POST"])
@verify_user
def message_attachment():
    user = g.user
    op_id = request.form.get("op_id", None)
    if fm.is_member(user.id, op_id):
        file_token = secrets.token_urlsafe(16)
        file = request.files['file']
        message_type = MessageType(int(request.form.get("message_type")))
        user = g.user
        # ToDo review
        users = fm.fetch_users_without_permission(int(op_id), user.id)
        if users is False:
            return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
        if file is not None:
            with fs.open_fs('/') as home_fs:
                file_dir = fs.path.join(APP.config['UPLOAD_FOLDER'], op_id)
                if '\\' not in file_dir:
                    if not home_fs.exists(file_dir):
                        home_fs.makedirs(file_dir)
                else:
                    file_dir = file_dir.replace('\\', '/')
                    if not os.path.exists(file_dir):
                        os.makedirs(file_dir)
                file_name, file_ext = file.filename.rsplit('.', 1)
                file_name = f'{file_name}-{time.strftime("%Y%m%dT%H%M%S")}-{file_token}.{file_ext}'
                file_name = secure_filename(file_name)
                file_path = fs.path.join(file_dir, file_name)
                file.save(file_path)
                static_dir = fs.path.basename(APP.config['UPLOAD_FOLDER'])
                static_dir = static_dir.replace('\\', '/')
                static_file_path = os.path.join(static_dir, op_id, file_name)
            new_message = cm.add_message(user, static_file_path, op_id, message_type)
            new_message_dict = get_message_dict(new_message)
            sockio.emit('chat-message-client', json.dumps(new_message_dict))
            return jsonify({"success": True, "path": static_file_path})
        return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
    # normal use case never gets to this
    return "False"


@APP.route('/uploads/<name>/<path:filename>', methods=["GET"])
def uploads(name=None, filename=None):
    base_path = mscolab_settings.UPLOAD_FOLDER
    if name is None:
        abort(404)
    if filename is None:
        abort(404)
    return send_from_directory(base_path, werkzeug.security.safe_join("", name, filename))


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
    last_used = datetime.datetime.utcnow()
    user = g.user
    r = str(fm.create_operation(path, description, user, last_used, content=content, category=category))
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
    # ToDo refactor see fm.get_change_content(
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
    r = str(fm.update_operation(int(op_id), attribute, value, user))
    if r == "True":
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return r


@APP.route('/operation_details', methods=["GET"])
@verify_user
def get_operation_details():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    user = g.user
    result = fm.get_operation_details(int(op_id), user)
    if result is False:
        return "False"
    return json.dumps(result)


@APP.route('/set_last_used', methods=["POST"])
@verify_user
def set_last_used():
    # ToDo refactor move to file_manager
    op_id = request.form.get('op_id', None)
    operation = Operation.query.filter_by(id=int(op_id)).first()
    operation.last_used = datetime.datetime.utcnow()
    temp_operation_active = operation.active
    operation.active = True
    db.session.commit()
    # Reload Operation List
    if not temp_operation_active:
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return jsonify({"success": True}), 200


@APP.route('/update_last_used', methods=["POST"])
@verify_user
def update_last_used():
    # ToDo refactor move to file_manager
    operations = Operation.query.filter().all()
    for operation in operations:
        if operation.last_used is not None and \
                (datetime.datetime.utcnow() - operation.last_used).days > 30:
            operation.active = False
        else:
            operation.active = True
    db.session.commit()
    return jsonify({"success": True}), 200


@APP.route('/undo', methods=["POST"])
@verify_user
def undo_ftml():
    # ToDo rename to undo_changes
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo(ch_id, user)
    # get op_id from change
    ch = Change.query.filter_by(id=ch_id).first()
    if result is True:
        sockio.sm.emit_file_change(ch.op_id)
    return str(result)


@APP.route("/creator_of_operation", methods=["GET"])
@verify_user
def get_creator_of_operation():
    op_id = request.args.get('op_id', request.form.get('op_id', None))
    u_id = g.user.id
    creator_name = fm.fetch_operation_creator(op_id, u_id)
    if creator_name is False:
        return jsonify({"success": False, "message": "You don't have access to this data"}), 403
    return jsonify({"success": True, "username": creator_name}), 200


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
        sockio.sm.emit_operation_permissions_updated(user.id, op_id)
        return jsonify({"success": True, "message": "User permissions successfully deleted!"})

    return jsonify({"success": False, "message": "Some error occurred. Please try again."})


@APP.route('/import_permissions', methods=['POST'])
@verify_user
def import_permissions():
    import_op_id = int(request.form.get('import_op_id'))
    current_op_id = int(request.form.get('current_op_id'))
    user = g.user
    success, users, message = fm.import_permissions(import_op_id, current_op_id, user.id)
    if success:
        for u_id in users["add_users"]:
            sockio.sm.emit_new_permission(u_id, current_op_id)
        for u_id in users["modify_users"]:
            # changes navigation for viewer/collaborator
            sockio.sm.emit_update_permission(u_id, current_op_id)
        for u_id in users["delete_users"]:
            # invalidate waypoint table, title of windows
            sockio.sm.emit_revoke_permission(u_id, current_op_id)

        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)

        sockio.sm.emit_operation_permissions_updated(user.id, current_op_id)
        return jsonify({"success": True})

    return jsonify({"success": False,
                    "message": message})


@APP.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = confirm_token(token, expiration=86400)
    except TypeError:
        return jsonify({"success": False}), 401
    if email is False:
        flash("Sorry, your token has expired or is invalid! We will need to resend your authentication email",
              'category_info')
        return render_template('user/status.html', uri={"path": "reset_request", "name": "Resend authentication email"})
    user = User.query.filter_by(emailid=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            user.hash_password(form.confirm_password.data)
            user.confirmed = True
            db.session.commit()
            flash('Password reset Success. Please login by the user interface.', 'category_success')
            return render_template('user/status.html')
        except IOError:
            flash('Password reset failed. Please try again later', 'category_danger')
    return render_template('user/reset_password.html', form=form)


@APP.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if mscolab_settings.MAIL_ENABLED:
        form = ResetRequestForm()
        if form.validate_on_submit():
            # Check wheather user exists or not based on the db
            user = User.query.filter_by(emailid=form.email.data).first()
            if user:
                try:
                    username = user.username
                    token = generate_confirmation_token(form.email.data)
                    reset_password_url = url_for('reset_password', token=token, _external=True)
                    html = render_template('user/reset_confirmation.html',
                                           reset_password_url=reset_password_url, username=username)
                    subject = "MSColab Password reset request"
                    send_email(form.email.data, subject, html)
                    flash('An email was sent if this user account exists', 'category_success')
                    return render_template('user/status.html')
                except IOError:
                    flash('''We apologize, but it seems that there was an issue sending
                    your request email. Please try again later.''', 'category_info')
            else:
                flash('An email was sent if this user account exists', 'category_success')
                return render_template('user/status.html')
        return render_template('user/reset_request.html', form=form)
    else:
        logging.warning("To send emails, the value of `MAIL_ENABLED` in `conf.py` should be set to True.")
        return render_template('errors/403.html'), 403


def start_server(app, sockio, cm, fm, port=8083):
    create_files()
    sockio.run(app, port=port)


def main():
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)

if __name__ == '__main__':
    main()
