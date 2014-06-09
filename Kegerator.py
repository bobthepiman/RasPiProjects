#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import time
import numpy as np
import urllib2
import datetime

import pifacedigitalio

import DHT22
import DS18B20
import Carriots
import humidity

import astropy.io.ascii as ascii
import astropy.table as table


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    RH = float('nan')
    AH = float('nan')
    status = 'unknown'


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
    now = datetime.datetime.now()
    DateString = '{}'.format(now.strftime('%Y%m%d'))
    TimeString = '{} HST'.format(now.strftime('%H:%M:%S'))
    LogFileName = os.path.join('/', 'var', 'log', 'Kegerator', 'Log_{}.txt'.format(DateString))
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    logger.addHandler(LogFileHandler)

    ##-------------------------------------------------------------------------
    ## Get Temperature and Humidity Values
    ##-------------------------------------------------------------------------
    logger.info('#### Reading Temperature and Humidity Sensors ####')
    temperatures_F = []

#     logger.info('Reading DHT22')
#     DHT = DHT22.DHT22()
#     temps = []
#     temps_C = []
#     hums = []
#     for i in range(0,3):
#         DHT.read()
#         logger.debug('  Temperature = {:.3f} F, Humidity = {:.1f} %'.format(DHT.temperature_F, DHT.humidity))
#         temps.append(DHT.temperature_F)
#         temps_C.append(DHT.temperature_C)
#         hums.append(DHT.humidity)
#     DHT_temperature_F = np.median(temps)
#     temperatures_F.append(DHT_temperature_F)
#     DHT_temperature_C = np.median(temps_C)
#     DHT_humidity = np.median(hums)
#     logger.info('  Temperature = {:.3f} F, Humidity = {:.1f} %'.format(DHT_temperature_F, DHT_humidity))
#     AH = humidity.relative_to_absolute_humidity(DHT_temperature_C, DHT_humidity)
#     logger.info('  Absolute Humidity = {:.2f} g/m^3'.format(AH))

    logger.info('Reading DS18B20')
    sensor = DS18B20.DS18B20()
    sensor.read()
    for temp in sensor.temperatures_C:
        logger.info('  Temperature = {:.3f} F'.format(temp*9./5.+32.))
        temperatures_F.append(temp*9./5.+32.)




    ##-------------------------------------------------------------------------
    ## Turn Kegerator Relay On or Off Based on Temperature
    ##-------------------------------------------------------------------------
    temp_high = 42.0
    temp_low = 38.0
    temperature = np.median(temperatures_F)
    piFace = pifacedigitalio.PiFaceDigital()
    if temperature > temp_high:
        logger.info('Temperature {:.1f} is greater than {:.1f}.  Turning freezer on.'.format(temperature, temp_high))
        status = 'On'
        piFace.output_pins[0].turn_off()
    elif temperature < temp_low:
        logger.info('Temperature {:.1f} is greater than {:.1f}.  Turning freezer on.'.format(temperature, temp_high))
        status = 'Off'
        piFace.output_pins[0].turn_on()
    else:
        logger.info('Temperature if {:.1f}.  Taking no action.'.format(temperature))
        status = 'no-change'





    ##-------------------------------------------------------------------------
    ## Record Values to Table
    ##-------------------------------------------------------------------------
    datafile = os.path.join('/', 'var', 'log', 'Kegerator', '{}.txt'.format(DateString))
    logger.debug("Preparing astropy table object for data file {}".format(datafile))
    if not os.path.exists(datafile):
        logger.info("Making new astropy table object")
        SummaryTable = table.Table(names=('date', 'time', 'temp1', 'temp2', 'temp3', 'hum', 'AH', 'status'), \
                                   dtype=('S10', 'S12', 'f4', 'f4', 'f4', 'f4', 'f4', 'S8') )
    else:
        logger.info("Reading astropy table object from file: {0}".format(datafile))
        try:
            SummaryTable = ascii.read(datafile, guess=False,
                                      header_start=0, data_start=1,
                                      Reader=ascii.basic.Basic,
                                      converters={
                                      'date': [ascii.convert_numpy('S10')],
                                      'time': [ascii.convert_numpy('S12')],
                                      'temp1': [ascii.convert_numpy('f4')],
                                      'temp2': [ascii.convert_numpy('f4')],
                                      'temp3': [ascii.convert_numpy('f4')],
                                      'hum': [ascii.convert_numpy('f4')],
                                      'AH': [ascii.convert_numpy('f4')],
                                      'status': [ascii.convert_numpy('S11')],
                                      })
        except:
            logger.critical("Failed to read data file: {0} {1} {2}".format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
    ## Add row to table
    logger.debug("Writing new row to data table.")
    while len(temperatures_F) < 3:
        temperatures_F.append(float('nan'))
    SummaryTable.add_row((DateString, TimeString, \
                          temperatures_F[0], temperatures_F[1], \
                          temperatures_F[2], RH, AH, status))
    ## Write Table to File
    logger.info("  Writing new data file.")
    ascii.write(SummaryTable, datafile, Writer=ascii.basic.Basic)


    ## Log to Carriots
#     logger.info('Sending Data to Carriots')
#     logger.debug('  Creating Device object')
#     Device = Carriots.Client(device_id="Shed@joshwalawender")
#     logger.debug('  Reading api key')
#     Device.read_api_key_from_file(file=os.path.join(os.path.expanduser('~joshw'), '.carriots_api'))
#     data_dict = {'Temperature1': sensor.temperatures_F[0], \
#                  'Temperature2': sensor.temperatures_F[1], \
#                  'Temperature3': DHT.temperature_F, \
#                  'Humidity': DHT.humidity, \
#                  'Absolute Humidity': AH, \
#                  'Status': status
#                  }
#     logger.debug(data_dict)
#     logger.debug('  Uploading data')
#     try:
#         Device.upload(data_dict)
#     except urllib2.HTTPError as e:
#         logger.critical('  Upload failed')
#         logger.critical('  {}'.format(e.code))
#         logger.critical('  {}'.format(e.reason))
#     except:
#         logger.critical('  Upload failed')
#         logger.critical('  Unexpected error: {}'.format(sys.exc_info()[0]))


    logger.info('Done')



if __name__ == '__main__':
    main()
