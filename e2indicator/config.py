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
            if "hostname" not in self:
                self["hostname"] = "localhost"
            if "model" not in self:
                self["model"] = ""
            if "showStationIcon" not in self:
                self["showStationIcon"] = True
            if "showStationName" not in self:
                self["showStationName"] = True
            if "showCurrentShowTitle" not in self:
                self["showCurrentShowTitle"] = True
            if "currentShowTitleFallback" not in self:
                self["currentShowTitleFallback"] = True
            if "updateDelay" not in self:
                self["updateDelay"] = 5.0
            if "showHistory" not in self:
                self["showHistory"] = True
            if "maxHistoryEntries" not in self:
                self["maxHistoryEntries"] = 5
            if "showExtras" not in self:
                self["showExtras"] = False
        except:
            self.logger.exception("Couldn't load config, using defaults")
            self["hostname"] = "localhost"
            self["model"] = ""
            self["showStationIcon"] = True
            self["showStationName"] = True
            self["showCurrentShowTitle"] = True
            self["currentShowTitleFallback"] = True
            self["updateDelay"] = 5.0
            self["showHistory"] = True
            self["maxHistoryEntries"] = 5
            self["showExtras"] = True

    def save(self):
        path = os.path.join(user_config_dir("e2indicator"), "config.toml")
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            toml.dump(self, f)
            
