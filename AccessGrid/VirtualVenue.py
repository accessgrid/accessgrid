#-----------------------------------------------------------------------------
# Name:        VirtualVenue.py
# Purpose:     The Virtual Venue is the object that provides the collaboration
#               scopes in the Access Grid.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VirtualVenue.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

class VirtualVenue:
   self.__doc__ = """
    A Virtual Venue is a virtual space for collaboration on the Access Grid.
    Virtual Venues 
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
    eventChannel = None
    administrators = ()
    
    # Management methods
    
    def __init__(self, server, description):
                
    def AddNetworkService(self, networkServiceDescription):

    def GetNetworkServices(self):
    
    def RemoveNetworkService(self, networkServiceDescription):
        
    def AddConnection(self, connectionDescription):
        
    def SetDescription(self, description):
        
    def GetDescription(self):
        
    def GetStreams(self):

    def Destroy(self):
    
    # Client Methods
        
    def Enter(self, clientProfile):
        
    def Exit(self, id):
    
    def GetState(self, id):
        
    def UpdateClientProfile(self, clientProfile):

    def AddData(self, dataDescription):
    
    def GetData(self, dataDescription):
    
    def RemoveData(self, dataDescription):
   
    def AddService(self, serviceDescription):
    
    def RemoveService(self, serviceDescription):
        
    # Internal Methods
    
    def NegotiateCapabilities(self, ClientProfile):