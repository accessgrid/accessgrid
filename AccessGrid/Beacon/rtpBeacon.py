#!/usr/bin/python2
#----------------------------------------------------------------------------
# Name:        rtpbeacon.py
# Purpose:     This program runs as a service to provide multicast
#              information on multicast connectivity.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeacon.py,v 1.1 2005-06-22 22:40:19 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------
"""
The beacon is designed to provide multicast connectivity information.
This is done by sending at a prescribed interval a short message via
RTP (a plain text string as it were). Then the normal RTP statistics
communicated via RTCP are used to track the performance of the group.
"""

__revision__ = "$Id: rtpBeacon.py,v 1.1 2005-06-22 22:40:19 lefvert Exp $"

import os, sys, signal, optparse, time, random, threading, copy
import logging, logging.handlers

import common
from common import common
from common.RTPBeacon import RTPBeacon, RTPBeaconFileConfig, RTPBeaconRegConfig
from rtpBeaconUI import BeaconFrame
        
class Beacon:
    def __init__(self, log = None, config = None):
        ''' Initalize parameters '''
        self.__config = None
        self.__log = log
        self.__rtpbeacon = None
        
        if config:
            self.__config = RTPBeaconFileConfig(config)
        else:
            if sys.platform == 'win32':
                self.__config = RTPBeaconRegConfig()
            else:
                self.__config = RTPBeaconFileConfig()
                        
        # Convert all values to strings (otherwise unicode on Windows)
        for option in self.__config.GetKeys():
            self.__config.configData[option] = str(self.__config.configData[option])

    def Start(self):
        ''' Start the beacon '''
        self.__rtpbeacon = RTPBeacon(config=self.__config, log=self.__log)
        self.__rtpbeacon.Start()
        self.__sdes = {} # key ssrc, value sdes
        self.__sources = [] # ordered list of source numbers
        self.__rtpbeacon.sensor.handlerDict[3] = self.ReceiveSDES
     
    def Stop(self):
        ''' Stop the beacon '''
        self.__rtpbeacon.Stop()
     
    def SetConfigData(self, key, value):
        ''' Set beacon configuration data'''
        self.__config.configData[key] = str(value)

    def GetConfigData(self, key):
        ''' Get beacon configuration data '''
        if self.__config.configData.has_key(key):
            return self.__config.configData[key]

    def GetSources(self):
        '''Get dictionary of sources and sdes values.'''
        return self.__sources[0:10]

    def GetSdes(self, ssrc):
        ''' Get sdes information for given source '''
        if self.__sdes.has_key(ssrc):
            return self.__sdes[ssrc]
        else:
            return None

    def GetMySSRC(self):
        ''' Get my ssrc number '''
        self.__rtpbeacon.sensor.GetSSRC()

    def GetReport(self, ssrc1, ssrc2):
        ''' Get receiver report '''
        return self.__rtpbeacon.sensor.session.get_rr(ssrc2, ssrc1)
        
    def ReceiveSDES(self, session, event):
        ''' Handler for SDES update events. '''
        sdestype, sdes = common.make_sdes_item(event.data)

        # make sure the sources list is ordered.
        if event.ssrc not in self.__sources:
            self.__sources.append(event.ssrc)
               
        if sdestype == 2:
            self.__sdes[event.ssrc] = sdes

                
if __name__ == "__main__":
    from wxPython.wx import *
   
    # Parse command line options
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", metavar="LEVEL",
                      type="int", default=20,
                      help="Specify the verbosity level, 2 dumps rtp data as well.")
    parser.add_option("-c", "--config", dest="config", metavar="CONFIG",
                      default=None,
                      help="Specify the filename of a config file.")
    
    options, args = parser.parse_args()
    
    # Create the logging solution
    log = logging.getLogger("RTPBeacon")
    
    if options.verbose <= logging.DEBUG: 
        hdlr = logging.StreamHandler()
    else:
        if sys.platform == 'win32':
            hdlr = logging.handlers.NTEventLogHandler("RTPBeacon")
        else:
            hdlr = logging.handlers.RotatingFileHandler("Beacon.log")
            
    fmt = '%(asctime)s %(filename)s %(lineno)d '
    hdlr.setFormatter(logging.Formatter(fmt + '%(message)s'))
    log.addHandler(hdlr)
    log.setLevel(options.verbose)

    beacon = Beacon(log, options.config)
    beacon.SetConfigData('user', 'Susanne')
    beacon.SetConfigData('groupAddress', '233.4.200.19' )#19')
    beacon.SetConfigData('groupPort', '10002')
    beacon.SetConfigData('reportInterval', '86400')
    beacon.Start()
       
    # Create the user interface
    app = wxPySimpleApp()
    frame = BeaconFrame(None, sys.stdout, beacon)
    app.MainLoop()

    beacon.Stop()
