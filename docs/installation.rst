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
