#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import glob
import time
import argparse
import logging
import subprocess
import re

import RPi.GPIO as GPIO

import DHT22
import DS18B20


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():

    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    parser = argparse.ArgumentParser(
             description="Program description.")
    ## add flags
    parser.add_argument("-v", "--verbose",
        action="store_true", dest="verbose",
        default=False, help="Be verbose! (default = False)")
    ## add arguments
    parser.add_argument("--input",
        type=str, dest="input",
        help="The input.")
    args = parser.parse_args()

    ##-------------------------------------------------------------------------
    ## Create logger object
    ##-------------------------------------------------------------------------
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    if args.verbose:
        LogConsoleHandler.setLevel(logging.DEBUG)
    else:
        LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)23s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    logger.addHandler(LogConsoleHandler)
    ## Set up file output
#     LogFileName = None
#     LogFileHandler = logging.FileHandler(LogFileName)
#     LogFileHandler.setLevel(logging.DEBUG)
#     LogFileHandler.setFormatter(LogFormat)
#     logger.addHandler(LogFileHandler)

#     os.system('modprobe w1-gpio')
#     os.system('modprobe w1-therm')

    ##-------------------------------------------------------------------------
    ## Read DS18B20 Temperature Sensors
    ##-------------------------------------------------------------------------
    temps = DS18B20.read()
    for temp in temps:
        logger.info('Temperature (DS18B20) = {:.1f} F'.format(temp))
    
    ##-------------------------------------------------------------------------
    ## Read DHT22 Temperature and Humidity Sensor
    ##-------------------------------------------------------------------------
    temp_DHT, humidity = DHT22.read()
    logger.info('Temperature (DHT22) = {:.1f} F'.format(temp_DHT))
    logger.info('Humidity (DHT22) = {:.0f} %'.format(humidity))


if __name__ == '__main__':
    main()
