#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time

class FeedbackWatcher(threading.Thread):
    
    ended = False
    enigma2_indicator = None
    enigma_client = None
    mpris_server = None
    current_service = None

    def __init__(self, enigma2_indicator, enigma_client, mpris_server):
        threading.Thread.__init__(self)
        self.enigma2_indicator = enigma2_indicator
        self.enigma_client = enigma_client
        self.mpris_server = mpris_server

    def kill(self):
        self.ended = True

    def run(self):
        while not self.ended:
            self.current_service = self.enigma_client.get_current_service_stream()
            self.enigma_client.update_label(self.current_service)
            self.mpris_server.update()
            time.sleep(10.0)

