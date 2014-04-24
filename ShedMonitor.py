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
    LogFileName = os.path.join('/', 'home', 'joshw', 'logs', 'ShedLog.txt')
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    logger.addHandler(LogFileHandler)

    ##-------------------------------------------------------------------------
    ## Get Temperature and Humidity Values
    ##-------------------------------------------------------------------------
    logger.info('#### Reading Temperature and Humidity Sensors ####')
    logger.info('Reading DHT22')
    DHT = DHT22.DHT22()
    temps = []
    temps_C = []
    hums = []
    for i in range(0,3):
        DHT.read()
        logger.debug('  Temperature = {:.3f} F, Humidity = {:.1f} %'.format(DHT.temperature_F, DHT.humidity))
        temps.append(DHT.temperature_F)
        temps_C.append(DHT.temperature_C)
        hums.append(DHT.humidity)
    DHT_temperature_F = np.median(temps)
    DHT_temperature_C = np.median(temps_C)
    DHT_humidity = np.median(hums)
    logger.info('  Temperature = {:.3f} F, Humidity = {:.1f} %'.format(DHT_temperature_F, DHT_humidity))
    AH = humidity.relative_to_absolute_humidity(DHT_temperature_C, DHT_humidity)
    logger.info('  Absolute Humidity = {:.2f} g/m^3'.format(AH))

    logger.info('Reading DS18B20')
    sensor = DS18B20.DS18B20()
    sensor.read()
    for temp in sensor.temperatures_C:
        logger.info('  Temperature = {:.3f} F'.format(temp*9./5.+32.))


    ##-------------------------------------------------------------------------
    ## Determine Status Using Humidity
    ##-------------------------------------------------------------------------
    threshold_humid = 55
    threshold_wet = 75
    if (DHT.humidity < threshold_humid):
        status = 'OK'
    elif (DHT.humidity > threshold_humid) and (DHT.humidity < threshold_wet):
        status = 'HUMID'
    else:
        status = 'WET'
    logger.info('Status: {}'.format(status))


    ##-------------------------------------------------------------------------
    ## Determine Status and Alarm Using History
    ##-------------------------------------------------------------------------
    datestring = time.strftime('%Y%m%d_log.txt', time.localtime())
    timestring = time.strftime('%Y/%m/%d %H:%M:%S HST', time.localtime())
    datafile = os.path.join('/', 'home', 'joshw', 'logs', datestring)
    if os.path.exists(datafile):
        logger.debug("Reading history data from file: {0}".format(datafile))
        data = ascii.read(datafile, guess=False,
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
    else:
        data = []
    if len(data) > 12:
        translation = {'OK':0, 'HUMID':1, 'WET':2, 'HUMID-ALARM':1, 'WET-ALARM':2}
        recent_status_vals = [translation[val] for val in data['status'][-6:]]
        recent_status = np.mean(recent_status_vals)
        recent_alarm = ('HUMID-ALARM' in data['status'][-12:]) or ('WET-ALARM' in data['status'][-12:])
        logger.debug('  Recent Status = {:.2f}, Current Status = {}, Recent alarm: {}'.format(recent_status, status, recent_alarm))
        if (recent_status > 0.5) and not status == 'OK' and not recent_alarm:
            status = status + '-ALARM'


    ##-------------------------------------------------------------------------
    ## Record Values to Table
    ##-------------------------------------------------------------------------
    logger.debug("Preparing astropy table object for data file {}".format(datafile))
    if not os.path.exists(datafile):
        logger.debug("  Making new astropy table object")
        SummaryTable = table.Table(names=('date', 'time', 'temp1', 'temp2', 'temp3', 'hum', 'AH', 'status', 'threshold humid', 'threshold wet'), \
                                   dtypes=('S10', 'S12', 'f4', 'f4', 'f4', 'f4', 'f4', 'S5', 'f4', 'f4') )
    else:
        logger.info("  Reading astropy table object from file: {0}".format(datafile))
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
                                      'threshold humid': [ascii.convert_numpy('f4')],
                                      'threshold wet': [ascii.convert_numpy('f4')],
                                      })
        except:
            logger.critical("  Failed to read data file: {0} {1} {2}".format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
    ## Add row to table
    logger.debug("  Writing new row to data table.")
    if len(sensor.temperatures_F) < 2:
        sensor.temperatures_F = [float('nan'), float('nan')]
    SummaryTable.add_row((timestring[0:10], timestring[11:23], \
                          sensor.temperatures_F[0], sensor.temperatures_F[1], \
                          DHT.temperature_F, DHT.humidity, AH, status, threshold_humid, threshold_wet))
    ## Write Table to File
    logger.info("  Writing new data file.")
    ascii.write(SummaryTable, datafile, Writer=ascii.basic.Basic)


    ## Log to Carriots
    logger.info('Sending Data to Carriots')
    logger.debug('  Creating Device object')
    Device = Carriots.Client(device_id="Shed@joshwalawender")
    logger.debug('  Reading api key')
    Device.read_api_key_from_file(file=os.path.join(os.path.expanduser('~joshw'), '.carriots_api'))
    data_dict = {'Temperature1': sensor.temperatures_F[0], \
                 'Temperature2': sensor.temperatures_F[1], \
                 'Temperature3': DHT.temperature_F, \
                 'Humidity': DHT.humidity, \
                 'Absolute Humidity': AH, \
                 'Status': status
                 }
    logger.debug(data_dict)
    logger.debug('  Uploading data')
    try:
        Device.upload(data_dict)
    except urllib2.HTTPError as e:
        logger.critical('  Upload failed')
        logger.critical('  {}'.format(e.code))
        logger.critical('  {}'.format(e.reason))
    except:
        logger.critical('  Upload failed')
        logger.critical('  Unexpected error: {}'.format(sys.exc_info()[0]))
    logger.info('Done')



if __name__ == '__main__':
    main()
