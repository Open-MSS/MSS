# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_saml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the SAML login: identities linked to accounts, one-time codes, and which responses are accepted.

    The responses come from an identity provider of pysaml2 in the test process, signed like the ones of a real one.

    This file is part of MSS.

    :copyright: Copyright 2026 Reimar Bauer
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
import base64
import datetime
import json
import re
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import mock
import pytest
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.client import Saml2Client
from saml2.config import IdPConfig, SPConfig
from saml2.metadata import create_metadata_string
from saml2.saml import NAMEID_FORMAT_PERSISTENT, NAMEID_FORMAT_TRANSIENT, NameID, AUTHN_PASSWORD
from saml2.server import Server

from mslib.mscolab import auth
from mslib.mscolab.conf import setup_saml2_backend
from mslib.mscolab.models import db, IdpIdentity, SamlLogin, User
from mslib.mscolab.seed import add_user, get_user
from mslib.mscolab.server import create_server_app
from tests.fixtures import _isolated_mscolab_settings

XMLSEC1 = shutil.which("xmlsec1")
requires_xmlsec1 = pytest.mark.skipif(XMLSEC1 is None, reason="SAML signatures need xmlsec1")

IDP_NAME = "test_idp"
IDP_ENTITY_ID = "https://idp.example.org/idp.xml"
SP_ENTITY_ID = "https://mscolab.example.org/sp.xml"
ACS_PATH = f"/{IDP_NAME}/acs/post"
ACS_URL = f"http://localhost{ACS_PATH}"
ALICE = {"eduPersonPrincipalName": ["alice@idp.example.org"], "email": ["alice@example.org"], "givenName": ["Alice"]}
LOCAL_USER = ("alice@example.org", "alice", "alice-password", "Alice Local")


def _key_and_cert(directory, name):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, name)])
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=1)).sign(key, hashes.SHA256()))
    key_file, cert_file = directory / f"{name}.key", directory / f"{name}.crt"
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                           serialization.NoEncryption()))
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return str(key_file), str(cert_file)


def _sp_config(key_file, cert_file, idp_metadata=None):
    config = {
        "entityid": SP_ENTITY_ID,
        "key_file": key_file,
        "cert_file": cert_file,
        "xmlsec_binary": XMLSEC1,
        "service": {"sp": {
            "endpoints": {"assertion_consumer_service": [(ACS_URL, BINDING_HTTP_POST)]},
            "authn_requests_signed": True,
            "want_response_signed": True,
            "want_assertion_signed": True,
            "allow_unknown_attributes": True,
            # as in the configurations before 12.0.0: the server must refuse unsolicited responses anyway
            "allow_unsolicited": True,
        }},
    }
    if idp_metadata is not None:
        config["metadata"] = {"inline": [idp_metadata]}
    return SPConfig().load(config)


def _idp_config(key_file, cert_file, sp_metadata=None):
    config = {
        "entityid": IDP_ENTITY_ID,
        "key_file": key_file,
        "cert_file": cert_file,
        "xmlsec_binary": XMLSEC1,
        "service": {"idp": {
            "endpoints": {"single_sign_on_service": [("https://idp.example.org/sso", BINDING_HTTP_REDIRECT)]},
            "policy": {"default": {"attribute_restrictions": None, "lifetime": {"minutes": 15}}},
            "name_id_format": [NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_PERSISTENT],
        }},
    }
    if sp_metadata is not None:
        config["metadata"] = {"inline": [sp_metadata]}
    return IdPConfig().load(config)


def _metadata(config):
    return create_metadata_string(None, config, 4, None, None, None, None, None).decode("utf-8")


class TestIdp:
    """An identity provider that answers the AuthnRequests of the server with signed responses"""
    __test__ = False

    def __init__(self, directory):
        sp_key, sp_cert = _key_and_cert(directory, "sp")
        idp_key, idp_cert = _key_and_cert(directory, "idp")
        sp_metadata = _metadata(_sp_config(sp_key, sp_cert))
        idp_metadata = _metadata(_idp_config(idp_key, idp_cert))
        self.server = Server(config=_idp_config(idp_key, idp_cert, sp_metadata))
        self.idp_config = {
            'idp_identity_name': IDP_NAME,
            'idp_data': {
                'idp_name': 'Test Identity Provider',
                'saml2client': Saml2Client(_sp_config(sp_key, sp_cert, idp_metadata)),
                'assertion_consumer_endpoints': [ACS_PATH],
                'user_id_attribute': 'eduPersonPrincipalName',
            },
        }

    def response(self, in_response_to, identity=ALICE, name_id=None):
        """A signed SAMLResponse to the request in_response_to, as the browser posts it to the server"""
        if name_id is None:
            name_id = NameID(format=NAMEID_FORMAT_TRANSIENT, text="transient-id")
        response = self.server.create_authn_response(
            identity, in_response_to, ACS_URL, SP_ENTITY_ID, name_id=name_id,
            authn={"class_ref": AUTHN_PASSWORD, "authn_auth": IDP_ENTITY_ID},
            sign_response=True, sign_assertion=True)
        return base64.b64encode(str(response).encode("utf-8")).decode("ascii")


