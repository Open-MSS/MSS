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
import json
import logging
import secrets
from functools import wraps

from flask import Blueprint, request, url_for, render_template, jsonify, flash, redirect, current_app
from flask_httpauth import HTTPBasicAuth
from flask.wrappers import Response
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.metadata import create_metadata_string

from mslib.mscolab.auth import check_login, register_user, generate_confirmation_token, create_or_update_idp_user, \
    get_idp_entity_id, confirm_token
from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.forms import ResetPasswordForm, ResetRequestForm
from mslib.mscolab.models import User
from mslib.utils.auth import send_email

AUTH_BP = Blueprint('auth', __name__, template_folder='templates')

auth_basic_auth = HTTPBasicAuth()


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get('enable_basic_http_authentication', False):
            return auth_basic_auth.login_required(f)(*args, **kwargs)
        return f(*args, **kwargs)

    return decorated


@AUTH_BP.route("/status")
@optional_auth
def hello():
    if request.authorization is not None:
        if current_app.config.get('enable_basic_http_authentication', False):
            auth_basic_auth.login_required()
            return json.dumps({
                'message': "Mscolab server",
                'use_saml2': current_app.config['USE_SAML2'],
                'direct_login': current_app.config['DIRECT_LOGIN']
            })
        return json.dumps({
            'message': "Mscolab server",
            'use_saml2': current_app.config['USE_SAML2'],
            'direct_login': current_app.config['DIRECT_LOGIN']
        })
    else:
        return json.dumps({
            'message': "Mscolab server",
            'use_saml2': current_app.config['USE_SAML2'],
            'direct_login': current_app.config['DIRECT_LOGIN']
        })


@AUTH_BP.route('/token', methods=["POST"])
@optional_auth
def get_auth_token():
    emailid = request.form['email']
    password = request.form['password']
    user = check_login(emailid, password)
    if user is not False:
        if current_app.config['MAIL_ENABLED']:
            if user.confirmed:
                token = user.generate_auth_token()
                return json.dumps({
                    'token': token,
                    'user': {'username': user.username, 'id': user.id, 'fullname': user.fullname}})
            else:
                return "False"
        else:
            token = user.generate_auth_token()
            return json.dumps({
                'token': token,
                'user': {'username': user.username, 'id': user.id, 'fullname': user.fullname}})
    else:
        logging.debug("Unauthorized user: %s", emailid)
        return "False"


@AUTH_BP.route('/test_authorized')
def authorized():
    token = request.args.get('token', request.form.get('token'))
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


@AUTH_BP.route("/register", methods=["POST"])
@optional_auth
def user_register_handler():
    email = request.form['email']
    password = request.form['password']
    username = request.form['username']
    fullname = request.form['fullname']
    result = register_user(email, password, username, fullname)
    status_code = 200
    try:
        if result["success"]:
            status_code = 201
            if current_app.config['MAIL_ENABLED']:
                status_code = 204
                token = generate_confirmation_token(email)
                confirm_url = url_for('auth.confirm_email', token=token, _external=True)
                html = render_template('auth/user/activate.html', username=username, confirm_url=confirm_url)
                subject = "MSColab Please confirm your email"
                send_email(email, subject, html)
    except TypeError:
        result, status_code = {"success": False}, 401
    return jsonify(result), status_code


def init_saml(state):
    """Runs once when blueprint is registered."""
    app = state.app

    if not app.config.get("USE_SAML2"):
        return

    setup_saml2_backend()
    register_saml_routes()


