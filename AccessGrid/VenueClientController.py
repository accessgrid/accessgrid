#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClientController.py
# Purpose:     This is the controller module for the venue client
#
# Author:      Thomas D. Uram
#
# Created:     2004/02/20
# RCS-ID:      $Id: VenueClientController.py,v 1.2 2004-02-24 18:36:21 turam Exp $
# Copyright:   (c) 2002-2004
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------


# standard imports
import cPickle
import logging
import os
import re
import threading
import time


# Access Grid imports
from AccessGrid import DataStore
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import ServiceDescription,DataDescription,ApplicationDescription
from AccessGrid.Platform import GetUserConfigDir,GetUserAppPath

from AccessGrid.Platform import GetMimeCommands
from AccessGrid.Platform import GetSharedDocDir, GetTempDir
from AccessGrid.Platform import isWindows

from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType

from AccessGrid import Toolkit

log = logging.getLogger("AG.VenueClientController")

class NotAuthorizedError(Exception):
    pass


class VenueClientController:

    def __init__(self):
    
        self.history = []
        self.myVenuesFile = os.path.join(GetUserConfigDir(), "myVenues.txt" )
        
        self.__LoadMyVenues()


    ###########################################################################################
    #
    # Private Methods

    def __SetHistory(self, uri, back):
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
            
            
    def __LoadMyVenues(self):
        try:
            myVenuesFileH = open(self.myVenuesFile, 'r')
        except:
            log.exception("Failed to load MyVenues file")
        else:
            self.myVenuesDict = cPickle.load(myVenuesFileH)
            
        myVenuesFileH.close()
        
    # end Private Methods
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Controller Implementation

    def SetGui(self,gui):
        self.gui = gui
        
    def SetVenueClient(self,venueClient):
        self.venueClient = venueClient

    # end Controller Implementation
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Menu Callbacks

    def AddDataCB(self, fileList):
        # Upload if we have a file list
        if fileList:
            self.UploadVenueFiles(fileList)

    def AddServiceCB(self,serviceDescription):
        if serviceDescription:
            log.debug("Adding service: %s to venue" %serviceDescription.name)
            try:
                self.venueClient.AddService(serviceDescription)
            except Exception, e:
                if isinstance(e,faultType) and e.faultstring == "ServiceAlreadyPresent":
                    self.gui.Error("A service by that name already exists", "Add Service Error")
                else:
                    log.exception("bin.VenueClient::AddService: Error occured when trying to add service")
                    self.gui.Error("The service could not be added", "Add Service Error")

    def SaveTextCB(self,filePath,text):
        '''
        Saves text from text chat to file.
        '''
        if filePath:
            # Save the text from chat in file.
            try:
                textFile = open(filePath, "w")
                textFile.write(text)
                textFile.close()
            except:
                log.exception("VenueClientFrame.SaveText: Can not save text.")
                self.gui.Error("Text could not be saved.", "Save Text")
        
    def ModifyVenueRolesCB(self,rolesDict):
        try:
            if rolesDict:
                # Get new role configuration
                rolesDict = addPeopleDialog.GetInfo()
                # Set new role configuration
                if rolesDict:
                    RoleClient(venueUri).SetVenueRoles(rolesDict)

        except Exception, e:
            if isinstance(e, faultType) and str(e.faultstring) == "NotAuthorized":
                    text = "You are not authorized to administrate this venue.\n"
                    self.gui.Warn(text, "Not Authorized")
                    log.info("VenueClientFrame.OpenModifyVenueRolesDialog: Not authorized to administrate roles in this venue %s." % str(venueUri))
            else:
                log.exception("VenueClientFrame.OpenModifyVenueRolesDialog: Error administrating roles in this venue %s." % str(venueUri))
                text = "Error administrating roles in this venue " + str(venueUri) + "."
                self.gui.Error(text, "Venue Role Administration Error")

    def ExitCB(self):
        '''
        Called when the window is closed using the built in close button
        '''
        #
        # If we are connected to a venue, exit the venue
        # Do this before terminating services, since we need
        # to message them to shut down their services first
        #
        if self.venueClient.IsInVenue():
            self.venueClient.ExitVenue()

        self.venueClient.Shutdown()

        os._exit(0)  # this should not be necessary, replace if needed.



    #
    # Preferences Menu
    #
    
    def EditProfileCB(self,profile):
        if profile:
            self.ChangeProfile(profile)
        

    """
    ManageCertificates menu is provided by CertMgmt module
    """


    def UseMulticastCB(self):
        try:
            self.venueClient.SetTransport("multicast")
            self.venueClient.UpdateNodeService()
        except NetworkLocationNotFound, e:
            log.exception("VenueClientFrame.UseMulticast: EXCEPTION UPDATING NODE SERVICE")

    def UseUnicastCB(self,provider):

        oldProvider = self.venueClient.GetProvider()
        oldTransport = self.venueClient.GetTransport()

        # Set the transport in the venue client and update the node service
        self.venueClient.SetProvider(provider)
        self.venueClient.SetTransport("unicast")
        try:
            self.venueClient.UpdateNodeService()
        except NetworkLocationNotFound:

            # Reset the provider/transport 
            self.venueClient.SetProvider(oldProvider)
            self.venueClient.SetTransport(oldTransport)

            # Report the error to the user
            text="Can't access streams from selected bridge; reverting to previous selection"
            self.gui.Warn(None, text, "Use Unicast failed")


    def EnableVideoCB(self,enableFlag):
        try:
            self.venueClient.SetVideoEnabled(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling video", "Error enabling/disabling video")
            log.info("Couldn't enable/disable video")

    def EnableAudioCB(self,enableFlag):
        try:
            self.venueClient.SetAudioEnabled(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling audio", "Error enabling/disabling audio")
            log.info("Couldn't enable/disable video")
    
    def SetNodeUrlCB(self,nodeUrl):
        if nodeUrl:
            self.venueClient.SetNodeUrl(nodeUrl)

    
    # 
    # MyVenues Menu
    #
    
    def GoToDefaultVenueCB(self):
        venueUrl = self.venueClient.GetProfile().homeVenue
        self.EnterVenueCB(venueUrl, 1)

    def SetAsDefaultVenueCB(self):
        # Get the current profile
        profile = self.venueClient.GetProfile()

        # Update the home venue to the current venue url
        profile.homeVenue = self.venueClient.GetVenue()

        # Store the changes
        self.ChangeProfile(profile)

    def AddToMyVenuesCB(self,name,url):
        self.myVenuesDict[name] = url
        self.SaveMyVenuesToFile()

                       
    def EditMyVenuesCB(self,myVenuesDict):
        if myVenuesDict:
            self.myVenuesDict = myVenuesDict
            self.SaveMyVenuesToFile()

    def GoToMenuAddressCB(self,venueUrl):
        self.EnterVenueCB(venueUrl,0)

    # Menu Callbacks
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Core UI Callbacks
    
    def GoBackCB(self):
        l = len(self.history)
        if(l>0):
            #
            # Go to last venue in the history list
            #
            uri = self.history[l - 1]
            self.EnterVenueCB(uri, 1)
    
    def EnterVenueCB(self,venueUrl,backFlag):
        self.__SetHistory(self.venueClient.GetVenue(),backFlag)

        # Enter the venue
        self.venueClient.EnterVenue(venueUrl)

    #
    # Participant Actions
    #
       
    def AddPersonalDataCB(self, fileList):
        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #

                
        if fileList:
            # upload!
            self.UploadPersonalFiles(fileList)

    def FollowCB(self, personToFollow):

        if(personToFollow != None and isinstance(personToFollow, ClientProfile)):
            url = personToFollow.venueClientURL
            name = personToFollow.name
            log.debug("VenueClientFrame.Follow: You are trying to follow :%s url:%s " %(name, url))

            if(self.venueClient.leaderProfile == personToFollow):
                text = "You are already following "+name
                title = "Notification"
                self.gui.Notify(text, title)
            
            elif (self.venueClient.pendingLeader == personToFollow):
                text = "You have already sent a request to follow "+name+". Please, wait for answer."
                title = "Notification"
                self.gui.Notify(text,title)

            else:
                try:
                    self.venueClient.Follow(personToFollow)
                except:
                    log.exception("VenueClientFrame.Follow: Can not follow %s" %personToFollow.name)
                    text = "You can not follow "+name
                    title = "Notification"
                    self.gui.Notify(text, title)
                
    def UnFollowCB(self):

        log.debug("VenueClientFrame.Unfollow: In UnFollow we are being lead by %s" %self.venueClient.leaderProfile.name)
        if self.venueClient.leaderProfile != None :
           
            try:
              
                self.venueClient.UnFollow(self.venueClient.leaderProfile)
                self.meMenu.Remove(self.ID_ME_UNFOLLOW)
            except:
               
                log.exception("VenueClientFrame.Unfollow: Can not stop following %s" %self.venueClient.leaderProfile.name)

        else:
            log.debug("VenueClientFrame.Unfollow: You are trying to stop following somebody you are not following")
        


    #
    # Data Actions
    #

    """
    AddData is up above in menu callbacks
    """

    def OpenDataCB(self,data):
        """
        """
       
        if(data != None and isinstance(data, DataDescription)):
            name = data.name
            commands = GetMimeCommands(ext = name.split('.')[-1])
            if commands == None:
                self.gui.Notify("No client registered for the selected data","Open Data")
                log.debug("VenueClientFrame.OpenData: %s"%message)
            else:
                if commands.has_key('Open'):
                    cmd = commands['Open']
                    self.StartCmd(cmd, data, verb='Open')
        else:
            self.gui.Notify("Please, select the data you want to open", "Open Data")     
    
    def SaveDataCB(self,data,path):
        self.SaveFile(data,path)

    def RemoveDataCB(self,itemList):
        
        for item in itemList:

            if(item != None and isinstance(item, DataDescription)):
                text ="Are you sure you want to delete "+ item.name + "?"
                if self.gui.Prompt(text, "Confirmation"):

                    try:
                        self.venueClient.RemoveData(item)
                    except NotAuthorizedError:
                        log.info("bin.VenueClient::RemoveData: Not authorized to  remove data")
                        self.gui.Prompt("You are not authorized to remove the file", "Remove Personal Files")        
                    except:
                        log.exception("bin.VenueClient::RemoveData: Error occured when trying to remove data")
                        self.gui.Error("The file could not be removed", "Remove Personal Files Error")
                             
            else:
                self.gui.Error("Please, select the data you want to delete", "No file selected")




    #
    # Service Actions
    #
    
    """
    AddService is up above in menu callbacks
    """

    def OpenServiceCB(self,service):
        
        if(service != None and isinstance(service, ServiceDescription)):
            self.venueClient.OpenService( service )
        else:
            self.gui.Notify("Please, select the service you want to open","Open Service")       
    
    def RemoveServiceCB(self,itemList):
        for item in itemList:
            if(item != None and isinstance(item, ServiceDescription)):
                text ="Are you sure you want to delete "+ item.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    try:
                        self.venueClient.RemoveService(item)
                    except:
                        log.exception("bin.VenueClient::RemoveService: Error occured when trying to remove service")
                        self.gui.Error("The service could not be removed", "Remove Service Error")
            else:
               self.gui.Notify("Please, select the service you want to delete")       
        

    #
    # Application Actions
    #
    
    def OpenApplicationCB(self, appDesc):
        """
        """
      
        if appDesc != None and isinstance(appDesc, ApplicationDescription):
            self.RunApp(appDesc)
        else:
            self.gui.Notify("Please, select the data you want to open","Open Application")
    

    def RemoveApplicationCB(self,appList):

        for app in appList:
            if(app != None and isinstance(app, ApplicationDescription)):
                text ="Are you sure you want to delete "+ app.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    self.venueClient.DestroyApplication( app.id )
            else:
                self.gui.Notify( "Please, select the application you want to delete")
            

    def StartApplicationCB(self, name, appDesc):
        """
        Start the specified application.  This method creates the application
        in the venue.

        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to start
        """
        log.debug("VenueClientFrame.StartApp: Creating application: %s" % app.name)

        appName = appDesc.name + ' - ' + name
        self.venueClient.CreateApplication( appName,
                                            appDesc.description,
                                            app.mimeType )
              
    def RunApplicationCB(self, appDesc, cmd='Open'):
        appdb = Toolkit.GetApplication().GetAppDatabase()
        
        cmdline = appdb.GetCommandLine(appDesc.mimeType, cmd)

        self.StartCmd(cmdline, appDesc, verb=cmd)
        

    #
    # Application Integration code
    #
    def JoinApp(self,app):
        """
        Join the specified application

        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to join
        """
        log.debug("Joining application: %s / %s" % (app.name, app.mimeType))
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commands = appdb.GetCommandNames(app.mimeType)

        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % app.mimeType
            self.gui.Prompt(message,message )
            log.debug(message)
        else:
            if 'Open' in commands:
                cmdLine = appdb.GetCommandLine(app.mimeType, 'Open')
                log.debug("executing cmd: %s" % cmdLine)
                pid = wxExecute(cmdLine)
                
    def GetMimeCommandNames(self,mimeType):
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commands = appdb.GetCommandNames(mimeType = mimeType)
        return commands
        
    def GetMimeCommandLine(self,mimeType,command):
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commandLine = appdb.GetCommandLine(mimeType,command)        
        return commandLine
    #
    # Text Actions
    #
                
    def SendTextCB(self,text):
        self.venueClient.SendText(text)

    # end Core UI Callbacks
    #
    ###########################################################################################

    ###########################################################################################
    #
    # General Implementation

    def UploadVenueFiles(self, file_list):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.
        
        """
        log.debug("In VenueClientController.UploadVenueFiles")
        log.debug("  file_list = %s" % str(file_list))
        
        filesToAdd = []
        
        # Check if data is already added
        for file in file_list:
            pathParts = os.path.split(file)
            name = pathParts[-1]
            fileExists = 0
                                
            dataDescriptions = self.venueClient.GetVenueDataDescriptions()
            for data in dataDescriptions:
                if data.name == name:
                    fileExists = 1
                    break
                    
            if fileExists:
                # file exists; prompt for replacement
                title = "Duplicated File"
                info = "A file named %s is already added, do you want to overwrite?" % name
                if self.gui.Prompt(info,title):
                    self.venueClient.RemoveData(data)
                    filesToAdd.append(name)
            else:
                # file doesn't exist; add it           
                filesToAdd.append(name)

        if len(filesToAdd) < 1:
            return
            
        # Open the upload files dialog
        self.gui.OpenUploadFilesDialog()

        #
        # Plumbing for getting progress callbacks to the dialog
        #
        def progressCB(filename, sent, total, file_done, xfer_done):
            if not self.gui.UploadFilesDialogCancelled():
                self.gui.UpdateUploadFilesDialog(filename, sent, total,file_done, 
                                                 xfer_done)
            return self.gui.UploadFilesDialogCancelled()

        #
        # Create the thread to run the upload.
        #
        # Some more plumbing with the local function to get the identity
        # retrieval in the thread, as it can take a bit the first time.
        # We use get_ident_and_upload as the body of the thread.


        url = self.venueClient.GetDataStoreUploadUrl()
        method = self.get_ident_and_upload
        ul_args = (url, filesToAdd, progressCB)

        log.debug("Have args, creating thread, url: %s, files: %s", url, filesToAdd)

        upload_thread = threading.Thread(target = method, args = ul_args)

        upload_thread.start()
        log.debug("Started thread")

        #
        # Dialog dlg will get cleaned up at the end of get_ident_and_upload.
        #



    def get_ident_and_upload(self, upload_url, file_list, progressCB, dialog=None):
        log.debug("Upload: getting identity")

        error_msg = None
        try:
            if upload_url.startswith("https:"):
                log.debug("Url starts with https:")
                DataStore.GSIHTTPUploadFiles(upload_url, file_list, progressCB)
            else:
                my_identity = self.venueClient.GetDefaultIdentityDN()
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
            self.gui.Notify(error_msg, "Upload Files Error")



    def ChangeProfile(self, profile):
        """
        This method changes this participants profile and saves the information to file.

        **Arguments:**
        
        *profile* The ClientProfile including the new profile information
        """
        #self.venueClient.profile = profile
        #self.venueClient.profile.Save(self.profileFile)
        #log.debug("Save profile")

        # use profile from path
        #self.venueClient.profile = ClientProfile(self.profileFile)
        #self.venueClient.SetProfile(self.venueClient.profile)
        
        self.venueClient.SaveProfile()

        if(self.venueClient.venueUri != None):
            log.debug("Update client profile in venue")

            try:
                self.venueClient.UpdateClientProfile(profile)
            except:
                log.exception("bin.VenueClient::ChangeProfile: Error occured when trying to update profile")
                # User does not need to know about this. The profile info got saved locally anyhow.                
                #self.gui.Error("Your profile could not be changed", "Change Profile Error")
        else:
            log.debug("Can not update client profile in venue - not connected")




    def AuthorizeLeadDialog(self, clientProfile):
        idPending = None
        idLeading = None

        if(self.venueClient.pendingLeader!=None):
            idPending = self.venueClient.pendingLeader.publicId
          

        if(self.venueClient.leaderProfile!=None):
            idLeading = self.venueClient.leaderProfile.publicId
          
          
        if(clientProfile.publicId != idPending and clientProfile.publicId != idLeading):
            text = "Do you want "+clientProfile.name+" to follow you?"
            title = "Authorize follow"
            response = self.gui.Prompt(text, title)
            self.venueClient.SendLeadResponse(clientProfile, response)

            dlg.Destroy()

        else:
            self.venueClient.SendLeadResponse(clientProfile, 0)


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
                self.gui.Prompt("File %s is not downloadable - it has status %s"
                              % (data_descriptor.name,
                                 data_descriptor.status), "Notification")
                return
                
            log.debug("Downloading: size=%s checksum=%s url=%s"
                      % (size, checksum, url))


            self.gui.OpenSaveFileDialog(local_pathname, size)

            #
            # Plumbing for getting progress callbacks to the dialog
            #
            def progressCB(progress, done):
                if not self.gui.SaveFileDialogCancelled():
                    self.gui.UpdateSaveFileDialog(progress,done)
                return self.gui.SaveFileDialogCancelled()

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

            download_thread.start()

            #
            # Dialog dlg will get cleaned up at the end of get_ident_and_download.
            #

        except DataStore.DownloadFailed, e:
            failure_reason = "Download error: %s" % (e[0])
        except EnvironmentError, e:
            failure_reason = "Exception: %s" % (str(e))

        if failure_reason is not None:
            self.gui.Prompt(failure_reason, "Download error")


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
                self.gui.Prompt("File %s is not downloadable - it has status %s"
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
            self.gui.Prompt(failure_reason, "Download error")

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
                my_identity = self.app.GetDefaultIdentityDN()
                DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                                           checksum, progressCB)
        except DataStore.DownloadFailed, e:
            log.exception("bin.VenueClient:get_ident_and_download: Got exception on download")
            self.gui.Notify("The file could not be downloaded", "Download Error")
                       
                                
    def UploadPersonalFiles(self, fileList):
        """
        Upload the given personal files to the venue.

        """
        log.debug("Upload personal files")

        for file in fileList:

            # Check if data is already added
            pathParts = os.path.split(file)
            index = len(pathParts)-1
            name = pathParts[index]

            dataDescriptions = self.venueClient.GetDataDescriptions()
            for data in dataDescriptions:
                if data.name == name:
                    title = "Duplicated File"
                    info = "A file named %s is already added, do you want to overwrite?" % name
                    # Overwrite?
                    if self.gui.Prompt( info, title ):
                        self.venueClient.dataStore.RemoveFiles([data])
                        
                        # The data description have to be removed, else the size parameter will
                        # not match and open will fail for modified data.
                        self.venueClient.SendEvent(Events.RemoveDataEvent(self.venueClient.GetEventChannelId(), data))
                        
                    else:
                        return
                                         
            try:
                my_identity = self.app.GetDefaultIdentityDN()
                self.venueClient.dataStore.UploadLocalFiles([file], my_identity, self.venueClient.GetProfile().publicId)

                # Send an event alerting about new data (only if it is new)
                #if newData: 
                dataDescription = self.venueClient.dataStore.GetDescription(name)
                self.venueClient.SendEvent(Events.AddDataEvent(self.venueClient.GetEventChannelId(), 
                                                               dataDescription))
            except DataStore.DuplicateFile, e:
                title = "Duplicated File"
                info = "This file %s is already added. Rename your file and add it again." %e
                self.gui.Prompt(info, title)
                                                     
            except Exception, e:
                log.exception("bin.VenueClient:UploadPersonalFiles failed")
                title = "Add Personal Data Error"
                text = "The file could not be added, error occured."
                self.gui.Error(text, title)
                
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
                my_identity = self.app.GetDefaultIdentityDN()
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
            self.gui.Error(error_msg, "Upload Files Error")
           


    def StartCmd(self, command, item=None, namedVars=None, verb=None):
        """
        """
        localFilePath = None
        name = None
        if namedVars == None:
            namedVars = dict()

        if item == None:
            return

        # If item is data, download the filename specified in it.
        if isinstance(item, DataDescription):
            localFilePath = os.path.join(GetTempDir(),
                                         item.name.replace(" ", "_"))
            self.SaveFileNoProgress(item, localFilePath)

            # Fix odd commands
            if isWindows():
                if command.find("%1") != -1:
                    command = command.replace("%1", "")
                if command.find("%L") != -1:
                    command = command.replace("%L", "")
                if command.find("%*") != -1:
                    command = command.replace("%*", "")
            else:
                if command.find("%s") != -1:
                    command = command.replace("%s", "")

            command = command.replace("\"\"", "")
            
            if len(command) > 1:
                if command.find("%") == -1:
                    command = "\""+command+" \"%(localFilePath)s\"\""
            else:
                command = "\"%(localFilePath)s\""
            
        else:
            # Get the app dir and run
            if isinstance(item, ApplicationDescription):
                appdb = Toolkit.GetApplication().GetAppDatabase()
                name = appdb.GetNameForMimeType(item.mimeType)
                if name != None:
                    appName = '_'.join(name.split(' '))
                    appDir = os.path.join(GetUserAppPath(), appName)
                    try:
                        os.chdir(appDir)
                    except:
                        log.warn("Couldn't Change dir to app directory")
                        return
                else:
                    self.gui.Notify("You have no client for this Shared Application.", "Notification")
                    
            if isWindows():
                if command.find("%1") != -1:
                    command = command.replace("%1", "")
            else:
                if command.find("%s") != -1:
                    command = command.replace("%s", "")

            command = command.replace("\"\"", "")
            
            if len(command) > 1:
                if command.find("%") == -1:
                    command = "\""+command+"\" \"%(appUrl)s\""
            else:
                command = "\""+command+"\""
                
        if verb != None:
            namedVars['appCmd'] = verb
        namedVars['appName'] = item.name.replace(" ", "_")
        namedVars['appDesc'] = item.description
        # This is NOT on every description type, so we're not using it yet
        # namedVars['appMimeType'] = item.mimeType
        namedVars['appUrl'] = item.uri
        namedVars['localFilePath'] = localFilePath
        namedVars['venueUrl'] = self.venueClient.GetVenue()
        
        # We're doing some icky munging to make our lives easier
        # We're only doing this for a single occurance of a windows
        # environment variable
        prog = re.compile("\%[a-zA-Z0-9\_]*\%")
        result = prog.match(command)

        if result != None:
            subStr = result.group()

            realCommand = command.replace(subStr,
                                          "DORKYREPLACEMENT") % namedVars
            realCommand = realCommand.replace("DORKYREPLACEMENT", subStr)
        else:
            try:
                realCommand = command % namedVars
            except:
                import pprint
                log.exception("Command failed, probably misconfigured. \
                Tried to run, %s with named arguments %s", command,
                              pprint.pformat(namedVars))
                return

        if isWindows():
            shell = os.environ['ComSpec']
            realCommand = "%s %s %s" % (shell, "/c", realCommand)
            
        aList = realCommand.split(' ')
        print "CMD: ", realCommand
        self.venueClient.StartProcess(aList[0], aList[1:])
       
    def SaveMyVenuesToFile(self):
        myVenuesFileH = open(self.myVenuesFile, 'w')
        cPickle.dump(self.myVenuesDict, myVenuesFileH)
        myVenuesFileH.close()

    def GetMyVenues(self):
        return self.myVenuesDict

    # end General Implementation
    #
    ###########################################################################################
