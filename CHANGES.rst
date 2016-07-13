Changelog
================

Version 1.2.0
------------------------------------

New Features:
 - mss client, setup default configuration and json config file, #36, #37
 - mss client get capabilities update without new login, #29
 - wsgi and standalone server refactored and merged into one application,
   mswms is the new name of the standalone server #30
 - server configuration files simplified, #39
 - server templates got more variables defined in mss_wms_settings.py, #44, #45
 - geopy distance calculation dependency replaced by pyproj, #34
 - Simplification for adding or removing CLaMS parameters, #12

Bug Fixes:
 - execute bit only on executables, #40

Other Changes:
 - Isabell Krisch added to AUTHORS
 - skipped dependency of conda-forge, because geopy function replaced, #38
 - https://anaconda.org/atmo/mss introduced
 - moved of mslib.thirdparty.owslib to mslib.owslib and hardcoded all imports in owslib to mslib.owslib, #1
 - improved documentations


Version 1.1.0 
----------------------------------

New Features:
 - Vertical section styles supported in standalone server, #10
 - More formats for exchanging flight paths implemented, #7
 - Reverse flight path, #11 
 - Displaying model data from CLaMS, #4
 - Visualisation of gravity wave forecasts, #14
 - Improved labels in plots, #8
   
Bug Fixes:
 - Improved debugging in standalone server, #9
 - Fix for Labels accumulate in plots upon saving, #5
 - PEP8, #19


Other Changes:
 - Namespace refactored, all modules dependend to mslib #24
 - Sphinx documentation introduced, #25, #26
 - Documentation on http://mss.rtfd.io 
 - Installation recipes based on conda  
 - First public release on June 28, 2016

