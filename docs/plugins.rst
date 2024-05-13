MSUI plugins
============

.. _msuiplugins:


Flight track import/export
--------------------------

As the planned flight track has to be quickly communicated to different parties having different
desired file formats, MSS supports a simple plugin system for exporting planned flights and
importing changed files back in addition to the main FTML format. These filters may be accessed
from the File menu of the Main Window.

MSS currently offers several import/export filters in the mslib.plugins.io module, which may serve
as an example for the definition of own plugins. Take care that added plugins use different file extensions.
They are listed below. The CSV plugin is enabled by default.
Enabling the experimental FliteStar text import plugin would require those lines in
the UI settings file:

.. code:: text

    "import_plugins": {
        "FliteStar": ["fls", "mslib.plugins.io.flitestar", "load_from_flitestar"]
    },

The dictionary entry defines the name of the filter in the File menu. The list specifies in this
order the extension, the python module implementing the function, and finally the function name.
The module may be placed in any location of the PYTHONPATH or into the configuration directory
path.

An exemplary test file format that can be ex- and imported may be activated by:

.. code:: text

    "import_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "load_from_txt"]
    },
    "export_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"]
    },

The given plugins demonstrate, how additional plugins may be implemented. Please be advised that several
attributes of the waypoints are automatically computed by MSS (for example all time and performance data)
and will be overwritten after reading back the file.

**Available Export Formats:**

.. code:: text

    "export_plugins": {
        "Text": ["txt", "mslib.plugins.io.text", "save_to_txt"],
        "KML": ["kml", "mslib.plugins.io.kml", "save_to_kml"],
        "GPX": ["gpx", "mslib.plugins.io.gpx", "save_to_gpx"]
    },


User contributed Plugins
------------------------

.. include:: samples/plugins/navaid.rst
