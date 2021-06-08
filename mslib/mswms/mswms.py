#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

    mslib.mswms.mswms
    ~~~~~~~~~~~~~~~~~

    The module can be run with the Python Flask framework and can be run as
    python mswms.py.

    :copyright: Copyright 2016 Reimar Bauer
    :copyright: Copyright 2016-2021 by the mss team, see AUTHORS.
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

import argparse
import logging
import sys

from mslib import __version__
from mslib.mswms.wms import mss_wms_settings
from mslib.mswms.wms import app as application
from mslib.utils import setup_logging, Updater, Worker


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
    parser.add_argument("--update", help="Updates MSS to the newest version", action="store_true", default=False)
    args = parser.parse_args()

    if args.version:
        print("***********************************************************************")
        print("\n            Mission Support System (mss)\n")
        print("***********************************************************************")
        print("Documentation: http://mss.rtfd.io")
        print("Version:", __version__)
        sys.exit()

    updater = Updater()
    if args.update:
        updater.on_update_available.connect(lambda old, new: updater.update_mss())
        updater.on_log_update.connect(lambda s: print(s.replace("\n", "")))
        updater.on_status_update.connect(lambda s: print(s.replace("\n", "")))
        updater.run()
        while Worker.workers:
            list(Worker.workers)[0].wait()
        sys.exit()

    setup_logging(args)
    updater.on_update_available.connect(lambda old, new: logging.info(f"MSS can be updated from {old} to {new}.\nRun"
                                                                      " the --update argument to update the server."))
    updater.run()

    logging.info("Configuration File: '%s'", mss_wms_settings.__file__)

    application.run(args.host, args.port)


if __name__ == '__main__':
    main()
