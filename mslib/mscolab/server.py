# -*- coding: utf-8 -*-
"""

    mslib.mscolab.server
    ~~~~~~~~~~~~~~~~~~~~

    Server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2024 by the MSS team, see AUTHORS.
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
import datetime
import secrets
import socketio
import sqlalchemy.exc
import werkzeug

from itsdangerous import URLSafeTimedSerializer, BadSignature
from flask import g, jsonify, request, render_template, flash
from flask import send_from_directory, abort, url_for, redirect
from flask_mail import Mail, Message
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from validate_email import validate_email
from saml2.metadata import create_metadata_string
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from flask.wrappers import Response

from mslib.mscolab.conf import mscolab_settings, setup_saml2_backend
from mslib.mscolab.models import Change, MessageType, User
from mslib.mscolab.sockets_manager import _setup_managers
from mslib.mscolab.utils import create_files, get_message_dict
from mslib.utils import conditional_decorator
from mslib.index import create_app
from mslib.mscolab.forms import ResetRequestForm, ResetPasswordForm


APP = create_app(__name__, imprint=mscolab_settings.IMPRINT, gdpr=mscolab_settings.GDPR)
mail = Mail(APP)
CORS(APP, origins=mscolab_settings.CORS_ORIGINS if hasattr(mscolab_settings, "CORS_ORIGINS") else ["*"])
auth = HTTPBasicAuth()


try:
    from mscolab_auth import mscolab_auth
except ImportError as ex:
    logging.warning("Couldn't import mscolab_auth (ImportError:'{%s), creating dummy config.", ex)

    class mscolab_auth:
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


def _initialize_managers(app):
    sockio, cm, fm = _setup_managers(app)
    # initializing socketio and db
    app.wsgi_app = socketio.Middleware(socketio.server, app.wsgi_app)
    sockio.init_app(app)
    # db.init_app(app)
    return app, sockio, cm, fm


_app, sockio, cm, fm = _initialize_managers(APP)


def check_login(emailid, password):
    try:
        user = User.query.filter_by(emailid=str(emailid)).first()
    except sqlalchemy.exc.OperationalError as ex:
        logging.debug("Problem in the database (%ex), likely version client different", ex)
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


def register_user(email, password, username):
    if len(str(email.strip())) == 0 or len(str(username.strip())) == 0:
        return {"success": False, "message": "Your username or email cannot be empty"}
    is_valid_username = True if username.find("@") == -1 else False
    is_valid_email = validate_email(email)
    if not is_valid_email:
        return {"success": False, "message": "Your email ID is not valid!"}
    if not is_valid_username:
        return {"success": False, "message": "Your username cannot contain @ symbol!"}
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return {"success": False, "message": "This email ID is already taken!"}
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return {"success": False, "message": "This username is already registered"}
    user = User(email, username, password)
    result = fm.modify_user(user, action="create")
    return {"success": result}


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


def get_idp_entity_id(selected_idp):
    """
    Finds the entity_id from the configured IDPs
    :return: the entity_id of the idp or None
    """
    for config in setup_saml2_backend.CONFIGURED_IDPS:
        if selected_idp == config['idp_identity_name']:
            idps = config['idp_data']['saml2client'].metadata.identity_providers()
            only_idp = idps[0]
            entity_id = only_idp
            return entity_id
    return None


def create_or_update_idp_user(email, username, token, authentication_backend):
    """
    Creates or updates an idp user in the system based on the provided email,
     username, token, and authentication backend.
    :param email: idp users email
    :param username: idp users username
    :param token: authentication token
    :param authentication_backend: authenticated identity providers name
    :return: bool : query success or not
    """
    user = User.query.filter_by(emailid=email).first()
    if not user:
        # using an IDP for a new account/profile, e-mail is already verified by the IDP
        confirm_time = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=1)
        user = User(email, username, password=token, confirmed=True, confirmed_on=confirm_time,
                    authentication_backend=authentication_backend)
        result = fm.modify_user(user, action="create")
    else:
        user.authentication_backend = authentication_backend
        user.hash_password(token)
        result = fm.modify_user(user, action="update_idp_user")
    return result


@APP.route('/')
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
def home():
    return render_template("/index.html")


@APP.route("/status")
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
def hello():
    if request.authorization is not None:
        if mscolab_settings.__dict__.get('enable_basic_http_authentication', False):
            auth.login_required()
            return json.dumps({
                'message': "Mscolab server",
                'use_saml2': mscolab_settings.USE_SAML2,
                'direct_login': mscolab_settings.DIRECT_LOGIN
            })
        return json.dumps({
            'message': "Mscolab server",
            'use_saml2': mscolab_settings.USE_SAML2,
            'direct_login': mscolab_settings.DIRECT_LOGIN
        })
    else:
        return json.dumps({
            'message': "Mscolab server",
            'use_saml2': mscolab_settings.USE_SAML2,
            'direct_login': mscolab_settings.DIRECT_LOGIN
        })


@APP.route('/token', methods=["POST"])
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
def get_auth_token():
    emailid = request.form['email']
    password = request.form['password']
    user = check_login(emailid, password)
    if user is not False:
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
@conditional_decorator(auth.login_required, mscolab_settings.__dict__.get('enable_basic_http_authentication', False))
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
            fm.modify_user(user, attribute="confirmed_on", value=datetime.datetime.now(tz=datetime.timezone.utc))
            fm.modify_user(user, attribute="confirmed", value=True)
            return render_template('user/confirmed.html', username=user.username)


@APP.route('/user', methods=["GET"])
@verify_user
def get_user():
    return json.dumps({'user': {'id': g.user.id, 'username': g.user.username}})


@APP.route("/delete_own_account", methods=["POST"])
@verify_user
def delete_own_account():
    """
    delete own account
    """
    user = g.user
    result = fm.modify_user(user, action="delete")
    return jsonify({"success": result}), 200


# Chat related routes
@APP.route("/messages", methods=["GET"])
@verify_user
def messages():
    user = g.user
    op_id = request.args.get("op_id", request.form.get("op_id", None))
    if fm.is_member(user.id, op_id):
        timestamp = request.args.get("timestamp", request.form.get("timestamp", "1970-01-01T00:00:00+00:00"))
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
        users = fm.fetch_users_without_permission(int(op_id), user.id)
        if users is False:
            return jsonify({"success": False, "message": "Could not send message. No file uploaded."})
        if file is not None:
            static_file_path = cm.add_attachment(op_id, APP.config['UPLOAD_FOLDER'], file, file_token)
            if static_file_path is not None:
                new_message = cm.add_message(user, static_file_path, op_id, message_type)
                new_message_dict = get_message_dict(new_message)
                sockio.emit('chat-message-client', json.dumps(new_message_dict))
                return jsonify({"success": True, "path": static_file_path})
            else:
                return "False"
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
    active = (request.form.get('active', "True") == "True")
    last_used = datetime.datetime.now(tz=datetime.timezone.utc)
    user = g.user
    r = str(fm.create_operation(path, description, user, last_used,
                                content=content, category=category, active=active))
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
    named_version = request.args.get('named_version') == "True"
    user = g.user
    result = fm.get_all_changes(int(op_id), user, named_version)
    if result is False:
        jsonify({"success": False, "message": "Some error occurred!"})
    return jsonify({"success": True, "changes": result})


@APP.route('/get_change_content', methods=['GET'])
@verify_user
def get_change_content():
    ch_id = int(request.args.get('ch_id', request.form.get('ch_id', 0)))
    user = g.user
    result = fm.get_change_content(ch_id, user)
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
    skip_archived = (request.args.get('skip_archived', request.form.get('skip_archived', "False")) == "True")
    user = g.user
    return json.dumps({"operations": fm.list_operations(user, skip_archived=skip_archived)})


@APP.route('/delete_operation', methods=["POST"])
@verify_user
def delete_operation():
    op_id = int(request.form.get('op_id', 0))
    user = g.user
    success = fm.delete_operation(op_id, user)
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
    op_id = request.form.get('op_id', None)
    user = g.user
    days_ago = int(request.form.get('days', 0))
    fm.update_operation(int(op_id), 'last_used',
                        datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=days_ago),
                        user)
    if days_ago > mscolab_settings.ARCHIVE_THRESHOLD:
        fm.update_operation(int(op_id), "active", False, user)
    else:
        fm.update_operation(int(op_id), "active", True, user)
        token = request.args.get('token', request.form.get('token', False))
        json_config = {"token": token}
        sockio.sm.update_operation_list(json_config)
    return jsonify({"success": True}), 200


@APP.route('/undo_changes', methods=["POST"])
@verify_user
def undo_changes():
    ch_id = request.form.get('ch_id', -1)
    ch_id = int(ch_id)
    user = g.user
    result = fm.undo_changes(ch_id, user)
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
            fm.modify_user(user, "confirmed", True)
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
            # Check whether user exists or not based on the db
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


if mscolab_settings.USE_SAML2:
    # setup idp login config
    setup_saml2_backend()

    # set routes for SSO
    @APP.route('/available_idps/', methods=['GET'])
    def available_idps():
        """
        This function checks if IDP (Identity Provider) is enabled in the mscolab_settings module.
        If IDP is enabled, it retrieves the configured IDPs from setup_saml2_backend.CONFIGURED_IDPS
        and renders the 'idp/available_idps.html' template with the list of configured IDPs.
        """
        configured_idps = setup_saml2_backend.CONFIGURED_IDPS
        return render_template('idp/available_idps.html', configured_idps=configured_idps), 200

    @APP.route("/idp_login/", methods=['POST'])
    def idp_login():
        """Handle the login process for the user by selected IDP"""
        selected_idp = request.form.get('selectedIdentityProvider')
        sp_config = None
        for config in setup_saml2_backend.CONFIGURED_IDPS:
            if selected_idp == config['idp_identity_name']:
                sp_config = config['idp_data']['saml2client']
                break

        try:
            _, response_binding = sp_config.config.getattr("endpoints", "sp")[
                "assertion_consumer_service"
            ][0]
            entity_id = get_idp_entity_id(selected_idp)
            _, binding, http_args = sp_config.prepare_for_negotiated_authenticate(
                entityid=entity_id,
                response_binding=response_binding,
            )
            if binding == BINDING_HTTP_REDIRECT:
                headers = dict(http_args["headers"])
                return redirect(str(headers["Location"]), code=303)
            return Response(http_args["data"], headers=http_args["headers"])
        except (NameError, AttributeError):
            return render_template('errors/403.html'), 403

    def create_acs_post_handler(config):
        """
        Create acs_post_handler function for the given idp_config.
        """
        def acs_post_handler():
            """
            Function to handle SAML authentication response.
            """
            try:
                outstanding_queries = {}
                binding = BINDING_HTTP_POST
                authn_response = config['idp_data']['saml2client'].parse_authn_request_response(
                    request.form["SAMLResponse"], binding, outstanding=outstanding_queries
                )
                email = None
                username = None

                try:
                    email = authn_response.ava["email"][0]
                    username = authn_response.ava["givenName"][0]
                    token = generate_confirmation_token(email)
                except (NameError, AttributeError, KeyError):
                    try:
                        # Initialize an empty dictionary to store attribute values
                        attributes = {}

                        # Loop through attribute statements
                        for attribute_statement in authn_response.assertion.attribute_statement:
                            for attribute in attribute_statement.attribute:
                                attribute_name = attribute.name
                                attribute_value = \
                                    attribute.attribute_value[0].text if attribute.attribute_value else None
                                attributes[attribute_name] = attribute_value

                        # Extract the email and givenname attributes
                        email = attributes["email"]
                        username = attributes["givenName"]
                        token = generate_confirmation_token(email)
                    except (NameError, AttributeError, KeyError):
                        return render_template('errors/403.html'), 403

                if email is not None and username is not None:
                    idp_user_db_state = create_or_update_idp_user(email,
                                                                  username, token, idp_config['idp_identity_name'])
                    if idp_user_db_state:
                        return render_template('idp/idp_login_success.html', token=token), 200
                    return render_template('errors/500.html'), 500
                return render_template('errors/500.html'), 500
            except (NameError, AttributeError, KeyError):
                return render_template('errors/403.html'), 403
        return acs_post_handler

    # Implementation for handling configured SAML assertion consumer endpoints
    for idp_config in setup_saml2_backend.CONFIGURED_IDPS:
        try:
            for assertion_consumer_endpoint in idp_config['idp_data']['assertion_consumer_endpoints']:
                # Dynamically add the route for the current endpoint
                APP.add_url_rule(f'/{assertion_consumer_endpoint}/', assertion_consumer_endpoint,
                                 create_acs_post_handler(idp_config), methods=['POST'])
        except (NameError, AttributeError, KeyError) as ex:
            logging.warning("USE_SAML2 is %s, Failure is: %s", mscolab_settings.USE_SAML2, ex)

    @APP.route('/idp_login_auth/', methods=['POST'])
    def idp_login_auth():
        """Handle the SAML authentication validation of client application."""
        try:
            data = request.get_json()
            token = data.get('token')
            email = confirm_token(token, expiration=1200)
            if email:
                user = check_login(email, token)
                if user:
                    random_token = secrets.token_hex(16)
                    user.hash_password(random_token)
                    fm.modify_user(user, action="update_idp_user")
                    return json.dumps({
                        "success": True,
                        'token': random_token,
                        'user': {'username': user.username, 'id': user.id, 'emailid': user.emailid}
                    })
                return jsonify({"success": False}), 401
            return jsonify({"success": False}), 401
        except TypeError:
            return jsonify({"success": False}), 401

    @APP.route("/metadata/<idp_identity_name>", methods=['GET'])
    def metadata(idp_identity_name):
        """Return the SAML metadata XML for the requested IDP"""
        for config in setup_saml2_backend.CONFIGURED_IDPS:
            if idp_identity_name == config['idp_identity_name']:
                sp_config = config['idp_data']['saml2client']
                metadata_string = create_metadata_string(
                    None, sp_config.config, 4, None, None, None, None, None
                ).decode("utf-8")
                return Response(metadata_string, mimetype="text/xml")
        return render_template('errors/404.html'), 404


def start_server(app, sockio, cm, fm, port=8083):
    create_files()
    sockio.run(app, port=port)


def main():
    start_server(_app, sockio, cm, fm)


# for wsgi
application = socketio.WSGIApp(sockio)

if __name__ == '__main__':
    main()
