#!/usr/bin/python2
#----------------------------------------------------------------------------
# Name:        rtpbeacon.py
# Purpose:     This program runs as a service to provide multicast
#              information on multicast connectivity.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: rtpBeacon.py,v 1.6 2006-01-25 22:18:13 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#----------------------------------------------------------------------------
"""
The beacon is designed to provide multicast connectivity information.
This is done by sending at a prescribed interval a short message via
RTP (a plain text string as it were). Then the normal RTP statistics
communicated via RTCP are used to track the performance of the group.
"""

__revision__ = "$Id: rtpBeacon.py,v 1.6 2006-01-25 22:18:13 turam Exp $"

import os, sys, signal, optparse, time, random, threading, copy
import logging, logging.handlers

import common
from common import common
from common.RTPBeacon import RTPBeacon, RTPBeaconConfig
from rtpBeaconUI import BeaconFrame
        
class Beacon:
    def __init__(self, log = None, config = None):
        ''' Initalize parameters '''
        self.log = log
        self.__config = config
        if not self.__config:
            self.__config = RTPBeaconConfig()
        self.__rtpbeacon = None
        
        self.__sdes = {} # key ssrc, value sdes
        self.__sources = [] # ordered list of source numbers

    def Update(self):
        self.__rtpbeacon.sensor.Update()
       
    def Start(self):
        ''' Start the beacon '''
        self.__sdes = {} # key ssrc, value sdes
        self.__sources = [] # ordered list of source numbers

        self.__rtpbeacon = RTPBeacon(config=self.__config)
        self.__rtpbeacon.Start()
        self.__rtpbeacon.sensor.handlerDict[3] = self.ProcessSDES
        self.__rtpbeacon.sensor.handlerDict[4] = self.ProcessBye
        self.__rtpbeacon.sensor.handlerDict[6] = self.ProcessSourceDeleted
        
        # don't honor timeouts for now, not sure they can be trusted
        #self.__rtpbeacon.sensor.handlerDict[10] = self.ProcessTimeout
    
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
        return self.__sources

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
        
    def ProcessSDES(self, session, event):
        ''' Handler for SDES update events. '''
        sdestype, sdes = common.make_sdes_item(event.data)

        # make sure the sources list is ordered.
        if event.ssrc not in self.__sources:
            self.__sources.append(event.ssrc)
               
        if sdestype == 2:
            self.__sdes[event.ssrc] = sdes
            
    def ProcessSourceDeleted(self, session, event):
        self.__RemoveSource(session,event.ssrc)
        
    def ProcessTimeout(self, session, event):
        self.__RemoveSource(session,event.ssrc)

    def ProcessBye(self,session,event):
        self.__RemoveSource(session,event.ssrc)
    
    def __RemoveSource(self,session,ssrc):
        if ssrc in self.__sources:
            self.__sources.remove(ssrc)
        if ssrc in self.__sdes.keys():
            del self.__sdes[ssrc]
            
                
if __name__ == "__main__":
    from wxPython.wx import *
    from common.RTPBeacon import RTPBeaconFileConfig
   
    # Parse command line options
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", metavar="LEVEL",
                      type="int", default=20,
                      help="Specify the verbosity level, 2 dumps rtp data as well.")
    parser.add_option("-c", "--config", dest="config", metavar="CONFIG",
                      default=None,
                      help="Specify the filename of a config file.")
    parser.add_option("-u", "--user", dest="user", metavar="USER",
                      default='ag user',
                      help="Specify the name of the user running the beacon.")
    
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

    config = None
    if options.config:
        config = RTPBeaconFileConfig(options.config)

    beacon = Beacon(log, config)
    beacon.SetConfigData('user', options.user)
    beacon.SetConfigData('groupAddress', '233.4.200.18')#19')
    beacon.SetConfigData('groupPort', '10002')
    beacon.SetConfigData('reportInterval', '86400')
    beacon.Start()
       
    # Create the user interface
    app = wxPySimpleApp()
    frame = BeaconFrame(None, log, beacon)
    app.MainLoop()

    beacon.Stop()
