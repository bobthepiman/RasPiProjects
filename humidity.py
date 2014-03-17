#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import sys
import os
import argparse
import math

##-------------------------------------------------------------------------
## Absolute Humidity from Relative Humidity
##-------------------------------------------------------------------------
def relative_to_absolute_humidity(T, RH):
    '''
    Absolute Humidity (grams/m3) = (6.112 x e^[(17.67 x T)/(T+243.5)] x 2.1674 x rh) / (273.15+T)
    This formula is accurate to within 0.1 % from -30 C to +35 C
    (from http://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/)
    '''
    AH = (6.112 * math.exp((17.67*T)/(T+243.5)) * 2.1674*RH) / (273.15+T)

    return AH


##-------------------------------------------------------------------------
## Absolute Humidity from dew Point
##-------------------------------------------------------------------------
def dew_point_to_absolute_humidity(T, DP):
    '''
    Calculates relative and absolute humidity values from the dew point and
    temperature.
    
    Uses formula from: 
    http://www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf
    '''
    T_C = float(T)     ## Temperature in degrees C
    Td_C = float(DP)   ## Dew point in degrees C
    T_K = T_C + 273.16        ## Temperature in Kelvin
    Td_K = Td_C + 273.16      ## Dew point in Kelvin

    ## - calculate RH from DewPt and Temperature
    ## - calculate Pws as function of Temperature
    ## - caluclate Pw from Pws and RH
    ## - calculate AH from Pw and Temperature
    ice = False
    if not ice:
        A = 6.116441   ## valid for water (not ice) between -20 and 50 C
        m = 7.591386   ## valid for water (not ice) between -20 and 50 C
        Tn = 240.7263  ## valid for water (not ice) between -20 and 50 C
    else:
        A = 6.114742   ## valid for ice between -70 and 0 C
        m = 9.778707   ## valid for ice between -70 and 0 C
        Tn = 273.1466  ## valid for ice between -70 and 0 C
    C = 2.16679    ## gK/J

    RH = 10**(m*( (Td_C/(Td_C+Tn)) - (T_C/(T_C+Tn)) ))
    if T_C < Td_C:
        RH = 1.0

    ## The following formula for Pws is lower accuracy, but used for the water
    ## vapour saturation pressure over water (and over ice)
    Pws = A * 10**(m*T_C/(T_C+Tn))*100  ## in Pa
    Pw = Pws*RH
    AH = C*Pw/T_K

    return RH*100, AH


##-------------------------------------------------------------------------
## Main Program
##-------------------------------------------------------------------------
def main():
    '''
    Calculates relative and absolute humidity values from the dew point and
    temperature.
    
    Uses formula from: 
    http://www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf
    '''

    ##-------------------------------------------------------------------------
    ## Parse Command Line Arguments
    ##-------------------------------------------------------------------------
    ## create a parser object for understanding command-line arguments
    parser = argparse.ArgumentParser(
             description="Program description.")
    ## add flags
    parser.add_argument("-i", "--ice",
        action="store_true", dest="ice",
        default=False, help="Use values for ice rather than water?")
    ## add arguments
    parser.add_argument("-T",
        type=float, dest="T_C",
        required=True,
        help="Air temperature in degrees C.")
    parser.add_argument("-D",
        type=float, dest="Td_C",
        required=False,
        help="Dew point in degrees C.")
    parser.add_argument("-H",
        type=float, dest="RH",
        required=False,
        help="Relative humidity in %")
    args = parser.parse_args()

    if args.Td_C and not args.RH:
        RH, AH = dew_point_to_absolute_humidity(args.T_C, args.Td_C)
        print("Temperature = {:.1f} F".format(args.T_C*9/5+32))
        print("Relative Humidity = {:.1f} %".format(RH))
        print("Absolute Humidity = {:.2f} g/m^3".format(AH))
    elif args.RH:
        AH = relative_to_absolute_humidity(args.T_C, args.RH)
        print("Temperature = {:.1f} F".format(args.T_C*9/5+32))
        print("Absolute Humidity = {:.2f} g/m^3".format(AH))
    else:
        print('Give either dew point (-D) or relative humidity (-H)')


if __name__ == '__main__':
    main()
