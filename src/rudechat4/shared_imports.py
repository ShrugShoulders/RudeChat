#!/usr/bin/env python3

import aiofiles
import asyncio
import base64
import configparser
import dataclasses
from datetime import datetime, timedelta
import fnmatch
import glob
import irctokens
import json
import logging
import os
import platform
import pytz
import random
import re
import regex
import requests
import shutil
import ssl
import subprocess
import sys
import threading
import textwrap
import time
from typing import List, Tuple, Dict, Any, Optional
from tzlocal import get_localzone
import webbrowser

from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractItemView,
    QListView,
    QApplication,
    QCheckBox,
    QColorDialog,
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
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QScrollBar,
    QSystemTrayIcon
)

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QObject,
    QPoint,
    QTimer,
    QCoreApplication,
    QMetaObject,
    QRect,
    QRunnable,
    pyqtSignal,
    QThreadPool,
    pyqtSlot
)

from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QFontMetrics,
    QGuiApplication,
    QTextCharFormat,
    QTextCursor,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPixmap,
    QPalette, 
    QShortcut, 
    QKeySequence
)

if platform.system() == "Darwin":
    from objc import lookUpClass