@pytest.fixture(scope="module")
def test_idp(tmp_path_factory):
    return TestIdp(tmp_path_factory.mktemp("saml"))


@pytest.fixture
def saml_app(tmp_path, test_idp):
    settings = _isolated_mscolab_settings(tmp_path)
    settings.USE_SAML2 = True
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch.object(setup_saml2_backend, "CONFIGURED_IDPS", [test_idp.idp_config]):
        app = create_server_app(settings)
        with app.app_context():
            yield app
            db.session.remove()
            db.engine.dispose()


def _start_login(client):
    """Starts a SAML login like the page of available_idps, returns the id of the AuthnRequest"""
    response = client.post("/idp_login/", data={"selectedIdentityProvider": IDP_NAME})
    assert response.status_code == 303
    query = parse_qs(urlparse(response.headers["Location"]).query)
    assert "Signature" in query
    return SamlLogin.query.filter_by(idp_identity_name=IDP_NAME, code_hash=None).order_by(SamlLogin.id.desc()) \
        .first().request_id


def _post_response(client, saml_response):
    return client.post(ACS_PATH, data={"SAMLResponse": saml_response})


def _code(response):
    assert response.status_code == 200, response.text
    return re.search(r'<code id="idpCode">([^<]+)</code>', response.text).group(1)


def _saml_login(client, test_idp, **kwargs):
    """A complete SAML login in the browser, returns the code that it shows"""
    return _code(_post_response(client, test_idp.response(_start_login(client), **kwargs)))


def _exchange(client, code):
    return client.post("/idp_login_auth/", json={"token": code})


def _authorized(client, token):
    return client.get("/test_authorized", query_string={"token": token}).text == "True"


def test_saml_routes_need_use_saml2(mscolab_app):
    client = mscolab_app.test_client()
    assert client.get("/available_idps/").status_code == 404
    assert client.post("/idp_login/", data={"selectedIdentityProvider": IDP_NAME}).status_code == 404
    assert _exchange(client, "code").status_code == 404
    assert client.post("/idp_link", data={"token": "token", "code": "code"}).status_code == 404


@requires_xmlsec1
def test_server_with_saml_starts_and_offers_the_idps(saml_app):
    # the assertion consumer services are added to the app: a blueprint can't change after its registration
    assert ACS_PATH in {rule.rule for rule in saml_app.url_map.iter_rules()}
    response = saml_app.test_client().get("/available_idps/")
    assert response.status_code == 200
    assert f'value="{IDP_NAME}"' in response.text
    assert saml_app.test_client().get(f"/metadata/{IDP_NAME}").status_code == 200
    assert saml_app.test_client().get("/metadata/unknown").status_code == 404


@requires_xmlsec1
def test_new_identity_gets_an_account(saml_app, test_idp):
    client = saml_app.test_client()
    response = _exchange(client, _saml_login(client, test_idp))
    assert response.status_code == 200
    data = json.loads(response.text)
    assert data["success"] is True
    assert data["user"]["emailid"] == "alice@example.org" and data["user"]["username"] == "Alice"
    assert "fullname" in data["user"]
    assert _authorized(client, data["token"])
    user = get_user("alice@example.org")
    assert user.authentication_backend == IDP_NAME
    assert [(i.issuer, i.subject) for i in user.idp_identities] == [(IDP_ENTITY_ID, "alice@idp.example.org")]
    # the next login is the same account, also with another email and transient NameID
    identity = dict(ALICE, email=["alice@new.example.org"])
    data = json.loads(_exchange(client, _saml_login(client, test_idp, identity=identity)).text)
    assert data["user"]["id"] == user.id
    assert User.query.count() == 1


@requires_xmlsec1
def test_saml_login_needs_a_persistent_identifier(saml_app, test_idp):
    client = saml_app.test_client()
    identity = {key: value for key, value in ALICE.items() if key != "eduPersonPrincipalName"}
    assert _post_response(client, test_idp.response(_start_login(client), identity=identity)).status_code == 403
    # without user_id_attribute the NameID, if it is persistent
    del test_idp.idp_config['idp_data']['user_id_attribute']
    try:
        assert _post_response(client, test_idp.response(_start_login(client), identity=identity)).status_code == 403
        name_id = NameID(format=NAMEID_FORMAT_PERSISTENT, text="persistent-alice")
        code = _saml_login(client, test_idp, identity=identity, name_id=name_id)
    finally:
        test_idp.idp_config['idp_data']['user_id_attribute'] = 'eduPersonPrincipalName'
    assert _exchange(client, code).status_code == 200
    assert [i.subject for i in get_user("alice@example.org").idp_identities] == ["persistent-alice"]


