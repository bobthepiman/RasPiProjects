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
    def __init__(self, pin=18):
        self.temperature = None
        self.temperature_C = None
        self.temperature_F = None
        self.humidity = None
        self.time_struct = time.gmtime()
        self.pin = pin

    def time(self):
        return time.strftime('%Y/%m/%d %H:%M:%S UT', self.time_struct)

    def read(self):
        paths = [
                 os.path.join(os.path.expanduser('~'), 'bin', 'Adafruit-Raspberry-Pi-Python-Code'),
                 os.path.join(os.path.expanduser('~'), 'Adafruit-Raspberry-Pi-Python-Code'),
                 os.path.join(os.path.expanduser('~joshw'), 'bin', 'Adafruit-Raspberry-Pi-Python-Code'),
                 os.path.join(os.path.expanduser('~joshw'), 'Adafruit-Raspberry-Pi-Python-Code'),
                ]
        for trypath in paths:
            if os.path.exists(trypath):
                DHTexec = os.path.join(trypath, 'Adafruit_DHT_Driver', 'Adafruit_DHT')
        temp_match = None
        hum_match = None
        while not temp_match and not hum_match:
            try:
                self.time_struct = time.gmtime()
                output = subprocess.check_output([DHTexec, "2302", str(self.pin)])
            except subprocess.CalledProcessError as e:
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
        return self.temperature_C, self.temperature_F, self.humidity


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
