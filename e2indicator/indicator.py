#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "andreasschaeffer"

import gi
import logging
import os
import signal
import webbrowser

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject

from dbus.mainloop.glib import DBusGMainLoop

from e2indicator.gtkupdater import GtkUpdater
from e2indicator.client import Enigma2Client
from e2indicator.mpris import Enigma2MprisServer
from e2indicator.feedback import Enigma2FeedbackWatcher
from e2indicator.state import Enigma2State
from e2indicator.config import Enigma2Config
from e2indicator.device import Enigma2DeviceService

APPINDICATOR_ID = "e2indicator"

ICON_PATH = "/usr/share/icons/Humanity/devices/24"
INVISIBLE_ICON = "/usr/share/unity/icons/panel_shadow.png"

class Enigma2Indicator():

    indicator = None
    enigma_config = None
    enigma_state = None
    enigma_client = None
    enigma_mpris_server = None
    notification = notify.Notification.new("")
    notifications_initialized = False
    initialized = False
    gtk_updater = None
    menu = None

    logger = logging.getLogger("e2-indicator")

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

        self.update_label("Search for Devices...")
        
        self.enigma_config = Enigma2Config()

        self.enigma_device = Enigma2DeviceService(self.enigma_config)
        
        self.enigma_state = Enigma2State()
        self.enigma_client = Enigma2Client(self, self.enigma_config, self.enigma_state)

        self.update_label("%s: Loading Bouquets..." %(self.enigma_config["model"]))

        self.enigma_client.get_bouquets()

        self.feedback_watcher = Enigma2FeedbackWatcher(self.enigma_config, self.enigma_client)
        self.feedback_watcher.start()

        self.enigma_mpris_server = Enigma2MprisServer(self.enigma_client, self.enigma_state)
        self.enigma_mpris_server.start()

        self.set_initialized(True)

    def quit(self, source):
        self.set_initialized(False)
        if self.gtk_updater != None:
            self.gtk_updater.kill()
            self.gtk_updater.join(8)
        if self.feedback_watcher != None:
            self.feedback_watcher.kill()
            self.feedback_watcher.join(8)
        if self.enigma_mpris_server != None:
            self.enigma_mpris_server.kill()
            self.enigma_mpris_server.join(8)
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

    def update_icon(self, service):
        if service:
            self.indicator.set_icon(self.enigma_client.get_picon(service))
        else:
            self.indicator.set_icon(self.get_icon_path(self.get_icon()))

    def remove_icon(self):
        self.indicator.set_icon(INVISIBLE_ICON)

    def scroll(self, indicator, steps, direction):
        if direction == gdk.ScrollDirection.DOWN:
            self.enigma_client.channel_down()
        elif direction == gdk.ScrollDirection.UP:
            self.enigma_client.channel_up()

    def stream(self, widget):
        self.enigma_client.stream(self.enigma_state.current_service)

    def create_menu_item(self, menu, name, cmd):
        item = gtk.MenuItem(name)
        item.connect("activate", self.command_service.send_command_w, cmd)
        menu.append(item)

    def set_config(self, widget, key):
        self.enigma_config[key] = not self.enigma_config[key]
        self.enigma_client.update_label(self.enigma_state.current_service)

    def reload_bouquets(self, widget, data):
        self.enigma_client.get_bouquets(True)
        self.rebuild_menu()

    def rebuild_menu(self):
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        try:
            self.menu = gtk.Menu()
        except:
            return

        menu_tv = gtk.Menu()
        item_tv = gtk.MenuItem("TV")
        item_tv.set_submenu(menu_tv)
        for service in self.enigma_state.bouquets["tv"]:
            menu_bouquet = gtk.Menu()
            item_bouquet = gtk.MenuItem(service["name"])
            item_bouquet.set_submenu(menu_bouquet)
            menu_tv.append(item_bouquet)
            for sub_service in service["services"]:
                item_service = gtk.MenuItem(sub_service["name"])
                item_service.connect("activate", self.enigma_client.select_channel, sub_service)
                menu_bouquet.append(item_service)
            menu_bouquet.append(gtk.SeparatorMenuItem())
            item_m3u = gtk.MenuItem("Save %s.m3u"%(service["name"]))
            item_m3u.connect("activate", self.enigma_client.save_bouquet_as_pls, service)
            menu_bouquet.append(item_m3u)
        self.menu.append(item_tv)

        menu_radio = gtk.Menu()
        item_radio = gtk.MenuItem("Radio")
        item_radio.set_submenu(menu_radio)
        for service in self.enigma_state.bouquets["radio"]:
            menu_bouquet = gtk.Menu()
            item_bouquet = gtk.MenuItem(service["name"])
            item_bouquet.set_submenu(menu_bouquet)
            menu_radio.append(item_bouquet)
            for sub_service in service["services"]:
                item_service = gtk.MenuItem(sub_service["name"])
                item_service.connect("activate", self.enigma_client.select_channel, sub_service)
                menu_bouquet.append(item_service)
            menu_bouquet.append(gtk.SeparatorMenuItem())
            item_m3u = gtk.MenuItem("Save %s.m3u"%(service["name"]))
            item_m3u.connect("activate", self.enigma_client.save_bouquet_as_pls, service)
            menu_bouquet.append(item_m3u)
        self.menu.append(item_radio)

        self.menu.append(gtk.SeparatorMenuItem())

        item_stream = gtk.MenuItem("Stream Current Station")
        item_stream.connect("activate", self.stream)
        self.menu.append(item_stream)
        self.indicator.set_secondary_activate_target(item_stream)

        item_webinterface = gtk.MenuItem("Web Interface")
        item_webinterface.connect("activate", self.enigma_client.open_web_ui)
        self.menu.append(item_webinterface)

        menu_config = gtk.Menu()
        item_config = gtk.MenuItem("Config")
        item_config.set_submenu(menu_config)
        item_show_station_icon = gtk.CheckMenuItem.new_with_label("Show Station Logo")
        item_show_station_icon.set_active(self.enigma_config["showStationIcon"])
        item_show_station_icon.connect("toggled", self.set_config, "showStationIcon")
        menu_config.append(item_show_station_icon)
        item_show_station_name = gtk.CheckMenuItem.new_with_label("Show Station Name")
        item_show_station_name.set_active(self.enigma_config["showStationName"])
        item_show_station_name.connect("toggled", self.set_config, "showStationName")
        menu_config.append(item_show_station_name)
        item_show_current_show_title = gtk.CheckMenuItem.new_with_label("Show Current Show Title")
        item_show_current_show_title.set_active(self.enigma_config["showCurrentShowTitle"])
        item_show_current_show_title.connect("toggled", self.set_config, "showCurrentShowTitle")
        menu_config.append(item_show_current_show_title)
        item_current_show_title_fallback = gtk.CheckMenuItem.new_with_label("Fallback to Station Name")
        item_current_show_title_fallback.set_active(self.enigma_config["currentShowTitleFallback"])
        item_current_show_title_fallback.connect("toggled", self.set_config, "currentShowTitleFallback")
        menu_config.append(item_current_show_title_fallback)
        item_current_show_history = gtk.CheckMenuItem.new_with_label("Show History")
        item_current_show_history.set_active(self.enigma_config["showHistory"])
        item_current_show_history.connect("toggled", self.set_config, "showHistory")
        menu_config.append(item_current_show_history)
        item_current_show_extras = gtk.CheckMenuItem.new_with_label("Show Extras")
        item_current_show_extras.set_active(self.enigma_config["showExtras"])
        item_current_show_extras.connect("toggled", self.set_config, "showExtras")
        menu_config.append(item_current_show_extras)
        self.menu.append(item_config)

        self.menu.append(gtk.SeparatorMenuItem())

        menu_power = gtk.Menu()
        item_power = gtk.MenuItem("Power")
        item_power.set_submenu(menu_power)
        item_power_standby = gtk.MenuItem("Standby")
        item_power_standby.connect("activate", self.enigma_client.power_standby)
        menu_power.append(item_power_standby)
        item_power_deep_standby = gtk.MenuItem("Deep Standby")
        item_power_deep_standby.connect("activate", self.enigma_client.power_deep_standby)
        menu_power.append(item_power_deep_standby)
        item_power_reboot = gtk.MenuItem("Reboot")
        item_power_reboot.connect("activate", self.enigma_client.power_reboot)
        menu_power.append(item_power_reboot)
        item_power_restart_gui = gtk.MenuItem("Restart GUI")
        item_power_restart_gui.connect("activate", self.enigma_client.power_restart_gui)
        menu_power.append(item_power_restart_gui)
        item_power_wake_up = gtk.MenuItem("Wake Up")
        item_power_wake_up.connect("activate", self.enigma_client.power_wake_up)
        menu_power.append(item_power_wake_up)
        self.menu.append(item_power)

        self.menu.append(gtk.SeparatorMenuItem())

        if self.enigma_config["showExtras"]:
            menu_extras = gtk.Menu()
            item_extras = gtk.MenuItem("Extras")
            item_extras.set_submenu(menu_extras)
            item_reload_bouquets = gtk.MenuItem("Reload Bouquets")
            item_reload_bouquets.connect("activate", self.reload_bouquets, None)
            menu_extras.append(item_reload_bouquets)
            self.menu.append(item_extras)
            item_save_bouquets = gtk.MenuItem("Save Bouquets")
            item_save_bouquets.connect("activate", self.enigma_state.save_bouquets, None)
            menu_extras.append(item_save_bouquets)

            self.menu.append(gtk.SeparatorMenuItem())

        if self.enigma_config["showHistory"]:
            for (service, service_event) in self.enigma_state.history:
                if service_event and service_event["title"].strip() != "":
                    if "description" in service_event and service_event["description"].strip() != "":
                        menu_title = "%s\n%s\n%s" %(service["name"], service_event["title"], service_event["description"])
                    else:
                        menu_title = "%s\n%s" %(service["name"], service_event["title"])
                else:
                    menu_title = service["name"]
                item_history_item = gtk.ImageMenuItem(menu_title)
                image_path = self.enigma_client.get_picon(service)
                image = gtk.Image()
                image.set_from_file(image_path)
                item_history_item.set_image(image)
                item_history_item.set_always_show_image(True)
                item_history_item.connect("activate", self.enigma_client.select_channel, service)
                self.menu.append(item_history_item)
            self.menu.append(gtk.SeparatorMenuItem())


        self.menu.append(gtk.SeparatorMenuItem())

        item_quit = gtk.MenuItem("Quit")
        item_quit.connect("activate", self.quit)
        self.menu.append(item_quit)

        self.menu.append(gtk.SeparatorMenuItem())

        self.menu.show_all()
        return self.menu

    def main(self):
        gtk.main()
