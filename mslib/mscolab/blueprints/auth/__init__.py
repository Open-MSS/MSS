# -*- coding: utf-8 -*-
"""

    mslib.mscolab.blueprints.auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Auth Blueprint for server for mscolab module

    This file is part of MSS.

    :copyright: Copyright 2019 Shivashis Padhi
    :copyright: Copyright 2019-2026 by the MSS team, see AUTHORS.
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
import json
import logging

from flask import Blueprint, request, url_for, render_template, jsonify, flash, redirect, current_app, abort, g
from flask.wrappers import Response
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.metadata import create_metadata_string
from saml2.saml import NAMEID_FORMAT_PERSISTENT

from mslib.mscolab.auth import check_login, register_user, generate_confirmation_token, get_idp_entity_id, \
    confirm_token, generate_password_reset_token, confirm_password_reset_token, public_url_for, EMAIL_CONFIRMATION
from mslib.mscolab.auth import optional_auth, request_token, verify_user
from mslib.mscolab.auth import OutstandingSamlRequests, SamlLoginRefused, check_saml_login, find_idp_config, \
    finish_saml_login, idp_login, link_idp_identity, remember_saml_request, saml_attributes, saml_identity
from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.forms import ResendConfirmationForm, ResetPasswordForm, ResetRequestForm
from mslib.mscolab.models import User
from mslib.mscolab.api import endpoints
from mslib.mscolab.api.attachments import normalized_extensions
from mslib.mscolab.api.schemas import (
    IdpLinkRequest,
    IdpLinkResponse,
    IdpLoginAuthRequest,
    IdpLoginAuthResponse,
    IdpUserInfo,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    StatusResponse,
    UserInfo,
)
from mslib.mscolab.mail import send_email

AUTH_BP = Blueprint('auth', __name__, template_folder='templates')


@AUTH_BP.route(f"/{endpoints.STATUS}")
@optional_auth
def hello():
    if request.authorization is not None and current_app.config.get('ENABLE_BASIC_HTTP_AUTHENTICATION', False):
        current_app.extensions['basic_auth'].login_required()
    response = StatusResponse(
        message="Mscolab server",
        use_saml2=current_app.config['USE_SAML2'],
        direct_login=current_app.config['DIRECT_LOGIN'],
        # msui offers and checks attachments with these before uploading them
        attachment_extensions=sorted(normalized_extensions(current_app.config['MSCOLAB_ATTACHMENT_EXTENSIONS'])),
        max_upload_size=current_app.config['MAX_UPLOAD_SIZE'],
        # msui offers the password reset only if the server can send the email
        mail_enabled=bool(current_app.config['MAIL_ENABLED']),
    )
    return json.dumps(response.to_dict())


@AUTH_BP.route(f"/{endpoints.TOKEN}", methods=["POST"])
@optional_auth
def get_auth_token():
    req = LoginRequest.from_form(request.form)
    user = check_login(req.email, req.password)
    if user is not False:
        if current_app.config['MAIL_ENABLED'] and not user.confirmed:
            return "False"
        token = user.generate_auth_token()
        user_info = UserInfo(id=user.id, username=user.username, fullname=user.fullname)
        return LoginResponse(token=token, user=user_info).to_text()
    else:
        logging.debug("Unauthorized user: %s", req.email)
        return "False"


@AUTH_BP.route('/test_authorized')
def authorized():
    token = request_token()
    user = User.verify_auth_token(token)
    if user is not None:
        if current_app.config['MAIL_ENABLED']:
            if user.confirmed is False:
                return "False"
            else:
                return "True"
        else:
            return "True"
    else:
        return "False"


@AUTH_BP.route(f"/{endpoints.REGISTER}", methods=["POST"])
@optional_auth
def user_register_handler():
    req = RegisterRequest.from_form(request.form)
    result = register_user(req.email, req.password, req.username, req.fullname)
    status_code = 200
    try:
        if result["success"]:
            status_code = 201
            if current_app.config['MAIL_ENABLED']:
                status_code = 204
                token = generate_confirmation_token(req.email, EMAIL_CONFIRMATION)
                confirm_url = public_url_for('auth.confirm_email', token=token)
                html = render_template('auth/user/activate.html', username=req.username, confirm_url=confirm_url)
                subject = "MSColab Please confirm your email"
                if not send_email(req.email, subject, html):
                    # without the email the account can't be confirmed, and its address would stay taken
                    user = User.query.filter_by(emailid=str(req.email)).first()
                    if user is not None:
                        current_app.extensions['fm'].modify_user(user, action="delete")
                    result = {"success": False,
                              "message": "The email to confirm your address could not be sent. Please try again later."}
                    status_code = 503
    except TypeError:
        result, status_code = {"success": False}, 401
    response = RegisterResponse(success=result["success"], message=result.get("message"))
    return jsonify(response.to_dict()), status_code


def saml_required(func):
    """The SAML routes exist only with USE_SAML2"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("USE_SAML2"):
            abort(404)
        return func(*args, **kwargs)
    return wrapper