@requires_xmlsec1
def test_saml_login_does_not_take_over_an_account_by_email(saml_app, test_idp):
    assert add_user(*LOCAL_USER)
    client = saml_app.test_client()
    password_hash = get_user(LOCAL_USER[0]).password
    code = _saml_login(client, test_idp)
    response = _exchange(client, code)
    assert response.status_code == 409
    assert json.loads(response.text) == {"success": False, "link_required": True, "emailid": LOCAL_USER[0]}
    user = get_user(LOCAL_USER[0])
    assert user.idp_identities == [] and user.authentication_backend == "local" and user.password == password_hash

    # the owner logs in with the password and links the identity
    token = json.loads(client.post("/token", data={"email": LOCAL_USER[0], "password": LOCAL_USER[2]}).text)["token"]
    assert client.post("/idp_link", data={"token": "invalid", "code": code}).text == "False"
    assert client.post("/idp_link", data={"token": token, "code": "invalid"}).get_json() == {"success": False}
    assert client.post("/idp_link", data={"token": token, "code": code}).get_json() == {"success": True}
    # the code worked once
    assert client.post("/idp_link", data={"token": token, "code": code}).get_json() == {"success": False}
    assert _exchange(client, code).status_code == 401

    data = json.loads(_exchange(client, _saml_login(client, test_idp)).text)
    assert data["user"]["id"] == user.id
    # a SAML login never changes the password
    assert get_user(LOCAL_USER[0]).password == password_hash
    assert client.post("/token", data={"email": LOCAL_USER[0], "password": LOCAL_USER[2]}).text != "False"


@requires_xmlsec1
def test_only_the_account_of_the_email_can_link(saml_app, test_idp):
    assert add_user(*LOCAL_USER)
    assert add_user("mallory@example.org", "mallory", "mallory-password", "Mallory")
    client = saml_app.test_client()
    code = _saml_login(client, test_idp)
    assert _exchange(client, code).status_code == 409
    token = json.loads(client.post("/token", data={"email": "mallory@example.org",
                                                   "password": "mallory-password"}).text)["token"]
    assert client.post("/idp_link", data={"token": token, "code": code}).get_json() == {"success": False}
    assert IdpIdentity.query.count() == 0


def _saml_login_of(identity, issuer=IDP_ENTITY_ID, idp_identity_name=IDP_NAME, request_id="id-1"):
    """The code of a SAML login of identity, without the IdP"""
    auth.remember_saml_request(request_id, idp_identity_name)
    return auth.finish_saml_login(request_id, idp_identity_name, issuer, identity["eduPersonPrincipalName"][0],
                                  identity["email"][0], identity["givenName"][0])


@pytest.fixture
def request_idp(monkeypatch):
    """The entity id MSColab sends the login requests of IDP_NAME to, without a configured IdP"""
    monkeypatch.setattr(auth, "get_idp_entity_id", lambda name: IDP_ENTITY_ID if name == IDP_NAME else None)


def test_account_of_an_older_version_is_linked_on_its_first_login(mscolab_app, request_idp):
    with mscolab_app.app_context():
        # logged in by this IdP before, by email alone
        assert add_user(*LOCAL_USER)
        user = get_user(LOCAL_USER[0])
        user.authentication_backend = IDP_NAME
        db.session.commit()
        # another IdP of the same metadata, e.g. of a federation, can assert the email too: the owner links it
        code = _saml_login_of(ALICE, issuer="https://evil.example.org/idp.xml", request_id="id-0")
        assert auth.idp_login(code) == (None, LOCAL_USER[0])
        assert user.idp_identities == []
        assert auth.idp_login(_saml_login_of(ALICE, request_id="id-1")) == (user, None)
        assert [i.subject for i in user.idp_identities] == ["alice@idp.example.org"]
        # from then on only this identity: another one with the same email must be linked by the owner
        other = dict(ALICE, eduPersonPrincipalName=["someone@idp.example.org"])
        assert auth.idp_login(_saml_login_of(other, request_id="id-2")) == (None, LOCAL_USER[0])


