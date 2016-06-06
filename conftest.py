# Copyright: 2016 ReimarBauer
# License: APACHE-2.0, see LICENSE for details.


import py
import sys
import os

MSS_PATH = py.path.local(__file__).dirname
sys.path.extend([os.path.join(MSS_PATH, 'thirdparty')])
