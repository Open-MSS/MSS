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

from tutorials.utils import platform_keys, start, finish, create_tutorial_images, select_listelement, \
    find_and_click_picture, zoom_in


CTRL, ENTER, WIN, ALT = platform_keys()


def automate_rs():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
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
    pag.sleep(2)
    create_tutorial_images()

    # Opening Remote Sensing dockwidget
    find_and_click_picture('topviewwindow-select-to-open-control.png',
                           'topview window selection of docking widgets not found')
    select_listelement(3)
    pag.press(ENTER)
    pag.sleep(2)

    # update tutorial images
    create_tutorial_images()

    # enable adding waypoints
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Clickable button/option not found.')

    # Adding waypoints for demonstrating remote sensing
    x, y = pag.position()
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

    # Showing Solar Angle Colors
    find_and_click_picture('topviewwindow-show-angle-degree.png',
                           'Show angle in degrees not found')
    x, y = pag.position()

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

    # Changing azimuth angles
    find_and_click_picture('topviewwindow-viewing-direction-azimuth.png',
                           'Viewing direction azimuth not found')
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

    # Changing elevation angles
    find_and_click_picture('topviewwindow-elevation.png', 'elevation not found')
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


    # Drawing tangents to the waypoints and path
    find_and_click_picture('topviewwindow-draw-tangent-points.png',
                           'Draw tangent points not found')
    x, y = pag.position()
    # Changing color of tangents
    pag.click(x + 160, y, duration=1)
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(1)

    # Changing Kilometers of the tangent distance
    pag.click(x + 250, y, duration=1)
    pag.sleep(1)
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.typewrite('20', interval=1)
    pag.press(ENTER)
    pag.sleep(1)

    zoom_in('topviewwindow-zoom.png', "Zoom Button not found",
            move=(0, 150), dragRel=(230, 150))


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


    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_rs, duration=198, dry_run=True)
