#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.110 2003-04-09 19:46:34 olson Exp $
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

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid.Platform import GPI, GetUserConfigDir
from AccessGrid.VenueClient import VenueClient
from AccessGrid.DataStore import DataStore, GSIHTTPTransferServer
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.VenueClientUIClasses import VerifyExecutionEnvironment
from AccessGrid.Descriptions import DataDescription
from AccessGrid.Utilities import HaveValidProxy
from AccessGrid.UIUtilities import MyLog 
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN 
from AccessGrid import DataStore
from AccessGrid.GUID import GUID

if sys.platform == "win32":
    from AccessGrid import PersonalNode

try:
    from AccessGrid import CertificateManager
    CertificateManager.CertificateManagerWXGUI
    HaveCertificateManager = 1
except Exception, e:
    HaveCertificateManager = 0

    

from AccessGrid.hosting.pyGlobus import Server
    
class VenueClientUI(wxApp, VenueClient):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event. 
    """
    history = []
    client = None
    gotClient = false
    clientHandle = None
    venueUri = None
    personalDataStorePrefix = "personalDataStore"
    personalDataStorePort = 9999
    #personalDataStorePath = GetUserConfigDir()
    personalDataDict = {}
    #personalDataFile = os.path.join(personalDataStorePath, "myData.txt" )

    def __init__(self):

        self.isPersonalNode = 0
        self.debugMode = 0

        wxApp.__init__(self, false)
        VenueClient.__init__(self)


    def OnInit(self):
        """
        This method initiates all gui related classes.
        """

        self.__processArgs()
        
        self.__setLogger()

        VerifyExecutionEnvironment()

        self.__createHomePath()
        self.__createPersonalDataStore()

        if HaveCertificateManager:
            self.certificateManagerGUI = CertificateManager.CertificateManagerWXGUI()
            self.certificateManager = CertificateManager.CertificateManager(GetUserConfigDir(),
                                                                            self.certificateManagerGUI)
            self.certificateManager.InitEnvironment()
        
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(500, 400))
        self.SetTopWindow(self.frame)

        if self.isPersonalNode:
            def setSvcCallback(svcUrl, self = self):
                log.debug("setting node service URI to %s from PersonalNode", svcUrl)
                self.SetNodeServiceUri(svcUrl)
            self.personalNode = PersonalNode.PersonalNodeManager(setSvcCallback, self.debugMode)
            self.personalNode.Run()
        
        return true

    def __Usage(self):
        print "%s:" % (sys.argv[0])
        print "  -h|--help:      print usage"
        if sys.platform == "win32":
            print "  --personalNode: manage services as a personal node"
        
    def __processArgs(self):
        """
        Handle any arguments we're interested in.

        --personalNode: Handle startup of local node services.

        """

        try:
            if sys.platform == "win32":
                opts, args = getopt.getopt(sys.argv[1:], "hd",
                                           ["personalNode", "debug", "help"])
            else:
                opts, args = getopt.getopt(sys.argv[1:], "hd",
                                           ["debug", "help"])
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
        self.personalDataStorePath = os.path.join(self.accessGridPath, self.personalDataStorePrefix)
        self.personalDataFile = os.path.join(self.personalDataStorePath, "myData.txt" )

        if not os.path.exists(self.personalDataStorePath):
            try:
                os.mkdir(self.personalDataStorePath)
            except OSError, e:
                wxLogError("Could not create venueStoragePath.")
                self.personalDataStorePath = None
                
        self.dataStore = DataStore.DataStore(self, self.personalDataStorePath,
                                   self.personalDataStorePrefix)
        self.transferEngine = GSIHTTPTransferServer(('', self.personalDataStorePort))
        self.transferEngine.run()
        self.transferEngine.RegisterPrefix(self.personalDataStorePrefix, self)
        self.dataStore.SetTransferEngine(self.transferEngine)
              
        wxLogDebug("Creating personal datastore at %s using prefix %s and port %s" %(self.personalDataStorePath,
                                                                          self.personalDataStorePrefix, self.personalDataStorePort))
        # load personal data
        if os.path.exists(self.personalDataFile):
            file = open(self.personalDataFile, 'r')
            self.personalDataDict = cPickle.load(file)
            file.close()

        wxLogDebug("check for validity")
        for file, desc in self.personalDataDict.items():
            wxLogDebug("Checking file %s for validity"%file)
            url = self.transferEngine.GetDownloadDescriptor(self.personalDataStorePrefix, file)
            wxLogDebug("File url is %s"%url)
            
            if url is None:
                del self.personalDataDict[file]
                                          
    def __setLogger(self):
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

    def __createHomePath(self):
        self.accessGridPath = GetUserConfigDir()
        
        self.profileFile = os.path.join(self.accessGridPath, "profile" )
        wxLogDebug("Home path is %s" %self.accessGridPath)
        try:  # does the profile dir exist?
            os.listdir(self.accessGridPath)
            wxLogDebug("profile exists")
                      
        except:
            wxLogDebug("profile does not exist")
            os.mkdir(self.accessGridPath)

           
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

    def AuthorizeLead(self, clientProfile):
        """
        Note: Overloaded from VenueClient
        This method  notifies the user that somebody wants to follow him or
        her and allows the user to approve the request.
        """
        wxCallAfter(self.frame.AuthorizeLeadDialog, clientProfile)

   
    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        Note: Overloaded from VenueClient
        This method notifies the user if the request to follow somebody is approved
        or denied.
        """
        VenueClient.LeadResponse(self, leaderProfile, isAuthorized)
        wxCallAfter(self.frame.NotifyLeadDialog, leaderProfile, isAuthorized)

    LeadResponse.soap_export_as = "LeadResponse"
    
    
    def NotifyUnLead(self, clientProfile):
        """
        Note: Overloaded from VenueClient
        This method  notifies the user that somebody wants to stop following him or
        her
        """
        wxCallAfter(self.frame.NotifyUnLeadDialog, clientProfile)

    def __openProfileDialog(self):
        """
        This method opens a profile dialog where the user can fill in
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

    def AddUserEvent(self, user):
        if(user.profileType == 'user'):
            wxCallAfter(self.frame.contentListPanel.AddParticipant, user)
            wxCallAfter(wxLogDebug, "   %s" %(user.name))
        else:
            wxCallAfter(self.frame.contentListPanel.AddNode, user)
            wxCallAfter(wxLogDebug, "   %s" %(user.name))

    def RemoveUserEvent(self, user):
        if(user.profileType == 'user'):
            wxCallAfter(self.frame.contentListPanel.RemoveParticipant, user)
            wxCallAfter(wxLogDebug,"   %s" %(user.name))
        else:
            wxCallAfter(self.frame.contentListPanel.RemoveNode, user)
            wxCallAfter(wxLogDebug,"   %s" %(user.name))
                        
                        
    def ModifyUserEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Modify participant: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.ModifyParticipant, data)
          
    def AddDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Add data: %s" %(data.name))
        wxCallAfter(wxLogDebug, "EVENT - Add data: %s" %(data.type))
        wxCallAfter(self.frame.contentListPanel.AddData, data)
        

    def UpdateDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Update data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.UpdateData, data)
        
    def RemoveDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Remove data: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.RemoveData, data)


    def AddServiceEvent(self, service):
        """
        Note: Overloaded from VenueClient
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Add service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.AddService, service)


    def RemoveServiceEvent(self, service):
        """
        Note: Overloaded from VenueClient
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Remove service: %s" %(service.name))
        wxCallAfter(self.frame.contentListPanel.RemoveService, service)

        
    def AddConnectionEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Add connection: %s" %(data.name))
        wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, data)
      
    def SetConnectionsEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Set connections")
        wxCallAfter(self.frame.venueListPanel.CleanUp)
               
        for connection in data:
            wxCallAfter(wxLogDebug, "EVENT - Add connection: %s" %(connection.name))
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """

        wxCallAfter(wxLogDebug, "EVENT- Enter venue with url: %s" %(URL))
        
        if self.venueUri != None:
            self.oldUri = self.venueUri
        else:
            self.oldUri = None

        # clean up ui from last venue
        if self.oldUri != None:
            wxCallAfter(wxLogDebug, "clean up frame and exit")
            wxCallAfter(self.frame.CleanUp)

        VenueClient.EnterVenue( self, URL )
       
        venueState = self.venueState
        wxCallAfter(self.frame.SetLabel, venueState.name)

        # Load users
        users = venueState.users.values()
        wxCallAfter(wxLogDebug, "Add participants")
        for user in users:
            if(user.profileType == 'user'):
                wxCallAfter(self.frame.contentListPanel.AddParticipant, user)
                wxCallAfter(wxLogDebug, "   %s" %(user.name))
            else:
                wxCallAfter(self.frame.contentListPanel.AddNode, user)
                wxCallAfter(wxLogDebug, "   %s" %(user.name))

        # Load data 
        data = venueState.data.values()
        wxCallAfter(wxLogDebug, "Add data")
        for d in data:
            wxCallAfter(self.frame.contentListPanel.AddData, d)
            wxCallAfter(wxLogDebug, "   %s" %(d.name))

        # Load nodes
        wxCallAfter(wxLogDebug, "Add nodes")
        nodes = venueState.nodes.values()
        for node in nodes:
            wxCallAfter(self.frame.contentListPanel.AddNode, node)
            wxCallAfter(wxLogDebug, "   %s" %(node.name))

        # Load exits
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

        # Data storage location
        self.upload_url = self.client.GetUploadDescriptor()
        wxCallAfter(wxLogDebug, "Get upload url %s" %self.upload_url)

        # Add personal data to venue
        for data in self.personalDataDict.values():
            self.client.AddData(data)
        
    EnterVenue.soap_export_as = "EnterVenue"

    def ExitVenue(self):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        wxCallAfter(wxLogDebug, "Cleanup frame, save data, and exit venue")
       
        try:
            wxCallAfter(self.frame.CleanUp)
        except:
            pass
        
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
        wxCallAfter(wxLogDebug, "Go to new venue")
        self.oldUri = None
        
        if not HaveValidProxy():
            wxCallAfter(wxLogDebug, "You don't have a valid proxy")
            GPI()
                               
        if self.venueUri != None:
            self.oldUri = self.venueUri
        #else:
        #    self.oldUri = None
            
        try: # is this a server
            wxCallAfter(wxLogDebug, "Is this a server")
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            wxCallAfter(wxLogDebug, "server url: %s" %venueUri)
            
        except: # no, it is a venue
            venueUri = uri
            wxCallAfter(wxLogDebug, "venue url: %s" %venueUri)

        self.clientHandle = Client.Handle(venueUri)
        if(self.clientHandle.IsValid()):
             wxCallAfter(wxLogDebug, "the handler is valid")
            
             try:
                 self.client = self.clientHandle.get_proxy()
                 self.gotClient = true
                 #if self.oldUri != None:
                 #    wxCallAfter(wxLogDebug, "clean up frame and exit")
                 #    wxCallAfter(self.frame.CleanUp)
                 #    self.ExitVenue()

                 self.EnterVenue(venueUri)
                 wxCallAfter(wxLogDebug, "after enter venue %s" %venueUri)
                 self.__setHistory(self.oldUri, back)
                 wxCallAfter(self.frame.ShowMenu)
               
             except:
                 wxCallAfter(wxLogError, "Error while trying to enter venue")
                 if self.oldUri != None:
                     wxCallAfter(wxLogDebug,"Go back to old venue")
                     # go back to venue where we came from
                     self.EnterVenue(self.oldUri) 
        else:
            wxCallAfter(wxLogDebug, "Handler is not valid")
            if not HaveValidProxy():
                text = 'You do not have a valid proxy.' +\
                       '\nPlease, run "grid-proxy-init" on the command line"'
                text2 = 'Invalid proxy'

            else:
                
                if self.oldUri is None:
                    wxCallAfter(self.frame.FillInAddress, None, self.profile.homeVenue)

                else:
                    wxCallAfter(self.frame.FillInAddress, None, self.oldUri)
                    

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
        wxLogDebug("Upload personal files")
        self.dataStore.AddFile(fileList, self.profile.distinguishedName, self.profile.publicId) 
        #self.uploadPersonalDataUrl = self.dataStore.GetUploadDescriptor()
        #self.UploadFiles(fileList, self.uploadPersonalDataUrl,
        #                self.get_ident_and_upload)

    def UploadVenueFiles(self, fileList):
        wxLogDebug("Upload venue files")
        self.UploadFiles(fileList, self.upload_url,
                         self.get_ident_and_upload)
    
    def UploadFiles(self, file_list, url, method):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.

        """
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
            
        except:
            wxLogError("Error  occured when trying to add data")
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
                                             
        self.SetProfile(self.profile)

        if(self.gotClient):
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
        self.SetNodeServiceUri(url)

    # Methods to for personal data storage to call
    def GetData(self, filename):
        wxLogDebug("Get private data description: %s" %filename)
        if self.personalDataDict.has_key(filename):
            d = self.personalDataDict[filename]
        else:
            wxLogDebug("The private file does not exist")
            d = None
        return d

    def UpdateData(self, desc):
        self.personalDataDict[desc.GetName()] = desc
        self.client.UpdateData(desc)
        wxLogDebug("UpdateData: %s" %desc)


if __name__ == "__main__":

    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()        

    
  
