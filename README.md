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

Installing `MSS` from the `conda-forge` channel can be achieved by adding `conda-forge` to your channels with:


    $ conda config --add channels conda-forge

Once the `conda-forge` channel has been enabled, `mss` can be installed with:

    $ conda create -n mssenv mamba
    $ conda activate mssenv
    (mssenv) $ mamba install mss=6.0.0 python
    (mssenv) $ mss

It is possible to list all versions of `mss` available on your platform with:


    $ mamba search mss --channel conda-forge


Current release info
====================


| Name | Downloads | Version | Platforms |
| --- | --- | --- | --- |
| [![Conda Recipe](https://img.shields.io/badge/recipe-mss-green.svg)](https://anaconda.org/conda-forge/mss) | [![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss) | [![Conda Version](https://img.shields.io/conda/vn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss) | [![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss) |


[![Coverage Status](https://coveralls.io/repos/github/Open-MSS/MSS/badge.svg?branch=develop)](https://coveralls.io/github/Open-MSS/MSS?branch=develop)


Publications
============

Please read the reference documentation

   Rautenhaus, M., Bauer, G., and Doernbrack, A.: A web service based
   tool to plan atmospheric research flights, Geosci. Model Dev., 5,
   55-71, doi:10.5194/gmd-5-55-2012, 2012.

and the paper's Supplement (which includes a tutorial) before using the
application. The documents are available at:

- http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012.pdf
- http://www.geosci-model-dev.net/5/55/2012/gmd-5-55-2012-supplement.pdf

For copyright information, please see the files NOTICE and LICENSE, located
in the same directory as this README file.
   

   When using this software, please be so kind and acknowledge its use by
   citing the above mentioned reference documentation in publications,
   presentations, reports, etc. that you create. Thank you very much.



