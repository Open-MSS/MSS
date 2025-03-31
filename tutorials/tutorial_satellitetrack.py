"""
    msui.tutorials.tutorial_satellitetrack
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to work with remote sensing tool in topview.
    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2025 by the MSS team, see AUTHORS.
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


# Import platform-specific key combinations for cross-platform compatibility
CTRL, ENTER, WIN, ALT = platform_keys()
# Set up the base path for finding files
PATH = os.path.normpath(os.getcwd() + os.sep + os.pardir)
# Path to the sample satellite predictor file used in this tutorial
SATELLITE_PATH = os.path.join(PATH, 'docs/samples/satellite_tracks/satellite_predictor.txt')


def automate_rs():
    """
    This is the main automating script of the MSS remote sensing tutorial which will be recorded and saved
    to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)  # Pause for 5 seconds to allow the MSS GUI to fully load
    
    # Maximize the MSS window and open the first view (TopView)
    msui_full_screen_and_open_first_view()
    pag.sleep(2)  # Short pause to ensure the view is loaded
    
    # Create screenshot references for automated detection of UI elements
    create_tutorial_images()

    # Open the docking widgets control panel in TopView
    find_and_click_picture('topviewwindow-select-to-open-control.png',
                           'topview window selection of docking widgets not found')
    select_listelement(2)  # Select the second item in the list (Remote Sensing)
    pag.press(ENTER)  # Press Enter to open the selected control panel
    pag.sleep(2)  # Pause to allow the panel to open

    # Change the map projection to Global cylindrical projection
    find_and_click_picture('topviewwindow-00-global-cyl.png',
                           "Map change dropdown could not be located on the screen")
    select_listelement(7)  # Select the 7th map option (Global)

    # Update screenshot references after map change
    create_tutorial_images()

    # TODO: Improve by using QLineEdit leFile instead of the Load button
    # Load the satellite predictor file
    # First, click near the file input field (150px to the left of the Load button)
    find_and_click_picture('topviewwindow-load.png', 'Load button not found', xoffset=-150)
    # Type the path to the satellite predictor file
    type_and_key(SATELLITE_PATH, interval=0.1)
    # Click the Load button to load the file
    find_and_click_picture('topviewwindow-load.png', 'Load button not found')

    # Demonstrate how to switch between different satellite overpass times
    # First, click on the predicted satellite overpasses dropdown
    find_and_click_picture('topviewwindow-predicted-satellite-overpasses.png',
                           'Predicted satellite button not found', xoffset=200)
    x, y = pag.position()  # Store current cursor position
    
    # Click on the dropdown and cycle through 10 different overpass times
    pag.click(x + 200, y, duration=1)  # Click on the dropdown
    for _ in range(10):
        pag.click(x + 200, y, duration=1)  # Open the dropdown
        pag.sleep(1)  # Pause to let the dropdown open
        pag.press('down')  # Move down to the next overpass time
        pag.sleep(1)  # Pause to show the selection
        pag.press(ENTER)  # Select the highlighted time
        pag.sleep(1)  # Pause to show the result
    
    # Return to an earlier overpass time (3 positions up from current)
    pag.click(x + 200, y, duration=1)  # Open the dropdown again
    pag.press('up', presses=3, interval=1)  # Move up 3 positions
    pag.press(ENTER)  # Select the highlighted time
    pag.sleep(1)  # Pause to show the result

    # Update screenshot references after changing overpass times
    create_tutorial_images()

    # Enable waypoint insertion mode
    find_and_click_picture('topviewwindow-ins-wp.png',
                           'Clickable button/option not found.')

    # Set two waypoints at specific coordinates on the map
    pag.move(111, 153, duration=2)  # Move to first waypoint location
    pag.click(interval=2)  # Click to set the waypoint
    pag.sleep(1)  # Pause to show the waypoint being set
    pag.move(36, 82, duration=2)  # Move to second waypoint location
    pag.click(interval=2)  # Click to set the waypoint
    pag.sleep(1)  # Pause to show the waypoint being set

    # Update screenshot references after setting waypoints
    create_tutorial_images()
    pag.sleep(1)  # Short pause

    # Zoom into a specific area of the map
    zoom_in('topviewwindow-zoom.png', 'Zoom button could not be located.',
            move=(260, 130), dragRel=(184, 135))  # Zoom in by clicking and dragging

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    # Clean up by closing widgets and finishing the recording
    finish(close_widgets=2)  # Close 2 widgets before finishing


if __name__ == '__main__':
    # Entry point when script is run directly
    # Start the automation with a duration of 170 seconds
    start(target=automate_rs, duration=170)
