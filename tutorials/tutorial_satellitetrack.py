"""
    msui.tutorials.tutorial_satellitetrack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to work with remote sensing tool in topview.
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
import os.path
import pyautogui as pag
from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view,
                             create_tutorial_images, select_listelement, find_and_click_picture, type_and_key, zoom_in)
from tutorials.utils.platform_keys import platform_keys


CTRL, ENTER, WIN, ALT = platform_keys()
PATH = os.path.normpath(os.getcwd() + os.sep + os.pardir)
SATELLITE_PATH = os.path.join(PATH, 'docs/samples/satellite_tracks/satellite_predictor.txt')


def automate_rs():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    # Satellite Predictor file path
    msui_full_screen_and_open_first_view()
    pag.sleep(2)
    create_tutorial_images()

    find_and_click_picture('topviewwindow-select-to-open-control.png',
                           'topview window selection of docking widgets not found')
    select_listelement(2)
    pag.press(ENTER)
    pag.sleep(2)

    # Changing map to Global
    find_and_click_picture('topviewwindow-00-global-cyl.png',
                           "Map change dropdown could not be located on the screen")
    select_listelement(2)

    # update images
    create_tutorial_images()

    # Todo find and use QLineEdit leFile instead of Load button
    # Loading the file
    find_and_click_picture('topviewwindow-load.png', 'Load button not found', xoffset=-150)
    type_and_key(SATELLITE_PATH, interval=0.1)
    find_and_click_picture('topviewwindow-load.png', 'Load button not found')

    # Switching between different date and time of satellite overpass.
    find_and_click_picture('topviewwindow-predicted-satellite-overpasses.png',
                           'Predicted satellite button not found', xoffset=200)
    x, y = pag.position()

    pag.click(x + 200, y, duration=1)
    for _ in range(10):
        pag.click(x + 200, y, duration=1)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(ENTER)
        pag.sleep(1)
    pag.click(x + 200, y, duration=1)
    pag.press('up', presses=3, interval=1)
    pag.press(ENTER)
    pag.sleep(1)

    # update images
    create_tutorial_images()

    # enable adding waypoints
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Clickable button/option not found.')

    # set waypoints
    pag.move(111, 153, duration=2)
    pag.click(interval=2)
    pag.sleep(1)
    pag.move(36, 82, duration=2)
    pag.click(interval=2)
    pag.sleep(1)

    # update images
    create_tutorial_images()
    pag.sleep(1)

    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button could not be located.',
            move=(260, 130), dragRel=(184, 135))

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish(close_widgets=2)


if __name__ == '__main__':
    start(target=automate_rs, duration=170)
