#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueClient.py
# Purpose:     This is the client software for the user.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueClient.py,v 1.43 2003-02-14 21:14:57 olson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT -----------------------------------------------------------------------------
import threading
import os

from wxPython.wx import *

from pyGlobus.io import GSITCPSocketException

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid.Platform import GPI 
from AccessGrid.VenueClient import VenueClient, EnterVenueException
from AccessGrid.VenueClientUIClasses import WelcomeDialog
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.VenueClientUIClasses import UrlDialog, UrlDialogCombo
from AccessGrid.VenueClientUIClasses import SaveFileDialog, UploadFilesDialog
from AccessGrid.Descriptions import DataDescription
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.UIUtilities import ErrorDialog

from AccessGrid.TextClientUI import TextClientUI
from AccessGrid.hosting.pyGlobus.Utilities import GetDefaultIdentityDN
from AccessGrid import DataStore

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
        self.__createHomePath()
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(300, 400))
        self.SetTopWindow(self.frame)
        self.client = None
        self.gotClient = false
        return true

    def __createHomePath(self):
        if sys.platform == "win32":
            myHomePath = os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']
        elif sys.platform == "linux2":
            myHomePath = os.environ['HOME']

        self.accessGridPath = os.path.join(myHomePath, '.AccessGrid')
        self.profileFile = os.path.join(self.accessGridPath, "profile" )

        try:  # does the profile dir exist?
            os.listdir(self.accessGridPath)
                      
        except:
            os.mkdir(self.accessGridPath)


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
        
        self.profile = ClientProfile(self.profileFile)
                  
        if self.profile.IsDefault():  # not your profile
            self.__openProfileDialog()
        else:
            self.__startMainLoop(self.profile)

    def __openProfileDialog(self):
        """
        This method opens a profile dialog where the user can fill in
        his or her information.  
        """
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', self.profile)

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
        self.gotClient = true
        self.SetProfile(profile)
        
        if self.GoToNewVenue(self.profile.homeVenue):
            self.frame.Show(true)
            self.MainLoop()
        
        else:
            validVenue = false
            
            while not validVenue:
                connectToVenueDialog = UrlDialogCombo(NULL, -1, "Please, enter venue or venue server URL", list = self.frame.myVenuesList)
                if(connectToVenueDialog.ShowModal() == wxID_OK):
                    if self.GoToNewVenue(connectToVenueDialog.address.GetValue()):
                        self.frame.Show(true)
                        self.MainLoop()
                        notValidVenue = true
                  
                else:
                    break
              
    def ModifyUserEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.ModifyParticipant, data)
        pass

    def AddDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.AddData, data)
        pass

    def UpdateDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.UpdateData, data)
        pass

    def RemoveDataEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.RemoveData, data)
        pass

    def AddServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.AddService,data)
        pass

    def RemoveServiceEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a service is removed from the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.contentListPanel.RemoveService, data)
        pass

    def AddConnectionEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, data)
        pass

    def SetConnectionsEvent(self, data):
        """
        Note: Overloaded from VenueClient
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.
        """
        wxCallAfter(self.frame.venueListPanel.CleanUp)
        
        for connection in data:
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, connection)

        pass

    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        VenueClient.EnterVenue( self, URL )
        venueState = self.venueState
        wxCallAfter(self.frame.SetLabel, venueState.description.name)
        name = self.profile.name
        title = self.venueState.description.name
        description = self.venueState.description.description
        welcomeDialog = WelcomeDialog(NULL, -1, 'Enter Venue', name,
                                      title, description)

        users = venueState.users.values()
        for user in users:
            if(user.profileType == 'user'):
                wxCallAfter(self.frame.contentListPanel.AddParticipant, user)
            else:
                wxCallAfter(self.frame.contentListPanel.AddNode, user)

        data = venueState.data.values()
        for d in data:
            wxCallAfter(self.frame.contentListPanel.AddData, d)

        nodes = venueState.nodes.values()
        for node in nodes:
            wxCallAfter(self.frame.contentListPanel.AddNode, node)
        services = venueState.services.values()
        for service in services:
            wxCallAfter(self.frame.contentListPanel.AddService, service)

        exits = venueState.connections.values()
        for exit in exits:
            wxCallAfter(self.frame.venueListPanel.list.AddVenueDoor, exit)

        # Start text client
        textLoc = tuple(self.venueState.GetTextLocation())
        try:
            self.textClient = TextClientUI(self.frame, -1, "", location = textLoc)
            self.textClient.Show(true)
        except:
            wxCallAfter(ErrorDialog, self.frame, "Trying to open text client!")


        #
        # Find the upload location. HACK for now, this should come in
        # thru the venue description.
        #
        self.upload_url = self.client.GetUploadDescriptor()

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

        VenueClient.ExitVenue(self)
        
    def GoToNewVenue(self, uri):
        if self.venueUri != None:
            oldUri = self.venueUri
        else:
            oldUri = None
            
        try: # is this a server
            venueUri = Client.Handle(uri).get_proxy().GetDefaultVenue()
            
        except: # no, it is a venue
            venueUri = uri

        try:
            self.client = Client.Handle(venueUri).get_proxy()
            if oldUri != None:
                wxCallAfter(self.frame.CleanUp)
                self.ExitVenue()
            
            self.EnterVenue(venueUri)
            return true
        
        except GSITCPSocketException:  # no proxy
            GPI() # create proxy

            try:
                self.client = Client.Handle(venueUri).get_proxy()
                if oldUri != None:
                    wxCallAfter(self.frame.CleanUp)
                    self.ExitVenue()
                self.EnterVenue(venueUri)
                return true

            except EnterVenueException:
                if oldUri != None:
                    self.EnterVenue(oldUri) # go back to venue where we came from
                    return true
                else:
                    return false
        
        except EnterVenueException:
            if oldUri != None:
                self.EnterVenue(oldUri) # go back to venue where we came from
            else:
                return false
    
    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        self.ExitVenue()
        os._exit(1)
                
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

            print "descriptor is ", data_descriptor.__class__
            if data_descriptor.status != DataDescription.STATUS_PRESENT:
                dlg = wxMessageDialog(self.frame, 
                                      'File %s is not downloadable - it has status "%s"'
                                      % (data_descriptor.name, data_descriptor.status),
                                      "Invalid file",
                                      style = wxOK)
                
                dlg.ShowModal()
                dlg.Destroy()
                return

            #
            # Create the dialog for the download.
            #

            dlg = SaveFileDialog(self.frame, -1, "Saving file",
                                 "Saving file to %s ...     " % (local_pathname),
                                 "Saving file to %s ... done" % (local_pathname),
                                 size)

            print "Downloading: size=%s checksum=%s url=%s" % (size, checksum, url)
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
                my_identity = GetDefaultIdentityDN()
                try:
                    DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                                               checksum, progressCB)
                except DataStore.DownloadFailed, e:
                    print "Got exception on download: ", e

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
            dlg = wxMessageDialog(self.frame, failure_reason, "Download error",
                                  wxOK  | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            


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
        #
        # We use get_ident_and_upload as the body of the thread.
        #

        def get_ident_and_upload(upload_url, file_list, progressCB):
            print "Upload: getting identity"
            
            my_identity = GetDefaultIdentityDN()

            print "Got identity ", my_identity

            error_msg = None
            try:
                DataStore.HTTPUploadFiles(my_identity, upload_url, file_list, progressCB)
            except DataStore.FileNotFound, e:
                error_msg = "File not found: %s" % (e[0])
            except DataStore.NotAPlainFile, e:
                error_msg = "Not a plain file: %s" % (e[0])
            except DataStore.UploadFailed, e:
                error_msg = "Upload failed: %s" % (e)

            if error_msg is not None:
                print "Upload error ", error_msg
                #
                # TODO : put this stuff in a routine to wxCallAfter since
                # we can't do this here
                #dlg = wxMessageDialog(self.frame, error_msg, "Upload error",
                #                      wxOK  | wxICON_INFORMATION)
                #dlg.ShowModal()
                #dlg.Destroy()
                    
        #
        # Arguments to pass to get_ident_and_upload
        #

        ul_args = (self.upload_url, file_list, progressCB)

        print "Have args, creating thread ", ul_args

        upload_thread = threading.Thread(target = get_ident_and_upload,
                                           args = ul_args)

        #
        # Use wxCallAfter so we get the dialog filled in properly.
        #
        wxCallAfter(upload_thread.start)

        print "started thread"

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

        print "getting identity"
        my_identity = GetDefaultIdentityDN()
        upload_url = self.upload_url
        print "Have identity=%s upload_url=%s" % (my_identity, upload_url)

        error_msg = None
        try:
            DataStore.HTTPUploadFiles(my_identity, upload_url, file_list)
        except DataStore.FileNotFound, e:
            error_msg = "File not found: %s" % (e[0])
        except DataStore.NotAPlainFile, e:
            error_msg = "Not a plain file: %s" % (e[0])
        except DataStore.UploadFailed, e:
            error_msg = "Upload failed: %s" % (e)

        if error_msg is not None:
            print "Showing ", error_msg
            dlg = wxMessageDialog(self.frame, error_msg, "Upload error",
                                  wxOK  | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            
        print "Upload done"

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
        self.profile = profile
        self.profile.Save(self.profileFile)
        self.SetProfile(self.profile)

        if self.gotClient:
            self.client.UpdateClientProfile(profile)

    def SetNodeUrl(self, url):
        """
        This method sets the node service url
        """
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
       

    
  
