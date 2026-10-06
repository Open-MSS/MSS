# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_token_hygiene
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for login tokens (version, lifetime, revocation), the tokens of email links and what is logged.

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
import copy
import datetime
import json
import logging

import jwt
import mock
import pytest
import sqlalchemy
from flask import current_app

from mslib.mscolab import auth
from mslib.mscolab.app import InsecureMailSettingError, InsecureSecretError, create_app
from mslib.mscolab.conf import DefaultSettings, mscolab_settings
from mslib.mscolab.models import db, User
from mslib.mscolab.seed import add_user, get_user

USER = ("UV10@uv10.de", "UV10", "uv10-password", "User UV")
PUBLIC_URL = "https://mscolab.example.org"


@pytest.fixture
def app(mscolab_app):
    with mscolab_app.app_context():
        assert add_user(*USER)
        yield mscolab_app


def _login(client, password=USER[2]):
    response = client.post("/token", data={"email": USER[0], "password": password})
    assert response.text != "False"
    return json.loads(response.text)["token"]


def _authorized(client, token):
    return client.get("/test_authorized", query_string={"token": token}).text == "True"


def test_default_token_lifetime_is_ten_days(app):
    assert DefaultSettings.EXPIRATION == 864000
    token = get_user(USER[0]).generate_auth_token()
    exp = jwt.decode(token, options={"verify_signature": False})["exp"]
    remaining = exp - datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    assert abs(remaining - current_app.config["EXPIRATION"]) < 60


def test_token_carries_the_token_nonce(app):
    user = get_user(USER[0])
    nonce = user.token_nonce
    assert len(nonce) == 32
    token = user.generate_auth_token()
    assert jwt.decode(token, options={"verify_signature": False})["nonce"] == nonce
    assert User.verify_auth_token(token).id == user.id
    user.revoke_tokens()
    db.session.commit()
    # all earlier tokens of the user are revoked, a new one works
    assert user.token_nonce != nonce
    assert User.verify_auth_token(token) is None
    assert User.verify_auth_token(user.generate_auth_token()).id == user.id


def test_token_of_deleted_user_does_not_work_for_a_new_user_with_its_id(app):
    # SQLite reuses the id of a deleted user
    old = get_user(USER[0])
    old_id, old_token = old.id, old.generate_auth_token()
    db.session.delete(old)
    db.session.commit()
    new = User("other@example.org", "other", "other-password")
    new.id = old_id
    db.session.add(new)
    db.session.commit()
    assert User.verify_auth_token(old_token) is None
    assert User.verify_auth_token(new.generate_auth_token()).id == old_id


