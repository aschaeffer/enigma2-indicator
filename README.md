# Enigma 2 Indicator for Ubuntu

Indicator for Enigma 2 based set top boxes in the local network.

![Screenshot](/screenshot.png?raw=true "Enigma 2 Indicator")

## Features

* Indicator
  * Shows current current program title and station name
  * Automatically loads TV and radio bouquets and stations
  * Menu for selecting bouquet and station
* Ubuntu Sound Menu Integration
  * Station name and picon
  * Current program title and description (from EPG)
  * Channel up / down
* MPRIS
  * Channel up / down from another program

## Installation

    git clone https://github.com/aschaeffer/enigma2-indicator.git
    cd enigma2-indicator
    sudo cp -a enigma2-indicator.py /usr/local/bin
    sudo cp -a enigma2-indicator.png /usr/share/pixmaps
    sudo xdg-desktop-menu install enigma2-indicator.desktop
    gsettings get com.canonical.indicator.sound interested-media-players
    gsettings set com.canonical.indicator.sound interested-media-players "['audacious.desktop', 'vlc.desktop', 'smplayer.desktop', 'sony-av-indicator.desktop', 'enigma2-indicator.desktop']"

## Usage

    ./enigma2-indicator.py

## System requirements

* Ubuntu 16.04
* Engima 2 based set top box
* OpenWebIf

## Authors

* Andreas Schaeffer

## License

GNU GENERAL PUBLIC LICENSE, Version 3
