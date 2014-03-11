#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import os
import glob
import time
import argparse
import subprocess
import re


##-----------------------------------------------------------------------------
## Define DS18B20 object to hold information
##-----------------------------------------------------------------------------
class DS18B20(object):
    _singletons = dict()

    def __new__(cls):
        if not cls in cls._singletons:
            cls._singletons[cls] = object.__new__(cls)
        return cls._singletons[cls]

    def __init__(self):
        self.temperatures = []
        self.temperatures_C = []
        self.temperatures_F = []
        self.time_struct = time.gmtime()

    def time(self):
        return time.strftime('%Y/%m/%d %H:%M:%S UT', self.time_struct)

    def read(self):
        self.temperatures = []
        self.temperatures_C = []
        self.temperatures_F = []
        paths = glob.glob('/sys/bus/w1/devices/28-*')
        if len(paths) == 0:
            print('Warning: No devices found!')
            print('Check to make sure you have run:')
            print('sudo modprobe w1-gpio')
            print('sudo modprobe w1-therm')
        for path in paths:
            file = os.path.join(path, 'w1_slave')
            if os.path.exists(file):
                sensorFO = open(file, 'r')
                sensor_file_contents = sensorFO.readlines()
                sensorFO.close()
                MatchObj = re.search('t=(\d{1,6})', sensor_file_contents[1])
                if MatchObj:
                    temp = float(MatchObj.group(1))/1000
                    self.temperatures.append(temp)
                    self.temperatures_C.append(temp)
                    self.temperatures_F.append(temp*9./5.+32.)
                    self.time_struct = time.gmtime()


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    sensor = DS18B20()
    sensor.read()
    print('At {}'.format(sensor.time()))
    for temp in sensor.temperatures_C:
        print('  Temperature = {:.3f} C, {:.3f} F'.format(temp, temp*9./5.+32.))


if __name__ == '__main__':
    main()
