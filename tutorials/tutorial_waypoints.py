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
from sys import platform
from tutorials import screenrecorder as sr
from mslib.msui import mss_pyui


def initial_ops():
    """
    Executes the initial operations such as closing all opened windows and showing the desktop.
    """
    pag.sleep(5)
    if platform == "linux" or platform == "linux2":
        pag.hotkey('win', 'd')
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
    pag.sleep(15)
    try:
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.hotkey('win', 'up')
        elif platform == 'darwin':
            pag.hotkey('ctrl', 'command', 'f')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
    pag.hotkey('ctrl', 'h')
    pag.sleep(5)
    try:
        x, y = pag.locateCenterOnScreen('pictures/add_waypoint.PNG')
        pag.click(x, y)
    except Exception:
        print("\nException : Clickable button/option not found on the screen.")
    pag.moveTo(712, 347)
    pag.click(712, 347, interval=2)
    pag.moveTo(812, 412)
    pag.click(812, 412, interval=2)
    pag.sleep(5)

    pag.moveTo(900, 450)
    pag.click(900, 450, interval=2)
    pag.sleep(5)

    pag.moveTo(1000, 650)
    pag.click(900, 450, interval=2)
    pag.sleep(5)

    try:
        x, y = pag.locateCenterOnScreen('pictures/move_waypoint.PNG')
        pag.click(x,y, interval=3)
    except Exception:
        print("\n Exception : Move Waypoint button could not be located on the screen")
    pag.click(1000, 650, interval=3)
    pag.keyDown()

    print("\nAutomation is done upto this point. Will continue it next.")

    # Close Everything!
    try:
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
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
