#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.35 2003-02-10 21:23:57 lefvert Exp $
# Copyright:   (c) 2002-2003
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
        """
        This method initiates all gui related classes.
        """
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
        """
        This method is called during program startup. If this is the first time
        a user starts the client, a dialog is opened where the user can fill in
        his or her information.  The information is saved in a configuration file
        in /home/.AccessGrid/profile,  next time the program starts this profile
        information will be loaded automatically.  ConnectToVenue tries to connect
        to 'home venue' specified in the user profile, is this fails,  it will ask
        the user for a specific URL to a venue or venue server.
        """
               
        # This will set defaults for either of our platforms, hopefully
        if sys.platform == "win32":
            myHomePath = os.environ['HOMEPATH']
        elif sys.platform == "linux2":
            myHomePath = os.environ['HOME']

        accessGridDir = '.AccessGrid'
        self.profilePath = myHomePath+'/'+accessGridDir+'/profile'

        try:  # do we have a profile file
            os.listdir(myHomePath+'/'+accessGridDir)
            print '------- we have a profile file'
            
        except:
            print '------- no, we don"t have a profile file, make dir'
            os.mkdir(myHomePath+'/'+accessGridDir)

        self.profile = ClientProfile(self.profilePath)
                  
        if self.profile.IsDefault():  # not your profile
            print '------- we have to fill in the profile?'
            self.__openProfileDialog()
        else:
            print '------- start main loop?'
            self.__startMainLoop(self.profile)

    def __openProfileDialog(self):
        """
        This method opens a profile dialog where the user can fill in
        his or her information.  
        """
        print '------------- open profile dialog'
         
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', self.profile)

        if (profileDialog.ShowModal() == wxID_OK):
            print '------------- profile dialog'
            self.profile = profileDialog.GetNewProfile()
            self.ChangeProfile(self.profile)
          
            profileDialog.Destroy()
            self.__startMainLoop(self.profile)
            
        else:
            profileDialog.Destroy()
               
    def __startMainLoop(self, profile):
        """
        This method is called during client startup.  It sets the
        participant profile, enters the venue, and finally starts the
        wxPython main gui loop.
        """
        self.gotClient = true
        self.SetProfile(profile)
        # This test really wants to be "while the venue url is invalid, loop:

        print '---------- try if home profile can connect'
        if self.GoToNewVenue(self.profile.homeVenue):
            print '---------- home profile is good enter main loop'
            self.frame.Show(true)
            self.MainLoop()
        
        else:
            print '---------- home profile is not good'
            validVenue = false
            
            while not validVenue:
                print '---------- not a valid venue'
                connectToVenueDialog = ConnectToVenueDialog(NULL, -1,
                                                            "Please, enter venue or venue server URL")
                if(connectToVenueDialog.ShowModal() == wxID_OK):
                    print '---------- get URL from dialog'
                    if self.GoToNewVenue(connectToVenueDialog.address.GetValue()):
                        print '---------- the URL is ok - enter main loop'
                        self.frame.Show(true)
                        self.MainLoop()
                        notValidVenue = true
                  
                else:
                    print '---------- cancel dialog'
                    break
                #  self.frame.Show(true)
                #  self.MainLoop()

    def ModifyUserEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.
        """
        self.frame.contentListPanel.ModifyParticipant(data)
        pass

    def AddDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        """
        self.frame.contentListPanel.AddData(data)
        pass

    def RemoveDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.
        """
        self.frame.contentListPanel.RemoveData(data)
        pass

    def AddServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is added to the venue.
        Appropriate gui updates are made in client.
        """
        self.frame.contentListPanel.AddService(data)
        pass

    def RemoveServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is removed from the venue.
        Appropriate gui updates are made in client.
        """
        self.frame.contentListPanel.RemoveService(data)
        pass

    def AddConnectionEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
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
        try:
            self.textClient.Close()
        except:
            (name, args, tb) = formatExceptionInfo()

        print '----------exit venue'
        VenueClient.ExitVenue( self )
            
                                     
    def GoToNewVenue(self, uri):
        print '------------ uri: ',uri
        print '------------ go to new venue'
        if self.venueUri != None:
            print '------------ we have an old URL'
            oldUri = self.venueUri
        else:
            print '------------ old URL is none'
            oldUri = None
            
        try: # is this a server
            print '------------ is this a server'
            print uri
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            print '------------ this is a server'
            
        except: # no, it is a venue
            print '------------ this is a venue'
            venueUri = uri

        try:  # temporary solution until we can verify a proxy before hand
            self.client = Client.Handle(venueUri).get_proxy()
            print '------------ get proxy'
            if oldUri != None:
                print '------------ clean up frame'
                self.frame.CleanUp()
                self.ExitVenue()
            print '------------ enter venue - true'
            self.EnterVenue(venueUri)
            print '------------ enter venue - true 2'
            return true
        
        except GSITCPSocketException:
            print '------------ return false'
            return false
        
        except EnterVenueException:
            print '------------ enter venue exception'
            if oldUri != None:
                print 'enter venue'
                self.EnterVenue(oldUri)
            else:
                print '------------ return false'
                return false
    
    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        print '-------------on exit'
        self.ExitVenue()
        os._exit(1)
                
    def AddData(self, data):
        """
        This method adds data to the venue
        """
        self.client.AddData(data)

    def AddService(self, service):
        """
        This method adds a service to the venue
        """
        self.client.AddService(service)
        
    def RemoveData(self, data):
        """
        This method removes a data from the venue
        """
        self.client.RemoveData(data)
       
    def RemoveService(self, service):
        """
        This method removes a service from the venue
        """
        self.client.RemoveService(service)
        
    def ChangeProfile(self, profile):
        """
        This method changes this participants profile
        """
        print '---------- change profile'
        self.profile = profile
        self.profile.Save(self.profilePath)
        self.SetProfile(self.profile)

        if self.gotClient:
            self.client.UpdateClientProfile(profile)

        print '---------- sat profile'

        
if __name__ == "__main__":

    import sys
    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()
       

    
  
