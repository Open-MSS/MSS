Installation
============

The Mission Support System (MSS) including a Web Map Service (MSWMS), a Collaboration Server (MSColab) and a Graphical User Interface (MSUI) is available as
`conda-forge <https://anaconda.org/conda-forge/mss>`_ package.

This channel conda-forge has builds for linux-64, osx-64, win-64, osx-arm64

The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuous integration
build processes.

In 2024, the workflow that has packages co-installed from Anaconda's channel and conda-forge is `no longer supported
<https://conda-forge.org/docs/user/transitioning_from_defaults/#a-historical-note>`_
We recommend since version 10.0.0 of MSS to use `pixi <https://pixi.sh/latest/>`_ for an installation.
Get **pixi** from https://pixi.sh/latest/ for your operation system.


You can now decide if you want to install **mss** as global or a project.
Further details what we provide in the mss package you can read
in the :ref:`components` section.
For the configuratation of the msui client see :ref:`msui-configuration`


Global installation
-------------------

You can install **mss** global without defining a project first.
This method is practical when you are interested in starting the client
and don't need server configurations.::

    pixi global install mss


Usage
.....

::

    msui
    mswms -h
    mscolab -h
    mssautoplot -h

Updating
........

::

    pixi global update mss


Project installation
--------------------

Initialize a new project and navigate to the project directory::

    pixi init MSS
    cd MSS

Use the shell command to activate the environment and start a new shell in there.::

    pixi shell

Add the **mss** dependencies from conda-forge.::

    (MSS) pixi add mss

Usage
.....

Always when you want to start **mss** programs you have after its installation
to activate the environment by pixi shell in the project dir.
On the very first start of **msui** it takes a bit longer because it setups fonts.::

    cd MSS
    pixi shell

::

    (MSS) msui
    (MSS) mswms -h
    (MSS) mscolab -h
    (MSS) mssautoplot -h

Updating
........

::

    cd MSS
    pixi shell
    (MSS) pixi update mss


Server based installation example
---------------------------------

For a WMS server setup or MSColab setup you may want to have a dedicated user for the apache2 wsgi script.
We suggest to create a mss user.

* create a mss user on your system
* login as mss user
* do a pixi project installation of **mss**
For a simple test you could start the builtin standalone *mswms* and *mscolab* server::

   $ mswms &
   $ mscolab start

Point a browser for the verification of both servers installed on

  - `http://127.0.0.1:8083/status <http://127.0.0.1:8083/status>`_
  - `http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1 <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_



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
