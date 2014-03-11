#!/usr/bin/env python
# encoding: utf-8
"""
untitled.py

Created by Josh Walawender on 2012-02-11.
Copyright (c) 2012 . All rights reserved.
"""

import sys
import os
import argparse
import serial
import re
import math
import numpy
import logging
import time
import datetime


##-------------------------------------------------------------------------
## Query AAG
##-------------------------------------------------------------------------
def QueryAAG(AAG, send, nResponses, logger):
    nBytes = nResponses*15
    ## Clear Response Buffer
    while AAG.inWaiting() > 0:
        logger.debug('Clearing Buffer: {0}'.format(AAG.read(1)))
    ## Send Query to Device
    AAG.write(send)
#     logger.debug("Waiting for response ...")
#     for i in range(0,20):
#         print(AAG.inWaiting())
#         if AAG.inWaiting() == 0:
#             time.sleep(0.2)
#         else:
#             break
    ## read Response
    logger.debug("Attempting to read response.")
    responseString = AAG.read(nBytes+15)
    ## Check for Hand Shaking Block
    HSBgood = re.match('!'+chr(17)+'\s{12}0', responseString[-15:])
    if not HSBgood:
        logger.debug("Handshaking Block Bad")
    ## Check that Response Matches Standard Pattern
    ResponsePattern = '(\![\s\w]{2})([\s\w]{12})'*nResponses
    ResponseREO = re.compile(ResponsePattern)
    ResponseMatch = ResponseREO.match(responseString[0:-15])
    if not ResponseMatch:
        logger.debug("Response does not match expected pattern: {}".format(responseString))
    ## return
    if HSBgood and ResponseMatch:
        ResponseArray = []
        for i in range(0,nResponses):
            ResponseArray.append([ResponseMatch.group(1), ResponseMatch.group(2)])
        return ResponseArray
    else:
        return None


##########################################################
##  Get Sky Temperature
def AAG_GetSkyTemp(AAG):
    SkyTempF = None
    AAG.write("S!")
    response = AAG.read(30)
    IsResponse = re.match("(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})", response)
    if IsResponse:
        if re.match("\!1", IsResponse.group(1)):
            SkyTempC = float(IsResponse.group(2))/100.
            SkyTempF = SkyTempC*1.8+32.
    return SkyTempF



##########################################################
##  Get Ambient Temperature
def AAG_GetAmbTemp(AAG):
    AmbTempF = None
    AAG.write("T!")
    response = AAG.read(30)
    IsResponse = re.match("(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})", response)
    if IsResponse:
        if re.match("\!2", IsResponse.group(1)):
            AmbTempC = float(IsResponse.group(2))/100.
            AmbTempF = AmbTempC*1.8+32.
    return AmbTempF


##########################################################
##  Get Values
def AAG_GetValues(AAG):
    Voltage = None
    LDR = None
    TRain = None
    ## Constants
    ZenerConstant = 3.
    LDRPullupResistance = 56.
    RainPullupResistance = 1.
    RainResAt25 = 1.
    RainBeta = 3450.
    AbsZero = 273.15
    ## Query Cloud Sensor
    AAG.write("C!")
    response = AAG.read(75)
    ThreeResponse = re.compile("(\![\s\w]{2})([\s\w]{11,13})(\![\s\w]{2})([\s\w]{11,13})(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})")
    IsResponse = ThreeResponse.match(response)
    MatchZV     = re.compile("\!6")
    MatchLDRV   = re.compile("\!4")
    MatchRST    = re.compile("\!5")
    if IsResponse:
        ## Zener Voltage Reading
        if MatchZV.match(IsResponse.group(1)):
            ZenerReading = float(IsResponse.group(2))
            Voltage = 1023. * ZenerConstant / ZenerReading
        ## LDR Value
        if MatchLDRV.match(IsResponse.group(3)):
            LDRvalue = float(IsResponse.group(4))
            LDRvalue = sorted([1, LDRvalue, 1022])[1]  ## restrict range of values to 1 - 1022
            LDR = LDRPullupResistance / (1023./LDRvalue - 1)
        ## Rain Sensor Temperature
        if MatchRST.match(IsResponse.group(5)):
            RSTvalue = float(IsResponse.group(6))
            RSTvalue = sorted([1, RSTvalue, 1022])[1]  ## restrict range of values to 1 - 1022
            R = RainPullupResistance / (1023./RSTvalue - 1)
            R = math.log(R / RainResAt25)
            TRain = 1 / (R/RainBeta + 1 / (AbsZero + 25)) - AbsZero
    return [Voltage, LDR, TRain]


