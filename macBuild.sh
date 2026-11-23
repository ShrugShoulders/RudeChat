#!/bin/sh

python3 -c 'import sys; sys.exit(sys.version_info < (3, 13))' || { echo "RudeChat needs Python 3.13 or newer." >&2; exit 1; }

python3 setup.py py2app
zip -yr dist/RudeChat.app.zip dist/RudeChat.app
