"""
    mss.tutorials.tutorial_kml
    ~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to overlay kml flles on top of the map in topview.
    kml(key hole markup language) is an XML based file format for demonstrating geographical context. This will
    demonstrate how to customize the kml files and other various operations on it.
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
        print("\n INFO : Automation is running on Windows OS..\n")
    else:
        pag.alert(text="Sorry, no support on this platform!", title="Platform Exception", button='OK')


def call_recorder():
    """
    Calls the screen recorder class to start the recording of the automation.
    """
    rec = sr.ScreenRecorder(80, 20, int(pag.size()[0] / 1.5), int(pag.size()[1] - 100))
    rec.capture()
    rec.stop_capture()


def call_mss():
    """
    Calls the main MSS GUI window since operations are to be performed on it only.
    """
    mss_pyui.main()


def automate_kml():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    # Platform specific things
    if platform == 'linux' or platform == 'linux2':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/linux/'
        kml_path = 'pictures/kml_overlay/linux/'
        win = 'winleft'
        ctrl = 'ctrl'
    elif platform == 'win32':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/win32/'
        kml_path = 'pictures/kml_overlay/win32/'
        win = 'win'
        ctrl = 'ctrl'
    elif platform == 'darwin':
        enter = 'return'
        wms_path = 'pictures/tutorial_wms/linux/'
        kml_path = 'pictures/kml_overlay/linux/'
        ctrl = 'command'

    # Satellite Predictor file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    kml_file_path1 = os.path.join(path, 'docs/samples/kml/folder.kml')
    kml_file_path2 = os.path.join(path, 'docs/samples/kml/color.kml')

    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'up')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(3)

    # Opening KML overlay dockwidget
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.press('down', presses=4, interval=1)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control\' button/option not found on the screen.")

    # Removing all the files present
    try:
        x, y = pag.locateCenterOnScreen(f'{kml_path}select_all_files.png')
        pag.sleep(1)
        pag.click(x, y, duration=2)
        pag.sleep(3)
        # Clicking on Remove Files
        try:
            x1, y1 = pag.locateCenterOnScreen(f'{kml_path}remove_files.png')
            pag.sleep(1)
            pag.click(x1, y1, duration=1)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Remove Files\' button not found on the screen.")
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select All Files\' button not found on the screen.")

    # Adding the KML files and loading them
    try:
        x, y = pag.locateCenterOnScreen(f'{kml_path}add_kml_files.png')
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

    # Unselecting and Selecting Files to demonstrate visibility on the map.
    try:
        x, y = pag.locateCenterOnScreen(f'{kml_path}unselect_all_files.png')
        pag.click(x, y, duration=2)
        pag.sleep(2)
        try:
            x1, y1 = pag.locateCenterOnScreen(f'{kml_path}select_all_files.png')
            pag.click(x1, y1, duration=2)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Select All Files(Unselecting & Selecting)\' button not found on the screen.")
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Unselect All Files(Unselecting & Selecting)\' button not found on the screen.")

    # Selecting and Customizing the Folder.kml file
    try:
        x, y = pag.locateCenterOnScreen(f'{kml_path}kmloverlay.png')
        pag.click(x + 100, y + 20, duration=2)
        pag.sleep(4)
        try:
            # Changing color of folder.kml file
            x1, y1 = pag.locateCenterOnScreen(f'{kml_path}changecolor.png')
            pag.click(x1, y1, duration=2)
            pag.sleep(4)
            x2, y2 = pag.locateCenterOnScreen(f'{kml_path}pick_screen_color.png')
            pag.click(x2, y2 - 30, duration=1)
            pag.sleep(3)
            pag.press(enter)
            pag.sleep(4)

            pag.click(x1, y1, duration=2)
            pag.sleep(4)
            x2, y2 = pag.locateCenterOnScreen(f'{kml_path}pick_screen_color.png')
            pag.click(x2 + 20, y2 - 50, duration=1)
            pag.sleep(3)
            pag.press(enter)
            pag.sleep(4)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Change Color (folder.kml)\' button not found on the screen.")
        try:
            # Changing Linewidth of folder.kml file
            x1, y1 = pag.locateCenterOnScreen(f'{kml_path}changecolor.png')
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

        # Selecting and Customizing the color.kml file
        pag.click(x + 100, y + 38, duration=2)
        pag.sleep(2)

        # Changing map to Global
        try:
            if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
                x, y = pag.locateCenterOnScreen('pictures/europe(cyl).PNG')
                pag.click(x, y, interval=2)
            elif platform == 'win32':
                x, y = pag.locateCenterOnScreen('pictures/europe(cyl)win.PNG')
                pag.click(x, y, interval=2)
            pag.press('down', presses=2, interval=0.5)
            pag.press(enter, interval=1)
            pag.sleep(5)
        except (ImageNotFoundException, OSError, Exception):
            print("\n Exception : Map change dropdown could not be located on the screen")

        try:
            # Changing color of color.kml file
            x1, y1 = pag.locateCenterOnScreen(f'{kml_path}changecolor.png')
            pag.click(x1, y1, duration=2)
            pag.sleep(4)
            x2, y2 = pag.locateCenterOnScreen(f'{kml_path}pick_screen_color.png')
            pag.click(x2 - 20, y2 - 50, duration=1)
            pag.sleep(3)
            pag.press(enter)
            pag.sleep(3)

            pag.click(x1, y1, duration=2)
            pag.sleep(4)
            x2, y2 = pag.locateCenterOnScreen(f'{kml_path}pick_screen_color.png')
            pag.click(x2 - 5, y2 - 120, duration=1)
            pag.sleep(3)
            pag.press(enter)
            pag.sleep(4)

            # Changing Linewidth of color.kml file
            pag.click(x1 + 12, y1 + 50, duration=2)
            pag.sleep(4)
            pag.hotkey(ctrl, 'a')
            pag.sleep(1)
            pag.typewrite('6.53', interval=1)
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(3)

            pag.hotkey(ctrl, 'a')
            pag.sleep(1)
            pag.typewrite('3.45', interval=1)
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Change Color(Color.kml file)\' button not found on the screen.")
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'KML Overlay\' fixed text not found on the screen.")

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
    p2 = multiprocessing.Process(target=automate_kml)
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
