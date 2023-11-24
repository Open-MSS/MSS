# -*  coding: utf-8 -*-
"""

    tutorials.utils
    ~~~~~~~~~~~~~~~

    init of tutorials

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft  und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2022 by the MSS team, see AUTHORS.
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
import sys
import multiprocessing
import pyautogui as pag
from pyscreeze import ImageNotFoundException

from mslib.msui import msui
from tutorials.utils import screenrecorder as sr, picture
from tutorials.utils.picture import picture


def initial_ops():
    """
    Executes the initial operations such as closing all opened windows and showing the desktop.
    """
    pag.sleep(5)
    if sys.platform == "linux" or sys.platform == "linux2":
        pag.hotkey('winleft', 'd')
        print("\n INFO : Automation is running on Linux system..\n")
    elif sys.platform == "darwin":
        pag.hotkey('option', 'command', 'm')
        print("\n INFO : Automation is running on Mac OS..\n")
    elif sys.platform == "win32":
        pag.hotkey('win', 'd')
        print("\n INFO : Automation is running on Windows OS..\n")
    else:
        pag.alert(text="Sorry, no support on this platform!", title="platform Exception", button='OK')


def call_recorder(x_start=0, y_start=0, x_width=int(pag.size()[0]), y_width=int(pag.size()[1]), duration=120):
    """
    Calls the screen recorder class to start the recording of the automation.
    """
    sr.ScreenRecorder()
    rec = sr.ScreenRecorder(x_start, y_start, x_width, y_width)
    rec.capture(duration=duration)
    rec.stop_capture()


def call_msui():
    """
    Calls the main MSS GUI window since operations are to be performed on it only.
    """
    msui.main(tutorial_mode=True)


def platform_keys():
    #  sys.platform specific keyse
    if sys.platform == 'linux' or sys.platform == 'linux2':
        enter = 'enter'
        win = 'winleft'
        ctrl = 'ctrl'
        alt = 'altleft'
    elif sys.platform == 'win32':
        enter = 'enter'
        win = 'win'
        ctrl = 'ctrl'
        alt = 'alt'
    elif sys.platform == 'darwin':
        enter = 'return'
        ctrl = 'command'
    return ctrl, enter, win, alt


def finish():
    # clean up and close all
    try:
        if sys.platform == 'linux' or sys.platform == 'linux2':
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
        if sys.platform == 'win32':
            for _ in range(3):
                pag.hotkey('alt', 'f4')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('enter')
                pag.sleep(2)
            pag.hotkey('alt', 'tab')
            pag.press('q')
        elif sys.platform == 'darwin':
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
        raise


def start(target=None, duration=120, dry_run=False):
    """
    This function runs the above functions as different processes at the same time and can be
    controlled from here. (This is the main process.)
    """
    if target is None:
        return
    p1 = multiprocessing.Process(target=call_msui)
    p2 = multiprocessing.Process(target=target)
    if not dry_run:
        p3 = multiprocessing.Process(target=call_recorder, kwargs={"duration": duration})
        p3.start()

    print("\nINFO : Starting Automation.....\n")

    pag.sleep(5)
    initial_ops()
    p1.start()
    p2.start()

    p2.join()
    p1.join()
    if not dry_run:
        p3.join()
    print("\n\nINFO : Automation Completes Successfully!")
    # pag.press('q') # In some cases, recording windows does not closes. So it needs to ne there.
    sys.exit()


def create_tutorial_images():
    pag.hotkey('ctrl', 'f')
    pag.sleep(1)


def get_region(image):
    region = pag.locateOnScreen(image)
    return region


def click_center_on_screen(pic, duration=2):
    x, y = pag.locateCenterOnScreen(pic)
    pag.click(x, y, duration=duration)


def select_listelement(steps):
    _, enter, _, _ = platform_keys()
    pag.press('down', presses=steps, interval=0.5)
    pag.press(enter, interval=1)
    pag.sleep(5)


def find_and_click_picture(pic_name, exception_message, duration=2):
    try:
        click_center_on_screen(picture(pic_name), duration)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise


def load_kml_file(pic_name, file_path, exception_message):
    _, enter, _, _ = platform_keys()
    try:
        find_and_click_picture(pic_name, exception_message)
        pag.typewrite(file_path, interval=0.1)
        pag.sleep(1)
        pag.press(enter)
    except (ImageNotFoundException, OSError, Exception):
        print(exception_message)
        raise


def change_attribute(pic_name, exception_message, actions, interval=2, sleep_time=2):
    try:
        click_center_on_screen(picture(pic_name), interval)
        pag.sleep(sleep_time)
        actions()
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise
