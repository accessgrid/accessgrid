#-----------------------------------------------------------------------------
# Name:        TextClient.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClient.py,v 1.1 2003-03-19 20:45:51 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import pickle
import string
import logging

from threading import Thread

from pyGlobus.io import GSITCPSocket
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.Events import ConnectEvent, TextEvent
 
from wxPython.wx import *

class SimpleTextProcessor:
    def __init__(self, socket, venueId, textOut):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOut = textOut
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

        self.outputThread = Thread(target = self.ProcessNetwork)
        self.outputThread.start()

        self.localEcho = 0
        self.__setLogger()
      
    def __setLogger(self):
        logger = logging.getLogger("AG.TextClient")
        logger.setLevel(logging.DEBUG)
        logname = "TextClient.log"
        hdlr = logging.handlers.RotatingFileHandler(logname, "a", 10000000, 0)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(fmt)
        logger.addHandler(hdlr)
        self.log = logging.getLogger("AG.TextClient")
        self.log.info("--------- START TextClient")

    def LocalEcho(self):
        self.log.debug("Local echo")
        self.localEcho =~ self.localEcho
        
    def Stop(self):
        self.log.debug("Stop")
        self.running = 0
        self.outputThread = 0
        
    def Input(self, event):
        """ """
        self.log.debug("EVENT --- Input")
        if self.localEcho:
            self.log.debug("Raw output:%s"%event.data.data)
            self._RawOutput(event.data.data + '\n')

        # the exception should be caught in UI not here.
        # try: 
        self.log.debug("In try statement")
        pdata = pickle.dumps(event)
        lenStr = "%s\n" % len(pdata)
        self.wfile.write(lenStr)
        self.wfile.write(pdata)
        # except:
        #     pass
           
    def Output(self, text):
        """ """
        data = text.data

        #        print "TS: %s GDI: %s" % (text.sender, GetDefaultIdentityDN())
        if text.sender == GetDefaultIdentityDN():
            string = "You say, \"%s\"\n" % (data)
        elif text.sender != None:
            name = text.sender
            stuff = name.split('/')
            for s in stuff[1:]:
                (k,v) = s.split('=')
                if k == 'CN':
                    name = v
            string = "%s says, \"%s\"\n" % (name, data)
        else:
            string = "Someone says, \"%s\"\n" % (data)

        self._RawOutput(string)

    def _RawOutput(self, string):
        try:
            self.log.debug("Raw output:%s" %string)
            wxCallAfter(self.textOut.AppendText, string)
        except:
            self.log.debug("except in _RawOutput - stop text client")
            self.Stop()
        
    def ProcessNetwork(self):
        """ """
        self.log.debug("Process network")
        self.running = 1
        while self.running:
            str = self.rfile.readline()
            size = int(str)
            pdata = self.rfile.read(size, size)
            event = pickle.loads(pdata)
            self.Output(event.data)