@pytest.mark.parametrize("backend", ["local", "other_idp"])
def test_account_of_another_backend_is_not_linked_on_login(mscolab_app, backend):
    with mscolab_app.app_context():
        assert add_user(*LOCAL_USER)
        user = get_user(LOCAL_USER[0])
        user.authentication_backend = backend
        db.session.commit()
        code = _saml_login_of(ALICE)
        assert auth.idp_login(code) == (None, LOCAL_USER[0])
        assert user.idp_identities == []
        # the code stays valid for the link
        assert auth.link_idp_identity(user, code) is True
        assert auth.idp_login(_saml_login_of(ALICE, request_id="id-2")) == (user, None)


def test_identities_of_different_issuers_are_different(mscolab_app):
    with mscolab_app.app_context():
        user, _ = auth.idp_login(_saml_login_of(ALICE, request_id="id-1"))
        # another IdP of the same configured metadata, e.g. of a federation, asserts the same subject
        code = _saml_login_of(ALICE, issuer="https://evil.example.org/idp.xml", request_id="id-2")
        assert auth.idp_login(code) == (None, user.emailid)


def test_code_works_once_and_expires(mscolab_app):
    with mscolab_app.app_context():
        code = _saml_login_of(ALICE, request_id="id-1")
        user, _ = auth.idp_login(code)
        assert user is not None
        assert auth.idp_login(code) == (None, None)
        code = _saml_login_of(ALICE, request_id="id-2")
        SamlLogin.query.update({SamlLogin.created_on: datetime.datetime.now(tz=datetime.timezone.utc)
                                - datetime.timedelta(seconds=auth.IDP_LOGIN_CODE_LIFETIME + 1)})
        db.session.commit()
        assert auth.idp_login(code) == (None, None)
        assert auth.idp_login(None) == (None, None) and auth.idp_login("") == (None, None)


def test_saml_request_is_answered_once_and_in_time(mscolab_app):
    with mscolab_app.app_context():
        auth.remember_saml_request("id-1", IDP_NAME)
        outstanding = auth.OutstandingSamlRequests(IDP_NAME)
        assert outstanding and "id-1" in outstanding and "id-2" not in outstanding and None not in outstanding
        assert "id-1" not in auth.OutstandingSamlRequests("other_idp")
        assert auth.finish_saml_login("id-1", "other_idp", IDP_ENTITY_ID, "subject", None, None) is None
        assert auth.finish_saml_login(None, IDP_NAME, IDP_ENTITY_ID, "subject", None, None) is None
        assert auth.finish_saml_login("id-1", IDP_NAME, IDP_ENTITY_ID, "subject", None, None) is not None
        # one instance checks one response, it looks up each request once
        assert "id-1" in outstanding
        assert "id-1" not in auth.OutstandingSamlRequests(IDP_NAME)
        assert auth.finish_saml_login("id-1", IDP_NAME, IDP_ENTITY_ID, "subject", None, None) is None
        auth.remember_saml_request("id-2", IDP_NAME)
        SamlLogin.query.filter_by(request_id="id-2").update({SamlLogin.created_on: datetime.datetime.now(
            tz=datetime.timezone.utc) - datetime.timedelta(seconds=auth.SAML_REQUEST_LIFETIME + 1)})
        db.session.commit()
        assert "id-2" not in auth.OutstandingSamlRequests(IDP_NAME)
        assert auth.finish_saml_login("id-2", IDP_NAME, IDP_ENTITY_ID, "subject", None, None) is None


def test_old_saml_logins_are_removed(mscolab_app):
    with mscolab_app.app_context():
        auth.remember_saml_request("id-1", IDP_NAME)
        SamlLogin.query.update({SamlLogin.created_on: datetime.datetime.now(tz=datetime.timezone.utc)
                                - datetime.timedelta(days=1)})
        db.session.commit()
        auth.remember_saml_request("id-2", IDP_NAME)
        assert [login.request_id for login in SamlLogin.query.all()] == ["id-2"]


def test_saml_login_without_email_gets_no_account(mscolab_app):
    with mscolab_app.app_context():
        auth.remember_saml_request("id-1", IDP_NAME)
        code = auth.finish_saml_login("id-1", IDP_NAME, IDP_ENTITY_ID, "subject", None, "Alice")
        assert auth.idp_login(code) == (None, None)
        assert User.query.count() == 0


def test_deleting_a_user_deletes_its_identities(mscolab_app, mscolab_managers):
    _, _, fm = mscolab_managers
    with mscolab_app.app_context():
        user, _ = auth.idp_login(_saml_login_of(ALICE))
        assert IdpIdentity.query.count() == 1
        assert fm.modify_user(user, action="delete")
        assert IdpIdentity.query.count() == 0


