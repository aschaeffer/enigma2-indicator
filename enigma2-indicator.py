#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from symbol import except_clause

__author__ = "andreasschaeffer"

import socket
import time
import signal
import gi
import os
import threading
import logging
import traceback
import time
import webbrowser
import json
import xml
import requests
import dbus
import dbus.service
import copy
from xml.etree import ElementTree
from urllib.parse import quote

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version('Notify', '0.7')

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject

from dbus.mainloop.glib import DBusGMainLoop

logging.basicConfig(level = logging.DEBUG, format = "%(asctime)-15s [%(name)-5s] [%(levelname)-5s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

APPINDICATOR_ID = "enigma2-indicator"

IDENTITY = 'enigma2-indicator'

DESKTOP = 'enigma2-indicator'

BUS_NAME = 'org.mpris.MediaPlayer2.' + IDENTITY
OBJECT_PATH = '/org/mpris/MediaPlayer2'
ROOT_INTERFACE = 'org.mpris.MediaPlayer2'
PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'
PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'
PLAYLISTS_IFACE = 'org.mpris.MediaPlayer2.Playlists'

ICON_PATH = "/usr/share/icons/Humanity/devices/24"

HOSTNAME = "daskaengurutv"

class Enigma2Client():

    model = ""
    service_name = ""
    current_service = None
    services = []
    enigma2_indicator = None
    bouquets = {}

    def __init__(self, enigma2_indicator):
        self.bouquets["tv"] = []
        self.bouquets["radio"] = []
        self.enigma2_indicator = enigma2_indicator

    def update_bouquets(self):
        self.get_bouquets_tv()
        self.get_bouquets_radio()
        
    def get_model(self):
        response = requests.get("http://%s/web/about" %(HOSTNAME))
        tree = ElementTree.fromstring(response.content)
        for child in tree[0]:
            if child.tag == "e2model":
                self.model = child.text
        return self.model

    def get_current_service(self):
        response = requests.get("http://%s/web/subservices" %(HOSTNAME))
        tree = ElementTree.fromstring(response.content)
        for service_tag in tree:
            if service_tag.tag == "e2service":
                service = {}
                for service_attr in service_tag:
                    if service_attr.tag == "e2servicereference":
                        service["reference"] = service_attr.text
                    if service_attr.tag == "e2servicename":
                        service["name"] = service_attr.text
                self.current_service = service
        return self.current_service

    def get_bouquets_tv(self):
        response = requests.get("http://%s/web/getservices" %(HOSTNAME))
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
        # http://daskaengurutv/web/getservices?sRef=1:7:2:0:0:0:0:0:0:0:type == 2 FROM BOUQUET "bouquets.radio"
        response = requests.get("http://%s/web/getservices?sRef=1:7:2:0:0:0:0:0:0:0:type == 2 FROM BOUQUET \"bouquets.radio\"" %(HOSTNAME))
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
        response = requests.get("http://%s/web/getservices?sRef=1:7:1:0:0:0:0:0:0:0:FROM%%20BOUQUET%%20%%22%s%%22%%20ORDER%%20BY%%20bouquet" %(HOSTNAME, bouquet))
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
        response = requests.get("http://%s/web/getservices?sRef=%s" %(HOSTNAME, quote(service["reference"])))
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
        response = requests.get("http://%s/web/epgservice?sRef=%s" %(HOSTNAME, quote(service["reference"])))
        tree = ElementTree.fromstring(response.content)
        service["events"] = []
        for e2event_tag in tree:
            if e2event_tag.tag == "e2event":
                service_event = {}
                for e2event_attr in e2event_tag:
                    if e2event_attr.tag == "e2eventtitle":
                        service_event["title"] = e2event_attr.text
                    if e2event_attr.tag == "e2eventdescription":
                        service_event["description"] = e2event_attr.text
                    if e2event_attr.tag == "e2eventstart":
                        service_event["start"] = int(e2event_attr.text)
                    if e2event_attr.tag == "e2eventduration":
                        service_event["duration"] = int(e2event_attr.text)
                    if e2event_attr.tag == "e2eventcurrenttime":
                        service_event["currenttime"] = int(e2event_attr.text)
                service["events"].append(service_event)

    def get_current_service_event(self, service):
        if "events" in service:
            for service_event in service["events"]:
                if service_event["start"] < service_event["currenttime"] and service_event["start"] + service_event["duration"] > service_event["currenttime"]:
                    return service_event
        return None

    def select_channel(self, widget, service):
        response = requests.get("http://%s/web/zap?sRef=%s" %(HOSTNAME, quote(service["reference"])))
        self.current_service = service
        self.update_label(service)

    def update_label(self, service):
        self.get_epg(service)
        current_service_event = self.get_current_service_event(service)
        if current_service_event != None:
            self.enigma2_indicator.update_label("%s: %s" %(service["name"], current_service_event["title"]))
        else:
            self.enigma2_indicator.update_label(service["name"])

    def stream(self, service):
        webbrowser.open("http://%s/web/stream.m3u?ref=%s" %(HOSTNAME, quote(service["reference"])))

    def channel_up(self):
        response = requests.get("http://%s/web/remotecontrol?command=403" %(HOSTNAME))
        self.update_label(self.get_current_service())

    def channel_down(self):
        response = requests.get("http://%s/web/remotecontrol?command=402" %(HOSTNAME))
        self.update_label(self.get_current_service())


class FeedbackWatcher(threading.Thread):
    
    ended = False
    enigma2_indicator = None
    enigma_client = None
    current_service = None

    def __init__(self, enigma2_indicator, enigma_client):
        threading.Thread.__init__(self)
        self.enigma2_indicator = enigma2_indicator
        self.enigma_client = enigma_client

    def run(self):
        while not self.ended:
            self.current_service = self.enigma_client.get_current_service()
            self.enigma_client.update_label(self.current_service)
            time.sleep(10.0)

    def kill(self):
        self.ended = True


class GtkUpdater(threading.Thread):
    
    ended = False

    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        while not self.ended:
            gtk.main_iteration_do(False)

    def kill(self):
        self.ended = True




class MprisServer(threading.Thread, dbus.service.Object):

    enigma2_indicator = None
    enigma_client = None
    properties = None
    bus = None
    ended = False
    
    logger = logging.getLogger("mpris")

    def __init__(self, enigma2_indicator, enigma_client):
        threading.Thread.__init__(self)
        self.enigma2_indicator = enigma2_indicator
        self.enigma_client = enigma_client
        self.properties = {
            ROOT_INTERFACE: self._get_root_iface_properties(),
            PLAYER_INTERFACE: self._get_player_iface_properties()
        }
        self.main_loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
        # self.main_loop = GObject.MainLoop()
        self.bus = dbus.SessionBus(mainloop = self.main_loop)
        self.bus_name = self._connect_to_dbus()
        dbus.service.Object.__init__(self, self.bus_name, OBJECT_PATH)

    def _get_root_iface_properties(self):
        return {
            'CanQuit': (True, None),
            'Fullscreen': (False, None),
            'CanSetFullscreen': (False, None),
            'CanRaise': (False, None),
            # NOTE Change if adding optional track list support
            'HasTrackList': (False, None),
            'Identity': (IDENTITY, None),
            'DesktopEntry': (DESKTOP, None),
            'SupportedUriSchemes': (dbus.Array([], 's', 1), None),
            'SupportedMimeTypes': (dbus.Array([], 's', 1), None),
        }

    def _get_player_iface_properties(self):
        return {
            'PlaybackStatus': (self.get_playback_status, None),
            'LoopStatus': (self.get_loop_status, None),
            'Rate': (1.0, None),
            'Shuffle': (None, None),
            'Metadata': (self.get_metadata, None),
            'Volume': (self.get_volume, self.set_volume),
            'Position': (self.get_position, None),
            'MinimumRate': (1.0, None),
            'MaximumRate': (1.0, None),
            'CanGoNext': (self.can_go_next, None),
            'CanGoPrevious': (self.can_go_previous, None),
            'CanPlay': (self.can_play, None),
            'CanPause': (self.can_pause, None),
            'CanSeek': (self.can_seek, None),
            'CanControl': (self.can_control, None),
        }

    def _connect_to_dbus(self):
        # bus_type = self.config['mpris']['bus_type']
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(BUS_NAME, self.bus)
        return bus_name

    def get_playback_status(self):
        return 'Playing'

    def get_loop_status(self):
        return 'None'

    def can_go_next(self):
        return True

    def can_go_previous(self):
        return True

    def can_play(self):
        return True

    def can_pause(self):
        return True

    def can_seek(self):
        return True

    def can_control(self):
        return True

    def update_metadata(self):
        self.enigma_client.get_epg(self.enigma_client.current_service)
        self.current_service_event = self.enigma_client.get_current_service_event(self.enigma_client.current_service)

    def get_metadata(self):
        self.logger.debug("Get Metadata")
        service = self.enigma_client.current_service
        metadata = {
            'mpris:trackid': service["reference"],
            'mpris:length': 0,
            'xesam:title': service["name"],
            'xesam:artist': service["name"],
            'mpris:artUrl': 'http://%s/picon/%s.png' %(HOSTNAME, service["reference"][:-1].replace(":", "_"))
        }
#            1_0_19_283E_3FB_1_C00000_0_0_0
#            1:0:19:283E:3FB:1:C00000:0:0:0:
        if self.current_service_event:
            metadata['mpris:length'] = dbus.Int64(self.current_service_event["duration"] * 1000)
            metadata['xesam:title'] = self.current_service_event["title"]
            metadata['xesam:album'] = self.current_service_event["description"]
        return dbus.Dictionary(metadata, signature = 'sv')

    def get_position(self):
        return dbus.Int64((self.current_service_event["currenttime"] - self.current_service_event["start"]) * 1000)

    def get_volume(self):
        return 1.0

    def set_volume(self, value):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def Pause(self):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def PlayPause(self):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def Play(self):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def Stop(self):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def Next(self):
        self.enigma_client.channel_down()
        time.sleep(1.0)
        self.update_metadata()
        self.PropertiesChanged(PLAYER_INTERFACE, { 'Metadata': self.get_metadata() }, [])

    @dbus.service.method(PLAYER_INTERFACE)
    def Previous(self):
        self.enigma_client.channel_up()
        time.sleep(1.0)
        self.update_metadata()
        self.PropertiesChanged(PLAYER_INTERFACE, { 'Metadata': self.get_metadata() }, [])

    # --- Properties interface

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = 'ss', out_signature = 'v')
    def Get(self, interface, prop):
        self.logger.debug('%s.Get(%s, %s) called' %(dbus.PROPERTIES_IFACE, repr(interface), repr(prop)))
        (getter, _) = self.properties[interface][prop]
        if callable(getter):
            return getter()
        else:
            return getter

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = 's', out_signature = 'a{sv}')
    def GetAll(self, interface):
        self.logger.debug('%s.GetAll(%s) called' %(PROPERTIES_INTERFACE, repr(interface)))
        getters = {}
        for key, (getter, _) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = 'ssv', out_signature = '')
    def Set(self, interface, prop, value):
        self.logger.debug( '%s.Set(%s, %s, %s) called' %(PROPERTIES_INTERFACE, repr(interface), repr(prop), repr(value)))
        _, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)
            self.PropertiesChanged(interface, {prop: self.Get(interface, prop)}, [])

    @dbus.service.signal(dbus_interface = PROPERTIES_INTERFACE, signature = 'sa{sv}as')
    def PropertiesChanged(self, interface, changed_properties, invalidated_properties):
        self.logger.debug('%s.PropertiesChanged(%s, %s, %s) signaled' %(PROPERTIES_INTERFACE, interface, changed_properties, invalidated_properties))

    # --- Root interface methods

    @dbus.service.method(dbus_interface=ROOT_INTERFACE)
    def Raise(self):
        self.logger.debug('%s.Raise called' %(ROOT_INTERFACE))
        # Do nothing, as we do not have a GUI

    @dbus.service.method(dbus_interface=ROOT_INTERFACE)
    def Quit(self):
        self.logger.debug('%s.Quit called' %(ROOT_INTERFACE))
        self.enigma2_indicator.quit(None)

    def kill(self):
        self.ended = True

    def run(self):
        time.sleep(1.0)
        self.update_metadata()
        self.PropertiesChanged(PLAYER_INTERFACE, { 'Metadata': self.get_metadata() }, [])
        time.sleep(5.0)
        while not self.ended:
            try:
                self.update_metadata()
                self.PropertiesChanged(PLAYER_INTERFACE, { 'Metadata': self.get_metadata() }, [])
            except:
                pass
            finally:
                time.sleep(10.0)


