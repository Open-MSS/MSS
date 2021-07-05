"""
    mslib.msui.tutorial_waypoints
    ~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to play with and use waypoints
    for activating/creating a flight track.

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


def automate_waypoints(obj=None):
    """
    This is the main automating script of the MSS waypoints tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(15)

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

    # Adding waypoints
    try:
        x, y = pag.locateCenterOnScreen('pictures/add_waypoint.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\nException : Clickable button/option not found on the screen.")
    pag.move(-50, 150, duration=1)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(65, 65, duration=1)
    pag.click(interval=2)
    pag.sleep(1)

    pag.move(-150, 30, duration=1)
    x1, y1 = pag.position()
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(200, 150, duration=1)
    pag.click(interval=2)
    x2, y2 = pag.position()
    pag.sleep(3)

    # Moving waypoints
    try:
        x, y = pag.locateCenterOnScreen('pictures/move_waypoint.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Move Waypoint button could not be located on the screen")

    pag.moveTo(x2, y2, duration=1)
    pag.click(interval=2)
    pag.dragRel(100, 150, duration=1)
    pag.moveTo(x1, y1, duration=1)
    pag.dragRel(35, -50, duration=1)
    x1, y1 = pag.position()

    # Deleting waypoints
    try:
        x, y = pag.locateCenterOnScreen('pictures/remove_waypoint.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Remove Waypoint button could not be located on the screen")
    pag.moveTo(x1, y1, duration=1)
    pag.click(duration=1)
    pag.press('left')
    pag.sleep(3)
    if platform == 'linux' or platform == 'linux2' or platform == 'win32':
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.press('return', interval=1)
    pag.sleep(2)

    # Changing map to Global
    try:
        if platform == 'linux' or 'linux2' or 'darwin':
            x, y = pag.locateCenterOnScreen('pictures/europe(cyl).PNG')
            pag.click(x, y, interval=2)
        elif platform == 'win32':
            x, y = pag.locateCenterOnScreen('pictures/europe(cyl)win.PNG')
            pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Map change dropdown could not be located on the screen")
    pag.press('down', presses=2, interval=0.5)
    if platform == 'linux' or platform == 'linux2' or platform == 'win32':
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.press('return', interval=1)
    pag.sleep(5)

    # Zooming into the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/zoom.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Zoom button could not be located on the screen")
    pag.move(150, 200, duration=1)
    pag.dragRel(400, 250, duration=2)
    pag.sleep(5)

    # Panning into the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/pan.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Pan button could not be located on the screen")
    pag.moveRel(400, 400, duration=1)
    pag.dragRel(-100, -50, duration=2)
    pag.sleep(5)

    pag.move(-20, -25, duration=1)
    pag.dragRel(90, 50, duration=2)
    pag.sleep(5)

    # Switching to the previous appearance of the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/previous.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Previous button could not be located on the screen")
    pag.sleep(5)

    # Switching to the next appearance of the map
    try:
        x, y = pag.locateCenterOnScreen('pictures/next.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Next button could not be located on the screen")
    pag.sleep(5)

    # Resetting the map to the original size
    try:
        x, y = pag.locateCenterOnScreen('pictures/home.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Home button could not be located on the screen")
    pag.sleep(5)

    # Saving the figure
    try:
        x, y = pag.locateCenterOnScreen('pictures/save.PNG')
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Save button could not be located on the screen")
    current_time = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
    fig_filename = f'Fig_{current_time}.PNG'
    pag.sleep(3)
    if platform == 'win32':
        pag.write(fig_filename, interval=0.25)
        pag.press('enter', interval=1)
    if platform == 'linux' or platform == 'linux2':
        # pag.hotkey('altleft', 'tab') if the save file system window is not in the forefront, use this statement.
        # This can happen sometimes. At that time, you just need to uncomment it.
        pag.write(fig_filename, interval=0.25)
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.write(fig_filename, interval=0.25)
        pag.press('return', interval=1)

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
    sys.exit()


if __name__ == '__main__':
    main()
