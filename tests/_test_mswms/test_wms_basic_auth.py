# -*- coding: utf-8 -*-
"""

    tests._test_mswms.test_wms_basic_auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test the basic HTTP authentication of mswms

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
import hashlib
import logging
import sys
import runpy
import types
from pathlib import Path

import pytest

from mslib.mswms import app as mswms_app_module
from mslib.utils.basic_auth import BasicAuthSettingError, hash_password

USERS = [("mswms", hash_password("secret")), ("legacy", hashlib.md5("old".encode("utf-8")).hexdigest())]

GETCAPABILITIES = "/?request=GetCapabilities&service=WMS&version=1.3.0"

# every kind of page: the WMS, the docs, the gallery with its plots and code, and all static files
PROTECTED_PATHS = [
    "/",
    GETCAPABILITIES,
    "/?request=GetMap&service=WMS&version=1.3.0",
    "/index",
    "/mss",
    "/mss/about",
    "/mss/install",
    "/mss/help",
    "/mss/imprint",
    "/mss/gdpr",
    "/mss/favicon.ico",
    "/mss/logo.png",
    "/mss/overview.png",
    "/mss/plots",
    "/mss/code/plot_example.md",
    "/mss/code/plot_example.md?download=true",
    "/static/plots.html",
    "/static/plots/plot_example.png",
    "/gallery-static/plots.html",
    "/docs-static/docs/about.md",
    "/xstatic/jquery/jquery.min.js",
    "/mss_theme/img/wise12_overview.png",
    "/does-not-exist",
]

# pages that exist on every server, also without a generated gallery
EXISTING_PATHS = ["/", GETCAPABILITIES, "/index", "/mss/about", "/mss/plots", "/mss/favicon.ico", "/mss/logo.png",
                  "/docs-static/docs/about.md"]


def basic(username, password):
    credentials = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def protected_app(mswms_app, monkeypatch):
    monkeypatch.setitem(mswms_app.config, "ENABLE_BASIC_HTTP_AUTHENTICATION", True)
    monkeypatch.setitem(mswms_app.extensions, "mswms_allowed_users", USERS)
    return mswms_app


@pytest.mark.parametrize("path", PROTECTED_PATHS)
def test_every_page_needs_the_login(protected_app, path):
    client = protected_app.test_client()
    for headers in [{}, basic("mswms", "wrong"), basic("unknown", "secret"), basic("legacy", "secret"),
                    {"Authorization": "Bearer secret"}, {"Authorization": "Basic not-base64"}]:
        response = client.get(path, headers=headers)
        assert response.status_code == 401, (path, headers)
        assert response.headers["WWW-Authenticate"].startswith("Basic ")
        assert response.data == b"Unauthorized Access"
    for headers in [basic("mswms", "secret"), basic("legacy", "old")]:
        response = client.get(path, headers=headers)
        assert response.status_code != 401, (path, headers)


@pytest.mark.parametrize("path", EXISTING_PATHS)
def test_pages_are_served_with_the_login(protected_app, path):
    response = protected_app.test_client().get(path, headers=basic("mswms", "secret"))
    assert response.status_code == 200, path


def test_getcapabilities_with_the_login(protected_app):
    response = protected_app.test_client().get(GETCAPABILITIES, headers=basic("mswms", "secret"))
    assert response.status_code == 200
    assert b"<WMS_Capabilities" in response.data


def test_without_users_nobody_gets_in(protected_app, monkeypatch):
    monkeypatch.setitem(protected_app.extensions, "mswms_allowed_users", [])
    response = protected_app.test_client().get("/mss/plots", headers=basic("mswms", "secret"))
    assert response.status_code == 401


@pytest.mark.parametrize("path", EXISTING_PATHS)
def test_disabled_authentication_keeps_pages_open(mswms_app, monkeypatch, path):
    monkeypatch.setitem(mswms_app.config, "ENABLE_BASIC_HTTP_AUTHENTICATION", False)
    response = mswms_app.test_client().get(path)
    assert response.status_code == 200, path


def test_init_basic_auth_loads_mswms_auth(mswms_app, monkeypatch, caplog):
    monkeypatch.setitem(mswms_app.config, "ENABLE_BASIC_HTTP_AUTHENTICATION", True)
    monkeypatch.setitem(mswms_app.extensions, "mswms_allowed_users", None)
    mswms_auth = types.ModuleType("mswms_auth")
    mswms_auth.allowed_users = USERS + [("mswms2", "add_argon2_hash_of_PASSWORD_here")]
    monkeypatch.setitem(sys.modules, "mswms_auth", mswms_auth)
    with caplog.at_level(logging.WARNING):
        mswms_app_module._init_basic_auth(mswms_app)
    assert mswms_app.extensions["mswms_allowed_users"] == mswms_auth.allowed_users
    messages = [record.getMessage() for record in caplog.records]
    assert any("mswms_auth: the password of user 'legacy' is stored as MD5 digest" in m for m in messages)
    assert any("mswms_auth: user 'mswms2' has no valid password hash" in m for m in messages)
    client = mswms_app.test_client()
    assert client.get("/mss/plots").status_code == 401
    assert client.get("/mss/plots", headers=basic("mswms", "secret")).status_code == 200


def test_init_basic_auth_without_mswms_auth_rejects_everyone(mswms_app, monkeypatch):
    monkeypatch.setitem(mswms_app.config, "ENABLE_BASIC_HTTP_AUTHENTICATION", True)
    monkeypatch.setitem(mswms_app.extensions, "mswms_allowed_users", None)
    monkeypatch.setitem(sys.modules, "mswms_auth", None)
    mswms_app_module._init_basic_auth(mswms_app)
    assert mswms_app.extensions["mswms_allowed_users"] == []
    assert mswms_app.test_client().get("/", headers=basic("mswms", "secret")).status_code == 401


def test_init_basic_auth_disabled_loads_nobody(mswms_app, monkeypatch, caplog):
    monkeypatch.setitem(mswms_app.config, "ENABLE_BASIC_HTTP_AUTHENTICATION", False)
    monkeypatch.setitem(mswms_app.extensions, "mswms_allowed_users", None)
    mswms_auth = types.ModuleType("mswms_auth")
    mswms_auth.allowed_users = [("mswms", "add_argon2_hash_of_PASSWORD_here")]
    monkeypatch.setitem(sys.modules, "mswms_auth", mswms_auth)
    with caplog.at_level(logging.WARNING):
        mswms_app_module._init_basic_auth(mswms_app)
    assert mswms_app.extensions["mswms_allowed_users"] == []
    # no warnings about the placeholders of the sample when nobody uses them
    assert caplog.records == []


def test_busy_password_checks_answer_503(protected_app, monkeypatch):
    def busy(*args):
        raise mswms_app_module.PasswordCheckBusy("busy")

    monkeypatch.setattr(mswms_app_module, "check_credentials", busy)
    response = protected_app.test_client().get("/", headers=basic("mswms", "secret"))
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "10"


def test_lowercase_setting_refuses_to_start(mswms_app, monkeypatch):
    # earlier samples spelled it in lower case, Flask ignores that and the server would run without login
    monkeypatch.setattr(mswms_app_module.mswms_settings, "enable_basic_http_authentication", True, raising=False)
    with pytest.raises(BasicAuthSettingError, match="ENABLE_BASIC_HTTP_AUTHENTICATION"):
        mswms_app_module._init_basic_auth(mswms_app)


@pytest.fixture
def auth_wsgi(monkeypatch):
    # the sample of docs/samples/wsgi, with an mswms_auth that has a user with a password that isn't ASCII
    module = types.ModuleType("mswms_auth")
    module.allowed_users = [("mswms", hash_password("pässwort")), ("legacy", hashlib.md5(b"old").hexdigest())]
    monkeypatch.setitem(sys.modules, "mswms_auth", module)
    path = Path(__file__).parents[2] / "docs" / "samples" / "wsgi" / "auth.wsgi"
    return runpy.run_path(str(path))


def test_auth_wsgi_is_standalone():
    # Apache runs it in its own Python, without mslib
    path = Path(__file__).parents[2] / "docs" / "samples" / "wsgi" / "auth.wsgi"
    imports = [line for line in path.read_text().splitlines() if line.startswith(("import ", "from "))]
    assert imports and not any("mslib" in line for line in imports), imports


def test_auth_wsgi_checks_passwords(auth_wsgi):
    check_password = auth_wsgi["check_password"]

    def apache(text):
        # mod_wsgi passes what the browser sent as UTF-8, decoded as ISO-8859-1
        return text.encode("utf-8").decode("latin-1")

    assert check_password({}, apache("mswms"), apache("pässwort")) is True
    assert check_password({}, apache("legacy"), apache("old")) is True
    assert check_password({}, apache("mswms"), apache("wrong")) is False
    assert check_password({}, apache("unknown"), apache("pässwort")) is False
