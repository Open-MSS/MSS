# Installation


![image](https://anaconda.org/conda-forge/mss/badges/installer/conda.svg)


## Install distributed version by conda


[Anaconda](https://www.continuum.io/why-anaconda) provides an
enterprise-ready data analytics platform that empowers companies to
adopt a modern open data science analytics architecture.

MSS is available as anaconda package on the channel.

[conda-forge/mss](https://anaconda.org/conda-forge/mss)

The conda-forge packages are based on defaults and other conda-forge
packages. This channel conda-forge has builds for osx-64, linux-64,
win-64

The conda-forge [github organization](https://conda-forge.github.io/)
uses various automated continuos integration build processes.

### conda-forge channel

Please add the channel conda-forge to your defaults:

    $ conda config --add channels conda-forge
    $ conda config --add channels defaults

The last channel added gets on top of the list. This gives the order:
First search in default packages then in conda-forge.

You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have
to leave out the 'source' here and below). :

    $ conda create -n mssenv python=3
    $ conda activate mssenv
    $ conda install mamba
    $ mamba install mss

For updating an existing MSS installation to the current version, it is
best to install it into a new environment. If an existing environment
shall be updated, it is important to update all packages in this
environment. :

    $ conda activate mssenv
    $ conda update --all
    $ mss

For further details mss-configuration

### Server based installation


For a wms server setup or mscolab setup you may want to have a dedicated
user for the apache2 wsgi script. We suggest to create a mss user.

-   create a mss user on your system
-   login as mss user
-   create a *src* directory in /home/mss
-   cd src
-   get [miniconda](http://conda.pydata.org/miniconda.html) for Python 3
-   set execute bit on install script
-   execute script, enable environment in .bashrc
-   login again or export PATH="/home/mss/miniconda3/bin:\$PATH"
-   python --version should tell Python 3.X.X
-   conda create -n mssenv python=3
-   conda activate mssenv
-   conda install mamba
-   mamba install mss

For a simple test you could start the builtin standalone *mswms* and
*mscolab* server:

    $ mswms &
    $ mscolab start

Point a browser for the verification of both servers installed on

  - <http://127.0.0.1:8083/status> 
  - <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>

Further details in the components section on <http://mss.rtfd.io>
