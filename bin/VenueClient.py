#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.193 2003-08-14 17:27:35 eolson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------


import threading
import os
import logging, logging.handlers
import cPickle
import getopt
import sys
import urlparse
import time

log = logging.getLogger("AG.VenueClient")

#
# Preload some stuff. This speeds up app startup drastically.
#
# Only do this on windows, Linux is fast enough as it is.
#

if sys.platform == "win32":

    from pyGlobus import utilc, gsic, ioc
    from AccessGrid.hosting.pyGlobus import Utilities
    utilc.globus_module_activate(gsic.get_module())
    utilc.globus_module_activate(ioc.get_module())
    Utilities.CreateTCPAttrAlwaysAuth()

#
# Back to your normal imports.
#

from wxPython.wx import *
from wxPython.wx import wxTheMimeTypesManager as mtm

from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.hosting.pyGlobus import Client

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid import DataStore
from AccessGrid import PersonalNode
from AccessGrid import Toolkit
from AccessGrid.Toolkit import AG_TRUE, AG_FALSE

from AccessGrid import Events
from AccessGrid.CertificateManager import CertificateManager
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.Utilities import StartDetachedProcess
from AccessGrid.UIUtilities import MessageDialog, InitMimeTypes, ProgressDialog
from AccessGrid.UIUtilities import GetMimeCommands, ErrorDialog
from AccessGrid.UIUtilities import ErrorDialogWithTraceback
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.GUID import GUID
from AccessGrid.VenueClient import VenueClient
from AccessGrid.VenueClientEventSubscriber import VenueClientEventSubscriber
from AccessGrid.Platform import GetUserConfigDir

