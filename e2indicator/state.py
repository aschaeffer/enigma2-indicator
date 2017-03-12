#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import toml
import os
from appdirs import *

class Enigma2State():

    model = ""
    current_service = None
    current_service_event = None
    services = []
    bouquets = {
        "tv": [],
        "radio": []
    }
    history = []
    audiotracks = []

    logger = logging.getLogger("e2-state")

    def __init__(self):
        pass

    def reset_bouquets(self):
        self.bouquets = {
            "tv": [],
            "radio": []
        }

    def load_bouquets(self, widget = None, value = None):
        try:
            path = os.path.join(user_config_dir("e2indicator"), "bouquets.toml")
            with open(path, "r") as f:
                self.bouquets = toml.load(f)
            return True
        except:
            self.logger.exception("Couldn't load bouquets")
            return False

    def save_bouquets(self, widget = None, value = None):
        path = os.path.join(user_config_dir("e2indicator"), "bouquets.toml")
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            toml.dump(self.bouquets, f)
