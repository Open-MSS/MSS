"""
    msui.tutorials.tutorial_satellitetrack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to work with remote sensing tool in topview.
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
import os.path

from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils import platform_keys, start, finish, create_tutorial_images
from tutorials.utils.picture import picture


def automate_rs():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    ctrl, enter, win, alt = platform_keys()

    # Satellite Predictor file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    satellite_path = os.path.join(path, 'docs/samples/satellite_tracks/satellite_predictor.txt')

    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'pageup')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(3)
    create_tutorial_images()

    # Opening Satellite Track dockwidget
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-select-to-open-control.png'))
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.press('down', presses=2, interval=1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control\' button/option not found on the screen.")
        raise
    # update images
    create_tutorial_images()

    # Loading the file:
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-load.png'))
        pag.sleep(1)
        pag.click(x - 150, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite(satellite_path, interval=0.1)
        pag.sleep(1)
        pag.click(x, y, duration=1)
        pag.press(enter)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Load\' button not found on the screen.")
        raise

    # Switching between different date and time of satellite overpass.
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-predicted-satellite-overpasses.png'))
        pag.click(x + 200, y, duration=1)
        for _ in range(10):
            pag.click(x + 200, y, duration=1)
            pag.sleep(1)
            pag.press('down')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(2)
        pag.click(x + 200, y, duration=1)
        pag.press('up', presses=3, interval=1)
        pag.press(enter)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Predicted Satellite Overpass\' dropdown menu not found on the screen.")
        raise

    # Changing map to global
    try:
        if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            x, y = pag.locateCenterOnScreen(picture('topviewwindow-01-europe-cyl.png'))
            pag.click(x, y, interval=2)
        pag.press('down', presses=2, interval=0.5)
        pag.press(enter, interval=1)
        pag.sleep(5)
    except ImageNotFoundException:
        print("\n Exception : Map change dropdown could not be located on the screen")
        raise

    # Adding waypoints for demonstrating remote sensing
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-ins-wp.png'))
        pag.click(x, y, interval=2)
        pag.move(111, 153, duration=2)
        pag.click(duration=2)
        pag.move(36, 82, duration=2)
        pag.click(duration=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Add waypoint button in topview not found on the screen.")
        raise

    # Zooming into the map
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-zoom.png'))
        pag.click(x, y, interval=2)
        pag.move(260, 130, duration=1)
        pag.dragRel(184, 135, duration=2)
        pag.sleep(5)
    except ImageNotFoundException:
        print("\n Exception : Zoom button could not be located on the screen")
        raise
    pag.sleep(1)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_rs, duration=148)
