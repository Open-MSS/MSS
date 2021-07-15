"""
    mslib.msui.tutorial_wms
    ~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the web map service section of Mission
    Support System and plan flighttracks accordingly.

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
import datetime
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
        print("\n INFO : Automation is running on Windows OS..\n")
    else:
        pag.alert(text="Sorry, no support on this platform!", title="Platform Exception", button='OK')


def call_recorder():
    """
    Calls the screen recorder class to start the recording of the automation.
    """
    sr.main()


def call_mss():
    """
    Calls the main MSS GUI window since operations are to be performed on it only.
    """
    mss_pyui.main()


def automate_waypoints():
    """
    This is the main automating script of the MSS waypoints tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(10)

    # Maximizing the window
    try:
        if platform == 'linux' or platform == 'linux2':
            pag.hotkey('winleft', 'up')
        elif platform == 'darwin':
            pag.hotkey('ctrl', 'command', 'f')
        elif platform == 'win32':
            pag.hotkey('win', 'up')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(5)

    # Opening web map service
    try:
        x, y = pag.locateCenterOnScreen('pictures/selecttoopencontrol.PNG')
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' select to open control\' button/option not found on the screen.")
    pag.press('down', interval=1)
    if platform == 'linux' or platform == 'linux2' or platform == 'win32':
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.press('return', interval=1)
    pag.move(None, -777, duration=1)
    pag.dragRel(400, None, duration=2)

    # Locating Server Layer
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/layers.png')
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Server\\Layers\' button/option not found on the screen.")
    pag.move(35, -485, duration=1)
    pag.dragRel(-800, -60, duration=2)
    pag.sleep(1)

    # Entering wms URL
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/wms_url.png')
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'WMS URL\' editbox button/option not found on the screen.")
    pag.hotkey('ctrl', 'a', interval=1)
    pag.write('http://open-mss.org/', interval=0.25)
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/get_capabilities.png')
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Get capabilities\' button/option not found on the screen.")
    pag.sleep(3)

    # Selecting some layers
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/divergence_layer.png')
        temp1, temp2 = x, y
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence Layer\' option not found on the screen.")
    pag.sleep(1)
    pag.move(None, 22, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, 44, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, 22, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, -88, duration=1)
    pag.click(interval=1)
    pag.sleep(1)

    # Filter layer
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/layer_filter.png')
        pag.click(x+60, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Layer filter editbox\' button/option not found on the screen.")
    pag.write('temp', interval=0.25)
    pag.move(None, 81, duration=1)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(None, 22, duration=1)
    pag.click(interval=2)
    pag.sleep(1)

    # Clearing filter
    pag.move(30, -104, duration=1)
    pag.click(interval=1)
    if platform == 'linux' or platform == 'linux2' or platform == 'win32':
        pag.press('backspace', presses=4, interval=0.25)
    elif platform == 'darwin':
        pag.press('delete', presses=4, interval=0.25)
    pag.sleep(1)

    # Multilayering
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/multilayering.png')
        pag.moveTo(x, y, duration=2)
        pag.move(-48, None)
        pag.click()
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering Checkbox\' button/option not found on the screen.")
    pag.sleep(1)
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/divergence_layer.png')
        pag.moveTo(x-268, y, duration=2)
        pag.click(interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence layer multilayering checkbox\' option not found on the screen.")
    pag.sleep(2)
    pag.move(None, 88, duration=1)
    pag.click(interval=1)
    pag.sleep(2)
    pag.move(None, -88, duration=1)
    pag.click(interval=1)
    pag.sleep(2)
    pag.move(None, 88, duration=1)
    pag.click(interval=1)
    pag.sleep(2)
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/multilayering.png')
        pag.moveTo(x, y, duration=2)
        pag.move(-48, None)
        pag.click()
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering Checkbox\' button/option not found on the screen.")
    pag.sleep(1)

    # Starring the layers
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/divergence_layer.png')
        pag.moveTo(x-255, y, duration=2)
        pag.click(interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence layer star\' button/option not found on the screen.")
    pag.sleep(1)
    pag.move(None, 88, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, -22, duration=1)
    pag.click(interval=1)
    pag.sleep(1)

    # Filtering starred layers.
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/star_filter.png')
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Starred filter\' button/option not found on the screen.")
    pag.move(-50, 80, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, 22, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(None, 22, duration=1)
    pag.click(interval=1)
    pag.sleep(1)
    pag.move(20, -133, duration=1)
    pag.click(interval=1)
    pag.sleep(1)

    # Setting different levels and valid time
    pag.click(temp1, temp2 + 88, interval=2)
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/level.png')
        pag.click(x+200, y, interval=2)
        pag.move(None, 20, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.click(x + 200, y, interval=1)
        pag.move(None, 100, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.click(x + 200, y, interval=1)
        pag.move(None, 140, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Pressure level\' button/option not found on the screen.")


    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/initialization.png')
        initx, inity = x, y
        pag.click(x+200, y, interval=1)
        pag.sleep(1)
        pag.click(x+200, y, interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Initialization\' button/option not found on the screen.")

    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/valid.png')
        validx, validy = x, y
        pag.click(x+200, y, interval=2)
        pag.move(None, 20, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.click(x + 200, y, interval=1)
        pag.move(None, 80, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Valid till\' button/option not found on the screen.")

    # Time gap for initialization and valid
    pag.click(initx+818, inity, interval=2)
    pag.press('up', presses=5, interval=0.25)
    pag.press('down', presses=3, interval=0.25)
    pag.press('enter') if platform == 'linux' or platform == 'linux2' or platform == 'win32' else pag.press('return')

    pag.click(validx+833, validy, interval=2)
    pag.press('up', presses=5, interval=0.20)
    pag.press('down', presses=6, interval=0.20)
    pag.press('enter') if platform == 'linux' or platform == 'linux2' or platform == 'win32' else pag.press('return')

    # Previous and Next of Initial(Initialization) values
    pag.click(initx + 753, inity, clicks=2, interval=2)
    pag.click(initx + 882, inity, clicks=2, interval=2)

    # Previous and Next of Valid values
    pag.click(validx+760, validy, clicks=4, interval=2)
    pag.click(validx+884, validy, clicks=4, interval=2)

    # Auto-update feature of wms
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/auto_update.png')
        pag.click(x-53, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' auto update checkbox\' button/option not found on the screen.")
    pag.click(temp1, temp2, interval=1)
    try:
        retx, rety = pag.locateCenterOnScreen('pictures/tutorial_wms/retrieve.png')
        pag.click(retx, rety, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' retrieve\' button/option not found on the screen.")
    pag.sleep(3)
    pag.click(temp1, temp2+88, interval=2)
    pag.click(retx, rety, interval=2)
    pag.sleep(3)
    pag.click(x-53, y, interval=2)
    pag.click(temp1, temp2, interval=2)
    pag.sleep(2)

    # Using and not using Cache
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/use_cache.png')
        pag.click(x-46, y, interval=2)
        pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2+88, interval=2)
        pag.sleep(4)
        pag.click(x - 46, y, interval=2)
        pag.click(temp1, temp2 + 44, interval=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Use Cache checkbox\' button/option not found on the screen.")

    # Clearing cache. The layers load slower
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/clear_cache.png')
        pag.click(x, y, interval=2)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
        pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2+88, interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2 + 44, interval=2)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Clear cache\' button/option not found on the screen.")

    # Transparent layer
    pag.click(temp1, temp2, interval=2)
    pag.sleep(1)
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/transparent.png')
        pag.click(x-53, y, interval=2)
        pag.click(retx, rety, interval=2)
        pag.sleep(1)
        pag.click(x - 53, y, interval=2)
        pag.click(temp1, temp2, interval=2)
        pag.click(retx, rety, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")

    # Removing a Layer from the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/remove.png')
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.click(temp1, temp2+88, interval=2)
        pag.click(x, y, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")

    # Deleting All layers
    try:
        x, y = pag.locateCenterOnScreen('pictures/tutorial_wms/delete_layers.png')
        pag.click(x-74, y, interval=2)
        pag.sleep(1)
        x1, y1 = pag.locateCenterOnScreen('pictures/tutorial_wms/get_capabilities.png')
        pag.click(x1, y1, interval=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Deleting all layers bin\' button/option not found on the screen.")

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    try:
        if platform == 'linux' or platform == 'linux2':
            pag.hotkey('altleft', 'f4', interval=1)
            for _ in range(2):
                pag.hotkey('altleft', 'f4')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('enter')
                pag.sleep(1)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('left')
            pag.keyUp('altleft')
            pag.press('q')
        if platform == 'win32':
            pag.hotkey('alt', 'f4', interval=1)
            for _ in range(2):
                pag.hotkey('alt', 'f4')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('enter')
                pag.sleep(1)
            pag.hotkey('alt', 'tab')
            pag.press('q')
        elif platform == 'darwin':
            pag.hotkey('command', 'w', interval=1)
            for _ in range(2):
                pag.hotkey('command', 'w')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('return')
                pag.sleep(1)
            pag.hotkey('command', 'tab')
            pag.press('q')
    except Exception:
        print("Cannot automate : Enable Shortcuts for your system or try again")
    pag.press('q')


def main():
    """
    This function runs the above functions as different processes at the same time and can be
    controlled from here. (This is the main process.)
    """
    p1 = multiprocessing.Process(target=call_mss)
    p2 = multiprocessing.Process(target=automate_waypoints)
    p3 = multiprocessing.Process(target=call_recorder)

    print("\nINFO : Starting Automation.....\n")
    p3.start()
    pag.sleep(5)
    initial_ops()
    p1.start()
    p2.start()

    p2.join()
    p1.join()
    p3.join()
    print("\n\nINFO : Automation Completes Successfully!")
    pag.press('q')
    sys.exit()


if __name__ == '__main__':
    main()
