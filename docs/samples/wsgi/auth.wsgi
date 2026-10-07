# Checks the basic authentication of Apache (WSGIAuthUserScript) with the users of mswms_auth.
#
# Apache runs this script in its own Python, not in the environment of the MSS daemon process, so it only
# uses the standard library and argon2 (pip install argon2-cffi, or the python3-argon2 package of your
# system). It accepts the same entries as MSWMS: argon2 hashes from 'python -m mslib.utils.basic_auth',
# and, deprecated, MD5 digests.
import hashlib
import hmac
import secrets
import sys

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

sys.path.extend(['/home/mss/INSTANCE/config'])

import mswms_auth  # noqa: E402

_HASHER = PasswordHasher()
# checked for an unknown username, so that it takes as long as a known one
_DUMMY_HASH = _HASHER.hash(secrets.token_urlsafe(16))


def _matches(password, password_hash):
    if password_hash.startswith("$argon2") and password_hash.isascii():
        try:
            return _HASHER.verify(password_hash, password)
        except (VerificationError, InvalidHashError, UnicodeError, ValueError, TypeError):
            return False
    if len(password_hash) == 32:
        return hmac.compare_digest(hashlib.md5(password.encode("utf-8")).hexdigest(), password_hash.lower())
    return False


def check_password(environ, username, password):
    # mod_wsgi passes the user and the password decoded as ISO-8859-1; browsers send UTF-8
    try:
        username = username.encode("latin-1").decode("utf-8")
        password = password.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return False
    for user, password_hash in mswms_auth.allowed_users:
        if hmac.compare_digest(user.encode("utf-8"), username.encode("utf-8")):
            return _matches(password, password_hash)
    _matches(password, _DUMMY_HASH)
    return False