@requires_xmlsec1
def test_response_is_accepted_once(saml_app, test_idp):
    client = saml_app.test_client()
    saml_response = test_idp.response(_start_login(client))
    assert _post_response(client, saml_response).status_code == 200
    assert _post_response(client, saml_response).status_code == 403


@requires_xmlsec1
def test_unsolicited_responses_are_refused(saml_app, test_idp):
    client = saml_app.test_client()
    _start_login(client)
    # to a request this server didn't send, and to none, although the SP configuration allows unsolicited ones
    assert _post_response(client, test_idp.response("id-unknown")).status_code == 403
    assert _post_response(client, test_idp.response(None)).status_code == 403
    assert SamlLogin.query.filter(SamlLogin.code_hash.isnot(None)).count() == 0


@requires_xmlsec1
def test_late_response_is_refused(saml_app, test_idp):
    client = saml_app.test_client()
    request_id = _start_login(client)
    SamlLogin.query.update({SamlLogin.created_on: datetime.datetime.now(tz=datetime.timezone.utc)
                            - datetime.timedelta(seconds=auth.SAML_REQUEST_LIFETIME + 1)})
    db.session.commit()
    assert _post_response(client, test_idp.response(request_id)).status_code == 403


@requires_xmlsec1
def test_changed_response_is_refused(saml_app, test_idp):
    client = saml_app.test_client()
    saml_response = base64.b64decode(test_idp.response(_start_login(client))).decode("utf-8")
    forged = saml_response.replace("alice@idp.example.org", "bob@idp.example.org")
    assert forged != saml_response
    assert _post_response(client, base64.b64encode(forged.encode("utf-8")).decode("ascii")).status_code == 403
    assert _post_response(client, "not a SAML response").status_code == 403
    assert IdpIdentity.query.count() == 0


def test_identity_is_the_one_of_the_signed_assertion():
    # pysaml2 checks the issuer of the response around the assertion only if the response is signed
    assertion = mock.Mock(issuer=mock.Mock(text=IDP_ENTITY_ID))
    authn_response = mock.Mock(assertion=assertion, name_id=None)
    authn_response.issuer.return_value = "https://evil.example.org/idp.xml"
    idp_data = {"user_id_attribute": "eduPersonPrincipalName"}
    attributes = {"eduPersonPrincipalName": ["alice@idp.example.org"]}
    assert auth.saml_identity(authn_response, idp_data, attributes) == (IDP_ENTITY_ID, "alice@idp.example.org")
    assertion.issuer = None
    assert auth.saml_identity(authn_response, idp_data, attributes) is None


def _basic_auth(password="testvaluepassword"):
    credentials = base64.b64encode(f"user:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {credentials}"}


def test_code_exchange_needs_the_basic_auth_of_the_server(mscolab_app):
    mscolab_app.config.update(USE_SAML2=True, ENABLE_BASIC_HTTP_AUTHENTICATION=True)
    client = mscolab_app.test_client()
    with mscolab_app.app_context():
        code = _saml_login_of(ALICE)
    assert _exchange(client, code).status_code == 401
    assert client.post("/idp_login_auth/", json={"token": code}, headers=_basic_auth("wrong")).status_code == 401
    response = client.post("/idp_login_auth/", json={"token": code}, headers=_basic_auth())
    assert response.status_code == 200
    token = json.loads(response.text)["token"]
    assert client.post("/idp_link", data={"token": token, "code": code}).status_code == 401
    assert client.post("/idp_link", data={"token": token, "code": code},
                       headers=_basic_auth()).get_json() == {"success": False}


def test_unconfirmed_account_does_not_log_in_by_saml(mscolab_app, request_idp):
    mscolab_app.config.update(USE_SAML2=True, MAIL_ENABLED=True)
    client = mscolab_app.test_client()
    with mscolab_app.app_context():
        # an account of an older version that logged in by this IdP, with email confirmation like /token
        assert add_user(*LOCAL_USER)
        user = get_user(LOCAL_USER[0])
        user.authentication_backend = IDP_NAME
        user.confirmed = False
        db.session.commit()
        code = _saml_login_of(ALICE)
    response = _exchange(client, code)
    # refused before the code is used: nothing is linked yet, the user learns why
    assert response.status_code == 403 and "token" not in json.loads(response.text)
    assert "isn't confirmed" in json.loads(response.text)["message"]
    with mscolab_app.app_context():
        assert get_user(LOCAL_USER[0]).idp_identities == []
        user = get_user(LOCAL_USER[0])
        user.confirmed = True
        db.session.commit()
    # confirmed, the same code logs in
    assert _exchange(client, code).status_code == 200


