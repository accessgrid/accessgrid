#-----------------------------------------------------------------------------
# Name:        TextClient.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClient.py,v 1.13 2003-05-08 22:02:56 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import pickle
import logging
import struct

from threading import Thread

from pyGlobus.io import GSITCPSocket, IOBaseException
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth

class TextClientConnectException(Exception):
    """
    This gets returned when a connect fails.
    """
    pass

class TextClientReadDataException(Exception):
    """
    This exception is used to indicate a read error.

    This is usually thrown when an IOBaseException has occured on the
    underlying GSITCPSocket. It can also be thrown if the read succeeds,
    but the data resulting is bad.
    """
    pass

class TextClientWriteDataException(Exception):
    """
    This exception is used to indicate a write error.

    This is usually thrown when an IOBaseException has occured on the
    underlying GSITCPSocket.
    """
    pass

class TextClientBadDataException(Exception):
    """
    This exception is used to indicate bad data has been received.

    This is usually thrown when an EOFError has occured on during unpickling.
    """
    pass

class SimpleTextProcessor:
    def __init__(self, socket, venueId, callback):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOutCallback = callback
        self.wfile = self.socket.makefile('wb', 0)
        self.rfile = self.socket.makefile('rb', -1)

        self.log = logging.getLogger("AG.TextClient")
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
            # Pickle the data
            pdata = pickle.dumps(event)
            size = struct.pack("i", len(pdata))
            # Send the size as 4 bytes
            self.wfile.write(size)
            # Send the pickled event data
            self.wfile.write(pdata)
        except:
            self.log.exception("SimpleTextProcessor: Filed to write data")
            raise TextClientWriteDataException
        
    def Output(self, text):
        """ """
        data = text.data

        if text.sender == GetDefaultIdentityDN():
            string = "You say, \"%s\"\n" % (data)
        elif text.sender != None:
            name = text.sender
            stuff = name.split('/')
            for s in stuff[1:]:
                if len(s):
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
            try:
                data = self.rfile.read(4)
                self.log.debug("TextClient: Read data(%s)", data)
            except IOBaseException:
                data = None
                self.running = 0
                self.log.exception("TextClient: Read data failed.")
                raise TextClientReadDataException
            
            if data != None and len(data) == 4:
                sizeTuple = struct.unpack('i', data)
                size = sizeTuple[0]
                self.log.debug("Unpacked %d", size)
            else:
                self.log.exception("TextClient: Read data failed.")
                raise TextClientReadDataException
            
            try:
                pdata = self.rfile.read(size)
                self.log.debug("TextClient: Read data.")
            except:
                self.running = 0
                self.log.exception("TextClient: Read data failed.")
                raise TextClientReadDataException

            # Unpickle the data
            try:
                event = pickle.loads(pdata)
            except EOFError, e:
                self.running = 0
                log.exception("TextClient: unpickle got EOF.")
                raise TextClientBadDataException

            # Handle the data
            self.Output(event.data)
            
        self.socket.close()
