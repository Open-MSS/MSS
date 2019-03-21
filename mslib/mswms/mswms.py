#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

    mslib.mswms.mswms
    ~~~~~~~~~~~~~~~~~

    The module can be run with the Python Flask framework and can be run as
    python msswms.py.

    :copyright: Copyright 2016 Reimar Bauer
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

from __future__ import print_function
from __future__ import absolute_import

<<<<<<< HEAD
import paste.httpserver
=======
# Hack to fix missing PROJ4 env var in root environment
import os
import setuptools
import sys


if os.getenv("PROJ_LIB") is None or os.getenv("PROJ_LIB") == "PROJ_LIB":
    conda_file_dir = setuptools.__file__
    conda_dir = conda_file_dir.split('lib')[0]
    proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
    os.environ["PROJ_LIB"] = proj_lib
    # if proj4 is installed we have also in the base environment epsg data
    if not os.path.exists(proj_lib):
        os.makedirs(proj_lib)
        epsg_file = os.path.join(proj_lib, 'epsg')
        if not os.path.exists(epsg_file):
            with open(os.path.join(proj_lib, 'epsg'), 'w') as fid:
                fid.write("# Placeholder for epsg data")

>>>>>>> Update mswms
import argparse
import logging


from mslib import __version__
from mslib.mswms.wms import mss_wms_settings, app
from mslib.utils import setup_logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="show version", action="store_true", default=False)
    parser.add_argument("--host", help="hostname",
                        default="127.0.0.1", dest="host")
    parser.add_argument("--port", help="port", dest="port", default="8081")
    parser.add_argument("--threadpool", help="threadpool", dest="use_threadpool", action="store_true", default=False)
    parser.add_argument("--debug", help="show debugging log messages on console", action="store_true", default=False)
    parser.add_argument("--logfile", help="If set to a name log output goes to that file", dest="logfile",
                        default=None)
    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    setup_logging(args)

    if mss_wms_settings.__dict__.get('enable_basic_http_authentication', False):
        logging.debug("Enabling basic HTTP authentication. Username and "
                      "password required to access the service.")

    logging.info(u"Configuration File: '{}'".format(mss_wms_settings.__file__))

    app.run(args.host, args.port)


if __name__ == '__main__':
    main()
