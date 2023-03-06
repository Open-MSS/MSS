"""
    msui.tutorials.tutorial_waypoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to play with and use waypoints
    for activating/creating a flight track.

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
import datetime

from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils import platform_keys, start, finish
from tutorials.pictures import picture


def automate_waypoints():
    """
    This is the main automating script of the MSS waypoints tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(15)
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
    pag.sleep(2)
    pag.hotkey('ctrl', 'h')
    pag.sleep(5)

    # Adding waypoints
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'add_waypoint.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\nException : Clickable button/option not found on the screen.")
        raise
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
        x, y = pag.locateCenterOnScreen(picture('wms', 'move_waypoint.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Move Waypoint button could not be located on the screen")
        raise

    pag.moveTo(x2, y2, duration=1)
    pag.click(interval=2)
    pag.dragRel(100, 150, duration=1)
    pag.moveTo(x1, y1, duration=1)
    pag.dragRel(35, -50, duration=1)
    x1, y1 = pag.position()

    # Deleting waypoints
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'remove_waypoint.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Remove Waypoint button could not be located on the screen")
        raise
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
        if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            print(pag.position())
            x, y = pag.locateCenterOnScreen(picture('wms', 'europe_cyl.png'))
            pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Map change dropdown could not be located on the screen")
        raise
    pag.press('down', presses=2, interval=0.5)
    if platform == 'linux' or platform == 'linux2' or platform == 'win32':
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.press('return', interval=1)
    pag.sleep(5)

    # Zooming into the map
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'zoom.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Zoom button could not be located on the screen")
        raise
    pag.move(150, 200, duration=1)
    pag.dragRel(400, 250, duration=2)
    pag.sleep(5)

    # Panning into the map
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'pan.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Pan button could not be located on the screen")
        raise
    pag.moveRel(400, 400, duration=1)
    pag.dragRel(-100, -50, duration=2)
    pag.sleep(5)

    pag.move(-20, -25, duration=1)
    pag.dragRel(90, 50, duration=2)
    pag.sleep(5)

    # Switching to the previous appearance of the map
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'previous.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Previous button could not be located on the screen")
        raise
    pag.sleep(5)

    # Switching to the next appearance of the map
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'next.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Next button could not be located on the screen")
        raise
    pag.sleep(5)

    # Resetting the map to the original size
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'home.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Home button could not be located on the screen")
        raise
    pag.sleep(5)

    # Saving the figure
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'save.png'))
        pag.click(x, y, interval=2)
    except ImageNotFoundException:
        print("\n Exception : Save button could not be located on the screen")
        raise
    current_time = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
    fig_filename = f'Fig_{current_time}.png'
    pag.sleep(3)
    if platform == 'win32':
        pag.write(fig_filename, interval=0.25)
        pag.press('enter', interval=1)
    if platform == 'linux' or platform == 'linux2':
        pag.hotkey('altleft', 'tab')  # if the save file system window is not in the forefront, use this statement.
        # This can happen sometimes. At that time, you just need to uncomment it.
        pag.write(fig_filename, interval=0.25)
        pag.press('enter', interval=1)
    elif platform == 'darwin':
        pag.write(fig_filename, interval=0.25)
        pag.press('return', interval=1)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_waypoints, duration=158)
