from setuptools import setup, find_packages

setup(
    name="RudeChat",
    version="3.0.4",
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
)
