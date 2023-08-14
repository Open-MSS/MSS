# Installation


## Install distributed version by mamba

The Mission Support System (MSS) including a Web Map Service a Collaboration Server and a Graphical User Interface is available as
[conda-forge](https://anaconda.org/conda-forge/mss) package.


We strongly recommend to start from [Mambaforge](https://mamba.readthedocs.io/en/latest/installation.html)
a community project of the conda-forge community.

You can install it either automatically with the help of a script or manually.

### Automatically


* For **Windows**, use [Windows.bat](https://github.com/Open-MSS/mss-install/blob/main/Windows.bat?raw=1)

 1. Right click on the webpage and select "Save as..." to download the file
 1. Double click the downloaded file and follow further instructions
    * For fully automatic installation, open cmd and execute it with `/Path/To/Windows.bat -a`

* For **Linux/Mac**, use [LinuxMac.sh](https://github.com/Open-MSS/mss-install/blob/main/LinuxMac.sh?raw=1)

 1. Right click on the webpage and select "Save as..." to download the file
 1. Make it executable via `chmod +x LinuxMac.sh`
 1. Execute it and follow further instructions `./LinuxMac.sh`
    * For fully automatic installation, run it with the -a parameter `./LinuxMac.sh -a`


### Manually

As **Beginner** start with an installation of Mambaforge 
Get [mambaforge](https://github.com/conda-forge/miniforge#mambaforge) for your Operation System


You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have
to leave out the 'source' here and below).

```
  $ mamba create -n mssenv
  $ mamba activate mssenv
  $ mamba install mss python
```
For updating an existing MSS installation to the current version, it is
best to install it into a new environment. If an existing environment
shall be updated, it is important to update all packages in this
environment. 

```
  $ mamba activate mssenv
  $ msui --update
```


### Server based installation


For a wms server setup or mscolab setup you may want to have a dedicated
user for the apache2 wsgi script. We suggest to create a mss user.

-   create a mss user on your system
-   login as mss user
-   create a *src* directory in /home/mss
-   cd src
-   get [mambaforge](https://github.com/conda-forge/miniforge#mambaforge)
-   set execute bit on install script
-   execute script, enable environment in .bashrc
-   login again or export PATH="/home/mss/mambaforge/bin:\$PATH"
-   python --version should tell Python 3.X.X
-   mamba create -n mssenv
-   mamba activate mssenv
-   mamba install mss python

For a simple test you could start the builtin standalone *mswms* and
*mscolab* server:

```
  $ mswms &
  $ mscolab start
```

Point a browser for the verification of both servers installed on

  - <http://127.0.0.1:8083/status> 
  - <http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>

Further details in the components section on <http://mss.rtfd.io>
