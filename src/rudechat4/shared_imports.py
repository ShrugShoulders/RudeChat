import aiofiles
import asyncio
import base64
import configparser
import dataclasses
from datetime import datetime, timedelta
import emoji
import fnmatch
import glob
import irctokens
import json
import logging
import os
import platform
from plyer import notification as plyer_notification
import pytz
import random
import re
import requests
import shutil
import ssl
import subprocess
import sys
import threading
import textwrap
import time
from typing import List, Tuple
from tzlocal import get_localzone
import webbrowser

from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QScrollBar
)

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QObject,
    QPoint,
    QTimer,
)

from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QTextCharFormat,
    QTextCursor
)

if platform.system() == "Darwin":
    from objc import lookUpClass

# Soon to be Obsolete
import tkinter as tk
from tkinter import (
    Tk,
    ttk,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    messagebox,
    PhotoImage,
    Scrollbar,
    scrolledtext,
    simpledialog,
    StringVar
)