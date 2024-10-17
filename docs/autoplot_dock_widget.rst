mssautoplot - UI Setup
======================

Autoplot Docking Widget
-----------------------

**Autoplot Dockwidget Description:**
The Docking Widget offers users a Graphical User Interface (GUI) for downloading plots based on specified configurations. It provides a user-friendly approach, integrating seamlessly with other dock widgets. This widget can be accessed across all three views—Top View, Side View, and Linear View—ensuring flexibility and ease of use for different user preferences.

**Components:**

The autoplot docking widget contains the following parameters which can be configured:

- **Select configuration file button**: This button is used to select the JSON file for uploading the configurations to the dock widget. By default, it uses the `mssautoplot.json` file located in this path - `$HOME/.config/msui`.

- **Left Treewidget**: The following parameters can be configured or updated based on requirements:

  - Flight
  - Map Sections
  - Vertical
  - Filename
  - Initial Time
  - Valid Time

- **Right Treewidget**: The following parameters can be configured or updated:

  - URL
  - Layers
  - Styles
  - Level
  - Start Time
  - End Time
  - Time Interval

- **ComboBoxes**: These allow configuring the start time, end time, and time interval. Ensure that the start time is always less than the end time. The plots are downloaded from the start time to the end time at the provided time intervals.

- **Download Plots Button**: This button is used to download plots based on the configurations. The configuration is saved in the `mssautoplot.json` file by default, located at `$HOME/.config/msui`.

- **Update/Create JSON file**: This button will create or update the JSON file. If not present, it will update the default `mssautoplot.json` file located at `$HOME/.config/msui`.

How to Use
----------

The `mssautoplot.json` file located in the `$HOME/.config/msui` directory contains the default configuration.

The **left treewidget** is used to configure the automated plotting flights list:

.. code-block:: json

   "automated_plotting_flights":
   [
      ["flight1", "section1", "vertical1", "filename1", "init_time1", "time1"],
      ["flight2", "section2", "vertical2", "filename2", "init_time2", "time2"]
   ]

- Flight, filename, and section parameters are configured in the **Top View**.
- The vertical parameter is configured in the **Side View**.

The **right treewidget** is used to configure the automated plotting flight sections, which are based on the view:

- For **Top View**, it is `"automated_plotting_hsecs": [["URL", "Layer", "Styles", "Level"]]`.
- For **Side View**, it is `"automated_plotting_vsecs": [["URL", "Layer", "Styles", "Level"]]`.
- For **Linear View**, it is `"automated_plotting_lsecs": [["URL", "Layer", "Styles"]]`.

Inserting, Updating, and Removing Configuration in the Treewidget
-----------------------------------------------------------------

There are three buttons— **Add**, **Update**, and **Remove**—under each treewidget:

- **Add Button**: Inserts a row based on the current configurations.

  - For the left treewidget, the current values of flight, section, vertical, filename, init_time, and time are inserted.
  - For the right treewidget, the current values of URL, Layers, Styles, Level, Start Time, End Time, and Time Interval are inserted.

- **Remove Button**: Removes the selected row.

- **Update Button**: Updates the selected row with the current values (only active after selecting a row).

Ensure that the **right tree widget** has at least one row before inserting into the left treewidget.

Downloading the Plots
---------------------

Plots can be downloaded in the following ways:

1. Upload the configuration JSON file by clicking the **Select configuration file** button, then click the **Download Plots** button to download the plots.
2. Upload the configuration JSON file by clicking the **Select configuration file** button, then make modifications as needed.
3. Download plots with or without flight track from start time to end time at specified time intervals. This ensures that a total of `M x N` plots are downloaded, where `M` is the number of rows in the left treewidget and `N` is the number of rows in the right treewidget.

Example
-------

An `mssautoplot.json` file generated after clicking the **Update/Create Configuration file Button** in the path, e.g. “$HOME/.config/msui” by default:

**/$HOME/.config/msui/mssautoplot.json**

.. literalinclude:: samples/config/msui/autoplot_dockwidget.json.sample