def test_email_of_an_account_matches_in_any_case(mscolab_app):
    with mscolab_app.app_context():
        assert add_user("Alice@Example.org", *LOCAL_USER[1:])
        user = get_user("Alice@Example.org")
        code = _saml_login_of(ALICE)
        assert auth.idp_login(code) == (None, "Alice@Example.org")
        assert auth.link_idp_identity(user, code) is True
        assert auth.idp_login(_saml_login_of(ALICE, request_id="id-2")) == (user, None)
        assert User.query.count() == 1


def test_failed_link_keeps_the_code(mscolab_app):
    with mscolab_app.app_context():
        assert add_user(*LOCAL_USER)
        user = get_user(LOCAL_USER[0])
        # two logins of the same identity, both refused until it is linked
        first, second = _saml_login_of(ALICE, request_id="id-1"), _saml_login_of(ALICE, request_id="id-2")
        assert auth.idp_login(first) == (None, LOCAL_USER[0]) and auth.idp_login(second) == (None, LOCAL_USER[0])
        assert auth.link_idp_identity(user, first) is True
        # linked meanwhile: the second link fails, its code still logs in
        assert auth.link_idp_identity(user, second) is False
        assert auth.idp_login(second) == (user, None)
        assert auth.idp_login(second) == (None, None)


def test_account_of_an_older_version_gets_only_one_identity_on_login(mscolab_app, request_idp):
    with mscolab_app.app_context():
        assert add_user(*LOCAL_USER)
        user = get_user(LOCAL_USER[0])
        user.authentication_backend = IDP_NAME
        db.session.commit()
        first = auth._saml_login_of_code(_saml_login_of(ALICE, request_id="id-1"))
        other = dict(ALICE, eduPersonPrincipalName=["someone@idp.example.org"])
        second_code = _saml_login_of(other, request_id="id-2")
        second = auth._saml_login_of_code(second_code)
        # both found the account without an identity, the first one links
        assert auth._use_saml_login(first, user, link=True, first_identity=True) is True
        assert auth._use_saml_login(second, user, link=True, first_identity=True) is False
        assert [i.subject for i in user.idp_identities] == ["alice@idp.example.org"]
        # the code of the second login is kept, for the owner to link it
        assert auth.link_idp_identity(user, second_code) is True


def test_open_saml_logins_are_capped(mscolab_app, monkeypatch):
    monkeypatch.setattr(auth, "MAX_SAML_LOGINS", 2)
    with mscolab_app.app_context():
        assert auth.remember_saml_request("id-1", IDP_NAME) is True
        assert auth.finish_saml_login("id-1", IDP_NAME, IDP_ENTITY_ID, "subject", None, None) is not None
        assert auth.remember_saml_request("id-2", IDP_NAME) is True
        # a code that wasn't exchanged yet counts too
        assert auth.remember_saml_request("id-3", IDP_NAME) is False
        assert SamlLogin.query.count() == 2
        # an expired request makes room
        SamlLogin.query.filter_by(request_id="id-2").update({SamlLogin.created_on: datetime.datetime.now(
            tz=datetime.timezone.utc) - datetime.timedelta(seconds=auth.SAML_REQUEST_LIFETIME + 1)})
        db.session.commit()
        assert auth.remember_saml_request("id-3", IDP_NAME) is True
        assert sorted(login.request_id for login in SamlLogin.query.all()) == ["id-1", "id-3"]


@requires_xmlsec1
def test_too_many_open_saml_logins_answer_503(saml_app, monkeypatch):
    monkeypatch.setattr(auth, "MAX_SAML_LOGINS", 0)
    response = saml_app.test_client().post("/idp_login/", data={"selectedIdentityProvider": IDP_NAME})
    assert response.status_code == 503
    assert SamlLogin.query.count() == 0


@pytest.mark.parametrize("emailid, username, message", [
    (None, "Alice", "no valid email"),
    ("not an email", "Alice", "no valid email"),
    ("alice@" + "a" * 250 + ".org", "Alice", "no valid email"),
    # the start of the email is taken too
    ("taken@example.org", "Alice@Example", "are taken or can't be used"),
    ("taken@example.org", "A" * 256, "are taken or can't be used"),
    ("taken@example.org", "taken", "are taken or can't be used"),
    ("taken@example.org", None, "are taken or can't be used"),
], ids=["no-email", "invalid-email", "long-email", "username-with-at", "long-username", "taken-username",
        "taken-email-start"])
def test_saml_login_with_unusable_data_is_refused(mscolab_app, emailid, username, message):
    with mscolab_app.app_context():
        assert add_user("bob@example.org", "taken", "bob-password", "Bob")
        with pytest.raises(auth.SamlLoginRefused, match=message):
            auth.check_saml_login(IDP_ENTITY_ID, "alice@idp.example.org", emailid, username)


