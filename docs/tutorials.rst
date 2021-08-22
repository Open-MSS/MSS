==============================================================================
A user guide for tool chain of automated tutorials for the MSUI user interface
==============================================================================

The tool chain for tutorials are automatically generated tutorials by use of python scripts to automate the software to
perform different tasks and hence, demonstrating and explaining to the user various parts of the MSS software. It tells
the user about the different technical aspects of MSS which a new user would take time to know that, otherwise.

There are nine such total automating scripts that are meant for explaining nine such parts or sub parts of MSS software
and it's use.
Listing them below as:

* tutorial_hexagoncontrol.py for explaining hexagon control in table view.

* tutorial_kml.py for explaining kml dockwidget in topview.

* tutorial_mscolab.py for understanding mscolab feature of MSS.

* tutorial_performancesettings.py for giving a demo what is there in performance settings of table view.

* tutorial_remotesensing.py for demonstrating remote sensing dockwidget of topview.

* tutorial_satellitetrack.py for demonstrating satellite track dockwidget of topview.

* tutorial_views.py for demonstrating the top view, sideview, table view and linear view together.

* tutorial_waypoints.py for demonstrating how to place waypoints in topview.

* tutorial_wms.py for explaining web map service section of topview.

Other important files with their functions are as follows:

* screenrecorder.py for opening a screen recorder window which is a small window in the top right corner of the
  rectangular recording area on the screen. The window gets closed when you press 'q' keeping the window in focus. This
  will also stop the recording of the screen when window gets closed.

* cursor.py which is used for generating the image of the present cursor image.

* audio.py which translates and converts into speech the texts and saves them as .mp3 files.

Getting Started..
=================

On the Anaconda terminal, type the following ::

 cd ..../MSS/$
 $ conda activate mssdev


 (mssdev)$ conda install --file requirements.d/tutorials.txt
 (mssdev)$ conda deactivate
 (base)$ conda activate mssdev


This will install all the dependencies required for running of the tutorials.


**On Linux additionally** ::

    $ sudo apt-get install scrot
    $ sudo apt-get install python3-tk
    $ sudo apt-get install python3-dev
    $ sudo apt-get install libx11-dev libxext-dev libxfixes-dev libxi-dev


Now, just go into the _../MSS/tutorials/_ directory ::

    $ cd ../MSS/tutorials/


Keep the following things in mind before running a script

* You should have only an **US keyboard layout**. If you have a different keyboard layout, you just need to change it to
  US keyboard!
* The **cursor.py** python file will run only on Linux and not on Windows for grabbing the mouse pointer image.

* The screen recording starts as the recording window appears and ends when you quit the recording window by pressing
  'q' when the window is being displayed in the foreground.

* The **audio.py** file should have translation APIs and text-to-speech (t2s) APIs written at specified places inside it
  to run successfully! It has a #ToDo to read.


In Linux for making the cursor visible as a highlighter, perform the following
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are in Windows, there is no need of this highlighter. It is by default that it also records the mouse-pointer.

* Clone the repository https://github.com/swillner/highlight-pointer.git into a directory eg. `highlighter` on your system

Change directory into that location ::

$ cd highlighter/highlight-pointer/
$ make

After the `make` gets successful, run ::

$ ./highlight-pointer -r 10

This will make your cursor highlighted as a red cursor having radius as 10. You can minimize the terminal and continue
your work with the highlighted cursor.
When you have to stop just open that terminal again and type **CTRL + C**

For more details in its customization, you can visit https://github.com/swillner/highlight-pointer

THE RUNNING OF THE SCRIPTS
~~~~~~~~~~~~~~~~~~~~~~~~~~
Each python file inside MSS/tutorials can be run directly like ::

(mssdev)~/..MSS/tutorials/ $ python screenrecorder.py

For recording anything on your screen. The videos will be then saved to `MSS/tutorials/Screen Recorders/`

For all the tutorials, you can do the same, example ::

(mssdev)~/..MSS/tutorials/ $ python tutorial_remotesensing.py
(mssdev)~/..MSS/tutorials/ $ python tutorial_satellitetrack.py
(mssdev)~/..MSS/tutorials/ $ python tutorial_hexagoncontrol.py

The `MSS/tutorials/textfiles` contain descriptions of the tutorial videos in text format, these later can be
converted to audio files by `audio.py` script after adding certain #ToDOs.

**Note**
In  tutorials development, when creating a class of Screen Recorder as ::

$ rec = ScreenRecorder(x_start, y_start, width, height) or $ rec = ScreenRecorder()
$ rec.capture()
$ rec.stop_capture()

When no arguments are passed to ScreenRecorder class during object creation, it records full screen but if you have to
record a particular area of screen, just pass the below parameters.

* "x_start" is the starting pixel from left or how many pixels from the left panel it will capture the screen area.
* "y_Start" is the starting pixel from top or how many pixels down from the top panel, it will start capture.
* "width" is the pixel length from x_start that will form the recording area.
* "height is the pixel length from y_start that will from the recording area.

The top left corner is (0,0) and the width for eg is 1920 and the height for eg is 1080 of my screen.

Knowing MouseInfo()
~~~~~~~~~~~~~~~~~~~
For deciding the pixels, or know how  much length or height i should go down or what is the relative distance of one
point from the other, pyautogui's mouseInfo() comes to the rescue ::

    (mssdev)$ python
    $ import pyautogui
    $ pyautogui.mouseInfo()

This will open a window which will be very helpful in development and other pixel position related things.

.. Important::
  MSS/tutorials is still under development, so if the automation makes problems in your system, it may be due to certain
  parameters specific to your system and also since it is not widely used and tried, there will be always a scope of
  improvement. Kindly report that bug or discrepancies to https://github.com/Open-MSS/MSS/issues/new

Videos post processing via ffmpeg
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The post processing of the videos can be done using ffmpeg in Command Line Interface.

The generated video size is too large, so if you want to reduce the size, you can ::

    $ cd MSS/tutorials/Screen Recordings/
    (mssdev)$ ffmpeg -i input.mp4 -vcodec h264 -acodec mp2 output.mp4

For trimming the videos from a start (00:14:00) and end time (05:19:00), you can ::

    $ cd MSS/tutorials/Screen Recordings/
    (mssdev)$ ffmpeg -i input.mp4 -ss 00:14:00 -to 05:19:00 -c:v libx264 -crf 30 output.mp4

For cropping the video
(you can also use Screen Recorder for selected screen area recording feature as described above) ::

    $ cd MSS/tutorials/Screen Recordings/
    (mssdev)$ fmpeg -i input.mp4 -filter_complex "[0:v]crop=1919:978:0:33[cropped]" -map "[cropped]" output.mp4

    # “crop=width:height:x:y” is the format

For merging audios into the video ::

    (mssdev)$ ffmpeg -i input.mp4 -i audio.mp3 -c:v copy -c:a aac output.mp4
In this case, the video and audio must be in same directory and you should cd into that directory.
