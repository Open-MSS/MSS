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


import collections.abc
import datetime
import functools
import hashlib
import hmac
import logging
import secrets

import email_validator
import sqlalchemy
from flask import current_app, request, abort, g, url_for
from itsdangerous import URLSafeTimedSerializer, BadSignature
from saml2.saml import NAMEID_FORMAT_PERSISTENT

from mslib.mscolab.api.schemas import TOKEN_HEADER
from mslib.mscolab.app import db
from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.models import IdpIdentity, SamlLogin, User


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


def request_token():
    """
    Returns the login token of the request, False if there is none

    msui sends it in the header TOKEN_HEADER with GET requests, in the body with others; older clients sent it in
    the query string or the body.
    """
    return request.headers.get(TOKEN_HEADER) or request.args.get('token', request.form.get('token', False))


def _request_user():
    """
    Returns the user authenticated by the token of the request, None if there is none or it is not confirmed
    """
    try:
        user = User.verify_auth_token(request_token())
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
_TOKEN_PURPOSES = (EMAIL_CONFIRMATION, PASSWORD_RESET)


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
    A signed token with email for purpose, one of EMAIL_CONFIRMATION and PASSWORD_RESET
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


def find_idp_config(idp_identity_name):
    """The configured IdP idp_identity_name of setup_saml2_backend.CONFIGURED_IDPS, None if there is none"""
    for idp_config in setup_saml2_backend.CONFIGURED_IDPS:
        if idp_config['idp_identity_name'] == idp_identity_name:
            return idp_config
    return None


def get_idp_entity_id(selected_idp):
    """
    Finds the entity_id from the configured IDPs
    :return: the entity_id of the idp or None
    """
    idp_config = find_idp_config(selected_idp)
    if idp_config is None:
        return None
    return idp_config['idp_data']['saml2client'].metadata.identity_providers()[0]


# The IdP must answer a SAML login within SAML_REQUEST_LIFETIME seconds, msui must exchange its code within
# IDP_LOGIN_CODE_LIFETIME seconds after that
SAML_REQUEST_LIFETIME = 600
IDP_LOGIN_CODE_LIFETIME = 1200
# Anyone can start a SAML login, the server keeps at most this many unfinished ones
MAX_SAML_LOGINS = 1000


def _now():
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _saml_requests(idp_identity_name, request_id):
    # the login request_id sent to the IdP idp_identity_name, if the IdP can still answer it
    return SamlLogin.query.filter(
        SamlLogin.request_id == str(request_id),
        SamlLogin.idp_identity_name == str(idp_identity_name),
        SamlLogin.code_hash.is_(None),
        SamlLogin.created_on >= _now() - datetime.timedelta(seconds=SAML_REQUEST_LIFETIME))


def remember_saml_request(request_id, idp_identity_name):
    """
    Stores the id of an AuthnRequest sent to the IdP idp_identity_name: only a response to it is accepted, and once

    Returns False and stores nothing if MAX_SAML_LOGINS logins are unfinished, until some of them expire.
    """
    # expired requests and codes
    SamlLogin.query.filter(sqlalchemy.or_(
        sqlalchemy.and_(SamlLogin.code_hash.is_(None),
                        SamlLogin.created_on < _now() - datetime.timedelta(seconds=SAML_REQUEST_LIFETIME)),
        SamlLogin.created_on < _now() - datetime.timedelta(seconds=IDP_LOGIN_CODE_LIFETIME),
    )).delete(synchronize_session=False)
    if SamlLogin.query.count() >= MAX_SAML_LOGINS:
        db.session.commit()
        return False
    db.session.add(SamlLogin(request_id, idp_identity_name))
    db.session.commit()
    return True


