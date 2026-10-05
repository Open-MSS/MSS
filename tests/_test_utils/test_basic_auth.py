# -*- coding: utf-8 -*-
"""

    tests._test_utils.test_basic_auth
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides pytest functions to test mslib.utils.basic_auth

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
import hashlib
import logging
from unittest import mock

import pytest

from mslib.utils import basic_auth
from mslib.utils.basic_auth import check_allowed_users, check_credentials, hash_password

ARGON2_HASH = hash_password("secret")
MD5_DIGEST = hashlib.md5("legacy".encode("utf-8")).hexdigest()
ALLOWED_USERS = [("alice", ARGON2_HASH), ("bob", MD5_DIGEST)]


@pytest.fixture(autouse=True)
def empty_cache():
    basic_auth._verified.clear()
    yield
    basic_auth._verified.clear()


def test_hash_password():
    password_hash = hash_password("secret")
    assert password_hash.startswith("$argon2id$")
    assert "secret" not in password_hash
    # salted: the same password gives another hash
    assert password_hash != ARGON2_HASH
    assert check_credentials([("alice", password_hash)], "alice", "secret")


def test_check_credentials_argon2():
    assert check_credentials(ALLOWED_USERS, "alice", "secret")
    assert not check_credentials(ALLOWED_USERS, "alice", "wrong")
    assert not check_credentials(ALLOWED_USERS, "alice", "")
    # the password of another user
    assert not check_credentials(ALLOWED_USERS, "alice", "legacy")
    assert not check_credentials(ALLOWED_USERS, "carol", "secret")
    assert not check_credentials(ALLOWED_USERS, "Alice", "secret")


def test_check_credentials_md5_still_works():
    assert check_credentials(ALLOWED_USERS, "bob", "legacy")
    assert check_credentials([("bob", MD5_DIGEST.upper())], "bob", "legacy")
    assert not check_credentials(ALLOWED_USERS, "bob", "wrong")
    # the digest itself is not the password
    assert not check_credentials(ALLOWED_USERS, "bob", MD5_DIGEST)


def test_check_credentials_md5_is_compared_in_constant_time():
    with mock.patch("mslib.utils.basic_auth.hmac.compare_digest", wraps=basic_auth.hmac.compare_digest) as compare:
        assert check_credentials(ALLOWED_USERS, "bob", "legacy")
    assert mock.call(MD5_DIGEST, MD5_DIGEST) in compare.call_args_list


@pytest.mark.parametrize("username, password", [
    (None, "secret"), ("alice", None), (None, None), (b"alice", "secret"), ("alice", b"secret"),
])
def test_check_credentials_missing_or_wrong_type(username, password):
    assert not check_credentials(ALLOWED_USERS, username, password)


def test_check_credentials_non_ascii():
    allowed_users = [("jürgen", hash_password("pässwort")), ("zoë", hashlib.md5("ünïcode".encode()).hexdigest())]
    assert check_credentials(allowed_users, "jürgen", "pässwort")
    assert check_credentials(allowed_users, "zoë", "ünïcode")
    assert not check_credentials(allowed_users, "jürgen", "passwort")
    assert not check_credentials(allowed_users, "jurgen", "pässwort")


@pytest.mark.parametrize("entry", [
    ("mswms", "add_argon2_hash_of_PASSWORD_here"),
    ("mswms", "add_md5_digest_of_PASSWORD_here"),
    ("mswms", "secret"),
    ("mswms", ""),
    ("mswms", "$argon2id$broken"),
    ("mswms",),
    ("mswms", "secret", "extra"),
    "mswms",
    None,
    ("mswms", None),
    (None, ARGON2_HASH),
])
def test_check_credentials_skips_invalid_entries(entry):
    assert not check_credentials([entry], "mswms", "secret")
    assert not check_credentials([entry], "mswms", "add_argon2_hash_of_PASSWORD_here")
    # the valid entries after it still work
    assert check_credentials([entry] + ALLOWED_USERS, "alice", "secret")


def test_check_credentials_no_users():
    assert not check_credentials([], "alice", "secret")


def test_successful_argon2_check_is_remembered():
    with mock.patch.object(basic_auth, "_PASSWORD_HASHER", wraps=basic_auth._PASSWORD_HASHER) as hasher:
        for _ in range(3):
            assert check_credentials(ALLOWED_USERS, "alice", "secret")
        assert hasher.verify.call_count == 1
        # failed checks are not remembered
        for _ in range(2):
            assert not check_credentials(ALLOWED_USERS, "alice", "wrong")
        assert hasher.verify.call_count == 3
    # only a keyed digest is kept, not the password
    assert all(isinstance(key, bytes) and b"secret" not in key for key in basic_auth._verified)


def test_remembered_check_needs_the_same_hash():
    assert check_credentials(ALLOWED_USERS, "alice", "secret")
    # a new hash of another password for alice, e.g. after a change in mswms_auth
    assert not check_credentials([("alice", hash_password("other"))], "alice", "secret")


def test_cache_is_bounded():
    with mock.patch.object(basic_auth, "_CACHE_SIZE", 2):
        users = [(f"user{i}", hash_password(f"password{i}")) for i in range(3)]
        for i in range(3):
            assert check_credentials(users, f"user{i}", f"password{i}")
            assert len(basic_auth._verified) <= 2


def test_check_allowed_users(caplog):
    allowed_users = [
        ("alice", ARGON2_HASH),
        ("bob", MD5_DIGEST),
        ("mswms", "add_argon2_hash_of_PASSWORD_here"),
        ("broken",),
        (None, ARGON2_HASH),
    ]
    with caplog.at_level(logging.WARNING):
        check_allowed_users(allowed_users, "mswms_auth")
    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 4, messages
    assert all(message.startswith("mswms_auth: ") for message in messages)
    assert "user 'bob' is stored as MD5 digest" in messages[0]
    assert "user 'mswms' has no valid password hash" in messages[1]
    assert "not a pair of strings" in messages[2]
    assert "not a pair of strings" in messages[3]
    assert not any("alice" in message for message in messages)


def test_check_allowed_users_quiet_for_argon2(caplog):
    with caplog.at_level(logging.WARNING):
        check_allowed_users([("alice", ARGON2_HASH)], "mscolab_auth")
    assert caplog.records == []


def test_main_prints_hash(capsys):
    with mock.patch("mslib.utils.basic_auth.getpass.getpass", side_effect=["secret-password", "secret-password"]):
        basic_auth.main()
    password_hash = capsys.readouterr().out.strip()
    assert check_credentials([("alice", password_hash)], "alice", "secret-password")
    assert "secret" not in password_hash


def test_main_refuses_different_passwords(capsys):
    with mock.patch("mslib.utils.basic_auth.getpass.getpass", side_effect=["secret-password", "other-password"]), \
            pytest.raises(SystemExit) as exit_info:
        basic_auth.main()
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "differ" in captured.err


# fixed ids: ARGON2_HASH has a random salt, and pytest-xdist needs the same test ids in every worker
@pytest.mark.parametrize("password_hash", [ARGON2_HASH + "ä", "$argon2id$v=19$m=65536,t=3,p=4$ä$ä"],
                         ids=["valid_hash_with_umlaut", "umlaut_in_salt_and_hash"])
def test_hash_with_non_ascii_characters_is_invalid(caplog, password_hash):
    # e.g. a paste error; it must neither raise (HTTP 500 on every page) nor stay unnoticed
    assert check_credentials([("u", password_hash)], "u", "secret") is False
    with caplog.at_level(logging.WARNING):
        check_allowed_users([("u", password_hash)], "mswms_auth")
    assert "has no valid password hash" in caplog.records[0].getMessage()


@pytest.mark.parametrize("username", ["\ud800", "al\udcffice"])
def test_usernames_with_lone_surrogates(username):
    # e.g. from a broken settings file or a request; no exception
    assert check_credentials([(username, ARGON2_HASH)], "alice", "secret") is False
    assert check_credentials(ALLOWED_USERS, username, "secret") is False


def test_unknown_user_takes_a_password_check():
    # an unknown username must take as long as a known one with a wrong password
    with mock.patch.object(basic_auth, "_verify_argon2", wraps=basic_auth._verify_argon2) as verify:
        assert not check_credentials(ALLOWED_USERS, "unknown", "secret")
        assert verify.call_count == 1
        assert verify.call_args.args[0] == basic_auth._DUMMY_HASH
        assert not check_credentials(ALLOWED_USERS, "alice", "wrong")
        assert verify.call_count == 2
        assert verify.call_args.args[0] == ARGON2_HASH


def test_parallel_password_checks_are_limited(monkeypatch):
    # every check slot is taken, a further check waits _CHECK_TIMEOUT and gives up
    monkeypatch.setattr(basic_auth, "_checks", basic_auth.threading.BoundedSemaphore(1))
    monkeypatch.setattr(basic_auth, "_CHECK_TIMEOUT", 0.01)
    assert basic_auth._checks.acquire(timeout=1)
    try:
        with pytest.raises(basic_auth.PasswordCheckBusy):
            check_credentials(ALLOWED_USERS, "alice", "secret")
        with pytest.raises(basic_auth.PasswordCheckBusy):
            check_credentials(ALLOWED_USERS, "unknown", "secret")
    finally:
        basic_auth._checks.release()
    assert check_credentials(ALLOWED_USERS, "alice", "secret")
    # a remembered login needs no check slot
    assert basic_auth._checks.acquire(timeout=1)
    try:
        assert check_credentials(ALLOWED_USERS, "alice", "secret")
    finally:
        basic_auth._checks.release()


def test_default_limit_of_parallel_checks():
    assert basic_auth._PARALLEL_CHECKS == 4
    assert basic_auth._CHECK_TIMEOUT == 10


@pytest.mark.parametrize("password", ["", "short", "7-chars"])
def test_main_refuses_short_passwords(capsys, password):
    with mock.patch("mslib.utils.basic_auth.getpass.getpass", side_effect=[password, password]), \
            pytest.raises(SystemExit) as exit_info:
        basic_auth.main()
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "at least 8 characters" in captured.err


def test_check_basic_auth_setting(caplog):
    class Settings:
        ENABLE_BASIC_HTTP_AUTHENTICATION = True

    basic_auth.check_basic_auth_setting(Settings, "mswms_settings")

    class OldSettings:
        enable_basic_http_authentication = True

    with caplog.at_level(logging.ERROR), pytest.raises(basic_auth.BasicAuthSettingError, match="ENABLE_BASIC_HTTP"):
        basic_auth.check_basic_auth_setting(OldSettings, "mswms_settings")
    assert "enable_basic_http_authentication" in caplog.records[0].getMessage()
