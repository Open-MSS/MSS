# -*- coding: utf-8 -*-
"""

    mslib.setup
    ~~~~~~~~~~~~~~~~

    setuptools script

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2020 by the mss team, see AUTHORS.
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
from past.builtins import execfile
from setuptools import setup, find_packages
long_description = open('README.md').read()
execfile('mslib/version.py')

setup(
    name="mss",
    version=__version__,  # noqa
    description="MSS - Mission Support System",
    long_description=long_description,
    classifiers="Development Status :: 5 - Production/Stable",
    keywords="mslib",
    maintainer="Reimar Bauer",
    maintainer_email="rb.proj@gmail.com",
    author="Marc Rautenahaus",
    author_email="wxmetvis@posteo.de",
    license="Apache-2.0",
    url="https://github.com/Open-MSS/MSS",
    platforms="any",
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],  # we use conda build recipe
    entry_points=dict(
        console_scripts=['mss = mslib.msui.mss_pyui:main'],
    ),
)
