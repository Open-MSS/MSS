"""
    msui.tutorials.tutorial_performancesettings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to change the performance of flight track in table
    view such as managing fuel capacity, etc.
    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2022 by the MSS team, see AUTHORS.
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

import pyautogui as pag
import os.path
import tempfile
import shutil

from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils import platform_keys, start, finish
from tutorials.pictures import picture


def automate_performance():
    """
    This is the main automating script of the performance settings of table view tutorial which will be recorded and
    saved to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    ctrl, enter, win, alt = platform_keys()

    # Satellite Predictor file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    ps_file_path = os.path.join(path, 'docs/samples/config/msui/performance_simple.json.sample')
    dirpath = tempfile.mkdtemp()
    sample = os.path.join(dirpath, 'example.json')
    shutil.copy(ps_file_path, sample)

    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'up')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.sleep(2)
    pag.hotkey('ctrl', 't')
    pag.sleep(3)

    # Opening Performance Settings dockwidget
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'selecttoopencontrol.png'))
        pag.moveTo(x + 250, y - 462, duration=1)
        if platform == 'linux' or platform == 'linux2':
            # the window need to be moved a bit below the topview window
            pag.dragRel(400, 387, duration=2)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(200, 487, duration=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control\' button/option not found on the screen.")
        raise

    tv_x, tv_y = pag.position()
    # Opening Hexagon Control dockwidget
    if tv_x is not None and tv_y is not None:
        pag.moveTo(tv_x - 250, tv_y + 462, duration=2)
        pag.click(duration=2)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)

    # Exploring through the file system and loading the performance settings json file for a dummy aircraft.
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'select.png'))
        pag.click(x, y, duration=2)
        pag.sleep(1)
        pag.typewrite(sample, interval=0.1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select\' button (for loading performance_settings.json file) not found on the screen.")
        raise
    # Checking the Show Performance checkbox to display the settings file in the table view
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'show_performance.png'))
        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Show Performance\' checkbox not found on the screen.")
        raise

    # Changing the maximum take off weight
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'maximum_takeoff_weight.png'))
        pag.click(x + 318, y, duration=2)
        pag.sleep(4)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('87000', interval=0.3)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Maximum Takeoff Weight\' fill box not found on the screen.")
        raise
    # Changing the aircraft weight of the dummy aircraft
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'aircraft_weight.png'))
        pag.click(x + 300, y, duration=2)
        pag.sleep(4)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('48000', interval=0.3)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Aircraft weight\' fill box not found on the screen.")
        raise

    # Changing the take off time of the dummy aircraft
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'take_off_time.png'))
        pag.click(x + 410, y, duration=2)
        pag.sleep(4)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        for _ in range(5):
            pag.press('up')
            pag.sleep(2)
        pag.typewrite('04', interval=0.5)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Take off time\' fill box not found on the screen.")
        raise

    # Showing and hiding the performance settings
    try:
        x, y = pag.locateCenterOnScreen(picture('performancesettings', 'show_performance.png'))
        pag.click(x, y, duration=2)
        pag.sleep(3)

        pag.click(x, y, duration=2)
        pag.sleep(3)

        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Show Performance\' checkbox not found on the screen.")
        raise

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_performance)
