# -*- coding: utf-8 -*-
"""

    mslib.index
    ~~~~~~~~~~~~

    shows some docs on the root url of the server

    This file is part of mss.

    :copyright: Copyright 2020 Reimar Bauer
    :copyright: Copyright 2020-2021 by the mss team, see AUTHORS.
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
import mslib

from flask import render_template
from flask import Flask
from flask import send_from_directory, send_file, url_for
from flask import abort
from markdown import Markdown
from xstatic.main import XStatic
from mslib.msui.icons import icons

# set the project root directory as the static folder
DOCS_SERVER_PATH = os.path.dirname(os.path.abspath(mslib.__file__))
# This can be used to set a location by SCRIPT_NAME for testing. e.g. export SCRIPT_NAME=/demo/
SCRIPT_NAME = os.environ.get('SCRIPT_NAME', '/')


def _xstatic(name):
    mod_names = [
        'jquery', 'bootstrap',
    ]
    pkg = __import__('xstatic.pkg', fromlist=mod_names)
    serve_files = {}

    for mod_name in mod_names:
        mod = getattr(pkg, mod_name)
        # ToDo protocol should become configurable
        xs = XStatic(mod, root_url='/static', provider='local', protocol='http')
        serve_files[xs.name] = xs.base_dir
    try:
        return serve_files[name]
    except KeyError:
        return None


def prefix_route(route_function, prefix='', mask='{0}{1}'):
    '''
    https://stackoverflow.com/questions/18967441/add-a-prefix-to-all-flask-routes/18969161#18969161
    Defines a new route function with a prefix.
    The mask argument is a `format string` formatted with, in that order:
      prefix, route
    '''
    def newroute(route, *args, **kwargs):
        ''' prefix route '''
        return route_function(mask.format(prefix, route), *args, **kwargs)
    return newroute


def app_loader(name):
    APP = Flask(name, template_folder=os.path.join(DOCS_SERVER_PATH, 'static', 'templates'))
    APP.config.from_object(name)
    APP.route = prefix_route(APP.route, SCRIPT_NAME)

    @APP.route('/xstatic/<name>/', defaults=dict(filename=''))
    @APP.route('/xstatic/<name>/<path:filename>')
    def files(name, filename):

        base_path = _xstatic(name)
        if base_path is None:
            abort(404)
        if not filename:
            abort(404)
        return send_from_directory(base_path, filename)

    @APP.route('/mss_theme/<name>/', defaults=dict(filename=''))
    @APP.route('/mss_theme/<name>/<path:filename>')
    def mss_theme(name, filename):
        if name != 'img':
            abort(404)
        base_path = os.path.join(DOCS_SERVER_PATH, 'static', 'img')
        return send_from_directory(base_path, filename)

    def get_topmenu():
        menu = [
            (url_for('index'), 'Mission Support System',
             ((url_for('about'), 'About'),
              (url_for('install'), 'Install'),
              (url_for('help'), 'Help'),
              )),
        ]
        return menu

    APP.jinja_env.globals.update(get_topmenu=get_topmenu)

    def get_content(filename, overrides=None):
        markdown = Markdown()
        content = ""
        if os.path.isfile(filename):
            with codecs.open(filename, 'r', 'utf-8') as f:
                md_data = f.read()
            md_data = md_data.replace(':ref:', '')
            if overrides is not None:
                v1, v2 = overrides
                md_data = md_data.replace(v1, v2)
            content = markdown.convert(md_data)
        return content

    @APP.route("/index")
    def index():
        return render_template("/index.html")

    @APP.route("/mss/about")
    @APP.route("/mss")
    def about():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'about.md')
        img_url = url_for('overview')
        overrides = ['![image](/mss/overview.png)', f'![image]({img_url})']
        content = get_content(_file,
                              overrides=overrides)
        return render_template("/content.html", act="about", content=content)

    @APP.route("/mss/install")
    def install():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'installation.md')
        content = get_content(_file)
        return render_template("/content.html", act="install", content=content)

    @APP.route("/mss/help")
    def help():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'help.md')
        content = get_content(_file)
        return render_template("/content.html", act="help", content=content)

    @APP.route("/mss/imprint")
    def imprint():
        _file = os.path.join(DOCS_SERVER_PATH, 'static', 'docs', 'imprint.md')
        content = get_content(_file)
        return render_template("/content.html", act="imprint", content=content)

    @APP.route('/mss/favicon.ico')
    def favicons():
        base_path = icons("16x16", "favicon.ico")
        return send_file(base_path)

    @APP.route('/mss/logo.png')
    def logo():
        base_path = icons("64x64", "mss-logo.png")
        return send_file(base_path)

    @APP.route('/mss/overview.png')
    def overview():
        base_path = os.path.join(DOCS_SERVER_PATH, 'static', 'img', 'wise12_overview.png')
        return send_file(base_path)

    return APP
