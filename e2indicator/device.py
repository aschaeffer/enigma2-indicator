#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import socket
import threading
from xml.etree import ElementTree

class ScanPort(threading.Thread):

    ip = None
    result = -1
    enigma2 = False
    model = ""

    logger = logging.getLogger("e2-scan")

    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        try:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.settimeout(3)
            self.result = _socket.connect_ex((self.ip, 80))
            _socket.close()
            if self.result == 0:
                response = requests.get("http://%s/web/about" %(self.ip))
                if response.status_code == 200:
                    tree = ElementTree.fromstring(response.content)
                    for child in tree[0]:
                        if child.tag == "e2model":
                            self.enigma2 = True
                            self.model = child.text
        except:
            self.enigma2 = False

class Enigma2DeviceService():

    enigma_config = None

    initialized = False
    my_ip = None
    my_network = None

    ip = None
    model = ""

    logger = logging.getLogger("e2-device")

    def __init__(self, enigma_config):
        self.enigma_config = enigma_config
        self.my_ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        self.my_network = self.my_ip.rsplit(".", 1)[0]
        self.logger.info("Network: %s IP: %s" %(self.my_network, self.my_ip))
        if not self.is_enigma(self.enigma_config["hostname"]):
            if self.find_device():
                self.enigma_config["hostname"] = self.ip
                self.enigma_config["model"] = self.model

    def find_device(self):
        self.logger.info("Searching for enigma2 devices in %s.*" %(self.my_network))
        threads = []
        for last_octet in range(1, 254):
            device_ip = "%s.%s" %(self.my_network, last_octet)
            thread = ScanPort(device_ip)
            thread.start()
            threads.append(thread)

        for last_octet in range(1, 254):
            thread = threads[last_octet - 1]
            thread.join()
            if thread.enigma2:
                self.ip = thread.ip
                self.model = thread.model
                self.logger.info("Detected %s device on %s:%d" %(self.model, self.ip, 80))

        if self.ip == None:
            self.logger.error("No device found in the local network!")
            return False
        else:
            return True

    def is_enigma(self, hostname):
        try:
            response = requests.get("http://%s/web/about" %(hostname))
            if response.status_code == 200:
                tree = ElementTree.fromstring(response.content)
                for child in tree[0]:
                    if child.tag == "e2model":
                        return True
            return False
        except:
            return False
