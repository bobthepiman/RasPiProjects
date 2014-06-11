#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import numpy as np
import datetime
import math

import RPi.GPIO as GPIO

import DHT22
import DS18B20
import Carriots
import humidity

import astropy.io.ascii as ascii
import astropy.table as table


temp_high = 42.0
temp_low = 38.0


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main(args):
#     temp_high = 42.0
#     temp_low = 38.0
    status = 'unknown'

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)

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

    try:
        logger.debug('Reading DHT22')
        DHT = DHT22.DHT22(pin=18)
        DHT.read()
        logger.debug('  Temperature = {:.3f} F, Humidity = {:.1f} %'.format(DHT.temperature_F, DHT.humidity))
        temperatures_F.append(DHT.temperature_F)
        RH = DHT.humidity
        AH = humidity.relative_to_absolute_humidity(DHT.temperature_C, DHT.humidity)
        logger.debug('  Absolute Humidity = {:.2f} g/m^3'.format(AH))
    except:
        RH = float('nan')
        AH = float('nan')


    logger.debug('Reading DS18B20')
    sensor = DS18B20.DS18B20()
    sensor.read()
    for temp in sensor.temperatures_C:
        logger.debug('  Temperature = {:.3f} F'.format(temp*9./5.+32.))
        temperatures_F.append(temp*9./5.+32.)


    ##-------------------------------------------------------------------------
    ## Record Values to Table
    ##-------------------------------------------------------------------------
    datafile = os.path.join('/', 'var', 'log', 'Kegerator', '{}.txt'.format(DateString))
    logger.debug("Preparing astropy table object for data file {}".format(datafile))
    if not os.path.exists(datafile):
        logger.info("Making new astropy table object")
        SummaryTable = table.Table(names=('date', 'time', 'AmbTemp', 'KegTemp', 'KegTemp1', 'KegTemp2', 'KegTemp3', 'RH', 'AH', 'status'), \
                                   dtype=('S10',  'S12',  'f4',      'f4',      'f4',       'f4',       'f4',       'f4', 'f4', 'S8') )
    else:
        logger.debug("Reading astropy table object from file: {0}".format(datafile))
        try:
            SummaryTable = ascii.read(datafile, guess=False,
                                      header_start=0, data_start=1,
                                      Reader=ascii.basic.Basic,
                                      converters={
                                      'date': [ascii.convert_numpy('S10')],
                                      'time': [ascii.convert_numpy('S12')],
                                      'AmbTemp': [ascii.convert_numpy('f4')],
                                      'KegTemp': [ascii.convert_numpy('f4')],
                                      'KegTemp1': [ascii.convert_numpy('f4')],
                                      'KegTemp2': [ascii.convert_numpy('f4')],
                                      'KegTemp3': [ascii.convert_numpy('f4')],
                                      'hum': [ascii.convert_numpy('f4')],
                                      'AH': [ascii.convert_numpy('f4')],
                                      'status': [ascii.convert_numpy('S11')],
                                      })
        except:
            logger.critical("Failed to read data file: {0} {1} {2}".format(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2]))


    ##-------------------------------------------------------------------------
    ## Turn Kegerator Relay On or Off Based on Temperature
    ##-------------------------------------------------------------------------
    temperatures_F.sort()
    ambient_temperature = temperatures_F.pop()
    assert ambient_temperature > max(temperatures_F)
    logger.info('Ambient Temperature = {:.1f}'.format(ambient_temperature))
    for temp in temperatures_F:
        logger.info('Kegerator Temperatures = {:.1f} F'.format(temp))
    temperature = np.median(temperatures_F)
    logger.info('Median Temperature = {:.1f} F'.format(temperature))
    if temperature > temp_high:
        status = 'On'
        logger.info('Temperature {:.1f} is greater than {:.1f}.  Turning freezer {}.'.format(temperature, temp_high, status))
        GPIO.output(23, True)
    elif temperature < temp_low:
        status = 'Off'
        logger.info('Temperature {:.1f} is less than {:.1f}.  Turning freezer {}.'.format(temperature, temp_low, status))
        GPIO.output(23, False)
    else:
        if len(SummaryTable) > 0:
            status = SummaryTable['status'][-1]
        else:
            status = 'unknown'
        logger.info('Temperature if {:.1f}.  Taking no action.  Status is {}'.format(temperature, status))


    ##-------------------------------------------------------------------------
    ## Add row to data table
    ##-------------------------------------------------------------------------
    logger.debug("Writing new row to data table.")
    while len(temperatures_F) < 4:
        temperatures_F.append(float('nan'))
    SummaryTable.add_row((DateString, TimeString, ambient_temperature, temperature, \
                          temperatures_F[0], temperatures_F[1], temperatures_F[2], \
                          RH, AH, status))
    ## Write Table to File
    logger.debug("  Writing new data file.")
    ascii.write(SummaryTable, datafile, Writer=ascii.basic.Basic)


    ##-------------------------------------------------------------------------
    ## Log to Carriots
    ##-------------------------------------------------------------------------
    logger.info('Sending Data to Carriots')
    logger.debug('  Creating Device object')
    Device = Carriots.Client(device_id="kegerator@joshwalawender")
    logger.debug('  Reading api key')
    Device.read_api_key_from_file(file=os.path.join(os.path.expanduser('~joshw'), '.carriots_api'))
    data_dict = {'Temperature': temperature, \
                 'Status': status
                 }
    logger.debug('  Data: {}'.format(data_dict))
    Device.upload(data_dict)

    logger.info('Done')



