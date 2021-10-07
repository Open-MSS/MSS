Installation
=================


.. image:: https://anaconda.org/conda-forge/mss/badges/installer/conda.svg


`Anaconda <https://www.anaconda.com/>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on the channel.

`conda-forge <https://anaconda.org/conda-forge/mss>`_

This channel conda-forge has builds for osx-64, linux-64, win-64

The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuos integration
build processes.

To install MSS you need the conda installer or its drop-in replacement the mamba installer. We explain below how you
get by the conda installer the mamba installer. Mamba is a fast cross platform installerr.

Automatic installation
++++++++++++++++++++++

* For **Windows**, go `here <https://github.com/Open-MSS/mss-install/blob/main/Windows.bat?raw=1>`_

  #. Right click on the webpage and select "Save as..." to download the file

  #. Double click the downloaded file and follow further instructions

    * For fully automatic installation, open cmd and execute it with :code:`/Path/To/Windows.bat -a`

* For **Linux/Mac**, go `here <https://github.com/Open-MSS/mss-install/blob/main/LinuxMac.sh?raw=1>`_

  #. Right click on the webpage and select "Save as..." to download the file

  #. Make it executable via :code:`chmod +x LinuxMac.sh`

  #. Execute it and follow further instructions :code:`./LinuxMac.sh`

    * For fully automatic installation, run it with the -a parameter :code:`./LinuxMac.sh -a`

Preparations for installing MSS
+++++++++++++++++++++++++++++++

The fastest way to get the conda installer is to start with Miniconda or Miniforge.
This is a small subset of the Anaconda package with only the conda installer and its dependencies.
If you do prefer to use over 7K open-source packages install Anaconda.

We recommend to install this for the local user. This does not require administrator permissions.

As **Beginner** start with an installation of Miniconda
- `Get Miniconda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/>`_

If you are an Advanced User you know that `Anaconda <https://docs.continuum.io/anaconda/install/>`_
or `Miniforge <https://github.com/conda-forge/miniforge/>`_ are compatible too.


conda-forge channel
+++++++++++++++++++++

Please add the channel conda-forge to your defaults::

  $ conda config --add channels conda-forge

The conda-forge channel must be on top of the list before the anaconda default channel.

Install
+++++++

You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have to 
leave out the 'source' here and below). ::

    $ conda create -n mssenv mamba
    $ conda activate mssenv
    (mssenv) $ mamba install mss=$mss_version python
    (mssenv) $ mss

Update
++++++

builtin update
--------------

With 5.0 we provide a new feature for updating MSS by the UI or the command line
After you started the MSS UI it informs you after a while if there is a new update available.
From the command line you can trigger this update feature by ::

    (mssenv) $ mss --update



other methods
-------------

For updating an existing MSS installation to the current version, it is best to install
it into a new environment. If your current version is not far behind the new version
you could try the mamba update mss as described.


.. Important::
  mamba is under development. All dependencies of MSS and MSS itselfs are under development.
  Sometimes this update feature of mamba can't resolve from existing to new dependencies.

search for MSS what you can get ::

   (mssenv) $ mamba search mss
   ...
   $mss_search


compare what you have installed ::

   (mssenv) $ mamba list mss

     mss                            3.0.2     py39hf3d152e_0    conda-forge


We have reports that often an update suceeds by using the install option and the new version number,
in this example $mss_version and python as second option ::

   (mssenv) $ mamba install mss=$mss_version python

All attemmpts show what you get if you continue. **Continue only if you get what you want.**

The alternative is to use a new environment and install mss.



For further details of configurating mss :ref:`mss-configuration`



Server based installation
~~~~~~~~~~~~~~~~~~~~~~~~~

For a wms server setup or mscolab setup you may want to have a dedicated user for the apache2 wsgi script.
We suggest to create a mss user.

* create a mss user on your system
* login as mss user
* create a *src* directory in /home/mss
* cd src
* get `miniconda <http://conda.pydata.org/miniconda.html>`_ for Python 3
* set execute bit on install script
* execute script, enable environment in .bashrc
* login again or export PATH="/home/mss/miniconda3/bin:$PATH"
* conda create -n mssenv mamba
* conda activate mssenv
* mamba install mss=$mss_version python

For a simple test you could start the builtin standalone *mswms* and *mscolab* server::

   $ mswms &
   $ mscolab start

Point a browser for the verification of both servers installed on

  - `http://127.0.0.1:8083/status <http://127.0.0.1:8083/status>`_
  - `http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1 <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_

Further details in the components section on `<http://mss.rtfd.io>`_


Based on Docker
+++++++++++++++

You can use images `from the docker hub <https://hub.docker.com/r/openmss/mss>`_. based on our `repository <https://github.com/Open-MSS/dockerhub>`_

Build settings are based on the stable branch. Our openmss/mss:latest has any update in the stable branch.


You can start server and client by loading the image ::

 $ xhost +local:docker
 $ docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix openmss/mss:latest  /bin/bash
 $ /opt/conda/envs/mssenv/bin/mss &
 $ /opt/conda/envs/mssenv/bin/mswms --port 80 &
 $ /opt/conda/envs/mssenv/bin/mscolab &
 $ curl http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1
 $ curl http://localhost:8083/status

The WMS server initialized by demodata, and the mscolab server and the userinterface can be started by ::

 $  xhost +local:docker
 $  docker run -d --net=host -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix openmss/mss:latest MSS





