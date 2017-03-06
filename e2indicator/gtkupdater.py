#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
import threading
import time

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk as gtk

class GtkUpdater(threading.Thread):
    
    ended = False

    def __init__(self):
        threading.Thread.__init__(self)

    def kill(self):
        self.ended = True
    
    def run(self):
        while not self.ended:
            gtk.main_iteration_do(False)
            time.sleep(0.2)
