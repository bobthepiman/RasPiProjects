#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import os
import glob
import time
import subprocess
import re


##-----------------------------------------------------------------------------
## Define DHT22 object to hold information
##-----------------------------------------------------------------------------
class DHT22(object):
    _singletons = dict()

    def __new__(cls):
        if not cls in cls._singletons:
            cls._singletons[cls] = object.__new__(cls)
        return cls._singletons[cls]

    def __init__(self):
        self.temperature = None
        self.temperature_C = None
        self.temperature_F = None
        self.humidity = None
        self.time_struct = time.gmtime()

    def time(self):
        return time.strftime('%Y/%m/%d %H:%M:%S UT', self.time_struct)

    def read(self):
#         DHTexec = os.path.join('/', 'home', 'joshw', 'bin', \
#                                'Adafruit-Raspberry-Pi-Python-Code', \
#                                'Adafruit_DHT_Driver', 'Adafruit_DHT')
#         DHTexec = os.path.join('/usr', 'local', 'bin', 'Adafruit_DHT')
        DHTexec = os.path.join('Adafruit_DHT')
        temp_match = None
        hum_match = None
        while not temp_match and not hum_match:
            try:
                self.time_struct = time.gmtime()
                output = subprocess.check_output([DHTexec, "2302", "18"])
            except subprocess.CalledProcessError as e:
#                 print('Command: {}'.format(repr(e.cmd)))
#                 print('Returncode: {}'.format(e.returncode))
#                 print('Output: {}'.format(e.output))
                raise
            except:
                raise
            temp_match = re.search("Temp =\s+([0-9.]+)", output)
            hum_match = re.search("Hum =\s+([0-9.]+)", output)
            if temp_match:
                self.temperature_C = float(temp_match.group(1))
                self.temperature_F = 32. + 9./5.*self.temperature_C
                self.temperature = self.temperature_C
            else:
                self.temperature_C = None
                self.temperature_F = None
                self.temperature = None
            if hum_match:
                self.humidity = float(hum_match.group(1))
            else:
                self.humidity = None


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    sensor = DHT22()
    sensor.read()
    print('At {}'.format(sensor.time()))
    print('  Temperature = {:.3f} C, {:.3f} F'.format(sensor.temperature_C, sensor.temperature_F))
    print('  Humidity = {:.1f} %'.format(sensor.humidity))


if __name__ == '__main__':
    main()