class VenueClientUI(wxApp, VenueClientEventSubscriber):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event.
    """
    history = []
    accessGridPath = GetUserConfigDir()
    profileFile = os.path.join(accessGridPath, "profile" )
  
    isPersonalNode = 0
    debugMode = 0
    transferEngine = None

    fallbackRecoveryUrl = None
    
    def __init__(self, startupDialog):
        self.startupDialog = startupDialog
        self.startupDialog.UpdateOneStep()
        if not os.path.exists(self.accessGridPath):
            try:
                os.mkdir(self.accessGridPath)
            except OSError, e:
                log.exception("bin.VenueClient::__init__: Could not create base path")
        self.venueClient = VenueClient()
        self.venueClient.AddEventSubscriber(self)
        wxApp.__init__(self, false)
        self.onExitCalled = false
        self.startupDialog.UpdateOneStep()
        # State kept so UI can add venue administration options.
        self.isVenueAdministrator = false
        
    def OnInit(self):
        """
        This method initiates all gui related classes.

        **Returns:**

        *Integer* 1 if initiation is successful 
        """
        self.startupDialog.UpdateOneStep()
         
        self.__processArgs()
        self.__setLogger()

        #
        # We verify first because the Toolkit code assumes a valid
        # globus environment.
        #
        self.startupDialog.UpdateOneStep()

        VerifyExecutionEnvironment()
       
        try:
            self.startupDialog.UpdateOneStep()
            
            self.app = Toolkit.WXGUIApplication()

        except Exception, e:
            log.exception("bin.VenueClient::OnInit: WXGUIApplication creation failed")

            text = "Application object creation failed\n%s\nThe venue client cannot continue." % (e,)
            ErrorDialog(None, text, "Initialization failed",
                          style = wxOK  | wxICON_ERROR)
            sys.exit(1)

        try:
            self.app.Initialize()

        except Exception, e:
            log.exception("bin.VenueClient::OnInit: App initialization failed")
            
            #ErrorDialogWithTraceback(None, "Application initialization failed. Attempting to continue",
            #            "Initialization failed")

            ErrorDialog(None, "Application initialization failed. Attempting to continue",
                        "Initialization failed")
        
        #
        # Initiate user interface components
        #
        self.startupDialog.UpdateOneStep()
         
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(500, 400))
        self.SetTopWindow(self.frame)
        
        #
        # Tell the UI about installed applications
        #
        self.startupDialog.UpdateOneStep()
        
        self.frame.SetInstalledApps( self.venueClient.GetInstalledApps() )
        self.frame.EnableAppMenu( false )
       
        #
        # Load user mailcap from AG Config Dir
        #
        self.startupDialog.UpdateOneStep()
         
        mailcap = os.path.join(GetUserConfigDir(), "mailcap")
        InitMimeTypes(mailcap)

        log.debug("bin.VenueClient::OnInit: ispersonal=%s", self.isPersonalNode)

        if self.isPersonalNode:
            def setSvcCallback(svcUrl, self = self):
                log.debug("bin.VenueClient::OnInit: setting node service URI to %s from PersonalNode", svcUrl)
                self.venueClient.nodeServiceUri = svcUrl


            self.personalNode = PersonalNode.PersonalNodeManager(setSvcCallback, self.debugMode)
            self.personalNode.Run()


        #
        # Initialize globus runtime stuff.
        #
        self.startupDialog.UpdateOneStep()

        self.app.InitGlobusEnvironment()

        self.startupDialog.UpdateOneStep()
       
        return true

    def __openProfileDialog(self):
        """
        This method opens a profile dialog, in which the user can fill in
        his or her information.
        """
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile')
        profileDialog.SetProfile(self.venueClient.profile)

        if (profileDialog.ShowModal() == wxID_OK):
            self.venueClient.profile = profileDialog.GetNewProfile()
            
            #
            # Change profile based on values filled in to the profile dialog
            #
            self.ChangeProfile(self.venueClient.profile)
            profileDialog.Destroy()

            #
            # Start the main wxPython thread
            #
            self.__startMainLoop(self.venueClient.profile)

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

        log.debug("bin.VenueClient: SetProfile")
        self.venueClient.SetProfile(profile)
        self.frame.venueAddressBar.SetAddress(self.venueClient.profile.homeVenue)
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

        self.logFile = None

        try:
            opts, args = getopt.getopt(sys.argv[1:], "hdl:",
                                       ["personalNode", "debug", "help", "logfile="])

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
            elif opt in ('--logfile', '-l'):
                self.logFile = arg

  
    def __setLogger(self):
        """
        Sets the logging mechanism.
        """
        log = logging.getLogger("AG")
        log.setLevel(logging.DEBUG)

        if self.logFile is None:
            logname = "VenueClient.log"
        else:
            logname = self.logFile
            
        hdlr = logging.FileHandler(logname)
        extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
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
        self.venueClient.profile = ClientProfile(self.profileFile)

        if self.venueClient.profile.IsDefault():  # not your profile
            log.debug("the profile is the default profile - open profile dialog")
            self.__openProfileDialog()
        else:
            # self.profile.publicId = str(GUID())
            self.__startMainLoop(self.venueClient.profile)

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
        wxCallAfter(self.frame.NotifyLeadDialog, leaderProfile, isAuthorized)


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

    def AddUserEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant enters
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The ClientProfile of the participant who just  entered the venue
        """

        user = event.data
        
        wxCallAfter(self.frame.statusbar.SetStatusText, "%s just entered the venue" %user.name)
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

        #
        # Ugh. The baseclass appears to want the processed event data,
        # so we'll create a new event object that has the processed
        # data.
        #

        newEvent = Events.Event(event.eventType, event.venue, profile)

        wxCallAfter(self.frame.contentListPanel.AddParticipant, profile)
        log.debug("  add user: %s" %(profile.name))

    def Heartbeat(self, isSuccess):
        '''
        Note: Overridden from VenueClient
        This method sends a heartbeat to indicate that the client
        is still connected to the venue. If the heartbeat is not
        received properly, the client will exit the venue.
        '''
        
        if not isSuccess:
            wxCallAfter(self.HandleServerConnectionFailure)

    def _TryReconnect(self):
        """
        """
        log.debug("Trying to reconnect")
        attempts = 3
        connected = 0
        while attempts > 0:
            try:
                self.venueClient.EnterVenue(self.venueClient.Uri)
                attempts = 0
                connected = 1
            except:
                attempts = attempts - 1

        if connected == 0 and attempts == 0:
            if self.venueClient.venueUri != self.fallbackRecoveryUrl:
                self.venueClient.EnterVenue(self.fallbackRecoveryUrl)
                self.fallbackRecoveryUri = None
            else:
                self.fallbackRecoveryTimer.cancel()
                self.fallbackRecoveryTimer = None

    def HandleServerConnectionFailure(self):
        log.debug("bin::VenueClient::HandleServerConnectionFailure: call exit venue")
        # Try backup server if that's configured
        if len(self.venueClient.venueState.backupServer) > 0:
            log.debug("falling back to server: %s",
                      self.venueClient.venueState.backupServer)

            urlparts = list(urlparse.urlparse(self.venueClient.venueUri))
            urlparts[1] = self.venueClient.venueState.backupServer
            backupurl = urlparse.urlunparse(urlparts)

            log.debug("current venue: %s, backup venue: %s",
                      self.venueClient.venueUri,
                      backupurl)

            oldUrl = self.venueClient.venueUri

            self.venueClient.EnterVenue(backupurl)

            log.debug("Testing recovery url")
            if self.fallbackRecoveryUrl == None:
                log.debug("trying to recover")
                self.fallbackRecoveryUrl = oldUrl
                self.fallbackRecoveryTimer = threading.Timer(10.0,
                                                             self._TryReconnect)
                self.fallbackRecoveryTimer.start()
        else:
            # If not ohwell, you're stuck
            self.frame.CleanUp()
            self.frame.venueAddressBar.SetTitle("You are not in a venue",
                                                'Click "Go" to connect to the venue, which address is displayed in the address bar') 
            self.venueClient.ExitVenue()
            MessageDialog(None, "Your connection to the venue is interrupted and you will be removed from the venue.  \nPlease, try to connect again.", "Lost Connection")

    def RemoveUserEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant exits
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The ClientProfile of the participant who just exited the venue
        """

        user = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "%s just left the venue" %user.name)

        wxCallAfter(self.frame.contentListPanel.RemoveParticipant, user)
        log.debug("  remove user: %s" %(user.name))

    def ModifyUserEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *user* The modified ClientProfile of the participant that just changed profile information
        """

        user = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "%s just changed profile information" %user.name)
        log.debug("EVENT - Modify participant: %s" %(user.name))
        wxCallAfter(self.frame.contentListPanel.ModifyParticipant, user)

    def AddDataEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        
        **Arguments:**
        
        *data* The DataDescription representing data that just got added to the venue
        """

        data = event.data

        "this is the data uri received", data.id
        
        if data.type == "None" or data.type == None:
            wxCallAfter(self.frame.statusbar.SetStatusText, "file '%s' just got added to venue" %data.name)
            
            # Just change venuestate for venue data.
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass

        log.debug("EVENT - Add data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.AddData, data)

    def UpdateDataEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *data* The DataDescription representing data that just got updated in the venue
        """
        data = event.data
        
        log.debug("EVENT - Update data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.UpdateData, data)

    def RemoveDataEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *data* The DataDescription representing data that just got removed from the venue
        """

        data = event.data
        # Handle venue data (personal data is in VenueClientUIClasses)
        if data.type == "None" or data.type == None:
            wxCallAfter(self.frame.statusbar.SetStatusText, "file '%s' just got added to venue" %data.name)
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass
        
        wxCallAfter(self.frame.statusbar.SetStatusText, "File '%s' just got removed from the venue" %data.name)
        log.debug("EVENT - Remove data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.RemoveData, data)

    def ModifyStreamEvent(self, event):
        """
        This method is called when a venue stream is modified.
        """
        transportList = self.venueClient.GetTransportList()
        if 'unicast' in transportList:
            self.frame.SetUnicastEnabled(1)
        else:
            self.frame.SetUnicastEnabled(0)


    def AddApplicationEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a new application is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *app* The ApplicationDescription representing the application that just got added to the venue
        """
        app = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "Application '%s' just got added to the venue" %app.name)
        log.debug("EVENT - Add application: %s, Mime Type: %s" %(app.name, app.mimeType))
        wxCallAfter(self.frame.contentListPanel.AddApplication, app)

    def RemoveApplicationEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time an application is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *app* The ApplicationDescription representing the application that just got removed from the venue
        """
        app = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "Application '%s' just got removed from the venue" %app.name)
        log.debug("EVENT - Remove application: %s" %(app.name))
        wxCallAfter(self.frame.contentListPanel.RemoveApplication, app)

    def AddServiceEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *service* The ServiceDescription representing the service that just got added to the venue
        """
        service = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "Service '%s' just got added to the venue" %service.name)
        log.debug("EVENT - Add service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.AddService, service)

    def RemoveServiceEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *service* The ServiceDescription representing the service that just got removed from the venue
        """
        service = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "Service '%s' just got removed from the venue" %service.name)
        log.debug("EVENT - Remove service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.RemoveService, service)

    def AddConnectionEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connection* The ConnectionDescription representing the exit that just got added to the venue
        """
        connection = event.data
        wxCallAfter(self.frame.statusbar.SetStatusText, "A new exit, '%s', just got added to the venue" %connection.name)  
        log.debug("EVENT - Add connection: %s" %(connection.name))
        wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def SetConnectionsEvent(self, event):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connections* A list of ConnectionDescriptions representing all the exits in the venue.
        """
        connections = event.data
        log.debug("EVENT - Set connections")
        wxCallAfter(self.frame.venueListPanel.CleanUp)

        for connection in connections:
            log.debug("EVENT - Add connection: %s" %(connection.name))
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def PreEnterVenue(self, URL, back = false):
        wxCallAfter(self.frame.statusbar.SetStatusText, "trying to enter venue at %s"%URL)
        #
        # Check to see if we have a valid grid proxy
        # If not, run grid proxy init
        #
        if not self.app.certificateManager.HaveValidProxy():
            log.debug("VenueClient::EnterVenue: You don't have a valid proxy")
            self.app.certificateManager.CreateProxy()

    def EnterVenue(self, URL, back = false, warningString="",
                   enterSuccess=AG_TRUE):
        """
        Note: Overridden from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
      
        **Arguments:**
        
        *URL* A string including the venue address we want to connect to
        *back* Boolean value, true if the back button was pressed, else false.
        
        """
        log.debug("bin.VenueClient::EnterVenue: Enter venue with url: %s"
                  % URL)

        if not enterSuccess:
            text = "You have not entered the venue located at %s.\nAn error occured.  Please, try again." % URL
            ErrorDialog(None, text, "Enter Venue Error",
                          style = wxOK  | wxICON_ERROR)
            return

        #
        # Check to see if we have a valid grid proxy
        # If not, run grid proxy init
        #
        if not self.app.certificateManager.HaveValidProxy():
            log.debug("VenueClient::EnterVenue: You don't have a valid proxy")
            self.app.certificateManager.CreateProxy()

        # initialize flag in case of failure
        enterUISuccess = AG_TRUE

        try:
            #   
            # Add current uri to the history if the go button is pressed
            #
            self.__setHistory(self.venueClient.venueUri, back)
            
            wxCallAfter(self.frame.statusbar.SetStatusText, "Entered venue %s successfully" %self.venueClient.venueState.name)

            # clean up ui from current venue before entering a new venue
            if self.venueClient.venueUri != None:
                log.debug("clean up frame")
                wxCallAfter(self.frame.CleanUp)

            # Get current state of the venue
            venueState = self.venueClient.venueState
            wxCallAfter(self.frame.venueAddressBar.SetTitle,
                            venueState.name, venueState.description) 

            # Load clients
            log.debug("Add participants")
            wxCallAfter(self.frame.statusbar.SetStatusText,
                            "Load participants")
            for client in venueState.clients.values():
                wxCallAfter(self.frame.contentListPanel.AddParticipant,
                            client)
                log.debug("   %s" %(client.name))

            # Load data
            log.debug("Add data")
            wxCallAfter(self.frame.statusbar.SetStatusText, "Load data")
            for data in venueState.data.values():
                wxCallAfter(self.frame.contentListPanel.AddData, data)
                log.debug("   %s" %(data.name))

            # Load services
            log.debug("Add service")
            wxCallAfter(self.frame.statusbar.SetStatusText,
                        "Load services")
            for service in venueState.services.values():
                wxCallAfter(self.frame.contentListPanel.AddService,
                            service)
                log.debug("   %s" %(service.name))

            # Load applications
            log.debug("Add application")
            wxCallAfter(self.frame.statusbar.SetStatusText,
                        "Load applications")
            for app in venueState.applications.values():
                wxCallAfter(self.frame.contentListPanel.AddApplication,
                            app)
                log.debug("   %s" %(app.name))

            #  Load exits
            log.debug("Add exits")
            wxCallAfter(self.frame.statusbar.SetStatusText, "Load exits")
            for exit in venueState.connections.values():
                wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor,
                            exit)
                log.debug("   %s" %(exit.name))

            #
            # Tell the text client which location it should listen to
            #
            log.debug("Set text location and address bar")
            self.venueClient.textClient.RegisterOutputCallback(self.frame.textClientPanel.OutputText)
#            wxCallAfter(self.frame.SetTextLocation)

            wxCallAfter(self.frame.FillInAddress, None, URL)
            
            # Venue data storage location
            # self.upload_url = self.venueClient.client.GetUploadDescriptor()
            #log.debug("Get upload url %s" %self.dataStoreUploadUrl)

            # Determine if we are an administrator so we can add administrator features to UI.
            if "Venue.Administrators" in self.venueClient.venueProxy.DetermineSubjectRoles():
                self.isVenueAdministrator = AG_TRUE
            else:
                self.isVenueAdministrator = AG_FALSE
            
            log.debug("Add your personal data descriptions to venue")
            wxCallAfter(self.frame.statusbar.SetStatusText, "Add your personal data to venue")
            warningString = warningString 

            # Enable menus
            wxCallAfter(self.frame.ShowMenu)
            
            #
            # Enable the application menu that is displayed over
            # the Applications items in the list
            # (this is not the app menu above)
            wxCallAfter(self.frame.EnableAppMenu, true)

            # Enable/disable the unicast menu entry appropriately
            enableUnicastToggle = 0
            if len(self.venueClient.streamDescList):
                if self.venueClient.streamDescList[0].__dict__.has_key("networkLocations"):
                    netlocs = self.venueClient.streamDescList[0].networkLocations
                    for netloc in netlocs:
                        if netloc.type == "unicast":
                            enableUnicastToggle = 1
            self.frame.SetUnicastEnabled(enableUnicastToggle)
            
            # Call EnterVenue on users that are following you.
            # This should be done last for UI update reasons.
            log.debug("Lead followers")
            self.venueClient.LeadFollowers()
            
            log.debug("Entered venue")
            
            #
            # Display all non fatal warnings to the user
            #
            if warningString != '': 
                message = "Following non fatal problems have occured when you entered the venue:\n" + warningString
                MessageDialog(None, message, "Notification")
                
                wxCallAfter(self.frame.statusbar.SetStatusText, "Entered %s successfully" %self.venueClient.venueState.name)
       
        except Exception, e:
            log.exception("bin.VenueClient::EnterVenue failed")
            enterUISuccess = AG_FALSE

        if not enterUISuccess:
            text = "You have not entered the venue located at %s.\nAn error occured.  Please, try again."%URL
            ErrorDialog(None, text, "Enter Venue Error",
                          style = wxOK  | wxICON_ERROR)
             
#     def ExitVenue(self):
#         """
#         Note: Overridden from VenueClient
#         This method calls the venue client method and then
#         performs its own operations when the client exits a venue.
#         """
#         log.debug("exit venue")

#         #
#         # Shut down the text client
#         #

#         wxCallAfter(self.frame.CloseTextConnection)

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
            self.venueClient.EnterVenue(uri, true)

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """

        # Ensure things are not shut down twice.
        if not self.onExitCalled:
            self.onExitCalled = true
            log.info("--------- END VenueClient")

            #
            # If we are connected to a venue, exit the venue
            # Do this before terminating services, since we need
            # to message them to shut down their services first
            #
            if self.venueClient.isInVenue:
                self.venueClient.ExitVenue()

            #
            # If we're running as a personal node, terminate the services.
            #
            if self.isPersonalNode:
                log.debug("Terminating services")
                self.personalNode.Stop()

            self.venueClient.Shutdown()      

            self.ExitMainLoop()

            #os._exit(0)  # this should not be necessary, replace if needed.

        else:
            log.info("note that bin.VenueClient.OnExit() was called twice.")

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
            wxCallAfter(ErrorDialog, None, "The file could not be downloaded", "Download Error",  wxOK | wxICON_ERROR)
            
    def UploadPersonalFiles(self, fileList):
        """
        Upload the given personal files to the venue.

        """
        log.debug("Upload personal files")
        try:
            my_identity = GetDefaultIdentityDN()
            self.venueClient.dataStore.UploadLocalFiles(fileList, my_identity, self.venueClient.profile.publicId)

        except DataStore.DuplicateFile, e:
            title = "Add Personal Data Error"
            ErrorDialog(self.frame, e, title, style = wxOK|wxICON_ERROR)

        except Exception, e:
            log.exception("bin.VenueClient:UploadPersonalFiles failed")
            title = "Add Personal Data Error"
            text = "The file could not be added, error occured."
            ErrorDialog(self.frame, text, title,  wxOK | wxICON_ERROR)
                               
    def UploadVenueFiles(self, file_list):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.
        
        """
        url = self.venueClient.dataStoreUploadUrl
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

        upload_thread.start()
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
            wxCallAfter(ErrorDialog,
                        None, error_msg,
                        "Upload Files Error", wxOK | wxICON_ERROR)
               
    def UploadFilesNoDialog(self, file_list):
        """
        Upload the given files to the venue.

        This uses the DataStore HTTP upload engine code.
        """

        log.debug("Upload files - no dialog. upload_url=%s", self.venueClient.dataStoreUploadUrl)
        upload_url = self.venueClient.dataStoreUploadUrl

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
            ErrorDialog(None, error_msg, "Upload Files Error", style = wxOK|wxICON_ERROR)
           
    def RemoveData(self, data, ownerProfile):
        """
        This method removes a data from the venue. If the data is personal, this method
        also removes the data from the personal data storage.

        **Arguments:**
        
        *data* The DataDescription we want to remove from vnue
        """
        log.debug("Remove data: %s from venue" %data.name)

        
        try:
            self.venueClient.RemoveData(data, ownerProfile)
        except:
            log.exception("bin.VenueClient::RemoveData: Error occured when trying to remove data")
            ErrorDialog(None, "The file could not be removed", "Remove Personal Files Error", style = wxOK | wxICON_ERROR)
          
    def AddService(self, service):
        """
        This method adds a service to the venue

        **Arguments:**
        
        *service* The ServiceDescription we want to add to the venue
        """
        log.debug("Adding service: %s to venue" %service.name)
        try:
            self.venueClient.client.AddService(service)

        except:
            log.exception("bin.VenueClient::AddService: Error occured when trying to add service")
            ErrorDialog(None, "The service could not be added", "Add Service Error", style = wxOK | wxICON_ERROR)
          
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
                ErrorDialog(None, "The service could not be opened", "Open Service Error", style = wxOK | wxICON_ERROR)
                
    def RemoveService(self, service):
        """
        This method removes a service from the venue

        **Arguments:**
        
        *service* The ServiceDescription representing the service we want to remove from the venue
        """
        log.debug("Remove service: %s from venue" %service.name)
        try:
            self.venueClient.client.RemoveService(service)

        except:
            log.exception("bin.VenueClient::RemoveService: Error occured when trying to remove service")
            ErrorDialog(None, "The service could not be removed", "Remove Service Error", style = wxOK | wxICON_ERROR)
            
    def ChangeProfile(self, profile):
        """
        This method changes this participants profile and saves the information to file.

        **Arguments:**
        
        *profile* The ClientProfile including the new profile information
        """
        self.venueClient.profile = profile
        self.venueClient.profile.Save(self.profileFile)
        log.debug("Save profile")

        # use profile from path
        self.venueClient.profile = ClientProfile(self.profileFile)
        self.venueClient.SetProfile(self.venueClient.profile)

        if(self.venueClient.venueUri != None):
            log.debug("Update client profile in venue")

            try:
                self.venueClient.client.UpdateClientProfile(profile)

            except:
                log.exception("bin.VenueClient::ChangeProfile: Error occured when trying to update profile")
                ErrorDialog(None, "Your profile could not be changed", "Change Profile Error", style = wxOK | wxICON_ERROR)
        else:
            log.debug("Can not update client profile in venue - not connected")

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
        appDesc = self.venueClient.client.CreateApplication( app.name, app.description,
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
        self.venueClient.client.DestroyApplication( app.id )
        log.debug("Destroying application: %s" % app.name)

    def RemoveStreamEvent(self):
        pass

    def SetTransport(self, transport):
        self.venueClient.SetTransport(transport)

    def GetTransport(self):
        return self.venueClient.GetTransport()

    def SetProvider(self, provider):
        self.venueClient.SetProvider(provider)

    def UpdateNodeService(self):
        self.venueClient.UpdateNodeService()

    def SetVideoEnabled(self, enableFlag):
        if self.venueClient.nodeServiceUri:
            Client.Handle(self.venueClient.nodeServiceUri).GetProxy().SetServiceEnabledByMediaType("video",enableFlag)

    def SetAudioEnabled(self, enableFlag):
        if self.venueClient.nodeServiceUri:
            Client.Handle(self.venueClient.nodeServiceUri).GetProxy().SetServiceEnabledByMediaType("audio",enableFlag)



if __name__ == "__main__":

    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    app = wxPySimpleApp()
    max = 10
    
    dlg = ProgressDialog("Startup", "Loading Venue Client. Please be patient.", max)
    dlg.Show()
    
    vc = VenueClientUI(dlg)
    vc.ConnectToVenue()
    
