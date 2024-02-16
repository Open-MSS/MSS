# -*- coding: utf-8 -*-
"""

    mslib.utils.get_content
    ~~~~~~~~~~~~~~~~~~~~~~~

    Returns the content of a markdown file as html

    This file is part of MSS.

    :copyright: Copyright 2008-2014 Deutsches Zentrum fuer Luft- und Raumfahrt e.V.
    :copyright: Copyright 2011-2014 Marc Rautenhaus (mr)
    :copyright: Copyright 2016-2023 by the MSS team, see AUTHORS.
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

import codecs
import os

from markdown import Markdown


def get_content(filename, md_overrides=None, html_overrides=None):
    markdown = Markdown(extensions=["fenced_code"])
    content = ""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            md_data = f.read()
        md_data = md_data.replace(':ref:', '')
        if md_overrides is not None:
            v1, v2 = md_overrides
            md_data = md_data.replace(v1, v2)
        content = markdown.convert(md_data)
        if html_overrides is not None:
            v1, v2 = html_overrides
            content = content.replace(v1, v2)
    return content
