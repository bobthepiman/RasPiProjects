#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import logging
import subprocess
import datetime
import pytz
import ephem


##-------------------------------------------------------------------------
## Define Camera Class
##-------------------------------------------------------------------------
def Camera(object):
    '''Class representing the camera configuration
    '''
    def __init__(self, camera='Canon 5D',\
                 mode=None, aperture=None,\
                 exposure=None, ISO=None,\
                 port=None, logger=None):
        self.camera_type = camera
        self.mode = mode
        self.aperture = aperture
        self.exposure = exposure
        self.ISO = ISO
        self.port = port
        self.logger = logger
        ## Gphoto
        self.gphoto = 'sudo /sw/bin/gphoto2'
        ## Commands
        if self.camera_type == 'Canon 5D':
            self.imageformat_cmd = '/main/settings/imageformat'
            self.imageformat_list = {'RAW': '0'}
            self.focusmode_cmd = '/main/settings/focusmode'
            self.focusmode_list = {'manual': '3'}
            self.mode_cmd = ''
            self.mode_list = {'Av': 0,
                              'Tv': 0,
                              'M': 0}
            self.aperture_cmd = ''
            self.aperture_list = {'1.4': 0,
                                  '1.8': 0,
                                  '2.0': 0,
                                  '2.8': 0,
                                  '3.5': 0,
                                  '4.0': 0,
                                  '4.5': 0,
                                  '5.6': 0,
                                  '6.3': 0,
                                  '8.0': 0,
                                 }
            self.exposure_cmd = ''
            self.exposure_list = {}
            self.ISO_cmd = ''
            self.ISO_list = {'50': 0,
                             '100': 0,
                             '200': 0,
                             '800': 0,
                             '1600': 0,
                             '3200': 0,
                             '6400': 0,
                             '12800': 0}


    def set_image_format(self, format):
        assert format in self.imageformat_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.imageformat_cmd, self.imageformat_list[format])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def set_focus_mode(self, focusmode):
        assert focusmode in self.focusmode_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.focusmode_cmd, self.focusmode_list[focusmode])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def set_mode(self, mode):
        assert mode in self.mode_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.mode_cmd, self.mode_list[mode])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def set_aperture(self, aperture):
        assert aperture in self.aperture_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.aperture_cmd, self.aperture_list[aperture])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def set_exposure(self, exposure):
        assert exposure in self.exposure_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.exposure_cmd, self.exposure_list[exposure])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def set_ISO(self, ISO):
        assert ISO in self.ISO_list.keys()
        gphoto_command = '{} --port {} --set-config {}={}'.format(\
                          self.gphoto, self.port,\
                          self.ISO_cmd, self.ISO_list[exposure])
        result = subprocess.call(gphoto_command, shell=True)
        if self.logger: self.logger.debug(result)


    def take_exposure(self):
        pass


