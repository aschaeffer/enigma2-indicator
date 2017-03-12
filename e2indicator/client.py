#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import requests
import subprocess
import time
import webbrowser
from appdirs import *
from xml.etree import ElementTree
from urllib.parse import quote
try:
    from e2indicator.streamscrobbler import streamscrobbler
except:
    pass

class Enigma2Client():

    enigma_indicator = None
    enigma_state = None
    streamscrobbler = None

    logger = logging.getLogger("e2-client")

    def __init__(self, enigma_indicator, enigma_config, enigma_state):
        self.enigma_indicator = enigma_indicator
        self.enigma_config = enigma_config
        self.enigma_state = enigma_state
        try:
            self.streamscrobbler = streamscrobbler()
        except:
            pass

    def get_model(self):
        response = requests.get("http://%s/web/about" %(self.enigma_config["hostname"]))
        tree = ElementTree.fromstring(response.content)
        for child in tree[0]:
            if child.tag == "e2model":
                self.enigma_state.model = child.text
        return self.enigma_state.model

    def get_current_service_stream(self):
        self.enigma_state.current_service = self.get_empty_service()
        try:
            response = requests.get("http://%s/web/streamsubservices" %(self.enigma_config["hostname"]))
            tree = ElementTree.fromstring(response.content)
            for service_tag in tree:
                if service_tag.tag == "e2service":
                    for service_attr in service_tag:
                        if service_attr.tag == "e2servicereference":
                            self.enigma_state.current_service["reference"] = service_attr.text
                            if service_attr.text.split(":")[0] == "4097":
                                self.enigma_state.current_service["type"] = "stream"
                                self.enigma_state.current_service["streamurl"] = service_attr.text.split(":")[10].replace("%3a", ":")
                                if service_attr.text.split(":")[2] == "0":
                                    self.enigma_state.current_service["streamtype"] = "tv"
                                elif service_attr.text.split(":")[2] == "2":
                                    self.enigma_state.current_service["streamtype"] = "radio"
                                else:
                                    self.enigma_state.current_service["streamtype"] = "stream"
                                self.logger.info("Stream Type: %s Stream URL: %s" %(self.enigma_state.current_service["streamtype"], self.enigma_state.current_service["streamurl"]))
                            else:
                                self.enigma_state.current_service["type"] = "normal"
                        if service_attr.tag == "e2servicename":
                            self.enigma_state.current_service["name"] = service_attr.text
        except:
            self.logger.error("Failed to get current service or stream")
        return self.enigma_state.current_service

    def get_empty_service(self):
        return {
            "reference": "0:0:0:0:0:0:0:0:0:0::",
            "name": "N/A",
            "type": "normal"
        }

    def get_bouquets(self, force = False):
        if force or not self.enigma_state.load_bouquets():
            self.enigma_state.reset_bouquets()
            self.get_bouquets_tv()
            self.get_bouquets_radio()
            self.enigma_state.save_bouquets()
        
    def get_bouquets_tv(self):
        response = requests.get("http://%s/web/getservices" %(self.enigma_config["hostname"]))
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
                    service["services"] = self.get_services_2(service)
                    self.enigma_state.bouquets["tv"].append(service)

    def get_bouquets_radio(self):
        response = requests.get("http://%s/web/getservices?sRef=1:7:2:0:0:0:0:0:0:0:type == 2 FROM BOUQUET \"bouquets.radio\"" %(self.enigma_config["hostname"]))
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
                    service["services"] = self.get_services_2(service)
                    self.enigma_state.bouquets["radio"].append(service)

    def get_services(self, bouquet):
        self.enigma_state.services = []
        response = requests.get("http://%s/web/getservices?sRef=1:7:1:0:0:0:0:0:0:0:FROM%%20BOUQUET%%20%%22%s%%22%%20ORDER%%20BY%%20bouquet" %(self.enigma_config["hostname"], bouquet))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                self.enigma_state.services.append(service)
        return self.enigma_state.services

    def get_services_2(self, service, recursive = 0):
        self.enigma_state.services = []
        response = requests.get("http://%s/web/getservices?sRef=%s" %(self.enigma_config["hostname"], quote(service["reference"])))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                if recursive > 0:
                    service["services"] = self.get_services_2(service, recursive -1)
                self.enigma_state.services.append(service)
        return self.enigma_state.services

    def fetch_services(self, service, recursive = 0):
        services = []
        response = requests.get("http://%s/web/getservices?sRef=%s" %(self.enigma_config["hostname"], quote(service["reference"])))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                if recursive > 0:
                    service["services"] = fetch_services(service, recursive -1)
                services.append(service)
        return services

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
                    self.logger.info("Getting EPG for %s" %(service["reference"]))
                    response = requests.get("http://%s/web/epgservice?sRef=%s" %(self.enigma_config["hostname"], quote(service["reference"])))
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
                    self.enigma_state.current_service_event = service_event
                    return service_event
        return None

    def update(self):
        last_service = self.enigma_state.current_service
        self.enigma_state.current_service = self.get_current_service_stream()
        self.get_epg(self.enigma_state.current_service)
        self.update_label(self.enigma_state.current_service)
        if not last_service or self.enigma_state.current_service["reference"] != last_service["reference"]:
            self.insert_history(self.enigma_state.current_service)

    def insert_history(self, service):
        history = []
        for _service in self.enigma_state.history:
            if _service["reference"] != service["reference"]:
                history.append(_service)
        history.insert(0, service)
        self.enigma_state.history = history
        self.enigma_indicator.rebuild_menu()

    def update_label(self, service):
        if service:
            if self.enigma_config["showCurrentShowTitle"]:
                current_service_event = self.get_current_service_event(service)
                if current_service_event != None:
                    if self.enigma_config["showStationName"]:
                        self.enigma_indicator.update_label("%s: %s" %(service["name"], current_service_event["title"]))
                    elif current_service_event["title"].strip() == "" and self.enigma_config["currentShowTitleFallback"]:
                        self.enigma_indicator.update_label(service["name"])
                    else:
                        self.enigma_indicator.update_label(current_service_event["title"])
                elif self.enigma_config["showStationName"]:
                    self.enigma_indicator.update_label(service["name"])
            elif self.enigma_config["showStationName"]:
                self.enigma_indicator.update_label(service["name"])
            else:
                self.enigma_indicator.update_label("")
            if self.enigma_config["showStationIcon"]:
                self.enigma_indicator.update_icon(service)
            elif self.enigma_config["showStationName"] or self.enigma_config["showCurrentShowTitle"]:
                # Showing the station name or current show title => No icon
                self.enigma_indicator.remove_icon()
            else:
                # No text => Icon needed
                self.enigma_indicator.update_icon(None)
        else:
            self.enigma_indicator.update_label("")
            self.enigma_indicator.update_icon(None)

    def stream(self, service):
        if service:
            if "type" in service and service["type"] == "stream":
                self.logger.info("Open stream %s" %(service["streamurl"]))
                webbrowser.open(service["streamurl"])
            elif "reference" in service:
                stream_url = "http://%s/web/stream.m3u?ref=%s" %(self.enigma_config["hostname"], quote(service["reference"]))
                self.logger.info("Open stream %s" %(stream_url))
                webbrowser.open(stream_url)
            else:
                self.logger.error("Missing service reference or stream url!")
        else:
            self.logger.error("No service!")

    def get_stream_url(self, service, quoted = True):
        if service:
            if "FROM BOUQUET" in service["reference"]:
                services = self.fetch_services(service)
                self.logger.info(str(services))
                self.logger.info(str(self.get_stream_url(services[0], quoted)))
                return self.get_stream_url(services[0], quoted)
            elif service["reference"].split(":")[0] == "4097":
                service["type"] = "stream"
                service["streamurl"] = service["reference"].split(":")[10].replace("%3a", ":")
                if service["reference"].split(":")[2] == "0":
                    service["streamtype"] = "tv"
                elif service["reference"].split(":")[2] == "2":
                    service["streamtype"] = "radio"
                else:
                    service["streamtype"] = "stream"
            if "type" in service and service["type"] == "stream":
                return service["streamurl"]
            elif "reference" in service:
                if quoted:
                    return "http://%s:8001/%s" %(self.enigma_config["hostname"], quote(service["reference"]))
                else:
                    return "http://%s:8001/%s" %(self.enigma_config["hostname"], service["reference"])
            else:
                self.logger.error("Missing service reference or stream url!")
        else:
            self.logger.error("No service!")

    def select_channel(self, widget, service):
        try:
            self.logger.info("Select channel %s" %(service["reference"]))
            response = requests.get("http://%s/web/zap?sRef=%s" %(self.enigma_config["hostname"], quote(service["reference"])))
            self.current_service = service
            self.update_label(service)
        except:
            self.logger.error("Failed to select channel")

    def channel_up(self):
        try:
            self.logger.info("Channel up")
            response = requests.get("http://%s/web/remotecontrol?command=403" %(self.enigma_config["hostname"]))
            self.update()
        except:
            self.logger.error("Failed to select next channel")

    def channel_down(self):
        try:
            self.logger.info("Channel down")
            response = requests.get("http://%s/web/remotecontrol?command=402" %(self.enigma_config["hostname"]))
            self.update()
        except:
            self.logger.error("Failed to select previous channel")

    def set_power_state(self, state):
        try:
            self.logger.info("Setting power state %d" %(state))
            response = requests.get("http://%s/web/powerstate?newstate=%d" %(self.enigma_config["hostname"], state))
            self.update()
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

    def open_web_ui(self, widget = None):
        webbrowser.open("http://%s/" %(self.enigma_config["hostname"]), 2)

    def save_bouquet_as_pls(self, widget = None, service = None):
        path = os.path.join(user_data_dir("e2indicator"), "%s.m3u" %(service["name"]))
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w") as f:
            f.write("#EXTM3U\n#EXTVLCOPT--http-reconnect=true\n")
            for _service in service["services"]:
                f.write("#EXTINF:-1,%s\n%s\n" %(_service["name"], self.get_stream_url(_service, False)))
        # webbrowser.open_new_tab("file://%s"%(path))
        # subprocess.call(["xdg-open", path])

    def get_picon(self, service):
        try:
            filename = "%s.png" %(service["reference"][:-1].replace(":", "_"))
            url = "http://%s/picon/%s" %(self.enigma_config["hostname"], filename)
            local_path = "/tmp/%s" %(filename)
            filename2 = "%s.png" %(service["name"].lower().replace(" ", ""))
            url2 = "http://%s/picon/%s" %(self.enigma_config["hostname"], filename2)
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
                            r = requests.get(url2)
                            if r.status_code == 200:
                                f = open(local_path, "wb")
                                f.write(r.content)
                                f.close()
                                return local_path2
                            else:
                                return self.enigma_indicator.get_icon_path(self.enigma_indicator.get_icon())
                    except:
                        return self.enigma_indicator.get_icon_path(self.enigma_indicator.get_icon())
                else:
                    return local_path2
            else:
                return local_path
            return self.enigma_indicator.get_icon_path(self.enigma_indicator.get_icon())
        except Exception as e:
            self.logger.error("Failed to update icon")
            return self.enigma_indicator.get_icon_path(self.enigma_indicator.get_icon())

    def get_picon_url(self, service):
        return "file://%s" %(self.get_picon(service))
