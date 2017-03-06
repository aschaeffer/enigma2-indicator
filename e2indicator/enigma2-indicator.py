#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from symbol import except_clause

__author__ = "andreasschaeffer"

import socket
import time
import signal
import gi
import os
import threading
import logging
import traceback
import time
import webbrowser
import json
import xml
import requests
import dbus
import dbus.service
import copy
from xml.etree import ElementTree
from urllib.parse import quote
try:
    from streamscrobbler import streamscrobbler
except:
    pass

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject

logging.basicConfig(level = logging.DEBUG, format = "%(asctime)-15s [%(name)-5s] [%(levelname)-5s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
