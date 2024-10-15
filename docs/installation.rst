Installation
============

The Mission Support System (MSS) including a Web Map Service, a Collaboration Server  and a Graphical User Interface is available as
`conda-forge <https://anaconda.org/conda-forge/mss>`_ package.

This channel conda-forge has builds for osx-64, linux-64, win-64

The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuous integration
build processes.

We provide an automatic installation and a manual installation.

We recommend to use Mamba for an installation.

Automatic
---------

* For **Windows**, use `Windows.bat <https://github.com/Open-MSS/mss-install/blob/main/Windows.bat?raw=1>`_

  #. Right click on the webpage and select "Save as..." to download the file

  #. Double click the downloaded file and follow further instructions

    * For fully automatic installation, open cmd and execute it with :code:`/Path/To/Windows.bat -a`

* For **Linux/Mac**, use `LinuxMac.sh <https://github.com/Open-MSS/mss-install/blob/main/LinuxMac.sh?raw=1>`_

  #. Right click on the webpage and select "Save as..." to download the file

  #. Make it executable via :code:`chmod +x LinuxMac.sh`

  #. Execute it and follow further instructions :code:`./LinuxMac.sh`

    * For fully automatic installation, run it with the -a parameter :code:`./LinuxMac.sh -a`


Manual
------

Mamba based installation
........................



We strongly recommend to start from `Miniforge3 <https://github.com/conda-forge/miniforge#install>`_,
a community project of the conda-forge community.

As **Beginner** start with an installation of Miniforge3
- Get `Miniforge3 <https://github.com/conda-forge/miniforge#download>`__ for your Operation System

If you use already Mambaforge please read the `FAQ <https://github.com/conda-forge/miniforge#faq>`__



Install MSS
~~~~~~~~~~~

You must install mss into a new environment to ensure the most recent
versions for dependencies. ::

    $ mamba create -n mssenv
    $ mamba activate mssenv
    (mssenv) $ mamba install mss=$mss_version python
    (mssenv) $ msui


Mamba Server based installation example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a wms server setup or mscolab setup you may want to have a dedicated user for the apache2 wsgi script.
We suggest to create a mss user.

* create a mss user on your system
* login as mss user
* create a *src* directory in /home/mss
* cd src
* get `Miniforge3 <https://github.com/conda-forge/miniforge#download>`__
* set execute bit on install script
* execute script, enable environment in .bashrc
* login again
* mamba create -n mssenv
* mamba activate mssenv
* mamba install mss=$mss_version python

For a simple test you could start the builtin standalone *mswms* and *mscolab* server::

   $ mswms &
   $ mscolab start

Point a browser for the verification of both servers installed on

  - `http://127.0.0.1:8083/status <http://127.0.0.1:8083/status>`_
  - `http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1 <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_

Further details in the components section on `<http://mss.rtfd.io>`_




Conda based installation
........................

`Anaconda <https://www.anaconda.com/>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

Please add the channel conda-forge to your defaults::

  $ conda config --add channels conda-forge

The conda-forge channel must be on top of the list before the anaconda default channel.

From September 2023 libmamba is the `default installer in anaconda <https://conda.org/blog/2023-07-05-conda-libmamba-solver-rollout/>`__.

Install MSS
~~~~~~~~~~~

You must install mss into a new environment to ensure the most recent
versions for dependencies. ::

    $ conda create -n mssenv
    $ conda activate mssenv
    (mssenv) $ conda install mss=$mss_version python --solver=libmamba
    (mssenv) $ msui


Update Methods
..............

For updating an existing MSS installation to the current version, it is best to install
it into a new environment. If your current version is not far behind the new version
you could try the `mamba update mss` as described.


.. Important::
  mamba is under development. All dependencies of MSS and MSS itself are under development.
  Sometimes this update feature of mamba can't resolve from existing to new dependencies.

search for MSS what you can get ::

   (mssenv) $ mamba search mss
   ...
   $mss_search


compare what you have installed ::

   (mssenv) $ mamba list mss

     mss                            7.0.2     py310hff52083_0    conda-forge


We have reports that often an update succeeds by using the install option and the new version number,
in this example $mss_version and python as second option ::

   (mssenv) $ mamba install mss=$mss_version python

All attemmpts show what you get if you continue. **Continue only if you get what you want.**

The alternative is to use a new environment and install mss.



For further details of configuring mss :ref:`msui-configuration`


Docker Instance
---------------

You can use images `from the docker hub <https://hub.docker.com/r/openmss/mss>`_. based on our `repository <https://github.com/Open-MSS/dockerhub>`_

Build settings are based on the stable branch. Our openmss/mss:latest has any update in the stable branch.


You can start server and client by loading the image ::

 $ xhost +local:docker
 $ docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --network host openmss/mss:latest  /bin/bash
 $ /opt/conda/envs/mssenv/bin/msui &
 $ /opt/conda/envs/mssenv/bin/mswms --port 80 &
 $ /opt/conda/envs/mssenv/bin/mscolab start &
 $ curl http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1
 $ curl http://localhost:8083/status

The WMS server initialized by demodata, and the mscolab server and the userinterface can be started by ::

 $  xhost +local:docker
 $  docker run -d -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --network host openmss/mss:latest MSS


If you want only to start the msui do this by ::

 $  xhost +local:docker
 $  docker run -d -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --network host openmss/mss:latest msui


We have not setup keyring in the docker container. When a login is needed you will get a message:

INFO: Can't use Keyring on your system: No recommended backend was available.
Install a recommended 3rd party backend package; or, install the keyrings.alt package
if you want to use the non-recommended backends. See https://pypi.org/project/keyring
for details.

For using keyring in a the openmss/mss container you need to start the container with different options
and after installing gnome-keyring you have to configure it. ::

 $ xhost +local:docker
 $ docker run -ti --ulimit nofile=65536:65536 --cap-add=IPC_LOCK --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix --network host openmss/mss:latest  /bin/bash
 $ apt update
 $ apt install gnome-keyring
 $ conda activate mssenv
 $ dbus-run-session -- sh # start a new D-bus shell, prompt changes to a hash
 # echo 'credpass' | gnome-keyring-daemon --unlock # unlock the systems keyring
 # msui # starts msui




Singularity
-----------

You can use images `from the docker hub <https://hub.docker.com/r/openmss/mss>`_. based on our `repository <https://github.com/Open-MSS/dockerhub>`_ by converting them to singularity
or build from our `singularity definition <https://github.com/Open-MSS/singularity>`_

Build settings are based on the stable branch. Our openmss/mss:latest has any update in the stable branch.


You can start server and client by loading the image ::

  $ host +
  $ singularity build -f mss.sif Singularity.def
  $ singularity shell mss.sif
  $ Singularity > msui # starts the ui
  $ Singularity > mswms_demodata --seed  # creates in your $HOME a mss/ folder with testdata
  $ Singularity > export PYTHONPATH=$HOME/mss; mswms # starts the development server
  $ Singularity > mscolab db --init; mscolab start # starts the mscolab development server