class OutstandingSamlRequests(collections.abc.Mapping):
    """
    The AuthnRequests sent to an IdP that it can still answer, as pysaml2 expects them in parse_authn_request_response

    Looked up in the database, a response can arrive at another process of the server than the one that sent the
    request. pysaml2 refuses a response to a request that isn't one of them, also if the SP configuration has
    allow_unsolicited; finish_saml_login refuses one without a request.
    """

    def __init__(self, idp_identity_name):
        self.idp_identity_name = idp_identity_name
        # pysaml2 looks up the same request several times
        self._found = {}

    def __getitem__(self, request_id):
        if request_id is None:
            raise KeyError(request_id)
        if request_id not in self._found:
            self._found[request_id] = _saml_requests(self.idp_identity_name, request_id).first() is not None
        if not self._found[request_id]:
            raise KeyError(request_id)
        # where the login started, pysaml2 keeps it as came_from; unused
        return "/"

    def __iter__(self):
        # pysaml2 only logs the keys
        return iter(())

    def __len__(self):
        return 0

    def __bool__(self):
        # pysaml2 ignores an empty mapping
        return True


def saml_attributes(authn_response):
    """
    The attributes of a SAML response as {name: [values]}, by their names in the response and by the friendly names
    of pysaml2's attribute maps
    """
    attributes = {}
    assertion = getattr(authn_response, "assertion", None)
    for statement in (assertion.attribute_statement if assertion is not None else []):
        for attribute in statement.attribute:
            values = [value.text for value in attribute.attribute_value if value.text]
            for name in (attribute.name, attribute.friendly_name):
                if name:
                    attributes.setdefault(name, values)
    for name, values in (authn_response.ava or {}).items():
        attributes[name] = [value for value in values if isinstance(value, str)]
    return attributes


def saml_identity(authn_response, idp_data, attributes):
    """
    (issuer, subject) of a SAML response, the identity a user is linked to; None if the response has no persistent
    identifier

    The issuer is the entity id of the IdP that signed the assertion: the metadata of one configured IdP can hold
    several, e.g. of a federation. The issuer of the response around it may be unsigned. An unsigned assertion
    (want_assertion_signed: false) counts only if the signed response has the same issuer: pysaml2 checks the
    signature of an assertion or response that has one, so only a signature ties the issuer to its key. The subject
    is the value of the attribute idp_data['user_id_attribute'] in attributes, see saml_attributes, or the NameID if
    that isn't set and the NameID is persistent. A transient NameID changes with every login, an email address can
    be given to someone else. Logs why a response has no identity.
    """
    assertion = getattr(authn_response, "assertion", None)
    issuer = assertion.issuer.text if assertion is not None and assertion.issuer is not None else None
    if issuer and getattr(assertion, "signature", None) is None:
        response = getattr(authn_response, "response", None)
        if getattr(response, "signature", None) is None or authn_response.issuer() != issuer:
            logging.warning("Refused a SAML response with an unsigned assertion of %r: the response around it isn't "
                            "signed by the same IdP", issuer)
            return None
    attribute = idp_data.get('user_id_attribute')
    if attribute:
        values = attributes.get(attribute, [])
        # of several values none is the identifier
        subject = values[0] if len(values) == 1 else None
    else:
        name_id = authn_response.name_id
        subject = name_id.text if name_id is not None and name_id.format == NAMEID_FORMAT_PERSISTENT else None
    if not issuer:
        logging.warning("Refused a SAML response without issuer")
        return None
    if not subject:
        logging.warning("Refused a SAML response of %r without a persistent identifier: set 'user_id_attribute' of "
                        "the IdP to a single valued attribute that identifies a user", issuer)
        return None
    if len(issuer) > 255 or len(subject) > 255:
        logging.warning("Refused a SAML response of %r: its issuer or identifier is longer than 255 characters", issuer)
        return None
    return issuer, subject


class SamlLoginRefused(Exception):
    """A SAML login that can't log in, the message tells the user why"""


def user_of_email(emailid):
    """
    The user of emailid, whatever its case, None if there is none; an exact match comes first

    Raises SamlLoginRefused if several accounts have emailid in different case: which one is meant is unknown.
    """
    user = User.query.filter_by(emailid=str(emailid)).first()
    if user is None:
        users = User.query.filter(sqlalchemy.func.lower(User.emailid) == str(emailid).lower()).limit(2).all()
        if len(users) > 1:
            raise SamlLoginRefused("Several accounts of this server have your email address in different upper and "
                                   "lower case. Ask its administrator for help.")
        user = users[0] if users else None
    return user


