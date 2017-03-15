#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name = "e2indicator",
      packages = ["e2indicator"],
      version = "0.9.0",
      description = "Ubuntu indicator for Enigma2",
      keywords = ["enigma2", "indicator", "ubuntu", "mpris"],
      classifiers = [
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
      ],
      url = "https://github.com/aschaeffer/enigma2-indicator",
      download_url = "https://github.com/aschaeffer/enigma2-indicator/archive/0.9.0.tar.gz",
      author = "Andreas Schaeffer",
      author_email = "e2indicator@schaeffernet.de",
      license = "GPLv3",
      data_files = [
          ("/usr/share/applications", ["dist/share/applications/e2indicator.desktop"]),
          ("/usr/share/pixmaps", ["dist/share/pixmaps/e2indicator.png"]),
      ],
      entry_points = {"console_scripts": ["e2indicator = e2indicator.__main__:main"]},
      install_requires = [
          'appdirs', 'toml'
      ]
)
