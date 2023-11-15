"""
    msui.tutorials.tutorial_kml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to overlay kml flles on top of the map in topview.
    kml(key hole markup language) is an XML based file format for demonstrating geographical context. This will
    demonstrate how to customize the kml files and other various operations on it.
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
from tutorials.utils import platform_keys, start, finish
from tutorials.pictures import picture


def automate_kml():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    ctrl, enter, win, alt = platform_keys()

    # Satellite Predictor file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    kml_file_path1 = os.path.join(path, 'docs/samples/kml/folder.kml')
    kml_file_path2 = os.path.join(path, 'docs/samples/kml/color.kml')

    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'pageup')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")

    pag.hotkey('ctrl', 'h')
    pag.sleep(1)
    # lets create our helper images
    create_tutorial_images()

    # Changing map to Global
    try:
        pic = picture('topviewwindow-01-europe-cyl.png')
        x, y = pag.locateCenterOnScreen(pic)

        pag.click(x, y, interval=2)
        pag.press('down', presses=2, interval=0.5)
        pag.press(enter, interval=1)
        pag.sleep(5)
    except (ImageNotFoundException, OSError, Exception):
        print("\n Exception : Map change dropdown could not be located on the screen")
        raise

    # Opening KML overlay dockwidget
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-select-to-open-control.png'))
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.press('down', presses=4, interval=1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control\' button/option not found on the screen.")

    create_tutorial_images()

    # Adding the KML files and loading them
    try:
        x, y = pag.locateCenterOnScreen(picture('topviewwindow-add-kml-files.png'))
        pag.click(x, y, duration=2)
        pag.sleep(1)
        pag.typewrite(kml_file_path1, interval=0.1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)

        pag.click(x, y, duration=2)
        pag.sleep(1)
        pag.typewrite(kml_file_path2, interval=0.1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Add KML Files\' button not found on the screen.")
        raise

    # Unselecting and Selecting Files to demonstrate visibility on the map.
    try:
        x1, y1 = pag.locateCenterOnScreen(picture('topviewwindow-unselect-all-files.png'))
        pag.click(x1, y1, duration=2)
        pag.sleep(2)
        try:
            x1, y1 = pag.locateCenterOnScreen(picture('topviewwindow-select-all-files.png'))
            pag.click(x1, y1, duration=2)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Select All Files(Unselecting & Selecting)\' button not found on the screen.")
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select All Files(Unselecting & Selecting)\' button not found on the screen.")
        raise
    create_tutorial_images()
    # Selecting and Customizing the Folder.kml file

    pag.move(-200, 0, duration=1)
    pag.click(interval=2)

    try:
        # Changing color of folder.kml file
        x1, y1 = pag.locateCenterOnScreen(picture('topviewwindow-change-color.png'))
        pag.click(x1, y1, duration=2)
        pag.sleep(4)
        pag.move(-220, -300, duration=1)
        pag.click(interval=2)
        pag.press(enter)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Change Color \' button not found on the screen.")
        raise
    try:
        # Changing Linewidth of folder.kml file
        x1, y1 = pag.locateCenterOnScreen(picture('topviewwindow-change-color.png'))
        pag.click(x1 + 12, y1 + 50, duration=2)
        pag.sleep(2)
        pag.hotkey(ctrl, 'a')
        for _ in range(8):
            pag.press('down')
            pag.sleep(3)
        pag.hotkey(ctrl, 'a')
        pag.typewrite('6.50', interval=1)
        pag.press(enter)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Change Color(folder.kml again)\' button not found on the screen.")
        raise

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


def create_tutorial_images():
    pag.hotkey('ctrl', 'f')
    pag.sleep(1)
    pag.hotkey('enter')


if __name__ == '__main__':
    start(target=automate_kml, duration=220)
