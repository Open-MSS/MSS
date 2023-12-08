Mission Support System Usage Guidelines
=======================================

Welcome to the Mission Support System software for planning
atmospheric research flights. This document is intended to point you
into the right direction in order to get the software working on your
computer.


Installing MSS
==============

Automatically
-------------

- For **Windows**, go [here](https://github.com/Open-MSS/mss-install/blob/main/Windows.bat?raw=1)
    - Right click on the webpage and select "Save as..." to download the file
    - Double click the downloaded file and follow further instructions
        - For fully automatic installation, open cmd and execute it with `/Path/To/Windows.bat -a`
- For **Linux/Mac**, go [here](https://github.com/Open-MSS/mss-install/blob/main/LinuxMac.sh?raw=1)
    - Right click on the webpage and select "Save as..." to download the file
    - Make it executable via `chmod +x LinuxMac.sh`
    - Execute it and follow further instructions `./LinuxMac.sh`
        - For fully automatic installation, run it with the -a parameter `./LinuxMac.sh -a`

Manually
--------

As **Beginner** start with an installation of Miniforge 
Get [miniforge](https://github.com/conda-forge/miniforge#download) for your Operation System


You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have
to leave out the 'source' here and below).

```
  $ mamba create -n mssenv
  $ mamba activate mssenv
  (mssenv) $ mamba install mss python
```
For updating an existing MSS installation to the current version, it is
best to install it into a new environment. If an existing environment
shall be updated, it is important to update all packages in this
environment. 

```
  $ mamba activate mssenv
  (mssenv) $ msui --update
```

It is possible to list all versions of `mss` available on your platform with:

```
    $ mamba search mss --channel conda-forge
```

For a simple test you can setup a demodata wms server and start a msolab server with default settings

```
  (mssenv) $ mswms_demodata --seed
  (mssenv) $ export PYTHONPATH=~/mss
  (mssenv) $ mswms &
  (mssenv) $ mscolab start &
  (mssenv) $ msui
```




Current release info
====================
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6572620.svg)](https://doi.org/10.5281/zenodo.6572620)
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss)
[![DOCS](https://img.shields.io/badge/%F0%9F%95%AE-docs-green.svg)](http://mss.rtd.io)
[![Conda Recipe](https://img.shields.io/badge/recipe-mss-green.svg)](https://anaconda.org/conda-forge/mss) 
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss)
[![Coverage Status](https://coveralls.io/repos/github/Open-MSS/MSS/badge.svg?branch=develop)](https://coveralls.io/github/Open-MSS/MSS?branch=develop)


Publications
============

Please read the reference documentation

   Bauer, R., Grooß, J.-U., Ungermann, J., Bär, M., Geldenhuys, M., and Hoffmann, L.: The Mission Support
   System (MSS v7.0.4) and its use in planning for the SouthTRAC aircraft campaign, Geosci.
   Model Dev., 15, 8983–8997, https://doi.org/10.5194/gmd-15-8983-2022, 2022.

   Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based
   tool to plan atmospheric research flights, Geosci. Model Dev., 5,
   55-71, https://doi.org/10.5194/gmd-5-55-2012, 2012.

and the paper's Supplement (which includes a tutorial) before using the
application. The documents are available at:

- http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012.pdf
- http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012-supplement.pdf

For copyright information, please see the files NOTICE and LICENSE, located
in the same directory as this README file.
   

   When using this software, please be so kind and acknowledge its use by
   citing the above mentioned reference documentation in publications,
   presentations, reports, etc. that you create. Thank you very much.



