#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClientEventSubscriber.py
# Purpose:     This provides predefined callbacks that are called from 
#                AccessGrid.VenueClient.
#
# Author:      Eric C. Olson
#
# Created:     2003/07/21
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------


import logging, logging.handlers
log = logging.getLogger("AG.VenueClient")

from AccessGrid.Toolkit import AG_TRUE, AG_FALSE

class VenueClientEventSubscriber:
    """
    An interface to receive AccessGrid.VenueClient events.
    Defines the basic callbacks that AccessGrid.VenueClient will use.
    If you want to customize the VenueClient, you can inherit this class and
        override whichever functions below you need.
    For an example that uses this, please see bin/CommandLineVenueClient.py.
    """

    # Functions that don't include an event argument are often initiated by 
    #     the local machine/client and are simple called from AccessGrid.VenueClient.
    #     That is why they often don't have a full "event" object as an argument.

    def PreEnterVenue(self, URL, back=AG_FALSE):
        pass

    def EnterVenue(self, URL, back=AG_FALSE, warningString="", enterSuccess=AG_TRUE):
        pass

    def ExitVenue(self):
        pass

    def LeadResponse(self, leaderProfile, isAuthorized):
        pass

    def Heartbeat(self, isSuccess):
        pass

    # Functions that also pass an event argument.

    def AddUserEvent(self, event):
        pass

    def RemoveUserEvent(self, event):
        pass

    def ModifyUserEvent(self, event):
        pass

    def AddDataEvent(self, event):
        pass

    def UpdateDataEvent(self, event):
        pass

    def RemoveDataEvent(self, event):
        pass

    def AddServiceEvent(self, event):
        pass

    def RemoveServiceEvent(self, event):
        pass

    def AddApplicationEvent(self, event):
        pass

    def RemoveApplicationEvent(self, event):
        pass

    def AddConnectionEvent(self, event):
        pass

    def RemoveConnectionEvent(self, event):
        pass

    def SetConnectionsEvent(self, event):
        pass

    def AddStreamEvent(self, event):
        pass

    def RemoveStreamEvent(self, event):
        pass


