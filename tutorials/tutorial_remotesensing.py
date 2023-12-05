"""
    msui.tutorials.tutorial_remotesensing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to work with remote sensing tool in topview.
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

from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view,
                             create_tutorial_images, select_listelement, find_and_click_picture, zoom_in,
                             add_waypoints_to_topview)
from tutorials.utils.platform_keys import platform_keys
from mslib.utils.config import load_settings_qsettings

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_rs():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    msui_full_screen_and_open_first_view()
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    _open_remote_sensing_widget(topview["os_screen_region"])
    add_waypoints_to_topview(topview["os_screen_region"])
    _show_solar_angle(topview["os_screen_region"])
    azimuth_x, azimuth_y = _change_azimuth_angle(topview["os_screen_region"])
    _change_elevation_angle(topview["os_screen_region"])
    x, y = _draw_tangents_to_the_waypoints(topview["os_screen_region"])
    _change_tangent_distance(x, y)
    _rotate_the_tangent_by_different_angels(azimuth_x, azimuth_y, y, topview["os_screen_region"])

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


def _open_remote_sensing_widget(os_screen_region):
    # Opening Remote Sensing dockwidget
    find_and_click_picture('topviewwindow-select-to-open-control.png',
                           'topview window selection of docking widgets not found',
                           region=os_screen_region)
    select_listelement(3)
    pag.press(ENTER)
    create_tutorial_images()


def _rotate_the_tangent_by_different_angels(azimuth_x, azimuth_y, y, os_screen_region):
    zoom_in('topviewwindow-zoom.png', "Zoom Button not found",
            move=(0, 150), dragRel=(230, 150), region=os_screen_region)
    # Rotating the tangent through various angles
    pag.click(azimuth_x, azimuth_y, duration=1)
    pag.sleep(1)
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.typewrite('120', interval=0.5)
    pag.sleep(2)
    for _ in range(10):
        pag.press('down')
        pag.sleep(2)
    pag.sleep(1)
    pag.click(azimuth_x + 500, y, duration=1)
    pag.sleep(1)


def _change_tangent_distance(x, y):
    # Changing Kilometers of the tangent distance
    pag.click(x + 250, y, duration=1)
    pag.sleep(1)
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.typewrite('20', interval=1)
    pag.press(ENTER)
    pag.sleep(1)


def _draw_tangents_to_the_waypoints(os_screen_region):
    # Drawing tangents to the waypoints and path
    find_and_click_picture('topviewwindow-draw-tangent-points.png',
                           'Draw tangent points not found',
                           region=os_screen_region)
    x, y = pag.position()
    # Changing color of tangents
    pag.click(x + 160, y, duration=1)
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(1)
    return x, y


def _change_elevation_angle(os_screen_region):
    # Changing elevation angles
    find_and_click_picture('topviewwindow-elevation.png',
                           'elevation not found',
                           region=os_screen_region)
    x, y = pag.position()
    pag.click(x + 70, y, duration=1)
    pag.sleep(2)
    pag.hotkey(CTRL, 'a')
    pag.sleep(2)
    pag.typewrite('-1', interval=1)
    pag.press(ENTER)
    pag.sleep(1)
    pag.click(duration=1)
    pag.hotkey(CTRL, 'a')
    pag.typewrite('-3', interval=1)
    pag.press(ENTER)
    pag.sleep(1)


def _change_azimuth_angle(os_screen_region):
    # Changing azimuth angles
    find_and_click_picture('topviewwindow-viewing-direction-azimuth.png',
                           'Viewing direction azimuth not found',
                           region=os_screen_region)
    x, y = pag.position()
    pag.click(x + 90, y, duration=1)
    pag.move(100, 100)
    azimuth_x, azimuth_y = pag.position()
    pag.sleep(2)
    pag.hotkey(CTRL, 'a')
    pag.sleep(2)
    pag.typewrite('45', interval=1)
    pag.press(ENTER)
    pag.sleep(1)
    pag.click(duration=1)
    pag.hotkey(CTRL, 'a')
    pag.typewrite('90', interval=1)
    pag.press(ENTER)
    pag.sleep(1)
    return azimuth_x, azimuth_y


def _show_solar_angle(os_screen_region):
    # Showing Solar Angle Colors
    x, y = find_and_click_picture('topviewwindow-show-angle-degree.png',
                                  'Show angle in degrees not found',
                                  region=os_screen_region)
    for _ in range(2):
        pag.click(x + 100, y, duration=1)
        pag.press('down', interval=1)
        pag.sleep(1)
        pag.press(ENTER, interval=1)
        pag.sleep(2)
    for _ in range(3):
        pag.click(x + 200, y, duration=1)
        pag.press('down', interval=1)
        pag.sleep(1)
        pag.press(ENTER, interval=1)
        pag.sleep(2)
    pag.click(x + 200, y, duration=1)
    pag.press('up', presses=3, interval=1)
    pag.sleep(1)
    pag.press(ENTER, interval=1)
    pag.sleep(2)


if __name__ == '__main__':
    start(target=automate_rs, duration=198, dry_run=True)