##-------------------------------------------------------------------------
## Time Lapse Program
##-------------------------------------------------------------------------
def time_lapse(port='usb:001,011'):
    logger = logging.getLogger('TimeLapseLogger')
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
    today = datetime.datetime.now().strftime('%Y%m%d')
    LogFileName = os.path.join('/', 'var', 'log', 'TimeLapse', 'log_{}.txt'.format(today))
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    logger.addHandler(LogFileHandler)


    ##-------------------------------------------------------------------------
    ## Use ephem to Calculate Sunrise, Sunset, Twilights
    ##-------------------------------------------------------------------------
    MLO = ephem.Observer()
    MLO.lon = "-155:34:33.9"
    MLO.lat = "+19:32:09.66"
    MLO.elevation = 3400.0
    MLO.temp = 10.0
    MLO.pressure = 680.0

    MKO = ephem.Observer()
    MKO.lon = "-155:28:33.7"
    MKO.lat = "+19:49:31.81"
    MKO.elevation = 4200.0
    MKO.temp = 1.0
    MKO.pressure = 625.0

    UTC = pytz.utc
    HST = pytz.timezone('Pacific/Honolulu')

    Observatory = MKO
    now = datetime.datetime.now(UTC)
    Observatory.date = now
    Observatory.date = datetime.datetime(2013, 8, 23, 8, 0, 0)
    the_Sun = ephem.Sun()
    the_Sun.compute(Observatory)

    if (the_Sun.alt < 0) and (now.astimezone(HST).hour < 12):
        today_noon = HST.localize(datetime.datetime(now.astimezone(HST).year, now.astimezone(HST).month, now.astimezone(HST).day-1, 12, 0, 0)).astimezone(UTC)
        Observatory.date = today_noon
    elif (the_Sun.alt < 0) and (now.astimezone(HST).hour >= 12):
        today_noon = HST.localize(datetime.datetime(now.astimezone(HST).year, now.astimezone(HST).month, now.astimezone(HST).day, 12, 0, 0)).astimezone(UTC)
        Observatory.date = today_noon

    Observatory.horizon = '0.0'
    sunset = UTC.localize(Observatory.next_setting(ephem.Sun()).datetime())
    sunrise = UTC.localize(Observatory.next_rising(ephem.Sun()).datetime())
    Observatory.horizon = '-6.0'
    civil_twilight_end = UTC.localize(Observatory.next_setting(ephem.Sun(), use_center=True).datetime())
    civil_twilight_begin = UTC.localize(Observatory.next_rising(ephem.Sun(), use_center=True).datetime())
    Observatory.horizon = '-12.0'
    nautical_twilight_end = UTC.localize(Observatory.next_setting(ephem.Sun(), use_center=True).datetime())
    nautical_twilight_begin = UTC.localize(Observatory.next_rising(ephem.Sun(), use_center=True).datetime())
    Observatory.horizon = '-18.0'
    astronomical_twilight_end = UTC.localize(Observatory.next_setting(ephem.Sun(), use_center=True).datetime())
    astronomical_twilight_begin = UTC.localize(Observatory.next_rising(ephem.Sun(), use_center=True).datetime())

    logger.info('Sunset:                      {}'.format(sunset.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Civil Twilight End:          {}'.format(civil_twilight_end.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Nautical Twilight End:       {}'.format(nautical_twilight_end.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Astronomical Twilight End:   {}'.format(astronomical_twilight_end.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Astronomical Twilight Begin: {}'.format(astronomical_twilight_begin.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Nautical Twilight Begin:     {}'.format(nautical_twilight_begin.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Civil Twilight Begin:        {}'.format(civil_twilight_begin.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))
    logger.info('Sunrise:                     {}'.format(sunrise.astimezone(HST).strftime('%Y/%m/%d %H:%M:%S HST')))

    sys.exit(0)

    ##-------------------------------------------------------------------------
    ## Configure Camera
    ##-------------------------------------------------------------------------
    cam = Camera(camera='Canon 5D', port=args.port, logger=logger)

    logger.info('Setting image format to RAW')
    cam.set_image_format('Raw')


    logger.info('Setting focus mode to manual')
    cam.set_focus_mode('manual')



    ##-------------------------------------------------------------------------
    ## Enter Main Time Lapse Loop
    ##-------------------------------------------------------------------------
    while True:
        now = datetime.datetime.now(tz=pytz.utc)

        if (now < sunset) or (now > sunrise):
            mode = 'Av'
            logger.info('It is day. Mode: {}'.format(mode))
            cam.set_mode(mode)
        elif (now > sunset) and (now < civil_twilight_end):
            mode = 'Av'
            logger.info('It is evening (civil) twilight. Mode = {}'.format(mode))
            cam.set_mode(mode)
        elif (now > civil_twilight_end) and (now < nautical_twilight_end):
            mode = 'Av'
            logger.info('It is evening (nautical) twilight. Mode = {}'.format(mode))
            cam.set_mode(mode)
        elif (now > nautical_twilight_end) and (now < astronomical_twilight_end):
            mode = 'M'
            aperture = '2.0'
            exposure = '20'
            ISO = 1600
            logger.info('It is evening (astronomical) twilight. Mode = {}. Av = {}. Tv = {}. ISO = {}.'.format(mode, aperture, exposure, iso))
            cam.set_mode(mode)
            cam.set_aperture(aperture)
            cam.set_exposure(exposure)
            cam.set_ISO(ISO)
        elif now > astronomical_twilight_end:
            mode = 'M'
            aperture = '2.0'
            exposure = '20'
            ISO = 1600
            logger.info('It is fully dark. Mode = {}. Av = {}. Tv = {}. ISO = {}.'.format(mode, aperture, exposure, iso))
            cam.set_mode(mode)
            cam.set_aperture(aperture)
            cam.set_exposure(exposure)
            cam.set_ISO(ISO)

        cam.take_exposure()


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
    ## add arguments
    parser.add_argument("--port",
        type=str, dest="port",
        help="The port (use 'sudo gphoto2 --auto-detect' to find port.")
    args = parser.parse_args()


    time_lapse(port=args.port)
