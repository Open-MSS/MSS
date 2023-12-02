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
from tutorials.utils import start, create_tutorial_images
from tutorials.utils.platform_keys import platform_keys
from tutorials.utils.picture import picture


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
            pag.hotkey('winleft', 'pageup')
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
    # lets create our helper images
    create_tutorial_images()

    # Locating Server Layer
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-server-layer.png'))
        pag.click(x, y, interval=2)
        if platform == 'win32':
            pag.move(35, -485, duration=1)
            pag.dragRel(-800, -60, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.move(35, -522, duration=1)
            pag.dragRel(650, -30, duration=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Server\\Layers\' button/option not found on the screen.")
        raise
    # lets create our helper images
    create_tutorial_images()

    # Entering wms URL
    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-http-localhost-8081.png'))
        pag.click(x - 220, y + 10)
        pag.hotkey('ctrl', 'a', interval=1)
        pag.write('http://open-mss.org/', interval=0.25)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'WMS URL\' editbox button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-get-capabilities.png'))
        pag.click(x, y, interval=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Get capabilities\' button/option not found on the screen.")
        raise
    # lets create our helper images
    create_tutorial_images()

    # lookup layer entry from the multilayering checkbox
    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-multilayering.png'))
        # Divergence and Geopotential
        pag.click(x + 50, y + 70, interval=2)
        pag.sleep(1)
        # Relative Huminidity
        pag.click(x + 50, y + 110, interval=2)
        pag.sleep(1)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering \' checkbox not found on the screen.")
        raise

    # Filter layer
    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-layer-filter.png'))
        pag.click(x + 150, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Layer filter editbox\' button/option not found on the screen.")
        raise

    if x is not None and y is not None:
        pag.write('temperature', interval=0.25)
        pag.click(interval=2)
        pag.sleep(1)

        # lets create our helper images
        create_tutorial_images()
        # clear by clicking on the red X
        try:
            pic = picture('multilayersdialog-temperature.png', boundingbox=(627, 0, 657, 20))
            x, y = pag.locateCenterOnScreen(pic)
            pag.click(x, y, interval=2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : \'Layer filter editbox\' button/option not found on the screen.")
            raise

    # star two layers
    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-multilayering.png'))
        # Divergence and Geopotential
        pag.click(x, y + 70, interval=2)
        pag.sleep(1)
        # Relative Huminidity
        pag.click(x, y + 110, interval=2)
        pag.sleep(1)

    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering \' checkbox not found on the screen.")
        raise

    # Filtering starred layers.
    try:
        pic = picture('multilayersdialog-temperature.png', boundingbox=(658, 2, 677, 18))
        x, y = pag.locateCenterOnScreen(pic)
        pag.click(x, y, interval=2)
        pag.sleep(2)

        # removing starred selection showing full list
        pag.click(x, y, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Starred filter\' button/option not found on the screen.")
        raise

    # Setting different levels and valid time
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-level.png'))
        pag.click(x + 200, y, interval=2)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Pressure level\' button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-initialisation.png'))
        initx, inity = x, y
        pag.click(x + 200, y, interval=1)
        pag.sleep(1)
        pag.click(x + 200, y, interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Initialization\' button/option not found on the screen.")
        raise
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-valid.png'))
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
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-auto-update.png'))
        pag.click(x - 53, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' auto update checkbox\' button/option not found on the screen.")
        raise

    try:
        retx, rety = pag.locateCenterOnScreen(picture('topviewwindow-retrieve.png'))
        pag.click(retx, rety, interval=2)
        # pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.click(retx, rety, interval=2)
        pag.sleep(3)
        pag.click(x - 53, y, interval=2)
        # pag.click(temp1, temp2, interval=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\' retrieve\' button/option not found on the screen.")
        raise

    # Using and not using Cache
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-use-cache.png'))
        pag.click(x - 46, y, interval=2)
        # pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        # pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.sleep(4)
        pag.click(x - 46, y, interval=2)
        # pag.click(temp1, temp2 + (gap * 2), interval=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Use Cache checkbox\' button/option not found on the screen.")
        raise

    # Clearing cache. The layers load slower
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-clear-cache.png'))
        pag.click(x, y, interval=2)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
        # pag.click(temp1, temp2, interval=2)
        pag.sleep(4)
        # pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.sleep(4)
        # pag.click(temp1, temp2 + (gap * 2), interval=2)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Clear cache\' button/option not found on the screen.")
        raise

    # transparent layer
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-transparent.png'))
        pag.click(x - 53, y, interval=2)
        if retx is not None and rety is not None:
            pag.click(retx, rety, interval=2)
            pag.sleep(1)
            pag.click(x - 53, y, interval=2)
            # pag.click(temp1, temp2, interval=2)
            pag.click(retx, rety, interval=2)
            pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")
        raise

    # Removing a Layer from the map
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-remove.png'))
        pag.click(x, y, interval=2)
        pag.sleep(1)
        # pag.click(temp1, temp2 + (gap * 4), interval=2)
        pag.click(x, y, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Transparent Checkbox\' button/option not found on the screen.")
        raise

    # Deleting All layers
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-server-layer.png'))
        pag.click(x, y, interval=2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Server\\Layers\' button/option not found on the screen.")
        raise

    try:
        x, y = pag.locateCenterOnScreen(picture('multilayersdialog-multilayering.png'))
        # Divergence and Geopotential
        pag.click(x - 16, y + 50, interval=2)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : \'Multilayering \' checkbox not found on the screen.")
        raise


if __name__ == '__main__':
    start(target=automate_waypoints, duration=280)