def init_saml(state):
    """
    Adds the assertion consumer services of the configured IdPs to the app, if it uses SAML

    Their paths come from the configuration of each IdP, so they are added to the app and not to the blueprint, which
    can't change once it was registered with an app.
    """
    app = state.app
    if not app.config.get("USE_SAML2"):
        return
    for idp_config in setup_saml2_backend.CONFIGURED_IDPS:
        try:
            endpoints_ = idp_config['idp_data']['assertion_consumer_endpoints']
        except KeyError as ex:
            logging.warning("The IdP %s has no assertion consumer service: %s", idp_config.get('idp_identity_name'), ex)
            continue
        if not idp_config['idp_data'].get('user_id_attribute'):
            name_id_formats = idp_config['idp_data']['saml2client'].config.getattr("name_id_format", "sp") or []
            if NAMEID_FORMAT_PERSISTENT not in ([name_id_formats] if isinstance(name_id_formats, str)
                                                else name_id_formats):
                logging.warning("The IdP %s has no 'user_id_attribute' and the SP asks for no persistent NameID: "
                                "every SAML login by it is refused. Set 'user_id_attribute' in "
                                "setup_saml2_backend.py, see docs/sso_via_saml_mscolab.rst",
                                idp_config['idp_identity_name'])
        for index, path in enumerate(endpoints_):
            # as configured, also with a trailing slash: the metadata tells the IdP this URL
            app.add_url_rule(f"/{path.lstrip('/')}", f"saml_acs_{idp_config['idp_identity_name']}_{index}",
                             _acs_post_handler(idp_config), methods=['POST'], strict_slashes=False)


def _first(values):
    return values[0] if values else None


def _acs_post_handler(idp_config):
    """The handler of the SAML responses of the IdP idp_config"""
    idp_identity_name = idp_config['idp_identity_name']

    def acs_post_handler():
        try:
            authn_response = idp_config['idp_data']['saml2client'].parse_authn_request_response(
                request.form["SAMLResponse"], BINDING_HTTP_POST, outstanding=OutstandingSamlRequests(idp_identity_name))
        except Exception as ex:
            # pysaml2 raises many kinds of exceptions for an invalid, unsigned, expired or unsolicited response
            logging.warning("Refused a SAML response of %s: %s: %s", idp_identity_name, type(ex).__name__, ex)
            return render_template('auth/errors/403.html'), 403
        if authn_response is None:
            return render_template('auth/errors/403.html'), 403
        attributes = saml_attributes(authn_response)
        identity = saml_identity(authn_response, idp_config['idp_data'], attributes)
        if identity is None:
            # saml_identity logged why
            return render_template('auth/errors/403.html'), 403
        try:
            email, username = check_saml_login(*identity, _first(attributes.get("email") or attributes.get("mail")),
                                               _first(attributes.get("givenName") or attributes.get("displayName")))
        except SamlLoginRefused as ex:
            logging.warning("Refused a SAML response of %s: %s", idp_identity_name, ex)
            return render_template('auth/errors/403.html', message=str(ex)), 403
        code = finish_saml_login(authn_response.in_response_to, idp_identity_name, *identity, email, username)
        if code is None:
            # no login of this server waits for this response: it was sent again, or too late
            logging.warning("Refused a SAML response of %s that answers no open login", idp_identity_name)
            return render_template('auth/errors/403.html'), 403
        return render_template('auth/idp/idp_login_success.html', code=code), 200

    return acs_post_handler


@AUTH_BP.route('/available_idps/', methods=['GET'])
@saml_required
@optional_auth
def available_idps():
    """The page to choose one of the IdPs of setup_saml2_backend.CONFIGURED_IDPS for a login"""
    configured_idps = setup_saml2_backend.CONFIGURED_IDPS
    return render_template('auth/idp/available_idps.html', configured_idps=configured_idps), 200


