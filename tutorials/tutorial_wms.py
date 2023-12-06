"""
    msui.tutorials.tutorial_wms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use the web map service section of Mission
    Support System and plan flighttracks accordingly.

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
from tutorials.utils import (start, finish, msui_full_screen_and_open_first_view, create_tutorial_images,
                             find_and_click_picture, move_and_setup_layerchooser, get_region,
                             select_listelement)
from tutorials.utils.platform_keys import platform_keys
from mslib.utils.config import load_settings_qsettings

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_wms():
    """
    This is the main automating script of the MSS web map service tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    msui_full_screen_and_open_first_view()
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
    x, y = find_and_click_picture('multilayersdialog-multilayering.png',
                                  'Multilayering selection not found',
                                  region=tuple(tvll_region))
    pag.click()
    # Divergence and Geopotential
    pag.click(x, y + 70, interval=2)
    pag.sleep(1)
    # Relative Huminidity
    pag.click(x, y + 110, interval=2)
    pag.sleep(1)

    # let's create our helper images
    create_tutorial_images()

    # Filter layer
    find_and_click_picture('multilayersdialog-layer-filter.png',
                           'multilayers layer filter not found',
                           region=tuple(tvll_region), xoffset=150)
    pag.write('temperature', interval=0.25)
    pag.click(interval=2)
    pag.sleep(1)

    # let's create our helper images
    create_tutorial_images()
    # clear by clicking on the red X
    find_and_click_picture('multilayersdialog-temperature.png',
                           'multilayersdialog temperature not found',
                           bounding_box=(627, 0, 657, 20), region=tuple(tvll_region))

    # let's create our helper images
    create_tutorial_images()
    # star two layers
    xm, ym = find_and_click_picture('multilayersdialog-multilayering.png',
                                    'Multilayering selection not found',
                                    region=tuple(tvll_region))

    pag.click()

    # unstar Relative Huminidity
    pag.click(xm, ym + 110, interval=2)
    pag.sleep(1)

    # Filtering starred layers.
    x, y = find_and_click_picture('multilayersdialog-temperature.png',
                                  'multilayersdialog temperature not found',
                                  bounding_box=(658, 2, 677, 18), region=tuple(tvll_region))
    pag.sleep(2)
    # removing starred selection showing full list
    pag.click(x, y, interval=2)
    pag.sleep(1)

    # Load some data
    pag.click(xm + 200, ym + 70, interval=2)
    create_tutorial_images()
    pag.sleep(2)

    # Setting different levels and valid time
    region = get_region('topviewwindow-30-0-hpa.png', region=topview["os_screen_region"])
    find_and_click_picture('topviewwindow-30-0-hpa.png',
                           '30 hPa not found',
                           region=topview["os_screen_region"])
    for _ in range(5):
        select_listelement(1)
        pag.click()

    # changing level using the > and < right side
    a = region.left + region.width + 45
    b = region.top + region.height / 2

    for _ in range(3):
        pag.click(a, b)

    a = region.left + region.width + 20
    b = region.top + region.height / 2

    for _ in range(5):
        pag.click(a, b)

    region = get_region('topviewwindow-2012-10-17t12-00-00z.png',
                        region=topview["os_screen_region"])

    find_and_click_picture('topviewwindow-2012-10-17t12-00-00z.png',
                           '2012-10-17t12-00-00z not found',
                           region=topview["os_screen_region"], yoffset=30)

    for _ in range(2):
        select_listelement(1)
        pag.click()

    # changing valid time using the > and < right side
    a = region.left + region.width + 45
    b = region.top + region.height / 2

    for _ in range(3):
        pag.click(a, b)

    a = region.left + region.width + 20
    b = region.top + region.height / 2

    for _ in range(5):
        pag.click(a, b)

    # Auto-update feature of wms
    x, y = find_and_click_picture('topviewwindow-auto-update.png',
                                  'autoupdate not found',
                                  region=topview["os_screen_region"]
                                  )

    retx, rety = find_and_click_picture('topviewwindow-retrieve.png',
                                        'retrieve not found',
                                        region=topview["os_screen_region"])
    pag.click(retx, rety, interval=2)
    pag.sleep(3)
    pag.click(x, y, interval=2)
    pag.sleep(2)

    # Using and not using Cache
    find_and_click_picture('topviewwindow-use-cache.png',
                           'use cache not found',
                           region=topview["os_screen_region"])

    # select a layer
    pag.click(xm + 200, ym + 140, interval=2)
    pag.sleep(1)
    pag.click()

    # Clearing cache. The layers load slower
    find_and_click_picture('topviewwindow-clear-cache.png',
                           'Clear cache not found',
                           region=topview["os_screen_region"])
    pag.press(ENTER)
    # select a layer
    pag.click(xm + 200, ym + 110, interval=2)
    pag.sleep(1)
    pag.click()

    # transparent layer
    x, y = find_and_click_picture('topviewwindow-transparent.png',
                                  'Transparent not found',
                                  region=topview["os_screen_region"],
                                  )
    pag.click(retx, rety, interval=2)
    pag.sleep(1)
    pag.click(x, y, interval=2)
    pag.click(retx, rety, interval=2)
    pag.sleep(1)

    # Removing a Layer from the map
    x, y = find_and_click_picture('topviewwindow-remove.png',
                                  'remove not found',
                                  region=topview["os_screen_region"])

    pag.sleep(1)
    pag.click(x, y, interval=2)

    # Deleting All layers
    find_and_click_picture('topviewwindow-server-layer.png',
                           'Server layer not found',
                           region=topview["os_screen_region"])

    find_and_click_picture('multilayersdialog-multilayering.png',
                           'multilayering not found',
                           xoffset=-16, yoffset=50)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")

    # Close Everything!
    finish()


if __name__ == '__main__':
    start(target=automate_wms, duration=280)
