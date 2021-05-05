Installation
=================


.. image:: https://anaconda.org/conda-forge/mss/badges/installer/conda.svg



Install distributed version by conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Anaconda <https://www.anaconda.com/>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on the channel.

`conda-forge <https://anaconda.org/conda-forge/mss>`_

This channel conda-forge has builds for osx-64, linux-64, win-64

The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuos integration
build processes.

To install MSS you need the conda installer or its drop-in replacement the mamba installer. We explain below how you
get by the conda installer the mamba installer. Mamba is a fast cross platform installerr.

Preparations for installing MSS
+++++++++++++++++++++++++++++++

The fastest way to get the conda installer is to start with Miniconda.
This is a small subset of the Anaconda package with only the conda installer and its dependencies.
If you do prefer to use over 7K open-source packages install Anaconda.

We recommend to install this for the local user. This does not require administrator permissions.


- `Get miniconda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/>`_
- `Get Anaconda <https://docs.continuum.io/anaconda/install/>`_


conda-forge channel
+++++++++++++++++++++

Please add the channel conda-forge to your defaults::

  $ conda config --add channels conda-forge

The conda-forge channel must be on top of the list before the anaconda default channel.

You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have to 
leave out the 'source' here and below). ::

    $ conda create -n mssenv mamba
    $ conda activate mssenv
    $ mamba install mss


You need to reactivate after the installation once the environment to setup all needed enironment
variables. ::

    $ conda deactivate
    $ conda activate mssenv
    $ mss


For updating an existing MSS installation to the current version, it is best to install
it into a new environment. If an existing environment shall be updated, it is important
to update all packages in this environment. ::

   $ conda activate mssenv
   $ mamba update --all
   $ mss

For further details :ref:`mss-configuration`

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
* mamba install mss

For a simple test you could start the builtin standalone *mswms* and *mscolab* server::

   $ mswms &
   $ mscolab start

Point a browser for the verification of both servers installed on

  - `http://127.0.0.1:8083/status <http://127.0.0.1:8083/status>`_
  - `http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1 <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_

Further details in the components section on `<http://mss.rtfd.io>`_



