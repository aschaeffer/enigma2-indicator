#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

class Enigma2State():

    model = ""
    current_service = None
    current_service_event = None
    services = []
    bouquets = {
        "tv": [],
        "radio": []
    }

    logger = logging.getLogger("e2-state")

    def __init__(self):
        pass