class Enigma2Indicator():

    indicator = None
    enigma_client = None
    mpris_server = None
    notification = notify.Notification.new("")
    notifications_initialized = False
    initialized = False
    gtk_updater = None

    def __init__(self):

        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, self.get_icon_path(self.get_icon()), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

        menu = gtk.Menu()
        item_quit = gtk.MenuItem("Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)
        menu.show_all()
        self.indicator.set_menu(menu)
        self.indicator.connect("scroll-event", self.scroll)

        self.gtk_updater = GtkUpdater()
        self.gtk_updater.start()

        notify.init(APPINDICATOR_ID)
        self.notification = notify.Notification.new("")
        self.notifications_initialized = True

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        self.enigma_client = Enigma2Client(self)

        self.update_label("Loading...")
        self.enigma_client.update_bouquets()
        self.indicator.set_menu(self.build_menu())
        
        current_service = self.enigma_client.get_current_service()
        self.enigma_client.update_label(current_service)

        self.feedback_watcher = FeedbackWatcher(self, self.enigma_client)
        self.feedback_watcher.start()

        self.mpris_server = MprisServer(self, self.enigma_client)
        self.mpris_server.start()

        self.set_initialized(True)

    def quit(self, source):
        self.set_initialized(False)
        if self.gtk_updater != None:
            self.gtk_updater.kill()
            self.gtk_updater.join(8)
        if self.feedback_watcher != None:
            self.feedback_watcher.kill()
            self.feedback_watcher.join(8)
        if self.mpris_server != None:
            self.mpris_server.kill()
            self.mpris_server.join(8)
        gtk.main_quit()

    def set_initialized(self, initialized):
        self.initialized = initialized

    def get_icon(self):
        return "monitor"
    
    def get_icon_path(self, icon_name):
        return os.path.abspath("%s/%s.svg" %(ICON_PATH, icon_name))

    def show_notification(self, title, text, icon):
        if self.notifications_initialized:
            self.notification.update(title, text, icon)
            self.notification.show()

    def update_label(self, text = None):
        self.indicator.set_label(text, "")

    def scroll(self, indicator, steps, direction):
        if direction == gdk.ScrollDirection.DOWN:
            self.enigma_client.channel_down()
        elif direction == gdk.ScrollDirection.UP:
            self.enigma_client.channel_up()

    def stream(self, widget):
        self.enigma_client.stream(self.enigma_client.current_service)

    def open_web_ui(self, widget):
        webbrowser.open("http://%s/" %(HOSTNAME), 2)

    def create_menu_item(self, menu, name, cmd):
        item = gtk.MenuItem(name)
        item.connect("activate", self.command_service.send_command_w, cmd)
        menu.append(item)

    def build_menu(self):
        menu = gtk.Menu()

        menu_tv = gtk.Menu()
        item_tv = gtk.MenuItem("TV")
        item_tv.set_submenu(menu_tv)
        for service in self.enigma_client.bouquets["tv"]:
            menu_bouquet = gtk.Menu()
            item_bouquet = gtk.MenuItem(service["name"])
            item_bouquet.set_submenu(menu_bouquet)
            menu_tv.append(item_bouquet)
            for sub_service in self.enigma_client.get_services_2(service):
                item_service = gtk.MenuItem(sub_service["name"])
                item_service.connect("activate", self.enigma_client.select_channel, sub_service)
                menu_bouquet.append(item_service)
        menu.append(item_tv)

        menu_radio = gtk.Menu()
        item_radio = gtk.MenuItem("Radio")
        item_radio.set_submenu(menu_radio)
        for service in self.enigma_client.bouquets["radio"]:
            menu_bouquet = gtk.Menu()
            item_bouquet = gtk.MenuItem(service["name"])
            item_bouquet.set_submenu(menu_bouquet)
            menu_radio.append(item_bouquet)
            for sub_service in self.enigma_client.get_services_2(service):
                item_service = gtk.MenuItem(sub_service["name"])
                item_service.connect("activate", self.enigma_client.select_channel, sub_service)
                menu_bouquet.append(item_service)
        menu.append(item_radio)

        menu.append(gtk.SeparatorMenuItem())

        item_stream = gtk.MenuItem("Stream Current Station")
        item_stream.connect("activate", self.stream)
        menu.append(item_stream)
        self.indicator.set_secondary_activate_target(item_stream)

        item_webinterface = gtk.MenuItem("Web Interface")
        item_webinterface.connect("activate", self.open_web_ui)
        menu.append(item_webinterface)

        item_quit = gtk.MenuItem("Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.append(gtk.SeparatorMenuItem())

        menu.show_all()
        return menu

    def main(self):
        gtk.main()


if __name__ == "__main__":
    enigma2_indicator = Enigma2Indicator()
    enigma2_indicator.main()

