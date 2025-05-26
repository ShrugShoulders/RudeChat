#!/bin/sh

python3 setup.py py2app
zip -yr dist/RudeChat.app.zip dist/RudeChat.app
