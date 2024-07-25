"""
    msui.tutorials.tutorial_views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the top view, side view, table view andq
    linear view section of Mission Support System in creating a operation and planning the flightrack.

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

from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view, create_tutorial_images,
                             select_listelement, find_and_click_picture, zoom_in, type_and_key, move_window,
                             move_and_setup_layerchooser, show_other_widgets, add_waypoints_to_topview)
from tutorials.utils.platform_keys import platform_keys
from mslib.utils.config import load_settings_qsettings

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_views():
    """
    This is the main automating script of the MSS views tutorial which will cover all the views(topview, sideview,
    tableview, linear view) in demonstrating how to create an operation. This will be recorded and savedto a file having
    dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    msui_full_screen_and_open_first_view()

    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    # move topview on screen
    x_drag_rel = 910
    y_drag_rel = -10
    move_window(topview["os_screen_region"], x_drag_rel, y_drag_rel)
    create_tutorial_images()
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    add_waypoints_to_topview(topview['os_screen_region'])
    # memorize last added point
    x1, y1 = pag.position()

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
    sideview = load_settings_qsettings('sideview', {"os_screen_region": (0, 0, 0, 0)})

    # move sideview on screen
    x_drag_rel = -50
    y_drag_rel = -30
    move_window(sideview["os_screen_region"], x_drag_rel, y_drag_rel)

    pag.keyDown('altleft')
    # this selects the next window in the window manager on budgie and kde
    pag.press('tab')
    pag.keyUp('tab')
    pag.press('tab')
    pag.keyUp('tab')
    pag.keyUp('altleft')
    pag.sleep(1)
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    # Locating Server Layer
    find_and_click_picture('topviewwindow-server-layer.png',
                           'Topview Server Layer not found',
                           region=topview["os_screen_region"])
    create_tutorial_images()
    move_and_setup_layerchooser(topview["os_screen_region"], -171, -390, 10, 675)

    tvll_region = list(topview["os_screen_region"])
    tvll_region[3] = tvll_region[3] + 675

    # Selecting some layers in topview layerlist
    # lookup layer entry from the multilayering checkbox
    find_and_click_picture('multilayersdialog-multilayering.png',
                           'Multilayering selection not found',
                           region=tuple(tvll_region))

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
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    # Moving waypoints in Topview
    _tv_move_waypoints(topview["os_screen_region"], x1, y1)
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
    topview = load_settings_qsettings('topview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    find_and_click_picture('topviewwindow-00-global-cyl.png',
                           'Projection 00-global-cyl not found',
                           region=topview["os_screen_region"])
    select_listelement(2)

    # Zooming into the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button not found',
            move=(155, 121), dragRel=(260, 110),
            region=topview["os_screen_region"])
    pag.sleep(2)
    create_tutorial_images()
    sideview = load_settings_qsettings('sideview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    # SideView Operations
    # Locating Server Layer
    find_and_click_picture('sideviewwindow-server-layer.png',
                           'Sideview server layer not found',
                           region=sideview["os_screen_region"])

    create_tutorial_images()
    move_and_setup_layerchooser(sideview["os_screen_region"], -171, -390, 10, 600)

    ll_sv_x, ll_sv_y = pag.position()

    _sv_layers(sideview["os_screen_region"], tvll_region)

    find_and_click_picture('sideviewwindow-valid.png',
                           'Sideview Window not found',
                           region=sideview["os_screen_region"])
    x, y = pag.position()
    pag.click(x + 200, y, interval=1)
    pag.move(0, 80, duration=1)
    pag.press(ENTER)

    create_tutorial_images()
    sideview = load_settings_qsettings('sideview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    pag.sleep(2)
    _sv_adjust_altitude(sideview["os_screen_region"])

    create_tutorial_images()
    _sv_add_waypoints(sideview["os_screen_region"])

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
    tableview = load_settings_qsettings('tableview', {"os_screen_region": (0, 0, 0, 0)})
    # move tableview on screen
    x_drag_rel = 250
    y_drag_rel = 687
    move_window(tableview["os_screen_region"], x_drag_rel, y_drag_rel)

    show_other_widgets()

    # pag.dragRel(None, -450, duration=2)
    tv_x, tv_y = pag.position()
    pag.click(tv_x, tv_y)
    pag.sleep(1)
    tableview = load_settings_qsettings('tableview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)
    create_tutorial_images()
    # Locating the selecttoopencontrol for tableview to perform operations
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'Tableview select to open control not found',
                           region=tableview["os_screen_region"])
    # explaining the tableview
    x, xoffset, y = _tab_add_data()
    _tab_clone(tableview["os_screen_region"], x, y, xoffset)
    _tab_insert(tableview["os_screen_region"], x, y, xoffset)
    _tab_delete(tableview["os_screen_region"], x, y)
    _tab_reverse(tableview["os_screen_region"])

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
    pag.sleep(1)

    create_tutorial_images()
    linearview = load_settings_qsettings('linearview', {"os_screen_region": (0, 0, 0, 0)})

    # move linearview on screen
    x_drag_rel = 0
    y_drag_rel = 630

    move_window(linearview["os_screen_region"], x_drag_rel, y_drag_rel)

    show_other_widgets()

    lv_x, lv_y = pag.position()
    create_tutorial_images()
    linearview = load_settings_qsettings('linearview', {"os_screen_region": (0, 0, 0, 0)})
    pag.sleep(1)

    # Locating Server Layer
    find_and_click_picture('linearwindow-server-layer.png',
                           "Server layer button not found",
                           region=linearview["os_screen_region"])

    create_tutorial_images()
    move_and_setup_layerchooser(linearview["os_screen_region"], -171, -390, 900, 100)

    create_tutorial_images()

    # Selecting Some Layers in Linear wms section
    gap = 32
    find_and_click_picture('multilayersdialog-multilayering.png', 'Multilayer not found',
                           bounding_box=(18, 0, 95, 20))
    x, y = pag.position()
    # unselect multilayer
    pag.click(x, y)
    pag.sleep(1)

    # Cloudcover
    pag.click(x + 50, y + 70, interval=2)
    pag.sleep(1)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap * 2, duration=1)
    pag.click(interval=1)
    pag.sleep(3)
    pag.move(0, gap, duration=1)
    pag.click(interval=1)
    pag.sleep(3)

    # CLosing Linear View Layer List
    pag.click(x, y, duration=2)
    pag.sleep(1)
    pag.hotkey('altleft', 'f4')

    # Clicking on Linear View  Window Head
    pag.click(lv_x, lv_y, duration=1)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    finish(close_widgets=4)


def _sv_layers(os_screen_region, tvll_region):
    """

    Selects in the sideview layer chooser some layers

    :param os_screen_region: a list representing the region of the screen where the actions will be performed.
    :param tvll_region: a list representing the region of the screen that will be used for calculations.

    Return type:
    None

    Example usage:
    os_screen_region = [0, 0, 1920, 1080]
    tvll_region = [100, 100, 500, 500]
    _sv_layers(os_screen_region, tvll_region)

    """
    gap = 16
    svll_region = list(os_screen_region)
    svll_region[3] = tvll_region[3] + 600
    find_and_click_picture('multilayersdialog-multilayering.png',
                           'Multilayering not found',
                           region=tuple(svll_region))
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


def _tab_reverse(os_screen_region):
    """
    Reverses the order of a table view displayed on the screen.

    :param os_screen_region (tuple): The region of the screen where the table view is located.

    Returns:
        None
    """
    find_and_click_picture('tableviewwindow-reverse.png', 'Reverse Button not found',
                           region=os_screen_region)
    x1, y1 = pag.position()
    for _ in range(3):
        pag.click(x1, y1, duration=1)
        pag.sleep(1.5)


def _tab_delete(os_screen_region, x, y):
    """
    Delete a selected tab in a table view.

    :param os_screen_region (tuple): The region of the screen where the table view is located.
    :param x (int): The x-coordinate of the tab to delete relative to the table view.
    :param y (int): The y-coordinate of the tab to delete relative to the table view.

    Returns:
        None
    """
    find_and_click_picture('tableviewwindow-delete-selected.png', 'Delete button not',
                           region=os_screen_region)
    x1, y1 = pag.position()
    pag.click(x + 150, y - 201, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.press(ENTER)
    pag.sleep(2)


def _tab_insert(os_screen_region, x, y, xoffset):
    """
    Inserts multiple new row of waypoints into the table view.

    :param os_screen_region (tuple): The region of the screen where the table view is located.
    :param x (int): The x-coordinate of the starting position.
    :param y (int): The y-coordinate of the starting position.
    :param xoffset (int): The x-offset for clicking on the table view.

    Returns:
        None
    """
    # Inserting a new row of waypoints
    find_and_click_picture('tableviewwindow-insert.png', 'Insert button not found',
                           region=os_screen_region)
    x1, y1 = pag.position()
    pag.click(x + 117, y - 294, duration=1)
    pag.sleep(2)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + xoffset + 85, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_key('58')
    pag.sleep(1)
    pag.click(x + xoffset + 170, y - 232, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_key('360')


def _tab_clone(os_screen_region, x, y, xoffset):
    """
    Clone a table line in the specified screen region.

    :param os_screen_region: The region of the screen where the table view window is located.
    :param x: The x-coordinate of a line in the table view window.
    :param y: The y-coordinate of a line in the table view window.
    :param xoffset: The offset to be added to the x-coordinate when performing clicks.

    :return: None

    :raises: Exception - If the clone button is not found.

    Example usage:
    _tab_clone(os_screen_region, x, xoffset, y)
    """
    find_and_click_picture('tableviewwindow-clone.png', 'Clone button not found',
                           region=os_screen_region)
    x1, y1 = pag.position()
    pag.click(x + xoffset, y - 263, duration=1)
    pag.sleep(1)
    pag.click(x1, y1, duration=1)
    pag.sleep(2)
    pag.click(x + xoffset, y - 232, duration=1)
    pag.sleep(1)
    pag.click(x + xoffset + 85, y - 232, duration=1)
    pag.sleep(1)
    type_and_key('65.26')
    pag.click(x + xoffset + 550, y - 232, duration=1)
    pag.doubleClick(duration=1)
    type_and_key('Comment1')


def _tab_add_data():
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
    type_and_key('Location')
    # another waypoint name
    pag.click(x + xoffset, y - 263, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    # no blank in values
    type_and_key('StopPoint', interval=0.1)
    # Changing hPa level of waypoints
    pag.click(x + xoffset + 170, y - 232, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_key('250')
    # xoffset
    # Changing longitude of 'Location A' waypoint
    pag.click(x + xoffset + 125, y - 294, duration=1)
    pag.sleep(1)
    pag.doubleClick()
    pag.sleep(1)
    type_and_key('12.36')
    return x, xoffset, y


def _tv_move_waypoints(os_screen_region, x, y):
    find_and_click_picture('topviewwindow-mv-wp.png',
                           'Move waypoints not found',
                           region=os_screen_region)
    pag.click(x, y, interval=2)
    pag.moveTo(x, y, duration=1)
    pag.dragTo(x + 46, y - 67, duration=1, button='left')
    pag.click(interval=2)


def _sv_add_waypoints(os_screen_region):
    # Adding waypoints in SideView
    find_and_click_picture('sideviewwindow-ins-wp.png',
                           'sideview ins waypoint not found',
                           region=os_screen_region)
    x, y = pag.position()
    pag.click(x + 239, y + 186, duration=1)
    pag.sleep(3)
    pag.click(x + 383, y + 93, duration=1)
    pag.sleep(3)
    pag.click(x + 450, y + 140, duration=1)
    pag.sleep(4)
    pag.click(x, y, duration=1)
    pag.sleep(1)


def _sv_adjust_altitude(os_screen_region):
    """
    Adjusts the altitude of sideview waypoints.

    Parameters:
    - os_screen_region: The screen region where sideview is located

    Returns: None
    """
    # smaller region, seems the widget covers a bit the content
    pic_name = ('sideviewwindow-cloud-cover-0-1-vertical-section-valid-2012-10-18t06-00-00z-'
                'initialisation-2012-10-17t12-00-00z.png')
    # pic = picture(pic_name, bounding_box=(20, 20, 60, 300))
    find_and_click_picture('sideviewwindow-mv-wp.png',
                           'Sideview move wp not found',
                           region=os_screen_region)
    find_and_click_picture(pic_name, bounding_box=(187, 300, 206, 312))
    # adjust altitude of sideview waypoints
    px, py = pag.position()
    offsets = [0, 60, 93]

    for offset in offsets:
        pag.click(px + offset, py, interval=2)
        pag.moveTo(px + offset, py, duration=1)
        pag.dragTo(px + offset, py - offset - 50, duration=5, button='left')
        pag.click(interval=2)


def _tv_add_waypoints(os_screen_region):

    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Topview Window not found',
                           region=os_screen_region)
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
    start(target=automate_views, duration=567)
