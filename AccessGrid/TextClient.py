#-----------------------------------------------------------------------------
# Name:        TextClient.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClient.py,v 1.4 2003-03-27 20:24:56 judson Exp $
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
 
class SimpleTextProcessor:
    def __init__(self, socket, venueId, callback):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOutCallback = callback
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

        logname = "TextClient.log"
        hdlr = logging.handlers.RotatingFileHandler(logname, "a", 10000000, 0)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(fmt)
        
        self.log = logging.getLogger("AG.TextClient")
        self.log.addHandler(hdlr)
        self.log.setLevel(logging.DEBUG)
        self.log.info("--------- START TextClient")

        self.outputThread = Thread(target = self.ProcessNetwork)
        self.outputThread.start()

    def Stop(self):
        self.log.debug("Stop")
        self.running = 0
        self.outputThread = 0
        
    def Input(self, event):
        """ """
        self.log.debug("EVENT --- Input")
        self.log.debug("%s", event)
        
        # the exception should be caught in UI not here.
        try: 
            pdata = pickle.dumps(event)
            lenStr = "%s\n" % len(pdata)
            self.wfile.write(lenStr)
            self.wfile.write(pdata)
        except:
            self.log.debug("in except")
           
    def Output(self, text):
        """ """
        data = text.data

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

        self.textOutCallback(string)

    def ProcessNetwork(self):
        """ """
        self.log.debug("Process network")
        self.running = 1
        while self.running:
            str = self.rfile.readline()
            self.log.debug("READ /%s/ from network.", str)
            size = int(str)
            pdata = self.rfile.read(size, size)
            event = pickle.loads(pdata)
            self.Output(event.data)

        self.socket.close()
