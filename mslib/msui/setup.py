import setuptools 

setuptools.setup( 
    name='mss', 
    version='1.0', 
    author='Chris Doucette', 
    author_email='chris@ediblesec.com', 
    description='Hides a message with a Caesar cipher', 
    packages=setuptools.find_packages(), 
    entry_points={ 
        'console_scripts': [ 
            'mss = mss_pyui.mss_pyui:main' 
        ] 
    }, 
    classifiers=[ 
        'Programming Language :: Python :: 3', 
        'License :: OSI Approved :: MIT License', 
        'Operating System :: OS Independent', 
    ], 
)