"""
    msui.tutorials.tutorial_waypoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to play with and use waypoints
    for activating/creating a flight track.

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
import datetime

from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view, select_listelement,
                             find_and_click_picture, zoom_in, panning)
from tutorials.utils.platform_keys import platform_keys

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_waypoints():
    """
    This is the main automating script of the MSS waypoints tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    msui_full_screen_and_open_first_view()

    # enable adding waypoints
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Clickable button/option not found.')

    # set waypoints
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

    # enable moving waypoints
    find_and_click_picture('topviewwindow-mv-wp.png',
                           ' Move Waypoint button could not be located.')

    # moving waypoints
    pag.moveTo(x2, y2, duration=1)
    pag.click(interval=2)
    pag.dragRel(100, 150, duration=1)
    pag.moveTo(x1, y1, duration=1)
    pag.dragRel(35, -50, duration=1)
    x1, y1 = pag.position()

    # enable deleting waypoints
    find_and_click_picture('topviewwindow-del-wp.png',
                           'Remove Waypoint button could not be located.')

    # delete waypoints
    pag.moveTo(x1, y1, duration=1)
    pag.click(duration=1)
    # Yes is default
    pag.sleep(3)
    pag.press(ENTER)
    pag.sleep(2)

    # Changing map to Global
    find_and_click_picture('topviewwindow-00-global-cyl.png',
                           "Map change dropdown could not be located.")
    select_listelement(2)
    pag.sleep(5)

    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button could not be located.',
            move=(150, 200), dragRel=(400, 250))

    # Panning into the map
    panning('topviewwindow-pan.png', 'Pan button could not be located.',
            moveRel=(400, 400), dragRel=(-100, -50))

    # another panning, button is still active
    pag.move(-20, -25, duration=1)
    pag.dragRel(90, 50, duration=2)
    pag.sleep(5)

    # Switching to the previous appearance of the map
    find_and_click_picture('topviewwindow-back.png', 'back button could not be located.')
    pag.sleep(5)

    # Switching to the next appearance of the map
    find_and_click_picture('topviewwindow-forward.png', 'forward button could not be located.')
    pag.sleep(5)

    # Resetting the map to the original size
    find_and_click_picture('topviewwindow-home.png', 'home button could not be located.')
    pag.sleep(3)

    # Saving the figure
    find_and_click_picture('topviewwindow-save.png', 'save button could not be located.')
    current_time = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
    pag.hotkey('altleft', 'tab')  # if the save file system window is not in the forefront, use this statement.
    # This can happen sometimes. At that time, you just need to uncomment it.
    pag.write(f'Fig_{current_time}.png', interval=0.25)
    pag.press(ENTER)
    pag.sleep(2)
    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish(close_widgets=2)


if __name__ == '__main__':
    start(target=automate_waypoints, duration=158)
