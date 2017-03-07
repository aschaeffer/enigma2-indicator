#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import requests
import time
import webbrowser
from xml.etree import ElementTree
from urllib.parse import quote
try:
    from e2indicator.streamscrobbler import streamscrobbler
except:
    pass

class Enigma2Client():

    model = ""
    service_name = ""
    current_service = None
    services = []
    enigma2_indicator = None
    streamscrobbler = None
    bouquets = {}

    logger = logging.getLogger("e2indicator-client")

    def __init__(self, enigma2_indicator):
        self.bouquets["tv"] = []
        self.bouquets["radio"] = []
        self.enigma2_indicator = enigma2_indicator
        try:
            self.streamscrobbler = streamscrobbler()
        except:
            pass

    def update_bouquets(self):
        self.get_bouquets_tv()
        self.get_bouquets_radio()
        
    def get_model(self):
        response = requests.get("http://%s/web/about" %(self.enigma2_indicator.config["hostname"]))
        tree = ElementTree.fromstring(response.content)
        for child in tree[0]:
            if child.tag == "e2model":
                self.model = child.text
        return self.model

    def get_current_service_stream(self):
        self.current_service = self.get_empty_service()
        try:
            response = requests.get("http://%s/web/streamsubservices" %(self.enigma2_indicator.config["hostname"]))
            tree = ElementTree.fromstring(response.content)
            for service_tag in tree:
                if service_tag.tag == "e2service":
                    for service_attr in service_tag:
                        if service_attr.tag == "e2servicereference":
                            self.current_service["reference"] = service_attr.text
                            if service_attr.text.split(":")[0] == "4097":
                                self.current_service["type"] = "stream"
                                self.current_service["streamurl"] = service_attr.text.split(":")[10].replace("%3a", ":")
                                if service_attr.text.split(":")[2] == "0":
                                    self.current_service["streamtype"] = "tv"
                                elif service_attr.text.split(":")[2] == "2":
                                    self.current_service["streamtype"] = "radio"
                                else:
                                    self.current_service["streamtype"] = "stream"
                                self.logger.info("Stream Type: %s Stream URL: %s" %(self.current_service["streamtype"], self.current_service["streamurl"]))
                            else:
                                self.current_service["type"] = "normal"
                        if service_attr.tag == "e2servicename":
                            self.current_service["name"] = service_attr.text
        except:
            self.logger.error("Failed to get current service or stream")
        return self.current_service

    def get_empty_service(self):
        return {
            "reference": "0:0:0:0:0:0:0:0:0:0::",
            "name": "N/A",
            "type": "normal"
        }

    def get_bouquets_tv(self):
        response = requests.get("http://%s/web/getservices" %(self.enigma2_indicator.config["hostname"]))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                type = None
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                        if ".radio" in service["reference"]:
                            type = "radio"
                        if ".tv" in service["reference"]:
                            type = "tv"
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                if type == "tv":
                    self.bouquets["tv"].append(service)

    def get_bouquets_radio(self):
        response = requests.get("http://%s/web/getservices?sRef=1:7:2:0:0:0:0:0:0:0:type == 2 FROM BOUQUET \"bouquets.radio\"" %(self.enigma2_indicator.config["hostname"]))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                type = None
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                        if ".radio" in service["reference"]:
                            type = "radio"
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                if type == "radio":
                    self.bouquets["radio"].append(service)

    def get_services(self, bouquet):
        self.services = []
        response = requests.get("http://%s/web/getservices?sRef=1:7:1:0:0:0:0:0:0:0:FROM%%20BOUQUET%%20%%22%s%%22%%20ORDER%%20BY%%20bouquet" %(self.enigma2_indicator.config["hostname"], bouquet))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                self.services.append(service)
        return self.services

    def get_services_2(self, service):
        self.services = []
        response = requests.get("http://%s/web/getservices?sRef=%s" %(self.enigma2_indicator.config["hostname"], quote(service["reference"])))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                self.services.append(service)
        return self.services

    def get_epg(self, service):
        try:
            if "type" in service and service["type"] == "stream":
                service_event = self.get_empty_service_event_stream(service)
                if service["streamtype"] == "radio":
                    try:
                        stationinfo = self.streamscrobbler.getServerInfo(service["streamurl"])
                        metadata = stationinfo.get("metadata")
                        service_event["title"] = metadata["song"]
                    except:
                        self.logger.exception("Failed to get current song from radio stream")
                service["events"] = []
                service["events"].append(service_event)
            else:
                try:
                    response = requests.get("http://%s/web/epgservice?sRef=%s" %(self.enigma2_indicator.config["hostname"], quote(service["reference"])))
                    tree = ElementTree.fromstring(response.content)
                    service["events"] = []
                    for e2event_tag in tree:
                        if e2event_tag.tag == "e2event":
                            service_event = self.get_empty_service_event(service)
                            for e2event_attr in e2event_tag:
                                if e2event_attr.tag == "e2eventid":
                                    service_event["id"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventservicereference":
                                    service_event["reference"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventservicename":
                                    service_event["service"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventtitle":
                                    service_event["title"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventdescription":
                                    service_event["description"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventdescriptionextended":
                                    service_event["descriptionextended"] = e2event_attr.text
                                if e2event_attr.tag == "e2eventstart":
                                    service_event["start"] = int(e2event_attr.text)
                                if e2event_attr.tag == "e2eventduration":
                                    service_event["duration"] = int(e2event_attr.text)
                                if e2event_attr.tag == "e2eventcurrenttime":
                                    service_event["currenttime"] = int(e2event_attr.text)
                                if e2event_attr.tag == "e2eventremaining":
                                    service_event["remaining"] = int(e2event_attr.text)
                            service["events"].append(service_event)
                except:
                    self.logger.error("Failed to get EPG: Connection refused")
                    return self.get_empty_service_event(service)
        except:
            self.logger.exception("Failed to get EPG")

    def get_empty_service_event(self, service):
        return {
            "id": 0,
            "reference": service["reference"],
            "service": service["name"],
            "title": " ",
            "description": " ",
            "descriptionextended": " ",
            "start": 0,
            "duration": 0,
            "currenttime": 0,
            "remaining": 0
        }

    def get_empty_service_event_stream(self, service):
        service_event = self.get_empty_service_event(service)
        service_event["start"] = int(time.time()) - 10
        service_event["duration"] = 60000
        service_event["currenttime"] = int(time.time()) + 1
        service_event["remaining"] = (service_event["start"] + service_event["duration"]) - service_event["currenttime"]
        return service_event

    def get_current_service_event(self, service):
        if "events" in service:
            for service_event in service["events"]:
                if service_event["start"] < service_event["currenttime"] and service_event["start"] + service_event["duration"] > service_event["currenttime"]:
                    return service_event
        return None

    def update_label(self, service):
        if service:
            if self.enigma2_indicator.config["showCurrentShowTitle"]:
                self.get_epg(service)
                current_service_event = self.get_current_service_event(service)
                if current_service_event != None:
                    if self.enigma2_indicator.config["showStationName"]:
                        self.enigma2_indicator.update_label("%s: %s" %(service["name"], current_service_event["title"]))
                    else:
                        self.enigma2_indicator.update_label("%s" %(current_service_event["title"]))
                elif self.enigma2_indicator.config["showStationName"]:
                    self.enigma2_indicator.update_label(service["name"])
            elif self.enigma2_indicator.config["showStationName"]:
                self.enigma2_indicator.update_label(service["name"])
            else:
                self.enigma2_indicator.update_label("")
            if self.enigma2_indicator.config["showStationIcon"]:
                self.enigma2_indicator.update_icon(service)
            elif self.enigma2_indicator.config["showStationName"] or self.enigma2_indicator.config["showCurrentShowTitle"]:
                # Showing the station name or current show title => No icon
                self.enigma2_indicator.remove_icon()
            else:
                # No text => Icon needed
                self.enigma2_indicator.update_icon(None)
        else:
            self.enigma2_indicator.update_label("")
            self.enigma2_indicator.update_icon(None)

    def stream(self, service):
        if service:
            if "type" in service and service["type"] == "stream":
                self.logger.info("Open stream %s" %(service["streamurl"]))
                webbrowser.open(service["streamurl"])
            elif "reference" in service:
                stream_url = "http://%s/web/stream.m3u?ref=%s" %(self.enigma2_indicator.config["hostname"], quote(service["reference"]))
                self.logger.info("Open stream %s" %(stream_url))
                webbrowser.open(stream_url)
            else:
                self.logger.error("Missing service reference or stream url!")
        else:
            self.logger.error("No service!")

    def select_channel(self, widget, service):
        try:
            response = requests.get("http://%s/web/zap?sRef=%s" %(self.enigma2_indicator.config["hostname"], quote(service["reference"])))
            self.current_service = service
            self.update_label(service)
        except:
            self.logger.error("Failed to select channel")

    def channel_up(self):
        try:
            response = requests.get("http://%s/web/remotecontrol?command=403" %(self.enigma2_indicator.config["hostname"]))
            self.update_label(self.get_current_service_stream())
        except:
            self.logger.error("Failed to select next channel")

    def channel_down(self):
        try:
            response = requests.get("http://%s/web/remotecontrol?command=402" %(self.enigma2_indicator.config["hostname"]))
            self.update_label(self.get_current_service_stream())
        except:
            self.logger.error("Failed to select previous channel")

    def set_power_state(self, state):
        try:
            response = requests.get("http://%s/web/powerstate?newstate=%d" %(self.enigma2_indicator.config["hostname"], state))
            self.update_label(self.get_current_service_stream())
        except:
            self.logger.error("Failed to set power state")

    def power_standby(self, widget = None):
        self.set_power_state(0)

    def power_deep_standby(self, widget = None):
        self.set_power_state(1)

    def power_reboot(self, widget = None):
        self.set_power_state(2)

    def power_restart_gui(self, widget = None):
        self.set_power_state(3)

    def power_wake_up(self, widget = None):
        self.set_power_state(116)

    def get_picon(self, service):
        try:
            filename = "%s.png" %(service["reference"][:-1].replace(":", "_"))
            url = "http://%s/picon/%s" %(self.enigma2_indicator.config["hostname"], filename)
            local_path = "/tmp/%s" %(filename)
            filename2 = "%s.png" %(service["name"].lower().replace(" ", ""))
            url2 = "http://%s/picon/%s" %(self.enigma2_indicator.config["hostname"], filename2)
            local_path2 = "/tmp/%s" %(filename2)
            if not os.path.exists(local_path):
                if not os.path.exists(local_path2):
                    try:
                        r = requests.get(url)
                        if r.status_code == 200:
                            f = open(local_path, "wb")
                            f.write(r.content)
                            f.close()
                            return local_path
                        else:
                            r = requests.get(url)
                            if r.status_code == 200:
                                f = open(local_path, "wb")
                                f.write(r.content)
                                f.close()
                                return local_path2
                            else:
                                return self.enigma2_indicator.get_icon_path(self.enigma2_indicator.get_icon())
                    except:
                        return self.enigma2_indicator.get_icon_path(self.enigma2_indicator.get_icon())
                else:
                    return local_path2
            else:
                return local_path
            return self.enigma2_indicator.get_icon_path(self.enigma2_indicator.get_icon())
        except Exception as e:
            self.logger.error("Failed to update icon")
            return self.enigma2_indicator.get_icon_path(self.enigma2_indicator.get_icon())

    def get_picon_url(self, service):
        return "file://%s" %(self.get_picon(service))
