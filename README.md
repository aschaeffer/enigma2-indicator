# Enigma 2 Indicator for Ubuntu

Indicator for Enigma 2 based set top boxes in the local network.

![Screenshot Enigma2 Indicator](/docs/images/screenshot-enigma2-indicator.png?raw=true "Enigma2 Indicator")
![Screenshot Sound Menu](/docs/images/screenshot-sound-menu.png?raw=true "Sound Menu Integration")

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
    sudo -H pip install . --no-cache-dir --upgrade
    gsettings set com.canonical.indicator.sound interested-media-players "['e2indicator.desktop']"

## Usage

Just launch the enigma2 indicator from the sound menu.

## Usage Command Line

    $ e2indicator

## System requirements

* Ubuntu 16.04
* Engima 2 based set top box
* OpenWebIf

## Authors

* Andreas Schaeffer

## License

GNU GENERAL PUBLIC LICENSE, Version 3
