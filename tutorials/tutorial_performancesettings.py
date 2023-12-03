"""
    msui.tutorials.tutorial_performancesettings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to change the performance of flight track in table
    view such as managing fuel capacity, etc.
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
import os.path
import pyautogui as pag
import shutil
import tempfile

from tutorials.utils import start, finish, create_tutorial_images, select_listelement, \
    find_and_click_picture, type_and_key
from tutorials.utils.platform_keys import platform_keys

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_performance():
    """
    This is the main automating script of the performance settings of table view tutorial which will be recorded and
    saved to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    # Performance file path
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    ps_file_path = os.path.join(path, 'docs/samples/config/msui/performance_simple.json.sample')
    dirpath = tempfile.mkdtemp()
    sample = os.path.join(dirpath, 'example.json')
    shutil.copy(ps_file_path, sample)

    # Maximizing the window
    hotkey = WIN, 'pageup'
    try:
        pag.hotkey(*hotkey)
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")

    pag.hotkey(CTRL, 't')
    create_tutorial_images()
    pag.sleep(1)
    # Opening Performance Settings dockwidget
    find_and_click_picture('tableviewwindow-select-to-open-control.png',
                           'Select to open control not found')
    select_listelement(2)
    pag.press(ENTER)
    x, y = pag.position()

    pag.moveTo(x + 250, y - 462, duration=1)
    pag.dragRel(400, 387, duration=2)
    pag.sleep(1)

    # updating tutorial images
    create_tutorial_images()

    # Exploring through the file system and loading the performance settings json file for a dummy aircraft.
    find_and_click_picture('tableviewwindow-select.png', 'Select button not found')
    type_and_key(sample)

    # Checking the Show Performance checkbox to display the settings file in the table view
    find_and_click_picture('tableviewwindow-show-performance.png',
                           'Show performance button not found',
                           bounding_box=(0, 0, 140, 23))

    # Changing the maximum take off weight
    find_and_click_picture('tableviewwindow-maximum-take-off-weight-lb.png',
                           'Max take off weight lb not found')
    x, y = pag.position()
    pag.click(x + 318, y, duration=2)
    type_and_key('87000')
    pag.sleep(2)

    # Changing the aircraft weight of the dummy aircraft
    find_and_click_picture('tableviewwindow-aircraft-weight-no-fuel-lb.png',
                           'Aircraft weight no fuel not found')
    x, y = pag.position()
    pag.click(x + 300, y, duration=2)
    type_and_key('48000')

    # Changing the take off time of the dummy aircraft
    find_and_click_picture('tableviewwindow-take-off-time.png',
                           'take off time not found')
    x, y = pag.position()
    pag.click(x + 410, y, duration=2)
    type_and_key('')
    for _ in range(5):
        pag.press('up')
        pag.sleep(2)
    type_and_key('04', interval=0.5)

    # update tutorial images
    create_tutorial_images()

    # Showing and hiding the performance settings
    for _ in range(3):
        find_and_click_picture('tableviewwindow-show-performance.png',
                               'show performance button not found',
                               bounding_box=(0, 0, 140, 23))
        # update tutorial images
        create_tutorial_images()
        pag.sleep(2)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


if __name__ == '__main__':
    start(target=automate_performance, duration=114, dry_run=True)
