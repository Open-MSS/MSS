mss - User Interface
======================================

The executable for the user interface application is "**mss**". It
does not provide any command line options. Warnings about CDAT
features are due to the NAppy package and can be ignored. The program
should open the main window of the user interface, from which you can
open further windows, including top view, side view and so on.

Configuration for the user interface is located in
"mss_settings.json". In this file, you can specify, for instance, the
default WMS URLs for the WMS client, the size of the local image cache
(the MSUI caches retrieved WMS images to accelerate repeated
retrievals), or the predefined locations that the user can select in
the table view.

A few options influencing the appearance of the displayed plots and
flight tracks (colours etc.) can be set directly in the user
interface (top view and side view).

.. _mss-configuration:

Configuration of mss
~~~~~~~~~~~~~~~~~~~~


Settings file
.............

This file includes configuration settings central to the entire
Mission Support User Interface (mss). Among others, define

 - available map projections
 - vertical section interpolation options
 - the lists of predefined web service URLs
 - predefined waypoints for the table view
 - batch products for the loop view in this file.

If you don't have a mss_settings.json then default configuration is in place.

Store this mss_settings.json in a path, e.g. "$HOME/.config/mss"

The file could be loaded by the File Load Configuration dialog or
by the environment variable MSS_SETTINGS pointing to your mss_settings.json.

**/$HOME/.config/mss/mss_settings.json**


.. literalinclude:: samples/config/mss/mss_settings.json.sample


Performance
...........

MSS may also roughly estimate the fuel consumption and thus range of the aircraft
neglecting weather conditions given a proper configuration file specifying the
aircraft performance. Such a file may be loaded using the 'performance settings' button
in Table View. The aircraft performance is specified using tables given in the JSON format.
A basic configuration looks like the following file:

.. literalinclude:: samples/config/mss/performance_simple.json

This example file assumes a constant speed of 400 nm/h and a constant fuel consumption of
2900 lbs/h irrespective of flight level changes. The aircraft weight and available fuel are
also given, but these may also be adjusted in the GUI after loading.

The columns of the cruise table are aircraft weight (lbs), aircraft altitude (feet),
speed (nm/h), and fuel consumption (lbs/h). MSS bilinearily interpolates in aircraft
weight and altitude and extrapolates assuming a constant behaviour outside the given data.
The climb table specifies the aircraft performance when climbing up from 0 feet altitude,
while the descent table specifies the behaviour when descending down to 0 feet altitude.
The column headers are aircraft weight (lbs), aircraft altitude (feet), time spent (minutes),
distance required (nm), and fuel consumed (lbs). To compute the required data for a flight
level change, a bilinear interpolation in the table for current aircraft weight and the
two involved altitudes is performed and the difference of the resulting value is used in
the calculation.


Flight track import/export
..........................

As the planned flight track has to be quickly communicated to different parties having different
desired file formats, MSS supports a simple plugin system for exporting planned flights and
importing changed files back in addition to the main FTML format. These filters may be accessed
from the File menu of the Main Window.

MSS currently offers several import/export filters in the mslib.plugins.io module, which may serve
as an example for the definition of own plugins. The CSV plugin is enabled by default. Enabling the
experimental FliteStar text import plugin would require those lines in the UI settings file:

.. code-block:: json

    "import_plugins": {
        "FliteStar": ["txt", "mslib.plugins.io.flitestar", "load_from_flitestar"]
    },

The dictionary entry defines the name of the filter in the File menu. The list specifies in this
order the extension, the python module implementing the function, and finally the function name.
The module may be placed in any location of the PYTHONPATH or into the configuration directory
path.

An exemplary test file format that can be ex- and imported may be activated by:

.. code-block:: json

    "import_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"]
    },
    "export_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]
    },

The given plugins demonstrate, how additional plugins may be implemented. Please be advised that several
attributes of the waypoints are automatically computed by MSS (for example all time and performance data)
and will be overwritten after reading back the file.