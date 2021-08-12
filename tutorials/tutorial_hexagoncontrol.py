"""
    mss.tutorials.tutorial_hexagoncontrol.py
    ~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to create a hexagon flightrack with the waypoints.
    Placing a centre waypoint, how we can draw a perfect hexagon flight path around it with variable radius of
    hexagon and variable angle of first waypoint of the hexagon.
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
    rec = sr.ScreenRecorder(80, 20, pag.size()[0], pag.size()[1] - 150)
    rec.capture()
    rec.stop_capture()


def call_mss():
    """
    Calls the main MSS GUI window since operations are to be performed on it only.
    """
    mss_pyui.main()


def automate_hexagoncontrol():
    """
    This is the main automating script of the MSS hexagon control of table view which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    # Platform specific things
    if platform == 'linux' or platform == 'linux2':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/linux/'
        hc_path = 'pictures/hexagon_control/linux/'
        win = 'winleft'
        ctrl = 'ctrl'
    elif platform == 'win32':
        enter = 'enter'
        wms_path = 'pictures/tutorial_wms/win32/'
        hc_path = 'pictures/hexagon_control/linux/'
        win = 'win'
        ctrl = 'ctrl'
    elif platform == 'darwin':
        enter = 'return'
        wms_path = 'pictures/tutorial_wms/linux/'
        hc_path = 'pictures/hexagon_control/linux/'
        ctrl = 'command'

    # Screen Resolutions
    sc_width, sc_height = pag.size()[0] - 1, pag.size()[1] - 1

    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'up')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(3)

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

    # Zooming into the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/zoom.PNG')
        pag.click(x, y, interval=2)
        pag.move(379, 205, duration=1)
        pag.dragRel(70, 75, duration=2)
        pag.sleep(5)
    except ImageNotFoundException:
        print("\n Exception : Zoom button could not be located on the screen")

    # Opening TableView
    pag.move(500, None, duration=1)
    pag.click(duration=1)
    pag.sleep(1)
    pag.hotkey('ctrl', 't')
    pag.sleep(3)

    # Relocating Tableview by performing operations on table view
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        pag.moveTo(x, y - 462, duration=1)
        if platform == 'linux' or platform == 'linux2':
            pag.dragRel(649, 887, duration=3)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(200, 487, duration=2)
        pag.sleep(2)
        if platform == 'linux' or platform == 'linux2':
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('altleft')
        elif platform == 'win32':
            pag.keyDown('alt')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('alt')
        elif platform == 'darwin':
            pag.keyDown('command')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('command')
        pag.sleep(1)
        if platform == 'win32' or platform == 'darwin':
            pag.dragRel(None, -700, duration=2)
            tv_x, tv_y = pag.position()
        elif platform == 'linux' or platform == 'linux2':
            pag.dragRel(None, -850, duration=2)
            tv_x, tv_y = pag.position()
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : TableView's Select to open Control option not found on the screen.")

    # Opening Hexagon Control dockwidget
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png', region=(int(sc_width / 2) - 350,
                                                                                      0, int(sc_width / 2), sc_height))
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'select to open control(table view)\' button/option not found on the screen.")

    # Entering Centre Latitude and Centre Longitude of Delhi around which hexagon will be drawn
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}center_latitude.png')
        pag.sleep(1)
        pag.click(x + 370, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('28.57', interval=0.3)
        pag.sleep(1)
        pag.press(enter)

        pag.sleep(1)
        pag.click(x + 943, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('77.10', interval=0.3)
        pag.sleep(1)
        pag.press(enter)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Center Latitude\' button not found on the screen.")

    # Clicking on the add hexagon button
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}add_hexagon.png')
        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Add Hexagon\' button not found on the screen.")

    # Changing the Radius of the hexagon
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}radius.png')
        pag.click(x + 400, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('500.00', interval=0.3)
        pag.sleep(1)
        pag.press(enter)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Radius\' button not found on the screen.")

    # Clicking on the Remove Hexagon Button
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}remove_hexagon.png')
        pag.click(x, y, duration=2)
        pag.sleep(2)
        pag.press('left')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Remove Hexagon\' button not found on the screen.")

    # Clicking on the add hexagon button
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}add_hexagon.png')
        pag.click(x, y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Add Hexagon\' button not found on the screen.")

    # Changing the angle of first point of the hexagon
    try:
        x, y = pag.locateCenterOnScreen(f'{hc_path}radius.png')
        pag.sleep(1)
        pag.click(x + 967, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('90.00', interval=0.3)
        pag.sleep(1)
        pag.press(enter)

        # Clicking on the Remove Hexagon Button
        try:
            x, y = pag.locateCenterOnScreen(f'{hc_path}remove_hexagon.png')
            pag.click(x, y, duration=2)
            pag.sleep(2)
            pag.press('left')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Remove Hexagon\' button not found on the screen.")

        # Clicking on the add hexagon button
        try:
            x, y = pag.locateCenterOnScreen(f'{hc_path}add_hexagon.png')
            pag.click(x, y, duration=2)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Add Hexagon\' button not found on the screen.")

        # Changing to a different angle of first point
        x, y = pag.locateCenterOnScreen(f'{hc_path}radius.png')
        pag.sleep(1)
        pag.click(x + 967, y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.typewrite('120.00', interval=0.3)
        pag.sleep(1)
        pag.press(enter)

        # Clicking on the Remove Hexagon Button
        try:
            x, y = pag.locateCenterOnScreen(f'{hc_path}remove_hexagon.png')
            pag.click(x, y, duration=2)
            pag.sleep(2)
            pag.press('left')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Remove Hexagon\' button not found on the screen.")

        # Clicking on the add hexagon button
        try:
            x, y = pag.locateCenterOnScreen(f'{hc_path}add_hexagon.png')
            pag.click(x, y, duration=2)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Add Hexagon\' button not found on the screen.")
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Radius (for Angle of first point)\' button not found on the screen.")

    pag.moveTo(tv_x, tv_y, duration=2)
    pag.click(duration=2)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    try:
        if platform == 'linux' or platform == 'linux2':
            for _ in range(3):
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
            for _ in range(3):
                pag.hotkey('alt', 'f4')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('enter')
                pag.sleep(2)
            pag.hotkey('alt', 'tab')
            pag.press('q')
        elif platform == 'darwin':
            for _ in range(3):
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
    p2 = multiprocessing.Process(target=automate_hexagoncontrol)
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
