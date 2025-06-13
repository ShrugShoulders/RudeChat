from setuptools import setup, find_packages
import platform

if platform.system() == "Darwin":
    VERSION = '4.1.1'

    APP = ['src/rudechat4/__main__.py']
    DATA_FILES = []
    OPTIONS = {
        'iconfile': 'src/rudechat4/rude.icns', 
        'excludes': ['rubicon', 'setuptools'],
        'plist': {
            'CFBundleName': 'RudeChat',
            'CFBundleDisplayName': 'RudeChat',
            'CFBundleGetInfoString': 'RudeChat',
            'CFBundleIdentifier': 'io.github.ShrugShoulders.rudechat',
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'CFBundleIconFile': 'rude.icns',
        }
    }

    setup(
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        scripts=["src/rudechat4/__main__.py"],
        install_requires=[
            'pytz',
            'asyncio',
            'irctokens',
            'plyer',
            'aiofiles',
            'colorchooser',
            'tzlocal',
            'tkcolorpicker',
            'pillow',
            'pystray',
            'emoji',
            'PyQt6',
            'requests',
        ],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: OS Independent",
        ],
        package_data={
            "rudechat4": [
                "Art/*",
                "Sounds/*",
                "Fortune Lists/*",
                "Splash/*",
                "*.rudeserver",
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
                'rudechat=rudechat4.__main__:main',
            ],
        },
        # MacOS specific (Build using `python3 setup.py py2app` in root directory)
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app']
    )

else:
    setup(
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        scripts=["src/rudechat4/__main__.py"],
        install_requires=[
            'pytz',
            'asyncio',
            'irctokens',
            'plyer',
            'aiofiles',
            'colorchooser',
            'tzlocal',
            'tkcolorpicker',
            'pillow',
            'pystray',
            'emoji',
            'PyQt6',
            'requests',
        ],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Operating System :: OS Independent",
        ],
     
        package_data={
            "rudechat4": [
                "Art/*",
                "Sounds/*",
                "Fortune Lists/*",
                "Splash/*",
                "*.rudeserver",
                "*.ini",
                "nickname_colours.json",
                "rude.ico",
                "rude.icns",
                "*.png",
                "ignore_list.txt",
                "filtered_channels.txt",
                "first_run.txt",
            ],
        },
     
        entry_points={
            'console_scripts': [
                'rudechat=rudechat4.__main__:main',
            ],
        },
    )