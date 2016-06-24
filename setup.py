# The README.txt file should be written in reST so that PyPI can use
# it to generate your project's PyPI page.
from setuptools import setup, find_packages
long_description = open('README').read()
execfile('mslib/version.py')

setup(
    name="mss",
    version=__version__,
    description="MSS - Mission Support System",
    long_description=long_description,
    classifiers="Development Status :: 5 - Production/Stable",
    keywords="mslib",
    maintainer="Marc Rautenhaus",
    maintainer_email="wxmetvis@posteo.de",
    author="Marc Rautenahaus",
    author_email="wxmetvis@posteo.de",
    license="Apache 2.0",
    url="https://bitbucket.org/wxmetvis/mss",
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
