#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import subprocess
import datetime
import ephem

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
    parser.add_argument("--port",
        type=str, dest="port", required=True,
        help="The port (use 'sudo gphoto2 --auto-detect' to find port.")
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


    ##-------------------------------------------------------------------------
    ## 
    ##-------------------------------------------------------------------------
    Observatory = ephem.Observer()
    Observatory.lon = "-155:34:33.9"
    Observatory.lat = "+19:32:09.66"
    Observatory.elevation = 3400.0
    Observatory.temp = 10.0
    Observatory.pressure = 680.0
    now = datetime.datetime.utcnow()
    Observatory.date = now

    the_Sun = ephem.Sun()
    the_Sun.compute(Observatory)

    Observatory.horizon = '0.0'
    SunsetTime  = Observatory.previous_setting(ephem.Sun()).datetime()
    SunriseTime = Observatory.next_rising(ephem.Sun()).datetime()
    Observatory.horizon = '-6.0'
    EveningCivilTwilightTime = Observatory.previous_setting(ephem.Sun(), use_center=True).datetime()
    MorningCivilTwilightTime = Observatory.next_rising(ephem.Sun(), use_center=True).datetime()
    Observatory.horizon = '-12.0'
    EveningNauticalTwilightTime = Observatory.previous_setting(ephem.Sun(), use_center=True).datetime()
    MorningNauticalTwilightTime = Observatory.next_rising(ephem.Sun(), use_center=True).datetime()
    Observatory.horizon = '-18.0'
    EveningAstronomicalTwilightTime = Observatory.previous_setting(ephem.Sun(), use_center=True).datetime()
    MorningAstronomicalTwilightTime = Observatory.next_rising(ephem.Sun(), use_center=True).datetime()

    logger.info('Sunset is at: {} UT'.format(SunsetTime))


    logger.info('Setting image format to RAW')
    gphoto_command = 'sudo /sw/bin/gphoto2 --port {} --set-config /main/settings/imageformat=0'.format(args.port)
    result = subprocess.call(gphoto_command, shell=True)
    logger.debug(result)


    logger.info('Setting focus mode to manual')
    gphoto_command = 'sudo /sw/bin/gphoto2 --port {} --set-config /main/settings/focusmode=3'.format(args.port)
    result = subprocess.call(gphoto_command, shell=True)
    logger.debug(result)


    mode = None
    now = datetime.datetime.utcnow()
    Observatory.date = now
    the_Sun = ephem.Sun()
    the_Sun.compute(Observatory)
    if the_Sun.alt < 0:
        logger.info('Sun is down')
        if now < SunsetTime:
            logger.info('It is day')
            mode = 'Av'
        elif (now > SunsetTime) and (now < EveningCivilTwilightTime):
            logger.info('It is evening (civil) twilight')
            mode = 'Av'
        elif (now > EveningCivilTwilightTime) and (now < EveningNauticalTwilightTime):
            logger.info('It is evening (nautical) twilight')
            mode = 'Av'
        elif (now > EveningNauticalTwilightTime) and (now < EveningAstronomicalTwilightTime):
            logger.info('It is evening (astronomical) twilight')
            mode = 'M'
        elif now > EveningAstronomicalTwilightTime:
            logger.info('It is fully dark')
            mode = 'M'

    gphoto_command = ['sudo', 'gphoto2', '--port', args.port, ]

if __name__ == '__main__':
    main()
