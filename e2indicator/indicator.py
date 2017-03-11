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

        self.enigma_config = Enigma2Config()
        self.enigma_state = Enigma2State()
        self.enigma_client = Enigma2Client(self, self.enigma_config, self.enigma_state)

        self.update_label("Loading...")
        self.enigma_client.update_bouquets()
        self.indicator.set_menu(self.build_menu())

        self.enigma_client.update()

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
        self.enigma_client.stream(self.enigma_client.current_service)

    def create_menu_item(self, menu, name, cmd):
        item = gtk.MenuItem(name)
        item.connect("activate", self.command_service.send_command_w, cmd)
        menu.append(item)

    def set_config(self, widget, key):
        self.enigma_config[key] = not self.enigma_config[key]
        self.enigma_client.update_label(self.enigma_state.current_service)

    def build_menu(self):
        menu = gtk.Menu()

        menu_tv = gtk.Menu()
        item_tv = gtk.MenuItem("TV")
        item_tv.set_submenu(menu_tv)
        for service in self.enigma_state.bouquets["tv"]:
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
        for service in self.enigma_state.bouquets["radio"]:
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
        item_webinterface.connect("activate", self.enigma_client.open_web_ui)
        menu.append(item_webinterface)

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
        menu.append(item_config)

        menu.append(gtk.SeparatorMenuItem())

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
        menu.append(item_power)

        menu.append(gtk.SeparatorMenuItem())

        item_quit = gtk.MenuItem("Quit")
        item_quit.connect("activate", self.quit)
        menu.append(item_quit)

        menu.append(gtk.SeparatorMenuItem())

        menu.show_all()
        return menu

    def main(self):
        gtk.main()
