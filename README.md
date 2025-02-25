**Chat:**
[![IRC: #mss-general on libera.chat](https://img.shields.io/badge/libera.chat-%23MSS_General-blue)](https://web.libera.chat/?channels=#mss-general)
[![IRC: #mss-gsoc on libera.chat](https://img.shields.io/badge/libera.chat-%23MSS_GSoC-brightgreen)](https://web.libera.chat/?channels=#mss-gsoc)


Mission Support System Usage Guidelines
=======================================

Welcome to the Mission Support System software for planning
atmospheric research flights. This document is intended to point you
into the right direction in order to get the software working on your
computer.


## Installing MSS

We distinguish between Developer and User installations.

### Developer Installation
Please read our [contributing](https://open-mss.github.io/contributing/) pages.
and [development](https://mss.readthedocs.io/en/stable/development.html) guidelines

### User Installation

Get **pixi** from https://pixi.sh/latest/ for your operation system.

You can now decide if you want to install **mss** as global or a project.

#### Global installation
You can install **mss** global without defining a project first.
This method is practical when you are interested in starting the client
and don't need server configurations.

    pixi global install mss

#### Usage

    msui
    mswms -h
    mscolab -h
    mssautoplot -h


##### Updating

    pixi global update mss

#### Project installation
Initialize a new project and navigate to the project directory.

    pixi init MSS
    cd MSS

Use the shell command to activate the environment and start a new shell in there.

    pixi shell

Add the **mss** dependencies from conda-forge.

    (MSS) pixi add mss

##### Usage
Always when you want to start **mss** programs you have after its installation
to activate the environment by pixi shell in the project dir.
On the very first start of **msui** it takes a bit longer because it setups fonts.

    cd MSS
    pixi shell

    (MSS) msui
    (MSS) mswms -h
    (MSS) mscolab -h
    (MSS) mssautoplot -h

##### Updating

    cd MSS
    pixi shell
    (MSS) pixi update mss


Current release info
====================
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6572620.svg)](https://doi.org/10.5281/zenodo.6572620)
[![JuRSE Code Pick](https://img.shields.io/badge/JuRSE_Code_Pick-July_2024-blue)](https://www.fz-juelich.de/en/rse/jurse-community/jurse-code-of-the-month/july-2024)
[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/mss.svg)](https://anaconda.org/conda-forge/mss)
[![DOCS](https://img.shields.io/badge/%F0%9F%95%AE-docs-green.svg)](https://mss.rtfd.io)
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

Acknowledgements
----------------

We are very grateful for your continuing support for MSS!

See our [Contributors page](https://mss.readthedocs.io/en/stable/authors.html) for a list of authors. See also our info on [funding](
https://mss.readthedocs.io/en/stable/funding.html).