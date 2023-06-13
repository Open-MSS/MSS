# -*- coding: utf-8 -*-
"""

    conf_sp_idp.sp.app.app.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Service provider for ensure SSO process with pysaml2

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
    :copyright: Copyright 2023- by the MSS team, see AUTHORS.
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

# Parts of the code

import random
import string
import yaml

from flask import Flask, redirect, request, render_template, url_for
from flask.wrappers import Response
from flask_login.utils import login_required, logout_user
from flask_login import LoginManager, UserMixin, login_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from saml2.config import SPConfig
from saml2.client import Saml2Client
from saml2.metadata import create_metadata_string
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST

from conf import sp_settings

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = sp_settings.SQLALCHEMY_DB_URI
app.config["SECRET_KEY"] = sp_settings.SECRET_KEY

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


class User(UserMixin, db.Model):
    """Class representing a user"""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), index=True, unique=True)

    def __repr__(self):
        return f'<User {format(self.email)}>'

    def get_id(self):
        """Get the user's ID"""
        return self.id



with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    """ since the user_id is just the primary key of our user table,
    use it in the query for the user """
    return User.query.get(int(user_id))


with open("../saml2_backend.yaml", encoding="utf-8") as fobj:
    sp_config = SPConfig().load(yaml.load(fobj, yaml.loader.SafeLoader)["config"]["sp_config"])

sp = Saml2Client(sp_config)


def rndstr(size=16, alphabet=""):
    """
    Returns a string of random ascii characters or digits
    :type size: int
    :type alphabet: str
    :param size: The length of the string
    :param alphabet: A string with characters.
    :return: string
    """
    rng = random.SystemRandom()
    if not alphabet:
        alphabet = string.ascii_letters[0:52] + string.digits
    return type(alphabet)().join(rng.choice(alphabet) for _ in range(size))


def get_idp_entity_id():
    """
    Finds the entity_id for the IDP
    :return: the entity_id of the idp or None
    """

    idps = sp.metadata.identity_providers()
    only_idp = idps[0]
    entity_id = only_idp

    return entity_id


@app.route("/")
def index():
    "Return the home page template"
    return render_template("index.html")


@app.route("/metadata/")
def metadata():
    """Return the SAML metadata XML."""
    metadata_string = create_metadata_string(
        None, sp.config, 4, None, None, None, None, None
    ).decode("utf-8")
    return Response(metadata_string, mimetype="text/xml")


@app.route("/login/")
def login():
    """Handle the login process for the user."""
    try:
        # pylint: disable=unused-variable
        acs_endp, response_binding = sp.config.getattr("endpoints", "sp")[
            "assertion_consumer_service"
        ][0]
        relay_state = rndstr()
        # pylint: disable=unused-variable
        entity_id = get_idp_entity_id()
        req_id, binding, http_args = sp.prepare_for_negotiated_authenticate(
            entityid=entity_id,
            response_binding=response_binding,
            relay_state=relay_state,
        )
        if binding == BINDING_HTTP_REDIRECT:
            headers = dict(http_args["headers"])
            return redirect(str(headers["Location"]), code=303)

        return Response(http_args["data"], headers=http_args["headers"])
    except AttributeError as error:
        print(error)
        return Response("An error occurred", status=500)

@app.route("/profile/", methods=["GET"])
@login_required
def profile():
    """Display the user's profile page."""
    return render_template("profile.html")

@app.route("/logout/", methods=["GET"])
def logout():
    """Logout the current user and redirect to the index page."""
    logout_user()
    return redirect(url_for("index"))

@app.route("/acs/post", methods=["POST"])
def acs_post():
    """Handle the SAML authentication response received via POST request."""
    outstanding_queries = {}
    binding = BINDING_HTTP_POST
    authn_response = sp.parse_authn_request_response(
        request.form["SAMLResponse"], binding, outstanding=outstanding_queries
    )
    email = authn_response.ava["email"][0]

    # Check if an user exists, or add one
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, remember=True)
    return redirect(url_for("profile"))


@app.route("/acs/redirect", methods=["GET"])
def acs_redirect():
    """Handle the SAML authentication response received via redirect."""
    outstanding_queries = {}
    binding = BINDING_HTTP_REDIRECT
    authn_response = sp.parse_authn_request_response(
        request.form["SAMLResponse"], binding, outstanding=outstanding_queries
    )
    return str(authn_response.ava)
