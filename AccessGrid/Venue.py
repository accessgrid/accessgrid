#-----------------------------------------------------------------------------
# Name:        Venue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: Venue.py,v 1.2 2003-01-07 20:27:13 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from AccessGrid.hosting.pyGlobus import ServiceBase

class Venue(ServiceBase.ServiceBase):
    """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    """
    uniqueId = ''
    venueState = None
    venueConfiguration = None

    description = None
    connections = []
    users = []
    nodes = []
    data = []
    services = []

    venueServer = None
    networkServices = []
    streams = []
    administrators = []

    coherenceService = None
    multicastAddressAllocator = None
    dataStore = None
    
    def __init__(self, server, uniqueId, description, administrator,
                 coherenceService, multicastAddressAllocator, dataStore):
        self.uniqueId = uniqueId
        self.description = description
        self.venueServer = server
        self.administrators.append(administrator)
        self.coherenceService = coherenceService
        self.coherenceService.start()
        self.multicastAddressAllocator = multicastAddressAllocator
        self.dataStore = dataStore

    # Management methods
    def AddNetworkService(self, connectionInfo, networkServiceDescription):
        """ """
        self.networkServices.append(networkServiceDescription)

    AddNetworkService.pass_connection_info = 1
    AddNetworkService.soap_export_as = "AddNetworkService"
    
    def GetNetworkServices(self):
        """ """
        return self.networkServices
    
    def RemoveNetworkService(self, networkServiceDescription):
        """ """
        self.networksServices.remove(networkServiceDescription)
        
    def AddConnection(self, connectionDescription):
        """ """
        self.connections.add(connectionDescription)
        
    def SetDescription(self, description):
        """ """
        self.description = description
        
    def GetDescription(self):
        """ """
        return self.description
    
    def GetStreams(self):
        """ """
        return self.streams()
    
    # Client Methods
    def Enter(self, connectionInfo, clientProfile):
        """ """
        print "Called Venue Enter for: "

        print dir(clientProfile)

        self.users.append(clientProfile)
        
        state = {
            'description' : self.description,
            'connections' : self.connections,
            'users' : self.users,
            'nodes' : self.nodes,
            'data' : self.data,
            'services' : self.services,
            'coherenceLocation' : self.coherenceService.GetLocation()
            }

        evt = {
            'event' : 'Enter',
            'data' : clientProfile
            }
        
        self.coherenceService.distribute(evt)

        return state
    
    Enter.pass_connection_info = 1
    Enter.soap_export_as = "Enter"
    
    def Exit(self, connectionInfo, id):
        """ """
        print "Called Venue Exit on " + str(connectionInfo)

        evt = {
            'event' : 'Exit',
            'data' : id
            }
        
        self.coherenceService.distribute(evt)
        
    Exit.pass_connection_info = 1
    Exit.soap_export_as = "Exit"

    def GetState(self, connectionInfo, id):
        """ """
        print "Called GetState on " + self.uniqueId

        state = {
            'description' : self.description,
            'connections' : self.connections,
            'users' : self.users,
            'nodes' : self.nodes,
            'data' : self.data,
            'services' : self.services,
            'coherenceLocation' : self.coherenceService.GetLocation()
            }

        return state
    
    GetState.pass_connection_info = 1
    GetState.soap_export_as = "GetState"

    def UpdateClientProfile(self, connectionInfo, clientProfile):
        """ """
        
        evt = {
            'event' : 'UpdateClientProfile',
            'data' : clientProfile
            }
        
        self.coherenceService.distribute(evt)
        
    UpdateClientProfile.pass_connection_info = 1
    UpdateClientProfile.soap_export_as = "UpdateClientProfile"

    def AddData(self, connectionInfo, dataDescription):
        """ """
        self.data.append(dataDescription)

        # Do something with the data store

        evt = {
            'event' : 'AddData',
            'data' : dataDescription
            }
        
        self.coherenceService.distribute(evt)

    AddData.pass_connection_info = 1
    AddData.soap_export_as = "AddData"

    def GetData(self, connectionInfo, dataDescription):
        """ """

        # Do something with the data store

        evt = {
            'event' : 'GetData',
            'data' : dataDescription
            }
        
        self.coherenceService.distribute(evt)
        
    GetData.pass_connection_info = 1
    GetData.soap_export_as = "GetData"

    def RemoveData(self, connectionInfo, dataDescription):
        """ """
        self.data.remove(dataDescription)

        # Do something with the data store
        
        evt = {
            'event' : 'GetData',
            'data' : dataDescription
            }
        
        self.coherenceService.distribute(evt)

    RemoveData.pass_connection_info = 1
    RemoveData.soap_export_as = "RemoveData"

    def AddService(self, connectionInfo, serviceDescription):
        """
        This methods should add a service description to the Venue.
        """

        self.services.append(serviceDescription)
        
        evt = {
            'event' : 'AddService',
            'data' : serviceDescription
            }
        
        self.coherenceService.distribute(evt)

    AddService.pass_connection_info = 1
    AddService.soap_export_as = "AddService"

    def RemoveService(self, connectionInfo, serviceDescription):
        """ """

        self.services.remove(serviceDescription)
        
        evt = {
            'event' : 'RemoveService',
            'data' : serviceDescription
            }
        
        self.coherenceService.distribute(evt)

    RemoveService.pass_connection_info = 1
    RemoveService.soap_export_as = "RemoveService"

    # Internal Methods
    def NegotiateCapabilities(self, ClientProfile):
        """ """
        
