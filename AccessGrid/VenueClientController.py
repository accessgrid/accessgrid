#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueClientController.py
# Purpose:     This is the controller module for the venue client
#
# Author:      Thomas D. Uram
#
# Created:     2004/02/20
# RCS-ID:      $Id: VenueClientController.py,v 1.3 2004-02-25 15:47:54 turam Exp $
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
        """
        This method 

        **Arguments:**
        
        """
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
        """
        This method 

        **Arguments:**
        
        """
        self.gui = gui
        
    def SetVenueClient(self,venueClient):
        """
        This method 

        **Arguments:**
        
        """
        self.__venueClient = venueClient

    # end Controller Implementation
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Menu Callbacks

    def AddDataCB(self, fileList):
        """
        This method 

        **Arguments:**
        
        """
        # Upload if we have a file list
        if fileList:
            self.UploadVenueFiles(fileList)

    def AddServiceCB(self,serviceDescription):
        """
        This method 

        **Arguments:**
        
        """
        if serviceDescription:
            log.debug("Adding service: %s to venue" %serviceDescription.name)
            self.__venueClient.AddService(serviceDescription)
                    
    def SaveTextCB(self,filePath,text):
        '''
        Saves text from text chat to file.
        '''
        """
        This method 

        **Arguments:**
        
        """
        if filePath:
            # Save the text from chat in file.
            textFile = open(filePath, "w")
            textFile.write(text)
            textFile.close()
        
    def ModifyVenueRolesCB(self,rolesDict):
        """
        This method 

        **Arguments:**
        
        """
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
        """
        This method 

        **Arguments:**
        
        """
        #
        # If we are connected to a venue, exit the venue
        # Do this before terminating services, since we need
        # to message them to shut down their services first
        #
        if self.__venueClient.IsInVenue():
            self.__venueClient.ExitVenue()

        self.__venueClient.Shutdown()

        os._exit(0)  # this should not be necessary, replace if needed.



    #
    # Preferences Menu
    #
    
    def EditProfileCB(self,profile):
        """
        This method 

        **Arguments:**
        
        """
        if profile:
            self.ChangeProfile(profile)
        

    """
    ManageCertificates menu is provided by CertMgmt module
    """


    def UseMulticastCB(self):
        """
        This method 

        **Arguments:**
        
        """
        try:
            self.__venueClient.SetTransport("multicast")
            self.__venueClient.UpdateNodeService()
        except NetworkLocationNotFound, e:
            log.exception("VenueClientFrame.UseMulticast: EXCEPTION UPDATING NODE SERVICE")

    def UseUnicastCB(self,provider):
        """
        This method 

        **Arguments:**
        
        """

        oldProvider = self.__venueClient.GetProvider()
        oldTransport = self.__venueClient.GetTransport()

        # Set the transport in the venue client and update the node service
        self.__venueClient.SetProvider(provider)
        self.__venueClient.SetTransport("unicast")
        try:
            self.__venueClient.UpdateNodeService()
        except:
            # Reset the provider/transport 
            self.__venueClient.SetProvider(oldProvider)
            self.__venueClient.SetTransport(oldTransport)
            raise

    def EnableVideoCB(self,enableFlag):
        """
        This method 

        **Arguments:**
        
        """
        try:
            self.__venueClient.SetVideoEnabled(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling video", "Error enabling/disabling video")
            log.info("Couldn't enable/disable video")

    def EnableAudioCB(self,enableFlag):
        """
        This method 

        **Arguments:**
        
        """
        try:
            self.__venueClient.SetAudioEnabled(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling audio", "Error enabling/disabling audio")
            log.info("Couldn't enable/disable video")
    
    def SetNodeUrlCB(self,nodeUrl):
        """
        This method 

        **Arguments:**
        
        """
        if nodeUrl:
            self.__venueClient.SetNodeUrl(nodeUrl)

    
    # 
    # MyVenues Menu
    #
    
    def GoToDefaultVenueCB(self):
        """
        This method 

        **Arguments:**
        
        """
        venueUrl = self.__venueClient.GetProfile().homeVenue
        self.EnterVenueCB(venueUrl, 1)

    def SetAsDefaultVenueCB(self):
        """
        This method 

        **Arguments:**
        
        """
        # Get the current profile
        profile = self.__venueClient.GetProfile()

        # Update the home venue to the current venue url
        profile.homeVenue = self.__venueClient.GetVenue()

        # Store the changes
        self.ChangeProfile(profile)

    def AddToMyVenuesCB(self,name,url):
        """
        This method 

        **Arguments:**
        
        """
        self.myVenuesDict[name] = url
        self.SaveMyVenuesToFile(self.myVenuesFile)

                       
    def EditMyVenuesCB(self,myVenuesDict):
        """
        This method 

        **Arguments:**
        
        """
        if myVenuesDict:
            self.myVenuesDict = myVenuesDict
            self.SaveMyVenuesToFile(self.myVenuesFile)

    def GoToMenuAddressCB(self,venueUrl):
        """
        This method 

        **Arguments:**
        
        """
        self.EnterVenueCB(venueUrl,0)

    # Menu Callbacks
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Core UI Callbacks
    
    def GoBackCB(self):
        """
        This method 

        **Arguments:**
        
        """
        l = len(self.history)
        if(l>0):
            #
            # Go to last venue in the history list
            #
            uri = self.history[l - 1]
            self.EnterVenueCB(uri, 1)
    
    def EnterVenueCB(self,venueUrl,backFlag):
        """
        This method 

        **Arguments:**
        
        """
        self.__SetHistory(self.__venueClient.GetVenue(),backFlag)

        # Enter the venue
        self.__venueClient.EnterVenue(venueUrl)

    #
    # Participant Actions
    #
       
    def AddPersonalDataCB(self, fileList):
        """
        This method 

        **Arguments:**
        
        """
        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #

                
        if fileList:
            # upload!
            self.UploadPersonalFiles(fileList)

    def FollowCB(self, personToFollow):
        """
        This method 

        **Arguments:**
        
        """

        if(personToFollow != None and isinstance(personToFollow, ClientProfile)):
            url = personToFollow.venueClientURL
            name = personToFollow.name
            log.debug("VenueClientFrame.Follow: You are trying to follow :%s url:%s " %(name, url))

            if(self.__venueClient.leaderProfile == personToFollow):
                text = "You are already following "+name
                title = "Notification"
                self.gui.Notify(text, title)
            
            elif (self.__venueClient.pendingLeader == personToFollow):
                text = "You have already sent a request to follow "+name+". Please, wait for answer."
                title = "Notification"
                self.gui.Notify(text,title)

            else:
                try:
                    self.__venueClient.Follow(personToFollow)
                except:
                    log.exception("VenueClientFrame.Follow: Can not follow %s" %personToFollow.name)
                    text = "You can not follow "+name
                    title = "Notification"
                    self.gui.Notify(text, title)
                
    def UnFollowCB(self):
        """
        This method 

        **Arguments:**
        
        """

        log.debug("VenueClientFrame.Unfollow: In UnFollow we are being lead by %s" %self.__venueClient.leaderProfile.name)
        if self.__venueClient.leaderProfile != None :
           
            try:
              
                self.__venueClient.UnFollow(self.__venueClient.leaderProfile)
                self.meMenu.Remove(self.ID_ME_UNFOLLOW)
            except:
               
                log.exception("VenueClientFrame.Unfollow: Can not stop following %s" %self.__venueClient.leaderProfile.name)

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
        This method 

        **Arguments:**
        
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
    
    def SaveDataCB(self,data,path):
        """
        This method 

        **Arguments:**
        
        """
        self.SaveFile(data,path)

    def RemoveDataCB(self,itemList):
        """
        This method removes data in the specified list from the venue

        **Arguments:**
        
        *itemList* List of 
        
        """
        for item in itemList:
            if(item != None and isinstance(item, DataDescription)):
                text ="Are you sure you want to delete "+ item.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    self.__venueClient.RemoveData(item)

    def ModifyDataCB(self,dataDesc):
        """
        This method modifies the specified data in the venue

        **Arguments:**
        
        *dataDesc* DataDescription of the data to modify
        
        """
        self.__venueClient.ModifyData(dataDesc)


    #
    # Service Actions
    #
    
    """
    AddService is up above in menu callbacks
    """

    def OpenServiceCB(self,serviceDesc):
        """
        This method opens the specified service

        **Arguments:**
        
        *serviceDesc* ServiceDescription of the service to open
        
        """
        if(serviceDesc != None and isinstance(serviceDesc, ServiceDescription)):
            self.__venueClient.OpenService( serviceDesc )
    
    def RemoveServiceCB(self,itemList):
        """
        This method removes services in the specified list from the venue

        **Arguments:**
        
        *itemList* List of ServiceDescriptions to remove
        
        """
        for item in itemList:
            if(item != None and isinstance(item, ServiceDescription)):
                text ="Are you sure you want to delete "+ item.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    self.__venueClient.RemoveService(item)

    def UpdateServiceCB(self,serviceDesc):
        """
        This method updates the specified service

        **Arguments:**
        
        *serviceDesc* ServiceDescription of the service to update
        
        """
        self.__venueClient.UpdateService(serviceDesc)

    #
    # Application Actions
    #
    
    def OpenApplicationCB(self, appDesc):
        """
        This method opens the specified application

        **Arguments:**
        
        *appDesc* ApplicationDescription of the app to open
        
        """
        if appDesc != None and isinstance(appDesc, ApplicationDescription):
            self.RunApp(appDesc)

    def RemoveApplicationCB(self,appList):
        """
        This method removes applications in the specified list from the venue

        **Arguments:**
        
        *appList* List of ApplicationDescriptions to remove from venue
        
        """
        for app in appList:
            if(app != None and isinstance(app, ApplicationDescription)):
                text ="Are you sure you want to delete "+ app.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    self.__venueClient.DestroyApplication( app.id )
            

    def StartApplicationCB(self, name, appDesc):
        """
        Start the specified application.  This method creates the application
        in the venue.

        **Arguments:**
        
        *name* User-specified name of the application to start
        *app* ApplicationDescription of the application we want to start
        """
        log.debug("VenueClientFrame.StartApp: Creating application: %s" % app.name)

        appName = appDesc.name + ' - ' + name
        self.__venueClient.CreateApplication( appName,
                                            appDesc.description,
                                            app.mimeType )
              
    def RunApplicationCB(self, appDesc, cmd='Open'):
        """
        This method runs the specified application

        **Arguments:**
        
        *appDesc* ApplicationDescription of app to run
        *cmd* Command to execute on the app
        
        """
        appdb = Toolkit.GetApplication().GetAppDatabase()
        
        cmdline = appdb.GetCommandLine(appDesc.mimeType, cmd)

        self.StartCmd(cmdline, appDesc, verb=cmd)
        
    def UpdateApplicationCB(self,appDesc):
        """
        This method updates the application description for the specified application

        **Arguments:**
        
        *appDesc* ApplicationDescription of the app to update
        
        """
        self.__venueClient.UpdateApplication(appDesc)
        

    #
    # Application Integration code
    #
    def JoinApp(self,appDesc):
        """
        Join the specified application

        **Arguments:**
        
        *appDesc* The ApplicationDescription of the application we want to join
        """
        log.debug("Joining application: %s / %s" % (appDesc.name, appDesc.mimeType))
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commands = appdb.GetCommandNames(appDesc.mimeType)

        if commands == None:
            message = "No client registered for the selected application\n(mime type = %s)" % appDesc.mimeType
            self.gui.Prompt(message,message )
            log.debug(message)
        else:
            if 'Open' in commands:
                cmdLine = appdb.GetCommandLine(appDesc.mimeType, 'Open')
                log.debug("executing cmd: %s" % cmdLine)
                pid = wxExecute(cmdLine)
                
    def GetMimeCommandNames(self,mimeType):
        """
        This method returns mime command names for the given mime type

        **Arguments:**
        
        *mimeType* A mime type
        
        """
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commands = appdb.GetCommandNames(mimeType = mimeType)
        return commands
        
    def GetMimeCommandLine(self,mimeType,command):
        """
        This method returns the command line associated with the
        given mime type and command

        **Arguments:**
        
        *mimeType* Mime type for which to retrieve the command line
        *command* Related command
        
        """
        appdb = Toolkit.GetApplication().GetAppDatabase()
        commandLine = appdb.GetCommandLine(mimeType,command)        
        return commandLine
    #
    # Text Actions
    #
                
    def SendTextCB(self,text):
        self.__venueClient.SendText(text)

    # end Core UI Callbacks
    #
    ###########################################################################################

    ###########################################################################################
    #
    # General Implementation

    def UploadVenueFiles(self, fileList):
        """
        Upload the given files to the venue.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers and to allow for live updates of a download status.

        **Arguments:**
        
        *fileList* The list of files to upload
        
        """
        log.debug("In VenueClientController.UploadVenueFiles")
        log.debug("  fileList = %s" % str(fileList))
        
        filesToAdd = []
        
        # Check if data is already added
        for file in fileList:
            pathParts = os.path.split(file)
            name = pathParts[-1]
            fileExists = 0
                                
            dataDescriptions = self.__venueClient.GetVenueDataDescriptions()
            for data in dataDescriptions:
                if data.name == name:
                    fileExists = 1
                    break
                    
            if fileExists:
                # file exists; prompt for replacement
                title = "Duplicated File"
                info = "A file named %s is already added, do you want to overwrite?" % name
                if self.gui.Prompt(info,title):
                    self.__venueClient.RemoveData(data)
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


        url = self.__venueClient.GetDataStoreUploadUrl()
        method = self.get_ident_and_upload
        ul_args = (url, filesToAdd, progressCB)

        log.debug("Have args, creating thread, url: %s, files: %s", url, filesToAdd)

        upload_thread = threading.Thread(target = method, args = ul_args)

        upload_thread.start()
        log.debug("Started thread")

        #
        # Dialog dlg will get cleaned up at the end of get_ident_and_upload.
        #



    def get_ident_and_upload(self, uploadUrl, fileList, progressCB):
        """
        This method uploads the specified files to the given upload destination

        **Arguments:**
        
        *uploadUrl* URL to upload destination
        *fileList* List of files to upload
        *progressCB* A callable that will be called periodically for progress updates
                     (see the DataStore module for the method signature)
        
        """
        log.debug("Upload: getting identity")

        error_msg = None
        try:
            if uploadUrl.startswith("https:"):
                log.debug("Url starts with https:")
                DataStore.GSIHTTPUploadFiles(uploadUrl, fileList, progressCB)
            else:
                my_identity = self.__venueClient.GetDefaultIdentityDN()
                log.debug("Got identity %s" % my_identity)
                DataStore.HTTPUploadFiles(my_identity, uploadUrl,
                fileList, progressCB)

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
        
        # Save the profile locally
        self.__venueClient.SaveProfile()

        # Update client profile in venue
        if(self.__venueClient.venueUri != None):
            log.debug("Update client profile in venue")

            try:
                self.__venueClient.UpdateClientProfile(profile)
            except:
                log.exception("bin.VenueClient::ChangeProfile: Error occured when trying to update profile")
                # User does not need to know about this. The profile info got saved locally anyhow.                
                #self.gui.Error("Your profile could not be changed", "Change Profile Error")
        else:
            log.debug("Can not update client profile in venue - not connected")




    def AuthorizeLeadDialog(self, clientProfile):
        """
        This method is used to prompt the user to authorize a
        request to lead another user

        **Arguments:**
        
        *clientProfile* Profile of the user requesting to be led
        
        """
        idPending = None
        idLeading = None

        if(self.__venueClient.pendingLeader!=None):
            idPending = self.__venueClient.pendingLeader.publicId
          

        if(self.__venueClient.leaderProfile!=None):
            idLeading = self.__venueClient.leaderProfile.publicId
          
          
        if(clientProfile.publicId != idPending and clientProfile.publicId != idLeading):
            text = "Do you want "+clientProfile.name+" to follow you?"
            title = "Authorize follow"
            response = self.gui.Prompt(text, title)
            self.__venueClient.SendLeadResponse(clientProfile, response)

            dlg.Destroy()

        else:
            self.__venueClient.SendLeadResponse(clientProfile, 0)


    def SaveFile(self, dataDescription, localPathname):
        """
        Save a file from the datastore into a local file.

        We assume that the caller has assured the user that if the
        user has picked a file that already exists, that it will be
        overwritten.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers, to allow for live updates of a download status,
        and to perhaps allow multiple simultaneous transfers.

        **Arguments:**
        
        *dataDescription* DataDescription of the file to save
        *localPathname* Path to destination file
        
        """
        log.debug("Save file descriptor: %s, path: %s"
                  % (dataDescription, localPathname))


        failure_reason = None
        try:
            #
            # Retrieve details from the descriptor
            #
            size = dataDescription.size
            checksum = dataDescription.checksum
            url = dataDescription.uri

            #
            # Make sure this data item is valid
            #
            log.debug("data descriptor is %s" %dataDescription.__class__)

            if dataDescription.status != DataDescription.STATUS_PRESENT:
                self.gui.Notify("File %s is not downloadable - it has status %s"
                              % (dataDescription.name,
                                 dataDescription.status), "Notification")
                return
                
            log.debug("Downloading: size=%s checksum=%s url=%s"
                      % (size, checksum, url))


            self.gui.OpenSaveFileDialog(localPathname, size)

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
            dl_args = (url, localPathname, size, checksum, progressCB)
                
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
            self.gui.Notify(failure_reason, "Download error")


    def SaveFileNoProgress(self, dataDescription, localPathname):
        """
        Save a file from the datastore into a local file.

        We assume that the caller has assured the user that if the
        user has picked a file that already exists, that it will be
        overwritten.

        This implementation fires up a separate thread for the actual
        transfer. We want to do this to keep the application live for possible
        long-term transfers, to allow for live updates of a download status,
        and to perhaps allow multiple simultaneous transfers.

        **Arguments:**
        
        *dataDescription* DataDescription of the file to save
        *localPathname* Path to destination file
        
        """
        log.debug("Save file descriptor: %s, path: %s"%(dataDescription, localPathname))

        failure_reason = None
        try:
            #
            # Retrieve details from the descriptor
            #
            size = dataDescription.size
            checksum = dataDescription.checksum
            url = dataDescription.uri

            #
            # Make sure this data item is valid
            #
            log.debug("data descriptor is %s" %dataDescription.__class__)

            if dataDescription.status != DataDescription.STATUS_PRESENT:
                self.gui.Notify("File %s is not downloadable - it has status %s"
                              % (dataDescription.name,
                                 dataDescription.status), "Notification")
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
            dl_args = (url, localPathname, size, checksum,
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
            self.gui.Notify(failure_reason, "Download error")

    def get_ident_and_download(self, url, local_pathname, size, checksum, progressCB):
        """
        This method 

        **Arguments:**
        
        *url* The url of the file to download
        *local_pathname* The path to the destination file
        *size* The size of the file
        *checksum* File checksum
        *progressCB* A callable that will be called periodically for progress updates
                     (see the DataStore module for the method signature)
        
        """
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
        This method uploads the given personal files to the venue.

        **Arguments:**
        
        *fileList* The list of files to upload
        
        """
        log.debug("Upload personal files")

        for file in fileList:

            # Check if data is already added
            pathParts = os.path.split(file)
            index = len(pathParts)-1
            name = pathParts[index]

            dataDescriptions = self.__venueClient.GetDataDescriptions()
            for data in dataDescriptions:
                if data.name == name:
                    title = "Duplicated File"
                    info = "A file named %s is already added, do you want to overwrite?" % name
                    # Overwrite?
                    if self.gui.Prompt( info, title ):
                        self.__venueClient.dataStore.RemoveFiles([data])
                        
                        # The data description have to be removed, else the size parameter will
                        # not match and open will fail for modified data.
                        self.__venueClient.SendEvent(Events.RemoveDataEvent(self.__venueClient.GetEventChannelId(), data))
                        
                    else:
                        return
                                         
            try:
                my_identity = self.app.GetDefaultIdentityDN()
                self.__venueClient.dataStore.UploadLocalFiles([file], my_identity, self.__venueClient.GetProfile().publicId)

                # Send an event alerting about new data (only if it is new)
                #if newData: 
                dataDescription = self.__venueClient.dataStore.GetDescription(name)
                self.__venueClient.SendEvent(Events.AddDataEvent(self.__venueClient.GetEventChannelId(), 
                                                               dataDescription))
            except DataStore.DuplicateFile, e:
                title = "Duplicated File"
                info = "This file %s is already added. Rename your file and add it again." %e
                self.gui.Notify(info, title)
                                                     
            except Exception, e:
                log.exception("bin.VenueClient:UploadPersonalFiles failed")
                title = "Add Personal Data Error"
                text = "The file could not be added, error occured."
                self.gui.Error(text, title)
                
    def UploadFilesNoDialog(self, fileList):
        """
        This method uploads the given files to the venue.
        This uses the DataStore HTTP upload engine code.

        **Arguments:**
        
        *fileList*  The list of files to upload
        
        """

        uploadUrl = self.__venueClient.GetDataStoreUploadUrl
        log.debug("Upload files - no dialog. uploadUrl=%s", uploadUrl)

        error_msg = None
        try:
            if uploadUrl.startswith("https:"):
                DataStore.GSIHTTPUploadFiles(uploadUrl, fileList)
            else:
                my_identity = self.app.GetDefaultIdentityDN()
                DataStore.HTTPUploadFiles(my_identity, uploadUrl, fileList)
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
        This method builds up the command line given a command-line
        specification, and executes it

        **Arguments:**
        
        *command*
        *item*
        *namedVars*
        *verb*
        
        
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
        namedVars['venueUrl'] = self.__venueClient.GetVenue()
        
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
        self.__venueClient.StartProcess(aList[0], aList[1:])
       
    def SaveMyVenuesToFile(self,myVenuesFile):
        """
        This method synchs the saved venues list to disk
        """
        myVenuesFileH = open(myVenuesFile, 'w')
        cPickle.dump(self.myVenuesDict, myVenuesFileH)
        myVenuesFileH.close()

    def GetMyVenues(self):
        """
        This method returns the user's saved venues list
        """
        return self.myVenuesDict

    # end General Implementation
    #
    ###########################################################################################
