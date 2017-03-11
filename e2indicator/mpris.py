#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import threading
import dbus
import dbus.service

from dbus.mainloop.glib import DBusGMainLoop

IDENTITY = "e2indicator"
DESKTOP = "e2indicator"

BUS_NAME = "org.mpris.MediaPlayer2." + IDENTITY
OBJECT_PATH = "/org/mpris/MediaPlayer2"
ROOT_INTERFACE = "org.mpris.MediaPlayer2"
PLAYER_INTERFACE = "org.mpris.MediaPlayer2.Player"
PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

class Enigma2MprisServer(threading.Thread, dbus.service.Object):

    enigma_client = None
    enigma_state = None
    properties = None
    bus = None
    ended = False

    logger = logging.getLogger("e2-mpris")

    def __init__(self, enigma_client, enigma_state):
        threading.Thread.__init__(self)
        self.enigma_client = enigma_client
        self.enigma_state = enigma_state
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
            "CanQuit": (self.can_quit, None),
            "Fullscreen": (False, None),
            "CanSetFullscreen": (False, None),
            "CanRaise": (self.can_raise, None),
            # NOTE Change if adding optional track list support
            "HasTrackList": (False, None),
            "Identity": (IDENTITY, None),
            "DesktopEntry": (DESKTOP, None),
            "SupportedUriSchemes": (dbus.Array([], "s", 1), None),
            "SupportedMimeTypes": (dbus.Array([], "s", 1), None),
        }

    def _get_player_iface_properties(self):
        return {
            "PlaybackStatus": (self.get_playback_status, None),
            "LoopStatus": (self.get_loop_status, None),
            "Rate": (1.0, None),
            "Shuffle": (None, None),
            "Metadata": (self.get_metadata, None),
            "Volume": (self.get_volume, self.set_volume),
            "Position": (self.get_position, None),
            "MinimumRate": (1.0, None),
            "MaximumRate": (1.0, None),
            "CanGoNext": (self.can_go_next, None),
            "CanGoPrevious": (self.can_go_previous, None),
            "CanPlay": (self.can_play, None),
            "CanPause": (self.can_pause, None),
            "CanSeek": (self.can_seek, None),
            "CanControl": (self.can_control, None),
        }

    def _connect_to_dbus(self):
        self.bus = dbus.SessionBus()
        bus_name = dbus.service.BusName(BUS_NAME, self.bus)
        return bus_name

    def can_quit(self):
        return True

    def can_raise(self):
        return True

    def get_playback_status(self):
        return "Playing"

    def get_loop_status(self):
        return "None"

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

    def get_empty_dbus_dict(self):
        return dbus.Dictionary(self.get_empty_metadata_dict(), signature = "sv")

    def get_empty_metadata_dict(self):
        return {
            "mpris:trackid": "",
            "mpris:length": 0,
            "xesam:title": " ",
            "xesam:artist": " ",
            "mpris:artUrl": " ",
            "xesam:album": " ",
            "xesam:comment": " ",
        }

    def get_position(self):
        if "currenttime" in self.enigma_state.current_service_event and "start" in self.enigma_state.current_service_event:
            return dbus.Int64((self.enigma_state.current_service_event["currenttime"] - self.enigma_state.current_service_event["start"]) * 1000)
        else:
            return 0

    def get_volume(self):
        return 1.0

    def set_volume(self, value):
        pass

    @dbus.service.method(PLAYER_INTERFACE)
    def Pause(self):
        self.update()

    @dbus.service.method(PLAYER_INTERFACE)
    def PlayPause(self):
        self.update()

    @dbus.service.method(PLAYER_INTERFACE)
    def Play(self):
        self.update()

    @dbus.service.method(PLAYER_INTERFACE)
    def Stop(self):
        self.update()

    @dbus.service.method(PLAYER_INTERFACE)
    def Next(self):
        self.enigma_client.channel_down()
        self.update()

    @dbus.service.method(PLAYER_INTERFACE)
    def Previous(self):
        self.enigma_client.channel_up()
        self.update()

    # --- Properties interface

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = "ss", out_signature = "v")
    def Get(self, interface, prop):
        # self.logger.debug("%s.Get(%s, %s) called" %(dbus.PROPERTIES_IFACE, repr(interface), repr(prop)))
        (getter, _) = self.properties[interface][prop]
        if callable(getter):
            return getter()
        else:
            return getter

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = "s", out_signature = "a{sv}")
    def GetAll(self, interface):
        self.logger.debug("%s.GetAll(%s) called" %(PROPERTIES_INTERFACE, repr(interface)))
        getters = {}
        for key, (getter, _) in self.properties[interface].iteritems():
            getters[key] = getter() if callable(getter) else getter
        return getters

    @dbus.service.method(dbus_interface = PROPERTIES_INTERFACE, in_signature = "ssv", out_signature = "")
    def Set(self, interface, prop, value):
        self.logger.debug( "%s.Set(%s, %s, %s) called" %(PROPERTIES_INTERFACE, repr(interface), repr(prop), repr(value)))
        _, setter = self.properties[interface][prop]
        if setter is not None:
            setter(value)
            self.PropertiesChanged(interface, {prop: self.Get(interface, prop)}, [])

    @dbus.service.signal(dbus_interface = PROPERTIES_INTERFACE, signature = "sa{sv}as")
    def PropertiesChanged(self, interface, changed_properties, invalidated_properties):
        self.logger.debug("%s.PropertiesChanged(%s, %s, %s) signaled" %(PROPERTIES_INTERFACE, interface, changed_properties, invalidated_properties))

    # --- Root interface methods

    @dbus.service.method(dbus_interface=ROOT_INTERFACE)
    def Raise(self):
        self.client.open_web_ui()

    @dbus.service.method(dbus_interface=ROOT_INTERFACE)
    def Quit(self):
        self.logger.debug("%s.Quit called" %(ROOT_INTERFACE))

    def update(self):
        self.PropertiesChanged(PLAYER_INTERFACE, { "Metadata": self.get_metadata() }, [])

    def get_metadata(self):
        try:
            if self.enigma_state.current_service and self.enigma_state.current_service_event:
                service = self.enigma_state.current_service
                current_service_event = self.enigma_state.current_service_event
                # self.logger.debug("Get Metadata for %s" %(service["reference"]))
                metadata = {
                    "mpris:trackid": service["reference"],
                    "mpris:length": 0,
                    "xesam:title": " ",
                    "xesam:artist": service["name"],
                    "xesam:album": " ",
                    "xesam:comment": " ",
                    "mpris:artUrl": self.enigma_client.get_picon_url(service)
                }
                if current_service_event:
                    if "id" in current_service_event and current_service_event["id"]:
                        metadata["mpris:trackid"] = current_service_event["id"]
                    if "title" in current_service_event and current_service_event["title"]:
                        metadata["xesam:title"] = current_service_event["title"]
                    if "description" in current_service_event and current_service_event["description"]:
                        metadata["xesam:album"] = current_service_event["description"]
                    elif "descriptionextended" in current_service_event and current_service_event["descriptionextended"]:
                        metadata["xesam:album"] = current_service_event["descriptionextended"]
                    if "descriptionextended" in current_service_event and current_service_event["descriptionextended"]:
                        metadata["xesam:comment"] = current_service_event["descriptionextended"]
                    if "duration" in current_service_event and current_service_event["duration"]:
                        metadata["mpris:length"] = dbus.Int64(current_service_event["duration"] * 1000)
                # self.logger.info(str(metadata))
                return dbus.Dictionary(metadata, signature = "sv")
            else:
                return self.get_empty_dbus_dict()
        except:
            self.logger.exception("Failed to get metadata")
            return self.get_empty_dbus_dict()

    def kill(self):
        self.ended = True

    def run(self):
        while not self.ended:
            time.sleep(1.0)
            self.update()