##########################################################
##  Get PWM Value
def AAG_GetPWMvalue(AAG):
    AAG.write("Q!")
    response = AAG.read(30)
    MatchPWMDC  = re.compile("\!Q")
    OneResponse = re.compile("(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})")
    IsResponse = OneResponse.match(response)
    if IsResponse:
        if MatchPWMDC.match(IsResponse.group(1)):
            PWMvalue = float(IsResponse.group(2))*100./1023.
    return PWMvalue


##########################################################
##  Get Errors
def AAG_GetErrors(AAG):
    MatchError1 = re.compile("\!E1")
    MatchError2 = re.compile("\!E2")
    MatchError3 = re.compile("\!E3")
    MatchError4 = re.compile("\!E4")
    FourResponse  = re.compile("(\![\s\w]{2})([\s\w]{11,13})(\![\s\w]{2})([\s\w]{11,13})(\![\s\w]{2})([\s\w]{11,13})(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})")
    AAG.write("D!")
    response = AAG.read(75)
    IsResponse = FourResponse.match(response)
    if IsResponse:
        if MatchError1.match(IsResponse.group(1)):
            Error1 = int(IsResponse.group(2))
        if MatchError2.match(IsResponse.group(3)):
            Error2 = int(IsResponse.group(4))
        if MatchError3.match(IsResponse.group(5)):
            Error3 = int(IsResponse.group(6))
        if MatchError4.match(IsResponse.group(7)):
            Error4 = int(IsResponse.group(8))
    return [Error1, Error2, Error3, Error4]


##########################################################
##  Get PWM Value
def AAG_GetSwitch(AAG):
    Safe = None
    AAG.write("F!")
    response = AAG.read(30)
    MatchSafe   = re.compile("\!X")
    MatchUnSafe = re.compile("\!Y")
    OneResponse = re.compile("(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})")
    IsResponse = OneResponse.match(response)
    if IsResponse:
        if MatchSafe.match(IsResponse.group(1)):
            Safe = True
        if MatchUnSafe.match(IsResponse.group(1)):
            Safe = False
    return Safe
    
    
##########################################################
##  Get Wind
def AAG_GetWind(AAG):
    WindSpeed = None
    AAG.write("F!")
    response = AAG.read(30)
    OneResponse = re.compile("(\![\s\w]{2})([\s\w]{11,13})(\!.{12,15})")
    IsResponse = OneResponse.match(response)
    if IsResponse:
        if re.match("\!v", IsResponse.group(1)):
            SkyTempC = float(IsResponse.group(2))/100.



