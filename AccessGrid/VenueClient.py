#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.4 2003-01-15 22:55:54 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.CoherenceClient import CoherenceClient
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import Event, VenueState

class VenueClient:
   """
   This is the client side object that maintains a stateful
   relationship with a Virtual Venue. This object provides the
   programmatic interface to the Access Grid for a Venues User
   Interface.  The VenueClient can only be in one venue at a
   time.
   """

   def __init__(self, profile=None):
      """
      This client class is used on shared and personal nodes.
      """
      self.profile = profile
      self.nodeServiceUri = None
      self.workspaceDock = None
      self.__InitVenueData__()
       

   def __InitVenueData__( self ):
      self.coherenceClient = None
      self.venueState = None
      self.currentVenue = None
      self.privateId = None
      self.streamDescList = []

   def SetProfile(self, profile):
      self.profile = profile
      
   def coherenceCallback(self, event):
      print "Got coherence event: " + event.eventType, str(event.data)


      

      
   def EnterVenue(self, URL):
      """
      EnterVenue puts this client into the specified venue.
      """

      if self.currentVenue != None:
         self.ExitVenue()

      #
      # Retrieve list of node capabilities
      #
      if self.nodeServiceUri:
         print "using node service uri ", self.nodeServiceUri
         self.profile.capabilities = Client.Handle( self.nodeServiceUri ).get_proxy().GetCapabilities()
         print "Got capabilities "
         for cap in self.profile.capabilities:
            print "  ", cap.role, cap.type

      #
      # Enter the venue
      #
      (venueState, self.privateId, self.streamDescList ) = Client.Handle( URL ).get_proxy().Enter( self.profile )
      self.venueState = VenueState( venueState.description, 
                                    venueState.connections, 
                                    venueState.users,
                                    venueState.nodes, 
                                    venueState.data, 
                                    venueState.services, 
                                    venueState.coherenceLocation )

      if self.streamDescList != None:
         print "streams ------"
         for stream in self.streamDescList:
            print "  ", stream.capability.type, stream.capability.role, stream.location.host, stream.location.port

      print dir(self.venueState)
      print self.venueState.users
      print dir(self.venueState.users)

      self.currentVenue = URL

      #
      # Start the coherence client
      #
#FIXME - should create coherence client at instantiation, and with each enter
#        update its host/port (setting the callbacks at instantiation, too)
      #print "Starting coherence client on ", cl['host'], cl['port']
      self.coherenceClient = CoherenceClient( self.venueState.coherenceLocation.host,
                                              self.venueState.coherenceLocation.port,
                                              self.coherenceCallback )
      self.coherenceClient.add_callback( Event.ENTER, self.venueState.AddUser )
      self.coherenceClient.add_callback( Event.EXIT, self.venueState.RemoveUser )
      self.coherenceClient.add_callback( Event.ADD_DATA, self.venueState.AddData )
      self.coherenceClient.add_callback( Event.REMOVE_DATA, self.venueState.RemoveData )
      self.coherenceClient.add_callback( Event.ADD_SERVICE, self.venueState.AddService )
      self.coherenceClient.add_callback( Event.REMOVE_SERVICE, self.venueState.RemoveService )
      self.coherenceClient.add_callback( Event.ADD_CONNECTION, self.venueState.AddConnection )
      self.coherenceClient.add_callback( Event.REMOVE_CONNECTION, self.venueState.RemoveConnection )
      self.coherenceClient.start()


      # 
      # Update the node service with stream descriptions
      #
      if self.nodeServiceUri:
         Client.Handle( self.nodeServiceUri ).get_proxy().ConfigureStreams( streamDescList )
      
   def ExitVenue(self):
      """
      ExitVenue removes this client from the specified venue.
      """
      Client.Handle( self.currentVenue ).get_proxy().Exit( self.privateId )
      self.__InitVenueData__()
      
   def GetVenue(self):
      """
      GetVenue gets the venue the client is currently in.
      """
      return self.currentVenue
      
   def AddService(self, serviceDescription):
      """
      AddService adds a service to the client. The expected
      minimum set of services always present include:
      Workspace Docking Service
      Node Service
      """
      
   def RemoveService(self, serviceDescription):
      """
      RemoveService removes a service from the client.
      """
      
   def ModifyService(self, serviceDescription):
      """
      ModifyService modifies a service description for a
      service in the Venue.
      """
      
   def GetServices(self):
      """
      GetServices returns the list of services provided by this client.
      """
      
   def GetHomeVenue(self):
      """
      GetHomeVenue returns the default venue for this venue client.
      """
      
   def SetHomeVenue(self, venueURL):
      """
      SetHomeVenue sets the default venue for this venue client.
      """
      
   def FollowNode(self, clientProfile):
      """
      FollowNode tells this venue client to follow the node
      specified.
      """
      
   def UnfollowNode(self, clientProfile):
      """
      UnfollowNode tells this venue client to stop following
      the node specified.
      """
      
   def LeadNode(self, clientProfile):
      """
      LeadNode tells this venue client to drag the specified
      node with it.
      """

   def SetNodeServiceUri( self, nodeServiceUri ):
      self.nodeServiceUri = nodeServiceUri

if __name__ == "__main__":
   import sys
   from AccessGrid.hosting.pyGlobus import Client
   from AccessGrid.hosting.pyGlobus.Server import Server
   profile = ClientProfile('userProfileExample')
   
   vc = VenueClient(profile)
   vc.EnterVenue(sys.argv[1])

   port = 10100
   if len(sys.argv) > 1:
      port = int(sys.argv[1])
   server = Server( port )
   service = server.create_service_object()

   serviceManager._bind_to_service( service )
