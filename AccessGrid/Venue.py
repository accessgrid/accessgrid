#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class Venue:
    __doc__ = """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    venueServer = None
    description = None
    connections = ()
    users = ()
    nodes = ()
    data = ()
    services = ()
    networkServices = ()
    streams = ()
    coherenceService = None
    multicastAddressAllocator = None
    dataStore = None
    administrators = ()
    uniqueID = ''
    
    # Management methods
    
    def __init__(self, server, uniqueID, description, coherenceService, 
                 multicastAddressAllocator, dataStore):
        self.uniqueID = uniqueID
        self.venueServer = server
        self.description = description
        self.coherenceService = coherenceService
        self.multicastAddressAllocator = multicastAddressAllocator
        self.dataStore = dataStore
        
    def AddNetworkService(self, networkServiceDescription):
        __doc__ = """ """
        self.networkServices.append(networkServiceDescription)
        
    def GetNetworkServices(self):
        __doc__ = """ """
        return self.networkServices
    
    def RemoveNetworkService(self, networkServiceDescription):
        __doc__ = """ """
        self.networkServices.remove(networkServiceDescription)
        
    def AddConnection(self, connectionDescription):
        __doc__ = """ """
        self.connections.append(connectionDescription)
        
    def SetDescription(self, description):
        __doc__ = """ """
        self.description = description
        
    def GetDescription(self):
        __doc__ = """ """
        return self.description
    
    def GetStreams(self):
        __doc__ = """ """
        return self.streams
    
    def Destroy(self):
        __doc__ = """ """
    
    # Client Methods
        
    def Enter(self, clientProfile):
        __doc__ = """ """
        print "Called Venue Enter on " + self.uniqueID
        
    def Exit(self, id):
        __doc__ = """ """
        print "Called Venue Exit on " + self.uniqueID
        
    def GetState(self, id):
        __doc__ = """ """
        print "Called GetState on " + self.uniqueID
        
    def UpdateClientProfile(self, clientProfile):
        __doc__ = """ """
        
    def AddData(self, dataDescription):
        __doc__ = """ """
    
    def GetData(self, dataDescription):
        __doc__ = """ """
        return self.data
    
    def RemoveData(self, dataDescription):
        __doc__ = """ """
   
    def AddService(self, serviceDescription):
        __doc__ = """
        This methods should add a service description to the Venue.
        """
        self.services.append(servideDescription)
        
    def RemoveService(self, serviceDescription):
        __doc__ = """ """
        self.services.remove(serviceDescription)
        
    # Internal Methods
    
    def NegotiateCapabilities(self, ClientProfile):
        __doc__ = """ """
        
    def GetUniqueID(self):
        __doc__ = """ """
        return self.uniqueID