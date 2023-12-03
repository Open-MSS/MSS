"""
    msui.tutorials.tutorial_mscolab
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script generates an automatic demonstration of how to use Mission Support System Collaboration for users
    to collaborate in flight planning and thereby explain how to use it's various functionalities.
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
import os
import pyautogui as pag

from tutorials.utils import (start, finish, create_tutorial_images, select_listelement,
                             find_and_click_picture, type_and_key)

from tutorials.utils.platform_keys import platform_keys
from tutorials.utils.picture import picture

CTRL, ENTER, WIN, ALT = platform_keys()

USERNAME = 'John Doe'
EMAIL = 'johndoe@gmail.com'
PASSWORD = 'johndoe'
OPERATION_NAME = 'operation_of_john_doe'
OPERATION_DESCRIPTION = """This is John Doe's operation. He wants his collegues and friends \
                         to collaborate on this operation with him in the network. Mscolab, here, \
                         will be very helpful for Joe with various features to use!"""
PATH = os.path.normpath(os.getcwd() + os.sep + os.pardir)
EXMPLE_IMAGE_PATH = os.path.join(os.path.join(PATH, 'docs', 'mss-logo.png'))
MSCOLAB_URL = 'http://localhost:8083/'


# ToDo fix waypoint movement
def automate_mscolab():
    """
    This is the main automating script of the Mission Support System Collaboration or Mscolab tutorial which will be
    recorded and saved to a file having dateframe nomenclature with a .mp4 extension(codec).
    """
    # Giving time for loading of the MSS GUI.
    pag.sleep(5)
    hotkey = WIN, 'pageup'
    pag.hotkey(*hotkey)

    create_tutorial_images()
    pag.sleep(2)
    modify_x, modify_y = None, None

    connect_to_mscolab_url()
    create_tutorial_images()
    pag.sleep(1)
    create_user()
    login_user()

    create_tutorial_images()
    # Opening a new Mscolab Operation

    file_x, file_y = find_and_click_picture("msuimainwindow-menubar.png", 'File menu not found', bounding_box=(0, 0, 38, 22))
    pag.moveTo(file_x, file_y, duration=2)
    pag.click(file_x, file_y, duration=2)
    for _ in range(2):peration_of_john_doe
        pag.press('down')
        pag.sleep(1)
        pag.press(ENTER)
        pag.sleep(2)
    pag.press('tab')
    for value in [OPERATION_NAME, OPERATION_DESCRIPTION]:
        type_and_key(value, key='tab', interval=0.05)

    create_tutorial_images()
    find_and_click_picture('addoperationdialog-ok.png',
                           'OK button when adding a new operation not found on the screen.')
    create_tutorial_images()

    find_and_click_picture('msuimainwindow-operations.png',
                           'Operations label not found on screen',
                           bounding_box=(0, 0, 72, 17))
    open_operations_x, open_operations_y = pag.position()
    pag.moveTo(open_operations_x, open_operations_y + 20, duration=2)
    pag.sleep(1)
    pag.doubleClick(open_operations_x, open_operations_y + 20, duration=2)
    pag.sleep(2)

    # Managing Users for the operation that you are working on
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=2)
        pag.press('down', presses=3, interval=2)
        pag.press('right')
        pag.press('down', presses=2, interval=2)
        pag.press(ENTER)
        pag.sleep(3)
    else:
        print('Image not Found : File menu not found (while managing users)')

    create_tutorial_images()

    # positions of buttons in the view mscolab admin windo
    pic = picture("mscolabadminwindow-all-users-without-permission.png")
    ref_x, ref_y = pag.locateCenterOnScreen(pic)
    left_side = (ref_x, ref_y, 400, 800)

    pic = picture("mscolabadminwindow-all-users-with-permission.png")
    ref_x, ref_y = pag.locateCenterOnScreen(pic)
    right_side = (ref_x, ref_y, 800, 1000)

    selectall_left_x, selectall_left_y = find_and_click_picture('mscolabadminwindow-select-all.png',
                                                                'Select All leftside button not found',
                                                                region=left_side)

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
    pag.hotkey(CTRL, 'a')
    pag.sleep(1)
    pag.press('backspace')
    pag.sleep(2)

    # Selecting and adding users for collaborating in the operation.
    if selectall_left_x is not None and selectall_left_y is not None:
        for count in range(4):
            pag.moveTo(selectall_left_x, selectall_left_y + 57 * count, duration=1)
            pag.click(selectall_left_x, selectall_left_y + 57 * count, duration=1)
        x, y = find_and_click_picture('mscolabadminwindow-add.png',
                                      'Add (all the users) button not found on the screen.',
                                      region=left_side)

        pag.moveTo(x, y, duration=2)
        pag.click(x, y, duration=2)
        pag.sleep(1)
    else:
        print('Not able to select users for adding')

    # Searching and changing user permissions and deleting users
    selectall_right_x, selectall_right_y = find_and_click_picture('mscolabadminwindow-select-all.png',
                                                                  'Select All (modifying permissions) '
                                                                  'button not found on the screen.',
                                                                  region=right_side)
    pag.moveTo(selectall_right_x - 170, selectall_right_y, duration=2)
    pag.click(selectall_right_x - 170, selectall_right_y, duration=2)
    pag.typewrite('t', interval=0.3)
    pag.sleep(1)
    pag.hotkey(CTRL, 'a')
    pag.press('backspace')
    pag.sleep(1)

    # Selecting and modifying user roles
    if selectall_right_x is not None and selectall_right_y is not None:
        for i in range(3):
            pag.moveTo(selectall_right_x, selectall_right_y + 56, duration=1)
            # pag.move(selectall_right_x, row_gap * (i + 1), duration=1)
            pag.click(duration=1)
            pag.sleep(2)
            modify_x, modify_y = find_and_click_picture('mscolabadminwindow-modify.png',
                                                        'Modify (access permissions) '
                                                        'button not found on the screen.)')
            pag.click(modify_x - 141, modify_y, duration=2)
            if i == 0:
                pag.press('up', presses=2)
            else:
                pag.press('down')
                pag.sleep(1)
            pag.press(ENTER)
            pag.sleep(1)
            pag.click(modify_x, modify_y, duration=2)
            pag.sleep(1)

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
            pag.press(ENTER)
            pag.sleep(1)
        pag.sleep(1)
    else:
        print('Image Not Found: Select All button has previously not found on the screen')

    # Closing user permission window
    pag.hotkey(ALT, 'f4')
    pag.sleep(2)

    # Demonstrating Chat feature of mscolab to the user
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=2)
        pag.press(ENTER)
        pag.sleep(3)
    else:
        print('Image not Found : File menu not found (while opening Chat window)')

    create_tutorial_images()
    chat_message1 = 'Hi buddy! What\'s the next plan? I have marked the points in topview for the dummy operation.'
    chat_message2 = 'Hey there user! This is the chat feature of MSCOLAB. You can have a conversation with your '

    # Sending messages to collaboraters or other users
    pag.typewrite(chat_message1, interval=0.05)
    pag.sleep(2)
    x, y = find_and_click_picture('mscolaboperation-send.png',
                                  'Send (while in chat window) button not found on the screen.')
    pag.typewrite(chat_message2, interval=0.05)
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(2)

    # Uploading an example image of msui logo.
    pag.moveTo(x, y + 40, duration=2)
    pag.click(x, y + 40, duration=2)
    pag.sleep(1)
    pag.typewrite(EXMPLE_IMAGE_PATH, interval=0.2)
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(1)
    pag.moveTo(x, y, duration=2)
    pag.click(x, y, duration=2)
    pag.sleep(2)

    # Searching messages in the chatbox using the search bar
    previous_x, previous_y = find_and_click_picture('mscolaboperation-previous.png',
                                                    'Previous (while in chat window searching'
                                                    ' operation) button not found.')
    pag.moveTo(previous_x - 70, previous_y, duration=2)
    pag.click(previous_x - 70, previous_y, duration=2)
    pag.sleep(1)
    search_message = 'chat feature of MSCOLAB'
    pag.typewrite(search_message, interval=0.3)
    pag.sleep(1)
    pag.moveTo(previous_x + 82, previous_y, duration=2)
    pag.click(previous_x + 82, previous_y, duration=2)
    pag.sleep(2)
    pag.moveTo(previous_x, previous_y, duration=2)
    pag.click(previous_x, previous_y, duration=2)
    pag.sleep(2)
    # Closing the Chat Window
    pag.hotkey(ALT, 'f4')
    pag.sleep(2)

    # Opening Topview
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.sleep(1)
        pag.press('right')
        pag.sleep(1)
        pag.press(ENTER)
        pag.sleep(4)

    create_tutorial_images()
    # Adding some waypoints to topview
    x, y = find_and_click_picture('topviewwindow-ins-wp.png',
                                  'Topview insert wp button not found')
    pag.moveTo(x, y, duration=2)
    pag.click(x, y, duration=2)
    pag.move(-50, 150, duration=1)
    pag.click(interval=2)
    wp1_x, wp1_y = pag.position()
    pag.sleep(1)
    pag.move(65, 65, duration=1)
    pag.click(duration=2)
    # wp2_x, wp2_y = pag.position()
    pag.sleep(1)

    pag.move(-150, 30, duration=1)
    pag.click(duration=2)
    pag.sleep(1)
    pag.move(180, 100, duration=1)
    pag.click(duration=2)
    pag.sleep(3)

    # Closing the topview
    pag.hotkey(ALT, 'f4')
    pag.press('left')
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(1)

    # Opening version history window.
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right', presses=2, interval=1)
        pag.sleep(1)
        pag.press('down')
        pag.sleep(1)
        pag.press(ENTER)
        pag.sleep(1)

    create_tutorial_images()
    # Operations performed in version history window.

    x, y = find_and_click_picture('mscolabversionhistory-refresh-window.png',
                                  'Refresh Window (in version history window) button not found.')
    pag.moveTo(x, y, duration=2)
    pag.click(x, y, duration=2)
    pag.sleep(2)
    pag.click(x, y + 32, duration=2)
    pag.sleep(1)
    pag.press('down')
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(2)

    pag.moveTo(x, y + 164, duration=1)
    pag.click(x, y + 164, duration=1)
    pag.sleep(4)
    # Changing this change to a named version

    # Giving name to a change version.
    x1, y1 = pag.locateCenterOnScreen(picture('mscolabversionhistory-name-version.png'))
    pag.sleep(1)
    pag.moveTo(x1, y1, duration=2)
    pag.click(x1, y1, duration=2)
    pag.sleep(1)
    pag.typewrite('Initial waypoint', interval=0.3)
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(1)

    pag.moveTo(x, y + 93, duration=1)
    pag.click(x, y + 93, duration=1)
    pag.sleep(2)

    pag.moveTo(x, y + 125, duration=1)
    pag.click(x, y + 125, duration=1)
    pag.sleep(1)

    x2, y2 = pag.locateCenterOnScreen(picture('mscolabversionhistory-checkout.png'))
    pag.sleep(1)
    pag.moveTo(x2, y2, duration=2)
    pag.click(x2, y2, duration=2)
    pag.sleep(1)
    pag.press(ENTER)

    # Filtering changes to display only named changes.
    pag.moveTo(x1 + 29, y1, duration=1)
    pag.click(x1 + 29, y1, duration=1)
    pag.sleep(1)
    pag.press('up')
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(3)

    # Closing the Version History Window
    pag.hotkey(ALT, 'f4')
    pag.sleep(4)

    create_tutorial_images()
    # Activate Work Asynchronously with the mscolab server.
    # ToDo this needs to be extracted to a different tutorial

    find_and_click_picture('msuimainwindow-work-asynchronously.png',
                           'Work Asynchronously (in mscolab) '
                           'checkbox not found ', bounding_box=(0, 0, 149, 23))

    work_async_x, work_async_y = pag.position()
    pag.sleep(3)
    # Opening Topview again to move waypoints during working locally!
    if file_x is not None and file_y is not None:
        pag.moveTo(file_x, file_y, duration=2)
        pag.click(file_x, file_y, duration=2)
        pag.press('right')
        pag.sleep(1)
        pag.press(ENTER)
        pag.sleep(4)

    # Moving waypoints.
    create_tutorial_images()
    wp2_x, wp2_y = find_and_click_picture('topviewwindow-top-view.png',
                                          'Topviews Point 2 not found on the screen.',
                                          bounding_box=(322, 112, 346, 135))

    if wp1_x is not None and wp2_x is not None:
        find_and_click_picture('topviewwindow-mv-wp.png',
                               'Move Waypoint button could not be located')

        pag.click(wp2_x, wp2_y, interval=2)
        pag.moveTo(wp2_x, wp2_y, duration=1)
        pag.dragTo(wp1_x, wp1_y + 20, duration=1, button='left')
        pag.click(interval=2)
        pag.sleep(4)

    # Closing topview after displacing waypoints
    pag.hotkey(ALT, 'f4')
    pag.press('left')
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(2)

    # Saving to Server the Work that has been done asynchronously.
    if work_async_x is not None and work_async_y is not None:
        pag.moveTo(work_async_x + 600, work_async_y, duration=2)
        pag.click(work_async_x + 600, work_async_y, duration=2)
        pag.press('down', presses=2, interval=1)
        pag.press(ENTER)
        pag.sleep(3)

    create_tutorial_images()

    # Overwriting Server waypoints with Local Waypoints.
    find_and_click_picture('msuimainwindow-server-options.png',
                           'Overwrite with local waypoints (during saving to server) button not found.')

    pag.press('down', presses=2, interval=1)
    pag.sleep(2)
    pag.press(ENTER)
    pag.sleep(3)
    create_tutorial_images()

    # Unchecking work asynchronously
    pag.moveTo(work_async_x, work_async_y, duration=2)
    pag.click(work_async_x, work_async_y, duration=2)
    pag.sleep(3)

    # Activating a local flight track
    if open_operations_x is not None and open_operations_y is not None:
        pag.moveTo(open_operations_x - 900, open_operations_y, duration=2)
        pag.sleep(1)
        pag.doubleClick(open_operations_x - 900, open_operations_y, duration=2)
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
        pag.press(ENTER)
        pag.sleep(4)
        # Adding waypoints in a different fashion than the pevious one (for local flighttrack)
        find_and_click_picture('topviewwindow-ins-wp.png',
                               'Add waypoint (in topview again) button not found.')

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
        pag.hotkey('CTRL', 'up')

    # Activating the opened mscolab operation
    if open_operations_x is not None and open_operations_y is not None:
        pag.moveTo(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(1)
        pag.doubleClick(open_operations_x, open_operations_y + 20, duration=2)
        pag.sleep(3)

        # Opening the topview again by double-clicking on open views
        x, y = find_and_click_picture('msuimainwindow-open-views.png', 'open views not found')

        pag.moveTo(x, y + 22, duration=2)
        pag.doubleClick(x, y + 22, duration=2)
        pag.sleep(3)

        # Closing the topview
        pag.hotkey(ALT, 'f4')
        pag.press('left')
        pag.sleep(1)
        pag.press(ENTER)
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
        pag.press(ENTER, presses=2, interval=2)
        pag.sleep(2)
        pag.typewrite(OPERATION_NAME, interval=0.3)
        pag.press(ENTER, presses=2, interval=2)
        pag.sleep(3)

    create_tutorial_images()
    # Opening user profile
    x, y = find_and_click_picture('msuimainwindow-john-doe.png',
                                  'John Doe (in mscolab window) Profile/Logo button not found.',
                                  xoffset=40)
    pag.sleep(1)
    pag.press('down')
    pag.sleep(1)
    pag.press(ENTER, presses=2, interval=2)
    pag.sleep(2)

    pag.click(x + 32, y, duration=2)
    pag.sleep(1)
    pag.press('down', presses=2, interval=2)
    pag.press(ENTER)
    pag.sleep(3)

    print("\nAutomation is over for this tutorial. Watch next tutorial for other functions.")
    finish()


def login_user():
    # Login
    pag.press('tab', presses=2)
    type_and_key(ENTER, key='tab')
    type_and_key(PASSWORD, key='tab')
    pag.press(ENTER)
    # store userdata
    pag.press('left')
    pag.press(ENTER)


def create_user():
    find_and_click_picture('mscolabconnectdialog-add-user.png', 'Add User Button not found')
    pag.sleep(4)
    # Entering details of new user
    new_user_input = [USERNAME, EMAIL, PASSWORD, PASSWORD]
    for value in new_user_input:
        type_and_key(value, key='tab')
    pag.press('tab')
    pag.sleep(1)
    pag.press(ENTER)
    pag.sleep(2)


def connect_to_mscolab_url():
    # connect
    find_and_click_picture('msuimainwindow-connect.png',
                           "Connect to Mscolab button not found on the screen.")
    create_tutorial_images()
    pag.sleep(2)
    # create user on server
    find_and_click_picture('mscolabconnectdialog-http-localhost-8083.png', 'Url not found')
    type_and_key(MSCOLAB_URL)
    pag.press(ENTER)
    # update server data
    pag.press('left')
    pag.press(ENTER)


if __name__ == '__main__':
    start(target=automate_mscolab, duration=638, dry_run=True)
