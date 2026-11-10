# -*- coding: utf-8 -*-
"""

    tests._test_msidp.test_msidp
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the sessions, cookies, logs and error messages of the test identity provider msidp.

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
import logging
import shutil

import mock
import pytest
from werkzeug.test import Client

from mslib.msidp import idp
from mslib.msidp.idp_user import PASSWD

USER, PASSWORD = next(iter(PASSWD.items()))
ENVIRON = {"REQUEST_METHOD": "POST", "CONTENT_LENGTH": "0", "wsgi.url_scheme": "https", "HTTP_HOST": "localhost",
           "PATH_INFO": "/sso/ecp"}


@pytest.fixture
def server():
    """msidp with a stand-in for the pysaml2 server, only its session cache is real"""
    with mock.patch.object(idp.IdpServerSettings_, "IDP", mock.Mock(cache=idp.Cache())) as idp_server, \
            mock.patch.object(idp.IdpServerSettings_, "AUTHN_BROKER", mock.MagicMock()), \
            mock.patch.object(idp.IdpServerSettings_, "https", False):
        yield idp_server


@pytest.fixture
def probe():
    """Replaces the SAML endpoints by one that records the user msidp found for a request"""
    users = []

    def callback(environ, start_response, user):
        users.append(user)
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"probe"]

    with mock.patch.object(idp, "AUTHN_URLS", [(r"probe$", callback)]):
        yield users


def _verify(client, password=PASSWORD):
    form = {"login": USER, "password": password, "key": "the-key", "authn_reference": "ref",
            "redirect_uri": "https://sp.example.org/sso"}
    return client.post("/verify", data=form)


def test_login_sets_a_protected_cookie_and_no_session_id_in_the_url(server):
    response = _verify(Client(idp.application))
    assert response.status_code == 302
    assert response.headers["Location"] == "https://sp.example.org/sso?key=the-key"
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Secure" not in cookie
    uid = server.cache.user2uid[USER]
    assert uid not in response.headers["Location"]
    with mock.patch.object(idp.IdpServerSettings_, "https", True):
        assert "Secure" in _verify(Client(idp.application)).headers["Set-Cookie"]


def test_wrong_password_or_unknown_user_is_refused(server):
    assert _verify(Client(idp.application), password="wrong").status_code == 401
    response = Client(idp.application).post("/verify", data={"login": "nobody", "password": "x", "key": "k",
                                                             "authn_reference": "r", "redirect_uri": "u"})
    assert response.status_code == 401
    assert server.cache.uid2user == {}


def test_session_only_from_the_cookie(server, probe):
    client = Client(idp.application)
    assert _verify(client).status_code == 302
    uid = server.cache.user2uid[USER]
    client.get("/probe")
    # the same session id in the URL, without the cookie
    Client(idp.application).get("/probe", query_string={"id": uid})
    assert probe == [USER, None]


def test_session_expires_on_the_server(server, probe):
    client = Client(idp.application)
    assert _verify(client).status_code == 302
    expired = idp.time.time() + idp.SESSION_LIFETIME * 60 + 1
    with mock.patch.object(idp.time, "time", return_value=expired):
        client.get("/probe")
    assert probe == [None]
    assert server.cache.uid2user == {} and server.cache.user2uid == {}


def test_new_login_ends_the_earlier_session(server):
    first = server.cache.login(USER)
    second = server.cache.login(USER)
    assert server.cache.user_of(first) is None
    assert server.cache.user_of(second) == USER
    server.cache.logout(USER)
    assert server.cache.user_of(second) is None


def test_error_messages_are_escaped(server):
    server.parse_logout_request.side_effect = ValueError('<script>alert("xss")</script>')
    environ = {"REQUEST_METHOD": "GET", "QUERY_STRING": ""}
    start_response = mock.Mock()
    body = b"".join(idp.SLO(environ, start_response).do("request", idp.BINDING_HTTP_REDIRECT))
    assert start_response.call_args.args[0].startswith("400")
    assert b"<script>" not in body
    assert b"&lt;script&gt;" in body


@pytest.mark.parametrize("credentials, accepted", [
    (f"{USER}:{PASSWORD}", True),
    (f"{USER}:wrong", False),
    (f"nobody:{PASSWORD}", False),
    ("no colon", False),
])
def test_ecp_needs_the_right_password(server, credentials, accepted):
    environ = dict(ENVIRON, HTTP_AUTHORIZATION="Basic " + base64.b64encode(credentials.encode()).decode())
    start_response = mock.Mock()
    with mock.patch.object(idp.SSO, "operation", return_value=[b"response"]) as operation:
        sso = idp.SSO(environ, start_response)
        result = sso.ecp()
    if accepted:
        assert result == [b"response"] and sso.user == USER
        operation.assert_called_once()
    else:
        assert start_response.call_args.args[0].startswith("401")
        operation.assert_not_called()


def test_ecp_refuses_invalid_basic_auth(server):
    start_response = mock.Mock()
    environ = dict(ENVIRON, HTTP_AUTHORIZATION="Basic !!!")
    with mock.patch.object(idp.SSO, "operation") as operation:
        idp.SSO(environ, start_response).ecp()
    assert start_response.call_args.args[0].startswith("401")
    operation.assert_not_called()


def test_passwords_and_session_ids_are_not_logged(server, caplog):
    # the logging configuration of other tests can disable the existing loggers
    with mock.patch.object(idp.logger, "disabled", False), caplog.at_level(logging.DEBUG, logger=idp.logger.name):
        client = Client(idp.application)
        assert _verify(client).status_code == 302
        client.get("/unknown")
    uid = server.cache.user2uid[USER]
    # the debug messages are there
    assert f"Logged in {USER}" in caplog.text
    assert PASSWORD not in caplog.text
    assert uid not in caplog.text


@pytest.mark.skipif(shutil.which("xmlsec1") is None, reason="idp_conf needs xmlsec1")
def test_configured_log_level_is_not_debug():
    from mslib.msidp import idp_conf
    logging_config = idp_conf.CONFIG["logging"]
    assert logging_config["root"]["level"] == "WARNING"
    assert logging_config["loggers"]["saml2"]["level"] == "WARNING"
