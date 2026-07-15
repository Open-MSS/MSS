# -*  coding: utf-8 -*-
"""

    tutorials.utils
    ~~~~~~~~~~~~~~~

    init of tutorials

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft  und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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
import subprocess
import platform
import sys
import multiprocessing
import pyautogui as pag
from pyscreeze import ImageNotFoundException
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QLocale

from mslib.msui import msui
from tutorials.utils import screenrecorder as sr
from tutorials.utils.picture import picture
from tutorials.utils.platform_keys import platform_keys
from mslib.msui.constants import MSUI_CONFIG_PATH

CTRL, ENTER, WIN, ALT = platform_keys()


def screen_scale():
    """
    PyAutoGUI utilizes logical coordinates. When capturing screenshots on a Retina display,
    the resulting image is physically larger because each logical point consists of multiple physical pixels.
    Without adjusting for this scaling factor, image recognition will fail to locate the elements.
    """

    app = QApplication.instance()
    if app is not None:
        return app.primaryScreen().devicePixelRatio()
    # fallback: no QApplication running yet
    try:
        logical_width = pag.size()[0]
        screenshot_width = pag.screenshot().size[0]
        return screenshot_width / logical_width if logical_width else 1.0
    except (OSError, PermissionError, AttributeError, TypeError):
        return 1.0


def locate_center_on_screen(pic, region=None, confidence=None):
    """
    Locate the center of an image on screen and return its coordinates in
    pyautogui's logical point space, corrected for the display scale

    :param pic: The image file to locate on the screen.
    :param region: Optional region (in screenshot/physical pixels) to search in.
    :param confidence: Optional 0-1 match threshold (needs OpenCV). Captured
      images rarely match the live screen exactly on Retina/HiDPI (antialiasing,
      and toggle-button highlight states differ), so a value like 0.9 is needed
      there; None means an exact match.
    :return: The (x, y) center in logical points, or None if not found.
    """
    location = pag.locateCenterOnScreen(pic, region=region, confidence=confidence)
    if location is None:
        return None
    scale = screen_scale()
    return (location[0] / scale, location[1] / scale)


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
    # To use keyboard shortcuts, the relevant window must be active.
    QTimer.singleShot(0, lambda: (msui.mainwindow.raise_(),
                                  msui.mainwindow.activateWindow()))


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
        if sys.platform in ('linux', 'linux2'):
            for _ in range(close_widgets):
                pag.hotkey('altleft', 'f4')
                # pyautogui.ImageNotFoundException shows up when not enough views to close available
                find_and_click_picture('messagebox-yes.png', "Yes Button not found")
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('left')
            pag.keyUp('altleft')
            pag.press('q')
            find_and_click_picture('messagebox-yes.png', "Yes Button not found")
        if sys.platform == 'win32':
            for _ in range(close_widgets):
                pag.hotkey('alt', 'f4')
                # pyautogui.ImageNotFoundException shows up when not enough views to close available
                find_and_click_picture('messagebox-yes.png', "Yes Button not found")
            pag.hotkey('alt', 'tab')
            pag.press('q')
            find_and_click_picture('messagebox-yes.png', "Yes Button not found")
        elif sys.platform == 'darwin':
            for _ in range(close_widgets):
                pag.hotkey('command', 'w')
                # pyautogui.ImageNotFoundException shows up when not enough views to close available
                find_and_click_picture('messagebox-yes.png', "Yes Button not found")
            pag.hotkey('command', 'q')
            find_and_click_picture('messagebox-yes.png', "Yes Button not found")
    except Exception:
        print("Cannot automate : Enable Shortcuts for your system or try again")
        raise


def switch_window(presses=1, sleep=1):
    """
    Cycle to another window of the running application.

    This uses the platform's window-switching shortcut, since the key naming
    *and* the semantics differ per OS:

    - Linux/Windows: hold Alt and press Tab ``presses`` times.
    - macOS: press Command+Backtick presses ´ times. ⌘+´ cycles through
      the windows of the frontmost application (Alt+Tab would switch
      applications instead, not the MSUI view windows).

    :param presses: How many windows to advance by (default 1).
    :param sleep: Seconds to sleep afterwards (default 1, 0 to skip).
    """
    if sys.platform == 'darwin':
        for _ in range(presses):
            pag.hotkey('command', '`')
    else:
        pag.keyDown(ALT)
        for _ in range(presses):
            pag.press('tab')
        pag.keyUp(ALT)
    if sleep:
        pag.sleep(sleep)


def close_window(confirm=True, sleep=1):
    """
    Close the active window using the platform's shortcut.

    - Linux/Windows: Alt+F4.
    - macOS: Command+W (Alt/Option+F4 does nothing on macOS).

    :param confirm: When True, confirm a follow-up dialog by selecting the
        default button (Left then Enter). Default True.
    :param sleep: Seconds to wait before confirming the dialog (default 1).
    """
    if sys.platform == 'darwin':
        pag.hotkey('command', 'w')
    else:
        pag.hotkey(ALT, 'f4')
    if confirm:
        pag.sleep(sleep)
        pag.press('left')
        pag.press(ENTER)


def start(target=None, duration=120, dry_run=False, mscolab=False):
    """
    Starts the automation process.

    :param target: A function representing the target task to be automated. Default is None.
    :param duration: An integer representing the duration of the recording in seconds. Default is 120.
    :param dry_run: A boolean indicating whether to run in dry-run mode or not. Default is False.
    :return: None

    Note: Uncomment the line pag.press('q') if recording windows do not close in some cases.
    """
    if platform.system() in ('Linux', 'Darwin'):
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
    if sys.platform == "darwin":
        pag.hotkey(WIN, 'f')
    else:
        pag.hotkey(CTRL, 'f')
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


def click_center_on_screen(pic, duration=2, xoffset=0, yoffset=0, region=None, click=True,
                           confidence=None):
    """
    Clicks the center of an image on the screen.

    :param pic: The image file or partial image file to locate on the screen.
    :param duration: The duration (in seconds) for the click action. Default is 2 seconds.
    :param xoffset: The horizontal offset from the center of the image. Default is 0.
    :param yoffset: The vertical offset from the center of the image. Default is 0.
    :param region: The region on the screen to search for the image. Default is None, which searches the entire screen.
    :param click: Indicates whether to perform the click action. Default is True.
    :param confidence: Optional 0-1 match threshold (needs OpenCV); see
      locate_center_on_screen. None means an exact match.

    :return: None
    """
    x, y = locate_center_on_screen(pic, region=region, confidence=confidence)
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
                           bounding_box=None, region=None, click=True, confidence=None):
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
    :param confidence: Optional 0-1 match threshold (needs OpenCV); see
      locate_center_on_screen. Needed on Retina/HiDPI where captured images
      match the screen at ~0.98 rather than exactly. None means an exact match.

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
                               duration, xoffset=xoffset, yoffset=yoffset, region=region, click=click,
                               confidence=confidence)
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
        type_path(file_path, key=ENTER, clear=True)
    except (ImageNotFoundException, OSError, Exception):
        print(exception_message)
        raise


def _macos_keystroke(text):
    """
    Type *text* on macOS via AppleScript ``keystroke``.

    Honours the active keyboard layout, unlike pag.typewrite which sends US key
    codes (so '_' / '-' and similar get mangled on non-US layouts). Requires
    Accessibility + Automation permission for the launching app.
    """
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    subprocess.run(['osascript', '-e',
                    f'tell application "System Events" to keystroke "{escaped}"'], check=True)


def _linux_clipboard_copy(text):
    """
    Copy *text* to the Linux clipboard via the first available CLI tool.

    Tries ``wl-copy`` (Wayland), then ``xclip`` and ``xsel`` (X11). Returns True
    if a tool succeeded, False if none is installed -- letting the caller fall
    back to typewrite. Each tool reads the text from stdin and (xclip/wl-copy)
    forks to keep owning the selection, so the paste works afterwards.
    """
    candidates = []
    if os.environ.get('WAYLAND_DISPLAY'):
        candidates.append(['wl-copy'])
    candidates += [['xclip', '-selection', 'clipboard'], ['xsel', '--clipboard', '--input']]
    for cmd in candidates:
        try:
            subprocess.run(cmd, input=text, text=True, check=True)
            return True
        except (FileNotFoundError, OSError, subprocess.CalledProcessError):
            continue
    return False


def type_localized(text, key=ENTER, clear=False, interval=0.1):
    """
    Type *text* into the focused field independent of the keyboard layout.

    pag.write/typewrite sends US key codes, which mangle characters such as '_'
    or '-' on non-US layouts -- so a typed filename can come out wrong. macOS
    uses AppleScript keystroke (honours the active layout); Windows and Linux
    paste via the clipboard (Ctrl+V). On Linux this needs a clipboard CLI
    (``wl-copy``, ``xclip`` or ``xsel``); when none is installed it falls back to
    typewrite (fine for CI/Xvfb, which uses a US layout).

    :param text: the text to type.
    :param key: key to press afterwards (default ENTER); None to skip.
    :param clear: select existing content (Ctrl/Cmd+A) before typing.
    :param interval: per-character delay for the typewrite fallback.
    """
    if clear:
        pag.hotkey('command' if sys.platform == 'darwin' else CTRL, 'a')
        pag.sleep(0.5)
    if sys.platform == 'darwin':
        _macos_keystroke(text)
    elif sys.platform == 'win32':
        subprocess.run(['clip'], input=text, text=True, check=False)
        pag.sleep(0.5)
        pag.hotkey(CTRL, 'v')
    elif _linux_clipboard_copy(text):
        pag.sleep(0.5)
        pag.hotkey(CTRL, 'v')
    else:
        pag.typewrite(text, interval=interval)
    pag.sleep(1)
    if key is not None:
        pag.press(key)


def type_path(file_path, key=ENTER, clear=False):
    """
    Enter a filesystem path into the focused field or file dialog, independent
    of the keyboard layout.

    macOS uses the native "Go to Folder" sheet (see macos_enter_path_in_dialog);
    Windows and Linux type the path via type_localized. On Windows the path is
    first normalised to backslashes, which the native dialogs require (and which
    pyautogui cannot type on non-US layouts -- type_localized pastes it via the
    clipboard).

    :param file_path: the path to enter.
    :param key: key to press afterwards (default ENTER); None to skip.
    :param clear: select existing content before entering the path.
    """
    if sys.platform == 'darwin':
        macos_enter_path_in_dialog(file_path)
    else:
        path = os.path.normpath(file_path) if sys.platform == 'win32' else file_path
        type_localized(path, key=key, clear=clear)


def macos_enter_path_in_dialog(file_path):
    """
    Enter ``file_path`` into the macOS native file-open dialog.

    pag.typewrite() sends US key codes, so it mangles paths on non-US keyboards,
    and the Cmd+V paste shortcut is not reliably delivered to the panel's text
    field (it beeps instead of pasting). AppleScript ``keystroke`` honours the
    active keyboard layout and needs neither the clipboard nor Cmd+V.

    Requires Accessibility permission for the app that launches the tutorial
    (System Settings > Privacy & Security > Accessibility); without it macOS
    rejects the keystrokes with osascript.

    Requires Automation permission for the app that launches the tutorial
    (System Settings > Privacy & Security > Automation); without it macOS
    rejects the keystrokes with osascript.
    """
    def osa(applescript):
        subprocess.run(['osascript', '-e', applescript], check=True)

    # open the "Go to Folder" sheet, type the path, then confirm twice
    # (first Return accepts "Go to Folder", second accepts the open panel).
    osa('tell application "System Events" to keystroke "g" using {command down, shift down}')
    pag.sleep(2.5)  # wait for sheet to fully open
    _macos_keystroke(file_path)
    pag.sleep(0.8)
    osa('tell application "System Events" to keystroke return')
    pag.sleep(0.8)
    osa('tell application "System Events" to keystroke return')
    pag.sleep(1)


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


def select_color(open_pic, color_name, exception_message=None, region=None, confidence=None):
    """
    Open the predefined-swatch color dialog (CustomColorDialog) and click the
    swatch named ``color_name`` by locating its captured image on screen.

    This relies on create_tutorial_images() having captured the swatches as
    ``colorselectdialog-<color_name>.png`` (see CustomColorDialog), so the cursor
    goes to e.g. "red" wherever the dialog happens to open.

    :param open_pic: Image of the dock button that opens the color dialog.
    :param color_name: Friendly swatch name, e.g. "red", "blue", "green".
    :param exception_message: Optional message if ``open_pic`` is not found.
    :param region: Optional region applied to BOTH the open-button click and the
        swatch click (e.g. the view window's screen region). Constraining the
        swatch search avoids matching a same-colored preview button elsewhere.
        ``create_tutorial_images()`` always captures globally; ``region`` only
        bounds the on-screen clicks.
    :param confidence: Optional 0-1 match threshold (needs OpenCV); see
      locate_center_on_screen. None means an exact match.
    """
    # open the color dialog
    find_and_click_picture(open_pic,
                           exception_message or f"{open_pic} not found", region=region, confidence=confidence)
    pag.sleep(1)
    # capture the swatch images now that the dialog is visible
    create_tutorial_images()
    pag.sleep(1)
    # click the named swatch
    find_and_click_picture(f"colorselectdialog-{color_name}.png",
                           f"Color '{color_name}' not found in color dialog", region=region)


def zoom_in(pic_name, exception_message, move=(379, 205), dragRel=(70, 75), region=None, confidence=None):
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
    :param confidence: Optional 0-1 match threshold (needs OpenCV); see
      locate_center_on_screen. None means an exact match.
     Defaults to None, which means the entire screen will be searched.
    """
    try:
        x, y = locate_center_on_screen(picture(pic_name), region=region, confidence=confidence)
        pag.click(x, y, interval=2)
        pag.move(move[0], move[1], duration=1)
        pag.dragRel(dragRel[0], dragRel[1], duration=2)
        pag.sleep(5)
    except ImageNotFoundException:
        print(f"\nException: {exception_message}")
        raise


def panning(pic_name, exception_message, moveRel=(400, 400), dragRel=(-100, -50), region=None,
            confidence=None):
    """
    Executes panning action on the screen.

    :param pic_name: The name of the picture file to locate on the screen.
    :param exception_message: The message to display in case of exceptions.
    :param moveRel: The relative movements to be made after clicking on the picture. Defaults to (400, 400).
    :param dragRel: The relative movements to be made during the dragging action. Defaults to (-100, -50).
    :param region: The region of the screen to search for the picture. Defaults to None.
    :param confidence: Optional 0-1 match threshold (needs OpenCV); see
      locate_center_on_screen. None means an exact match.
    """
    try:
        x, y = locate_center_on_screen(picture(pic_name), region=region, confidence=confidence)
        pag.click(x, y, interval=2)
        pag.moveRel(moveRel[0], moveRel[1], duration=1)
        pag.dragRel(dragRel[0], dragRel[1], duration=2)
    except (ImageNotFoundException, OSError, Exception):
        print(f"\nException: {exception_message}")
        raise


def type_and_key(value, interval=0.1, key=ENTER):
    """
    Replace the focused field's content with *value*, then press *key*.

    A canonical dot-decimal numeric string (e.g. '90.00') is reformatted to the
    current locale's decimal separator first (e.g. '90,00' under a German/French
    locale); non-numeric strings are passed through. The actual typing is
    delegated to type_localized, so it clears the field (Cmd+A on macOS, Ctrl+A
    elsewhere) and enters the text independent of the keyboard layout.

    :param value: the value to type (locale-formatted if numeric).
    :param interval: per-character delay for the Linux typewrite fallback.
    :param key: key to press afterwards (default ENTER).
    """
    try:
        # preserve the number of decimal places from the canonical string
        decimals = len(value.split('.')[1]) if '.' in value else 0
        value = QLocale().toString(float(value), 'f', decimals)
    except (ValueError, TypeError, AttributeError):
        pass
    type_localized(value, key=key, clear=True, interval=interval)


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
    It cycles through the application windows using the platform-aware
    :func:`switch_window` helper.

    Example usage:
    show_other_widgets()

    """
    # show sideview
    switch_window(presses=2)
    # show linearview also
    switch_window(presses=1, sleep=0)
    # show topview also
    switch_window(presses=3)


def bring_main_window_to_front():
    # activate the MSUI main window.
    if sys.platform == 'darwin':
        pag.hotkey(WIN, 'up')
    else:
        pag.hotkey(CTRL, 'up')
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
        # The view shortcut is window-scoped
        bring_main_window_to_front()
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
