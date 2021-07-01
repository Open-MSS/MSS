"""
    mslib.msui.screenrecorder
    ~~~~~~~~~~~~~~~~~~~

    This python script is meant for recording the screens while automated  tutorials are running.

    This file is part of mss.

    :copyright: Copyright 2021 Hrithik Kumar Verma
    :copyright: Copyright 2021 by the mss team, see AUTHORS.
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
from PyQt5 import QtWidgets


class ScreenRecorder:
    """
    This is the screen recording class which helps to record the screen.
    """
    def __init__(self):
        """
        The constructor sets the FPS, codecs, VideoWriter object, filename, and directory
        for the recording of the screen.
        """
        self.record = True
        self.app = QtWidgets.QApplication(sys.argv)
        screen = self.app.primaryScreen()
        self.width = screen.size().width()
        self.height = screen.size().height()
        self.fps = self.get_fps()
        self.codec = cv2.VideoWriter_fourcc(*"mp4v")
        current_time = datetime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')
        self.file_name = f'REC_{current_time}.mp4'
        parent_dir = os.getcwd()
        dir = "Screen Recordings"
        try:
            path = os.path.join(parent_dir, dir)
            os.makedirs(path, exist_ok=True)
            final_path = os.path.join(path, self.file_name)
        except OSError:
            print("Directory \"Recordings\" cannot be created")
        self.recorded_video = cv2.VideoWriter(final_path, self.codec, self.fps, (self.width, self.height))
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
            bbox = {"top": 0, "left": 0, "width": self.width, "height": self.height}
            fps = 0
            last_time = time.time()
            while time.time() - last_time < 1:
                img = sct.grab(bbox)
                fps += 1
                img_np = np.asarray(img)
                cv2.imshow("Frame Test Window", img_np)
        cv2.destroyWindow("Frame Test Window")

        return fps

    def capture(self):
        """
        Captures the frames of the screen at the rate of fps frames/second and writes into the
        video writer object with the defined fourcc, codec and colour format.
        """
        with mss.mss() as sct:
            bbox = {"top": 0, "left": 0, "width": self.width, "height": self.height}
            self.start_rec_time = time.time()
            frame_time_ms = 1000 / self.fps
            frames = 0
            print(f"Starting to record with FPS value {self.fps} ...")
            while self.record:
                img = sct.grab(bbox)
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
              f"\'MSS\\tutorials\\Screen Recordings\' folder.")
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
