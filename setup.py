from setuptools import setup, find_namespace_packages, Extension
from Cython.Build import cythonize
import glob
import platform

VERSION = '4.1.2'

def isMac():
    return platform.system() == 'Darwin'

# Build the Cython extension
ext_modules = cythonize([
    Extension(
        "rudechat4.Cython.decoder_cython",
        sources=["src/rudechat4/Cython/decoder_cython.pyx"],
    )
])

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

setup(
    name='RudeChat',
    version=VERSION,
    packages=find_namespace_packages(where='src'),
    package_dir={"": "src"},
    include_package_data=True,
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
    package_data={
        "rudechat4": ["Cython/*"],  # include .pyx and other static files
    },
    entry_points={
        'console_scripts': [
            'rudechat=rudechat4.__main__:main',
        ],
    },
    app=APP if isMac() else [],
    data_files=[],
    ext_modules=ext_modules,
    options={'py2app': OPTIONS} if isMac() else {},
    setup_requires=['py2app'] if isMac() else [],
)