def register_saml_routes():
    """All SAML routes are registered here safely."""

    def create_acs_post_handler():
        """
        Create acs_post_handler function for the given idp_config.
        """

        def acs_post_handler(config, idp_identity_name):
            """
            Function to handle SAML authentication response.
            """
            try:
                outstanding_queries = {}
                binding = BINDING_HTTP_POST
                authn_response = config['idp_data']['saml2client'].parse_authn_request_response(
                    request.form["SAMLResponse"], binding, outstanding=outstanding_queries
                )

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
                        return render_template('auth/errors/403.html'), 403

                if email is not None and username is not None:
                    idp_user_db_state = create_or_update_idp_user(email,
                                                                  username, token, idp_identity_name)
                    if idp_user_db_state:
                        return render_template('auth/idp/idp_login_success.html', token=token), 200
                    return render_template('auth/errors/500.html'), 500
                return render_template('auth/errors/500.html'), 500
            except (NameError, AttributeError, KeyError):
                return render_template('auth/errors/403.html'), 403

        return acs_post_handler

    # Implementation for handling configured SAML assertion consumer endpoints
    for idp_config in setup_saml2_backend.CONFIGURED_IDPS:
        try:
            for assertion_consumer_endpoint in idp_config['idp_data']['assertion_consumer_endpoints']:
                # Dynamically add the route for the current endpoint
                AUTH_BP.add_url_rule(f'/{assertion_consumer_endpoint}/', assertion_consumer_endpoint,
                                     create_acs_post_handler(), methods=['POST'])
        except (NameError, AttributeError, KeyError) as ex:
            logging.warning("USE_SAML2 is %s, Failure is: %s", current_app.config['USE_SAML2'], ex)

    @AUTH_BP.route('/available_idps/', methods=['GET'])
    def available_idps():
        """
        This function checks if IDP (Identity Provider) is enabled in the mscolab_settings module.
        If IDP is enabled, it retrieves the configured IDPs from setup_saml2_backend.CONFIGURED_IDPS
        and renders the 'idp/available_idps.html' template with the list of configured IDPs.
        """
        configured_idps = setup_saml2_backend.CONFIGURED_IDPS
        return render_template('auth/idp/available_idps.html', configured_idps=configured_idps), 200

    @AUTH_BP.route("/idp_login/", methods=['POST'])
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
            return render_template('auth/errors/403.html'), 403

    @AUTH_BP.route('/idp_login_auth/', methods=['POST'])
    def idp_login_auth():
        """Handle the SAML authentication validation of client application."""
        try:
            data = request.get_json()
            token = data.get('token')
            email = confirm_token(token, expiration=1200)
            if email:
                user = check_login(email, token)
                if user:
                    from mslib.mscolab.server import getConfig
                    fm = getConfig()[3]
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

    @AUTH_BP.route("/metadata/<idp_identity_name>", methods=['GET'])
    def metadata(idp_identity_name):
        """Return the SAML metadata XML for the requested IDP"""
        for config in setup_saml2_backend.CONFIGURED_IDPS:
            if idp_identity_name == config['idp_identity_name']:
                sp_config = config['idp_data']['saml2client']
                metadata_string = create_metadata_string(
                    None, sp_config.config, 4, None, None, None, None, None
                ).decode("utf-8")
                return Response(metadata_string, mimetype="text/xml")
        return render_template('auth/errors/404.html'), 404


AUTH_BP.record_once(init_saml)


@AUTH_BP.route('/confirm/<token>')
def confirm_email(token):
    if current_app.config['MAIL_ENABLED']:
        try:
            email = confirm_token(token)
        except TypeError:
            return jsonify({"success": False}), 401
        if email is False:
            return jsonify({"success": False}), 401
        user = User.query.filter_by(emailid=email).first_or_404()
        if user.confirmed:
            return render_template('auth/user/confirmed.html', username=user.username)
        else:
            from mslib.mscolab.server import getConfig
            fm = getConfig()[3]
            fm.modify_user(user, attribute="confirmed_on", value=datetime.datetime.now(tz=datetime.timezone.utc))
            fm.modify_user(user, attribute="confirmed", value=True)
            return render_template('auth/user/confirmed.html', username=user.username)
    else:
        logging.warning("To send emails, the value of MAIL_ENABLED in conf.py should be set to True.")
        return render_template('auth/errors/403.html'), 403


@AUTH_BP.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = confirm_token(token, expiration=86400)
    except TypeError:
        return jsonify({"success": False}), 401
    if email is False:
        flash("Sorry, your token has expired or is invalid! We will need to resend your authentication email",
              'category_info')
        return render_template('auth/user/status_password.html',
                               uri={"path": "auth.reset_request", "name": "Resend ""authentication ""email"})
    user = User.query.filter_by(emailid=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        try:
            from mslib.mscolab.server import getConfig
            fm = getConfig()[3]
            user.hash_password(form.confirm_password.data)
            fm.modify_user(user, "confirmed", True)
            flash('Password reset Success. Please login by the user interface.', 'category_success')
            return render_template('auth/user/status_password.html')
        except IOError:
            flash('Password reset failed. Please try again later', 'category_danger')
    return render_template('auth/user/reset_password.html', form=form)


@AUTH_BP.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_app.config['MAIL_ENABLED']:
        form = ResetRequestForm()
        if form.validate_on_submit():
            # Check whether user exists or not based on the db
            user = User.query.filter_by(emailid=form.email.data).first()
            if user:
                try:
                    username = user.username
                    token = generate_confirmation_token(form.email.data)
                    reset_password_url = url_for('auth.reset_password', token=token, _external=True)
                    html = render_template('auth/user/reset_confirmation.html',
                                           reset_password_url=reset_password_url, username=username)
                    subject = "MSColab Password reset request"
                    send_email(form.email.data, subject, html)
                    flash('An email was sent if this user account exists', 'category_success')
                    return render_template('auth/user/status_password.html')
                except IOError:
                    flash('''We apologize, but it seems that there was an issue sending
                    your request email. Please try again later.''', 'category_info')
            else:
                flash('An email was sent if this user account exists', 'category_success')
                return render_template('auth/user/status_password.html')
        return render_template('auth/user/reset_request.html', form=form)
    else:
        logging.warning("To send emails, the value of `MAIL_ENABLED` in `conf.py` should be set to True.")
        return render_template('auth/errors/403.html'), 403
