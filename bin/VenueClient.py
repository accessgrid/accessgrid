#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.28 2003-02-06 20:45:47 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import threading
import os

from wxPython.wx import *

from pyGlobus.io import GSITCPSocketException

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid.VenueClient import VenueClient, EnterVenueException
from AccessGrid.VenueClientUIClasses import WelcomeDialog
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.VenueClientUIClasses import ConnectToVenueDialog
from AccessGrid.Descriptions import DataDescription
from AccessGrid.Events import Event
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.UIUtilities import ErrorDialog

from AccessGrid.TextClientUI import TextClientUI

class VenueClientUI(wxApp, VenueClient):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event. 
    """
    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        VenueClient.__init__(self)        
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(300, 400))
        self.SetTopWindow(self.frame)
        self.client = None
        self.gotClient = false
        return true

    def ConnectToVenue(self):
        myHomePath = os.environ['HOME']
        # venueServerUri = "https://localhost:6000/VenueServer"
        # venueUri = Client.Handle( venueServerUri ).get_proxy().GetDefaultVenue()
        
        # This will set defaults for either of our platforms, hopefully
        if sys.platform == "win32":
            myHomePath = os.environ['HOMEPATH']
        elif sys.platform == "linux2":
            myHomePath = os.environ['HOME']

        accessGridDir = '.AccessGrid'
        self.profilePath = myHomePath+'/'+accessGridDir+'/profile'

        try:  # do we have a profile file
            os.listdir(myHomePath+'/'+accessGridDir)
            
        except:
            os.mkdir(myHomePath+'/'+accessGridDir)

        self.profile = ClientProfile(self.profilePath)
                  
        if self.profile.IsDefault():  # not your profile
            self.__openProfileDialog(self.profile)
        else:
            self.__startMainLoop(self.profile)

    def __openProfileDialog(self):
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', self.profile)

        if (profileDialog.ShowModal() == wxID_OK): 
            self.ChangeProfile(profileDialog.GetNewProfile())
            profileDialog.Destroy()
            self.__startMainLoop(self.profile)
            
        else:
            profileDialog.Destroy()
               
    def __startMainLoop(self, profile):
        self.gotClient = true
        self.SetProfile(profile)

        self.GoToNewVenue(self.profile.homeVenue)

        self.frame.Show(true)
        self.MainLoop()

    def ModifyUserEvent(self, data):
        self.frame.contentListPanel.ModifyParticipant(data)
        pass

    def AddDataEvent(self, data):
        self.frame.contentListPanel.AddData(data)
        pass

    def RemoveDataEvent(self, data):
        self.frame.contentListPanel.RemoveData(data)
        pass

    def AddServiceEvent(self, data):
        self.frame.contentListPanel.AddService(data)
        pass

    def RemoveServiceEvent(self, data):
        self.frame.contentListPanel.RemoveService(data)
        pass

    def AddConnectionEvent(self, data):
        self.frame.venueListPanel.list.AddVenueDoor(data)
        pass

    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        VenueClient.EnterVenue( self, URL )
       
        venueState = self.venueState
        self.frame.SetLabel(venueState.description.name)
        name = self.profile.name
        title = self.venueState.description.name
        description = self.venueState.description.description
        welcomeDialog = WelcomeDialog(NULL, -1, 'Enter Venue', name,
                                      title, description)

        users = venueState.users.values()
        for user in users:
            if(user.profileType == 'user'):
                self.frame.contentListPanel.AddParticipant(user)
            else:
                self.frame.contentListPanel.AddNode(user)

        data = venueState.data.values()
        for d in data:
            self.frame.contentListPanel.AddData(d)

        nodes = venueState.nodes.values()
        for node in nodes:
            self.frame.contentListPanel.AddNode(node)
        services = venueState.services.values()
        for service in services:
            self.frame.contentListPanel.AddService(service)

        exits = venueState.connections.values()
        for exit in exits:
            self.frame.venueListPanel.list.AddVenueDoor(exit)

        # Start text client
        textLoc = tuple(self.venueState.GetTextLocation())
        try:
            self.textClient = TextClientUI(self.frame, -1, "", location = textLoc)
            self.textClient.Show(true)
        except:
            ErrorDialog(self.frame, "Trying to open text client!")

    def ExitVenue(self):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        print '----------- I send exit venue event'
        try:
            self.textClient.Close()
        except:
            (name, args, tb) = formatExceptionInfo()
#            print "Hm: %s %s" % (name, args)
            
        VenueClient.ExitVenue( self )
                                     
    def GoToNewVenue(self, uri):
        if self.venueUri != None:
            oldUri = self.venueUri
        else:
            oldUri = None
            
        try: # is this a server
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            print "URI: %s" % venueUri
        except: # no, it is a venue
            venueUri = uri

        try:  # temporary solution until exceptions work as should
            self.client = Client.Handle(venueUri).get_proxy()
            if oldUri != None:
                print "Cleaning up Old Venue! <%s>" % oldUri
                self.frame.CleanUp()
                self.OnExit()
            self.EnterVenue(venueUri)
        except GSITCPSocketException:
            ErrorDialog(self.frame, sys.exc_info()[1][0])
        except EnterVenueException:
            ErrorDialog(self.frame, "GoToNewVenue:")
            if oldUri != None:
                self.EnterVenue(oldUri)

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        self.ExitVenue()
                
    def AddData(self, data):
        self.client.AddData(data)

    def AddService(self, service):
        self.client.AddService(service)
        
    def RemoveData(self, data):
        self.client.RemoveData(data)

    def RemoveService(self, service):
        self.client.RemoveService(service)
        
    def ChangeProfile(self, profile):
        self.profile = profile
        self.profile.Save(self.profilePath)
        self.SetProfile(self.profile)

        if self.gotClient:
            self.client.UpdateClientProfile(profile)

        
if __name__ == "__main__":

    import sys
    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *
    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()
       

    
  