def _new_saml_username(emailid, username):
    """
    The username of a new account for a SAML login: the one that the IdP sent, else, also if that is taken or
    can't be used, the start of the email; raises SamlLoginRefused if register_user would refuse both
    """
    candidates = [name for name in (username, emailid.split("@")[0]) if name]
    for candidate in candidates:
        if len(candidate) <= 255 and "@" not in candidate \
                and User.query.filter_by(username=candidate).first() is None:
            return candidate
    raise SamlLoginRefused(f"The usernames {' and '.join(repr(name) for name in candidates)} that your identity "
                           "provider sent are taken or can't be used for an account of this server. Ask its "
                           "administrator for help.")


def check_saml_login(issuer, subject, emailid, username):
    """
    Checks the email and username that the IdP sent with the identity (issuer, subject); returns them as
    finish_saml_login stores them, raises SamlLoginRefused if the login can't log in

    A linked identity needs neither. Else the email must be valid: it may belong to an existing account, which must
    be linked, see idp_login. Else a new account is created, its username is checked like by register_user.
    """
    if IdpIdentity.query.filter_by(issuer=str(issuer), subject=str(subject)).first() is not None:
        return None, None
    if not isinstance(emailid, str) or len(emailid) > 255:
        raise SamlLoginRefused("Your identity provider sent no valid email address.")
    try:
        email_validator.validate_email(emailid, check_deliverability=False)
    except email_validator.EmailNotValidError:
        raise SamlLoginRefused("Your identity provider sent no valid email address.")
    if user_of_email(emailid) is not None:
        return emailid, None
    return emailid, _new_saml_username(emailid, username)


def _code_hash(code):
    # the code is random and long, a plain hash is enough to not store it
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def finish_saml_login(request_id, idp_identity_name, issuer, subject, emailid, username):
    """
    Stores the identity that the IdP asserts in its response to the login request_id, with emailid and username
    checked by check_saml_login; returns a one-time code that msui exchanges for a login token by idp_login, None if
    the IdP can't answer request_id (any more)

    Only one response per request: a second one, e.g. the first sent again, is refused.
    """
    if request_id is None:
        return None
    code = secrets.token_urlsafe(32)
    updated = _saml_requests(idp_identity_name, request_id).update({
        SamlLogin.code_hash: _code_hash(code),
        SamlLogin.issuer: str(issuer),
        SamlLogin.subject: str(subject),
        SamlLogin.emailid: None if emailid is None else str(emailid),
        SamlLogin.username: None if username is None else str(username),
        SamlLogin.created_on: _now(),
    }, synchronize_session=False)
    db.session.commit()
    return code if updated == 1 else None


_SamlLoginResult = collections.namedtuple("_SamlLoginResult", "id idp_identity_name issuer subject emailid username")


def _saml_login_of_code(code):
    # the finished SAML login of code, a copy: the row is gone once the code is used
    if not isinstance(code, str) or not code:
        return None
    saml_login = SamlLogin.query.filter(
        SamlLogin.code_hash == _code_hash(code),
        SamlLogin.created_on >= _now() - datetime.timedelta(seconds=IDP_LOGIN_CODE_LIFETIME)).first()
    if saml_login is None:
        return None
    return _SamlLoginResult(saml_login.id, saml_login.idp_identity_name, saml_login.issuer, saml_login.subject,
                            saml_login.emailid, saml_login.username)


