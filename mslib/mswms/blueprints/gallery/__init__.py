# -*- coding: utf-8 -*-
"""

    mslib.mswms.blueprints.gallery
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Gallery Blueprint for app module of mswms

    This file is part of MSS.

    :copyright: Copyright 2016-2026 by the MSS team, see AUTHORS.
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

import os

import werkzeug
from flask import Blueprint, render_template, request, abort, Response

from mslib.mswms.gallery_builder import STATIC_LOCATION
from mslib.utils.get_content import get_content

GALLERY_BP = Blueprint('gallery', __name__, template_folder='templates', static_url_path='/gallery-static',
                       static_folder=STATIC_LOCATION)


@GALLERY_BP.route("/mss/plots")
def plots():
    if STATIC_LOCATION != "" and os.path.exists(os.path.join(STATIC_LOCATION, 'plots.html')):
        _file = os.path.join(STATIC_LOCATION, 'plots.html')
        content = get_content(_file)
    else:
        content = "Gallery was not generated for this server.<br>" \
                  "For further info on how to generate it, run the " \
                  "<b>gallery --help</b> command line parameter of mswms.<br>" \
                  "An example of the gallery can be seen " \
                  "<a href=\"https://mss.readthedocs.io/en/stable/gallery/index.html\">here</a>"
    return render_template("gallery/content.html", act="plots", content=content)


@GALLERY_BP.route("/mss/code/<path:filename>")
def code(filename):
    if STATIC_LOCATION != "":
        download = request.args.get("download", False)
        _file = werkzeug.security.safe_join(STATIC_LOCATION, "code", filename)
        if _file is None:
            abort(404)
        content = get_content(_file)
        if not download:
            return render_template("gallery/content.html", act="code", content=content)
        else:
            if not os.path.isfile(_file):
                abort(404)
            with open(_file) as f:
                text = f.read()
            return Response("".join([s.replace("\t", "", 1) for s in text.split("```python")[-1]
                                    .splitlines(keepends=True)][1:-2]),
                            mimetype="text/plain",
                            headers={"Content-disposition": f"attachment; filename={filename.split('-')[0]}.py"})
    else:
        abort(404)
