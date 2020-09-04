# -*- coding: utf-8 -*-
"""

    mslib.index
    ~~~~~~~~~~~~

    shows some docs on the root url of the server

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
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
import codecs

from flask import render_template
from flask import Flask
from flask import send_from_directory, send_file
from flask import abort
from docutils.core import publish_parts
from xstatic.main import XStatic
from mslib.msui.icons import icons

# set the project root directory as the static folder
DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(__file__))

APP = Flask(__name__)


def _xstatic(name):
    mod_names = [
        'jquery', 'bootstrap',
    ]
    pkg = __import__('xstatic.pkg', fromlist=mod_names)
    serve_files = {}

    for mod_name in mod_names:
        mod = getattr(pkg, mod_name)
        xs = XStatic(mod, root_url='/static', provider='local', protocol='http')
        serve_files[xs.name] = xs.base_dir
    try:
        return serve_files[name]
    except KeyError:
        return None


@APP.route('/xstatic/<name>/', defaults=dict(filename=''))
@APP.route('/xstatic/<name>/<path:filename>')
def files(name, filename):

    base_path = _xstatic(name)
    if base_path is None:
        abort(404)
    if not filename:
        abort(404)
    return send_from_directory(base_path, filename)


def get_topmenu():
    menu = [
        ('/mss', 'Mission Support System',
         (('/mss/about', 'About'),
          ('/mss/install', 'Install'),
          ('/mss/help', 'Help'),
          )),
    ]
    return menu


APP.jinja_env.globals.update(get_topmenu=get_topmenu)


def get_content(filename, overrides=None):
    content = ""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            rst_data = f.read()
        img_location = 'https://mss.readthedocs.io/en/stable/_images/wise12_overview.png'
        rst_data = rst_data.replace('mss_theme/img/wise12_overview.png', img_location)

        content = publish_parts(rst_data, writer_name='html', settings_overrides=overrides)['html_body']
    return content


@APP.route("/index")
def index():
    return render_template("/index.html")


@APP.route("/mss/about")
@APP.route("/mss")
def about():
    _file = os.path.join(DOCS_SERVER_PATH, '..', 'docs', 'about.rst')
    content = get_content(_file)
    return render_template("/content.html", act="about", content=content)


@APP.route("/mss/install")
def install():
    _file = os.path.join(DOCS_SERVER_PATH, '..', 'docs', 'installation.rst')
    content = get_content(_file)
    return render_template("/content.html", act="install", content=content)


@APP.route("/mss/help")
def help():
    _file = os.path.join(DOCS_SERVER_PATH, '..', 'docs', 'help.rst')
    content = get_content(_file)
    return render_template("/content.html", act="help", content=content)


@APP.route('/mss/favicon.ico')
def favions():
    base_path = icons("16x16", "favicon.ico")
    return send_file(base_path)


@APP.route('/mss/logo.png')
def logo():
    base_path = icons("64x64", "mss-logo.png")
    return send_file(base_path)
