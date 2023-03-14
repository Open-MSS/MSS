"""
    msui.tutorials.tutorial_wms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the web map service section of Mission
    Support System and plan flighttracks accordingly.

    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2023 by the MSS team, see AUTHORS.
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

from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils import platform_keys, start, finish
from tutorials.pictures import picture


def automate_waypoints():
    """
    This is the main automating script of the MSS web map service tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    ctrl, enter, win, alt = platform_keys()

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
        raise
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(1)

    # Locating Server Layer
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'layers.png'))
        pag.click(x, y, interval=2)
        if platform == 'win32':
            pag.move(35, -485, duration=1)
            pag.dragRel(-800, -60, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.move(35, -522, duration=1)
            pag.dragRel(950, -30, duration=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Server\\Layers\' button/option not found on the screen.")
        raise

    # Entering wms URL
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'wms_url.png'))
        pag.click(x + 220, y, interval=2)
        pag.hotkey('ctrl', 'a', interval=1)
        pag.write('http://open-mss.org/', interval=0.25)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'WMS URL\' editbox button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'get_capabilities.png'))
        pag.click(x, y, interval=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Get capabilities\' button/option not found on the screen.")
        raise

    # Selecting some layers
    if platform == 'win32':
        gap = 22
    elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        gap = 18

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'equivalent_layer.png'))
        pag.click(x, y, interval=2)
        x, y = pag.locateCenterOnScreen(picture('wms', 'divergence_layer.png'))
        temp1, temp2 = x, y
        pag.click(x, y, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence Layer\' option not found on the screen.")
        raise

    # Filter layer
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'layer_filter.png'))
        pag.click(x + 150, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Layer filter editbox\' button/option not found on the screen.")
        raise

    if x is not None and y is not None:
        pag.write('temperature', interval=0.25)
        pag.moveTo(temp1, temp2, duration=1)
        pag.click(interval=2)
        pag.sleep(1)

        # Clearing filter
        pag.moveTo(x + 150, y, duration=1)
        pag.click(interval=1)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('backspace', presses=11, interval=0.25)
        elif platform == 'darwin':
            pag.press('delete', presses=11, interval=0.25)
        pag.sleep(1)

    # Multilayering
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'multilayering.png'))
        pag.moveTo(x, y, duration=2)
        # pag.move(-48, None)
        pag.click()
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering Checkbox\' button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'checkbox_unselected_divergence.png'))
        if platform == 'win32':
            pag.moveTo(x - 268, y, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.moveTo(x - 55, y, duration=2)
        pag.click(interval=1)
        pag.moveTo(x - 55, y + 30, duration=2)
        pag.click(interval=1)
        pag.sleep(2)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence layer multilayering checkbox\' option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'multilayering.png'))
        pag.moveTo(x, y, duration=2)
        # pag.move(-48, None)
        pag.click()
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering Checkbox\' button/option not found on the screen.")
        raise

    # Starring the layers
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'equivalent_layer.png'))
        pag.moveTo(x, y, duration=2)
        pag.click(interval=1)
        x, y = pag.locateCenterOnScreen(picture('wms', 'divergence_layer.png'))
        if platform == 'win32':
            pag.moveTo(x - 255, y, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.moveTo(x - 100, y, duration=2)
        pag.click(interval=1)
        pag.sleep(1)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Divergence layer star\' button/option not found on the screen.")
        raise

    # Filtering starred layers.
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'star_filter.png'))
        pag.click(x, y, interval=2)
        pag.click(temp1, temp2, duration=1)
        pag.sleep(1)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Starred filter\' button/option not found on the screen.")
        raise

    # removind Filtering starred layers
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'unstar_filter.png'))
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, interval=1)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Unstarred filter\' button/option not found on the screen.")
        raise

    # Setting different levels and valid time
    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2 + (gap * 4), interval=2)
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'level.png'))
        pag.click(x + 200, y, interval=2)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Pressure level\' button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'initialization.png'))
        initx, inity = x, y
        pag.click(x + 200, y, interval=1)
        pag.sleep(1)
        pag.click(x + 200, y, interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Initialization\' button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'valid.png'))
        validx, validy = x, y
        pag.click(x + 200, y, interval=2)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Valid till\' button/option not found on the screen.")
        raise

    # Time gap for initialization and valid
    if initx is not None and inity is not None and validx is not None and validy is not None:
        pag.click(initx + 818, inity, interval=2)
        pag.press('up', presses=5, interval=0.25)
        pag.press('down', presses=3, interval=0.25)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter')
        elif platform == 'darwin':
            pag.press('return')

        pag.click(validx + 833, validy, interval=2)
        pag.press('up', presses=5, interval=0.20)
        pag.press('down', presses=6, interval=0.20)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter')
        elif platform == 'darwin':
            pag.press('return')

        # Previous and Next of Initial(Initialization) values
        pag.click(initx + 733, inity, clicks=2, interval=2)
        pag.click(initx + 892, inity, clicks=2, interval=2)

        # Previous and Next of Valid values
        pag.click(validx + 743, validy, clicks=4, interval=4)
        pag.click(validx + 902, validy, clicks=4, interval=4)

    # Auto-update feature of wms
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'auto_update.png'))
        pag.click(x - 53, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' auto update checkbox\' button/option not found on the screen.")
        raise

    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2, interval=1)
        try:
            retx, rety = pag.locateCenterOnScreen(picture('wms', 'retrieve.png'))
            pag.click(retx, rety, interval=2)
            pag.sleep(3)
            pag.click(temp1, temp2 + (gap * 4), interval=2)
            pag.click(retx, rety, interval=2)
            pag.sleep(3)
            pag.click(x - 53, y, interval=2)
            pag.click(temp1, temp2, interval=2)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\' retrieve\' button/option not found on the screen.")
            raise

    # Using and not using Cache
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'use_cache.png'))
        pag.click(x - 46, y, interval=2)
        pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.sleep(4)
        pag.click(x - 46, y, interval=2)
        pag.click(temp1, temp2 + (gap * 2), interval=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Use Cache checkbox\' button/option not found on the screen.")
        raise

    # Clearing cache. The layers load slower
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'clear_cache.png'))
        pag.click(x, y, interval=2)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
        pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.sleep(4)
        pag.click(temp1, temp2 + (gap * 2), interval=2)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Clear cache\' button/option not found on the screen.")
        raise

    # rent layer
    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2, interval=2)
        pag.sleep(1)
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'transparent.png'))
        pag.click(x - 53, y, interval=2)
        if retx is not None and rety is not None:
            pag.click(retx, rety, interval=2)
            pag.sleep(1)
            pag.click(x - 53, y, interval=2)
            pag.click(temp1, temp2, interval=2)
            pag.click(retx, rety, interval=2)
            pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")
        raise

    # Removing a Layer from the map
    if temp1 is not None and temp2 is not None:
        try:
            x, y = pag.locateCenterOnScreen(picture('wms', 'remove.png'))
            pag.click(x, y, interval=2)
            pag.sleep(1)
            pag.click(temp1, temp2 + (gap * 4), interval=2)
            pag.click(x, y, interval=2)
            pag.sleep(1)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")
            raise
    # Deleting All layers
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'delete_layers.png'))
        if platform == 'win32':
            pag.click(x - 74, y, interval=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.click(x - 70, y, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Deleting all layers bin\' button/option not found on the screen.")
        raise

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_waypoints, duration=280)
