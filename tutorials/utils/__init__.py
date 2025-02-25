# -*  coding: utf-8 -*-
"""

    tutorials.utils
    ~~~~~~~~~~~~~~~

    init of tutorials

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft  und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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
    Starts a call recording of the specified area on the screen.

    :param x_start: (optional) The x-coordinate of the starting point for the recording area. Defaults to 0.
    :param y_start: (optional) The y-coordinate of the starting point for the recording area. Defaults to 0.
    :param x_width: (optional) The width of the recording area. Defaults to the width of the screen.
    :param y_width: (optional) The height of the recording area. Defaults to the height of the screen.
    :param duration: (optional) The duration of the recording in seconds. Defaults to 120 seconds.
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


def call_mscolab():
    # change of config won't work when it becomes earlier imported
    from mslib.mscolab import mscolab
    with mscolab.APP.app_context():
        # initialize our seeded example dbase
        mscolab.handle_db_seed()
    mscolab.handle_start()


def finish(close_widgets=3):
    """
    Closes all open windows and exits the application.

    This method is used to automate the process of closing all open windows and exiting the application.

    """
    # clean up and close all
    try:
        if sys.platform == 'linux' or sys.platform == 'linux2':
            for _ in range(close_widgets):
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
            for _ in range(close_widgets):
                pag.hotkey('alt', 'f4')
                pag.sleep(3)
                pag.press('left')
                pag.sleep(3)
                pag.press('enter')
                pag.sleep(2)
            pag.hotkey('alt', 'tab')
            pag.press('q')
        elif sys.platform == 'darwin':
            for _ in range(close_widgets):
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


def start(target=None, duration=120, dry_run=False, mscolab=False):
    """
    Starts the automation process.

    :param target: A function representing the target task to be automated. Default is None.
    :param duration: An integer representing the duration of the recording in seconds. Default is 120.
    :param dry_run: A boolean indicating whether to run in dry-run mode or not. Default is False.
    :return: None

    Note: Uncomment the line pag.press('q') if recording windows do not close in some cases.
    """
    if platform.system() == 'Linux':
        tutdir = "/tmp/msui_tutorials"
        if not os.path.isdir(tutdir):
            os.mkdir(tutdir)
        os.environ["MSUI_CONFIG_PATH"] = tutdir
        os.environ["XDG_CACHE_HOME"] = tutdir
        # makes sure the keyboard is set to US
        os.system("setxkbmap -layout us")

        # early
        if mscolab:
            mscdir = "/tmp/mscolab_tutorials"
            if not os.path.isdir(mscdir):
                os.makedirs(mscdir)
            settings_file = os.path.join(mscdir, "mscolab_settings.py")
            with open(settings_file, "w") as sf:
                sf.write('import os\n')
                sf.write('\n\n')
                sf.write(f"BASE_DIR = '{mscdir}'\n")
                sf.write('DATA_DIR = os.path.join(BASE_DIR, "colabdata")\n')
                sf.write('OPERATIONS_DATA = os.path.join(DATA_DIR, "filedata")\n')
                sf.write("DEBUG = True\n")

            os.environ["MSCOLAB_SETTINGS"] = settings_file
            sys.path.insert(0, mscdir)

    if target is None:
        return
    p1 = multiprocessing.Process(target=call_msui)
    p2 = multiprocessing.Process(target=target)
    if not dry_run:
        p3 = multiprocessing.Process(target=call_recorder, kwargs={"duration": duration})
        p3.start()
    if mscolab is True:
        print("Start and Seed MSColab server")
        p4 = multiprocessing.Process(target=call_mscolab, daemon=True)
        p4.start()

    print("\nINFO : Starting Automation.....\n")

    pag.sleep(5)
    initial_ops()
    p1.start()
    p2.start()

    # recording process needs to become joined
    if not dry_run:
        p3.join()

    print("\n\nINFO : Automation Completes Successfully!")

    # pag.press('q') # In some cases, recording windows does not closes. So it needs to ne there.
    sys.exit()


def create_tutorial_images():
    """

    This method `create_tutorial_images` is used to simulate the keyboard key
    combination 'Ctrl + F' and then puts the program to sleep for 1 second.

    """
    pag.hotkey('ctrl', 'f')
    pag.sleep(1)


def get_region(image, region=None):
    """
    Find the region of the given image on the screen.

    :param image: The image to locate on the screen.
    :return: The region of the image found on the screen.
    :rtype: tuple(int, int, int, int)
    """
    if region is not None:
        image_region = pag.locateOnScreen(picture(image), region=region)
    else:
        image_region = pag.locateOnScreen(picture(image))
    return image_region


def click_center_on_screen(pic, duration=2, xoffset=0, yoffset=0, region=None, click=True):
    """
    Clicks the center of an image on the screen.

    :param pic: The image file or partial image file to locate on the screen.
    :param duration: The duration (in seconds) for the click action. Default is 2 seconds.
    :param xoffset: The horizontal offset from the center of the image. Default is 0.
    :param yoffset: The vertical offset from the center of the image. Default is 0.
    :param region: The region on the screen to search for the image. Default is None, which searches the entire screen.
    :param click: Indicates whether to perform the click action. Default is True.

    :return: None
    """
    if region is None:
        x, y = pag.locateCenterOnScreen(pic)
    else:
        x, y = pag.locateCenterOnScreen(pic, region=region)
    if click:
        pag.click(x + xoffset, y + yoffset, duration=duration)


def select_listelement(steps, sleep=5, key=ENTER):
    """
    Selects an element from a list by moving the cursor downward and pressing a key.

    :param steps: Number of times to move the cursor downward.
    :param sleep: Time to sleep after pressing the key (default is 5 seconds).
    :param key: Key to press after moving the cursor (default is 'ENTER').
    :return: None
    """
    pag.press('down', presses=steps, interval=0.5)
    if key is not None:
        pag.press(key, interval=1)
    pag.sleep(sleep)


def find_and_click_picture(pic_name, exception_message=None, duration=2, xoffset=0, yoffset=0,
                           bounding_box=None, region=None, click=True):
    """

    Finds a specified picture and clicks on it.
    When the image can't be found, an exception is raised and a failure.png image is created

    :param pic_name: The name of the picture to find. This can be a file name or a string pattern.
    :param exception_message: Optional. Custom exception message to be displayed if the picture is not found.
     Defaults to None.
    :param duration: Optional. The duration of the click in seconds. Defaults to 2.
    :param xoffset: Optional. The x-axis offset for the click position. Defaults to 0.
    :param yoffset: Optional. The y-axis offset for the click position. Defaults to 0.
    :param bounding_box: Optional. The bounding box of the image. The image is cropped to. Defaults to None.
    :param region: Optional. The region in which to search for the picture. Defaults to None.
    :param click: Optional. Indicates whether to perform the click action. Defaults to True.

    :raises ImageNotFoundException: If the picture is not found.
    :raises OSError: If there is an error while processing the picture.
    :raises Exception: If any other exception occurs.

    :returns: A tuple containing the x and y coordinates of the clicked position.
    """
    pag.sleep(2)
    x, y = (0, 0)
    message = exception_message if exception_message is not None else f"{pic_name} not found"
    try:
        click_center_on_screen(picture(pic_name, bounding_box=bounding_box),
                               duration, xoffset=xoffset, yoffset=yoffset, region=region, click=click)
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
    """
    Loads a KML file using the given picture name and file path.

    :param pic_name: The name of the picture to be found and clicked.
    :param file_path: The path to the KML file.
    :param exception_message: The exception message to be printed and raised if an error occurs.
    :raises ImageNotFoundException: If the specified picture cannot be found.
    :raises OSError: If an error occurs while typing the file path or pressing the ENTER key.
    :raises Exception: If an unknown error occurs.

    """
    try:
        find_and_click_picture(pic_name, exception_message)
        pag.typewrite(file_path, interval=0.1)
        pag.sleep(1)
        pag.press(ENTER)
    except (ImageNotFoundException, OSError, Exception):
        print(exception_message)
        raise


def change_color(pic_name, exception_message, actions, interval=2, sleep_time=2):
    """
    Changes the color of the specified picture and performs the given actions.
    """
    try:
        click_center_on_screen(picture(pic_name), interval)
        pag.sleep(sleep_time)
        actions()
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise


def zoom_in(pic_name, exception_message, move=(379, 205), dragRel=(70, 75), region=None):
    """
    This method locates a given picture on the screen, clicks on it, moves the mouse cursor,
    performs a drag motion, waits for 5 seconds, and raises an exception if the picture is not found

    :param pic_name: The name of the picture to locate on the screen.
    :param exception_message: The message to be displayed in case the picture is not found.
    :param move: The amount to move the mouse cursor horizontally and vertically after clicking on the picture.
     Defaults to (379, 205).
    :param dragRel: The amount to drag the mouse cursor horizontally and vertically after moving.
     Defaults to (70, 75).
    :param region: The specific region of the screen to search for the picture.
     Defaults to None, which means the entire screen will be searched.
    """
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
    """
    Executes panning action on the screen.

    :param pic_name: The name of the picture file to locate on the screen.
    :param exception_message: The message to display in case of exceptions.
    :param moveRel: The relative movements to be made after clicking on the picture. Defaults to (400, 400).
    :param dragRel: The relative movements to be made during the dragging action. Defaults to (-100, -50).
    :param region: The region of the screen to search for the picture. Defaults to None.
    """
    try:
        x, y = pag.locateCenterOnScreen(picture(pic_name), region=region)
        pag.click(x, y, interval=2)
        pag.moveRel(moveRel[0], moveRel[1], duration=1)
        pag.dragRel(dragRel[0], dragRel[1], duration=2)
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise


def type_and_key(value, interval=0.1, key=ENTER):
    """
    Type and Enter method

    This method types the given value and then presses the Enter key on the keyboard.

    :param value (str): The value to be typed.
    :param interval (float, optional): The interval between typing each character. Defaults to 0.3 seconds.
    """
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.typewrite(value, interval=interval)
    pag.sleep(1)
    pag.press(key)


def move_window(os_screen_region, x_drag_rel, y_drag_rel, x_mouse_down_offset=100):
    """

    Move the window to a new position.

    :param os_screen_region: A tuple containing the screen region of the window to be moved.
      It should have the format (x, y, w, h), where x and y are the coordinates of the top-left
      corner of the window, and w and h are the width and height of the window, respectively.
    :param  x_drag_rel: The amount to drag the window horizontally relative to its current position.
      Positive values will move the window to the right, while negative values will move it
      to the left.
    :param y_drag_rel: The amount to drag the window vertically relative to its current position.
      Positive values will move the window down, while negative values will move it up.
    :param x_mouse_down_offset: The offset from the left corner of the window where the mouse button
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


def msui_full_screen_and_open_first_view(view_cmd='h'):
    """
    Open the first view and go full screen in MSUI.

    :param view_cmd: The command to open the view (default is 'h' for Home).
    :type view_cmd: str

    :return: None
    """
    pag.sleep(1)
    if view_cmd is not None:
        pag.hotkey(CTRL, view_cmd)
        pag.sleep(1)
    create_tutorial_images()
    pag.sleep(2)


def add_waypoints_to_topview(os_screen_region):
    # enable adding waypoints
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Clickable button/option not found.',
                           region=os_screen_region)
    # Adding waypoints for demonstrating remote sensing
    pag.move(-50, 150, duration=1)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(65, 65, duration=1)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(-150, 30, duration=1)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(200, 150, duration=1)
    pag.click(interval=2)
    pag.sleep(2)
