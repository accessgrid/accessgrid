#-----------------------------------------------------------------------------
# Name:        TextClient.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClient.py,v 1.16 2003-05-22 20:15:47 olson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
import pickle
import logging
import struct

log = logging.getLogger("AG.TextClient")

from threading import Thread

from pyGlobus.io import GSITCPSocket, IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc

from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN

from AccessGrid.Utilities import formatExceptionInfo

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
    def __init__(self, socket, venueId, callback, useThread = 0):
        """ """
        self.socket = socket
        self.venueId = venueId
        self.textOutCallback = callback
        self.wfile = self.socket.makefile('wb', 0)

        self.log = logging.getLogger("AG.TextClient")
        self.log.setLevel(logging.DEBUG)
        self.log.info("--------- START TextClient")

        if useThread:

            self.outputThread = Thread(target = self.ProcessNetwork)
            self.outputThread.start()

        else:
            self.InitAsynchIO()

    def Stop(self):
        self.wfile.close()
        self.log.debug("Stop")
        self.running = 0
        self.outputThread = 0

    def Input(self, event):
        """ """
        self.log.debug("EVENT --- Input")
        self.log.debug(str(event))
        
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
      
        # The check is now made in the ui.
        
        #if text.sender == GetDefaultIdentityDN():
        #    string = "You say, \"%s\"\n" % (data)
        #elif text.sender != None:
        #    name = text.sender
        #    stuff = name.split('/')
        #    for s in stuff[1:]:
        #        if len(s):
        #            (k,v) = s.split('=')
        #            if k == 'CN':
        #                name = v
        #                string = "%s says, \"%s\"\n" % (name, data)
        #            else:
        #                string = "Someone says, \"%s\"\n" % (data)

        # Added sender to the string.
        self.textOutCallback(text)

    def InitAsynchIO(self):
        """
        Initialize for using asynchronous IO for reading data from the network.
        """

        self.bufsize = 4096
        self.buffer = Buffer(self.bufsize)
        self.dataBuffer = ''
        self.waitingLen = 0

        h = self.socket.register_read(self.buffer, self.bufsize, 1, self.readCallbackWrap, None)

        log.debug("register returns %s", h)
        self.cbHandle = h

    def readCallbackWrap(self, arg, handle, ret, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """

        try:
            return self.readCallback(arg, handle, ret, buf, n)
        except Exception, e:
            log.exception("readcallback failed")

    def readCallback(self, arg, handle, ret, buf, n):

        log.debug("Got read handle=%s ret=%s  n=%s \n", handle, ret, n)

        if n == 0:
            log.debug("TextClient: asynch read gets n=0, EOF")
            self.running = 0
            return

        dstr = str(buf)
        self.dataBuffer += dstr

        if self.waitingLen == 0:

            sz = struct.calcsize('i')
            
            if len(self.dataBuffer) < sz:
                return

            lenstr = self.dataBuffer[:sz]
            dlen = struct.unpack('i', lenstr)
            log.debug("Data len %s", dlen)

            self.dataBuffer = self.dataBuffer[sz:]

            self.waitingLen = dlen[0]

        if len(self.dataBuffer) >= self.waitingLen:
            log.debug("finally read enough data, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata)

            self.waitingLen = 0
            
        h = self.socket.register_read(self.buffer, self.bufsize, 1,
                                    self.readCallbackWrap, None)
        log.debug("register returns %s", h)
        self.cbHandle = h

    def ProcessNetwork(self):
        """ """

        self.rfile = self.socket.makefile('rb', -1)
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

            self.handleData(pdata)

        self.socket.close()

    def handleData(self, pdata):

        # Unpickle the data
        try:
            event = pickle.loads(pdata)
        except EOFError, e:
            self.running = 0
            log.exception("TextClient: unpickle got EOF.")
            raise TextClientBadDataException

        # Handle the data
        self.Output(event.data)

