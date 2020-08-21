import os
import sys

from mslib.msui.constants import MSS_CONFIG_PATH

sys.path.append(MSS_CONFIG_PATH)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qt5'))

if __name__ == "__main__":
    from mslib.msui.mss_pyui import start_mss
    start_mss()
