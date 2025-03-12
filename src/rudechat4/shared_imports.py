#!/usr/bin/env python
import asyncio
import aiofiles
import base64
import glob
import ssl
import configparser
import datetime
import fnmatch
import irctokens
import time
import textwrap
import random
import datetime
import logging
import os
import platform
import subprocess
import re
import sys
import json
import tkinter as tk
import tkinter.font as tkFont
import dataclasses
import multiprocessing
import concurrent.futures
import shutil
import webbrowser
import pytz
import threading
import emoji
from PIL import Image
from tzlocal import get_localzone
from typing import List, Tuple, NamedTuple
from plyer import notification as plyer_notification
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import Tk, Frame, Label, Entry, Listbox, Menu, Scrollbar, StringVar, PhotoImage, messagebox
from tkinter import simpledialog
from threading import Thread

from PySide6.QtWidgets import QApplication, QMessageBox, QVBoxLayout, QWidget, QLabel, QPushButton, QComboBox, QCheckBox, QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QFrame, QGroupBox, QGridLayout, QMainWindow, QTextEdit, QHBoxLayout, QListWidget, QListView, QAbstractItemView, QListWidgetItem
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QTextFormat

if platform.system() == "Darwin":
    from objc import lookUpClass