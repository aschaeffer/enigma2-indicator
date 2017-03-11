#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import threading
import time

class Enigma2FeedbackWatcher(threading.Thread):
    
    ended = False
    enigma_client = None

    logger = logging.getLogger("e2-feedback")

    def __init__(self, enigma_config, enigma_client):
        threading.Thread.__init__(self)
        self.enigma_config = enigma_config
        self.enigma_client = enigma_client

    def kill(self):
        self.ended = True

    def run(self):
        while not self.ended:
            self.enigma_client.update()
            time.sleep(self.enigma_config["updateDelay"])

