#-----------------------------------------------------------------------------
# Name:        TextClient.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/01/02
# RCS-ID:      $Id: TextClient.py,v 1.19 2003-08-28 18:02:46 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import pickle
import logging
import struct

from AccessGrid.Events import Event, HeartbeatEvent, ConnectEvent
from AccessGrid.Events import DisconnectEvent, ClientExitingEvent, TextEvent

from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth
from AccessGrid.hosting.pyGlobus.Utilities import GetHostname

from pyGlobus.io import GSITCPSocket, IOBaseException
from pyGlobus.util import Buffer
from pyGlobus import ioc

class SimpleTextProcessor:
    def __init__(self, myProfile=None, textConnection=None,
                 outputCallback=None):
        self.profile = myProfile
        self.textConnection = textConnection
        self.outputCallback = outputCallback
        self.log = logging.getLogger("AG.TextClient.SimpleTextProcessor")
        
    def SetProfile(self, profile):
        """
        """
        self.profile = profile

    def SetTextConnection(self, textConnection):
        """
        """
        self.textConnection = textConnection
        
    def RegisterOutputCallback(self, callback):
        self.outputCallback = callback
        
    def Input(self, event):
        """
        """
        self.textConnection.Write(event)
        
    def Output(self, textPayload):
        """
        method to process output, then pass it out the the UI.
        """
        message, profile = textPayload.data
        
        textMessage = ''

        if profile.name == self.profile.name:
            textMessage = "You say, \"%s\"\n" % message
        elif textPayload.sender != None:
            textMessage = "%s says, \"%s\"\n" % (profile.name, message)
        else:
            textMessage = "Someone says, \"%s\"\n" % message
            self.log.info("Received text without a sender, ERROR!")
            
        if self.outputCallback != None:
            self.outputCallback(textMessage)
        else:
            self.log("TextClientSimpleTextProcessor.Output: No callback registered.")

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

class TextConnection:
    def __init__(self, textServiceLocation, processor):
        """
        """
        self.host, self.port = textServiceLocation
        self.processor = processor
        self.log = logging.getLogger("AG.TextClient.TextConnection")
        
        # Initialize connection
        self.bufsize = 4096
        self.buffer = Buffer(self.bufsize)
        self.dataBuffer = ''
        self.waitingLen = 0

        self.attr = CreateTCPAttrAlwaysAuth()
        self.socket = GSITCPSocket()

        try:
            self.socket.connect(self.host, self.port, self.attr)
        except:
            self.log.exception("Couldn't connect to text service! %s:%d",
                               self.host, self.port)
            raise TextClientConnectException

        self.wfile = self.socket.makefile('wb', 0)

        self.cbHandle = self.socket.register_read(self.buffer, self.bufsize, 1,
                                      self.readCallbackWrap, None)

        self.log.debug("TextConnection: register returns %s",
                       self.cbHandle)
        
        self.log.debug("\n\thost:%s\n\tport:%d\n\tattr:%s"
                   % (self.host, self.port, str(self.attr)))
        self.log.debug("\n\tsocket:%s" % str(self.socket))

    def Stop(self):
        self.wfile.close()
        self.log.debug("TextClient.Stop")

    def SetProcessor(self, processor):
        """
        """
        self.processor = processor
        
    def Write(self, event):
        """
        """
        self.log.debug("TextConnection.Write: EVENT --- Input")
        self.log.debug("TextConnection.Write: %s" % str(event))
        
        # Pickle the data
        pdata = pickle.dumps(event)
        size = struct.pack("i", len(pdata))
        # Send the size as 4 bytes
        self.wfile.write(size)
        # Send the pickled event data
        self.wfile.write(pdata)

    def InitAsynchIO(self):
        """
        Initialize for using asynchronous IO for reading data from the network.
        """

        self.bufsize = 4096
        self.buffer = Buffer(self.bufsize)
        self.dataBuffer = ''
        self.waitingLen = 0

        h = self.socket.register_read(self.buffer, self.bufsize, 1,
                                      self.readCallbackWrap, None)

        self.log.debug("TextConnection: register returns %s", h)
        self.cbHandle = h

    def readCallbackWrap(self, arg, handle, ret, buf, n):
        """
        Asynch read callback.

        We just use this to wrap the call to the readCallback itself,
        because the callback invocation mechanism silently ignores exceptions.
        """

        try:
            return self.readCallback(arg, handle, ret, buf, n)
        except Exception:
            self.log.exception("TextConnection: readcallback failed")

    def readCallback(self, arg, handle, ret, buf, n):

        self.log.debug("TextConnection: Got read handle=%s ret=%s  n=%s \n",
                  handle, ret, n)

        if n == 0:
            self.log.debug("TextConnection: asynch read gets n=0, EOF")
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
            self.log.debug("TextConnection: Data len %s", dlen)

            self.dataBuffer = self.dataBuffer[sz:]

            self.waitingLen = dlen[0]

        if len(self.dataBuffer) >= self.waitingLen:
            self.log.debug("TextConnection: read enough data, wait=%s buflen=%s",
                      self.waitingLen, len(self.dataBuffer))

            thedata = self.dataBuffer[:self.waitingLen]
            self.dataBuffer = self.dataBuffer[self.waitingLen:]

            self.handleData(thedata)

            self.waitingLen = 0
            
        self.cbHandle = self.socket.register_read(self.buffer, self.bufsize, 1,
                                                  self.readCallbackWrap, None)
        self.log.debug("TextConnection: register returns %s", self.cbHandle)

    def handleData(self, pdata):
        # Unpickle the data
        try:
            event = pickle.loads(pdata)
        except EOFError:
            self.log.exception("TextConnection: unpickle got EOF.")
            raise TextClientBadDataException

        # Handle the data
        if self.processor != None:
            self.processor.Output(event.data)

class TextClient:
    def __init__(self, profile, textServiceLocation=None):
        self.textServiceLocation = textServiceLocation
        self.textConnection = None
        self.profile = profile
        self.textProcessor = SimpleTextProcessor(myProfile=profile)
        self.log = logging.getLogger("AG.TextClient")
        
        if self.textServiceLocation != None:
            self.textConnection = TextConnection(self.textServiceLocation,
                                                 self.textProcessor)
            self.textProcessor.SetTextConnection(self.textConnection)
            
    def Connect(self, venueId, privateId):
        """
        """
        self.venueId = venueId
        self.privateId = privateId
        self.textProcessor.Input(ConnectEvent(venueId, privateId))
        
    def Disconnect(self, venueId, privateId):
        """
        """
        self.venueId = None
        self.privateId = None
        self.textProcessor.Input(DisconnectEvent(venueId, privateId))
        self.textConnection.Stop()
        
    def SetTextProcessor(self, processor):
        """
        """
        self.textProcessor = processor
        
    def RegisterOutputCallback(self, callback):
        """
        """
        self.textProcessor.RegisterOutputCallback(callback)

    def Input(self, text):
        """
        """
        self.textProcessor.Input(TextEvent(self.venueId, None,
                                           0, (text, self.profile)))
        
    def Stop(self):
        self.log.debug("TextClient.Stop")
        self.textProcessor.Input(DisconnectEvent(self.venueId, self.privateId))
        self.textConnection.Stop()

