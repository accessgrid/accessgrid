#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.137 2003-04-29 15:37:11 lefvert Exp $
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
from AccessGrid.UIUtilities import MyLog, MessageDialog, InitMimeTypes
from AccessGrid.UIUtilities import GetMimeCommands
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN
from AccessGrid.GUID import GUID
from AccessGrid.hosting.pyGlobus import Server
from AccessGrid.VenueClient import VenueClient
from AccessGrid.Platform import GPI, GetUserConfigDir
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog

from AccessGrid import PersonalNode
    
try:
    from AccessGrid import CertificateManager
    CertificateManager.CertificateManagerWXGUI
    HaveCertificateManager = 1
except Exception, e:
    HaveCertificateManager = 0

class VenueClientUI(wxApp, VenueClient):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event.
    """
    history = []
    client = None
    #gotClient = false
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

    def __init__(self):
        if not os.path.exists(self.accessGridPath):
            try:
                os.mkdir(self.accessGridPath)
            except OSError, e:
                wxLogError("Could not create base path")

        wxApp.__init__(self, false)
        VenueClient.__init__(self)

    def OnInit(self):
        """
        This method initiates all gui related classes.
        """
        self.__processArgs()
        self.__setLogger()
        VerifyExecutionEnvironment()
        self.__createPersonalDataStore()

        if HaveCertificateManager:
            self.certificateManagerGUI = CertificateManager.CertificateManagerWXGUI()
            self.certificateManager = CertificateManager.CertificateManager(GetUserConfigDir(),
            self.certificateManagerGUI)
            self.certificateManager.InitEnvironment()

        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(500, 400))
        self.SetTopWindow(self.frame)

        # Tell the UI about installed applications
        self.frame.SetInstalledApps( self.GetInstalledApps() )
        self.frame.EnableAppMenu( false )

        # Load user mailcap from AG Config Dir
        mailcap = os.path.join(GetUserConfigDir(), "mailcap")
        InitMimeTypes(mailcap)

        log.debug("OnInit: ispersonal=%s", self.isPersonalNode)

        if self.isPersonalNode:
            def setSvcCallback(svcUrl, self = self):
                log.debug("setting node service URI to %s from PersonalNode", svcUrl)
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
            self.ChangeProfile(self.profile)
            profileDialog.Destroy()
            self.__startMainLoop(self.profile)

        else:
            profileDialog.Destroy()
            os._exit(0)

    def __startMainLoop(self, profile):
        """
        This method is called during client startup.  It sets the
        participant profile, enters the venue, and finally starts the
        wxPython main gui loop.
        """
        self.SetProfile(profile)
        self.frame.venueAddressBar.SetAddress(self.profile.homeVenue)
        self.frame.Show(true)
        wxLogDebug("start wxApp main loop/thread")
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
        Creates the personal data storage and loads saved personal data.
        """
        wxLogDebug('------------------- %s' %self.personalDataStorePath)
        if not os.path.exists(self.personalDataStorePath):
            try:
                os.mkdir(self.personalDataStorePath)
            except OSError, e:
                wxLogError("Could not create personal data storage path")
                self.personalDataStorePath = None

        self.dataStore = DataStore.DataStore(self, self.personalDataStorePath,
        self.personalDataStorePrefix)
        self.transferEngine = DataStore.GSIHTTPTransferServer(('',
                                                               self.personalDataStorePort))
        self.transferEngine.run()
        self.transferEngine.RegisterPrefix(self.personalDataStorePrefix, self)
        self.dataStore.SetTransferEngine(self.transferEngine)

        wxLogDebug("Creating personal datastore at %s using prefix %s and port %s" %(self.personalDataStorePath,
        self.personalDataStorePrefix, self.personalDataStorePort))
        # load personal data
        if os.path.exists(self.personalDataFile):
            file = open(self.personalDataFile, 'r')
            self.personalDataDict = cPickle.load(file)
            wxLogDebug("This is my personal data %s" %str(self.personalDataDict))
            file.close()

            wxLogDebug("check for validity")
            for file, desc in self.personalDataDict.items():
                wxLogDebug("Checking file %s for validity"%file)
                url = self.transferEngine.GetDownloadDescriptor(self.personalDataStorePrefix, file)
                wxLogDebug("File url is %s"%url)

                if url is None:
                    del self.personalDataDict[file]

    def __setLogger(self):
        """
        Sets the logging mechanism.
        """
        log = logging.getLogger("AG")
        log.setLevel(logging.DEBUG)
        logname = "VenueClient.log"
        hdlr = logging.FileHandler(logname)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

        if self.debugMode:
            log.addHandler(logging.StreamHandler())

        wxLog_SetActiveTarget(wxLogGui())
        wxLog_SetActiveTarget(wxLogChain(MyLog(log)))
        wxLogInfo(" ")
        wxLogInfo("--------- START VenueClient")

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
            wxLogDebug("the profile is the default profile - open profile dialog")
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
        """
        wxCallAfter(self.frame.AuthorizeLeadDialog, clientProfile)


    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        Note: Overridden from VenueClient
        This method notifies the user if the request to follow somebody is approved
        or denied.
        """
        VenueClient.LeadResponse(self, leaderProfile, isAuthorized)
        wxCallAfter(self.frame.NotifyLeadDialog, leaderProfile, isAuthorized)

    LeadResponse.soap_export_as = "LeadResponse"


    def NotifyUnLead(self, clientProfile):
        """
        Note: Overridden from VenueClient
        This method  notifies the user that somebody wants to stop following him or
        her
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

        if(profile.profileType == 'user'):
            wxCallAfter(self.frame.contentListPanel.AddParticipant, profile)
            wxCallAfter(wxLogDebug, "  add user: %s" %(profile.name))

        else:
            wxCallAfter(self.frame.contentListPanel.AddNode, profile)
            wxCallAfter(wxLogDebug, "  add node: %s" %(profile.name))

    def RemoveUserEvent(self, user):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant exits
        the venue.  Appropriate gui updates are made in client.
        """
        VenueClient.RemoveUserEvent(self, user)

        if(user.profileType == 'user'):
            wxCallAfter(self.frame.contentListPanel.RemoveParticipant, user)
            wxCallAfter(wxLogDebug,"  remove user: %s" %(user.name))
        else:
            wxCallAfter(self.frame.contentListPanel.RemoveNode, user)
            wxCallAfter(wxLogDebug,"  remove node: %s" %(user.name))


    def ModifyUserEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.
        """
        
        VenueClient.ModifyUserEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Modify participant: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.ModifyParticipant, data)

    def AddDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        """
        VenueClient.AddDataEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Add data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.AddData, data)


    def UpdateDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.
        """

        VenueClient.UpdateDataEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Update data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.UpdateData, data)

    def RemoveDataEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.
        """
        VenueClient.RemoveDataEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Remove data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.RemoveData, data)

    def AddApplicationEvent(self, app):
        """
        Note: Overridden from VenueClient
        This method is called every time a new application is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Add application: %s" %(app.name))
        wxCallAfter(wxLogDebug, "EVENT - Add application: %s" %(app.mimeType))
        wxCallAfter(self.frame.contentListPanel.AddApplication, app)

    def RemoveApplicationEvent(self, app):
        """
        Note: Overridden from VenueClient
        This method is called every time an application is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Remove application: %s" %(app.name))
        wxCallAfter(self.frame.contentListPanel.RemoveApplication, app)


    def AddServiceEvent(self, service):
        """
        Note: Overridden from VenueClient
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.
        """

        # Convert the struct type to a ServiceDescription so we can use isinstance...
        s = ServiceDescription(service.name, service.description, service.uri,
                               service.mimeType)
        
        VenueClient.AddServiceEvent(self, s)
        wxCallAfter(wxLogDebug, "EVENT - Add service: %s" %(s.name))
        wxCallAfter(self.frame.contentListPanel.AddService, s)

    def RemoveServiceEvent(self, service):
        """
        Note: Overridden from VenueClient
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.
        """
        VenueClient.RemoveServiceEvent(self, service)
        wxCallAfter(wxLogDebug, "EVENT - Remove service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.RemoveService, service)


    def AddConnectionEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
                
        VenueClient.AddConnectionEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Add connection: %s" %(data.name))
        wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, data)

    def SetConnectionsEvent(self, data):
        """
        Note: Overridden from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
        VenueClient.SetConnectionsEvent(self, data)
        wxCallAfter(wxLogDebug, "EVENT - Set connections")
        wxCallAfter(self.frame.venueListPanel.CleanUp)

        for connection in data:
            wxCallAfter(wxLogDebug, "EVENT - Add connection: %s" %(connection.name))
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def EnterVenue(self, URL):
        """
        Note: Overridden from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        wxCallAfter(wxLogDebug, "EVENT- Enter venue with url: %s" %(URL))

        # clean up ui from current venue
        if self.venueUri != None:
            wxCallAfter(wxLogDebug, "clean up frame and exit")
            wxCallAfter(self.frame.CleanUp)

        self.clientHandle = Client.Handle(URL)

        # if this venue url has a valid web service then enter venue
        if(self.clientHandle.IsValid()):
            self.client = self.clientHandle.get_proxy()

            # Tell super class to enter venue
            VenueClient.EnterVenue( self, URL )

            venueState = self.venueState
            wxCallAfter(self.frame.SetLabel, venueState.name)

            # --- Load clients
            clients = venueState.clients.values()
            wxCallAfter(wxLogDebug, "Add participants")

            for client in clients:
                # Participants
                if(client.profileType == 'user'):
                    wxCallAfter(self.frame.contentListPanel.AddParticipant, client)
                    wxCallAfter(wxLogDebug, "   %s" %(client.name))

                    # Nodes
                else:
                    wxCallAfter(self.frame.contentListPanel.AddNode, client)
                    wxCallAfter(wxLogDebug, "   %s" %(client.name))

            # --- Load data
            data = venueState.data.values()
            wxCallAfter(wxLogDebug, "Add data")
            for d in data:
                wxCallAfter(self.frame.contentListPanel.AddData, d)
                wxCallAfter(wxLogDebug, "   %s" %(d.name))
                wxCallAfter(wxLogDebug, "   ------------- data type %s" %(d.type))
                wxCallAfter(wxLogDebug, "   ------------- my public id %s" %(self.profile.publicId))

            # --- Load services
            services = venueState.services.values()
            wxCallAfter(wxLogDebug, "Add service")
            for s in services:
                wxCallAfter(self.frame.contentListPanel.AddService, s)
                wxCallAfter(wxLogDebug, "   %s" %(s.name))

            # --- Load applications
            applications = venueState.applications.values()
            wxCallAfter(wxLogDebug, "Add application")
            for a in applications:
                wxCallAfter(self.frame.contentListPanel.AddApplication, a)
                wxCallAfter(wxLogDebug, "   %s" %(a.name))

            # Enable the application menu that is displayed over
            # the Applications items in the list (this is not the app menu above)
            self.frame.EnableAppMenu(true)

            # --- Load exits
            wxCallAfter(wxLogDebug, "Add exits")
            exits = venueState.connections.values()
            for exit in exits:
                wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, exit)
                wxCallAfter(wxLogDebug, "   %s" %(exit.name))

            # Start text location
            wxCallAfter(wxLogDebug, "Set text location and address bar")
            wxCallAfter(self.frame.SetTextLocation)
            wxCallAfter(self.frame.FillInAddress, None, URL)
            self.venueUri = URL

            # Venue data storage location
            self.upload_url = self.client.GetUploadDescriptor()
            wxCallAfter(wxLogDebug, "Get upload url %s" %self.upload_url)

            # Add your personal data descriptions to venue
            wxCallAfter(wxLogDebug, "Add your personal data descriptions to venue")
            self.__AddPersonalDataToVenue()

            # This should be done last for UI update reasons
            wxCallAfter(wxLogDebug, "Lead followers")
            self.LeadFollowers()

            wxCallAfter(wxLogDebug, "Entered venue")

    EnterVenue.soap_export_as = "EnterVenue"

    def __AddPersonalDataToVenue(self):
        '''
        Adds all personal data, stored in local file directory as a dictionary, to the venue.
        '''

        # Add personal data to venue
        duplicateData = []
        for data in self.personalDataDict.values():
            wxLogDebug("Add personal file %s to venue" %data.name)

            url = self.dataStore.GetDownloadDescriptor(data.name)

            # Is the file still present?
            if url is None:
                wxLogDebug("Personal file %s has vanished" %data.name)
                del self.personalDataDict[data.name]

                # Is there a file in the venue with the same name?
            elif(self.venueState.data.has_key(data.name)):
                duplicateData.append(data.name)

            else:
                try:
                    self.client.AddData(data)
                except Exception, e:
                    wxCallAfter(wxLogError, "Personal data, %s,  could not be added to the venue" %data.name)
                    wxCallAfter(wxLog_GetActiveTarget().Flush)

        # Notify user of what files already exist in the venue
        if(len(duplicateData) >0):
            files = ''
            for file in duplicateData:
                files = files + ' ' +file + ','

            wxCallAfter(wxLogMessage, "Personal data, %s \nalready exists in the venue and could not be added"
            %files)
            wxCallAfter(wxLog_GetActiveTarget().Flush)

    def ExitVenue(self):
        """
        Note: Overridden from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        wxCallAfter(wxLogDebug, "Cleanup frame, save data, and exit venue")
        VenueClient.ExitVenue(self)

    def __setHistory(self, uri, back):
        """
        This method sets the history list, which stores visited
        venue urls used by the back button.
        """
        wxCallAfter(wxLogDebug, "Set history url: %s " %uri)
        length = len(self.history)
        last = length -1

        if(length>0):
            if not back:           # clicked go button
                if(self.history[last] != uri):
                    self.history.append(uri)
            else:
                del self.history[last] # clicked back button

        elif(uri is not None):
            self.history.append(uri)

    def GoBack(self):
        """
        GoBack() is called when the user wants to go back to last visited venue
        """
        wxCallAfter(wxLogDebug,"Go back")

        l = len(self.history)
        if(l>0):
            uri = self.history[l - 1]
            self.GoToNewVenue(uri, true)

    def GoToNewVenue(self, uri, back = false):
        """
        GoToNewVenue(url, back) transports the user to a new venue
        with same url as the input parameter.  If the url is a server
        address, we will instead enter the default venue on the
        server.  If the url is invalid, the user re-enters the venue
        he or she just left.
        """
        wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: Go to new venue %s" %uri)
        self.oldUri = None

        if not HaveValidProxy():
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: You don't have a valid proxy")
            GPI()

        if self.venueUri != None:
            self.oldUri = self.venueUri

        try: # is this a server
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: Is this a server")
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: server url: %s" %venueUri)

        except: # no, it is a venue
            venueUri = uri
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: venue url: %s" %venueUri)

        self.clientHandle = Client.Handle(venueUri)
        if(self.clientHandle.IsValid()):
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: the handler is valid")

            #try:
            self.client = self.clientHandle.get_proxy()
            #self.gotClient = true
            self.EnterVenue(venueUri)
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: after enter venue %s" %venueUri)
            self.__setHistory(self.oldUri, back)
            wxCallAfter(self.frame.ShowMenu)

            #except:
            #    wxCallAfter(wxLogError, "Error while trying to enter venue")
            #    wxCallAfter(wxLog_GetActiveTarget().Flush)
            #if self.oldUri != None:
            #    wxCallAfter(wxLogDebug,"Go back to old venue")
            # go back to venue where we came from
            #    self.EnterVenue(self.oldUri)
        else:
            wxCallAfter(wxLogDebug, "VenueClient::GoToNewVenue: Handler is not valid")
            if not HaveValidProxy():
                text = 'You do not have a valid proxy.' +\
                       '\nPlease, run "grid-proxy-init" on the command line"'
                text2 = 'Invalid proxy'

            else:
                #if self.oldUri is None:
                #    wxCallAfter(self.frame.FillInAddress, None, self.profile.homeVenue)
                #else:
                #wxCallAfter(self.frame.FillInAddress, None, venueUri)

                text = 'The venue URL you specified is not valid'
                text2 = 'Invalid URL'

            wxCallAfter(wxLogMessage, text)
            wxCallAfter(wxLog_GetActiveTarget().Flush)

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        wxLogInfo("--------- END VenueClient")

        #
        # If we're running as a personal node, terminate the services.
        #

        if self.isPersonalNode:
            log.debug("Terminating services")
            self.personalNode.Stop()

        if self.venueUri != None:
            self.ExitVenue()

        # save personal data
        file = open(self.personalDataFile, 'w')
        cPickle.dump(self.personalDataDict, file)
        file.close()

        # stop personal data server
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
        wxCallAfter(wxLogDebug, "Save file descriptor: %s, path: %s"%(data_descriptor, local_pathname))

        failure_reason = None
        try:

            # Retrieve details from the descriptor
            size = data_descriptor.size
            checksum = data_descriptor.checksum
            url = data_descriptor.uri

            # Make sure this data item is valid
            wxCallAfter(wxLogDebug, "data descriptor is %s" %data_descriptor.__class__)

            if data_descriptor.status != DataDescription.STATUS_PRESENT:
                wxCallAfter(wxLogMessage, "File %s is not downloadable - it has status %s"
                % (data_descriptor.name, data_descriptor.status))
                wxCallAfter(wxLog_GetActiveTarget().Flush)

                return

            # Create the dialog for the download.
            dlg = SaveFileDialog(self.frame, -1, "Saving file",
            "Saving file to %s ...     " % (local_pathname),
            "Saving file to %s ... done" % (local_pathname),
            size)

            wxCallAfter(wxLogDebug, "Downloading: size=%s checksum=%s url=%s" % (size, checksum, url))
            dlg.Show(1)

            # Plumbing for getting progress callbacks to the dialog
            def progressCB(progress, done, dialog = dlg):
                wxCallAfter(dialog.SetProgress, progress, done)
                return dialog.IsCancelled()

            # Create the thread to run the download.
            #
            # Some more plumbing with the locla function to get the identity
            # retrieval in the thread, as it can take a bit the first time.
            #
            # We use get_ident_and_download as the body of the thread.

            # Arguments to pass to get_ident_and_download
            dl_args = (url, local_pathname, size, checksum, progressCB)

            download_thread = threading.Thread(target = self.get_ident_and_download,
            args = dl_args)

            # Use wxCallAfter so we get the dialog filled in properly.
            wxCallAfter(download_thread.start)

            # Fire up dialog as a modal.
            dlg.ShowModal()


            # The dialog has returned. This is either because the download
            # finished and the user clicked OK, or because the user clicked
            # Cancel to abort the download. In either event the
            # call to HTTPDownloadFile should return, and the thread quit.
            #
            # Wait for the thread to finish (if it doesn't it's a bug).
            download_thread.join()
            # Clean up.
            dlg.Destroy()

        except DataStore.DownloadFailed, e:
            failure_reason = "Download error: %s" % (e[0])
        except EnvironmentError, e:
            failure_reason = "Exception: %s" % (str(e))
        except:
            failure_reason = "Unknown"

        if failure_reason is not None:
            wxCallAfter(MessageDialog, self.frame, failure_reason, "Download error",
            wxOK  | wxICON_INFORMATION)


    def get_ident_and_download(self, url, local_pathname, size, checksum, progressCB):
        wxLogDebug("Get ident and download")
        try:
            if url.startswith("https"):
                wxLogDebug("url=%s, local path =%s, size = %s, checksum = %s"%(url, local_pathname, size, checksum))
                DataStore.GSIHTTPDownloadFile(url, local_pathname, size,
                checksum, progressCB)
                wxLogDebug("finished GSIHTTPDownload")

            else:
                wxLogDebug("url does not start with https")
                my_identity = GetDefaultIdentityDN()
                DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                checksum, progressCB)
        except DataStore.DownloadFailed, e:
            wxCallAfter(wxLogError, "Got exception on download")

    def UploadPersonalFiles(self, fileList):
        """
        Upload the given personal files to the venue.

        """
        wxLogDebug("Upload personal files")
        try:
            self.dataStore.AddFile(fileList, self.profile.distinguishedName, self.profile.publicId)

        except Exception, e:
            wxLogMessage(e[0])
            wxLog_GetActiveTarget().Flush()


    def UploadVenueFiles(self, file_list):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.

        """
        url = self.upload_url
        method = self.get_ident_and_upload

        # Create the dialog for the download.
        dlg = UploadFilesDialog(self.frame, -1, "Uploading files")

        dlg.Show(1)

        # Plumbing for getting progress callbacks to the dialog
        def progressCB(filename, sent, total, file_done, xfer_done,
            dialog = dlg):
            wxCallAfter(dialog.SetProgress, filename, sent, total,
            file_done, xfer_done)
            return dialog.IsCancelled()

        # Create the thread to run the upload.
        #
        # Some more plumbing with the local function to get the identity
        # retrieval in the thread, as it can take a bit the first time.
        # We use get_ident_and_upload as the body of the thread.

        # Arguments to pass to get_ident_and_upload
        ul_args = (url, file_list, progressCB)

        wxCallAfter(wxLogDebug,
        "Have args, creating thread, url: %s, files: %s" %
        (url, file_list))

        upload_thread = threading.Thread(target = method, args = ul_args)

        wxCallAfter(upload_thread.start)
        wxCallAfter(wxLogDebug, "Started thread")
        dlg.ShowModal()

        # The dialog has returned. This is either because the upload
        # finished and the user clicked OK, or because the user clicked
        # Cancel to abort the upload. In either event the
        # call to HTTPUploadFiles should return, and the thread quit.
        #
        # Wait for the thread to finish (if it doesn't it's a bug).
        upload_thread.join()
        dlg.Destroy()

    def get_ident_and_upload(self, upload_url, file_list, progressCB):
        wxCallAfter(wxLogDebug, "Upload: getting identity")

        error_msg = None
        try:
            if upload_url.startswith("https:"):
                wxCallAfter(wxLogDebug, "Url starts with https:")
                DataStore.GSIHTTPUploadFiles(upload_url, file_list, progressCB)
            else:
                my_identity = GetDefaultIdentityDN()
                wxCallAfter(wxLogDebug, "Got identity %s" % my_identity)
                DataStore.HTTPUploadFiles(my_identity, upload_url,
                file_list, progressCB)

        except DataStore.FileNotFound, e:
            error_msg = "File not found: %s" % (e[0])
        except DataStore.NotAPlainFile, e:
            error_msg = "Not a plain file: %s" % (e[0])
        except DataStore.UploadFailed, e:
            error_msg = "Upload failed: %s" % (e)

        if error_msg is not None:
            wxCallAfter(wxLogMessage, error_msg)
            wxCallAfter(wxLog_GetActiveTarget().Flush)
    # wxCallAfter(MessageDialog, NULL, error_msg)

    def UploadFilesNoDialog(self, file_list):
        """
        Upload the given files to the venue.

        This uses the DataStore HTTP upload engine code.
        """

        wxCallAfter(wxLogDebug, "Upload files - no dialog")
        upload_url = self.upload_url
        wxCallAfter(wxLogDebug, "Have identity=%s upload_url=%s" %
        (my_identity, upload_url))

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

        if error_msg is not None:
            wxCallAfter(wxLogMessage, error_msg)
            wxCallAfter(wxLog_GetActiveTarget().Flush)

    def AddData(self, data):
        """
        This method adds local data to the venue
        """
        wxLogDebug("Adding data: %s to venue" %data.name)
        wxLogDebug("Adding data: %s to venue" %data.type)
        try:
            self.client.AddData(data)
            self.personalDataDict[data.name] = data

        except Exception, e:
            wxLogError("Error occured when trying to add data %s" %e[0])
            wxLog_GetActiveTarget().Flush()

    def RemoveData(self, data):
        """
        This method removes a data from the venue
        """
        wxLogDebug("Remove data: %s from venue" %data.name)
        try:
            self.client.RemoveData(data)
            if(data.type == self.profile.publicId and self.personalDataDict.has_key(data.name)):
                del self.personalDataDict[data.name]
                self.dataStore.DeleteFile(data.name)

        except:
            wxLogError("Error occured when trying to remove data")
            wxLog_GetActiveTarget().Flush()

    def AddService(self, service):
        """
        This method adds a service to the venue
        """
        wxLogDebug("Adding service: %s to venue" %service.name)
        try:
            self.client.AddService(service)

        except:
            wxLogError("Error occured when trying to add service")
            wxLog_GetActiveTarget().Flush()

    def OpenService(self, service):
        """
        open the specified service
        """
        wxLogDebug("Opening service: %s / %s" % (service.name,
                                                 service.mimeType))
        commands = GetMimeCommands(filename=service.uri, type=service.mimeType)

        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % service.mimeType
            dlg = MessageDialog(self.frame, message )
            wxLogDebug(message)
        else:
            if commands.has_key('open'):
                wxLogDebug("executing cmd: %s" % commands['open'])
                if commands['open'][0:6] == "WX_DDE":
                    pid = wxExecute(commands['open'])
                else:
                    pid = wxShell(commands['open'])
                
    def RemoveService(self, service):
        """
        This method removes a service from the venue
        """
        wxLogDebug("Remove service: %s from venue" %service.name)
        try:
            self.client.RemoveService(service)

        except:
            wxLogError("Error occured when trying to remove service")
            wxLog_GetActiveTarget().Flush()


    def ChangeProfile(self, profile):
        """
        This method changes this participants profile
        """
        self.profile = profile
        self.profile.Save(self.profileFile)
        wxLogDebug("Save profile")

        # use profile from path
        self.profile = ClientProfile(self.profileFile)
        self.SetProfile(self.profile)

        if(self.venueUri != None):
            wxLogDebug("Update client profile in venue")

            try:
                self.client.UpdateClientProfile(profile)

            except:
                wxLogError("Error occured when trying to update profile")
                wxLog_GetActiveTarget().Flush()

        else:
            wxLogDebug("Can not update client profile in venue - not connected")

    def SetNodeUrl(self, url):
        """
        This method sets the node service url
        """
        wxLogDebug("Set node service url:  %s" %url)
        self.nodeServiceUri = url

    #
    # Methods for personal data storage to call
    #
    def GetData(self, filename):
        '''
        This method is called by the personal DataStore to get a
        DataDescription from the VenueClient.  If the file is not present
        GetData returns None
        '''
        wxLogDebug("Get private data description: %s" %filename)
        if self.personalDataDict.has_key(filename):
            d = self.personalDataDict[filename]

        else:
            wxLogDebug("The private file does not exist")
            d = None
        return d

    def GetVenueData(self, filename):
        '''
        This method is called by the personal DataStore to get a
        DataDescription present in the venue.  If the file is not present
        GetData returns None
        '''
        wxLogDebug("Get venue data description: %s" %filename)
        wxLogDebug("Venue state: %s" %str(self.venueState.data))
        if self.venueState.data.has_key(filename):
            d = self.venueState.data[filename]
        else:
            wxLogDebug("The venue file does not exist")
            d = None
        return d

    def UpdateData(self, desc):
        '''
        This method is called by the personal DataStore to update a
        DataDescription.
        '''
        self.personalDataDict[desc.GetName()] = desc
        self.client.UpdateData(desc)
        wxLogDebug("UpdateData: %s" %desc)

    #
    # Application Integration code
    #
    def StartApp(self,app):
        """
        Start the specified application.  This method creates the application
        in the venue, and then joins it by starting the appropriate client
        """
        wxLogDebug("Creating application: %s" % app.name)
        app.uri = self.client.CreateApplication( app.name, app.description, app.mimeType )
        self.JoinApp(app)

    def JoinApp(self,app):
        """
        Join the specified application
        """
        wxLogDebug("Joining application: %s / %s" % (app.name, app.mimeType))
        commands = GetMimeCommands(filename=app.uri, type=app.mimeType)

        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % app.mimeType
            dlg = MessageDialog(self.frame, message )
            wxLogDebug(message)
        else:
            if commands.has_key('open'):
                wxLogDebug("executing cmd: %s" % commands['open'])
                if commands['open'][0:6] == "WX_DDE":
                    pid = wxExecute(commands['open'])
                else:
                    StartDetachedProcess(commands['open'])

    def RemoveApp(self,app):
        """
        Delete the specified application from the venue
        """
        self.client.DestroyApplication( app.id )
        wxLogDebug("Destroying application: %s" % app.name)

if __name__ == "__main__":

    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()
