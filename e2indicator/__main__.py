#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import requests
try:
    from indicator import Enigma2Indicator
except:
    from e2indicator.indicator import Enigma2Indicator

logging.basicConfig(level = logging.INFO, format = "%(asctime)-15s [%(name)-5s] [%(levelname)-5s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger('requests').setLevel(logging.CRITICAL)

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    enigma2_indicator = Enigma2Indicator()
    enigma2_indicator.main()

    # Do argument parsing here (eg. with argparse) and anything else
    # you want your project to do.

if __name__ == "__main__":
    main()