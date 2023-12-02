"""
    msui.tutorials.tutorial_hexagoncontrol.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to create a hexagon flightrack with the waypoints.
    Placing a centre waypoint, how we can draw a perfect hexagon flight path around it with variable radius of
    hexagon and variable angle of first waypoint of the hexagon.
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

from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils import start, finish, create_tutorial_images, select_listelement, \
    find_and_click_picture, click_center_on_screen, zoom_in, type_and_enter
from tutorials.utils.platform_keys import platform_keys
from tutorials.utils.picture import picture

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_hexagoncontrol():
    """
    This is the main automating script of the MSS hexagon control of table view which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    hotkey = WIN, 'pageup'
    try:
        pag.hotkey(*hotkey)
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")

    pag.hotkey('CTRL', 'h')
    pag.sleep(1)
    create_tutorial_images()

    # Changing map to Global
    find_and_click_picture('topviewwindow-01-europe-cyl.png',
                           "Map change dropdown could not be located on the screen")
    select_listelement(2)
    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button could not be located on the screen',
            move=(379, 205), dragRel=(70, 75))

    # Opening TableView
    pag.move(500, 0, duration=1)
    pag.click(duration=1)
    pag.sleep(1)
    pag.hotkey('ctrl', 't')
    pag.sleep(3)

    # update images, because tableview was opened
    create_tutorial_images()

    # show both open windows arranged on screen
    tv_x, tv_y = arrange_open_app_windows()

    # Opening Hexagon Control dockwidget
    if tv_x is not None and tv_y is not None:
        pag.moveTo(tv_x - 250, tv_y + 462, duration=2)
        pag.click(duration=2)
        select_listelement(1)

    create_tutorial_images()

    # Entering Centre Latitude and Centre Longitude of Delhi around which hexagon will be drawn
    try:
        x, y = pag.locateCenterOnScreen(picture('tableviewwindow-center-latitude.png'))
        pag.sleep(1)
        pag.click(x + 370, y, duration=2)
        pag.sleep(1)
        type_and_enter('28.57')
        pag.sleep(1)
        pag.click(x + 943, y, duration=2)
        pag.sleep(1)
        type_and_enter('77.10')
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Center Latitude\' button not found on the screen.")
        raise

    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.")

    # Changing the Radius of the hexagon
    try:
        x, y = pag.locateCenterOnScreen(picture('tableviewwindow-radius.png'))
        pag.click(x + 400, y, duration=2)
        pag.sleep(1)
        type_and_enter('500.00')
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Radius\' button not found on the screen.")
        raise

    find_and_click_picture('tableviewwindow-remove-hexagon.png',
                           "'Remove Hexagon' button not found on the screen.")
    pag.press(ENTER)

    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.")

    # Changing the angle of first point of the hexagon
    click_center_on_screen(picture('tableviewwindow-radius.png'), xoffset=967)
    type_and_enter('90.00')

    # Clicking on the Remove Hexagon Button
    find_and_click_picture('tableviewwindow-remove-hexagon.png',
                           "'Remove Hexagon' button not found on the screen.")
    pag.press(ENTER)

    # Clicking on the add hexagon button
    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.")

    # Changing to a different angle of first point
    x, y = pag.locateCenterOnScreen(picture('tableviewwindow-radius.png'))
    pag.sleep(1)
    pag.click(x + 967, y, duration=2)
    pag.sleep(1)
    type_and_enter('120.00')

    # Clicking on the Remove Hexagon Button
    find_and_click_picture('tableviewwindow-remove-hexagon.png',
                           "'Remove Hexagon' button not found on the screen.")
    pag.press(ENTER)
    # Clicking on the add hexagon button
    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.")

    pag.moveTo(tv_x, tv_y, duration=2)
    pag.click(duration=2)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


def arrange_open_app_windows():
    # Relocating Tableview by performing operations on table view
    tv_x = None
    tv_y = None
    try:
        x, y = pag.locateCenterOnScreen(picture('tableviewwindow-select-to-open-control.png'))
        pag.moveTo(x + 250, y - 462, duration=1)
        if platform == 'linux' or platform == 'linux2':
            # the window need to be moved a bit below the topview window
            pag.dragRel(400, 387, duration=2)
        elif platform == 'win32' or platform == 'darwin':
            pag.dragRel(200, 487, duration=2)
        pag.sleep(2)
        if platform == 'linux' or platform == 'linux2':
            # this is to select over the window manager the topview and brings it on top
            # ToDo the help search function should be used for this (ctrl f)
            pag.keyDown('altleft')
            pag.press('tab')
            pag.keyUp('tab')
            pag.press('tab')
            pag.keyUp('tab')
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
            tv_x, tv_y = pag.position()
    except (ImageNotFoundException, OSError, TypeError, Exception):
        print("\nException : TableView's Select to open Control option not found on the screen.")
        raise
    return tv_x, tv_y


if __name__ == '__main__':
    start(target=automate_hexagoncontrol, duration=170)
