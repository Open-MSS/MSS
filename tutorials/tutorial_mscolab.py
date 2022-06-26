"""
    msui.tutorials.tutorial_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use Mission Support System Collaboration for users
    to collaborate in flight planning and thereby explain how to use it's various functionalities.
    This file is part of MSS.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021-2022 by the MSS team, see AUTHORS.
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
import multiprocessing
import sys
import os.path
from sys import platform
from pyscreeze import ImageNotFoundException
from tutorials.utils.__init__ import initial_ops, call_recorder, call_msui, platform_keys, finish
from tutorials.pictures import picture

def automate_mscolab():
    """
    This is the main automating script of the Mission Support System Collaboration or Mscolab tutorial which will be
    recorded and saved to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)

    ctrl, enter, win, alt = platform_keys()

    # Different inputs required in mscolab
    username = 'John Doe'
    email = 'johndoe@gmail.com'
    password = 'johndoe'
    p_name = 'operation_of_john_doe'
    p_description = """This is John Doe's operation. He wants his collegues and friends to collaborate on this operation
    with him in the network. Mscolab, here, will be very helpful for Joe with various features to use!"""
    chat_message1 = 'Hi buddy! What\'s the next plan? I have marked the points in topview for the dummy operation.' \
                    'Just have a look, please!'
    chat_message2 = 'Hey there user! This is the chat feature of MSCOLAB. You can have a conversation with your ' \
                    'fellow mates about the operation and discuss ideas and plans.'
    search_message = 'chat feature of MSCOLAB'
    localhost_url = 'http://localhost:8083'

    # Example upload of msui logo during Chat Window demonstration.
    path = os.path.normpath(os.getcwd() + os.sep + os.pardir)
    example_image_path = os.path.join(path, 'docs/msui-logo.png')

    file_x, file_y = None, None
    open_operations_x, open_operations_y = None, None
    selectall_left_x, selectall_left_y = None, None
    selectall_right_x, selectall_right_y = None, None
    modify_x, modify_y = None, None
    previous_x, previous_y = None, None
    work_async_x, work_async_y = None, None
    wp1_x, wp1_y = None, None
    wp2_x, wp2_y = None, None
    sc_width, sc_height = pag.size()[0] - 1, pag.size()[1] - 1
    # Maximizing the window
    try:
        pag.hotkey('ctrl', 'command', 'f') if platform == 'darwin' else pag.hotkey(win, 'up')
    except Exception:
        print("\nException : Enable Shortcuts for your system or try again!")
        raise
    pag.sleep(4)

    # Connecting to Mscolab (Mscolab localhost server must be activated beforehand for this to work)
    try:
        x, y = pag.locateCenterOnScreen(picture('mscolab', 'connect_to_mscolab.png'))
        pag.sleep(1)
        pag.click(x, y, duration=2)
        pag.sleep(2)

        # Entering local host URL
        try:
            x1, y1 = pag.locateCenterOnScreen(picture('mscolab', 'connect.png'))
            pag.click(x1 - 100, y1, duration=2)
            pag.sleep(1)
            pag.hotkey(ctrl, 'a')
            pag.sleep(1)
            pag.hotkey(ctrl, 'a')
            pag.typewrite(localhost_url, interval=0.2)
            pag.sleep(1)
            pag.click(x1, y1, duration=2)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Connect (to localhost)\' button not found on the screen.")
            raise
        # Adding a new user
        try:
            x2, y2 = pag.locateCenterOnScreen(picture('mscolab', 'add_user.png'))
            pag.click(x2, y2, duration=2)
            pag.sleep(4)

            # Entering details of new user
            new_user_input = [username, email, password, password]
            for input in new_user_input:
                pag.typewrite(input, interval=0.2)
                pag.sleep(1)
                pag.press('tab')
                pag.sleep(2)
            pag.press('tab')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(2)

            if pag.locateCenterOnScreen(picture('mscolab', 'emailid_taken.png')) is not None:
                print("The email id you have provided is already registered!")
                pag.sleep(1)
                pag.press('left')
                pag.sleep(1)
                pag.press(enter)
                pag.sleep(2)

            # Entering details of the new user that's created
            pag.press('tab', presses=2, interval=1)
            pag.typewrite(email, interval=0.2)
            pag.press('tab')
            pag.typewrite(password, interval=0.2)

        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Add user\' button not found on the screen.")
            raise
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Connect to Mscolab\' button not found on the screen.")
        raise

    # Opening a new Mscolab Operation
    try:
        file_x, file_y = pag.locateCenterOnScreen(picture('mscolab', 'file.png'))
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        for _ in range(2):
            pag.press('down')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(2)
        pag.press('tab')

        for input in [p_name, p_description]:
            pag.typewrite(input, interval=0.05)
            pag.press('tab')
            pag.sleep(2)

        try:
            x1, y1 = pag.locateCenterOnScreen(picture('mscolab', 'addop_ok.png'))
            pag.moveTo(x1, y1, duration=2)
            pag.click(x1, y1, duration=2)
            pag.sleep(2)
            pag.press(enter)
            pag.sleep(2)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Ok\' button when adding a new operation not found on the screen.")
            raise
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'File\' menu button not found on the screen.")
        raise
    try:
        open_operations_x, open_operations_y = pag.locateCenterOnScreen(picture('mscolab', 'openop.png'))
        pag.moveTo(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(1)
        pag.doubleClick(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Operations\' label not found on the screen.")
        raise

    # Managing Users for the operation that you are working on
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=2)
        pag.press('down', presses=2, interval=2)
        pag.press(enter)
        pag.sleep(3)
    else:
        print('Image not Found : File menu not found (while managing users)')

    # Demonstrating search and select of the users present in the network.
    try:
        selectall_left_x, selectall_left_y = pag.locateCenterOnScreen(picture('mscolab',
                                                                              'manageusers_left_selectall.png'),
                                                                              region=(0, 0, 600, sc_height))
        pag.moveTo(selectall_left_x, selectall_left_y, duration=2)
        pag.click(selectall_left_x, selectall_left_y, duration=1)
        pag.sleep(2)
        pag.moveTo(selectall_left_x + 90, selectall_left_y, duration=2)
        pag.click(selectall_left_x + 90, selectall_left_y, duration=1)
        pag.sleep(2)

        pag.click(selectall_left_x - 61, selectall_left_y, duration=1)
        pag.typewrite('test', interval=1)
        pag.moveTo(selectall_left_x, selectall_left_y, duration=2)
        pag.click(duration=2)
        pag.sleep(1)
        pag.moveTo(selectall_left_x + 90, selectall_left_y, duration=2)
        pag.click(duration=2)
        pag.sleep(2)

        # Deleting search item from the search box
        pag.click(selectall_left_x - 61, selectall_left_y, duration=2)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.sleep(1)
        pag.press('backspace')
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select All\' leftside button not found on the screen.")
        raise

    # Selecting and adding users for collaborating in the operation.
    if selectall_left_x is not None and selectall_left_y is not None:
        for count in range(4):
            pag.moveTo(selectall_left_x, selectall_left_y + 57 * count, duration=1)
            pag.click(selectall_left_x, selectall_left_y + 57 * count, duration=1)

        try:
            x, y = pag.locateCenterOnScreen(picture('mscolab', 'manageusers_add.png'))
            pag.moveTo(x, y, duration=2)
            pag.click(x, y, duration=2)
            pag.sleep(1)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException :\'Add (all the users)\' button not found on the screen.")
            raise
    else:
        print('Not able to select users for adding')

    # Searching and changing user permissions and deleting users
    try:
        selectall_right_x, selectall_right_y = pag.locateCenterOnScreen(picture('mscolab',
                                                                                'manageusers_right_selectall.png'),
                                                                                region=(600, 0, 1200, sc_height))
        pag.moveTo(selectall_right_x - 170, selectall_right_y, duration=2)
        pag.click(selectall_right_x - 170, selectall_right_y, duration=2)
        pag.typewrite('t', interval=0.3)
        pag.sleep(1)
        pag.hotkey(ctrl, 'a')
        pag.press('backspace')
        pag.sleep(1)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Select All (modifying permissions)\' button not found on the screen.")
        raise

    # Selecting and modifying user roles
    if selectall_right_x is not None and selectall_right_y is not None:
        row_gap = 30
        for i in range(3):
            pag.moveTo(selectall_right_x, selectall_right_y + 56, duration=1)
            # pag.move(selectall_right_x, row_gap * (i + 1), duration=1)
            pag.click(duration=1)
            pag.sleep(2)
            try:
                modify_x, modify_y = pag.locateCenterOnScreen(picture('mscolab', 'manageusers_modify.png'))
                pag.click(modify_x - 141, modify_y, duration=2)
                if i == 0:
                    pag.press('up', presses=2)
                else:
                    pag.press('down')
                    pag.sleep(1)
                pag.press(enter)
                pag.sleep(1)
                pag.click(modify_x, modify_y, duration=2)
                pag.sleep(1)
            except (ImageNotFoundException, OSError, Exception):
                print("\nException :\'Modify (access permissions)\' button not found on the screen.")
                raise

        # Deleting the first user in the list
        pag.moveTo(selectall_right_x, selectall_right_y + 56, duration=1)
        pag.click(selectall_right_x, selectall_right_y + 56, duration=1)
        if modify_x is not None and modify_y is not None:
            pag.moveTo(modify_x + 160, modify_y, duration=2)
            pag.click(modify_x + 160, modify_y, duration=2)
            pag.sleep(2)
        else:
            print('Image Not Found: Modify button has previously not found on the screen')

        # Filtering through access roles
        pag.click(selectall_right_x - 82, selectall_right_y, duration=2)
        pag.press('up', presses=3, interval=0.5)
        pag.sleep(1)
        for _ in range(3):
            pag.click(selectall_right_x - 82, selectall_right_y, duration=2)
            pag.press('down')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(1)
        pag.sleep(1)
    else:
        print('Image Not Found: Select All button has previously not found on the screen')

    # Closing user permission window
    pag.hotkey('command', 'w') if platform == 'dawrin' else pag.hotkey(alt, 'f4')
    pag.sleep(2)

    # Demonstrating Chat feature of mscolab to the user
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=2)
        pag.press(enter)
        pag.sleep(3)
    else:
        print('Image not Found : File menu not found (while opening Chat window)')

    # Sending messages to collaboraters or other users
    pag.typewrite(chat_message1, interval=0.05)
    pag.sleep(2)
    try:
        x, y = pag.locateCenterOnScreen(picture('mscolab', 'chat_send.png'))
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        pag.sleep(2)

        pag.typewrite(chat_message2, interval=0.05)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)

        # Uploading an example image of msui logo.
        pag.moveTo(x, y + 40, duration=2)
        pag.click(x, y + 40, duration=2)
        pag.sleep(1)
        pag.typewrite(example_image_path, interval=0.2)
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(1)
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Send (while in chat window)\' button not found on the screen.")
        raise
    # Searching messages in the chatbox using the search bar
    try:
        previous_x, previous_y = pag.locateCenterOnScreen(picture('mscolab', 'chat_previous.png'))
        pag.moveTo(previous_x - 70, previous_y, duration=2)
        pag.click(previous_x - 70, previous_y, duration=2)
        pag.sleep(1)
        pag.typewrite(search_message, interval=0.3)
        pag.sleep(1)
        pag.moveTo(previous_x + 82, previous_y, duration=2)
        pag.click(previous_x + 82, previous_y, duration=2)
        pag.sleep(2)
        pag.moveTo(previous_x, previous_y, duration=2)
        pag.click(previous_x, previous_y, duration=2)
        pag.sleep(2)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException :\'Previous (while in chat window searching operation)\' button not found on the screen.")
        raise
    # Closing the Chat Window
    pag.hotkey('command', 'w') if platform == 'darwin' else pag.hotkey(alt, 'f4')
    pag.sleep(2)

    # Opening Topview
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.sleep(1)
        pag.press('right')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(4)

    # Adding some waypoints to topview
    try:
        x, y = pag.locateCenterOnScreen(picture('wms', 'add_waypoint.png'))
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        pag.move(-50, 150, duration=1)
        pag.click(interval=2)
        wp1_x, wp1_y = pag.position()
        pag.sleep(1)
        pag.move(65, 65, duration=1)
        pag.click(duration=2)
        wp2_x, wp2_y = pag.position()
        pag.sleep(1)

        pag.move(-150, 30, duration=1)
        pag.click(duration=2)
        pag.sleep(1)
        pag.move(180, 100, duration=1)
        pag.click(duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Add waypoint (in topview) button not found on the screen.")
        raise

    # Closing the topview
    pag.hotkey('command', 'w') if platform == 'darwin' else pag.hotkey(alt, 'f4')
    pag.press('left')
    pag.sleep(1)
    pag.press(enter)
    pag.sleep(1)

    # Opening version history window.
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=1)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(1)

    # Operations performed in version history window.
    try:
        x, y = pag.locateCenterOnScreen(picture('mscolab', 'refresh_window.png'))
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        pag.sleep(2)
        pag.click(x, y + 32, duration=2)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)

        pag.moveTo(x, y + 164, duration=1)
        pag.click(x, y + 164, duration=1)
        pag.sleep(4)
        # Changing this change to a named version
        try:
            # Giving name to a change version.
            x1, y1 = pag.locateCenterOnScreen(picture('mscolab', 'name_version.png'))
            pag.sleep(1)
            pag.moveTo(x1, y1, duration=2)
            pag.click(x1, y1, duration=2)
            pag.sleep(1)
            pag.typewrite('Initial waypoint', interval=0.3)
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(1)

            pag.moveTo(x, y + 93, duration=1)
            pag.click(x, y + 93, duration=1)
            pag.sleep(2)

            pag.moveTo(x, y + 125, duration=1)
            pag.click(x, y + 125, duration=1)
            pag.sleep(1)

            # Checking out to a particular version
            pag.moveTo(x1 + 95, y1, duration=2)
            pag.click(x1 + 95, y1, duration=1)
            pag.sleep(1)
            pag.press('left')
            pag.sleep(2)
            pag.press(enter)
            pag.sleep(2)

            # Filtering changes to display only named changes.
            pag.moveTo(x1 + 29, y1, duration=1)
            pag.click(x1 + 29, y1, duration=1)
            pag.sleep(1)
            pag.press('up')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Name Version (in topview) button not found on the screen.")
            raise
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Refresh Window (in version history window) button not found on the screen.")
        raise
    # Closing the Version History Window
    pag.hotkey('command', 'w') if platform == 'darwin' else pag.hotkey(alt, 'f4')
    pag.sleep(4)

    # Activate Work Asynchronously with the mscolab server.
    try:
        x, y = pag.locateCenterOnScreen(picture('mscolab', 'work_asynchronously.png'))
        pag.sleep(1)
        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        work_async_x, work_async_y = pag.position()
        pag.sleep(3)
        # Opening Topview again to move waypoints during working locally!
        if file_x is not None and file_y is not None:
            pag.moveTo(file_x, file_y, duration=2)
            pag.click(file_x, file_y, duration=2)
            pag.press('right')
            pag.sleep(1)
            pag.press(enter)
            pag.sleep(4)

        # Moving waypoints.
        try:
            if wp1_x is not None and wp2_x is not None:
                x, y = pag.locateCenterOnScreen(picture('wms', 'move_waypoint.png'))
                pag.click(x, y, interval=2)
                pag.moveTo(wp2_x, wp2_y, duration=1)
                pag.click(interval=2)
                pag.dragRel(100, 150, duration=1)
                pag.moveTo(wp1_x, wp1_y, duration=1)
                pag.dragRel(35, -50, duration=1)
                pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\n Exception : Move Waypoint button could not be located on the screen")
            raise
        # Closing topview after displacing waypoints
        pag.hotkey('command', 'w') if platform == 'darwin' else pag.hotkey(alt, 'f4')
        pag.press('left')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)

        # Saving to Server the Work that has been done asynchronously.
        if work_async_x is not None and work_async_y is not None:
            pag.moveTo(work_async_x + 600, work_async_y, duration=2)
            pag.click(work_async_x + 600, work_async_y, duration=2)
            pag.press('down', presses=2, interval=1)
            pag.press(enter)
            pag.sleep(3)

        # Overwriting Server waypoints with Local Waypoints.
        try:
            x, y = pag.locateCenterOnScreen(picture('mscolab', 'overwrite_waypoints.png'))
            pag.sleep(1)
            pag.moveTo(x, y, duration=2)
            pag.click(x, y, duration=2)
            pag.sleep(2)
            pag.press(enter)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Overwrite with local waypoints (during saving to server) button"
                  " not found on the screen.")
            raise

        # Unchecking work asynchronously
        pag.moveTo(work_async_x, work_async_y, duration=2)
        pag.click(work_async_x, work_async_y, duration=2)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : Work Asynchronously (in mscolab) checkbox not found on the screen.")
        raise

    # Activating a local flight track
    if open_operations_x is not None and open_operations_y is not None:
        pag.moveTo(open_operations_x - 900, open_operations_y + 20, duration=2)
        pag.sleep(1)
        pag.doubleClick(open_operations_x - 900, open_operations_y + 20, duration=2)
        pag.sleep(2)
    else:
        print("Image Not Found : Open Operations label (for activating local flighttrack) not found, previously!")

    # Opening Topview again and making some changes in it
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.sleep(1)
        pag.press('right')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(4)
        # Adding waypoints in a different fashion than the pevious one (for local flighttrack)
        try:
            x, y = pag.locateCenterOnScreen(picture('wms', 'add_waypoint.png'))
            pag.moveTo(x, y, duration=2)
            pag.click(x, y, duration=2)
            pag.move(-50, 150, duration=1)
            pag.click(interval=2)
            pag.sleep(1)
            pag.move(65, 10, duration=1)
            pag.click(duration=2)
            pag.sleep(1)

            pag.move(-100, 10, duration=1)
            pag.click(duration=2)
            pag.sleep(1)
            pag.move(90, 10, duration=1)
            pag.click(duration=2)
            pag.sleep(3)

            # Sending topview to the background
            pag.hotkey('ctrl', 'up')
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Add waypoint (in topview again) button not found on the screen.")
            raise

    # Activating the opened mscolab operation
    if open_operations_x is not None and open_operations_y is not None:
        pag.moveTo(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(1)
        pag.doubleClick(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(3)

        # Opening the topview again by double clicking on open views
        try:
            x, y = pag.locateCenterOnScreen(picture('mscolab', 'openviews.png'))
            pag.moveTo(x, y + 22, duration=2)
            pag.doubleClick(x, y + 22, duration=2)
            pag.sleep(3)
        except (ImageNotFoundException, OSError, Exception):
            print("\nException : Open Views label not found on the screen.")

        # Closing the topview
        pag.hotkey('command', 'w') if platform == 'darwin' else pag.hotkey(alt, 'f4')
        pag.press('left')
        pag.sleep(1)
        pag.press(enter)
        pag.sleep(2)
    else:
        print("Image Not Found : Open Operations label (for activating mscolab operation) not found, previously!")

    # Deleting the operation
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=1)
        pag.sleep(1)
        pag.press('right', presses=2, interval=1)
        pag.sleep(1)
        pag.press('down', presses=3, interval=1)
        pag.press(enter, presses=2, interval=2)
        pag.sleep(2)
        pag.typewrite(p_name, interval=0.3)
        pag.press(enter, presses=2, interval=2)
        pag.sleep(3)

    # Opening user profile
    try:
        x, y = pag.locateCenterOnScreen(picture('mscolab', 'johndoe_profile.png'))
        pag.moveTo(x + 32, y, duration=2)
        pag.click(x + 32, y, duration=2)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(enter, presses=2, interval=2)
        pag.sleep(2)

        pag.click(x + 32, y, duration=2)
        pag.sleep(1)
        pag.press('down', presses=2, interval=2)
        pag.press(enter)
        pag.sleep(3)
    except (ImageNotFoundException, OSError, Exception):
        print("\nException : John Doe (in mscolab window) Profile/Logo button not found on the screen.")
        raise

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()

def main():
    """
    This function runs the above functions as different processes at the same time and can be
    controlled from here. (This is the main process.)
    """
    p1 = multiprocessing.Process(target=call_msui)
    p2 = multiprocessing.Process(target=automate_mscolab)
    p3 = multiprocessing.Process(target=call_recorder)

    print("\nINFO : Starting Automation.....\n")
    p3.start()
    pag.sleep(3)
    initial_ops()
    p1.start()
    p2.start()

    p2.join()
    p1.join()
    p3.join()
    print("\n\nINFO : Automation Completes Successfully!")
    sys.exit()


if __name__ == '__main__':
    main()
