# -*- coding: utf-8 -*-
"""

    mslib.utils.basic_auth
    ~~~~~~~~~~~~~~~~~~~~~~

    Checks users and passwords of the basic HTTP authentication of MSWMS and MSColab.

    The servers read the allowed users from ``mswms_auth.allowed_users`` or
    ``mscolab_auth.allowed_users``, a list of ``(username, password_hash)`` pairs. The password hash is
    an argon2 hash, create one with::

        python -m mslib.utils.basic_auth

    MD5 digests of the password, as recommended by earlier versions, are still accepted, but logged as
    deprecated, because they can be cracked quickly.

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

import getpass
import hashlib
import hmac
import logging
import re
import secrets
import sys
import threading

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_PASSWORD_HASHER = PasswordHasher()
_MD5_DIGEST = re.compile(r"[0-9a-fA-F]{32}")
# the hash tool refuses shorter passwords
MIN_PASSWORD_LENGTH = 8

# Basic auth sends the password with every request, e.g. with every GetMap of msui. Checking an argon2
# hash takes about 0.1 s and 64 MiB, so successful checks are remembered. Only a keyed digest is kept, never the
# password.
_CACHE_KEY = secrets.token_bytes(32)
_CACHE_SIZE = 1024
_verified = set()

# At most this many argon2 checks run at the same time, a request waits up to _CHECK_TIMEOUT seconds for one;
# many requests with a known username and a wrong password would otherwise use up the memory of the server.
_PARALLEL_CHECKS = 4
_CHECK_TIMEOUT = 10
_checks = threading.BoundedSemaphore(_PARALLEL_CHECKS)

# Checked when no user matches, so that a known and an unknown username take the same time
_DUMMY_HASH = _PASSWORD_HASHER.hash(secrets.token_urlsafe(16))

# The setting that enables basic authentication. Earlier samples spelled it in lower case, which Flask ignores.
BASIC_AUTH_SETTING = "ENABLE_BASIC_HTTP_AUTHENTICATION"


class PasswordCheckBusy(RuntimeError):
    """Too many password checks are running, the request should be answered with 503 Service Unavailable"""


class BasicAuthSettingError(RuntimeError):
    """The settings spell ENABLE_BASIC_HTTP_AUTHENTICATION in lower case; the server would run without login"""


def hash_password(password):
    """Return the argon2 hash of password for an entry of ``allowed_users``."""
    return _PASSWORD_HASHER.hash(password)


def _parse_entry(entry):
    """
    (username, password_hash, kind) of an entry of allowed_users, kind "argon2", "md5" or None for a hash that
    can't be checked; None if the entry is not a pair of strings
    """
    try:
        user, password_hash = entry
    except (TypeError, ValueError):
        return None
    if not isinstance(user, str) or not isinstance(password_hash, str):
        return None
    if password_hash.startswith("$argon2") and password_hash.isascii():
        return user, password_hash, "argon2"
    if _MD5_DIGEST.fullmatch(password_hash) is not None:
        return user, password_hash, "md5"
    return user, password_hash, None


def _encode(text):
    # also for texts with lone surrogates, e.g. from a broken settings file
    return text.encode("utf-8", "surrogatepass")


def _verify_argon2(password_hash, password):
    """Check password against an argon2 hash, at most _PARALLEL_CHECKS at a time"""
    if not _checks.acquire(timeout=_CHECK_TIMEOUT):
        raise PasswordCheckBusy("Too many password checks at the same time, try again later.")
    try:
        _PASSWORD_HASHER.verify(password_hash, password)
        return True
    except (VerificationError, InvalidHashError, UnicodeError, ValueError, TypeError):
        return False
    finally:
        _checks.release()


def _password_matches(password, password_hash, kind):
    if kind == "argon2":
        key = hmac.new(_CACHE_KEY, _encode(f"{password_hash}\0{password}"), "sha256").digest()
        if key in _verified:
            return True
        if not _verify_argon2(password_hash, password):
            return False
        if len(_verified) >= _CACHE_SIZE:
            _verified.clear()
        _verified.add(key)
        return True
    if kind == "md5":
        return hmac.compare_digest(hashlib.md5(_encode(password)).hexdigest(), password_hash.lower())
    return False


def check_credentials(allowed_users, username, password):
    """Return True if username and password belong to one of the allowed_users.

    :param allowed_users: list of ``(username, password_hash)`` pairs; entries of another form or with
        a hash that can't be checked are skipped, see :func:`check_allowed_users`
    :raises PasswordCheckBusy: if too many password checks are running
    """
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    matched = False
    for entry in allowed_users:
        parsed = _parse_entry(entry)
        if parsed is None:
            continue
        user, password_hash, kind = parsed
        if hmac.compare_digest(_encode(user), _encode(username)):
            matched = True
            if _password_matches(password, password_hash, kind):
                return True
    if not matched:
        # an unknown username takes as long as a known one with a wrong password
        _verify_argon2(_DUMMY_HASH, password)
    return False


def check_allowed_users(allowed_users, source):
    """Log the entries of allowed_users that can't log in or use a deprecated MD5 digest.

    Called once when a server starts with basic authentication enabled.

    :param source: name of the module the users come from, for the log messages
    """
    for entry in allowed_users:
        parsed = _parse_entry(entry)
        if parsed is None:
            logging.warning("%s: an entry of allowed_users is not a pair of strings (username, password_hash) and "
                            "is ignored.", source)
            continue
        user, _, kind = parsed
        if kind == "md5":
            logging.warning("%s: the password of user %r is stored as MD5 digest, which can be cracked quickly. "
                            "Replace it by an argon2 hash from 'python -m mslib.utils.basic_auth'.", source, user)
        elif kind is None:
            logging.warning("%s: user %r has no valid password hash and can't log in. "
                            "Create one with 'python -m mslib.utils.basic_auth'.", source, user)


def check_basic_auth_setting(settings, source):
    """Refuse settings that spell ENABLE_BASIC_HTTP_AUTHENTICATION in lower case.

    Flask only reads upper case settings. A server whose settings say ``enable_basic_http_authentication = True``,
    as earlier samples did, would run without any login.

    :param settings: the settings object or module
    :param source: name of the settings module, for the message
    :raises BasicAuthSettingError: if the lower case name is set
    """
    if hasattr(settings, BASIC_AUTH_SETTING.lower()):
        message = (f"{source} sets '{BASIC_AUTH_SETTING.lower()}', which is ignored, so the server would run "
                   f"without login. Rename it to '{BASIC_AUTH_SETTING}'.")
        logging.error(message)
        raise BasicAuthSettingError(message)


def main():
    password = getpass.getpass("Password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"The password needs at least {MIN_PASSWORD_LENGTH} characters.", file=sys.stderr)
        sys.exit(1)
    if password != getpass.getpass("Repeat the password: "):
        print("The passwords differ.", file=sys.stderr)
        sys.exit(1)
    print(hash_password(password))


if __name__ == "__main__":
    main()
