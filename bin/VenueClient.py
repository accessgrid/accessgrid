#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.76 2003-03-21 17:12:22 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import threading
import os
import logging, logging.handlers

from wxPython.wx import *

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid.Platform import GPI 
from AccessGrid.VenueClient import VenueClient
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.Descriptions import DataDescription
from AccessGrid.Utilities import HaveValidProxy
from AccessGrid.UIUtilities import MyLog 
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN 
from AccessGrid import DataStore

from AccessGrid.hosting.pyGlobus import Server

if sys.platform == "win32":
    from win32com.shell import shell, shellcon
    
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

    def OnInit(self):
        """
        This method initiates all gui related classes.
        """
        VenueClient.__init__(self)
        #self.CreateFollowLeadServer()
        self.__setLogger()
        self.__createHomePath()
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(500, 400))
        self.SetTopWindow(self.frame)
        return true
    
    def __setLogger(self):
        logger = logging.getLogger("AG.VenueClient")
        logger.setLevel(logging.DEBUG)
        logname = "VenueClient.log"
        hdlr = logging.handlers.RotatingFileHandler(logname, "a", 10000000, 0)
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
        hdlr.setFormatter(fmt)
        logger.addHandler(hdlr)
        log = logging.getLogger("AG.VenueClient")

        wxLog_SetActiveTarget(wxLogGui())  
        wxLog_SetActiveTarget(wxLogChain(MyLog(log)))
        wxLogInfo(" ")
        wxLogInfo("--------- START VenueClient")

    def __createHomePath(self):
        if sys.platform == "win32":
            myHomePath = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0) 
            #myHomePath = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']
        elif sys.platform == "linux2":
            myHomePath = os.environ['HOME']

        self.accessGridPath = os.path.join(myHomePath, '.AccessGrid')
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
        
    def AddServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Add service: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.AddService,data)
      
    def RemoveServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(wxLogDebug, "EVENT - Remove service: %s" %(data.name))
        wxCallAfter(self.frame.contentListPanel.RemoveService, data)
      
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

        # Make people you lead go to this venue
        self.__getFollowers(URL)

        if self.venueUri != None:
            self.oldUri = self.venueUri
        else:
            self.oldUri = None

        # clean up ui from last venue
        if self.oldUri != None:
            wxCallAfter(wxLogDebug, "clean up frame and exit")
            wxCallAfter(self.frame.CleanUp)
            #self.ExitVenue()

        VenueClient.EnterVenue( self, URL )
       
        venueState = self.venueState
        wxCallAfter(self.frame.SetLabel, venueState.description.name)
        #name = self.profile.name
        #title = self.venueState.description.name
        #description = self.venueState.description.description
        # welcomeDialog = WelcomeDialog(NULL, -1, 'Enter Venue', name,
        #                               title, description)

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

        # Load services
        wxCallAfter(wxLogDebug, "Add services")
        services = venueState.services.values()
        for service in services:
            wxCallAfter(self.frame.contentListPanel.AddService, service)
            wxCallAfter(wxLogDebug, "   %s" %(service.name))

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
        
    EnterVenue.soap_export_as = "EnterVenue"

    def ExitVenue(self):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        wxCallAfter(wxLogDebug, "Exit venue")
        VenueClient.ExitVenue(self)

    def __setHistory(self, uri, back):
        """
        This method sets the history list, which stores visited
        venue urls used by the back button.
        """
        wxLogDebug("Set history url: %s " %uri)
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
        wxLogDebug("Go back")
        
        l = len(self.history)
        if(l>0):
            uri = self.history[l - 1]
            self.GoToNewVenue(uri, true)
      
    def GoToNewVenue(self, uri, back = false):
        """
        GoToNewVenue(url, back) transports the user to a new venue with same url as
        the input parameter.  If the url is a server address, we will instead enter
        the default venue on the server.  If the url is invalid, the user re-enters
        the venue he or she just left. 
         """
        wxLogDebug("Go to new venue")
        self.oldUri = None
        
        if not HaveValidProxy():
            wxLogDebug("You don't have a valid proxy")
            GPI()
                               
        if self.venueUri != None:
            self.oldUri = self.venueUri
        else:
            self.oldUri = None
            
        try: # is this a server
            wxLogDebug("Is this a server")
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            wxLogDebug("server url: %s" %venueUri)
            
        except: # no, it is a venue
            venueUri = uri
            wxLogDebug("venue url: %s" %venueUri)

        self.clientHandle = Client.Handle(venueUri)
        if(self.clientHandle.IsValid()):
            wxLogDebug("the handler is valid")
            
            try:
                self.client = self.clientHandle.get_proxy()
                self.gotClient = true
                #if self.oldUri != None:
                #    wxLogDebug("clean up frame and exit")
                #    wxCallAfter(self.frame.CleanUp)
                #    self.ExitVenue()

                wxLogDebug("--enter venue %s" %venueUri)
                wxLogDebug(str(Client.Handle(venueUri).IsValid()))
                self.EnterVenue(venueUri)
                wxLogDebug("--after enter venue %s" %venueUri)
                self.__setHistory(self.oldUri, back)
                wxCallAfter(self.frame.ShowMenu)
               
            except:
                wxLogError("Error while trying to enter venue")
                if self.oldUri != None:
                    wxLogDebug("Go back to old venue")
                    self.EnterVenue(self.oldUri) # go back to venue where we came from
                    
        else:
            wxLogDebug("Handler is not valid")
            if not HaveValidProxy():
                text = 'You do not have a valid proxy.' +\
                       '\nPlease, run "grid-proxy-init" on the command line"'
                text2 = 'Invalid proxy'

            else:
                if oldUri is None:
                    wxCallAfter(self.frame.FillInAddress, None, self.profile.homeVenue)

                else:
                    wxCallAfter(self.frame.FillInAddress, None, oldUri)
                    

                text = 'The venue URL you specified is not valid'
                text2 = 'Invalid URL'

            wxLogMessage(text)
            wxLog_GetActiveTarget().Flush()

    def __getFollowers(self, venueUrl):
        wxLogDebug('Tell followers to go to url:%s ' %venueUrl)
        for person in self.followerProfiles.values():
            url = person.venueClientURL
            followerHandle = Client.Handle(url)
            wxLogDebug('This person is following me, url:%s ' %url)
            if(followerHandle.IsValid()):
                wxLogDebug("the follower handler is valid")
                followerProxy = followerHandle.get_proxy()
                followerProxy.EnterVenue(venueUrl)
                wxLogDebug("told followers to enter url: %s "%venueUrl)

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        wxLogInfo("--------- END VenueClient")
        if self.venueUri != None:
            self.ExitVenue()

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
        wxCallAfter(wxLogDebug, "Save file")
        
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

            wxCallAfter(wxLogDebug, "data descriptor is %s" %data_descriptor.__class__)
            
            if data_descriptor.status != DataDescription.STATUS_PRESENT:
                wxCallAfter(wxLogMessage, "File %s is not downloadable - it has status %s"
                            % (data_descriptor.name, data_descriptor.status))
                wxCallAfter(wxLog_GetActiveTarget().Flush)

                #MessageDialog(self.frame, 
                #              'File %s is not downloadable - it has status "%s"'
                #              % (data_descriptor.name, data_descriptor.status),
                #              "Invalid file",
                #              style = wxOK)
                
                return

            #
            # Create the dialog for the download.
            #

            dlg = SaveFileDialog(self.frame, -1, "Saving file",
                                 "Saving file to %s ...     " % (local_pathname),
                                 "Saving file to %s ... done" % (local_pathname),
                                 size)

            wxCallAfter(wxLogDebug, "Downloading: size=%s checksum=%s url=%s" % (size, checksum, url))
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
            # Some more plumbing with the locla function to get the identity
            # retrieval in the thread, as it can take a bit the first time.
            #
            # We use get_ident_and_download as the body of the thread.
            #

            def get_ident_and_download(url, local_pathname, size, checksum, progressCB):
                try:
                    if url.startswith("https"):
                        DataStore.GSIHTTPDownloadFile(url, local_pathname, size,
                                                      checksum, progressCB)

                    else:
                        my_identity = GetDefaultIdentityDN()
                        DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                                                   checksum, progressCB)
                except DataStore.DownloadFailed, e:
                    wxCallAfter(wxLogError, "Got exception on download")
                    
            #
            # Arguments to pass to get_ident_and_download
            #

            dl_args = (url, local_pathname, size, checksum, progressCB)

            download_thread = threading.Thread(target = get_ident_and_download,
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
            MessageDialog(self.frame, failure_reason, "Download error",
                                  wxOK  | wxICON_INFORMATION)

    def UploadFiles(self, file_list):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.

        """
        #
        # Create the dialog for the download.
        #

        dlg = UploadFilesDialog(self.frame, -1, "Uploading files")
        
        dlg.Show(1)

        # 
        # Plumbing for getting progress callbacks to the dialog
        #

        def progressCB(filename, sent, total, file_done, xfer_done, dialog = dlg):
            wxCallAfter(dialog.SetProgress, filename, sent, total, file_done, xfer_done)
            return dialog.IsCancelled()

        #
        # Create the thread to run the upload.
        #
        # Some more plumbing with the local function to get the identity
        # retrieval in the thread, as it can take a bit the first time.
        #        # We use get_ident_and_upload as the body of the thread.
        #

        def get_ident_and_upload(upload_url, file_list, progressCB):
            wxCallAfter(wxLogDebug, "Upload: getting identity")
                        
            error_msg = None
            try:
                if upload_url.startswith("https:"):
                    DataStore.GSIHTTPUploadFiles(upload_url, file_list, progressCB)
                else:
                    my_identity = GetDefaultIdentityDN()
                    wxCallAfter(wxLogDebug, "Got identity %s" %my_identity)
                    DataStore.HTTPUploadFiles(my_identity, upload_url, file_list, progressCB)
                    
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

        #
        # Arguments to pass to get_ident_and_upload
        #
        
        ul_args = (self.upload_url, file_list, progressCB)

        wxCallAfter(wxLogDebug, "Have args, creating thread")
            
        upload_thread = threading.Thread(target = get_ident_and_upload,
                                         args = ul_args)
        
        #
        # Use wxCallAfter so we get the dialog filled in properly.
        #
        wxCallAfter(upload_thread.start)
        
        wxCallAfter(wxLogDebug, "Started thread")
        
        #
        # Fire up dialog as a modal.
        #
        
        dlg.ShowModal()

        #
        # The dialog has returned. This is either because the upload
        # finished and the user clicked OK, or because the user clicked
        # Cancel to abort the upload. In either event the
        # call to HTTPUploadFiles should return, and the thread quit.
        #
        # Wait for the thread to finish (if it doesn't it's a bug).
        #
        #
        
        upload_thread.join()
        
        #
        # Clean up.
        #
        dlg.Destroy()
        

    def UploadFilesNoDialog(self, file_list):
        """
        Upload the given files to the venue.

        This uses the DataStore HTTP upload engine code.
        """

        wxCallAfter(wxLogDebug, "Upload files - no dialog")
        upload_url = self.upload_url
        wxCallAfter(wxLogDebug, "Have identity=%s upload_url=%s" % (my_identity, upload_url))

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
           

    def FollowParticipant(self, personToFollow):
        #url = personToFollow.venueClientURL
        #followHandle = Client.Handle(url)
        #if(followHandle.IsValid()):
        #    wxLogDebug("the follow handler is valid")
        try:
            #personToFollowProxy = self.clientHandle.get_proxy()
            #personToFollowProxy.Follow(personToFollow.venueClientURL)
            wxLogDebug("You are trying to follow %s" %personToFollow.name)
            self.Follow(personToFollow.venueClientURL)
            wxLogDebug("You are following %s" %personToFollow.name)
                
        except:
            wxLogError("Can not follow %s" %personToFollow.name)

    def AddData(self, data):
        """
        This method adds data to the venue
        """
        wxLogDebug("Adding data: %s to venue" %data.name)
        try:
            self.client.AddData(data)
            
        except:
            wxLogError("Error  occured when trying to add data")
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
        
    def RemoveData(self, data):
        """
        This method removes a data from the venue
        """
        wxLogDebug("Remove data: %s from venue" %data.name)
        try:
            self.client.RemoveData(data)

        except:
            wxLogError("Error occured when trying to remove data")
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
                     
if __name__ == "__main__":

    import sys
    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    wxInitAllImageHandlers()

    vc = VenueClientUI()
    vc.ConnectToVenue()
       

    
  
