# Copyright: 2016 ReimarBauer
# License: APACHE-2.0, see LICENSE for details.


import sys

import os
import py

MSS_PATH = py.path.local(__file__).dirname
sys.path.extend([os.path.join(MSS_PATH, 'mslib', 'thirdparty')])
