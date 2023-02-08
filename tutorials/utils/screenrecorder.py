"""
    msui.tutorials.screenrecorder
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This python script is meant for recording the screens while automated  tutorials are running.

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
import numpy as np
import cv2
import datetime
import os
import sys
import time
import mss
import pyautogui
import shutil
from PyQt5 import QtWidgets
from tutorials.utils.cursor import Xcursor
from sys import platform
from PIL import Image


class ScreenRecorder:
    """
    This is the screen recording class which helps to record the screen.
    """
    def __init__(self, x_start=None, y_start=None, sc_width=None, sc_height=None):
        """
        The constructor sets the FPS, codecs, VideoWriter object, filename, and directory
        for the recording of the screen.
        """
        self.record = True
        self.app = QtWidgets.QApplication(sys.argv)
        screen = self.app.primaryScreen()
        if x_start is None and y_start is None:
            self.x_start = 0
            self.y_start = 0
        else:
            self.x_start = x_start
            self.y_start = y_start
        if sc_width is None and sc_height is None:
            self.width = screen.size().width()
            self.height = screen.size().height()
        else:
            self.width = sc_width
            self.height = sc_height
        self.fps = self.get_fps()
        self.codec = cv2.VideoWriter_fourcc(*"mp4v")
        current_time = datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        self.file_name = f'REC_{current_time}.mp4'
        parent_dir = os.getcwd()
        dir = "recordings"
        try:
            path = os.path.join(parent_dir, dir)
            os.makedirs(path, exist_ok=True)
            final_path = os.path.join(path, self.file_name)
        except OSError:
            print("Directory \"Recordings\" cannot be created")
        self.recorded_video = cv2.VideoWriter(final_path, self.codec, self.fps, ((self.width - self.x_start),
                                                                                 (self.height - self.y_start)))
        self.window_name = "Screen Recorder : MSS"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 480, 480)
        cv2.moveWindow(self.window_name, self.width - 480, 0)

    def get_fps(self):
        """
        This method helps to get the Frames in one second according to the loop time and your
        screen refresh rate of your monitor (if considerable in the program) and sets the FPS.
        """
        with mss.mss() as sct:
            bbox = {"top": self.y_start, "left": self.x_start, "width": self.width - self.x_start,
                    "height": self.height - self.y_start}
            fps = 0
            last_time = time.time()
            while time.time() - last_time < 1:
                img = sct.grab(bbox)
                fps += 1
                img_np = np.asarray(img)
                cv2.imshow("Frame Test Window", img_np)
        cv2.destroyWindow("Frame Test Window")

        return fps

    def capture(self, duration=120):
        """
        Captures the frames of the screen at the rate of fps frames/second and writes into the
        video writer object with the defined fourcc, codec and colour format.
        """
        ini_time_for_now = datetime.datetime.now()
        future_date_after_120seconds = ini_time_for_now + datetime.timedelta(seconds=duration)
        if platform == 'linux' or platform == 'linux2':
            cursor = Xcursor()
            cursor_imgarray = cursor.getCursorImageArray()
            cursor.saveImage(cursor_imgarray, 'cursor_image.png')
            mouse_pointer = Image.open('cursor_image.png')
            width, height = mouse_pointer.size
        elif platform == 'win32' or platform == 'darwin':
            mouse_pointer = Image.open('../pictures/cursor_image.png')
            width, height = mouse_pointer.size
        else:
            print('Not supported in this platform')
            mouse_pointer = None
            width, height = None, None
        with mss.mss() as sct:
            bbox = {"top": self.y_start, "left": self.x_start, "width": self.width - self.x_start,
                    "height": self.height - self.y_start}
            self.start_rec_time = time.time()
            frame_time_ms = 1000 / self.fps
            frames = 0
            print(f"Starting to record with FPS value {self.fps} ...")
            while self.record:
                if platform == 'win32' or platform == 'darwin':
                    x, y = pyautogui.position()
                elif platform == 'linux':
                    x, y = pyautogui.size()[0] - 1, pyautogui.size()[1] - 1
                    # Fixed mouse pointer in linux at this coordinate. Throwing error of some kind.
                    # Hence, the mouse pointer is not visible in the recordings but is at a fixed place.
                    # Alternatively if you just record anything running screenrecorder.py directly this
                    # pyautogui.position() works perfectly in any operating system.(ofcourse you need to change the
                    # code by removing this platform thing). But when tutorials are called, it
                    # is throwing some untraceable error in Linux.
                img = Image.frombytes("RGBA", sct.grab(bbox).size, sct.grab(bbox).bgra, "raw", "RGBA")
                img.paste(mouse_pointer, (x, y, x + width, y + height), mask=mouse_pointer)
                img_np = np.array(img)
                img_final = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
                cv2.imshow(self.window_name, img_final)
                self.recorded_video.write(img_final)
                frames += 1
                expected_frames = ((time.time() - self.start_rec_time) * 1000) / frame_time_ms
                surplus = frames - expected_frames

                # Duplicate previous frame to meet FPS quota. Consider lowering the FPS instead!
                if int(surplus) <= -1:
                    frames -= int(surplus)
                    for i in range(int(-surplus)):
                        self.recorded_video.write(img_final)
                # Exits the screen capturing when user press 'q'
                if cv2.waitKey(max(int(surplus * frame_time_ms), 1)) & 0xFF == ord('q'):
                    break
                # exit after duration of seconds anyway
                if datetime.datetime.now() >= future_date_after_120seconds:
                    break

    def stop_capture(self):
        """
        When the screen is not being captured, this method is called to release the video writer
        objects and destroy all windows showing additional useful information to the user.
        """
        self.record = False
        self.end_rec_time = time.time()
        print(f".\n.\n.\n.\nFinished Recording in {self.end_rec_time - self.start_rec_time} seconds!")
        self.recorded_video.release()
        print(f"\n\nYour file \'{self.file_name}\' has been successfully saved in "
              f"\'MSS\\tutorials\\recordings\' folder.")
        shutil.copyfile(os.path.join('recordings', self.file_name),
                        os.path.join('recordings', 'last_recording.mp4'))
        cv2.destroyAllWindows()
        self.app.exit()


def main():
    """
    Main function calling the above functions.
    """
    rec = ScreenRecorder()
    rec.capture()
    rec.stop_capture()


if __name__ == '__main__':
    main()
