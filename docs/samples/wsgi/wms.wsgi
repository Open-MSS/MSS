import os
import sys

sys.path.insert(0, '/home/mss/INSTANCE/config')
sys.path.insert(0, '/home/mss/miniconda3/envs/instance/lib/python3.7/site-packages/mslib')
sys.path.insert(0, '/home/mss/INSTANCE/wsgi')

if os.getenv("PROJ_LIB") is None or os.getenv("PROJ_LIB") == "PROJ_LIB":
    os.environ["PROJ_LIB"] = '/home/mss/miniconda3/envs/instance/share/proj'

sys.stdout = sys.stderr
import logging
logging.basicConfig(stream=sys.stderr)

from mslib.mswms.wms import app as application
