#!/usr/bin/python

from UMTP import UMTPAGent
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation

agent = UMTPAgent()

stream = StreamDescription("testname",MulticastNetworkLocation('224.2.2.2',20200,127),[Capability()])
agent.SetStreamList([stream])
agent.SetServer()
agent.Start()

