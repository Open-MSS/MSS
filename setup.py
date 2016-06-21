# The README.txt file should be written in reST so that PyPI can use
# it to generate your project's PyPI page. 
long_description = open('README').read()
from setuptools import setup, find_packages


setup(
    name="mss",
    version="1.1b1",
    description="mss gui",
    long_description=long_description,
    classifiers="Development Status :: 5 - Production/Stable",
    keywords="mslib",
    maintainer="Marc Rautenhaus",
    maintainer_email="marc.rautenhaus@tum.de",
    author="Marc Rautenahaus",
    author_email="marc.rautenhaus@tum.de",
    license="Apache 2.0",
    url="https://bitbucket.org/wxmetvis/mss",
    platforms="any",
    packages=find_packages(),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[], # we use conda build recipe
    entry_points=dict(
        console_scripts=[
                         'mss = mslib.msui.mss_pyui:main',
                         ],
    ),
)

