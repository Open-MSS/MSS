"""
    msui.tutorials.tutorial_kml
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to overlay kml flles on top of the map in topview.
    kml(key hole markup language) is an XML based file format for demonstrating geographical context. This will
    demonstrate how to customize the kml files and other various operations on it.
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

import os
import pyautogui as pag
from tutorials.utils import (start, finish,
                             change_color, create_tutorial_images, find_and_click_picture,
                             load_kml_file, select_listelement, type_and_key, msui_full_screen_and_open_first_view
                             )
from tutorials.utils.platform_keys import platform_keys

CTRL, ENTER, WIN, ALT = platform_keys()


def automate_kml():
    pag.sleep(5)
    msui_full_screen_and_open_first_view()
    _switch_to_europe_map()
    _create_and_load_kml_files()
    _change_color_and_linewidth()
    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish(close_widgets=2)


def _switch_to_europe_map():
    find_and_click_picture('topviewwindow-00-global-cyl.png', "Map change dropdown could not be located on the screen.")
    select_listelement(2)
    pag.sleep(1)
    create_tutorial_images()


def _create_and_load_kml_files():
    parent_path = os.path.normpath(os.path.join(os.getcwd(), os.pardir))
    kml_folder_path = os.path.join(parent_path, 'docs/samples/kml')
    _load_kml_files(kml_folder_path)
    pag.sleep(1)
    create_tutorial_images()


def _load_kml_files(kml_folder_path):
    create_tutorial_images()
    find_and_click_picture('topviewwindow-select-to-open-control.png',
                           "'select to open control' button/option not found on the screen.")
    select_listelement(4)
    create_tutorial_images()
    _load_individual_kml_file('folder.kml', kml_folder_path)
    # cursor is on center of the button, moving it so it can be found on screen
    pag.move(100, 100)
    create_tutorial_images()
    _load_individual_kml_file('color.kml', kml_folder_path)
    pag.sleep(1)
    create_tutorial_images()


def _load_individual_kml_file(kml_filename, kml_folder_path):
    kml_file_path = os.path.join(kml_folder_path, f'{kml_filename}')
    load_kml_file('topviewwindow-add-kml-files.png', kml_file_path, "'Add KML Files' button not found on the screen.")
    pag.sleep(1)
    create_tutorial_images()


def _change_color_and_linewidth():
    find_and_click_picture('topviewwindow-select-all-files.png',
                           "'Select All Files(Unselecting & Selecting)' button not found on the screen.")
    create_tutorial_images()
    pag.move(-200, 0, duration=1)
    pag.click(interval=2)
    _change_color('topviewwindow-change-color.png',
                  lambda: (pag.move(-220, -300, duration=1), pag.click(interval=2), pag.press(ENTER)))
    create_tutorial_images()
    _change_linewidth('topviewwindow-2-00.png', lambda: (pag.hotkey(CTRL, 'a'),
                                                         [pag.press('down') for _ in range(8)],
                                                         type_and_key('2.50'), pag.sleep(1),
                                                         type_and_key('5.50')))


def _change_color(img_name, actions):
    change_color(img_name, "'Change Color' button not found on the screen.", actions, interval=2)


def _change_linewidth(img_name, actions):
    change_color(img_name, "'Change Linewidth' button not found on the screen.", actions, interval=2)


if __name__ == '__main__':
    start(target=automate_kml, duration=130)
