# -*- coding: utf-8 -*-
"""

    mslib.setup
    ~~~~~~~~~~~

    setuptools script

    This file is part of MSS.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2024 by the MSS team, see AUTHORS.
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

# The README.txt file should be written in reST so that PyPI can use
# it to generate your project's PyPI page.
import os
from past.builtins import execfile
from setuptools import setup, find_namespace_packages
long_description = open('README.md').read()
execfile('mslib/version.py')

console_scripts = [
    "mscolab = mslib.mscolab.mscolab:main",
    "mss = mslib.msui.mss:main",
    "mssautoplot = mslib.utils.mssautoplot:main",
    "msui = mslib.msui.msui:main",
    "mswms = mslib.mswms.mswms:main",
    "mswms_demodata = mslib.mswms.demodata:main"]
if os.name != 'nt':
    console_scripts.append('msidp = mslib.msidp.idp:main')

setup(
    name="open-mss",
    version=__version__,  # noqa
    description="MSS - Mission Support System",
    long_description=long_description,
    classifiers="Development Status :: 5 - Production/Stable",
    keywords="mslib",
    maintainer="Reimar Bauer",
    maintainer_email="rb.proj@gmail.com",
    author="Marc Rautenhaus",
    author_email="wxmetvis@posteo.de",
    license="Apache-2.0",
    url="https://github.com/Open-MSS/MSS",
    platforms="any",
    packages=find_namespace_packages(include=["mslib", "mslib.*"]),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],  # we use pixi
    entry_points=dict(
        console_scripts=console_scripts,
    ),
)