def test_saml_login_data_is_checked_only_for_a_new_account(mscolab_app):
    with mscolab_app.app_context():
        assert auth.check_saml_login(IDP_ENTITY_ID, "subject", "alice@example.org", None) == (
            "alice@example.org", "alice")
        assert add_user("Alice@example.org", "taken", "alice-password", "Alice")
        # the account of the email is linked, not created
        assert auth.check_saml_login(IDP_ENTITY_ID, "subject", "alice@example.org", "taken") == (
            "alice@example.org", None)
        assert auth.idp_login(_saml_login_of(dict(ALICE, email=["bob@example.org"], givenName=["Bob"])))[0] is not None
        # a linked identity logs in whatever the IdP sends
        assert auth.check_saml_login(IDP_ENTITY_ID, "alice@idp.example.org", None, "x@y") == (None, None)


@pytest.mark.parametrize("username, expected", [
    ("Alice", "Alice"), ("Max", "alice"), ("Alice@Example", "alice"), ("A" * 256, "alice"), (None, "alice"),
], ids=["given-name", "given-name-taken", "given-name-with-at", "given-name-too-long", "no-given-name"])
def test_new_account_falls_back_to_the_start_of_the_email(mscolab_app, username, expected):
    # common first names are taken soon
    with mscolab_app.app_context():
        assert add_user("max@example.org", "Max", "max-password", "Max")
        assert auth.check_saml_login(IDP_ENTITY_ID, "subject", "alice@example.org", username) == (
            "alice@example.org", expected)


def test_usernames_taken_after_the_response_are_refused(mscolab_app):
    with mscolab_app.app_context():
        code = _saml_login_of(ALICE)
        assert add_user("bob@example.org", "Alice", "bob-password", "Bob")
        assert add_user("carol@example.org", "alice", "carol-password", "Carol")
        assert auth.idp_login(code) == (None, None)
        assert User.query.count() == 2


@requires_xmlsec1
def test_saml_login_with_taken_usernames_shows_why(saml_app, test_idp):
    assert add_user("bob@example.org", "Alice", "bob-password", "Bob")
    assert add_user("carol@example.org", "alice", "carol-password", "Carol")
    client = saml_app.test_client()
    response = _post_response(client, test_idp.response(_start_login(client)))
    assert response.status_code == 403
    assert "The usernames &#39;Alice&#39; and &#39;alice&#39; that your identity provider sent are taken" \
        in response.text
    assert SamlLogin.query.filter(SamlLogin.code_hash.isnot(None)).count() == 0


def _assertion_response(signed_assertion, signed_response, response_issuer):
    assertion = mock.Mock(issuer=mock.Mock(text=IDP_ENTITY_ID), signature="signed" if signed_assertion else None)
    authn_response = mock.Mock(assertion=assertion, name_id=None,
                               response=mock.Mock(signature="signed" if signed_response else None))
    authn_response.issuer.return_value = response_issuer
    return authn_response


@pytest.mark.parametrize("signed_assertion, signed_response, response_issuer, accepted", [
    (True, False, None, True),
    (False, True, IDP_ENTITY_ID, True),
    # an IdP of the same metadata signs the response around an assertion that claims another IdP
    (False, True, "https://evil.example.org/idp.xml", False),
    (False, False, IDP_ENTITY_ID, False),
], ids=["signed-assertion", "signed-response-same-issuer", "signed-response-other-issuer", "nothing-signed"])
def test_issuer_of_an_unsigned_assertion_needs_the_signed_response(signed_assertion, signed_response, response_issuer,
                                                                   accepted):
    idp_data = {"user_id_attribute": "eduPersonPrincipalName"}
    attributes = {"eduPersonPrincipalName": ["alice@idp.example.org"]}
    identity = auth.saml_identity(_assertion_response(signed_assertion, signed_response, response_issuer), idp_data,
                                  attributes)
    assert identity == ((IDP_ENTITY_ID, "alice@idp.example.org") if accepted else None)


def test_identity_refusals_are_logged_with_their_reason():
    response = _assertion_response(True, False, None)
    with mock.patch("mslib.mscolab.auth.logging.warning") as warning:
        assert auth.saml_identity(response, {"user_id_attribute": "id"}, {"id": ["x" * 256]}) is None
    assert "longer than 255" in warning.call_args.args[0]
    with mock.patch("mslib.mscolab.auth.logging.warning") as warning:
        assert auth.saml_identity(response, {"user_id_attribute": "id"}, {}) is None
    assert "persistent identifier" in warning.call_args.args[0]


