#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client side object of the Virtual Venues Services.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: VenueClient.py,v 1.1.1.1 2002-12-16 22:25:37 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import CoherenceClient

class VenueClient:
    __doc__ = """
    This is the client side object that maintains a stateful relationship with
    a Virtual Venue. This object provides the programmatic interface to the
    Access Grid for a Venues User Interface.
    The VenueClient can only be in one venue at a time.
    """
    currentVenue = None
    homeVenue = None
    coherenceClient = None
    
    def __init__(self):
        __doc__ = """
        This client class is used on shared and personal nodes.
        """

    def EnterVenue(self):
        __doc__ = """
        EnterVenue puts this client into the specified venue.
        """
        
    def ExitVenue(self):
        __doc__ = """
        ExitVenue removes this client from the specified venue.
        """
        
    def GetVenue(self):
        __doc__ = """
        GetVenue gets the venue the client is currently in.
        """
        
    def AddService(self, serviceDescription):
        __doc__ = """
        AddService adds a service to the client. The expected minimum set of 
        services always present include:
            Workspace Docking Service
            Node Service
        """
        
    def RemoveService(self, serviceDescription):
        __doc__ = """
        RemoveService removes a service from the client.
        """
        
    def ModifyService(self, serviceDescription):
        __doc__ = """
        ModifyService modifies a service description for a service in the Venue.
        """
        
    def GetServices(self):
        __doc__ = """
        GetServices returns the list of services provided by this client.
        """
        
    def GetHomeVenue(self):
        __doc__ = """
        GetHomeVenue returns the default venue for this venue client.
        """
        
    def SetHomeVenue(self, venueURL):
        __doc__ = """
        SetHomeVenue sets the default venue for this venue client.
        """
        
    def FollowNode(self, clientProfile):
        __doc__ = """
        FollowNode tells this venue client to follow the node specified.
        """
        
    def UnfollowNode(self, clientProfile):
        __doc__ = """
        UnfollowNode tells this venue client to stop following the node 
        specified.
        """
        
    def LeadNode(self, clientProfile):
        __doc__ = """
        LeadNode tells this venue client to drag the specified node with it.
        """