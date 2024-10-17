"""
    msui.tutorials.tutorial_hexagoncontrol.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to create a hexagon flightrack with the waypoints.
    Placing a centre waypoint, how we can draw a perfect hexagon flight path around it with variable radius of
    hexagon and variable angle of first waypoint of the hexagon.
    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2024 by the MSS team, see AUTHORS.
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

from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view, create_tutorial_images, move_window,
                             select_listelement, find_and_click_picture, zoom_in, type_and_key)
from tutorials.utils.platform_keys import platform_keys
from mslib.utils.config import load_settings_qsettings

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_hexagoncontrol():
    """
    This is the main automating script of the MSS hexagon control of table view which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    pag.sleep(5)
    msui_full_screen_and_open_first_view()

    # Changing map to Global
    find_and_click_picture('topviewwindow-00-global-cyl.png',
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

    # show both open windows arranged on screen and open hexagon control widget
    _arrange_open_app_windows()
    tableview = load_settings_qsettings('tableview', {"os_screen_region": (0, 0, 0, 0)})
    create_tutorial_images()

    # Entering Centre Latitude and Centre Longitude of Delhi around which hexagon will be drawn
    find_and_click_picture('tableviewwindow-0-00-degn.png',
                           '0.00 degN not found',
                           region=tableview["os_screen_region"])
    type_and_key('28.57')
    find_and_click_picture('tableviewwindow-0-00-dege.png',
                           '0.00 degE not found',
                           region=tableview["os_screen_region"])
    type_and_key('77.10')
    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.",
                           region=tableview["os_screen_region"])

    # Changing the Radius of the hexagon
    find_and_click_picture('tableviewwindow-200-00-km.png', '200 km not found',
                           region=tableview["os_screen_region"])
    type_and_key('500.00')
    create_tutorial_images()
    find_and_click_picture('tableviewwindow-remove-hexagon.png',
                           "'Remove Hexagon' button not found on the screen.",
                           region=tableview["os_screen_region"])
    pag.press(ENTER)
    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.",
                           region=tableview["os_screen_region"])

    # Changing the angle of first point of the hexagon
    find_and_click_picture('tableviewwindow-0-00-deg.png', '0.00 deg not found',
                           region=tableview["os_screen_region"])
    type_and_key('90.00')

    _remove_hexagon()
    _add_hexagon()

    create_tutorial_images()
    # Changing to a different angle of first point
    find_and_click_picture('tableviewwindow-90-00-deg.png', '90.00 deg not found',
                           region=tableview["os_screen_region"])
    type_and_key('120.00')

    _remove_hexagon()
    create_tutorial_images()
    _add_hexagon()

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


def _add_hexagon():
    # Clicking on the add hexagon button
    find_and_click_picture('tableviewwindow-add-hexagon.png',
                           "'Add Hexagon' button not found on the screen.")


def _remove_hexagon():
    # Clicking on the Remove Hexagon Button
    find_and_click_picture('tableviewwindow-remove-hexagon.png',
                           "'Remove Hexagon' button not found on the screen.")
    pag.press(ENTER)


def _arrange_open_app_windows():
    # Relocating Tableview by performing operations on table view
    tableview = load_settings_qsettings('tableview', {"os_screen_region": (0, 0, 0, 0)})
    x_drag_rel = 250
    y_drag_rel = 687
    move_window(tableview["os_screen_region"], x_drag_rel, y_drag_rel)
    tableview = load_settings_qsettings('tableview', {"os_screen_region": (0, 0, 0, 0)})
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'select to open control not found',
                           region=tableview["os_screen_region"])
    select_listelement(1)

    pag.sleep(1)
    create_tutorial_images()

    pag.keyDown('altleft')
    pag.press('tab')
    pag.keyUp('tab')
    pag.press('tab')
    pag.keyUp('tab')
    pag.keyUp('altleft')
    pag.sleep(1)


if __name__ == '__main__':
    start(target=automate_hexagoncontrol, duration=170)
