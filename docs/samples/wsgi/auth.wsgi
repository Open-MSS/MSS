import sys
sys.path.extend(['/home/mss/INSTANCE/config'])

import mswms_auth
import hashlib

def check_password(environ, username, password):
    for u, p in mswms_auth.allowed_users:
        if (u == username) and (p == hashlib.md5(password).hexdigest()):
           return True
    return False
