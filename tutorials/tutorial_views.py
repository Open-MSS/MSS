"""
    msui.tutorials.tutorial_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the top view, side view, table view and
    linear view section of Mission Support System in creating a operation and planning the flightrack.

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
    find_and_click_picture, zoom_in, type_and_enter
from mslib.utils.config import load_settings_qsettings

CTRL, ENTER, WIN, ALT = platform_keys()

# ToDo in sideview and topview waypoint movement needs adjustment


def automate_views():
    """
    This is the main automating script of the MSS views tutorial which will cover all the views(topview, sideview,
    tableview, linear view) in demonstrating how to create a operation. This will be recorded and savedto a file having
    dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    hotkey = WIN, 'pageup'
    pag.hotkey(*hotkey)

    pag.hotkey(CTRL, 'h')
    create_tutorial_images()
    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)
    pag.sleep(1)
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Topview Window not found',
                           region=topview["os_screen_region"])

    x, y = pag.position()
    # Shifting topview window to upper right corner
    pag.click(x, y - 56, interval=2)
    pag.dragRel(910, -25, duration=2)
    pag.move(0, 56)


    tv_add_waypoints()

    # click on msui main
    pag.move(150, -150, duration=1)
    pag.click(interval=2)
    pag.sleep(1)

    hotkey = CTRL, 'up'
    pag.hotkey(*hotkey)

    # open sideview
    pag.hotkey(CTRL, 'v')
    pag.sleep(1)
    create_tutorial_images()
    sideview = load_settings_qsettings('sideview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)
    pag.sleep(1)

    pag.sleep(1)
    find_and_click_picture('sideviewwindow-ins-wp.png',
                           'Sideview Window not found',
                           region=sideview["os_screen_region"])
    sx1, sy1 = pag.position()

    pag.moveTo(sx1, sy1 - 56, duration=1)
    pag.dragRel(-50, -30, duration=2)
    pag.sleep(2)

    pag.keyDown('altleft')
    # this selects the next window in the window manager on budgie and kde
    pag.press('tab')
    pag.keyUp('tab')
    pag.press('tab')
    pag.keyUp('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    # Locating Server Layer
    find_and_click_picture('topviewwindow-server-layer.png',
                           'Topview Server Layer not found',
                           region=topview["os_screen_region"])
    create_tutorial_images()

    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Multilayder Dialog not found',
                           region=topview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)

    create_tutorial_images()
    pag.sleep(2)

    try:
        find_and_click_picture('multilayersdialog-get-capabilities.png',
                               "Get capabilities not found",
                               region=topview["os_screen_region"])
    except TypeError:
        pag.press(ENTER)

    pag.move(-171, -390, duration=1)
    pag.dragRel(10, 675, duration=2)  # To be decided
    tvll_region = topview["os_screen_region"]
    tvll_region[3] = tvll_region[3] + 675

    # Selecting some layers in topview layerlist
    # lookup layer entry from the multilayering checkbox
    find_and_click_picture('multilayersdialog-multilayering.png',
                           'Multilayering selection not found',
                           region=tvll_region)

    x, y = pag.position()
    # disable multilayer
    pag.click(x, y)
    # Divergence and Geopotential
    pag.click(x + 50, y + 70, interval=2)
    pag.sleep(1)
    # Relative Huminidity
    pag.click(x + 50, y + 110, interval=2)
    pag.sleep(1)

    create_tutorial_images()
    ll_tov_x, ll_tov_y = pag.position()
    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    # Moving waypoints in Topview
    # dtv_move_waypoints(topview, x1, y1)
    x3, y3 = pag.position()
    pag.sleep(1)

    # Deleting waypoints
    find_and_click_picture('topviewwindow-del-wp.png',
                           'Delete waypoints not found',
                           region=topview["os_screen_region"])
    pag.moveTo(x3, y3, duration=1)
    pag.click(duration=1)
    # Yes is default
    pag.sleep(3)
    pag.press(ENTER)
    pag.sleep(2)
    create_tutorial_images()
    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    find_and_click_picture('topviewwindow-01-europe-cyl.png',
                           'Projection 01-europe-cyl not found',
                           region=topview["os_screen_region"])
    select_listelement(2)

    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button not found',
            move=(155, 121), dragRel=(260, 110),
            region=topview["os_screen_region"])
    pag.sleep(2)
    create_tutorial_images()
    pag.sleep(1)
    sideview = load_settings_qsettings('sideview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    # SideView Operations
    # Locating Server Layer
    find_and_click_picture('sideviewwindow-server-layer.png',
                           'Sideview server layer not found',
                           region=sideview["os_screen_region"])

    create_tutorial_images()
    pag.sleep(1)
    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Inputfield for Url not found',
                           region=sideview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)
    try:
        find_and_click_picture('multilayersdialog-get-capabilities.png',
                               'Get capabilities not found',
                               region=sideview["os_screen_region"])
    except TypeError:
        pag.press(ENTER)

    pag.move(-171, -390, duration=1)
    pag.dragRel(10, 600, duration=2)
    ll_sv_x, ll_sv_y = pag.position()
    gap = 16

    svll_region = sideview["os_screen_region"]
    svll_region[3] = tvll_region[3] + 600

    find_and_click_picture('multilayersdialog-multilayering.png',
                           'Multilayering not found',
                           region=svll_region)
    x, y = pag.position()
    # Cloudcover
    pag.click(x + 50, y + 70, interval=2)
    pag.sleep(1)
    temp1, temp2 = x, y
    pag.click(x, y, interval=2)
    pag.sleep(3)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap * 2, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, -gap * 4, duration=1)
    pag.click(interval=1)
    pag.sleep(3)

    # Setting different levels and valid time
    pag.click(temp1, temp2 + (gap * 4), interval=2)

    find_and_click_picture('sideviewwindow-valid.png',
                           'Sideview Window not found',
                           region=sideview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 200, y, interval=1)
    pag.move(0, 80, duration=1)
    pag.press(ENTER)

    create_tutorial_images()
    pag.sleep(1)
    sideview = load_settings_qsettings('sideview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    pag.sleep(2)
    # sv_adjust_altitude(sideview)

    create_tutorial_images()
    pag.sleep(1)

    # sv_add_waypoints(sideview)

    # Closing list layer of sideview and topview to make screen a little less congested.
    pag.click(ll_sv_x, ll_sv_y, duration=2)
    pag.hotkey('altleft', 'f4')
    pag.sleep(1)
    pag.press('left')
    pag.press(ENTER)

    pag.click(ll_tov_x, ll_tov_y, duration=2)
    pag.hotkey('altleft', 'f4')
    pag.sleep(1)
    pag.press('left')
    pag.press(ENTER)

    # Table View
    # Opening Table View
    pag.move(-80, 120, duration=1)
    pag.click(duration=1)

    pag.sleep(1)
    pag.hotkey('ctrl', 't')
    pag.sleep(2)

    create_tutorial_images()
    pag.sleep(1)
    tableview = load_settings_qsettings('tableview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)
    # Relocating Tableview and performing operations on table view
    # ToDo refactor to a module improve where it enters data
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'tableview window select to open control not found',
                           region=tableview["os_screen_region"])
    x, y = pag.position()

    pag.click(x, y - 455, interval=2)
    pag.dragRel(250, 687, duration=2)
    pag.move(0, 455)

    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    pag.keyDown('altleft')
    pag.press('tab')
    pag.sleep(1)

    pag.dragRel(None, -450, duration=2)
    tv_x, tv_y = pag.position()
    pag.click(tv_x, tv_y)
    pag.sleep(1)
    tableview = load_settings_qsettings('tableview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)
    create_tutorial_images()
    pag.sleep(2)
    # Locating the selecttoopencontrol for tableview to perform operations
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'Tableview select to open control not found',
                           region=tableview["os_screen_region"])
    x, y = pag.position()

    xoffset = -100

    # Changing names of certain waypoints to predefined names
    pag.click(x + xoffset, y - 360, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    pag.sleep(2)
    pag.move(78, 0, duration=1)
    pag.sleep(1)
    pag.click(duration=1)
    pag.press('down', presses=5, interval=0.2)
    pag.sleep(1)
    pag.press('enter')
    pag.sleep(1)

    # Giving user defined names to waypoints

    pag.click(x + xoffset, y - 294, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    # marks word
    pag.doubleClick()
    type_and_enter('Location')

    pag.click(x + xoffset, y - 263, duration=1)
    pag.sleep(1)

    pag.doubleClick()
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    # no blank in values
    type_and_enter('StopPoint', interval=0.1)
    import time
    time.sleep(3)
    # Changing hPa level of waypoints
    pag.click(x + xoffset + 170, y - 232, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_enter('250')
    im = pag.screenshot(region=tableview["os_screen_region"])
    im.save('/tmp/msui/250.png')
    time.sleep(3)
    # xoffset
    # Changing longitude of 'Location A' waypoint
    pag.click(x + xoffset + 125, y - 294, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_enter('12.36')
    im = pag.screenshot(region=tableview["os_screen_region"])
    im.save('/tmp/msui/1236.png')
    time.sleep(3)

    find_and_click_picture('tableviewwindow-clone.png', 'Clone button not found',
                           region=tableview["os_screen_region"])
    x1, y1 = pag.position()

    pag.click(x + xoffset, y - 263, duration=1)
    pag.sleep(1)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + xoffset, y - 232, duration=1)
    pag.sleep(1)
    pag.click(x + xoffset + 85, y - 232, duration=1)
    pag.sleep(1)
    type_and_enter('65.26')

    pag.click(x + xoffset + 585, 0, duration=1)
    pag.doubleClick()
    type_and_enter('Comment1')

    # Inserting a new row of waypoints
    find_and_click_picture('tableviewwindow-insert.png', 'Insert button not found',
                           region=tableview["os_screen_region"])
    x1, y1 = pag.position()

    pag.click(x + 117, y - 294, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + xoffset + 85, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_enter('58')
    pag.sleep(1)

    pag.click(x + xoffset + 170, y - 232, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_enter('360')

    find_and_click_picture('tableviewwindow-delete-selected.png', 'Delete button not',
                           region=tableview["os_screen_region"])
    x1, y1 = pag.position()

    pag.click(x + 150, y - 201, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.press(ENTER)
    pag.sleep(2)

    find_and_click_picture('tableviewwindow-reverse.png', 'Reverse Button not found',
                           region=tableview["os_screen_region"])
    x1, y1 = pag.position()

    for _ in range(3):
        pag.click(x1, y1, duration=1)
        pag.sleep(1.5)

    # Closing Table View to make space on screen
    pag.click(tv_x, tv_y, duration=1)
    pag.hotkey('altleft', 'f4')
    pag.sleep(1)
    pag.press('left')
    pag.sleep(1)
    pag.press('enter')

    # Opening Linear View
    pag.sleep(1)
    pag.move(0, 400, duration=1)
    pag.click(interval=1)
    pag.hotkey(CTRL, 'l')
    pag.sleep(4)

    create_tutorial_images()
    pag.sleep(1)
    linearview = load_settings_qsettings('linearview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)
    # Relocating Linear View
    find_and_click_picture('linearwindow-select-to-open-control.png',
                           "Linearview window not found",
                           region=linearview["os_screen_region"])
    x, y = pag.position()
    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')

    pag.click(x, y)
    pag.dragRel(-90, -430, duration=2)
    pag.move(0, 56)

    lv_x, lv_y = pag.position()
    create_tutorial_images()
    pag.sleep(1)
    linearview = load_settings_qsettings('linearview', {"os_screen_region": [0, 0, 0, 0]})
    pag.sleep(1)

    # Locating Server Layer
    find_and_click_picture('linearwindow-server-layer.png',
                           "Server layer button not found",
                           region=linearview["os_screen_region"])

    create_tutorial_images()
    pag.sleep(2)
    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Url not found', region=linearview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)
    try:
        find_and_click_picture('multilayersdialog-get-capabilities.png',
                               'Get capabilities not found', region=linearview["os_screen_region"])
    except TypeError:
        pag.press(ENTER)

    pag.move(-171, -390, duration=1)
    pag.dragRel(-900, 245, duration=2)

    create_tutorial_images()
    pag.sleep(1)
    linearview = load_settings_qsettings('linearview', {"os_screen_region": [0, 0, 0, 0]})
    # Selecting Some Layers in Linear wms section
    gap = 16
    print(linearview)
    lvll_region = linearview["os_screen_region"]
    lvll_region[3] = lvll_region[0] - 900
    find_and_click_picture('multilayersdialog-multilayering.png',
                           ' Multlayer not found',
                           region=lvll_region)
    x, y = pag.position()

    # Cloudcover
    pag.click(x + 50, y + 70, interval=2)
    pag.sleep(1)
    temp1, temp2 = x, y
    pag.click(x, y, interval=2)
    pag.sleep(3)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap * 2, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, -gap * 4, duration=1)
    pag.click(interval=1)
    pag.sleep(3)

    # Add waypoints after anaylzing the linear section wms
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Topview ins wp not found',
                           region=topview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 30, y + 50, duration=1)

    # CLosing Linear View Layer List
    pag.click(temp1, temp2 + (gap * 4), duration=2)
    pag.sleep(1)
    pag.hotkey('altleft', 'f4')

    # Clicking on Linear View  Window Head
    pag.click(lv_x, lv_y, duration=1)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    finish()


def tv_move_waypoints(topview, x1, y1):
    find_and_click_picture('topviewwindow-mv-wp.png',
                           'Move waypoints not found',
                           region=topview["os_screen_region"])
    x, y = pag.position()
    # move point x1,y1
    pag.click(x1, y1, interval=2)
    pag.moveTo(x1, y1, duration=1)
    pag.dragTo(x1 + 46, y1 - 67, duration=1, button='left')
    pag.click(interval=2)

def sv_add_waypoints(sideview):
    # Adding waypoints in SideView
    find_and_click_picture('sideviewwindow-ins-wp.png',
                           'sideview ins waypoint not found',
                           region=sideview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 239, y + 186, duration=1)
    pag.sleep(3)
    pag.click(x + 383, y + 93, duration=1)
    pag.sleep(3)
    pag.click(x + 450, y + 140, duration=1)
    pag.sleep(4)
    pag.click(x, y, duration=1)
    pag.sleep(1)


def sv_adjust_altitude(sideview):
    # smaller region, seems the widget covers a bit the content
    pic_name = ('sideviewwindow-cloud-cover-0-1-vertical-section-valid-'
                '2012-10-17t12-00-00z-initialisation-2012-10-17t12-00-00z.png')
    # pic = picture(pic_name, bounding_box=(20, 20, 60, 300))
    find_and_click_picture('sideviewwindow-mv-wp.png',
                           'Sideview move wp not found',
                           region=sideview["os_screen_region"])
    find_and_click_picture(pic_name, bounding_box=(103, 300, 118, 312))
    # adjust altitude of sideview waypoints
    px, py = pag.position()
    offsets = [0, 60, 161, 200, ]
    for offset in offsets:
        pag.click(px + offset, py, interval=2)
        pag.moveTo(px + offset, py, duration=1)
        pag.dragTo(px + offset, py - offset - 50, duration=5, button='left')
        pag.click(interval=2)


def tv_add_waypoints():
    # Adding waypoints
    pag.sleep(1)
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



if __name__ == '__main__':
    start(target=automate_views, duration=567, dry_run=True)