##-------------------------------------------------------------------------
## PLOT
##-------------------------------------------------------------------------
def plot(args):
    import matplotlib.pyplot as pyplot

    ##-------------------------------------------------------------------------
    ## Set date to tonight if not specified
    ##-------------------------------------------------------------------------
    now = datetime.datetime.now()
    DateString = now.strftime("%Y%m%d")
    if not args.date:
        args.date = DateString


    ##-------------------------------------------------------------------------
    ## Define File Names
    ##-------------------------------------------------------------------------
    LogFile = os.path.join('/', 'var', 'log', 'Kegerator', 'PlotLog_'+args.date+".txt")
    PlotFile = os.path.join('/', 'var', 'log', 'Kegerator', args.date+".png")
    DataFile = os.path.join('/', 'var', 'log', 'Kegerator', args.date+".txt")


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
    LogFileHandler = logging.FileHandler(LogFile)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    logger.addHandler(LogFileHandler)

    logger.info("Kegerator.py invoked with --plot option")
    logger.info("  Making plot for day of {}".format(args.date))


    ##-------------------------------------------------------------------------
    ## Read Data
    ##-------------------------------------------------------------------------
    if os.path.exists(DataFile):
        logger.info("  Found data file: {}".format(DataFile))
        data = ascii.read(DataFile, guess=False,
                          header_start=0, data_start=1,
                          Reader=ascii.basic.Basic,
                          converters={
                          'date': [ascii.convert_numpy('S10')],
                          'time': [ascii.convert_numpy('S12')],
                          'AmbTemp': [ascii.convert_numpy('f4')],
                          'KegTemp': [ascii.convert_numpy('f4')],
                          'KegTemp1': [ascii.convert_numpy('f4')],
                          'KegTemp2': [ascii.convert_numpy('f4')],
                          'KegTemp3': [ascii.convert_numpy('f4')],
                          'RH': [ascii.convert_numpy('f4')],
                          'AH': [ascii.convert_numpy('f4')],
                          'status': [ascii.convert_numpy('S11')],
                          })
        datetime_objects = [datetime.datetime.strptime(x['time'], '%H:%M:%S HST') for x in data]
        time_decimal = [(x.hour + x.minute/60. + x.second/3600.) for x in datetime_objects]
        DecimalTime = max(time_decimal)

    ##-------------------------------------------------------------------------
    ## Make Plot
    ##-------------------------------------------------------------------------
        plot_upper_temp = 45
        plot_lower_temp = 29
        pyplot.ioff()
        plotpos = [
                   [0.05, 0.59, 0.65, 0.40], [0.73, 0.59, 0.21, 0.40],\
                   [0.05, 0.52, 0.65, 0.07], [0.73, 0.52, 0.21, 0.07],\
                   [0.05, 0.25, 0.65, 0.24], [0.73, 0.25, 0.21, 0.24],\
                   [0.05, 0.05, 0.65, 0.18], [0.73, 0.05, 0.21, 0.18],\
                  ]
        if len(data) > 1:
            logger.info("  Generating plot {} ... ".format(PlotFile))
            dpi = 100
            pyplot.figure(figsize=(14,8), dpi=dpi)

            ## Plot Temperature for This Day
            logger.debug("  Rendering Temperature Plot.")
            TemperatureAxes = pyplot.axes(plotpos[0], xticklabels=[])
            pyplot.title("Kegerator Temperatures for "+args.date)
            pyplot.plot(time_decimal, data['KegTemp'], 'ko', label="Median Temp.", markersize=3, markeredgewidth=0)
            pyplot.plot(time_decimal, data['KegTemp1'], 'bo', label="Temp. 1", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot(time_decimal, data['KegTemp2'], 'go', label="Temp. 2", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot(time_decimal, data['KegTemp3'], 'yo', label="Temp. 3", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot([DecimalTime, DecimalTime], [-100,100], 'g-', alpha=0.4)
            pyplot.ylabel("Kegerator Temp. (F)")
            pyplot.xlim(0, 24)
            pyplot.xticks(np.arange(0,24,2))
            pyplot.ylim(plot_lower_temp, plot_upper_temp)
            pyplot.grid()
            pyplot.legend(loc='best', prop={'size': 10})
            TemperatureAxes.axhline(32, color='red', lw=4)
            TemperatureAxes.axhline(temp_low, color='blue', lw=4)
            TemperatureAxes.axhline(temp_high, color='blue', lw=4)

            ## Plot Temperature for Last Hour
            logger.debug("  Rendering Recent Temperature Plot.")
            RecentTemperatureAxes = pyplot.axes(plotpos[1], xticklabels=[], yticklabels=[])
            pyplot.title("Last Hour")
            pyplot.plot(time_decimal, data['KegTemp'], 'ko', label="Kegerator Temp", markersize=3, markeredgewidth=0)
            pyplot.plot(time_decimal, data['KegTemp1'], 'bo', label="Kegerator Temp 1", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot(time_decimal, data['KegTemp2'], 'go', label="Kegerator Temp 2", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot(time_decimal, data['KegTemp3'], 'yo', label="Kegerator Temp 3", markersize=2, markeredgewidth=0, alpha=0.6)
            pyplot.plot([DecimalTime, DecimalTime], [-100,100], 'g-', alpha=0.4)
            pyplot.xticks(np.arange(0,24,0.25))
            if DecimalTime > 1.0:
                pyplot.xlim(DecimalTime-1.0, DecimalTime+0.1)
            else:
                pyplot.xlim(0,1.1)
            pyplot.ylim(plot_lower_temp, plot_upper_temp)
            pyplot.grid()
            RecentTemperatureAxes.axhline(32, color='red', lw=4)
            RecentTemperatureAxes.axhline(temp_low, color='blue', lw=4)
            RecentTemperatureAxes.axhline(temp_high, color='blue', lw=4)

            ## Plot Relay State
            translator = {'On': 1, 'Off': 0, 'unknown': -0.25}
            relay_state = [translator[val] for val in data['status']]
            logger.debug("  Rendering Relay Status Plot.")
            RelayAxes = pyplot.axes(plotpos[2], yticklabels=[])
            pyplot.plot(time_decimal, relay_state, 'ko-', markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [-1,2], 'g-', alpha=0.4)
            pyplot.ylabel("Relay")
            pyplot.xlim(0, 24)
            pyplot.yticks([0,1])
            
            pyplot.ylim(-0.5,1.5)
            pyplot.xticks(np.arange(0,24,2))
            pyplot.grid()

            ## Plot Relay State for Last Hour
            logger.debug("  Rendering Recent Relay State Plot.")
            RecentRelayAxes = pyplot.axes(plotpos[3], yticklabels=[])
            pyplot.plot(time_decimal, relay_state, 'ko-', markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [-1,2], 'g-', alpha=0.4)
            pyplot.xticks(np.arange(0,24,0.25))
            if DecimalTime > 1.0:
                pyplot.xlim(DecimalTime-1.0, DecimalTime+0.1)
            else:
                pyplot.xlim(0,1.1)
            pyplot.yticks([0,1])
            pyplot.ylim(-0.5,1.5)
            pyplot.grid()


            ## Plot Humidity for This Day
            HumidityAxes = pyplot.axes(plotpos[4], xticklabels=[])
            logger.debug("  Rendering Humidity Plot.")
            pyplot.plot(time_decimal, data['RH'], 'bo', label="Humidity", markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [0,100], 'g-', alpha=0.4)
            pyplot.ylabel("Humidity (%)")
            pyplot.xlabel("Time (Hours HST)")
            pyplot.xlim(0, 24)
            pyplot.ylim(30,100)
            pyplot.xticks(np.arange(0,24,2))
            pyplot.grid()

            ## Plot Humidity for Last 2 Hours
            logger.debug("  Rendering Recent Humidity Plot.")
            RecentHumidityAxes = pyplot.axes(plotpos[5], yticklabels=[], xticklabels=[])
            pyplot.plot(time_decimal, data['RH'], 'bo', label="Humidity", markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [0,100], 'g-', alpha=0.4)
            pyplot.xticks(np.arange(0,24,0.25))
            if DecimalTime > 1.0:
                pyplot.xlim(DecimalTime-1.0, DecimalTime+0.1)
            else:
                pyplot.xlim(0,1.1)
            pyplot.ylim(30,100)
            pyplot.grid()

            ## Plot Case Temperature for This Day
            logger.debug("  Rendering Case Temperature Plot.")
            AmbTemperatureAxes = pyplot.axes(plotpos[6])
            pyplot.plot(time_decimal, data['AmbTemp'], 'ro', label="Ambient Temp", markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [-100,100], 'g-', alpha=0.4)
            pyplot.ylabel("Case Temp. (F)")
            pyplot.xlim(0, 24)
            pyplot.xticks(np.arange(0,24,2))
            pyplot.yticks(np.arange(60,100,5))
            pyplot.ylim(math.floor(min(data['AmbTemp'])-6), math.ceil(max(data['AmbTemp'])+6))
            pyplot.grid()

            ## Plot Case Temperature for Last Hour
            logger.debug("  Rendering Recent Case Temperature Plot.")
            RecentAmbTemperatureAxes = pyplot.axes(plotpos[7], yticklabels=[])
            pyplot.plot(time_decimal, data['AmbTemp'], 'ro', label="Ambient Temp", markersize=3, markeredgewidth=0)
            pyplot.plot([DecimalTime, DecimalTime], [-100,100], 'g-', alpha=0.4)
            pyplot.xticks(np.arange(0,24,0.25))
            pyplot.yticks(np.arange(60,100,5))
            pyplot.ylim(math.floor(min(data['AmbTemp'])-6), math.ceil(max(data['AmbTemp'])+6))
            if DecimalTime > 1.0:
                pyplot.xlim(DecimalTime-1.0, DecimalTime+0.1)
            else:
                pyplot.xlim(0,1.1)
            pyplot.grid()

            logger.debug("  Saving plot to file: {}".format(PlotFile))
            pyplot.savefig(PlotFile, dpi=dpi, bbox_inches='tight', pad_inches=0.05)
            logger.info("  done.")
    else:
        logger.info("Could not find data file: {}".format(DataFile))

    ##-------------------------------------------------------------------------
    ## Create Daily Symlink if Not Already
    ##-------------------------------------------------------------------------
    LinkFileName = 'latest.png'
    LinkFile = os.path.join('/', 'var', 'log', 'Kegerator', LinkFileName)
    if not os.path.exists(LinkFile):
        logger.info('Making {} symlink to {}'.format(LinkFile, PlotFile))
        os.symlink(PlotFile, LinkFile)
        logger.info("Done")





if __name__ == '__main__':
    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    parser = argparse.ArgumentParser(
             description="Program description.")
    parser.add_argument("-v", "--verbose",
        action="store_true", dest="verbose",
        default=False, help="Be verbose! (default = False)")
    parser.add_argument("-p", "--plot",
        action="store_true", dest="plot",
        default=False, help="Make plot.")
    parser.add_argument("-d", "--date",
        dest="date", required=False, default="", type=str,
        help="Date to analyze. (i.e. '20130805')")
    args = parser.parse_args()

    if not args.plot:
        main(args)
    else:
        plot(args)