def _use_saml_login(saml_login, user, link=False, first_identity=False):
    """
    Uses up the code of saml_login: stores user, if it is new, and links the identity of saml_login to it, if link

    All in one transaction, so nothing changes if it fails: another request used the code first, linked the identity,
    or created the account meanwhile; or first_identity and the user has an identity meanwhile. Returns whether it
    succeeded.
    """
    # the checks below read the state of now, not of the reads before
    db.session.commit()
    try:
        if SamlLogin.query.filter_by(id=saml_login.id).delete(synchronize_session=False) != 1:
            db.session.rollback()
            return False
        if user.id is None:
            db.session.add(user)
            db.session.flush()
        elif first_identity:
            # waits for another request that links an identity to user at the same time
            User.query.filter_by(id=user.id).with_for_update().one()
            if IdpIdentity.query.filter_by(u_id=user.id).count() > 0:
                db.session.rollback()
                return False
        if link:
            db.session.add(IdpIdentity(user.id, saml_login.issuer, saml_login.subject))
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        db.session.rollback()
        return False
    return True


def _refuse_unconfirmed(user):
    # like /token, before the code is used: the user can confirm the email and try the same code again
    if current_app.config['MAIL_ENABLED'] and not user.confirmed:
        raise SamlLoginRefused("Your account isn't confirmed yet. Confirm your email address, then enter the code "
                               "again.")


def idp_login(code):
    """
    The user that the one-time code of a SAML login logs in

    Returns (user, None) and makes the code invalid. Returns (None, emailid) if the identity isn't linked to a user
    and its email belongs to an existing account: the user must log in to that account to link it, see
    link_idp_identity, the code stays valid for that. Returns (None, None) if the code is invalid or expired, or the
    login can't log in, see check_saml_login. Raises SamlLoginRefused, with a message for the user, if the account
    isn't confirmed (with MAIL_ENABLED) or its email is ambiguous; the code stays valid then.

    A new identity gets a new account. A SAML login never changes the password of an account.
    """
    saml_login = _saml_login_of_code(code)
    if saml_login is None:
        return None, None
    identity = IdpIdentity.query.filter_by(issuer=saml_login.issuer, subject=saml_login.subject).first()
    if identity is not None:
        user = identity.user
        _refuse_unconfirmed(user)
        return (user, None) if _use_saml_login(saml_login, user) else (None, None)
    if not saml_login.emailid:
        logging.warning("The SAML login of %s has no email, can't create an account", saml_login.idp_identity_name)
        return None, None
    user = user_of_email(saml_login.emailid)
    if user is not None:
        # Accounts of older versions logged in by the email that the IdP sent. One that logged in by this IdP before
        # and has no identity yet is linked on its first login, if the response comes from the IdP the login request
        # went to: the metadata of a federation lets any of its IdPs answer and assert the email. Any other account
        # must be linked by its owner.
        if user.authentication_backend != saml_login.idp_identity_name or user.idp_identities \
                or saml_login.issuer != get_idp_entity_id(saml_login.idp_identity_name):
            return None, user.emailid
        _refuse_unconfirmed(user)
        linked = _use_saml_login(saml_login, user, link=True, first_identity=True)
        return (user, None) if linked else (None, None)
    try:
        username = _new_saml_username(saml_login.emailid, saml_login.username)
    except SamlLoginRefused as ex:
        # an account with the username was created since the IdP answered
        logging.warning("Refused the SAML login of %s: %s", saml_login.idp_identity_name, ex)
        return None, None
    # nobody knows the password, the owner can set one by a password reset
    user = User(saml_login.emailid, username, password=secrets.token_urlsafe(32), confirmed=True,
                confirmed_on=_now() + datetime.timedelta(seconds=1),
                authentication_backend=saml_login.idp_identity_name)
    return (user, None) if _use_saml_login(saml_login, user, link=True) else (None, None)


def link_idp_identity(user, code):
    """
    Links the identity of a SAML login to user, if idp_login refused its code because its email is the one of user;
    returns whether it was linked

    user is logged in, so whoever links knows the password of the account and can log in at the IdP.
    """
    saml_login = _saml_login_of_code(code)
    if saml_login is None or not saml_login.emailid or saml_login.emailid.lower() != user.emailid.lower():
        return False
    return _use_saml_login(saml_login, user, link=True)
