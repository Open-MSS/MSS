# -*- coding: utf-8 -*-
"""

    mslib.utils.auth
    ~~~~~~~~~~~~~~~~

    handles passwords from the keyring for login and http_auuth


    To better understand of the code, look at the 'ships' example from
    chapter 14/16 of 'Rapid GUI Programming with Python and Qt: The
    Definitive Guide to PyQt Programming' (Mark Summerfield).

    This file is part of MSS.

    :copyright: Copyright 2023 Reimar Bauer
    :copyright: Copyright 2023-2026 by the MSS team, see AUTHORS.
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
import datetime
import functools
import logging

import email_validator
import keyring
import sqlalchemy
from flask import request, abort, g, current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature

from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.models import User

try:
    from jeepney.wrappers import DBusErrorResponse
except (ImportError, ModuleNotFoundError):
    class DBusErrorResponse(Exception):
        """
        Fallback definition on not DBus systems
        """
        def __init__(self, message):
            super().__init__(message)

from mslib.msui import constants


NAME = __name__


def del_password_from_keyring(service_name=NAME, username=""):
    """
    removes an entry by username and service_name from the keyring
    """
    if username.strip() != "":
        try:
            keyring.delete_password(service_name=service_name, username=username)
        except (keyring.errors.NoKeyringError, keyring.errors.PasswordDeleteError) as ex:
            logging.warning("Can't use Keyring on your system: %s" % ex)


def get_password_from_keyring(service_name=NAME, username=""):
    """
    When we request a username we use this function to fill in a form field with a password
    In this case by none existing credentials in the keyring we have to return an empty string
    """
    if username.strip() != "":
        try:
            cred = keyring.get_credential(service_name=service_name, username=username)
            if username is not None and cred is None:
                return ""
            elif cred is None:
                return None
            else:
                return cred.password
        except (keyring.errors.KeyringLocked, keyring.errors.InitError, DBusErrorResponse) as ex:
            logging.warning(ex)
            return None


def save_password_to_keyring(service_name=NAME, username="", password=""):
    """
    save a username and password for a given service_name
    """
    if "" not in (username.strip(), password.strip()):
        try:
            keyring.set_password(service_name=service_name, username=username, password=password)
        except keyring.errors.NoKeyringError as ex:
            logging.info("Can't use Keyring on your system: %s" % ex)


def get_auth_from_url_and_name(server_url, http_auth, overwrite_login_cache=True):
    """
    gets auth_username from http_auth and password from keyring for a given server_url
    """
    name = ""
    for url, auth_name in http_auth.items():
        if server_url == url:
            try:
                password = get_password_from_keyring(service_name=url, username=auth_name)
            except keyring.errors.NoKeyringError as ex:
                password = None
                logging.info("Can't use Keyring on your system: %s" % ex)
            if overwrite_login_cache and password is not None and password.strip() != "":
                constants.AUTH_LOGIN_CACHE[server_url] = (auth_name, password)
            name = auth_name
            break
    if name == "":
        name = None
    auth = constants.AUTH_LOGIN_CACHE.get(server_url, (name, None))
    return auth


def check_login(emailid, password):
    try:
        user = User.query.filter_by(emailid=str(emailid)).first()
    except sqlalchemy.exc.OperationalError as ex:
        logging.debug("Problem in the database (%ex), likely version client different", ex)
        return False
    if user is not None:
        if current_app.config['MAIL_ENABLED']:
            if user.confirmed:
                if user.verify_password(password):
                    return user
        else:
            if user.verify_password(password):
                return user
    return False


def register_user(email, password, username, fullname):
    if len(str(email.strip())) == 0 or len(str(username.strip())) == 0:
        return {"success": False, "message": "Your username or email cannot be empty"}
    is_valid_username = True if username.find("@") == -1 else False
    try:
        # ToDo verify what changed for check_deliverability
        email_validator.validate_email(email, check_deliverability=current_app.config['MAIL_ENABLED'])
    except (email_validator.exceptions.EmailSyntaxError):
        return {"success": False, "message": "Your email ID is not valid!"}
    if not is_valid_username:
        return {"success": False, "message": "Your username cannot contain @ symbol!"}
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return {"success": False, "message": "This email ID is already taken!"}
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return {"success": False, "message": "This username is already registered"}
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
    user = User(email, username, password, fullname)
    result = fm.modify_user(user, action="create")
    return {"success": result}


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def send_email(to, subject, template):
    if current_app.config['MAIL_DEFAULT_SENDER'] is not None:
        msg = Message(
            subject,
            recipients=[to],
            html=template,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        try:
            from mslib.mscolab.server import getConfig
            mail = getConfig()[4]
            mail.send(msg)
        except IOError:
            logging.error("Can't send email to %s", to)
    else:
        logging.debug("setup user verification by email")


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except (IOError, BadSignature):
        return False
    return email


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
    from mslib.mscolab.server import getConfig
    fm = getConfig()[3]
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
            if current_app.config['MAIL_ENABLED']:
                if user.confirmed:
                    g.user = user
                    return func(*args, **kwargs)
                else:
                    return "False"
            else:
                g.user = user
                return func(*args, **kwargs)
    return wrapper
