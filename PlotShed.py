#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import time
import matplotlib.pyplot as pyplot

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
    main()
