# -*  coding: utf-8 -*-
"""

    tutorials.utils
    ~~~~~~~~~~~~~~~

    init of tutorials

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft  und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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
import os
import platform
import sys
import multiprocessing
import pyautogui as pag
from pyscreeze import ImageNotFoundException

from mslib.msui import msui
from tutorials.utils import screenrecorder as sr
from tutorials.utils.picture import picture
from tutorials.utils.platform_keys import platform_keys
from mslib.msui.constants import MSUI_CONFIG_PATH

CTRL, ENTER, WIN, ALT = platform_keys()


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
    if platform.system() == 'Linux':
        # makes shure the keyboard is set to US
        os.system("setxkbmap -layout us")
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


def click_center_on_screen(pic, duration=2, xoffset=0, yoffset=0, region=None):
    if region is None:
        x, y = pag.locateCenterOnScreen(pic)
    else:
        x, y = pag.locateCenterOnScreen(pic, region=region)
    pag.click(x + xoffset, y + yoffset, duration=duration)


def select_listelement(steps, sleep=5, key=ENTER):
    pag.press('down', presses=steps, interval=0.5)
    pag.press(key, interval=1)
    pag.sleep(sleep)


def find_and_click_picture(pic_name, exception_message=None, duration=2, xoffset=0, yoffset=0,
                           bounding_box=None, region=None):
    x, y = (0, 0)
    message = exception_message if exception_message is not None else f"{pic_name} not found"
    try:
        click_center_on_screen(picture(pic_name, bounding_box=bounding_box),
                               duration, xoffset=xoffset, yoffset=yoffset, region=region)
        x, y = pag.position()
        # ToDo verify
        # pag.moveTo(x, y, duration=duration)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        filename = os.path.join(MSUI_CONFIG_PATH, "failure.png")
        print(f"\nException: {message} see {filename} for details")
        im = pag.screenshot(region=region)
        im.save(filename)
        raise

    return (x, y)


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


def zoom_in(pic_name, exception_message, move=(379, 205), dragRel=(70, 75), region=None):
    try:
        x, y = pag.locateCenterOnScreen(picture(pic_name), region=region)
        pag.click(x, y, interval=2)
        pag.move(move[0], move[1], duration=1)
        pag.dragRel(dragRel[0], dragRel[1], duration=2)
        pag.sleep(5)
    except ImageNotFoundException:
        print(f"\nException: {exception_message}")
        raise


def panning(pic_name, exception_message, moveRel=(400, 400), dragRel=(-100, -50), region=None):
    try:
        x, y = pag.locateCenterOnScreen(picture(pic_name), region=region)
        pag.click(x, y, interval=2)
        pag.moveRel(moveRel[0], moveRel[1], duration=1)
        pag.dragRel(dragRel[0], dragRel[1], duration=2)
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise


def type_and_key(value, interval=0.2, key=ENTER):
    """
    Type and Enter method

    This method types the given value and then presses the Enter key on the keyboard.

    :param value (str): The value to be typed.
    :param interval (float, optional): The interval between typing each character. Defaults to 0.3 seconds.

    Example:
        type_and_key("Hello, World!")
    """
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.typewrite(value, interval=interval)
    pag.sleep(1)
    pag.press(key)


def move_window(os_screen_region, x_drag_rel, y_drag_rel, x_mouse_down_offset=100):
    """

    Move the window to a new position.

    :param os_screen_region (tuple): A tuple containing the screen region of the window to be moved.
      It should have the format (x, y, w, h), where x and y are the coordinates of the top-left
      corner of the window, and w and h are the width and height of the window, respectively.
    :param  x_drag_rel (int): The amount to drag the window horizontally relative to its current position.
      Positive values will move the window to the right, while negative values will move it
      to the left.
    :param y_drag_rel (int): The amount to drag the window vertically relative to its current position.
      Positive values will move the window down, while negative values will move it up.
    :param x_mouse_down_offset (int): The offset from the left corner of the window where the mouse button
      will be pressed.
      This is useful to avoid clicking on any buttons or icons within the window. The default value is 100.

    Example usage:
    os_screen_region = (100, 200, 800, 600)
    x_drag_rel = 100
    y_drag_rel = 50
    move_window(os_screen_region, x_drag_rel, y_drag_rel)

    This will move the window located at (100, 200) to a new position that is 100 pixels to the right and 50 pixels
    down from its current position.

    """
    x, y = os_screen_region[0:2]
    # x, y is left corner where the msui logo is
    pag.mouseDown(x + x_mouse_down_offset, y - 10, duration=10)
    pag.sleep(1)
    pag.dragRel(x_drag_rel, y_drag_rel, duration=2)
    pag.mouseUp()


def move_and_setup_layerchooser(os_screen_region, x_move, y_move, x_drag_rel, y_drag_rel, x_mouse_down_offset=220):
    """

    Move and set up the layer chooser in a given screen region.

    :param os_screen_region: The screen region where the actions will be performed.
    :param x_move: The horizontal distance to move the mouse cursor.
    :param y_move: The vertical distance to move the mouse cursor.
    :param x_drag_rel: The horizontal distance to drag the mouse cursor relative to its current position.
    :param y_drag_rel: The vertical distance to drag the mouse cursor relative to its current position.
    :param x_mouse_down_offset (optional):  The offset from the left corner of the window where the mouse button
      will be pressed. This is useful to avoid clicking on any buttons or icons within the window. Defaults to 220.


    Example Usage:
    move_and_setup_layerchooser((0, 0, 1920, 1080), 100, -50, 200, 100, x_mouse_down_offset=300)
    move_and_setup_layerchooser((0, 0, 1920, 1080), -50, 0, 100, 200)

    """
    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Url not found', region=os_screen_region)
    x, y = pag.position()
    pag.click(x + x_mouse_down_offset, y, interval=2)
    type_and_key('http://open-mss.org/', interval=0.1)
    try:
        find_and_click_picture('multilayersdialog-get-capabilities.png',
                               'Get capabilities not found', region=os_screen_region)
    except TypeError:
        pag.press(ENTER)
    pag.move(x_move, y_move, duration=1)
    pag.dragRel(x_drag_rel, y_drag_rel, duration=2)


def show_other_widgets():
    """
    Displays other widgets in the application.

    This method shows the sideview, linearview, and topview of the application.
    It uses the `pag` module from the PyAutoGUI library to simulate key presses.

    Note:
    - The 'altleft' key is pressed and released in the following sections to navigate through the application.
    - The 'tab' key is pressed multiple times to switch between different views.

    Example usage:
    show_other_widgets()

    """
    # show sideview
    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    # show linearview also
    pag.keyDown('altleft')
    pag.press('tab')
    pag.keyUp('altleft')
    # show topview also
    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
