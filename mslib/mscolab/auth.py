# -*- coding: utf-8 -*-
"""

    mslib.mscolab.auth
    ~~~~~~~~~~~~~~~~~~

    handles passwords from the keyring for login and http_auth

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
import sqlalchemy
from flask import current_app, request, abort, g
from itsdangerous import URLSafeTimedSerializer, BadSignature

from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.models import User


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


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])


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
