from setuptools import setup, find_packages

APP = ['src/rudechat3/main.py']
DATA_FILES = []
OPTIONS = {'iconfile': '/Users/bash/Developer/RudeChat/src/rudechat3/rude.icns', 'excludes': ['rubicon']}

setup(
    name="RudeChat",
    version="3.1.4",
    description="RudeChat is a Python IRC client designed to be fast, portable, and fun.",
    author="Irish",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    scripts=["src/rudechat3/main.py"],
    install_requires=[
        'pytz',
        'asyncio',
        'irctokens',
        'plyer',
        'aiofiles',
        'colorchooser',
        'tzlocal',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_data={
        "rudechat3": [
            "Art/*",
            "Sounds/*",
            "Fortune Lists/*",
            "Splash/*",
            "*.rude",
            "*.ini",
            "nickname_colours.json",
            "rude.ico",
            "rude.png",
            "rude_tray_icon.png",
            "ignore_list.txt",
            "filtered_channels.txt",
            "first_run.txt",
        ],
    },
    entry_points={
        'console_scripts': [
            'rudechat=rudechat3.main:main',
        ],
    },
    # MacOS specific (Build using `python3 setup.py py2app` in root directory)
    app=APP,
	data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)