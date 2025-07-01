from setuptools import setup, find_namespace_packages
import glob
import platform

PKGS = [
    'rudechat4',
    'rudechat4.Client',
    'rudechat4.Components',
    'rudechat4.GUI',
    'rudechat4.Util',
    'rudechat4.Cython'
]
cython_so_files = glob.glob('src/rudechat4/Cython/*.so')

VERSION = '4.1.2'
APP = ['src/rudechat4/__main__.py']
OPTIONS = {
    'iconfile': 'src/rudechat4/Resources/Icons/rude.icns', 
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

def isMac():
    return platform.system() == 'Darwin'

setup(
    packages = find_namespace_packages(where='src'),
    package_dir={"": "src"},
    include_package_data=True,
    scripts=["src/rudechat4/__main__.py"],
    install_requires=[
        'pytz',
        'asyncio',
        'irctokens',
        'aiofiles',
        'tzlocal',
        'pillow',
        'emoji',
        'PyQt6',
        'requests',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'rudechat=rudechat4.__main__:main',
        ],
    },
    app = ['src/rudechat4/__main__.py'] if isMac() else [],
    data_files = [('rudechat4/Cython', cython_so_files),],
    options = {'py2app': OPTIONS} if isMac() else {},
    setup_requires = ['py2app'] if isMac() else []
)