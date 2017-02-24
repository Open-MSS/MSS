import sys
sys.path.extend(['/home/mss/config'])

import mss_wms_auth
import hashlib

def check_password(environ, username, password):
    for u, p in mss_wms_auth.allowed_users:
        if (u == username) and (p == hashlib.md5(password).hexdigest()):
           return True
    return False