@AUTH_BP.route("/idp_login/", methods=['POST'])
@saml_required
@optional_auth
def idp_login_handler():
    """Starts a login by the selected IdP: sends the browser there with an AuthnRequest"""
    selected_idp = request.form.get('selectedIdentityProvider')
    idp_config = find_idp_config(selected_idp)
    if idp_config is None:
        return render_template('auth/errors/404.html'), 404
    try:
        sp_config = idp_config['idp_data']['saml2client']
        _, response_binding = sp_config.config.getattr("endpoints", "sp")["assertion_consumer_service"][0]
        entity_id = get_idp_entity_id(selected_idp)
        request_id, binding, http_args = sp_config.prepare_for_negotiated_authenticate(
            entityid=entity_id,
            response_binding=response_binding,
        )
    except (NameError, AttributeError, KeyError, IndexError) as ex:
        logging.warning("Can't create a SAML request for %s: %s", selected_idp, ex)
        return render_template('auth/errors/403.html'), 403
    # the response must answer this request
    if not remember_saml_request(request_id, selected_idp):
        logging.warning("Refused a SAML login by %s: too many logins are unfinished", selected_idp)
        return render_template('auth/errors/503.html'), 503
    if binding == BINDING_HTTP_REDIRECT:
        headers = dict(http_args["headers"])
        return redirect(str(headers["Location"]), code=303)
    return Response(http_args["data"], headers=http_args["headers"])


@AUTH_BP.route(f"/{endpoints.IDP_LOGIN_AUTH}/", methods=['POST'])
@saml_required
@optional_auth
def idp_login_auth():
    """
    Exchanges the one-time code of a SAML login for a login token

    409 if the SAML identity must first be linked to the existing account of its email, see idp_link; 403 with a
    message if the login is refused, e.g. for an account that isn't confirmed (like /token). Like /token behind the
    HTTP basic authentication of the server, if it has one.
    """
    data = request.get_json(silent=True)
    req = IdpLoginAuthRequest.from_json_data(data if isinstance(data, dict) else {})
    try:
        user, emailid = idp_login(req.token)
    except SamlLoginRefused as ex:
        return jsonify(IdpLoginAuthResponse(success=False, message=str(ex)).to_dict()), 403
    if user is not None:
        user_info = IdpUserInfo(username=user.username, id=user.id, emailid=user.emailid, fullname=user.fullname)
        return IdpLoginAuthResponse(success=True, token=user.generate_auth_token(), user=user_info).to_text()
    if emailid is not None:
        return jsonify(IdpLoginAuthResponse(success=False, link_required=True, emailid=emailid).to_dict()), 409
    return jsonify(IdpLoginAuthResponse(success=False).to_dict()), 401


@AUTH_BP.route(f"/{endpoints.IDP_LINK}", methods=['POST'])
@saml_required
@optional_auth
@verify_user
def idp_link():
    """
    Links the SAML identity of a one-time code, that idp_login_auth refused with link_required, to the logged in user

    The code must be one for the email of the user.
    """
    req = IdpLinkRequest.from_form(request.form)
    return jsonify(IdpLinkResponse(success=link_idp_identity(g.user, req.code)).to_dict())


@AUTH_BP.route("/metadata/<idp_identity_name>", methods=['GET'])
@saml_required
def metadata(idp_identity_name):
    """Return the SAML metadata XML for the requested IDP"""
    idp_config = find_idp_config(idp_identity_name)
    if idp_config is None:
        return render_template('auth/errors/404.html'), 404
    metadata_string = create_metadata_string(
        None, idp_config['idp_data']['saml2client'].config, 4, None, None, None, None, None
    ).decode("utf-8")
    return Response(metadata_string, mimetype="text/xml")


AUTH_BP.record_once(init_saml)


