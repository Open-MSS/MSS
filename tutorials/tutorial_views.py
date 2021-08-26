"""
    mss.tutorials.tutorial_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the top view, side view, table view and
    linear view section of Mission Support System in creating a project and planning the flightrack.

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
    print("\n INFO : We will be learning how to create a project in MSS with all the views.\n")


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


def automate_views():
    """
    This is the main automating script of the MSS views tutorial which will cover all the views(topview, sideview,
    tableview, linear view) in demonstrating how to create a project. This will be recorded and savedto a file having
    dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        dir_path = 'pictures/tutorial_views/win/'
        wms_path = 'pictures/tutorial_wms/linux/'
    elif platform == 'win32':
        dir_path = 'pictures/tutorial_views/win/'
        wms_path = 'pictures/tutorial_wms/win/'

    # Screen Resolutions
    sc_width, sc_height = pag.size()[0] - 1, pag.size()[1] - 1

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
    pag.sleep(2)

    # Shfting topview window to upper right corner
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}add_waypoint.png')
        pag.click(x, y - 56, interval=2)
        if platform == 'win32' or platform == 'darwin':
            pag.dragRel(525, -110, duration=2)
        elif platform == 'linux' or platform == 'linux2':
            pag.dragRel(910, -25, duration=2)
        pag.move(None, 56)
        add_tv_x, add_tv_y = pag.position()
        pag.move(-486, -56, duration=1)
        pag.click(interval=1)
        if platform == 'win32' or platform == 'linux' or platform == 'linux2':
            pag.hotkey('ctrl', 'v')
        elif platform == 'darwin':
            pag.hotkey('command', 'v')
        pag.sleep(4)
        # Shifting Sideview window to upper left corner.
        try:
            x1, y1 = pag.locateCenterOnScreen(f'{dir_path}add_waypoint.png')
            if platform == 'win32' or platform == 'darwin':
                pag.moveTo(x1, y1 - 56, duration=1)
                pag.dragRel(-494, -177, duration=2)
            elif platform == 'linux' or platform == 'linux2':
                pag.moveTo(x1, y1 - 56, duration=1)
                pag.dragRel(-50, -30, duration=2)
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
                pag.press('command', 'tab', 'right')
            pag.sleep(1)
        except (ImageNotFoundException, OSError, Exception):
            print("Exception: \'Side View Window Header\' was not found on the screen")
    except (ImageNotFoundException, OSError, Exception):
        print("Exception: \'Topview Window Header\' was not found on the screen")

    # Adding waypoints
    if add_tv_x is not None and add_tv_y is not None:
        pag.sleep(1)
        pag.click(add_tv_x, add_tv_y, interval=2)
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
        pag.sleep(1)
        pag.move(100, -80, duration=1)
        pag.click(interval=2)
        pag.move(56, -63, duration=1)
        pag.click(interval=2)
        pag.sleep(3)
    else:
        print("Screen coordinates not available for add waypoints for topview")

    # Opening web map service
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png', region=(int(sc_width / 2), 0, sc_width,
                                                                                      sc_height))
        pag.click(x, y, interval=2)
        pag.press('down', interval=1)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Top views' select to open control\' button/option not found on the screen.")

    # Locating Server Layer
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}layers.png', region=(int(sc_width / 2), 0, sc_width, sc_height))
        pag.click(x, y, interval=2)
        # Entering wms URL
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}wms_url.png', region=(int(sc_width / 2), 0,
                                                                              sc_width, sc_height))
            pag.click(x + 220, y, interval=2)
            pag.hotkey('ctrl', 'a', interval=1)
            pag.write('http://open-mss.org/', interval=0.25)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Topviews' \'WMS URL\' editbox button/option not found on the screen.")
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}get_capabilities.png', region=(int(sc_width / 2), 0, sc_width,
                                                                                       sc_height))
            pag.click(x, y, interval=2)
            pag.sleep(4)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Topviews' \'Get capabilities\' button/option not found on the screen.")

        # Relocating Layerlist of topview
        if platform == 'win32':
            pag.move(-171, -390, duration=1)
            pag.dragRel(10, 627, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.move(-171, -390, duration=1)
            pag.dragRel(10, 675, duration=2)  # To be decided
        pag.sleep(1)
        # Storing screen coordinates for List layer of top view
        ll_tov_x, ll_tov_y = pag.position()
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Topviews WMS' \'Server\\Layers\' button/option not found on the screen.")

    # Selecting some layers in topview layerlist
    if platform == 'win32':
        gap = 22
    elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        gap = 16
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}divergence_layer.png', region=(int(sc_width / 2), 0, sc_width,
                                                                                   sc_height))
        temp1, temp2 = x, y
        pag.click(x, y, interval=2)
        pag.sleep(3)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, gap * 2, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, -gap * 4, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Topview's \'Divergence Layer\' option not found on the screen.")

    # Setting different levels and valid time
    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2 + (gap * 3), interval=2)
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}level.png', region=(int(sc_width / 2), 0, sc_width, sc_height))
        pag.click(x + 200, y, interval=2)
        pag.move(None, 140, duration=1)
        pag.click(interval=1)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Topview's \'Pressure level\' button/option not found on the screen.")
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}valid.png', region=(int(sc_width / 2), 0, sc_width, sc_height))
        pag.click(x + 200, y, interval=1)
        pag.move(None, 80, duration=1)
        pag.click(interval=1)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Topview's \'Valid till\' button/option not found on the screen.")

    # Moving waypoints in Topview
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}move_waypoint.png', region=(int(sc_width / 2), 0, sc_width,
                                                                                sc_height))
        if platform == 'win32' or platform == 'darwin':
            pag.click(x, y, interval=2)
            pag.moveTo(x2 + 4, y2 - 96, duration=1)
            pag.click(interval=2)
            pag.dragRel(100, 150, duration=1)
            pag.moveTo(x1 + 46, y1 - 67, duration=1)
            pag.dragRel(35, -50, duration=1)
            x3, y3 = pag.position()
        elif platform == 'linux' or platform == 'linux2':
            pag.click(x, y, interval=2)
            pag.moveTo(x2 + 5, y2 - 82, duration=1)
            pag.click(interval=2)
            pag.dragRel(100, 150, duration=1)
            pag.moveTo(x1 + 35, y1 - 60, duration=1)
            pag.dragRel(35, -50, duration=1)
            x3, y3 = pag.position()
        pag.sleep(1)
    except ImageNotFoundException:
        print("\n Exception : Move Waypoint button could not be located on the screen")

    # Deleting waypoints
    try:
        x, y = pag.locateCenterOnScreen('pictures/remove_waypoint.PNG', region=(int(sc_width / 2), 0, sc_width,
                                                                                sc_height))
        pag.click(x, y, interval=2)
        pag.moveTo(x3, y3, duration=1)
        pag.click(duration=1)
        if platform == 'win32':
            pag.press('left')
        pag.sleep(2)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
        pag.sleep(2)
    except ImageNotFoundException:
        print("\n Exception : Remove Waypoint button could not be located on the screen")

    # Changing map to Global
    try:
        if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            x, y = pag.locateCenterOnScreen('pictures/europe(cyl).PNG', region=(int(sc_width / 2), 0, sc_width,
                                                                                sc_height))
            pag.click(x, y, interval=2)
        elif platform == 'win32':
            x, y = pag.locateCenterOnScreen('pictures/europe(cyl)win.PNG', region=(int(sc_width / 2), 0, sc_width,
                                                                                   sc_height))
            pag.click(x, y, interval=2)
        pag.press('down', presses=2, interval=0.5)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
        pag.sleep(6)
    except (ImageNotFoundException, TypeError, OSError, Exception):
        print("\n Exception : Topview's Map change dropdown could not be located on the screen")

    # Zooming into the map
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}zoom.png', region=(int(sc_width / 2), 0, sc_width, sc_height))
        pag.click(x, y, interval=2)
        pag.move(155, 121, duration=1)
        pag.click(duration=1)
        pag.dragRel(260, 110, duration=2)
        pag.sleep(4)
    except ImageNotFoundException:
        print("\n Exception : Topview's Zoom button could not be located on the screen")

    # SideView Operations
    # Opening web map service
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png', region=(0, 0, int(sc_width / 2),
                                                                                      sc_height))
        pag.click(x, y, interval=2)
        pag.press('down', interval=1)
        if platform == 'linux' or platform == 'linux2' or platform == 'win32':
            pag.press('enter', interval=1)
        elif platform == 'darwin':
            pag.press('return', interval=1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'SideView's select to open control\' button/option not found on the screen.")

    # Locating Server Layer
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}layers.png', region=(0, 0, int(sc_width / 2), sc_height))
        pag.click(x, y, interval=2)
        # Entering wms URL
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}wms_url.png', region=(0, 0, int(sc_width / 2), sc_height))
            pag.click(x + 220, y, interval=2)
            pag.hotkey('ctrl', 'a', interval=1)
            pag.write('http://open-mss.org/', interval=0.25)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Sideviews' \'WMS URL\' editbox button/option not found on the screen.")
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}get_capabilities.png', region=(0, 0, int(sc_width / 2),
                                                                                       sc_height))
            pag.click(x, y, interval=2)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : SideView's \'Get capabilities\' button/option not found on the screen.")
        if platform == 'win32':
            pag.move(-171, -390, duration=1)
            pag.dragRel(10, 570, duration=2)
        elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            pag.move(-171, -390, duration=1)
            pag.dragRel(10, 600, duration=2)
        # Storing screen coordinates for List layer of side view
        ll_sv_x, ll_sv_y = pag.position()
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Sideviews WMS' \'Server\\Layers\' button/option not found on the screen.")

    # Selecting some layers in Sideview WMS
    if platform == 'win32':
        gap = 22
    elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        gap = 16
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}cloudcover.png', region=(0, 0, int(sc_width / 2), sc_height))
        temp1, temp2 = x, y
        pag.click(x, y, interval=2)
        pag.sleep(3)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, gap * 2, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
        pag.move(None, -gap * 4, duration=1)
        pag.click(interval=1)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Sideview's \'Cloud Cover Layer\' option not found on the screen.")

    # Setting different levels and valid time
    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2 + (gap * 4), interval=2)

    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}valid.png', region=(0, 0, int(sc_width / 2), sc_height))
        pag.click(x + 200, y, interval=1)
        pag.move(None, 80, duration=1)
        pag.click(interval=1)
        pag.sleep(4)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Sideview's \'Valid till\' button/option not found on the screen.")

    # Move waypoints in SideView
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}move_waypoint.png', region=(0, 0, int(sc_width / 2), sc_height))
        pag.click(x, y, interval=2)
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}options.png', region=(0, 0, int(sc_width / 2), sc_height))
            if platform == 'win32' or platform == 'darwin':
                pag.click(x + 76, y - 80, duration=1)
                pag.dragRel(-1, -139, duration=2)
                pag.click(x + 508, y - 80, duration=1)
                pag.dragRel(None, -80, duration=2)
                pag.click(x + 684, y - 80, duration=1)
                pag.dragRel(None, -150, duration=2)
            elif platform == 'linux' or platform == 'linux2':
                pag.click(x + 90, y - 80, duration=1)
                pag.dragRel(-1, -139, duration=2)
                pag.click(x + 508, y - 80, duration=1)
                pag.dragRel(None, -110, duration=2)
                pag.click(x + 695, y - 80, duration=1)
                pag.dragRel(None, -150, duration=2)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, TypeError, Exception):
            print("\nException : Sideview's waypoints location (Options button) not found on the screen.")
    except ImageNotFoundException:
        print("\n Exception :Sideview's Move Waypoint button could not be located on the screen")

    # Adding waypoints in SideView
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}add_waypoint.png', region=(0, 0, int(sc_width / 2), sc_height))
        pag.click(x, y, duration=1)
        pag.click(x + 239, y + 186, duration=1)
        pag.sleep(3)
        pag.click(x + 383, y + 93, duration=1)
        pag.sleep(3)
        pag.click(x + 450, y + 140, duration=1)
        pag.sleep(4)
        pag.click(x, y, duration=1)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : Sideview's add waypoint button not found on the screen.")

    # Closing list layer of sideview and topview to make screen a little less congested.
    pag.click(ll_sv_x, ll_sv_y, duration=2)
    if platform == 'linux' or platform == 'linux2':
        pag.hotkey('altleft', 'f4')
    elif platform == 'win32':
        pag.hotkey('alt', 'f4')
    elif platform == 'darwin':
        pag.hotkey('command', 'w')
    pag.sleep(1)
    pag.click(ll_tov_x, ll_tov_y, duration=2)
    if platform == 'linux' or platform == 'linux2':
        pag.hotkey('altleft', 'f4')
    elif platform == 'win32':
        pag.hotkey('alt', 'f4')
    elif platform == 'darwin':
        pag.hotkey('command', 'w')

    # Table View
    # Opening Table View
    pag.move(-80, 120, duration=1)
    # pag.moveTo(1800, 1000, duration=1)
    pag.click(duration=1)
    pag.hotkey('ctrl', 't')
    pag.sleep(2)

    # Relocating Tableview and performing operations on table view
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        pag.moveTo(x, y - 462, duration=1)
        if platform == 'linux' or platform == 'linux2':
            pag.dragRel(250, 887, duration=3)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(None, 487, duration=2)
        pag.sleep(2)
        if platform == 'linux' or platform == 'linux2':
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('altleft')
            pag.sleep(1)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('right', presses=2)  # This needs to be checked in Linux
            pag.keyUp('altleft')
        elif platform == 'win32':
            pag.keyDown('alt')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('alt')
            pag.sleep(1)
            pag.keyDown('alt')
            pag.press('tab')
            pag.press('right', presses=2)
            pag.keyUp('alt')
        elif platform == 'darwin':
            pag.keyDown('command')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('command')
            pag.sleep(1)
            pag.keyDown('command')
            pag.press('tab')
            pag.press('right', presses=2)
            pag.keyUp('command')
        pag.sleep(1)
        if platform == 'win32' or platform == 'darwin':
            pag.dragRel(None, -300, duration=2)
            tv_x, tv_y = pag.position()
        elif platform == 'linux' or platform == 'linux2':
            pag.dragRel(None, -450, duration=2)
            tv_x, tv_y = pag.position()

        # Locating the selecttoopencontrol for tableview to perform operations
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png',
                                            region=(0, int(sc_height * 0.75), sc_width, int(sc_height * 0.25)))

            # Changing names of certain waypoints to predefined names
            pag.click(x, y - 190, duration=1) if platform == 'win32' else pag.click(x, y - 325, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(2)
            pag.move(88, None, duration=1) if platform == 'win32' else pag.move(78, None, duration=1)
            pag.sleep(1)
            pag.click(duration=1)
            pag.press('down', presses=5, interval=0.2)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(1)

            # Giving user defined names to waypoints
            pag.click(x, y - 160, duration=1) if platform == 'win32' else pag.click(x, y - 294, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(1.5)
            if platform == 'linux' or platform == 'linux2' or platform == 'win32':
                pag.hotkey('ctrl', 'a')
            elif platform == 'darwin':
                pag.hotkey('command', 'a')
            pag.sleep(1)
            pag.write('Location A', interval=0.1)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(2)

            pag.click(x, y - 127, duration=1) if platform == 'win32' else pag.click(x, y - 263, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(2)
            if platform == 'linux' or platform == 'linux2' or platform == 'win32':
                pag.hotkey('ctrl', 'a')
            elif platform == 'darwin':
                pag.hotkey('command', 'a')
            pag.sleep(1)
            pag.write('Stop Point', interval=0.1)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(2)

            # Changing Length of Flight Level
            pag.click(x + 266, y - 95, duration=1) if platform == 'win32' else pag.click(x + 236, y - 263, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(1)
            pag.write('319', interval=0.2)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(2)

            # Changing hPa level of waypoints
            pag.click(x + 344, y - 65, duration=1) if platform == 'win32' else pag.click(x + 367, y - 232, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(1)
            pag.write('250', interval=0.2)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(2)

            # Changing longitude of 'Location A' waypoint
            pag.click(x + 194, y - 160, duration=1) if platform == 'win32' else pag.click(x + 165, y - 294, duration=1)
            pag.sleep(1)
            pag.doubleClick(duration=1)
            pag.sleep(1)
            pag.write('12.36', interval=0.2)
            pag.sleep(1)
            pag.press('return') if platform == 'darwin' else pag.press('enter')
            pag.sleep(2)

            # Cloning the row of waypoint
            try:
                x1, y1 = pag.locateCenterOnScreen(f'{wms_path}clone.png')
                pag.click(x + 15, y - 130, duration=1) if platform == 'win32' else pag.click(x + 15, y - 263,
                                                                                             duration=1)
                pag.sleep(1)
                pag.click(x1, y1, duration=1)
                pag.sleep(2)
                pag.click(x + 15, y - 100, duration=1) if platform == 'win32' else pag.click(x + 15, y - 232,
                                                                                             duration=1)
                pag.sleep(1)
                pag.doubleClick(x + 130, y - 100, duration=1) if platform == 'win32' else pag.click(x + 117, y - 232,
                                                                                                    duration=1)
                pag.sleep(1)
                pag.write('65.26', interval=0.2)
                pag.sleep(1)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
                pag.move(580, None, duration=1) if platform == 'win32' else pag.move(459, None, duration=1)
                pag.doubleClick(duration=1)
                pag.sleep(2)
                pag.write('This is a reference comment', interval=0.2)
                pag.sleep(1)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
            except (ImageNotFoundException, OSError, TypeError, Exception):
                print("\nException : Tableview's CLONE button not found on the screen.")

            # Inserting a new row of waypoints
            try:
                x1, y1 = pag.locateCenterOnScreen(f'{wms_path}insert.png')
                pag.click(x + 130, y - 160, duration=1) if platform == 'win32' else pag.click(x + 117, y - 294,
                                                                                              duration=1)
                pag.sleep(2)
                pag.click(x1, y1, duration=1)
                pag.sleep(2)
                pag.click(x + 130, y - 125, duration=1) if platform == 'win32' else pag.click(x + 117, y - 263,
                                                                                              duration=1)
                pag.sleep(1)
                pag.doubleClick(duration=1)
                pag.sleep(1)
                pag.write('58', interval=0.2)
                pag.sleep(0.5)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
                pag.move(63, None, duration=1) if platform == 'win32' else pag.move(48, None, duration=1)
                pag.doubleClick(duration=1)
                pag.sleep(1)
                pag.write('-1.64', interval=0.2)
                pag.sleep(1)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
                pag.move(108, None, duration=1) if platform == 'win32' else pag.move(71, None, duration=1)
                pag.doubleClick(duration=1)
                pag.sleep(1)
                pag.write('360', interval=0.2)
                pag.sleep(0.5)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
            except (ImageNotFoundException, OSError, TypeError, Exception):
                print("\nException : Tableview's INSERT button not found on the screen.")

            # Delete Selected waypoints row
            try:
                x1, y1 = pag.locateCenterOnScreen(f'{wms_path}deleteselected.png')
                pag.click(x + 150, y - 70, duration=1) if platform == 'win32' else pag.click(x + 150, y - 201,
                                                                                             duration=1)
                pag.sleep(2)
                pag.click(x1, y1, duration=1)
                pag.press('left')
                pag.sleep(1)
                pag.press('return') if platform == 'darwin' else pag.press('enter')
                pag.sleep(2)
            except (ImageNotFoundException, OSError, TypeError, Exception):
                print("\nException : Tableview's DELETE SELECTED button not found on the screen.")

            # Reverse waypoints' order
            try:
                x1, y1 = pag.locateCenterOnScreen(f'{wms_path}reverse.png')
                for _ in range(3):
                    pag.click(x1, y1, duration=1)
                    pag.sleep(1.5)
            except (ImageNotFoundException, OSError, TypeError, Exception):
                print("\nException : Tableview's REVERSE button not found on the screen.")
        except (ImageNotFoundException, OSError, TypeError, Exception):
            print("\nException : Tableview's selecttoopencontrol button (bottom part) not found on the screen.")
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : TableView's Select to open Control option (at the top) not found on the screen.")

    # Closing Table View to make space on screen
    if tv_x is not None and tv_y is not None:
        pag.click(tv_x, tv_y, duration=1)
    if platform == 'linux' or platform == 'linux2':
        pag.hotkey('altleft', 'f4')
        pag.press('left')
        pag.sleep(1)
        pag.press('enter')
    elif platform == 'win32':
        pag.hotkey('alt', 'f4')
        pag.press('left')
        pag.sleep(1)
        pag.press('enter')
    elif platform == 'darwin':
        pag.hotkey('command', 'w')
        pag.press('left')
        pag.sleep(1)
        pag.press('return')

    # Opening Linear View
    pag.sleep(1)
    pag.move(None, 400, duration=1)
    pag.click(interval=1)
    pag.hotkey('ctrl', 'l')
    pag.sleep(4)

    # Relocating Linear View
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png')
        pag.moveTo(x, y - 587, duration=1)
        if platform == 'linux' or platform == 'linux2':
            pag.dragRel(1053, 860, duration=3)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(553, 660, duration=2)
        pag.sleep(2)

        if platform == 'linux' or platform == 'linux2':
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('altleft')
            pag.sleep(1)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('right', presses=2)
            pag.keyUp('altleft')
        elif platform == 'win32':
            pag.keyDown('alt')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('alt')
            pag.sleep(1)
            pag.keyDown('alt')
            pag.press('tab')
            pag.press('right', presses=2, interval=1)
            pag.keyUp('alt')
        elif platform == 'darwin':
            pag.keyDown('command')
            pag.press('tab')
            pag.press('right')
            pag.keyUp('command')
            pag.sleep(1)
            pag.keyDown('command')
            pag.press('tab')
            pag.press('right', presses=2, interval=1)
            pag.keyUp('command')
        pag.sleep(1)
        pag.dragRel(-102, -470, duration=2) if platform == 'win32' else pag.dragRel(-90, -500, duration=2)
        lv_x, lv_y = pag.position()
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : Linearview's window header not found on the screen.")

    # Opening Linear WMS
    try:
        if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
            x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png',
                                            region=(0, int(sc_height * 0.85), sc_width, int(sc_height * 0.15)))
        elif platform == 'win32':
            x, y = pag.locateCenterOnScreen(f'{wms_path}selecttoopencontrol.png',
                                            region=(0, int(sc_height * 0.75), sc_width, int(sc_height * 0.25)))
        pag.click(x, y, duration=1)
        pag.press('down')
        pag.press('return') if platform == 'darwin' else pag.press('enter')
        pag.sleep(1)
        # Locating Server Layer
        try:
            x, y = pag.locateCenterOnScreen(f'{wms_path}layers.png', region=(0, int(sc_height * 0.75), sc_width,
                                                                             int(sc_height * 0.25)))
            pag.click(x, y, interval=2)
            # Entering wms URL
            try:
                x, y = pag.locateCenterOnScreen(f'{wms_path}wms_url.png', region=(0, int(sc_height * 0.65), sc_width,
                                                                                  int(sc_height * 0.35)))
                pag.click(x + 220, y, interval=2)
                pag.hotkey('ctrl', 'a', interval=1)
                pag.write('http://open-mss.org/', interval=0.25)
            except (ImageNotFoundException, OSError, Exception):
                print("\nException : Linearviews' \'WMS URL\' editbox button/option not found on the screen.")
            try:
                x, y = pag.locateCenterOnScreen(f'{wms_path}get_capabilities.png',
                                                region=(0, int(sc_height * 0.65), sc_width, int(sc_height * 0.35)))
                pag.click(x, y, interval=2)
                pag.sleep(3)
            except (ImageNotFoundException, OSError, Exception):
                print("\nException : LinearView's \'Get capabilities\' button/option not found on the screen.")
            if platform == 'win32':
                pag.move(-171, -390, duration=1)
                pag.dragRel(-867, 135, duration=2)
            elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
                pag.move(-171, -390, duration=1)
                pag.dragRel(-900, 245, duration=2)
            # Storing screen coordinates for List layer of side view
            ll_lv_x, ll_lv_y = pag.position()
            pag.sleep(1)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Linearview's WMS \'Server\\Layers\' button/option not found on the screen.")
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : Linearview's selecttoopencontrol not found on the screen.")

    # Selecting Some Layers in Linear wms section
    if platform == 'win32':
        gap = 22
    elif platform == 'linux' or platform == 'linux2' or platform == 'darwin':
        gap = 16
    try:
        x, y = pag.locateCenterOnScreen(f'{wms_path}horizontalwind.png', region=(0, int(sc_height / 2), sc_width,
                                                                                 int(sc_height / 2)))
        temp1, temp2 = x, y
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(1)
        pag.move(None, gap * 2, duration=1)
        pag.click(interval=1)
        pag.sleep(1)
        pag.move(None, gap, duration=1)
        pag.click(interval=1)
        pag.sleep(1)
        pag.move(None, -gap * 4, duration=1)
        pag.click(interval=1)
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Linearview's \'Horizontal Wind Layer\' option not found on the screen.")

    # Add waypoints after anaylzing the linear section wms
    try:
        x, y = pag.locateCenterOnScreen(f'{dir_path}add_waypoint.png', region=(0, 0, int(sc_width / 2), sc_height))
        pag.click(x, y, interval=2)
        pag.sleep(1)
        pag.click(x + 30, y + 50, duration=1)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\n Exception :Sideview's Add Waypoint button could not be located on the screen")

    # CLosing Linear View Layer List
    if temp1 is not None and temp2 is not None:
        pag.click(temp1, temp2 + (gap * 4), duration=2)
        pag.sleep(1)
        if platform == 'linux' or platform == 'linux2':
            pag.hotkey('altleft', 'f4')
        elif platform == 'win32':
            pag.hotkey('alt', 'f4')
        elif platform == 'darwin':
            pag.hotkey('command', 'w')
        pag.sleep(1)

    # Clicking on Linear View  Window Head
    if lv_x is not None and lv_y is not None:
        pag.click(lv_x, lv_y, duration=1)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    try:
        if platform == 'linux' or platform == 'linux2':
            for _ in range(4):
                pag.hotkey('altleft', 'f4')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('enter')
                pag.sleep(1)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.press('left')
            pag.keyUp('altleft')
            pag.sleep(1)
            pag.press('q')
        if platform == 'win32':
            for _ in range(4):
                pag.hotkey('alt', 'f4')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('enter')
                pag.sleep(1)
            pag.hotkey('alt', 'tab')
            pag.sleep(1)
            pag.press('q')
        elif platform == 'darwin':
            for _ in range(4):
                pag.hotkey('command', 'w')
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press('return')
                pag.sleep(1)
            pag.hotkey('command', 'tab')
            pag.sleep(1)
            pag.press('q')
    except Exception:
        print("Cannot automate : Enable Shortcuts for your system or try again")
    # pag.press('q')  # In some cases, recording windows does not closes. So it needs to ne there.


def main():
    """
    This function runs the above functions as different processes at the same time and can be
    controlled from here. (This is the main process.)
    """
    p1 = multiprocessing.Process(target=call_mss)
    p2 = multiprocessing.Process(target=automate_views)
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
