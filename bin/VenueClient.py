#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.158 2003-05-22 20:39:12 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import threading
import os
import logging, logging.handlers
import cPickle
import getopt
import sys

log = logging.getLogger("AG.VenueClient")

from wxPython.wx import *
from wxPython.wx import wxTheMimeTypesManager as mtm

from AccessGrid.hosting.pyGlobus import Server

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid import DataStore

from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Utilities import HaveValidProxy, formatExceptionInfo
from AccessGrid.Utilities import StartDetachedProcess
from AccessGrid.UIUtilities import  MessageDialog, InitMimeTypes
from AccessGrid.UIUtilities import GetMimeCommands, ErrorDialog, ErrorDialogWithTraceback
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN
from AccessGrid.GUID import GUID
from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.VenueClient import VenueClient
from AccessGrid.Platform import GPI, GetUserConfigDir
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog

from AccessGrid import PersonalNode
from AccessGrid import Toolkit

class VenueClientUI(wxApp, VenueClient):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event.
    """
    history = []
    client = None
    clientHandle = None
    venueUri = None
    personalDataStorePrefix = "personalDataStore"
    personalDataStorePort = 9999
    personalDataDict = {}
    accessGridPath = GetUserConfigDir()
    profileFile = os.path.join(accessGridPath, "profile" )
    personalDataStorePath = os.path.join(accessGridPath, personalDataStorePrefix)
    personalDataFile = os.path.join(personalDataStorePath, "myData.txt" )
    isPersonalNode = 0
    debugMode = 0
    transferEngine = None
       
    def __init__(self):
        if not os.path.exists(self.accessGridPath):
            try:
                os.mkdir(self.accessGridPath)
            except OSError, e:
                log.exception("bin.VenueClient::__init__: Could not create base path")

        wxApp.__init__(self, false)
        VenueClient.__init__(self)

    def OnInit(self):
        """
        This method initiates all gui related classes.

        **Returns:**

        *Integer* 1 if initiation is successful 
        """
        self.__processArgs()
        self.__setLogger()

        #
        # We verify first because the Toolkit code assumes a valid
        # globus environment.
        #

        VerifyExecutionEnvironment()

        try:
            self.app = Toolkit.WXGUIApplication()

        except Exception, e:
            log.exception("bin.VenueClient::OnInit: WXGUIApplication creation failed")

            dlg = wxMessageDialog(None, "Application object creation failed\n%s\nThe venue client cannot continue." % (e,),
                                  "Initialization failed",
                                  wxOK)
            dlg.ShowModal()
            dlg.Destroy()
            sys.exit(1)

        try:
            
            self.app.Initialize()

        except Exception, e:
            log.exception("bin.VenueClient::OnInit: App initialization failed")

            ErrorDialogWithTraceback(None, "Application initialization failed. Attempting to continue",
                        "Initialization failed")
        
        #
        # Create and load personal files
        #
        self.__createPersonalDataStore()

        #
        # Initiate user interface components
        #
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(500, 400))
        self.SetTopWindow(self.frame)

        #
        # Tell the UI about installed applications
        #
        self.frame.SetInstalledApps( self.GetInstalledApps() )
        self.frame.EnableAppMenu( false )

        #
        # Load user mailcap from AG Config Dir
        #
        mailcap = os.path.join(GetUserConfigDir(), "mailcap")
        InitMimeTypes(mailcap)

        log.debug("bin.VenueClient::OnInit: ispersonal=%s", self.isPersonalNode)

        if self.isPersonalNode:
            def setSvcCallback(svcUrl, self = self):
                log.debug("bin.VenueClient::OnInit: setting node service URI to %s from PersonalNode", svcUrl)
                self.nodeServiceUri = svcUrl

            self.personalNode = PersonalNode.PersonalNodeManager(setSvcCallback, self.debugMode)
            self.personalNode.Run()

        return true

    def __openProfileDialog(self):
        """
        This method opens a profile dialog, in which the user can fill in
        his or her information.
        """
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile')
        profileDialog.SetProfile(self.profile)

        if (profileDialog.ShowModal() == wxID_OK):
            self.profile = profileDialog.GetNewProfile()
            
            #
            # Change profile based on values filled in to the profile dialog
            #
            self.ChangeProfile(self.profile)
            profileDialog.Destroy()

            #
            # Start the main wxPython thread
            #
            self.__startMainLoop(self.profile)

        else:
            profileDialog.Destroy()
            os._exit(0)

    def __startMainLoop(self, profile):
        """
        This method is called during client startup.  It sets the
        participant profile, enters the venue, and finally starts the
        wxPython main gui loop.
        
        **Arguments:**
        
        *profile* The ClientProfile you want to be associated with in the venue.
        
        """
        
        self.SetProfile(profile)
        self.frame.venueAddressBar.SetAddress(self.profile.homeVenue)
        self.frame.Show(true)
        log.debug("bin.VenueClient::__startMainLoop: start wxApp main loop/thread")
        self.MainLoop()

    def __Usage(self):
        print "%s:" % (sys.argv[0])
        print "  -h|--help:      print usage"
        print "  -d|--debug:     show debugging messages"
        print "  --personalNode: manage services as a personal node"

    def __processArgs(self):
        """
        Handle any arguments we're interested in.

        --personalNode: Handle startup of local node services.

        """

        try:
            opts, args = getopt.getopt(sys.argv[1:], "hd",
                                       ["personalNode", "debug", "help"])

        except getopt.GetoptError:
            self.__Usage()
            sys.exit(2)

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.__Usage()
                sys.exit(0)
            elif opt == '--personalNode':
                self.isPersonalNode = 1
            elif opt in ('--debug', '-d'):
                self.debugMode = 1

    def __createPersonalDataStore(self):
        """
        Creates the personal data storage and loads personal data
        from file to a dictionary of DataDescriptions. If the file is removed
        from local path, the description is not added to the list.
        """

        log.debug("bin.VenueClient::__createPersonalDataStore: Creating personal datastore at %s using prefix %s and port %s" %(self.personalDataStorePath, self.personalDataStorePrefix,self.personalDataStorePort))

        if not os.path.exists(self.personalDataStorePath):
            try:
                os.mkdir(self.personalDataStorePath)
            except OSError, e:
                log.exception("bin.VenueClient::__createPersonalDataStore: Could not create personal data storage path")
                self.personalDataStorePath = None
               
        if self.personalDataStorePath:
                self.dataStore = DataStore.DataStore(self, self.personalDataStorePath,
                                                     self.personalDataStorePrefix)
                self.transferEngine = DataStore.GSIHTTPTransferServer(('',
                                                                       self.personalDataStorePort))
                self.transferEngine.run()
                self.transferEngine.RegisterPrefix(self.personalDataStorePrefix, self)
                self.dataStore.SetTransferEngine(self.transferEngine)

                #
                # load personal data from file
                #
                
                log.debug("bin.VenueClient::__createPersonalDataStore: Load personal data from file")
                if os.path.exists(self.personalDataFile):
                    file = open(self.personalDataFile, 'r')
                    self.personalDataDict = cPickle.load(file)
                    log.debug("bin.VenueClient::__createPersonalDataStore: Personal data dict: %s" %self.personalDataDict)
                    file.close()
                    
                    for file, desc in self.personalDataDict.items():
                        url = self.transferEngine.GetDownloadDescriptor(self.personalDataStorePrefix, file)
                        
                        if url is None:
                            log.debug("bin.VenueClient::__createPersonalDataStore: Personal file %s is not valid, remove it"%file)
                            del self.personalDataDict[file]

    def __setLogger(self):
        """
        Sets the logging mechanism.
        """
        log = logging.getLogger("AG")
        log.setLevel(logging.DEBUG)
        logname = "VenueClient.log"
        hdlr = logging.FileHandler(logname)
        extfmt = logging.Formatter("%(asctime)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(extfmt)
        log.addHandler(hdlr)

        if self.debugMode:
            hdlr = logging.StreamHandler()
            hdlr.setFormatter(fmt)
            log.addHandler(hdlr)
       
    def ConnectToVenue(self):
        """
        This method is called during program startup. If this is the first time
        a user starts the client, a dialog is opened where the user can fill in
        his or her information.  The information is saved in a configuration file,
        when the program starts next time this profile information will be loaded
        automatically.
        """
        self.profile = ClientProfile(self.profileFile)

        if self.profile.IsDefault():  # not your profile
            log.debug("the profile is the default profile - open profile dialog")
            self.__openProfileDialog()
        else:
            self.__startMainLoop(self.profile)

    #
    # Methods to support follow
    #

    def AuthorizeLead(self, clientProfile):
        """
        Note: Overridden from VenueClient
        This method  notifies the user that somebody wants to follow him or
        her and allows the user to approve the request.

        **Arguments:**
        
        *clientProfile* The ClientProfile of the user who wish to lead this client.
        """
        wxCallAfter(self.frame.AuthorizeLeadDialog, clientProfile)


    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        Note: Overridden from VenueClient
        This method notifies the user if the request to follow somebody is approved
        or denied.

        **Arguments:**
        
        *leaderProfile* The ClientProfile of the user we want to follow
        *iaAuthorized* Boolean value set to true if request is approved, else false.
        
        """
        VenueClient.LeadResponse(self, leaderProfile, isAuthorized)
        wxCallAfter(self.frame.NotifyLeadDialog, leaderProfile, isAuthorized)

    LeadResponse.soap_export_as = "LeadResponse"


    def NotifyUnLead(self, clientProfile):
        """
        Note: Overridden from VenueClient
        This method  notifies the user that somebody wants to stop following him or
        her

        **Arguments:**
        
        *clientProfile* The ClientProfile of the client who stopped following this client
        """
        wxCallAfter(self.frame.NotifyUnLeadDialog, clientProfile)

    #
    # Methods handling events sent when venue state changes
    #

    def AddUserEvent(self, user):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant enters
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The ClientProfile of the participant who just  entered the venue
        """
        profile = ClientProfile()
        profile.profileFile = user.profileFile
        profile.profileType = user.profileType
        profile.name = user.name
        profile.email = user.email
        profile.phoneNumber = user.phoneNumber
        profile.icon = user.icon
        profile.publicId = user.publicId
        profile.location = user.location
        profile.venueClientURL = user.venueClientURL
        profile.techSupportInfo = user.techSupportInfo
        profile.homeVenue = user.homeVenue
        profile.privateId = user.privateId
        profile.distinguishedName = user.distinguishedName

        # should also objectify the capabilities, but not doing it 
        # for now (until it's a problem ;-)
        profile.capabilities = user.capabilities

        VenueClient.AddUserEvent(self, profile)

        wxCallAfter(self.frame.contentListPanel.AddParticipant, profile)
        log.debug("  add user: %s" %(profile.name))

    def Heartbeat(self):
        '''
        Note: Overridden from VenueClient
        This method sends a heartbeat to indicate that the client
        is still connected to the venue. If the heartbeat is not
        received properly, the client will exit the venue.
        '''
        
        try:
            VenueClient.Heartbeat(self)
        except:
            log.exception("bin::VenueClient:Heartbeat: Heartbeat exception is caught, exit venue.")
            wxCallAfter(MessageDialog,
                        None,
                        "Your connection to the venue is interrupted and you will be removed from the venue.  \nPlease, try to connect again.",
                        "Lost Connection")
            
            if self.venueUri != None:
                log.debug("call exit venue")
                wxCallAfter(self.frame.CleanUp)
                wxCallAfter(self.frame.venueAddressBar.SetTitle, "You are not in a venue", 'Click "Go" to connect to the venue, which address is displayed in the address bar') 
                self.ExitVenue()
                                        
    def RemoveUserEvent(self, user):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant exits
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The ClientProfile of the participant who just exited the venue
        """
        VenueClient.RemoveUserEvent(self, user)

        wxCallAfter(self.frame.contentListPanel.RemoveParticipant, user)
        log.debug("  remove user: %s" %(user.name))

    def ModifyUserEvent(self, user):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The modified ClientProfile of the participant that just changed profile information
        """
        
        VenueClient.ModifyUserEvent(self, user)
        log.debug("EVENT - Modify participant: %s" %(user.name))
        wxCallAfter(self.frame.contentListPanel.ModifyParticipant, user)

    def AddDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *data* The DataDescription representing data that just got added to the venue
        """
        VenueClient.AddDataEvent(self, data)
        log.debug( "EVENT - Add data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.AddData, data)

    def UpdateDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *data* The DataDescription representing data that just got updated in the venue
        """
        VenueClient.UpdateDataEvent(self, data)
        log.debug("EVENT - Update data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.UpdateData, data)

    def RemoveDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *data* The DataDescription representing data that just got removed from the venue
        """
        VenueClient.RemoveDataEvent(self, data)
        log.debug("EVENT - Remove data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.RemoveData, data)

    def AddApplicationEvent(self, app):
        """
        Note: Overridden from VenueClient
        This method is called every time a new application is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *app* The ApplicationDescription representing the application that just got added to the venue
        """
        log.debug("EVENT - Add application: %s, Mime Type: %s" %(app.name, app.mimeType))
        wxCallAfter(self.frame.contentListPanel.AddApplication, app)

    def RemoveApplicationEvent(self, app):
        """
        Note: Overridden from VenueClient
        This method is called every time an application is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *app* The ApplicationDescription representing the application that just got removed from the venue
        """
        log.debug("EVENT - Remove application: %s" %(app.name))
        wxCallAfter(self.frame.contentListPanel.RemoveApplication, app)

    def AddServiceEvent(self, service):
        """
        Note: Overridden from VenueClient
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *service* The ServiceDescription representing the service that just got added to the venue
        """
        VenueClient.AddServiceEvent(self, service)
        log.debug("EVENT - Add service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.AddService, service)

    def RemoveServiceEvent(self, service):
        """
        Note: Overridden from VenueClient
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *service* The ServiceDescription representing the service that just got removed from the venue
        """
        VenueClient.RemoveServiceEvent(self, service)
        log.debug("EVENT - Remove service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.RemoveService, service)

    def AddConnectionEvent(self, connection):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connection* The ConnectionDescription representing the exit that just got added to the venue
        """
                
        VenueClient.AddConnectionEvent(self, connection)
        log.debug("EVENT - Add connection: %s" %(connection.name))
        wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def SetConnectionsEvent(self, connections):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connections* A list of ConnectionDescriptions representing all the exits in the venue.
        """
        VenueClient.SetConnectionsEvent(self, connections)
        log.debug("EVENT - Set connections")
        wxCallAfter(self.frame.venueListPanel.CleanUp)

        for connection in connections:
            log.debug("EVENT - Add connection: %s" %(connection.name))
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def EnterVenue(self, URL, back = false):
        """
        Note: Overridden from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
      
        **Arguments:**
        
        *URL* A string including the venue address we want to connect to
        *back* Boolean value, true if the back button was pressed, else false.
        
        """
        log.debug("bin.VenueClient::EnterVenue: Enter venue with url: %s" %(URL))

        #
        # Check to see if we have a valid grid proxy
        # If not, run grid proxy init
        #
        if not HaveValidProxy():
            log.debug("VenueClient::EnterVenue: You don't have a valid proxy")
            GPI()
        #   
        # Add current uri to the history if the go button is pressed
        #
        self.__setHistory(self.venueUri, back)

       
        #
        # If the url parameter is a server address, get default venue
        # else assume the url is a venue address.
        #

        self.venueUri = URL
        self.clientHandle = Client.Handle(self.venueUri)

        #
        # if this venue url has a valid web service then enter venue
        #
        log.debug("check client for validity")
        if(self.clientHandle.IsValid()):
            self.client = self.clientHandle.get_proxy()
            log.debug("OK")

            #
            # Tell super class to enter venue
            #
            try:
                warningString = VenueClient.EnterVenue( self, URL )
            #
            # Catch all fatal exceptions that will result in an enter venue failure.
            #
            except Exception, e:
                log.exception("bin.VenueClient::EnterVenue failed")
                text = "You have not entered the venue, an error occured.  Please, try again.\n\nNote: Read VenueClient.log for more detailed information"
                MessageDialog(None, text, "Enter Venue Error",
                              style = wxOK  | wxICON_ERROR)
            else:
                #
                # clean up ui from current venue before entering a new venue
                #
                if self.venueUri != None:
                    log.debug("clean up frame")
                    wxCallAfter(self.frame.CleanUp)
                #
                # Get current state of the venue
                #
                venueState = self.venueState
                wxCallAfter(self.frame.venueAddressBar.SetTitle, venueState.name, venueState.description) 

                #
                # Load clients
                #
                clients = venueState.clients.values()
                log.debug("Add participants")

                for client in clients:
                    wxCallAfter(self.frame.contentListPanel.AddParticipant, client)
                    log.debug("   %s" %(client.name))
                #    
                # Load data
                #
                data = venueState.data.values()
                log.debug("Add data")
                for d in data:
                    wxCallAfter(self.frame.contentListPanel.AddData, d)
                    log.debug("   %s" %(d.name))
                 
                #
                # Load services
                #
                services = venueState.services.values()
                log.debug("Add service")
                for s in services:
                    wxCallAfter(self.frame.contentListPanel.AddService, s)
                    log.debug("   %s" %(s.name))

                #
                # Load applications
                #
                applications = venueState.applications.values()
                log.debug("Add application")
                for a in applications:
                    wxCallAfter(self.frame.contentListPanel.AddApplication, a)
                    log.debug("   %s" %(a.name))

                #
                #  Load exits
                #
                log.debug("Add exits")
                exits = venueState.connections.values()
                for exit in exits:
                    wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, exit)
                    log.debug("   %s" %(exit.name))

                #
                # Tell the text client which location it should listen to
                #
                log.debug("Set text location and address bar")
                wxCallAfter(self.frame.SetTextLocation)
                wxCallAfter(self.frame.FillInAddress, None, URL)
                self.venueUri = URL

                #
                # Venue data storage location
                #
                self.upload_url = self.client.GetUploadDescriptor()
                log.debug("Get upload url %s" %self.upload_url)

                #
                # Add your personal data descriptions to venue
                #
                log.debug("Add your personal data descriptions to venue")
                personalDataWarning = self.__addPersonalDataToVenue()
                warningString = warningString + personalDataWarning
                #
                # Enable menus
                #
                wxCallAfter(self.frame.ShowMenu)

                #
                # Enable the application menu that is displayed over
                # the Applications items in the list (this is not the app menu above)
                #
                wxCallAfter(self.frame.EnableAppMenu, true)

                #
                # Call EnterVenue on users that are following you.
                # This should be done last for UI update reasons.
                #
                log.debug("Lead followers")
                self.LeadFollowers()
                
                log.debug("Entered venue")

                #
                # Display all non fatal warnings to the user
                #
                if warningString != '': 
                    message = "Following non fatal problems have occured when you entered the venue:\n" + warningString
                    MessageDialog(None, message, "Notification")
                   
        else:
            log.debug("VenueClient::EnterVenue: Handler is not valid")
            if not HaveValidProxy():
                text = 'You do not have a valid proxy.' +\
                       '\nPlease, run "grid-proxy-init" on the command line"'
                text2 = 'Invalid proxy'
                
            else:
                text = 'You were not able to enter the venue.  Please, make sure the venue URL address is correct.\n\nNote: If your computer clock is not synchronized you might be unable to connect to a venue.'
                text2 = 'Invalid URL'

            MessageDialog(None, text, text2)

    EnterVenue.soap_export_as = "EnterVenue"

    def __addPersonalDataToVenue(self):
        '''
        Adds all personal data, stored in local file directory as a dictionary, to the venue.
       
        **Returns:**
        
        *String* A warning string including information about data that could not be added to the venue
        '''
        #
        # Add personal data to venue
        #
        duplicateData = []
        for data in self.personalDataDict.values():
            log.debug("Add personal file %s to venue" %data.name)

            url = self.dataStore.GetDownloadDescriptor(data.name)

            #
            # Is the file still present?
            #
            if url is None:
                log.debug("Personal file %s has vanished" %data.name)
                del self.personalDataDict[data.name]

            #
            # Is there a file in the venue with the same name?
            #
            elif(self.venueState.data.has_key(data.name)):
                duplicateData.append(data.name)

            else:
                try:
                    self.client.AddData(data)
                except Exception, e:
                    duplicateData.append(data.name)
        #
        # Notify user of what files already exist in the venue
        #
        if(len(duplicateData)>0):
            files = ''
            for file in duplicateData:
                files = files + ' ' +file + ','

            return "\n\nPersonal data, %s \nalready exists in the venue and could not be added" %files

        else:
            return ''
                
    def ExitVenue(self):
        """
        Note: Overridden from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        log.debug("exit venue")

        #
        # Shut down the text client
        #

        wxCallAfter(self.frame.CloseTextConnection)
        VenueClient.ExitVenue(self)

    def __setHistory(self, uri, back):
        """
        This method sets the history list, which stores visited
        venue urls used by the back button.  A venue URL does not get
        saved if the back (<<) button is clicked.

        **Arguments:**
        
        *uri* A string containing the venue address we want to add to the history list
        *back* Boolean value, true if the back button was pressed, else false.
        """
        log.debug("Set history url: %s " %uri)
        length = len(self.history)
        last = length -1

        if(length>0):
            
            #
            # Clicked the "Go" button
            #
            if not back:
                #
                # Just add the url once even if we press "Go" several times
                #
                if(self.history[last] != uri):
                    self.history.append(uri)
            #
            # Clicked the "<<" button
            #
            else:
                del self.history[last] # clicked back button

        elif(uri is not None):
            #
            # If this is the first time connecting to a venue, just add the url
            #
            self.history.append(uri)
            
    def GoBack(self):
        """
        This method is called when the user wants to go back to last visited venue
        """
        log.debug("Go back")

        l = len(self.history)
        if(l>0):
            #
            # Go to last venue in the history list
            #
            uri = self.history[l - 1]
            self.EnterVenue(uri, true)

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        log.info("--------- END VenueClient")

        #
        # If we are connected to a venue, exit the venue
        # Do this before terminating services, since we need
        # to message them to shut down their services first
        #
        if self.isInVenue:
            self.ExitVenue()

        #
        # If we're running as a personal node, terminate the services.
        #
        if self.isPersonalNode:
            log.debug("Terminating services")
            self.personalNode.Stop()

        #
        # save personal data
        #
        
        file = open(self.personalDataFile, 'w')
        cPickle.dump(self.personalDataDict, file)
        file.close()

        #
        # stop personal data server
        #  
        if self.transferEngine:
            self.transferEngine.stop()

        os._exit(0)

    def SaveFile(self, data_descriptor, local_pathname):
        """
        Save a file from the datastore into a local file.

        We assume that the caller has assured the user that if the
        user has picked a file that already exists, that it will be
        overwritten.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers, to allow for live updates of a download status,
        and to perhaps allow multiple simultaneous transfers.

        """
        log.debug("Save file descriptor: %s, path: %s"
                  % (data_descriptor, local_pathname))

        failure_reason = None
        try:
            #
            # Retrieve details from the descriptor
            #
            size = data_descriptor.size
            checksum = data_descriptor.checksum
            url = data_descriptor.uri

            #
            # Make sure this data item is valid
            #
            log.debug("data descriptor is %s" %data_descriptor.__class__)

            if data_descriptor.status != DataDescription.STATUS_PRESENT:
                MessageDialog(None,
                              "File %s is not downloadable - it has status %s"
                              % (data_descriptor.name,
                                 data_descriptor.status), "Notification")
                return
            #
            # Create the dialog for the download.
            #
            dlg = SaveFileDialog(self.frame, -1, "Saving file",
                                 "Saving file to %s ...     "
                                 % (local_pathname),
                                 "Saving file to %s ... done"
                                 % (local_pathname),
                                 size)
            
            log.debug("Downloading: size=%s checksum=%s url=%s"
                      % (size, checksum, url))

            dlg.Show(1)

            #
            # Plumbing for getting progress callbacks to the dialog
            #
            def progressCB(progress, done, dialog = dlg):
                wxCallAfter(dialog.SetProgress, progress, done)
                return dialog.IsCancelled()

            #
            # Create the thread to run the download.
            #
            # Some more plumbing with the local function to get the identity
            # retrieval in the thread, as it can take a bit the first time.
            #
            # We use get_ident_and_download as the body of the thread.

            # Arguments to pass to get_ident_and_download
            #
            dl_args = (url, local_pathname, size, checksum, progressCB)
                
            download_thread = threading.Thread(target = self.get_ident_and_download,
                                               args = dl_args)

            #
            # Use wxCallAfter so we get the dialog filled in properly.
            #
            wxCallAfter(download_thread.start)

            #
            # Fire up dialog as a modal.
            #
            dlg.ShowModal()

            #
            # The dialog has returned. This is either because the download
            # finished and the user clicked OK, or because the user clicked
            # Cancel to abort the download. In either event the
            # call to HTTPDownloadFile should return, and the thread quit.
            #
            # Wait for the thread to finish (if it doesn't it's a bug).
            #
            download_thread.join()

            #
            # Clean up.
            #
            dlg.Destroy()

        except DataStore.DownloadFailed, e:
            failure_reason = "Download error: %s" % (e[0])
        except EnvironmentError, e:
            failure_reason = "Exception: %s" % (str(e))

        if failure_reason is not None:
            wxCallAfter(MessageDialog, None, failure_reason, "Download error",
                        wxOK  | wxICON_ERROR)

    def SaveFileNoProgress(self, data_descriptor, local_pathname):
        """
        Save a file from the datastore into a local file.

        We assume that the caller has assured the user that if the
        user has picked a file that already exists, that it will be
        overwritten.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers, to allow for live updates of a download status,
        and to perhaps allow multiple simultaneous transfers.

        """
        log.debug("Save file descriptor: %s, path: %s"%(data_descriptor, local_pathname))

        failure_reason = None
        try:
            #
            # Retrieve details from the descriptor
            #
            size = data_descriptor.size
            checksum = data_descriptor.checksum
            url = data_descriptor.uri

            #
            # Make sure this data item is valid
            #
            log.debug("data descriptor is %s" %data_descriptor.__class__)

            if data_descriptor.status != DataDescription.STATUS_PRESENT:
                MessageDialog(None,
                              "File %s is not downloadable - it has status %s"
                              % (data_descriptor.name,
                                 data_descriptor.status), "Notification")
                return
            #
            # Create the thread to run the download.
            #
            # Some more plumbing with the local function to get the identity
            # retrieval in the thread, as it can take a bit the first time.
            #
            # We use get_ident_and_download as the body of the thread.

            # Arguments to pass to get_ident_and_download
            #
            dl_args = (url, local_pathname, size, checksum,
                       lambda done, dialog: None)
            download_thread = threading.Thread(target = self.get_ident_and_download,
                                               args = dl_args)
            download_thread.start()
            download_thread.join()
        except DataStore.DownloadFailed, e:
            failure_reason = "Download error: %s" % (e[0])
        except EnvironmentError, e:
            failure_reason = "Exception: %s" % (str(e))

        if failure_reason is not None:
            MessageDialog(None, failure_reason, "Download error",
            style = wxOK  | wxICON_ERROR)

    def get_ident_and_download(self, url, local_pathname, size, checksum, progressCB):
        log.debug("Get ident and download")
        try:
            if url.startswith("https"):
                log.debug("url=%s, local path =%s, size = %s, checksum = %s"%(url, local_pathname, size, checksum))
                DataStore.GSIHTTPDownloadFile(url, local_pathname, size,
                                              checksum, progressCB)
                log.debug("finished GSIHTTPDownload")

            else:
                log.debug("url does not start with https")
                my_identity = GetDefaultIdentityDN()
                DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                                           checksum, progressCB)
        except DataStore.DownloadFailed, e:
            log.exception("bin.VenueClient:get_ident_and_download: Got exception on download")
            wxCallAfter(MessageDialog, None, "The file could not be downloaded", "Download Error",  wxOK | wxICON_ERROR)
            
    def UploadPersonalFiles(self, fileList):
        """
        Upload the given personal files to the venue.

        """
        log.debug("Upload personal files")
        try:
            self.dataStore.AddFile(fileList, self.profile.distinguishedName, self.profile.publicId)

        except DataStore.DuplicateFile, e:
            title = "Add Personal Data Error"
            MessageDialog(self.frame, e, title, style = wxOK|wxICON_ERROR)

        except Exception, e:
            log.exception("bin.VenueClient:UploadPersonalFiles failed")
            title = "Add Personal Data Error"
            text = "The file could not be added, error occured."
            MessageDialog(self.frame, text, title, style = wxOK|wxICON_ERROR)
         
    def UploadVenueFiles(self, file_list):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.
        
        """
        url = self.upload_url
        method = self.get_ident_and_upload

        #
        # Create the dialog for the download.
        #
        dlg = UploadFilesDialog(self.frame, -1, "Uploading files")

        dlg.Show(1)

        #
        # Plumbing for getting progress callbacks to the dialog
        #
        def progressCB(filename, sent, total, file_done, xfer_done,
            dialog = dlg):
            wxCallAfter(dialog.SetProgress, filename, sent, total,
                        file_done, xfer_done)
            return dialog.IsCancelled()

        #
        # Create the thread to run the upload.
        #
        # Some more plumbing with the local function to get the identity
        # retrieval in the thread, as it can take a bit the first time.
        # We use get_ident_and_upload as the body of the thread.

        #
        # Arguments to pass to get_ident_and_upload
        #
        ul_args = (url, file_list, progressCB)

        log.debug("Have args, creating thread, url: %s, files: %s", url, file_list)

        upload_thread = threading.Thread(target = method, args = ul_args)

        #
        # XXX is the wxCallAfter really needed here?
        #
        wxCallAfter(upload_thread.start)
        log.debug("Started thread")
        dlg.ShowModal()

        #
        # The dialog has returned. This is either because the upload
        # finished and the user clicked OK, or because the user clicked
        # Cancel to abort the upload. In either event the
        # call to HTTPUploadFiles should return, and the thread quit.
        #
        # Wait for the thread to finish (if it doesn't it's a bug).
        #
        upload_thread.join()
        dlg.Destroy()

    def get_ident_and_upload(self, upload_url, file_list, progressCB):
        log.debug("Upload: getting identity")

        error_msg = None
        try:
            if upload_url.startswith("https:"):
                log.debug("Url starts with https:")
                DataStore.GSIHTTPUploadFiles(upload_url, file_list, progressCB)
            else:
                my_identity = GetDefaultIdentityDN()
                log.debug("Got identity %s" % my_identity)
                DataStore.HTTPUploadFiles(my_identity, upload_url,
                file_list, progressCB)

        except DataStore.FileNotFound, e:
            error_msg = "File not found: %s" % (e[0])
        except DataStore.NotAPlainFile, e:
            error_msg = "Not a plain file: %s" % (e[0])
        except DataStore.UploadFailed, e:
            error_msg = "Upload failed: %s" % (e)
        except Exception, e:
            error_msg = "Upload failed"

        if error_msg is not None:
            log.exception("bin.VenueClient::get_ident_and_upload: Upload data error")
            wxCallAfter(MessageDialog,
                        None, error_msg,
                        "Upload Files Error", wxOK | wxICON_ERROR)
               
    def UploadFilesNoDialog(self, file_list):
        """
        Upload the given files to the venue.

        This uses the DataStore HTTP upload engine code.
        """

        log.debug("Upload files - no dialog. upload_url=%s", self.upload_url)
        upload_url = self.upload_url

        error_msg = None
        try:
            if upload_url.startswith("https:"):
                DataStore.GSIHTTPUploadFiles(upload_url, file_list)
            else:
                my_identity = GetDefaultIdentityDN()
                DataStore.HTTPUploadFiles(my_identity, upload_url, file_list)
        except DataStore.FileNotFound, e:
            error_msg = "File not found: %s" % (e[0])
        except DataStore.NotAPlainFile, e:
            error_msg = "Not a plain file: %s" % (e[0])
        except DataStore.UploadFailed, e:
            error_msg = "Upload failed: %s" % (e)
        except Exception, e:
            error_msg = "Upload failed"

        if error_msg is not None:
            log.exception("bin.VenueClient::UploadFilesNoDialog: Upload files failed")
            MessageDialog(None, error_msg, "Upload Files Error", style = wxOK|wxICON_ERROR)
           
    def AddData(self, data):
        """
        This method adds local personal data to the venue

        **Arguments:**
        
        *data* The DataDescription we want to add to personal data
        """
        log.debug("Adding data: %s to venue" %data.name)
        
        try:
            self.client.AddData(data)
            self.personalDataDict[data.name] = data
            
        except:
            log.exception("bin.VenueClient::AddData: Error occured when trying to add data")
            MessageDialog(None, "The files could not be added", "Add Personal Files Error")
           
    def RemoveData(self, data):
        """
        This method removes a data from the venue. If the data is personal, this method
        also removes the data from the personal data storage.

        **Arguments:**
        
        *data* The DataDescription we want to remove from vnue
        """
        log.debug("Remove data: %s from venue" %data.name)
        try:
            self.client.RemoveData(data)
            if(data.type == self.profile.publicId and self.personalDataDict.has_key(data.name)):
                del self.personalDataDict[data.name]
                self.dataStore.DeleteFile(data.name)

        except:
            log.exception("bin.VenueClient::RemoveData: Error occured when trying to remove data")
            MessageDialog(None, "The file could not be removed", "Remove Personal Files Error", style = wxOK | wxICON_ERROR)
          
    def AddService(self, service):
        """
        This method adds a service to the venue

        **Arguments:**
        
        *service* The ServiceDescription we want to add to the venue
        """
        log.debug("Adding service: %s to venue" %service.name)
        try:
            self.client.AddService(service)

        except:
            log.exception("bin.VenueClient::AddService: Error occured when trying to add service")
            MessageDialog(None, "The service could not be added", "Add Service Error", style = wxOK | wxICON_ERROR)
          
    def OpenService(self, service):
        """
        open the specified service

        **Arguments:**
        
        *service* The ServiceDescription representing the service we want to open
        """
        log.debug("Opening service: %s / %s" % (service.name,
                                                 service.mimeType))
        commands = GetMimeCommands(filename=service.uri, type=service.mimeType)
       
        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % service.mimeType
            dlg = MessageDialog(None, message )
            log.debug(message)

        else:
            try:
                if commands.has_key('open'):
                    log.debug("executing cmd: %s" % commands['open'])
                    if commands['open'][0:6] == "WX_DDE":
                        pid = wxExecute(commands['open'])
                    else:
                        pid = wxShell(commands['open'])
            except:
                log.exception("bin.VenueClient::OpenService: Open service failed")
                MessageDialog(None, "The service could not be opened", "Open Service Error", style = wxOK | wxICON_ERROR)
                
    def RemoveService(self, service):
        """
        This method removes a service from the venue

        **Arguments:**
        
        *service* The ServiceDescription representing the service we want to remove from the venue
        """
        log.debug("Remove service: %s from venue" %service.name)
        try:
            self.client.RemoveService(service)

        except:
            log.exception("bin.VenueClient::RemoveService: Error occured when trying to remove service")
            MessageDialog(None, "The service could not be removed", "Remove Service Error", style = wxOK | wxICON_ERROR)
            
    def ChangeProfile(self, profile):
        """
        This method changes this participants profile and saves the information to file.

        **Arguments:**
        
        *profile* The ClientProfile including the new profile information
        """
        self.profile = profile
        self.profile.Save(self.profileFile)
        log.debug("Save profile")

        # use profile from path
        self.profile = ClientProfile(self.profileFile)
        self.SetProfile(self.profile)

        if(self.venueUri != None):
            log.debug("Update client profile in venue")

            try:
                self.client.UpdateClientProfile(profile)

            except:
                log.exception("bin.VenueClient::ChangeProfile: Error occured when trying to update profile")
                MessageDialog(None, "Your profile could not be changed", "Change Profile Error", style = wxOK | wxICON_ERROR)
        else:
            log.debug("Can not update client profile in venue - not connected")

    def SetNodeUrl(self, url):
        """
        This method sets the node service url

        **Arguments:**
        
        *url* The string including the new node url address
        """
        log.debug("Set node service url:  %s" %url)
        self.nodeServiceUri = url

    #
    # Methods for personal data storage to call
    #
    def GetData(self, filename):
        '''
        This method is called by the personal DataStore to get a
        DataDescription from the VenueClient.

        **Arguments:**
        
        *filename* The name of the file we want to locate

        **Returns:** 

        *DataDescription* The DataDescription representing the data named filename.
        If the file is not present among personal data, None is returned
        '''
        log.debug("Get private data description: %s" %filename)
        if self.personalDataDict.has_key(filename):
            d = self.personalDataDict[filename]

        else:
            log.debug("The private file does not exist")
            d = None
        return d

    def GetVenueData(self, filename):
        '''
        This method is called by the personal DataStore to get a
        DataDescription present in the venue.

        **Arguments:**
        
        *filename* The name of the file we want to locate

        **Returns:**
        
        *DataDescription* The DataDescription representing the data named filename.
        If the file is not present in the venue, None is returned.

        '''
        log.debug("Get venue data description: %s" %filename)
        log.debug("Venue state: %s" %str(self.venueState.data))
        if self.venueState.data.has_key(filename):
            d = self.venueState.data[filename]
        else:
            log.debug("The venue file does not exist")
            d = None
        return d

    def UpdateData(self, data):
        '''
        This method is called by the personal DataStore to update a
        DataDescription.
        
        **Arguments:**
        
        *data* The DataDescription of the data we want to update
        '''
        self.personalDataDict[data.GetName()] = data
        self.client.UpdateData(data)
        log.debug("UpdateData: %s" %data)

    #
    # Application Integration code
    #
    def StartApp(self,app):
        """
        Start the specified application.  This method creates the application
        in the venue, and then joins it by starting the appropriate client

        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to start
        """
        log.debug("Creating application: %s" % app.name)
        appDesc = self.client.CreateApplication( app.name, app.description,
                                                 app.mimeType )
        self.JoinApp(appDesc)

    def JoinApp(self,app):
        """
        Join the specified application

        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to join
        """
        log.debug("Joining application: %s / %s" % (app.name, app.mimeType))
        commands = GetMimeCommands(filename=app.uri, type=app.mimeType)

        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % app.mimeType
            dlg = MessageDialog(None, message )
            log.debug(message)
        else:
            if commands.has_key('open'):
                log.debug("executing cmd: %s" % commands['open'])
                if commands['open'][0:6] == "WX_DDE":
                    pid = wxExecute(commands['open'])
                else:
                    StartDetachedProcess(commands['open'])

    def RemoveApp(self,app):
        """
        Delete the specified application from the venue
        
        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to remove from venue
        """
        self.client.DestroyApplication( app.id )
        log.debug("Destroying application: %s" % app.name)

if __name__ == "__main__":

    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()
