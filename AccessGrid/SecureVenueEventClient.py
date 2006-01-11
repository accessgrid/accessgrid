#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        SecureEventClient.py
# Purpose:     A secure group messaging service client that handles Access
#                 Grid venue events.
# Created:     2006/01/10
# RCS-ID:      $Id: SecureVenueEventClient.py,v 1.2 2006-01-11 18:36:14 eolson Exp $
# Copyright:   (c) 2006
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import sys
from twisted.internet import threadedselectreactor
try:
    threadedselectreactor.install()
    from twisted.internet import reactor
except:
    pass
from AccessGrid.VenueEventClient import mainWithUI, GenerateRandomString
from AccessGrid.VenueEventClient import VenueEventClient, TestMessages
from AccessGrid.SecureGroupMsgClient import SecureGroupMsgClient
from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient

class SecureVenueEventClient(VenueEventClient):
    '''
    A version of the EventClient that supports encryption.
    '''
    defaultGroupMsgClientClassList = [XMLGroupMsgClient, SecureGroupMsgClient]


### The code below is to help test and demo. ###

def testMain(location, privateId, channel="Test", msgLength=13, numMsgs=100, groupMsgClientClassList=None, multipleClients=False):
    vec = SecureVenueEventClient(location, privateId, channel, groupMsgClientClassList=groupMsgClientClassList)
    tm = TestMessages(vec=vec, numMsgs=numMsgs, multipleClients=multipleClients)
    tm.SetMsgData(GenerateRandomString(length=msgLength))
    vec.Start()

def main(eventPort=7002):
    wxapp = None
    if "--psyco" in sys.argv:
        print "optimizing with psyco."
        import psyco
        psyco.full()
    group = "Test"
    testMessageSize = 13
    useUI = True
    multipleClients = False
    eventPort = 7002
    location = ('localhost',eventPort)
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
        groupMsgClientClassList = None # Will use the default for SecureVenueEventClient
    elif format=='xml':
        from AccessGrid.XMLGroupMsgClient import XMLGroupMsgClient
        groupMsgClientClassList = [XMLGroupMsgClient, SecureGroupMsgClient]
    elif format=='pickle':
        from AccessGrid.PickleGroupMsgClient import PickleGroupMsgClient
        groupMsgClientClassList = [PickleGroupMsgClient, SecureGroupMsgClient]
    else:
        raise Exception("Unknown format")

    if useUI:
        wxapp = mainWithUI(group=group, venueEventClientClass=SecureVenueEventClient, groupMsgClientClassList=groupMsgClientClassList, eventPort=eventPort)
        wxapp.MainLoop()
    else:
        testMain(location=location, privateId=privateId, channel=group, msgLength=testMessageSize, numMsgs=numMsgs, groupMsgClientClassList=groupMsgClientClassList, multipleClients=multipleClients)
        from twisted.internet import reactor
        reactor.run()


if __name__ == '__main__':
    # need to parse for wx here to be able to get wx imports 
    #    and the threadedselectreactor that wx requires.
    useUI = True
    for arg in sys.argv:
        if arg.startswith("--perf"):
            useUI = False

    main(eventPort=7002)


