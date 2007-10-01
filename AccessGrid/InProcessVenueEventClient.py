#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueEventClient.py
# Purpose:     A secure group messaging service client that handles Access
#                 Grid venue events.
# Created:     2006/01/10
# RCS-ID:      $Id: InProcessVenueEventClient.py,v 1.3 2007-10-01 20:27:31 turam Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
try:
    from twisted.internet import _threadedselect as threadedselectreactor
except:
    from twisted.internet import threadedselectreactor

try:
    threadedselectreactor.install()
    from twisted.internet import reactor
except:
    pass
from AccessGrid.InsecureVenueEventClient import mainWithUI, GenerateRandomString
from AccessGrid.InsecureVenueEventClient import BaseVenueEventClient, TestMessages
from AccessGrid.InProcessGroupMsgClient import InProcessGroupMsgClient
from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient

class InProcessVenueEventClient(BaseVenueEventClient):
    '''
    A version of the EventClient that supports encryption.
    '''
    defaultGroupMsgClientClassList = [XMLGroupMsgClient, InProcessGroupMsgClient]

    def __init__(self, location, privateId, channel, groupMsgClientClassList=None):
        # Pass along the lower level groupMsgService, which the
        #   InProcessGroupMsgClient knows how to use.
        BaseVenueEventClient.__init__(self, location.groupMsgService, privateId, channel, groupMsgClientClassList)


InProcessVenueEventClient = InProcessVenueEventClient


### The code below is to help test and demo. ###

def testMain(eventService, privateId, channel="Test", msgLength=13, numMsgs=100, groupMsgClientClassList=None, multipleClients=False):
    vec = InProcessVenueEventClient(eventService, privateId, channel, groupMsgClientClassList=groupMsgClientClassList)
    tm = TestMessages(vec=vec, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    vec.Start()

def main(eventService):
    wxapp = None
    if "--psyco" in sys.argv:
        print "optimizing with psyco."
        import psyco
        psyco.full()
    group = "Test"
    testMessageSize = 13
    useUI = False
    multipleClients = False
    privateId = GenerateRandomString(length=6)
    format= 'default' # or  'xml' # or 'pickle'
    numMsgs = 10
    for arg in sys.argv:
        if arg.startswith("--group="):
            group = arg.lstrip("--group=")
            print "Setting group:", group
        if arg.startswith("--perf"):
            print "Measuring performance for single client."
            useUI = False 
        if arg.startswith("--largeMsg"):
            print "Using large messages (1000 bytes)"
            testMessageSize = 1000
        if arg.startswith("--format="):
            format = arg.lstrip("--format=")
        if arg.startswith("--multiClient"):
            multipleClients = True
        if arg.startswith("--numMsgs="):
            numMsgs = int(arg.lstrip("--numMsgs="))
            print "Setting number of messages:", numMsgs

    if format=='default':
        groupMsgClientClassList = None # Will use the default for InProcessVenueEventClient
    elif format=='xml':
        from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient
        groupMsgClientClassList = [XMLGroupMsgClient, InProcessGroupMsgClient]
    elif format=='pickle':
        from AccessGrid.PickleGroupMsgClient import PickleGroupMsgClient
        groupMsgClientClassList = [PickleGroupMsgClient, InProcessGroupMsgClient]
    else:
        raise Exception("Unknown format")

    if useUI:
        raise Exception( "Unimplemented.  Try without the UI" )
        wxapp = mainWithUI(group=group, venueEventClientClass=InProcessVenueEventClient, groupMsgClientClassList=groupMsgClientClassList)
        wxapp.MainLoop()
    else:
        testMain(eventService=eventService, privateId=privateId, channel=group, msgLength=testMessageSize, numMsgs=numMsgs, groupMsgClientClassList=groupMsgClientClassList, multipleClients=multipleClients)
        from twisted.internet import reactor
        reactor.run()


if __name__ == '__main__':
    # need to parse for wx here to be able to get wx imports 
    #    and the threadedselectreactor that wx requires.
    useUI = True
    for arg in sys.argv:
        if arg.startswith("--perf"):
            useUI = False

    # -- Starting the service for testing --
    from AccessGrid.EventService import EventService
    from AccessGrid.Toolkit import Service
    # Initialize the toolkit so Access Grid certificates will be available.
    Service.instance().Initialize("InProcessEventService", args=["InProcessEventService.py"])

    eventService = EventService(name="test", description="atest", id="testId", type="event", location=('localhost',7002))
    eventService.CreateChannel("Test")
    eventService.Start()

    # -- Starting the client for testing --

    from twisted.internet import reactor

    main(eventService)


