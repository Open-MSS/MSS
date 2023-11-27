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
    find_and_click_picture, zoom_in, type_and_enter, get_region
from tutorials.utils.picture import picture

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

    # Screen Resolutions
    sc_width, sc_height = pag.size()[0] - 1, pag.size()[1] - 1

    hotkey = WIN, 'pageup'
    pag.hotkey(*hotkey)

    pag.hotkey(CTRL, 'h')
    create_tutorial_images()
    pag.sleep(1)

    find_and_click_picture('topviewwindow-ins-wp.png', 'Topview Window not found')
    x, y = pag.position()
    # Shifting topview window to upper right corner
    pag.click(x, y - 56, interval=2)
    pag.dragRel(910, -25, duration=2)
    pag.move(0, 56)

    # Adding waypoints
    pag.sleep(1)
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

    # use CTRL UP instead
    pag.move(-686, -56, duration=1)
    pag.click(interval=1)

    pag.hotkey(CTRL, 'v')
    create_tutorial_images()
    pag.sleep(1)

    find_and_click_picture('sideviewwindow-ins-wp.png', 'Sideview Window not found')
    x1, y1 = pag.position()

    pag.moveTo(x1, y1 - 56, duration=1)
    pag.dragRel(-50, -30, duration=2)
    pag.sleep(2)

    pag.keyDown('altleft')
    # ToDo selection of views have to be done with ctrl f
    # this selects the next window in the window manager on budgie and kde
    pag.press('tab')
    pag.keyUp('tab')
    pag.press('tab')
    pag.keyUp('tab')
    pag.keyUp('altleft')

    # Locating Server Layer
    find_and_click_picture('topviewwindow-server-layer.png',
                           'Topview Server Layer not found',
                           region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    create_tutorial_images()
    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Multilayder Dialog not found',
                           region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)

    create_tutorial_images()
    pag.sleep(1)
    find_and_click_picture('multilayersdialog-get-capabilities.png',
                           "Get capabilities not found")
    pag.move(-171, -390, duration=1)
    pag.dragRel(10, 675, duration=2)  # To be decided

    # Selecting some layers in topview layerlist
    # lookup layer entry from the multilayering checkbox
    find_and_click_picture('multilayersdialog-multilayering.png',
                           'Multilayering selection not found')

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
    print(int(sc_width / 2) - 100, 0, sc_width, sc_height)
    # Moving waypoints in Topview
    find_and_click_picture('topviewwindow-mv-wp.png',
                           'Move waypoints not found',
                           region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    x, y = pag.position()
    # move point x1,y1
    pag.click(x1, y1, interval=2)
    pag.moveTo(x1, y1, duration=1)
    pag.dragTo(x1 + 46, y1 - 67, duration=1, button='left')
    pag.click(interval=2)
    x3, y3 = pag.position()
    pag.sleep(1)

    # Deleting waypoints
    find_and_click_picture('topviewwindow-del-wp.png',
                           'Delete waypoints not found',
                           region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    x, y = pag.position()
    pag.click(x, y, interval=2)
    pag.moveTo(x3, y3, duration=1)
    pag.click(duration=1)
    pag.press('enter', interval=1)
    create_tutorial_images()

    find_and_click_picture('topviewwindow-01-europe-cyl.png',
                           'Projection 01-europe-cyl not found',
                           region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    select_listelement(2)

    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button not found',
            move=(155, 121), dragRel=(260, 110),
            region=(int(sc_width / 2) - 100, 0, sc_width, sc_height))
    pag.sleep(4)

    # SideView Operations
    # Opening web map service
    #find_and_click_picture('sideviewwindow-select-to-open-control.png',
    #                       'Sideview select to open control not found',
    #                       region=(0, 0, int(sc_width / 2) - 100, sc_height))
    select_listelement(1)

    # Locating Server Layer
    find_and_click_picture('sideviewwindow-server-layer.png',
                           'Sideview server layer not found',
                           region=(0, 0, int(sc_width / 2) - 100, sc_height))
    find_and_click_picture('multilayersdialog-http-localhost-8081.png',
                           'Inputfield for Url not found')
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)

    find_and_click_picture('multilayersdialog-get-capabilities.png',
                           'Get capabilities not found')
    pag.move(-171, -390, duration=1)
    pag.dragRel(10, 600, duration=2)
    ll_sv_x, ll_sv_y = pag.position()
    gap = 16

    find_and_click_picture('multilayersdialog-multilayering.png', 'Multilayering not found')
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

    find_and_click_picture('sideviewwindow-valid.png', 'Sideview Window not found')
    x, y = pag.position()
    pag.click(x + 200, y, interval=1)
    pag.move(0, 80, duration=1)

    create_tutorial_images()
    pag.sleep(2)
    # smaller region, seems the widget covers a bit the content
    pic_name = 'sideviewwindow-cloud-cover-0-1-vertical-section-valid-2012-10-18t06-00-00z-initialisation-2012-10-17t12-00-00z.png'
    pic = picture(pic_name, bounding_box=(20, 20, 800, 200))
    loc = get_region(pic)
    sideview_region = (0, 0, loc.left + loc.width, loc.top)
    find_and_click_picture('sideviewwindow-mv-wp.png',
                           'Sideview not found',
                           region=sideview_region)
    pic_name = 'sideviewwindow-cloud-cover-0-1-vertical-section-valid-2012-10-18t06-00-00z-initialisation-2012-10-17t12-00-00z.png'
    find_and_click_picture(pic_name, bounding_box=(103, 300, 118, 312))
    px, py = pag.position()
    offsets = [0, 114, 161, 200, ]
    for offset in offsets:
        pag.click(px + offset, py, interval=2)
        pag.moveTo(px + offset, py, duration=1)
        pag.dragTo(px + offset, py - offset - 50, duration=5, button='left')
        pag.click(interval=2)

    create_tutorial_images()
    pag.sleep(1)

    # Adding waypoints in SideView
    find_and_click_picture('sideviewwindow-ins-wp.png', region=sideview_region)
    x, y = pag.position()
    pag.click(x + 239, y + 186, duration=1)
    pag.sleep(3)
    pag.click(x + 383, y + 93, duration=1)
    pag.sleep(3)
    pag.click(x + 450, y + 140, duration=1)
    pag.sleep(4)
    pag.click(x, y, duration=1)
    pag.sleep(1)

    # Closing list layer of sideview and topview to make screen a little less congested.
    ll_tov_x, ll_tov_y = pag.position()
    pag.click(ll_sv_x, ll_sv_y, duration=2)
    pag.hotkey('altleft', 'f4')
    pag.sleep(1)

    pag.click(ll_tov_x, ll_tov_y, duration=2)
    pag.hotkey('altleft', 'f4')

    # Table View
    # Opening Table View
    pag.move(-80, 120, duration=1)
    pag.click(duration=1)

    pag.sleep(1)
    pag.hotkey('ctrl', 't')
    pag.sleep(2)

    create_tutorial_images()
    # Relocating Tableview and performing operations on table view
    # ToDo refactor to a module improve where it enters data
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'tableview window select to open control not found')
    x, y = pag.position()

    pag.moveTo(x, y - 462, duration=1)
    pag.dragRel(250, 887, duration=3)

    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    pag.keyDown('altleft')
    pag.press('tab')
    pag.press('tab', presses=2)  # This needs to be checked in Linux
    pag.keyUp('altleft')
    pag.sleep(1)

    pag.dragRel(None, -450, duration=2)
    tv_x, tv_y = pag.position()

    # Locating the selecttoopencontrol for tableview to perform operations
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'Tableview select to open control not found')
    x, y = pag.position()

    xoffset = -50

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
    pag.doubleClick(duration=1)
    pag.sleep(1.5)
    type_and_enter('Location A')

    pag.click(x + xoffset, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    pag.sleep(2)
    type_and_enter('Stop Point', interval=0.1)

    # offset is wrong
    # Changing Length of Flight Level
    pag.click(x + 236, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    type_and_enter('319')

    # Changing hPa level of waypoints
    pag.click(x + 367, y - 232, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    type_and_enter('250')

    # xoffset
    # Changing longitude of 'Location A' waypoint
    pag.click(x + 165, y - 294, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    pag.sleep(1)
    type_and_enter('12.36')

    find_and_click_picture('tableviewwindow-clone.png', 'Clone button not found')
    x1, y1 = pag.position()

    pag.click(x + xoffset + 15, y - 263, duration=1)
    pag.sleep(1)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + xoffset + 15, y - 232, duration=1)
    pag.sleep(1)
    pag.click(x + xoffset + 117, y - 232, duration=1)
    pag.sleep(1)
    type_and_enter('65.26')

    pag.move(459, 0, duration=1)
    pag.doubleClick(duration=1)
    type_and_enter('This is a reference comment')

    # Inserting a new row of waypoints
    find_and_click_picture('tableviewwindow-insert.png', 'Insert button not found')
    x1, y1 = pag.position()

    pag.click(x + 117, y - 294, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + 117, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick(duration=1)
    pag.sleep(1)
    type_and_enter('58')
    pag.sleep(1)

    pag.move(48, 0, duration=1)
    pag.doubleClick(duration=1)
    type_and_enter('-1.64')
    pag.sleep(1)
    pag.move(71, 0, duration=1)
    type_and_enter('360')

    find_and_click_picture('tableviewwindow-delete-selected.png', 'Delete button not')
    x1, y1 = pag.position()

    pag.click(x + 150, y - 201, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.press('left')
    pag.press(ENTER)
    pag.sleep(2)

    find_and_click_picture('tableviewwindow-reverse.png', 'Reverse Button not found')
    x1, y1 = pag.position()

    for _ in range(3):
        pag.click(x1, y1, duration=1)
        pag.sleep(1.5)

    # Closing Table View to make space on screen
    pag.click(tv_x, tv_y, duration=1)
    pag.hotkey('altleft', 'f4')
    pag.press('left')
    pag.sleep(1)
    pag.press('enter')

    # Opening Linear View
    pag.sleep(1)
    pag.move(0, 400, duration=1)
    pag.click(interval=1)
    pag.hotkey('ctrl', 'l')
    pag.sleep(4)
    pag.hotkey(WIN, 'up')
    pag.click(10, 10, interval=2)
    pag.dragRel(853, 360, duration=3)
    pag.sleep(2)

    create_tutorial_images()
    # Relocating Linear View
    find_and_click_picture('linearwindow-select-to-open-control.png')

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

    pag.dragRel(-90, -500, duration=2)
    lv_x, lv_y = pag.position()

    # Locating Server Layer
    find_and_click_picture('linearwindow-server-layer.png', "Server layer button not found")
    create_tutorial_images()
    find_and_click_picture('multilayersdialog-http-localhost-8081.png', 'Url not found')
    x, y = pag.position()
    pag.click(x + 220, y, interval=2)
    type_and_enter('http://open-mss.org/', interval=0.1)
    find_and_click_picture('multilayersdialog-get-capabilities.png', 'Get capabilities not found')
    pag.move(-171, -390, duration=1)
    pag.dragRel(-900, 245, duration=2)

    create_tutorial_images()
    # Selecting Some Layers in Linear wms section
    gap = 16

    find_and_click_picture('multilayersdialog-multilayering.png', ' Multlayer not found')
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
    find_and_click_picture('topviewwindow-ins-wp.png', 'Topview ins wp not found')
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


if __name__ == '__main__':
    start(target=automate_views, duration=567, dry_run=True)