@AUTH_BP.route('/confirm/<token>')
def confirm_email(token):
    if current_app.config['MAIL_ENABLED']:
        try:
            email = confirm_token(token, EMAIL_CONFIRMATION)
        except TypeError:
            email = False
        if email is False:
            flash("Sorry, the link to confirm your email address has expired or is invalid", 'category_info')
            return render_template('auth/user/status_password.html', title="Confirm your email address",
                                   uri={"path": url_for("auth.resend_confirmation"),
                                        "name": "get a new confirmation email"}), 401
        user = User.query.filter_by(emailid=email).first_or_404()
        if user.confirmed:
            return render_template('auth/user/confirmed.html', username=user.username)
        else:
            fm = current_app.extensions['fm']
            fm.modify_user(user, attribute="confirmed_on", value=datetime.datetime.now(tz=datetime.timezone.utc))
            fm.modify_user(user, attribute="confirmed", value=True)
            return render_template('auth/user/confirmed.html', username=user.username)
    else:
        logging.warning("To send emails, the value of MAIL_ENABLED in conf.py should be set to True.")
        return render_template('auth/errors/403.html'), 403


@AUTH_BP.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # None also once the link was used: the token is bound to the password it was sent for
        confirmed = confirm_password_reset_token(token)
    except TypeError:
        return jsonify({"success": False}), 401
    if confirmed is None:
        flash("Sorry, your token has expired or is invalid! We will need to resend your authentication email",
              'category_info')
        return render_template('auth/user/status_password.html',
                               uri={"path": url_for("auth.reset_request"), "name": "Resend ""authentication ""email"})
    user, password_hash = confirmed
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            # only if the password is still the one of the link, and whoever may have known the old password is
            # logged out everywhere
            if not user.reset_password(password_hash, form.confirm_password.data):
                flash("Sorry, your token has expired or is invalid! We will need to resend your authentication email",
                      'category_info')
                return render_template('auth/user/status_password.html', uri={
                    "path": url_for("auth.reset_request"), "name": "Resend ""authentication ""email"})
            current_app.extensions['sockio'].sm.forget_user(user.id)
            flash('Password reset Success. Please login by the user interface.', 'category_success')
            return render_template('auth/user/status_password.html')
        except IOError:
            flash('Password reset failed. Please try again later', 'category_danger')
    return render_template('auth/user/reset_password.html', form=form)


@AUTH_BP.route("/resend_confirmation", methods=['GET', 'POST'])
def resend_confirmation():
    """
    Sends a new email to confirm the email address of an unconfirmed account

    For a confirmation link that expired, and for the accounts created before the server sent emails. Like
    reset_request it answers the same for an unknown address, a confirmed account and a sent email.
    """
    if not current_app.config['MAIL_ENABLED']:
        logging.warning("To send emails, the value of `MAIL_ENABLED` in `conf.py` should be set to True.")
        return render_template('auth/errors/403.html'), 403
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(emailid=form.email.data).first()
        if user is not None and not user.confirmed:
            token = generate_confirmation_token(user.emailid, EMAIL_CONFIRMATION)
            confirm_url = public_url_for('auth.confirm_email', token=token)
            html = render_template('auth/user/activate.html', username=user.username, confirm_url=confirm_url)
            if not send_email(user.emailid, "MSColab Please confirm your email", html):
                flash('''We apologize, but it seems that there was an issue sending
                the confirmation email. Please try again later.''', 'category_info')
                return render_template('auth/user/resend_confirmation.html', form=form)
        flash('An email was sent if this address has an account that is not confirmed yet', 'category_success')
        return render_template('auth/user/status_password.html', title="Confirm your email address")
    return render_template('auth/user/resend_confirmation.html', form=form)


@AUTH_BP.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_app.config['MAIL_ENABLED']:
        form = ResetRequestForm()
        if form.validate_on_submit():
            # Check whether user exists or not based on the db
            user = User.query.filter_by(emailid=form.email.data).first()
            if user:
                username = user.username
                token = generate_password_reset_token(user)
                reset_password_url = public_url_for('auth.reset_password', token=token)
                html = render_template('auth/user/reset_confirmation.html',
                                       reset_password_url=reset_password_url, username=username)
                subject = "MSColab Password reset request"
                if send_email(form.email.data, subject, html):
                    flash('An email was sent if this user account exists', 'category_success')
                    return render_template('auth/user/status_password.html')
                flash('''We apologize, but it seems that there was an issue sending
                your request email. Please try again later.''', 'category_info')
            else:
                flash('An email was sent if this user account exists', 'category_success')
                return render_template('auth/user/status_password.html')
        return render_template('auth/user/reset_request.html', form=form)
    else:
        logging.warning("To send emails, the value of `MAIL_ENABLED` in `conf.py` should be set to True.")
        return render_template('auth/errors/403.html'), 403
