#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        unittest_Node.py
# Purpose:     
#
# Created:     2004/05/07
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for a BridgeServer

This test case runs the necessary components to test the bridge server code.
It tries to ensure that the bridge server does the right thing with static
and dynamic streams in a venue, when a user enters a venue and when a user
is already in a venue.

Overview
--------

o Run the venue server

o Test static streams
  - Add static streams to venue
  - Start bridge server against venue
  - Enter venue with a venue client
    - Examine returned streamList for bridged streams
    
o Test dynamic streams in a bridged venue
  - Remove static streams
  - Enter the venue with a venue client with producer capability
      (so a stream is allocated)
  - Wait for venue client to receive ModifyStream event
    - Verify presence of bridged network location in event stream 

Note that PyUnit (and JUnit as well) execute setUp() and tearDown() once for
EACH test and make it difficult to setUp and tearDown something across multiple
tests.  This is not ideal for our server tests, but we work around it to keep a
server running for multiple tests.


"""

import time, sys, os
import unittest
import logging, logging.handlers
import traceback

from AccessGrid.hosting import SecureServer as Server
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import AGTkConfig, UserConfig
from AccessGrid.Platform.ProcessManager import ProcessManager


from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Venue import VenueIW
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.Types import Capability

server = None
log = None
smurl = None

venueserverport = 4000

processManager = None

venueServerPid = None
venueServer = None
venueUrl = None
venue = None


bridgerName = 'Argonne'
bridgerLoc =  'Chicago'

bridgeConfig = """
[BridgeServer]
name = %s
location = %s
qbexec = /bin/echo

# venue to bridge
[%s]
type = Venue
"""


ConfigName = 'BridgeServerTest.cfg'


def RemoveStreams(venue):
    streamList = venue.GetStreams()
    for stream in streamList:
        venue.RemoveStream(stream)
        

class BridgeServerTestCase(unittest.TestCase):
    """A test case for a whole Node."""

    def test_100_Setup(self):
        global venueServer, processManager, venue, venueUrl
        
        # initialize toolkit and environment
        app = Toolkit.Service().instance()
        app.Initialize("Node_test", sys.argv[:1])
        log = app.GetLog()
        
        # Start process manager
        processManager = ProcessManager()


        # Find venue server exe
        bin = AGTkConfig.instance().GetBinDir()
        venueserverexe = os.path.join(bin,'VenueServer.py')
        

        # Start the venue server
        exe = sys.executable
        opts = [ venueserverexe,
                 '-p', str(venueserverport),
               ]
        processManager.StartProcess(exe,opts)
                        
        # Create proxy to the venue server
        venueServer = VenueServerIW('https://localhost:%d/VenueServer' % (venueserverport,))
        
        # Wait for server to become reachable
        print "Wait for venue server..."
        up = 0
        while not up:
            try:
                up = venueServer.IsValid()
                print "up = ", up
                continue
            except:
                print "waiting for venue server..."
                pass
            time.sleep(1)
        
        venueUrl = venueServer.GetDefaultVenue()
        venue = VenueIW(venueUrl)
       
       
    def test_200_TestStaticStreams(self):
        global venue, venueUrl
        global bridgeConfig
        global bridgerName,bridgerLoc
        
        RemoveStreams(venue)
    
        # Add static stream to venue
        streamDesc = StreamDescription('static test stream',
                            MulticastNetworkLocation('224.2.2.2',20000,127),
                            Capability('producer','test'),
                            0,None,
                            1)
        venue.AddStream(streamDesc)
        
        
        # Start the bridgeserver against the venue
        # - find the bridgeserver exe
        bin = AGTkConfig.instance().GetBinDir()
        bridgeserverexe = os.path.join(bin,'BridgeServer.py')
        
        # - build a config file for the bridge server
        configFile = os.tmpnam()
        f = open(configFile,'w')
        f.write( bridgeConfig % (bridgerName,bridgerLoc,venueUrl,))
        f.close()
        
        # - start the bridge server
        exe = sys.executable
        opts = [ bridgeserverexe,
                 '-c', configFile,
               ]
        processManager.StartProcess(exe,opts)
        
        # Enter the venue
        
        print "sleeping"
        time.sleep(10)
        
        # Confirm presence of bridged network locations
        numBridgedStreams = 0
        streamList = venue.GetStreams()
        for stream in streamList:
            for netloc in stream.networkLocations:
                print "stream : ", stream.id, stream.name, netloc.host, netloc.port, netloc.profile.name, netloc.profile.location
                if (netloc.profile.name == bridgerName and 
                    netloc.profile.location == bridgerLoc ):
                    numBridgedStreams += 1
                    
        print "numstreams, numbridgedstreams = ", len(streamList), numBridgedStreams
                    
        assert len(streamList) == numBridgedStreams
        
        

    # Cleanup things set up in the test suite init above.
    #   Unittest suites don't have a proper way to cleanup things used 
    #   in the entire suite.
    def test_999_TearDown(self):
        processManager.TerminateAllProcesses()

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(BridgeServerTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

