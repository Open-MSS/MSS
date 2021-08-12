"""
    mss.tutorials.tutorial_performancesettings
    ~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to change the performance of flight track in table
    view such as managing fuel capacity, etc.
    This file is part of mss.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
import multiprocessing
import sys
import os.path
from sys import platform

from pyscreeze import ImageNotFoundException

from tutorials import screenrecorder as sr
from mslib.msui import mss_pyui


def initial_ops():
    """
    Executes the initial operations such as closing all opened windows and showing the desktop.
    """
    pag.sleep(5)
    if platform == "linux" or platform == "linux2":
        pag.hotkey('winleft', 'd')
        print("\n INFO : Automation is running on Linux system..\n")
    elif platform == "darwin":
        pag.hotkey('option', 'command', 'm')
        print("\n INFO : Automation is running on Mac OS..\n")
    elif platform == "win32":
        pag.hotkey('win', 'd')
        print("\nINFO : Automation is running on Windows OS..\n")
    else:
        pag.alert(text="Sorry, no support on this platform!", title="Platform Exception", button='OK')


def call_recorder():
    """
    Calls the screen recorder class to start the recording of the automation.
    """
    rec = sr.ScreenRecorder(80, 80, int(pag.size()[0]) - 400, int(pag.size()[1]) - 150)
    rec.capture()
    rec.stop_capture()


def call_mss():
    """
    Calls the main MSS GUI window since operations are to be performed on it only.
    """
    mss_pyui.main()


def automate_performance():
    """
    This is the main automating script of the performance settings of table view tutorial which will be recorded and
    saved to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    # Platform specific things
    if platform == 'linux' or platform == 'linux2':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/linux/'
        ps_path = 'pictures/performance_settings/linux/'
        win = 'winleft'
        ctrl = 'ctrl'
    elif platform == 'win32':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/win32/'
        ps_path = 'pictures/performance_settings/linux/'
        win = 'win'
        ctrl = 'ctrl'
    elif platform == 'darwin':
        enter = 'return'
        wms_path = 'pictures/tutorial_wms/linux/'
        ps_path = 'pictures/performance_settings/linux/'
        ctrl = 'command'

    # Satellite Predictor file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    ps_file_path = os.path.join(path, 'docs/samples/config/mss/performance_simple.json')

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
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        # Relocating the table view window
        pag.moveTo(x, y - 462, duration=1)
        if platform == 'linux' or platform == 'linux2':
            pag.dragRel(10, 100, duration=3)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(10, 10, duration=2)
        pag.sleep(2)
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.press('down', presses=2, interval=1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control\' button/option not found on the screen.")

    # Exploring through the file system and loading the performance settings json file for a dummy aircraft.
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}select.png')
        pag.click(x, y, duration=2)
        pag.sleep(1)
        pag.typewrite(ps_file_path, interval=0.1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select\' button (for loading performance_settings.json file) not found on the screen.")

    # Checking the Show Performance checkbox to display the settings file in the table view
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}show_performance.png')
        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Show Performance\' checkbox not found on the screen.")

    # Changing the maximum take off weight
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}maximum_takeoff_weight.png')
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

    # Changing the aircraft weight of the dummy aircraft
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}aircraft_weight.png')
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

    # Changing the take off time of the dummy aircraft
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}take_off_time.png')
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

    # Showing and hiding the performance settings
    try:
        x, y = pag.locateCenterOnScreen(f'{ps_path}show_performance.png')
        pag.click(x, y, duration=2)
        pag.sleep(3)

        pag.click(x, y, duration=2)
        pag.sleep(3)

        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Show Performance\' checkbox not found on the screen.")

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    try:
        if platform == 'linux' or platform == 'linux2':
            for _ in range(2):
                pag.hotkey('altleft', 'f4')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('enter')
                pag.sleep(2)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('left')
            pag.keyUp('altleft')
            pag.press('q')
        if platform == 'win32':
            for _ in range(2):
                pag.hotkey('alt', 'f4')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('enter')
                pag.sleep(2)
            pag.hotkey('alt', 'tab')
            pag.press('q')
        elif platform == 'darwin':
            for _ in range(2):
                pag.hotkey('command', 'w')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('return')
                pag.sleep(2)
            pag.hotkey('command', 'tab')
            pag.press('q')
    except Exception:
        print("Cannot automate : Enable Shortcuts for your system or try again")


def main():
    """
    This function runs the above functions as different processes at the same time and can be
    controlled from here. (This is the main process.)
    """
    p1 = multiprocessing.Process(target=call_mss)
    p2 = multiprocessing.Process(target=automate_performance)
    p3 = multiprocessing.Process(target=call_recorder)

    print("\nINFO : Starting Automation.....\n")
    p3.start()
    pag.sleep(3)
    initial_ops()
    p1.start()
    p2.start()

    p2.join()
    p1.join()
    p3.join()
    print("\n\nINFO : Automation Completes Successfully!")
    sys.exit()


if __name__ == '__main__':
    main()
