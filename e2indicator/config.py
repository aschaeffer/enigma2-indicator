#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import toml
import os
from appdirs import *

class Enigma2Config(dict):

    logger = logging.getLogger("e2-config")

    def __init__(self, *args, **kwargs):
        self.load()

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.save()

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def load(self):
        try:
            path = os.path.join(user_config_dir("e2indicator"), "config.toml")
            with open(path, "r") as f:
                config = toml.load(f)
                self.logger.info(str(config))
                for key, value in config.items():
                    self[key] = value
        except:
            self.logger.exception("Couldn't load config")
            self["hostname"] = "daskaengurutv"
            self["showStationIcon"] = True
            self["showStationName"] = True
            self["showCurrentShowTitle"] = True
            self["updateDelay"] = 5.0

    def save(self):
        path = os.path.join(user_config_dir("e2indicator"), "config.toml")
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            toml.dump(self, f)
            
