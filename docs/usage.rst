mss - User Interface
======================================

The executable for the user interface application is "**mss**". It
does not provide any command line options. Warnings about CDAT
features are due to the NAppy package and can be ignored. The program
should open the main window of the user interface, from which you can
open further windows, including top view, side view and so on. In case
you get an exception on startup, your system probably misses one of
the required Python packages. Check the INSTALL file for information.

Configuration for the user interface is located in
"mss_settings.py". In this file, you can specify, for instance, the
default WMS URLs for the WMS client, the size of the local image cache
(the MSUI caches retrieved WMS images to accelerate repeated
retrievals), or the predefined locations that the user can select in
the table view.

A few options influencing the appearance of the displayed plots and
flight tracks (colours etc.) can be set directly in the user
interface (top view and side view).

Configuration of User Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file includes configuration settings central to the entire
Mission Support User Interface (mss). Among others, define

 - available map projections
 - vertical section interpolation options
 - the lists of predefined web service URLs
 - predefined waypoints for the table view
 - batch products for the loop view in this file.

You have to provide the path of the mss_settings.py by e.g.::

   $ mkdir "$HOME/.config/mss"
   $ export PYTHONPATH="$HOME/.config/mss"


.. literalinclude:: samples/mss_settings.py.sample


