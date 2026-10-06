# -*- coding: utf-8 -*-
"""

    mslib.mscolab.auth
    ~~~~~~~~~~~~~~~~~~

    handles login/token/SAML logic

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
import hashlib
import hmac
import logging

import email_validator
import sqlalchemy
from flask import current_app, request, abort, g, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature

from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.models import User


def optional_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
            auth_basic_auth = current_app.extensions['basic_auth']
            return auth_basic_auth.login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated


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
    except (email_validator.exceptions.EmailSyntaxError, email_validator.exceptions.EmailUndeliverableError):
        return {"success": False, "message": "Your email ID is not valid!"}
    if not is_valid_username:
        return {"success": False, "message": "Your username cannot contain @ symbol!"}
    user_exists = User.query.filter_by(emailid=str(email)).first()
    if user_exists:
        return {"success": False, "message": "This email ID is already taken!"}
    user_exists = User.query.filter_by(username=str(username)).first()
    if user_exists:
        return {"success": False, "message": "This username is already registered"}
    fm = current_app.extensions['fm']
    user = User(email, username, password, fullname)
    result = fm.modify_user(user, action="create")
    return {"success": result}


def _request_user():
    """
    Returns the user authenticated by the token of the request, None if there is none or it is not confirmed
    """
    try:
        user = User.verify_auth_token(request.args.get('token', request.form.get('token', False)))
    except TypeError:
        logging.debug("no token in request form")
        abort(404)
    if not user or (current_app.config['MAIL_ENABLED'] and not user.confirmed):
        return None
    return user


def verify_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = _request_user()
        if user is None:
            return "False"
        # saving user details in flask.g
        g.user = user
        return func(*args, **kwargs)
    return wrapper


def verify_user_http(func):
    """
    Like verify_user, but refuses with HTTP 401 instead of the body "False",
    for endpoints whose response is not read as text, e.g. file downloads
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user = _request_user()
        if user is None:
            abort(401)
        g.user = user
        return func(*args, **kwargs)
    return wrapper


# Purposes of the tokens of generate_confirmation_token. Each has its own salt, so a token of one purpose, e.g. the
# email confirmation, can't be used for another, e.g. a password reset.
EMAIL_CONFIRMATION = "email-confirmation"
PASSWORD_RESET = "password-reset"
IDP_LOGIN = "idp-login"
_TOKEN_PURPOSES = (EMAIL_CONFIRMATION, PASSWORD_RESET, IDP_LOGIN)


def _serializer(purpose):
    # signed with SECRET_KEY, which every process of the server shares since #3239; a fixed salt per purpose, so
    # links still work after a restart or on another worker
    if purpose not in _TOKEN_PURPOSES:
        raise ValueError(f"unknown token purpose {purpose!r}")
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=f"mscolab-{purpose}")


def confirm_token(token, purpose, expiration=3600):
    """
    The email of a token of generate_confirmation_token for purpose, False if it is invalid or expired
    """
    try:
        email = _serializer(purpose).loads(token, max_age=expiration)
    except (IOError, BadSignature):
        return False
    return email


def generate_confirmation_token(email, purpose):
    """
    A signed token with email for purpose, one of EMAIL_CONFIRMATION, PASSWORD_RESET and IDP_LOGIN
    """
    return _serializer(purpose).dumps(email)


def _password_fingerprint(password_hash):
    # changes with the password; a keyed digest, so the token doesn't tell anything about the password hash
    key = current_app.config['SECRET_KEY']
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hmac.new(key, str(password_hash).encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def generate_password_reset_token(user):
    """
    A token for one password reset of user: it is no longer valid once the password has changed
    """
    return _serializer(PASSWORD_RESET).dumps({"email": user.emailid, "password": _password_fingerprint(user.password)})


def confirm_password_reset_token(token, expiration=86400):
    """
    (user, password hash) of a token of generate_password_reset_token, None if it is invalid, expired or already
    used; the password hash is the one the token was made for, see User.reset_password
    """
    try:
        data = _serializer(PASSWORD_RESET).loads(token, max_age=expiration)
    except (IOError, BadSignature):
        return None
    if not isinstance(data, dict):
        return None
    user = User.query.filter_by(emailid=str(data.get("email"))).first()
    if user is None or not hmac.compare_digest(str(data.get("password")), _password_fingerprint(user.password)):
        return None
    return user, user.password


def public_url_for(endpoint, **values):
    """
    The URL of endpoint for links in emails, built from PUBLIC_URL, not from the address of the request

    A request can name any host in its Host header; url_for(..., _external=True) would put it into the link, and
    the token of the link would go to that host.
    """
    return current_app.config['PUBLIC_URL'].rstrip("/") + url_for(endpoint, **values)


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
    fm = current_app.extensions['fm']
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
