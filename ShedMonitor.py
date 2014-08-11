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

'''
Crontab to run ShedMonitor.py:

PYTHONPATH = /home/joshw/bin/RasPiProjects/
@reboot  /sbin/modprobe w1-gpio ; /sbin/modprobe w1-therm
*/3  * * * * nice /usr/bin/python2.7 /home/joshw/bin/RasPiProjects/ShedMonitor.py
*/15 * * * * nice /usr/bin/python2.7 /home/joshw/bin/RasPiProjects/PlotShed.py
'''

##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main(verbose=False):
    ##-------------------------------------------------------------------------
    ## Create logger object
    ##-------------------------------------------------------------------------
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    if verbose:
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

    translation = {'OK':0, 'HUMID':1, 'WET':2, 'ALARM':2}
    if len(data) > 6:
        recent_status_vals = [translation[val] for val in data['status'][-6:]]
        recent_status = np.mean(recent_status_vals)
    if len(data) > 23:
        recent_alarm = 'ALARM' in data['status'][-23:]
        logger.debug('  Recent Status = {:.2f}, Current Status = {}, Recent alarm: {}'.format(recent_status, status, recent_alarm))
        if (recent_status > 0.5) and not status == 'OK' and not recent_alarm:
            status = 'ALARM'


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



##-------------------------------------------------------------------------
## Make Plot
##-------------------------------------------------------------------------
def plot(verbose=False):

    import matplotlib.pyplot as pyplot

    ##-------------------------------------------------------------------------
    ## Create logger object
    ##-------------------------------------------------------------------------
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    if verbose:
        LogConsoleHandler.setLevel(logging.DEBUG)
    else:
        LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)23s %(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    logger.addHandler(LogConsoleHandler)
    ## Set up file output
    LogFileName = os.path.join('/', 'home', 'joshw', 'logs', 'PlotLog.txt')
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    logger.addHandler(LogFileHandler)

    ##-------------------------------------------------------------------------
    ## Read Log File
    ##-------------------------------------------------------------------------
    datestring = time.strftime('%Y%m%d_log.txt', time.localtime())
    datafile = os.path.join('/', 'home', 'joshw', 'logs', datestring)
    logger.info("Reading Data File: "+datafile)
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
                      'status': [ascii.convert_numpy('S5')],
                      })


    ##-------------------------------------------------------------------------
    ## Plot
    ##-------------------------------------------------------------------------
    PlotFileName = time.strftime('%Y%m%d.png', time.localtime())
    PlotFile = os.path.join('/', 'home', 'joshw', 'logs', PlotFileName)
    logger.info("Writing Output File: "+PlotFile)
    dpi=72
    Figure = pyplot.figure(figsize=(16,10), dpi=dpi)
    times = [(time.strptime(val, '%H:%M:%S HST').tm_hour + time.strptime(val, '%H:%M:%S HST').tm_min/60.) for val in data['time'] ]

    HumidityAxes = pyplot.axes([0.10, 0.43, 0.9, 0.40])
    title_string = '{:10s} at {:12s}:\n'.format(data['date'][-1], data['time'][-1])
    title_string += 'Outside Temperature = {:.1f} F, '.format(data['temp2'][-1])
    title_string += 'Inside Temperature = {:.1f} F, '.format(data['temp3'][-1])
    title_string += 'Inside Humidity = {:.0f} %'.format(data['hum'][-1])
    pyplot.title(title_string)
    pyplot.plot(times, data['hum'], 'ko', label="Humidity", mew=0, ms=3)
    pyplot.plot(times, data['threshold humid'], 'y-', label='threshold humidity', linewidth=3, alpha=0.8)
    pyplot.plot(times, data['threshold wet'], 'r-', label='threshold humidity', linewidth=3, alpha=0.8)
    pyplot.fill_between(times, 0, data['hum'], where=(data['status']=="OK"), color='green', alpha=0.5)
    pyplot.fill_between(times, 0, data['hum'], where=(data['status']=="HUMID"), color='yellow', alpha=0.5)
    pyplot.fill_between(times, 0, data['hum'], where=(data['status']=="WET"), color='red', alpha=0.5)
    pyplot.fill_between(times, 0, data['hum'], where=(data['status']=="ALARM"), color='red', alpha=0.5)
    pyplot.fill_between(times, 90, 100, where=(data['status']=="HUMID-ALARM"), color='yellow', alpha=0.8)
    pyplot.fill_between(times, 90, 100, where=(data['status']=="WET-ALARM"), color='red', alpha=0.8)
    pyplot.yticks(range(10,100,10))
    pyplot.ylim(25,95)
    pyplot.ylabel("Humidity (%)")

    pyplot.xticks([])
    pyplot.xlim(0,24)
    pyplot.grid()

    AbsHumidityAxes = HumidityAxes.twinx()
    AbsHumidityAxes.set_ylabel('Abs. Hum. (g/m^3)', color='b')
    pyplot.plot(times, data['AH'], 'bo', label="Abs. Hum.", mew=0, ms=3)
    pyplot.yticks(range(00,45,5))
    pyplot.ylim(7.5,22.5)

    pyplot.xticks(range(0,25,1))
    pyplot.xlim(0,24)
    pyplot.xlabel('Hours (HST)')


    TemperatureAxes = pyplot.axes([0.10, 0.05, 0.9, 0.35])
    pyplot.plot(times, data['temp1'], 'go', label="Termperature1", mew=0, ms=3)
    pyplot.plot(times, data['temp2'], 'bo', label="Termperature2", mew=0, ms=3)
    pyplot.plot(times, data['temp3'], 'ko', label="Termperature3", mew=0, ms=3)
    pyplot.xticks(range(0,25,1))
    pyplot.yticks(range(50,110,10))
    pyplot.xlim(0,24)
    pyplot.ylim(65,105)
    pyplot.xlabel('Hours (HST)')
    pyplot.ylabel("Temperature (F)")
    pyplot.grid()

    pyplot.savefig(PlotFile, dpi=dpi, bbox_inches='tight', pad_inches=0.10)
    logger.info("Done")


    ##-------------------------------------------------------------------------
    ## Create Daily Symlink if Not Already
    ##-------------------------------------------------------------------------
    LinkFileName = 'latest.png'
    LinkFile = os.path.join('/', 'home', 'joshw', 'logs', LinkFileName)
    if not os.path.exists(LinkFile):
        logger.info('Making {} symlink to {}'.format(LinkFile, PlotFile))
        os.symlink(PlotFile, LinkFile)
        logger.info("Done")


if __name__ == '__main__':

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
    parser.add_argument("-p", "--plot",
        action="store_true", dest="plot",
        default=False, help="Make plot.")
    args = parser.parse_args()

    if not args.plot:
        main(verbose=args.verbose)
    else:
        plot(verbose=args.verbose)