def test_token_without_version_is_refused(app):
    # tokens of servers before the token version can't be revoked, they are refused
    user = get_user(USER[0])
    old_token = jwt.encode(
        {"id": user.id, "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(hours=1)},
        current_app.config["SECRET_KEY"], algorithm="HS256")
    assert User.verify_auth_token(old_token) is None


def test_users_table_has_token_nonce(app):
    # added by the 12.0.0 migration
    columns = {column["name"]: column for column in sqlalchemy.inspect(db.engine).get_columns("users")}
    assert columns["token_nonce"]["nullable"] is False


def test_logout_everywhere(app):
    client = app.test_client()
    first, second = _login(client), _login(client)
    assert _authorized(client, first) and _authorized(client, second)
    with mock.patch.object(app.extensions["sockio"].sm, "forget_user") as forget_user:
        response = client.post("/logout_everywhere", data={"token": first})
    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    forget_user.assert_called_once_with(get_user(USER[0]).id)
    # every token of the user is revoked, also the one of the request
    assert not _authorized(client, first) and not _authorized(client, second)
    assert client.post("/logout_everywhere", data={"token": first}).text == "False"
    assert _authorized(client, _login(client))


def test_token_purposes_are_separate(app):
    email = USER[0]
    confirmation = auth.generate_confirmation_token(email, auth.EMAIL_CONFIRMATION)
    idp_login = auth.generate_confirmation_token(email, auth.IDP_LOGIN)
    reset = auth.generate_password_reset_token(get_user(email))
    assert auth.confirm_token(confirmation, auth.EMAIL_CONFIRMATION) == email
    assert auth.confirm_token(idp_login, auth.IDP_LOGIN) == email
    # a token of one purpose is no token of another one
    assert auth.confirm_token(confirmation, auth.IDP_LOGIN) is False
    assert auth.confirm_token(idp_login, auth.EMAIL_CONFIRMATION) is False
    assert auth.confirm_token(reset, auth.EMAIL_CONFIRMATION) is False
    assert auth.confirm_password_reset_token(confirmation) is None
    assert auth.confirm_password_reset_token(idp_login) is None
    assert auth.confirm_password_reset_token(reset)[0].emailid == email
    with pytest.raises(ValueError):
        auth.generate_confirmation_token(email, "unknown")


def test_password_reset_link_works_once_and_logs_out_everywhere(app, monkeypatch):
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    client = app.test_client()
    old_token = _login(client)
    reset_token = auth.generate_password_reset_token(get_user(USER[0]))
    assert client.get(f"/reset_password/{reset_token}").status_code == 200
    new_password = "a-new-password"
    with mock.patch.object(app.extensions["sockio"].sm, "forget_user") as forget_user:
        response = client.post(f"/reset_password/{reset_token}",
                               data={"password": new_password, "confirm_password": new_password,
                                     "submit": "Change Password"})
    assert response.status_code == 200
    assert get_user(USER[0]).verify_password(new_password)
    forget_user.assert_called_once_with(get_user(USER[0]).id)
    # whoever knew the old password or had a token is out
    assert not _authorized(client, old_token)
    assert _authorized(client, _login(client, new_password))
    # the link was used, it can't set the password again
    assert auth.confirm_password_reset_token(reset_token) is None
    response = client.post(f"/reset_password/{reset_token}",
                           data={"password": "another-password", "confirm_password": "another-password",
                                 "submit": "Change Password"})
    assert b"expired or is invalid" in response.data
    assert get_user(USER[0]).verify_password(new_password)


def test_password_reset_link_works_once_also_at_the_same_time(app):
    # two requests with the same link, both checked before either changed the password
    reset_token = auth.generate_password_reset_token(get_user(USER[0]))
    first, second = auth.confirm_password_reset_token(reset_token), auth.confirm_password_reset_token(reset_token)
    user, password_hash = first
    assert user.reset_password(password_hash, "first-password") is True
    user, password_hash = second
    assert user.reset_password(password_hash, "second-password") is False
    assert get_user(USER[0]).verify_password("first-password")


def test_password_reset_with_bytes_secret_key(app, monkeypatch):
    # check_secret accepts a SECRET_KEY of bytes
    monkeypatch.setitem(app.config, "SECRET_KEY", b"0123456789abcdefghijklmnopqrstuvwxyz")
    reset_token = auth.generate_password_reset_token(get_user(USER[0]))
    user, _ = auth.confirm_password_reset_token(reset_token)
    assert user.emailid == USER[0]


def test_email_links_work_in_another_process(app, no_secret_key_in_environment):
    # the salts no longer change per process: a link still works after a restart or on another worker
    confirmation = auth.generate_confirmation_token(USER[0], auth.EMAIL_CONFIRMATION)
    with create_app(copy.copy(mscolab_settings)).app_context():
        assert current_app.config["SECRET_KEY"] == app.config["SECRET_KEY"]
        assert auth.confirm_token(confirmation, auth.EMAIL_CONFIRMATION) == USER[0]


def _mail_app(app, monkeypatch):
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    monkeypatch.setitem(app.config, "MAIL_ENABLED", True)
    monkeypatch.setitem(app.config, "PUBLIC_URL", PUBLIC_URL)
    return app.test_client()


def test_password_reset_link_uses_public_url(app, monkeypatch):
    client = _mail_app(app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email") as send_email:
        # the Host header of the request must not end up in the link
        response = client.post("/reset_request", data={"email": USER[0], "submit": "Reset password"},
                               headers={"Host": "attacker.example"})
    assert response.status_code == 200
    html = send_email.call_args.args[2]
    assert f"{PUBLIC_URL}/reset_password/" in html
    assert "attacker.example" not in html


def test_confirmation_link_uses_public_url(app, monkeypatch):
    client = _mail_app(app, monkeypatch)
    # with MAIL_ENABLED the address is checked for deliverability, which needs DNS
    with mock.patch("mslib.mscolab.blueprints.auth.send_email") as send_email, \
            mock.patch("mslib.mscolab.auth.email_validator.validate_email"):
        response = client.post("/register", data={"email": "new@example.org", "password": "a-password",
                                                  "username": "new", "fullname": "New"},
                               headers={"Host": "attacker.example"})
    assert response.status_code == 204
    html = send_email.call_args.args[2]
    assert f"{PUBLIC_URL}/confirm/" in html
    assert "attacker.example" not in html


@pytest.fixture
def no_secret_key_in_environment(monkeypatch):
    monkeypatch.delenv("MSCOLAB_SECRET_KEY", raising=False)


@pytest.mark.parametrize("public_url", [None, "", "mscolab.example.org", "ftp://mscolab.example.org", "https://"])
def test_mail_needs_public_url(no_secret_key_in_environment, public_url):
    settings = copy.copy(mscolab_settings)
    settings.MAIL_ENABLED = True
    settings.PUBLIC_URL = public_url
    with pytest.raises(InsecureMailSettingError, match="PUBLIC_URL"):
        create_app(settings)
    # reported like an insecure secret, e.g. by the mscolab command
    assert issubclass(InsecureMailSettingError, InsecureSecretError)


@pytest.mark.parametrize("mail_enabled, public_url", [(True, PUBLIC_URL), (True, "http://localhost:8083/"),
                                                      (False, None)])
def test_mail_with_public_url(no_secret_key_in_environment, mail_enabled, public_url):
    settings = copy.copy(mscolab_settings)
    settings.MAIL_ENABLED = mail_enabled
    settings.PUBLIC_URL = public_url
    assert create_app(settings).config["PUBLIC_URL"] == public_url


def test_socket_messages_with_token_are_not_logged(app, caplog):
    token = _login(app.test_client())
    sio = app.extensions["sockio"].test_client(app)
    with caplog.at_level(logging.DEBUG):
        sio.emit("start", {"token": token})
        sio.emit("operation-selected", {"token": token, "op_id": 1})
    sio.disconnect()
    assert token not in caplog.text


def test_seeded_passwords_are_not_logged(app, caplog):
    with caplog.at_level(logging.DEBUG):
        assert add_user("seed@example.org", "seed", "a-seeded-password", "Seed")
    assert "a-seeded-password" not in caplog.text
    assert "seed@example.org" in caplog.text