def test_email_in_several_cases_is_refused(mscolab_app):
    with mscolab_app.app_context():
        assert add_user("Bob@example.org", "bob1", "bob-password", "Bob")
        assert add_user("bob@Example.org", "bob2", "bob-password", "Bob")
        with pytest.raises(auth.SamlLoginRefused, match="different upper and lower case"):
            auth.check_saml_login(IDP_ENTITY_ID, "subject", "BOB@example.org", "Bob")
        # an exact match is not ambiguous
        assert auth.check_saml_login(IDP_ENTITY_ID, "subject", "Bob@example.org", "Bob") == ("Bob@example.org", None)


@pytest.mark.parametrize("body", ['["x"]', '"code"', '42', 'null'])
def test_code_exchange_with_a_body_that_is_no_object(mscolab_app, body):
    mscolab_app.config.update(USE_SAML2=True)
    response = mscolab_app.test_client().post("/idp_login_auth/", data=body, content_type="application/json")
    assert response.status_code == 401


def test_starting_a_saml_login_needs_the_basic_auth_of_the_server(mscolab_app):
    # anyone could fill the open SAML logins otherwise
    mscolab_app.config.update(USE_SAML2=True, ENABLE_BASIC_HTTP_AUTHENTICATION=True)
    client = mscolab_app.test_client()
    assert client.get("/available_idps/").status_code == 401
    assert client.post("/idp_login/", data={"selectedIdentityProvider": IDP_NAME}).status_code == 401
    assert client.post("/idp_login/", data={"selectedIdentityProvider": "unknown"},
                       headers=_basic_auth()).status_code == 404


def test_password_reset_unlinks_the_saml_identities(mscolab_app, request_idp):
    # an IdP that lets its users choose their email: someone created the account with the address of another person,
    # who takes it over by a password reset
    with mscolab_app.app_context():
        user, _ = auth.idp_login(_saml_login_of(ALICE, request_id="id-1"))
        assert len(user.idp_identities) == 1
        assert user.reset_password(user.password, "the-owners-password")
        assert get_user(ALICE["email"][0]).idp_identities == []
        assert get_user(ALICE["email"][0]).authentication_backend == "local"
        # the identity must be linked again, with the new password, also by the IdP that created the account
        assert auth.idp_login(_saml_login_of(ALICE, request_id="id-2")) == (None, ALICE["email"][0])


def _app_with_idp(tmp_path, idp_config):
    settings = _isolated_mscolab_settings(tmp_path)
    settings.USE_SAML2 = True
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
    with mock.patch.object(setup_saml2_backend, "CONFIGURED_IDPS", [idp_config]):
        return create_server_app(settings)


def _mock_idp(path, user_id_attribute="eduPersonPrincipalName", name_id_format=NAMEID_FORMAT_TRANSIENT):
    client = mock.Mock()
    client.config.getattr.return_value = name_id_format
    idp_data = {'assertion_consumer_endpoints': [path], 'saml2client': client}
    if user_id_attribute:
        idp_data['user_id_attribute'] = user_id_attribute
    return {'idp_identity_name': 'mocked_idp', 'idp_data': idp_data}


@pytest.mark.parametrize("path", ["mocked_idp/acs/post/", "mocked_idp/acs/post"], ids=["trailing-slash", "no-slash"])
def test_assertion_consumer_service_as_configured(tmp_path, path):
    # the metadata tells the IdP the configured URL, with its trailing slash
    app = _app_with_idp(tmp_path, _mock_idp(path))
    adapter = app.url_map.bind("localhost")
    for url in ("/mocked_idp/acs/post/", "/mocked_idp/acs/post"):
        assert adapter.match(url, method="POST")[0] == "saml_acs_mocked_idp_0"


def test_idp_without_identifier_warns_at_the_start(tmp_path):
    with mock.patch("mslib.mscolab.blueprints.auth.logging.warning") as warning:
        _app_with_idp(tmp_path, _mock_idp("mocked_idp/acs/post", user_id_attribute=None))
    assert any("every SAML login by it is refused" in call.args[0] for call in warning.call_args_list)
    with mock.patch("mslib.mscolab.blueprints.auth.logging.warning") as warning:
        _app_with_idp(tmp_path, _mock_idp("mocked_idp/acs/post", user_id_attribute=None,
                                          name_id_format=[NAMEID_FORMAT_PERSISTENT]))
    assert not any("every SAML login by it is refused" in call.args[0] for call in warning.call_args_list)


@pytest.mark.parametrize("username", ["   ", " Alice "], ids=["blank", "padded"])
def test_given_name_is_stripped(mscolab_app, username):
    with mscolab_app.app_context():
        expected = username.strip() or "alice"
        assert auth.check_saml_login(IDP_ENTITY_ID, "subject", "alice@example.org", username) == (
            "alice@example.org", expected)
