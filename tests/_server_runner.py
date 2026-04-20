# -*- coding: utf-8 -*-
"""
    tests._server_runner
    ~~~~~~~~~~~~~~~~~~~~

    Entry point for starting a WSGI app server in a subprocess.
    Used by tests/fixtures.py _running_server context manager.

    This file is part of MSS.

    :copyright: Copyright 2023-2026 by the MSS team, see AUTHORS.
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
import importlib
import sys
from werkzeug.serving import make_server


def main():
    app_module, app_attr, host = sys.argv[1], sys.argv[2], sys.argv[3]
    # Any remaining arguments are extra paths to prepend to sys.path,
    # allowing the subprocess to find settings modules (e.g. mscolab_settings).
    for extra_path in sys.argv[4:]:
        if extra_path not in sys.path:
            sys.path.insert(0, extra_path)
    module = importlib.import_module(app_module)
    app = getattr(module, app_attr)
    srv = make_server(host, 0, app, threaded=True)
    port = srv.server_address[1]
    # Signal the chosen port to the parent process via stdout
    print(port, flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
