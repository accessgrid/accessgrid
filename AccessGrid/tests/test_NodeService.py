import sys

from AccessGrid.hosting.pyGlobus import Client


import socket
from AccessGrid.Types import Capability, AGResource
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation


host = socket.gethostname()

nodeServiceUri = "https://localhost:11000/NodeService"
if len(sys.argv) > 1:
    nodeServiceUri = sys.argv[1]
nodesvc = Client.Handle( nodeServiceUri ).get_proxy()



# query available service managers
smlist = Client.Handle( nodeServiceUri ).get_proxy().GetServiceManagers().data
print "smlist ", smlist

if len(smlist) == 0:
   print "\n------------------ Add a Service Manager"
   # add known service manager
   nodesvc.AddServiceManager( AGServiceManagerDescription( "sm1_name", 'https://%s:12000/ServiceManager' % ( host ) ) )

print "\n------------------ List Installed Service Managers"
smlist = Client.Handle( nodeServiceUri ).get_proxy().GetServiceManagers()
for sm in smlist:
   print "   ", sm.name, sm.uri


# query available services
silist = nodesvc.GetAvailableServices()
print "\n------------------ List Available Services"
for si in silist:
   print "   ",si.name, si.uri

# add each one to each service manager
print "\n------------------ Install Available Services on each Service Manager"
smlist = nodesvc.GetServiceManagers()
for sm in smlist:
   print "   ", sm.name
   for si in silist:
      print "      ", si.name
      Client.Handle( sm.uri ).get_proxy().AddService( si.servicePackageUri, "None", "None" )


# list services
svclist = nodesvc.GetServices()
print "\n------------------ List Installed Services"
for svc in svclist:
   print "   ", svc.name, svc.uri, svc.serviceManagerUri


# configure streams
print "\n------------------ Configure Streams"
streamDs = []
streamDs.append( StreamDescription( "test", "noch eine", 
   MulticastNetworkLocation("233.2.171.39",42000,127), 
   Capability( Capability.CONSUMER, Capability.AUDIO ) ) )
streamDs.append( StreamDescription( "test", "noch eine", 
   MulticastNetworkLocation("233.2.171.39",42002,127), 
   Capability( Capability.PRODUCER, Capability.VIDEO ) ) )

nodesvc.ConfigureStreams( streamDs )

# start services
print "\n------------------ Start Services"
for svc in svclist:
   print "   ", svc.name, svc.uri
   try:
      if svc.uri != None and svc.uri != "None":
         Client.Handle( svc.uri ).get_proxy().Start()
      else:
         print "service has null uri"
   except:
      print "Exception ", sys.exc_type, sys.exc_value

print "sleep for 3 seconds"
import time
time.sleep(3)


# remove all services
print "\n------------------ Remove Services"
for sm in smlist:
   sm_svclist = Client.Handle( sm.uri ).get_proxy().GetServices()
   for svc in sm_svclist:
      print "   ", svc.name
      Client.Handle( sm.uri ).get_proxy().RemoveService( svc )