##########################################################
##  Get All Readings
def AAG_QueryAll(AAG, logger):
    ## Get nReadings
    nReadings = 15
    ClippingSigma = 2.0
    ClippingIterations = 2
    SkyTempF_array = []
    AmbTempF_array = []
    Voltage_array = []
    LDR_array = []
    TRain_array = []
    for i in range(0,nReadings,1):
        OneSkyTempF = AAG_GetSkyTemp(AAG)
        OneAmbTempF = AAG_GetAmbTemp(AAG)
        OneVoltage, OneLDR, OneTRain = AAG_GetValues(AAG)
        SkyTempF_array.append(OneSkyTempF)
        AmbTempF_array.append(OneAmbTempF)
        Voltage_array.append(OneVoltage)
        LDR_array.append(OneLDR)
        TRain_array.append(OneTRain)    
    for j in range(0,ClippingIterations, 1):
        SkyTempF_array = SigClip(SkyTempF_array, ClippingSigma)
        AmbTempF_array = SigClip(AmbTempF_array, ClippingSigma)
        Voltage_array  = SigClip(Voltage_array, ClippingSigma)
        LDR_array      = SigClip(LDR_array, ClippingSigma)
        TRain_array    = SigClip(TRain_array, ClippingSigma)
        SkyTempF = numpy.mean(SkyTempF_array)
        AmbTempF = numpy.mean(AmbTempF_array)
        Voltage  = numpy.mean(Voltage_array)
        LDR      = numpy.mean(LDR_array)
        TRain    = numpy.mean(TRain_array)

    PWMvalue = AAG_GetPWMvalue(AAG)
    Errors = AAG_GetErrors(AAG)
    Safe = AAG_GetSwitch(AAG)
    SafeDigit = 0
    if Safe: SafeDigit = 1

    logger.info("%7.2f (%5.1f %2d) %7.2f (%5.1f %2d) %7.2f (%5.1f %2d) %7.2f (%5.1f %2d) %7.2f (%5.1f %2d) %7d %5d" % (
                  SkyTempF, numpy.std(SkyTempF_array), len(SkyTempF_array),
                  AmbTempF, numpy.std(AmbTempF_array), len(AmbTempF_array),
                  Voltage, numpy.std(Voltage_array), len(Voltage_array),
                  LDR, numpy.std(LDR_array), len(LDR_array),
                  TRain, numpy.std(TRain_array), len(TRain_array),
                  PWMvalue, SafeDigit))

##########################################################
##  Sigma Clip an Array
def SigClip(Values, Sigma):
    Values = [val for val in Values if val]
    Values = numpy.array(Values)
    Mean = numpy.median(Values)
    StdDev = numpy.std(Values)
    if StdDev > Mean / 100.:
        ClippedValues = Values[(Values>Mean-Sigma*StdDev) & (Values<Mean+Sigma*StdDev)]
    else:
        ClippedValues = Values
    return ClippedValues


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
#     LogFileName = None
#     LogFileHandler = logging.FileHandler(LogFileName)
#     LogFileHandler.setLevel(logging.DEBUG)
#     LogFileHandler.setFormatter(LogFormat)
#     logger.addHandler(LogFileHandler)

    ##-------------------------------------------------------------------------
    ## Set up 
    ##-------------------------------------------------------------------------
    Continue = True
    now = datetime.datetime.utcnow()
    nowDecimal = now.hour + now.minute/60. + now.second/3600.
    DateString = "%04d%02d%02dUT" % (now.year, now.month, now.day)
    CloudSensorLogFile = "CloudSensorLog_"+DateString+".txt"
    CloudSensorLog = os.path.join("/Data", "CloudSensorLogs", CloudSensorLogFile)
    
    AAG = None
    SerialDevice = '/dev/ttyAMA0'
    try:
        AAG = serial.Serial(SerialDevice, 9600, timeout=2)
        logger.info("Connected to Cloud Sensor on {}".format(SerialDevice))
    except:
        logger.error("Unable to connect to AAG Cloud Sensor")
        
    if AAG:
        ## Get Ambient Temperature
        send = "!T"
        flag = "!2 "
        logger.info('Sending {} to Cloud Sensor.  Looking for {} back.'.format(send, flag))
        response = QueryAAG(AAG, send, 1, logger)
        if response:
            logger.debug('Response Recieved: {}{}'.format(response[0][0], response[0][1]))
            if response[0][0] == flag:
                AmbTempF = float(response[0][1])/100.*1.8+32.
                logger.info('Ambient Tmperature is {:.1f} deg F'.format(AmbTempF))
        else:
            logger.warning("No response recieved.")


        ## Get Sky Temperature
        send = "!S"
        flag = "!1 "
        logger.info('Sending {} to Cloud Sensor.  Looking for {} back.'.format(send, flag))
        response = QueryAAG(AAG, send, 1, logger)
        if response:
            logger.debug('Response Recieved: {}{}'.format(response[0][0], response[0][1]))
            if response[0][0] == flag:
                SkyTempF = float(response[0][1])/100.*1.8+32.
                logger.info('Sky Tmperature is {:.1f} deg F'.format(SkyTempF))
        else:
            logger.warning("No response recieved.")

        AAG.close()


if __name__ == '__main__':
    main()

