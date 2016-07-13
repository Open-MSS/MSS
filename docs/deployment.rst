wms - Web Map Service
=====================================

Once installation and configuration are complete, you can start the
Web Map Service application (provided you have forecast data to visualise).
The file "mswms" is an executable Python script starting  up a Paste HTTP server
with the WMS WSGI module.
A short description of how to start the program is given by the --help option.
The file "wms.wsgi" is intended to be used with an Apache web server
installation. "mss_wms_cl.py" is the command line interface for image
batch production.

A few notes:

- If you run the Paste WMS on a remote machine (e.g. on your office
  computer which you access via ssh from a campaign site), consider
  the ssh-tunnel option. Create the ssh connection with the "-L"
  option and start the WMS with the tunneled port as option.

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

.. _apache-deployment:

Apache server setup
--------------------------------


Our examples are based on the following directories located in the home directory of the mss user::

 .
 ├── config
 │   └── mss_wms_settings.py
 ├── log
 │   └── mss_error.log
 ├── miniconda2
 │   ├── bin
 │   ├── conda-bld
 │   ├── conda-meta
 │   ├── envs
 │   ├── etc
 │   ├── include
 │   ├── lib
 │   ├── LICENSE.txt
 │   ├── pkgs
 │   ├── share
 │   ├── ssl
 │   └── var
 └── wsgi
     ├── auth.wsgi
     └── wms.wsgi


Create that mss user first.



Configuration of apache mod_wsgi.conf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have to add to mod_wsgi.conf::

  WSGIPythonPath /home/mss/config:/home/mss/miniconda2/lib/python2.7/site-packages


By this setting you override the PYTHONPATH environment variable. So you have also to add
the site-packes directory of your miniconda or anaconda installation besides the config file path.




Configuration of wsgi for wms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can setup a vhost for this service.

**/home/mss/wsgi/wms.wsgi**


 .. literalinclude:: samples/wsgi/wms.wsgi


Configuration of wsgi auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To restrict access to your data use this script.

**/home/mss/wsgi/auth.wsgi**


 .. literalinclude:: samples/wsgi/auth.wsgi


Configuration of your site as vhost
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have to setup a webserver server site configuration file

**/etc/apache2/sites-available/mss.yourserver.de.conf**


 .. literalinclude:: samples/sites-available/mss.yourserver.de.conf


Enable it with a2ensite mss.yourserver.de.conf


Configuration file of the wms server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for the Mission Support System Web Map Service (wms).
The configuration file have to become added to the /home/mss/config directory

**/home/mss/config/mss_wms_settings.py**

 .. literalinclude:: samples/config/wms/mss_wms_settings.py.sample


You have to adopt this file to your data.

.. _mswms-deployment:

Standalone server setup
------------------------------

For the standalone server *mswms* you need the path of your mss_wms_settings.py added to the PYTHONPATH. E.g.::

 export PYTHONPATH=/home/mss/config




