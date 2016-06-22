Web Map Service
=====================================

Once installation and configuration are complete, you can start the
Web Map Service application (provided you have forecast data to
visualise). The file "mss_wms_wsgi.standalone_paste.py" is an
executable Python script starting up a Paste HTTP server with the WMS
WSGI module. A short description of how to start the program is given
in its docstring at the beginning of the file. The file
"mss_wms_wsgi.wsgi" is intended to be used with an Apache web server
installation. "mss_wms_cl.py" is the command line interface for image
batch production.

A few notes:

- If you run the Paste WMS on a remote machine (e.g. on your office
  computer which you access via ssh from a campaign site), consider
  the ssh-tunnel option. Create the ssh connection with the "-L"
  option and start the WMS with the "-ssh" option.

- The Paste WMS currently cannot run multithreaded (Apache does
  support multiple processes). This is due to that a single instance
  of the WSGI application handler class MSS_WMSResponse can create
  only one plot at a time (otherwise you get messed up plots when
  simultaneous requests occur). In the current implementation, only a
  single instance is passed to PASTE (to do all the initialisation
  work only once. To extend the software to handle simultaneous
  requests would probably involve creating a "factory" of
  MSS_WMSResponse instances.. If you want to do this, check if/how
  PASTE handles "worker" factories.

- Creating the capabilities document can take very long (> 1 min) if
  the forecast data files have to be read for the first time (the WMS
  program opens all files and tries to determine the available data
  and elevation ranges). Once the information used for the
  capabilities are in the cache, however, a GetCapabilities request
  should return a document within 1-2 seconds.

- A typical bottleneck for plot generation is when the forecast data
  files are located on a different computer than the WMS server. In
  this case, large amounts of data have to be transferred over the
  network. Hence, when possible, try to make sure the WMS runs on the
  same computer on which the input data files are hosted.


Configuration of the mss server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for the Mission Support System Web Map Service (MSWMS).
The configuration file have to become added to the python search path.

 .. literalinclude:: samples/mss_wms_settings.py.sample


Configuration of wsgi vhost for apache2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can setup a vhost for this service::

 .. literalinclude:: samples/wms_wsgi.sample


Configuration of wsgi auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To restrict access to your data use this script.

 .. literalinclude:: samples/auth.wsgi.sample


