# -*- coding: utf-8 -*-
"""

    tests._test_mscolab.test_mail
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for sending the emails of mscolab: the required sender, failed sends, and what users get told then

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
import logging
import smtplib

import mock
import pytest

from mslib.mscolab.app import InsecureMailSettingError, create_app
from mslib.mscolab.conf import mscolab_settings
from mslib.mscolab.mail import send_email
from mslib.mscolab.models import User
from mslib.mscolab.seed import add_user

USER = ("UV10@uv10.de", "UV10", "uv10-password", "User UV")
NEW_USER = {"email": "new@example.org", "password": "a-password", "username": "new", "fullname": "New"}
PUBLIC_URL = "https://mscolab.example.org"


@pytest.fixture
def no_secret_key_in_environment(monkeypatch):
    monkeypatch.delenv("MSCOLAB_SECRET_KEY", raising=False)


def _mail_settings(sender):
    settings = copy.copy(mscolab_settings)
    settings.MAIL_ENABLED = True
    settings.PUBLIC_URL = PUBLIC_URL
    settings.MAIL_DEFAULT_SENDER = sender
    return settings


@pytest.mark.parametrize("sender", [None, "", "  ", ("MSS",), ("", "MSS@localhost"), ("MSS", None), 42])
def test_mail_needs_a_sender(no_secret_key_in_environment, sender):
    with pytest.raises(InsecureMailSettingError, match="MAIL_DEFAULT_SENDER"):
        create_app(_mail_settings(sender))


def test_mail_needs_a_sender_also_if_it_is_not_set(no_secret_key_in_environment):
    settings = _mail_settings(None)
    del settings.MAIL_DEFAULT_SENDER
    with pytest.raises(InsecureMailSettingError, match="MAIL_DEFAULT_SENDER"):
        create_app(settings)


@pytest.mark.parametrize("sender", ["MSS@localhost", ("MSS", "MSS@localhost")])
def test_mail_with_a_sender(no_secret_key_in_environment, sender):
    assert create_app(_mail_settings(sender)).config["MAIL_DEFAULT_SENDER"] == sender


def test_no_sender_needed_without_mail(no_secret_key_in_environment):
    settings = _mail_settings(None)
    settings.MAIL_ENABLED = False
    assert create_app(settings).config["MAIL_ENABLED"] is False


def test_send_email(mscolab_app, monkeypatch):
    monkeypatch.setitem(mscolab_app.config, "MAIL_DEFAULT_SENDER", "MSS@localhost")
    monkeypatch.setattr(mscolab_app, "mail", mock.Mock())
    with mscolab_app.app_context():
        assert send_email("someone@example.org", "a subject", "<p>text</p>") is True
    message = mscolab_app.mail.send.call_args.args[0]
    assert message.recipients == ["someone@example.org"]
    assert message.sender == "MSS@localhost"
    assert message.subject == "a subject"
    assert message.html == "<p>text</p>"


@pytest.mark.parametrize("error", [smtplib.SMTPServerDisconnected("gone"), ConnectionRefusedError("refused")])
def test_send_email_reports_a_failed_send(mscolab_app, monkeypatch, caplog, error):
    monkeypatch.setitem(mscolab_app.config, "MAIL_DEFAULT_SENDER", "MSS@localhost")
    monkeypatch.setattr(mscolab_app, "mail", mock.Mock(**{"send.side_effect": error}))
    with mscolab_app.app_context(), caplog.at_level(logging.ERROR):
        assert send_email("someone@example.org", "a subject", "<p>text</p>") is False
    record = next(record for record in caplog.records if "Can't send email" in record.getMessage())
    # the reason is in the log, not only that it failed
    assert record.exc_info is not None


def test_send_email_does_not_hide_programming_errors(mscolab_app, monkeypatch):
    monkeypatch.setitem(mscolab_app.config, "MAIL_DEFAULT_SENDER", "MSS@localhost")
    monkeypatch.setattr(mscolab_app, "mail", mock.Mock(**{"send.side_effect": AttributeError("no send")}))
    with mscolab_app.app_context(), pytest.raises(AttributeError):
        send_email("someone@example.org", "a subject", "<p>text</p>")


def _mail_client(app, monkeypatch):
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    monkeypatch.setitem(app.config, "MAIL_ENABLED", True)
    monkeypatch.setitem(app.config, "PUBLIC_URL", PUBLIC_URL)
    return app.test_client()


def _register(client, sent):
    # with MAIL_ENABLED the address is checked for deliverability, which needs DNS
    with mock.patch("mslib.mscolab.blueprints.auth.send_email", return_value=sent), \
            mock.patch("mslib.mscolab.auth.email_validator.validate_email"):
        return client.post("/register", data=NEW_USER)


def test_registration_is_undone_when_the_confirmation_email_fails(mscolab_app, monkeypatch):
    client = _mail_client(mscolab_app, monkeypatch)
    response = _register(client, sent=False)
    assert response.status_code == 503
    assert response.json["success"] is False
    assert "could not be sent" in response.json["message"]
    with mscolab_app.app_context():
        assert User.query.filter_by(emailid=NEW_USER["email"]).first() is None
    # the address is not taken, the user can register again
    assert _register(client, sent=True).status_code == 204
    with mscolab_app.app_context():
        assert User.query.filter_by(emailid=NEW_USER["email"]).first() is not None


def test_password_reset_request_tells_when_the_email_fails(mscolab_app, monkeypatch):
    with mscolab_app.app_context():
        assert add_user(*USER)
    client = _mail_client(mscolab_app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email", return_value=False):
        response = client.post("/reset_request", data={"email": USER[0], "submit": "Reset password"})
    assert response.status_code == 200
    assert "issue sending" in response.text
    assert "An email was sent" not in response.text


def test_password_reset_request_when_the_email_is_sent(mscolab_app, monkeypatch):
    with mscolab_app.app_context():
        assert add_user(*USER)
    client = _mail_client(mscolab_app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email", return_value=True):
        response = client.post("/reset_request", data={"email": USER[0], "submit": "Reset password"})
    assert response.status_code == 200
    assert "An email was sent" in response.text


def _confirm_path(html):
    """the path of the confirmation link in the html of a confirmation email"""
    start = html.index(f"{PUBLIC_URL}/confirm/") + len(PUBLIC_URL)
    return html[start:html.index('"', start)]


def test_expired_confirmation_link_points_to_a_new_confirmation_email(mscolab_app, monkeypatch):
    client = _mail_client(mscolab_app, monkeypatch)
    response = client.get("/confirm/not-a-valid-token")
    assert response.status_code == 401
    assert "has expired or is invalid" in response.text
    assert 'href="/resend_confirmation"' in response.text


@pytest.mark.parametrize("confirmed, sent", [(False, True), (True, False)])
def test_resend_confirmation(mscolab_app, monkeypatch, confirmed, sent):
    with mscolab_app.app_context():
        assert add_user(*USER)
        if confirmed:
            user = User.query.filter_by(emailid=USER[0]).first()
            mscolab_app.extensions['fm'].modify_user(user, attribute="confirmed", value=True)
    client = _mail_client(mscolab_app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email", return_value=True) as send_email:
        response = client.post("/resend_confirmation", data={"email": USER[0], "submit": "Send confirmation email"})
    assert response.status_code == 200
    # the same answer whether an email was sent or not
    assert "An email was sent if this address has an account that is not confirmed yet" in response.text
    assert send_email.called is sent
    if sent:
        assert send_email.call_args.args[0] == USER[0]
        # the new link confirms the account
        with mock.patch("mslib.mscolab.blueprints.auth.send_email"):
            assert client.get(_confirm_path(send_email.call_args.args[2])).status_code == 200
        with mscolab_app.app_context():
            user = User.query.filter_by(emailid=USER[0]).first()
            assert user.confirmed is True
            assert user.confirmed_on is not None


def test_resend_confirmation_for_an_unknown_address(mscolab_app, monkeypatch):
    client = _mail_client(mscolab_app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email") as send_email:
        response = client.post("/resend_confirmation", data={"email": "unknown@example.org",
                                                             "submit": "Send confirmation email"})
    assert response.status_code == 200
    assert "An email was sent if this address has an account that is not confirmed yet" in response.text
    assert not send_email.called


def test_resend_confirmation_tells_when_the_email_fails(mscolab_app, monkeypatch):
    with mscolab_app.app_context():
        assert add_user(*USER)
    client = _mail_client(mscolab_app, monkeypatch)
    with mock.patch("mslib.mscolab.blueprints.auth.send_email", return_value=False):
        response = client.post("/resend_confirmation", data={"email": USER[0], "submit": "Send confirmation email"})
    assert response.status_code == 200
    assert "issue sending" in response.text
    assert "An email was sent" not in response.text


def test_resend_confirmation_needs_mail(mscolab_app, monkeypatch):
    monkeypatch.setitem(mscolab_app.config, "MAIL_ENABLED", False)
    assert mscolab_app.test_client().get("/resend_confirmation").status_code == 403


def test_password_reset_confirms_the_email_address(mscolab_app):
    with mscolab_app.app_context():
        assert add_user(*USER)
        user = User.query.filter_by(emailid=USER[0]).first()
        assert user.confirmed is False and user.confirmed_on is None
        assert user.reset_password(user.password, "a-new-password")
        assert user.confirmed is True
        assert user.confirmed_on is not None


def test_password_reset_keeps_the_date_of_an_earlier_confirmation(mscolab_app):
    with mscolab_app.app_context():
        assert add_user(*USER)
        user = User.query.filter_by(emailid=USER[0]).first()
        fm = mscolab_app.extensions['fm']
        fm.modify_user(user, attribute="confirmed", value=True)
        confirmed_on = datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
        fm.modify_user(user, attribute="confirmed_on", value=confirmed_on)
        assert user.reset_password(user.password, "a-new-password")
        assert user.confirmed_on == confirmed_on
