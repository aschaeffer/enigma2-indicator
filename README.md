# Enigma 2 Indicator for Ubuntu

Indicator for Enigma 2 based set top boxes in the local network.

![Screenshot](/screenshot.png?raw=true "Enigma 2 Indicator")

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

## Authors

* Andreas Schaeffer

## License

GNU GENERAL PUBLIC LICENSE, Version 3
