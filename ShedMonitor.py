#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import time
import urllib2

import DHT22
import DS18B20
import Carriots

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
    DHT.read()
    logger.info('  Temperature = {:.3f} C, {:.3f} F'.format(DHT.temperature_C, DHT.temperature_F))
    logger.info('  Humidity = {:.1f} %'.format(DHT.humidity))

    if DHT.humidity < 50:
        status = 'OK'
    elif DHT.humidity < 80:
        status = 'HUMID'
    else:
        status = 'WET'
    logger.info('  Status: {}'.format(status))

    logger.info('Reading DS18B20')
    sensor = DS18B20.DS18B20()
    sensor.read()
    for temp in sensor.temperatures_C:
        logger.info('  Temperature = {:.3f} C, {:.3f} F'.format(temp, temp*9./5.+32.))


    ##-------------------------------------------------------------------------
    ## Record Values to Table
    ##-------------------------------------------------------------------------
    datestring = time.strftime('%Y%m%d_log.txt', time.localtime())
    timestring = time.strftime('%Y/%m/%d %H:%M:%S HST', time.localtime())
    datafile = os.path.join('/', 'home', 'joshw', 'logs', datestring)
    logger.debug("Preparing astropy table object for data file {}".format(datafile))
    if not os.path.exists(datafile):
        logger.debug("Making new astropy table object")
        SummaryTable = table.Table(names=('date', 'time', 'temp1', 'temp2', 'temp3', 'hum', 'status'), \
                                   dtypes=('S10', 'S12', 'f4', 'f4', 'f4', 'f4', 'S5') )
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
                                      'status': [ascii.convert_numpy('S5')],
                                      })
        except:
            logger.critical("Failed to read data file: {0} {1} {2}".format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))
    ## Add row to table
    logger.debug("Writing new row to data table.")
    SummaryTable.add_row((timestring[0:10], timestring[11:23], \
                          sensor.temperatures_F[0], sensor.temperatures_F[1], \
                          DHT.temperature_F, DHT.humidity, status))
    ## Write Table to File
    logger.info("Writing new data file.")
    ascii.write(SummaryTable, datafile, Writer=ascii.basic.Basic)



#     AddHeader = False
#     if not os.path.exists(datafile):
#         AddHeader = True
#     if DHT.temperature_F and DHT.humidity and (len(sensor.temperatures_F) == 2):
#         logger.info('Writing Results to Data File: {}'.format(datafile))
#         if DHT.humidity < 50:
#             status = 'OK'
#         elif DHT.humidity < 80:
#             status = 'HUMID'
#         else:
#             status = 'WET'
#         datafileFO = open(datafile, 'a')
#         if AddHeader:
#             datafileFO.write('{:<24s} {:>5s} {:>5s} {:>5s} {:>5s} {:>8s}\n'.format( \
#                              '# Time', 'Temp1', 'Temp2', 'Temp3', 'Hum', 'Status'))
#         datafileFO.write('{:24s} {:5.1f} {:5.1f} {:5.1f} {:5.1f} {:>8s}\n'.format(timestring, \
#                          sensor.temperatures_F[0], sensor.temperatures_F[1], \
#                          DHT.temperature_F, DHT.humidity, status))
#         datafileFO.close()


    ## Log to Carriots
    logger.info('Sending Data to Carriots')
    logger.debug('Creating Device object')
    Device = Carriots.Client(device_id="Shed@joshwalawender")
    logger.debug('Reading api key')
    Device.read_api_key_from_file(file=os.path.join(os.path.expanduser('~joshw'), '.carriots_api'))
    data_dict = {'Temperature1': sensor.temperatures_F[0], \
                 'Temperature2': sensor.temperatures_F[1], \
                 'Temperature3': DHT.temperature_F, \
                 'Humidity': DHT.humidity, \
                 'Status': status
                 }
    logger.debug(data_dict)
    logger.debug('Uploading data')
    try:
        Device.upload(data_dict)
    except urllib2.HTTPError as e:
        logger.critical('  Upload failed')
        logger.critical('  {}'.format(e.code))
        logger.critical('  {}'.format(e.reason))
    except:
        logger.critical('  Upload failed')
        logger.critical('Unexpected error: {}'.format(sys.exc_info()[0]))
    logger.debug('Done')



if __name__ == '__main__':
    main()
