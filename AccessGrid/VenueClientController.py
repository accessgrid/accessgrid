#-----------------------------------------------------------------------------
# Name:        VenueClientController.py
# Purpose:     This is the controller module for the venue client
# Created:     2004/02/20
# RCS-ID:      $Id: VenueClientController.py,v 1.31 2004-06-02 03:06:21 turam Exp $
# Copyright:   (c) 2002-2004
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------

__revision__ = "$Id: VenueClientController.py,v 1.31 2004-06-02 03:06:21 turam Exp $"
__docformat__ = "restructuredtext en"

# standard imports
import cPickle
import os
import re
import threading
import time

# Access Grid imports
from AccessGrid.Toolkit import Application
from AccessGrid import Log
from AccessGrid import DataStore
from AccessGrid.AppDb import AppDb
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Descriptions import ServiceDescription, DataDescription
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.NetworkLocation import ProviderProfile
from AccessGrid.Platform.Config import UserConfig, MimeConfig, AGTkConfig
from AccessGrid.Platform import IsWindows, Config
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.VenueClient import NetworkLocationNotFound
from AccessGrid import Events


log = Log.GetLogger(Log.VenueClientController)

class NotAuthorizedError(Exception):
    pass

class VenueClientController:

    def __init__(self):
    
        self.history = []
        
        # Initiate venue client app
        self.__venueClientApp = VenueClientApp()

        # Create Process Manager
        self.processManager = ProcessManager()
        self.appProcessManager = ProcessManager()
        


    ##########################################################################
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
    ##########################################################################

    ##########################################################################
    #
    # Menu Callbacks

    def AddDataCB(self, fileList):
        """
        This method 

        **Arguments:**
        
        """
        # Upload if we have a file list
        if not fileList or not isinstance(fileList,list):
            raise ValueError
            
        self.UploadVenueFiles(fileList)

    def AddServiceCB(self,serviceDescription):
        """
        This method 

        **Arguments:**
        
        """
        if not serviceDescription or not isinstance(serviceDescription,ServiceDescription):
            raise ValueError
            
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
        if not filePath:
            raise ValueError
            
        if not text:
            raise ValueError
            
        # Save the text from chat in file.
        textFile = open(filePath, "w")
        textFile.write(text)
        textFile.close()
        
    def ModifyVenueRolesCB(self,rolesDict):
        """
        This method 

        **Arguments:**
        
        *rolesDict* Dictionary of roles
        
        """
        
        if not rolesDict:
            raise ValueError

        try:
            # Set new role configuration
            RoleClient(self.__venueClient.GetVenue()).SetVenueRoles(rolesDict)

        except Exception, e:
#             if isinstance(e, faultType) and str(e.faultstring) == "NotAuthorized":
#                 raise NotAuthorizedError
            raise

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
        if not profile or not isinstance(profile,ClientProfile):
            raise ValueError

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
        except NetworkLocationNotFound:
            log.exception("Multicast streams not found")
            raise

    def UseUnicastCB(self,provider):
        """
        This method 

        **Arguments:**
        
        """
        
        if not provider or not isinstance(provider,ProviderProfile):
            raise ValueError

        oldProvider = self.__venueClient.GetProvider()
        oldTransport = self.__venueClient.GetTransport()

        # Set the transport in the venue client and update the node service
        self.__venueClient.SetProvider(provider)
        self.__venueClient.SetTransport("unicast")
        try:
            self.__venueClient.UpdateNodeService()
        except:
            log.exception("Error switching to unicast")
        
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
            log.exception("Couldn't enable/disable video")

    def EnableAudioCB(self,enableFlag):
        """
        This method 

        **Arguments:**
        
        """
        try:
            self.__venueClient.SetAudioEnabled(enableFlag)
        except:
            log.exception("Couldn't enable/disable video")
    
    def SetNodeUrlCB(self,nodeUrl):
        """
        This method 

        **Arguments:**
        
        """
        if not nodeUrl:
            raise ValueError
        
        self.__venueClient.SetNodeUrl(nodeUrl)

    
    # 
    # MyVenues Menu
    #
    
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
        
        if not name:
            raise ValueError("Invalid venue name")
            
        if not url:
            raise ValueError("Invalid venue url")

        try:
            self.__venueClientApp.AddToMyVenues(name,url)
        except:
            log.exception("Error adding venue (name=%s,url=%s)", name,url)
            raise

                       
    def EditMyVenuesCB(self,myVenuesDict):
        """
        This method 

        **Arguments:**
        
        """
        
        if myVenuesDict == None or not isinstance(myVenuesDict,dict):
            log.exception("Incorrect param to EditMyVenuesCB")
            raise ValueError
                
        try:
            self.__venueClientApp.SetMyVenues(myVenuesDict)
        except:
            log.exception("Error setting my venues")
            raise
            

    # Menu Callbacks
    #
    ##########################################################################

    ##########################################################################
    #
    # Core UI Callbacks
    
    def GoBackCB(self):
        """
        This method 

        **Arguments:**
        
        """
        uri = self.__venueClientApp.PopHistory()
        if not uri:
            raise Exception("Invalid venue url retrieved from history list; %s", uri)
            
        self.__venueClient.EnterVenue(uri)
    
    def EnterVenueCB(self,venueUrl):
        """
        This method 

        **Arguments:**
        
        """
        if not venueUrl:
            raise ValueError

        # Push your own venue url to the history list
        self.__venueClientApp.PushHistory(self.__venueClient.GetVenue())

        # Exit the venue you are currently in before entering a new venue
        if self.__venueClient.IsInVenue():
            self.__venueClient.ExitVenue()

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

        if not fileList or not isinstance(fileList,list):
            raise ValueError

        try:
            self.UploadPersonalFiles(fileList)
        except:
            log.exception("Error adding personal data")
            raise

    def FollowCB(self, personToFollow):
        """
        This method 

        **Arguments:**
        
        """
        
        if not personToFollow or not isinstance(personToFollow,ClientProfile):
            raise ValueError

        try:
            self.__venueClient.Follow(personToFollow)
        except:
            log.exception("VenueClientFrame.Follow: Can not follow %s" %personToFollow.name)
            raise
                
    def UnFollowCB(self):
        """
        This method 

        **Arguments:**
        
        """

        log.debug("VenueClientFrame.Unfollow: In UnFollow we are being lead by %s" %self.__venueClient.leaderProfile.name)
        if self.__venueClient.leaderProfile != None :
           
            try:
              
                self.__venueClient.UnFollow(self.__venueClient.leaderProfile)
            except:
               
                log.exception("VenueClientFrame.Unfollow: Can not stop following %s" %self.__venueClient.leaderProfile.name)

        else:
            log.debug("VenueClientFrame.Unfollow: You are trying to stop following somebody you are not following")
        


    #
    # Data Actions
    #

    """
    AddDataCB is up above in menu callbacks
    """

    def OpenDataCB(self,data):
        """
        This method 

        **Arguments:**
        
        """
        
        if not data or not isinstance(data,DataDescription):
            raise ValueError
       
        name = data.name
        commands = self.mimeConfig.GetMimeCommands(ext = name.split('.')[-1])
        if commands == None:
            message = "No client registered for the selected data"
            self.gui.Notify(message,"Open Data")
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
        if not data:
            raise ValueError("Invalid data argument")
        
        if not path:
            raise ValueError("Invalid path argument")
        
        self.SaveVenueData(data,path)

    def RemoveDataCB(self,data):
        """
        This method removes data in the specified list from the venue

        **Arguments:**
        
        *data* DataDescription of the file to remove 
        
        """
        
        if not data or not isinstance(data,DataDescription):
            raise ValueError
        
        self.__venueClient.RemoveData(data)


    def UpdateDataCB(self,data):
        """
        This method modifies the specified data in the venue

        **Arguments:**
        
        *dataDesc* DataDescription of the data to modify
        
        """
        
        if not data or not isinstance(data,DataDescription):
            raise ValueError
            
        self.__venueClient.UpdateData(data)


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
        if not serviceDesc or not isinstance(serviceDesc,ServiceDescription):
            raise ValueError
        
        self.__venueClient.OpenService( serviceDesc )
    
    def RemoveServiceCB(self,service):
        """
        This method removes services in the specified list from the venue

        **Arguments:**
        
        *itemList* List of ServiceDescriptions to remove
        
        """
        if not service or not isinstance(service,ServiceDescription):
            raise ValueError
            
        try:
            self.__venueClient.RemoveService(service)
        except:
            log.exception("Error removing service")
            raise

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
    
    def StartApplicationCB(self, name, appDesc):
        """
        Start the specified application.  This method creates the application
        in the venue.

        **Arguments:**
        
        *name* User-specified name of the application to start
        *app* ApplicationDescription of the application we want to start
        """
        
        if not name:
            raise ValueError("Invalid name argument")
            
        if not appDesc or not isinstance(appDesc,ApplicationDescription):
            raise ValueError("Invalid appDesc argument")
        
        log.debug("VenueClientFrame.StartApp: Creating application: %s" % appDesc.name)

        appName = appDesc.name + ' - ' + name
        try:
            self.__venueClient.CreateApplication( appName,
                                                appDesc.description,
                                                appDesc.mimeType )
        except:
            log.exception("Error starting application")
            raise
              
    def RemoveApplicationCB(self,appList):
        """
        This method removes applications in the specified list from the venue

        **Arguments:**
        
        *appList* List of ApplicationDescriptions to remove from venue
        
        """
        
        if not appList or not isinstance(appList,list):
            raise ValueError
            
        for app in appList:
            if(app != None and isinstance(app, ApplicationDescription)):
                text ="Are you sure you want to delete "+ app.name + "?"
                if self.gui.Prompt(text, "Confirmation"):
                    self.__venueClient.DestroyApplication( app.id )
            

    def UpdateApplicationCB(self,appDesc):
        """
        This method updates the application description for the specified application

        **Arguments:**
        
        *appDesc* ApplicationDescription of the app to update
        
        """
        
        if not appDesc or not isinstance(appDesc,ApplicationDescription):
            raise ValueError
            
        self.__venueClient.UpdateApplication(appDesc)
        
    #
    # Text Actions
    #
                
    def SendTextCB(self,text):
        self.__venueClient.SendText(text)

    # end Core UI Callbacks
    #
    ##########################################################################

    ##########################################################################
    #
    # General Implementation


    #
    # Profile
    #

    def ChangeProfile(self, profile):
        """
        This method changes this participants profile and saves the information to file.

        **Arguments:**
        
        *profile* The ClientProfile including the new profile information
        """
        
        # Save the profile locally
        self.__venueClient.SaveProfile()

        # Update client profile in venue
        if self.__venueClient.GetVenue() != None:
            log.debug("Update client profile in venue")

            try:
                self.__venueClient.UpdateClientProfile(profile)
            except:
                log.exception("bin.VenueClient::ChangeProfile: Error occured when trying to update profile")
                # User does not need to know about this. The profile info got saved locally anyhow.                
                #self.gui.Error("Your profile could not be changed", "Change Profile Error")
        else:
            log.debug("Can not update client profile in venue - not connected")

    #
    # Lead/Follow
    #

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

        else:
            self.__venueClient.SendLeadResponse(clientProfile, 0)




    # 
    # Venue Data Access
    #

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
        ul_args = (url, fileList, progressCB)

        log.debug("Have args, creating thread, url: %s, files: %s", url, fileList)

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
                my_identity = str(Application.instance().GetDefaultSubject())
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

    def SaveVenueData(self, dataDescription, localPathname):
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
                    self.gui.UpdateSaveFileDialog(dataDescription.name, progress,done)
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
                my_identity = str(Application.instance().GetDefaultSubject())
                DataStore.HTTPDownloadFile(my_identity, url, local_pathname, size,
                                           checksum, progressCB)
        except DataStore.DownloadFailed:
            log.exception("bin.VenueClient:get_ident_and_download: Got exception on download")
            self.gui.Notify("The file could not be downloaded", "Download Error")
                       
                                
    def UploadPersonalFiles(self, fileList):
        """
        This method uploads the given personal files to the venue.

        **Arguments:**
        
        *fileList* The list of files to upload
        
        """
        log.debug("Upload personal files")

        for filepath in fileList:

            # Check if data is already added
            pathParts = os.path.split(filepath)
            index = len(pathParts)-1
            name = pathParts[index]

            dataDescriptions = self.__venueClient.GetPersonalData()
            for data in dataDescriptions:
                if data.name == name:
                    title = "Duplicated File"
                    info = "A file named %s is already added, do you want to overwrite?" % name
                    # Overwrite?
                    if self.gui.Prompt( info, title ):
                        self.__venueClient.RemoveData(data)
                    else:
                        return
                                         
            try:
                my_identity = Application.instance().GetDefaultSubject()
                self.__venueClient.dataStore.UploadLocalFiles([filepath], my_identity.name, self.__venueClient.GetProfile().publicId)

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
                my_identity = str(Application.instance().GetDefaultSubject())
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
           

    #
    # (Mime) Command Processing
    #
    
    def GetCommands(self,objDesc):
        return self.__venueClientApp.GetCommands(objDesc)
        
        
    def StartCmd(self, objDesc, verb=None,cmd=None):
        """
        This method builds up the command line given a command-line
        specification, and executes it

        **Arguments:**
        
        *objDesc*
        *verb*
        """
        
        if objDesc == None:
            raise ValueError("objDesc must not be None")

        if verb == None and cmd == None:
            raise ValueError("Neither verb nor cmd specified")

        # Use either the incoming verb or command
        if verb:
            commandList = self.GetCommands(objDesc)
            command = commandList[verb]
        elif cmd:
            command = cmd

        localFilePath = None
        name = None
        appDir = None
        processManager = self.processManager

        # If objDesc is data, download the filename specified in it.
        if isinstance(objDesc, DataDescription):
            localFilePath = os.path.join(UserConfig.instance().GetTempDir(),
                                         objDesc.name.replace(" ", "_"))
            self.SaveFileNoProgress(objDesc, localFilePath)

            # Fix odd commands
            if IsWindows():
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
            command = command.strip()
            
            if len(command) > 1:
                if command.find("%") == -1:
                    command = command+" %(localFilePath)s"
            else:
                command = "\"%(localFilePath)s\""
            
        elif isinstance(objDesc, ServiceDescription):
            # Fix odd commands
            if IsWindows():
                if command.find("%1") != -1:
                    command = command.replace("%1", "")
                if command.find("%L") != -1:
                    command = command.replace("%L", "")
                if command.find("%*") != -1:
                    command = command.replace("%*", "")
            else:
                if command.find("%s") != -1:
                    command = command.replace("%s", "")

            command = command.strip()
            
            if len(command) > 1:
                if command.find("%") == -1:
                    command = command+" %(appUrl)s"
            else:
                command = "\"%(appUrl)s\""
            
        else:
            # Get the app dir and go there
            if isinstance(objDesc, ApplicationDescription):
                name = self.__venueClientApp.GetNameForMimeType(objDesc.mimeType)
                if name != None:
                    appName = '_'.join(name.split(' '))
                    
                    # Get the app dir
                    if os.access(os.path.join(UserConfig.instance().GetSharedAppDir(), appName),os.R_OK):
                        appDir = os.path.join(UserConfig.instance().GetSharedAppDir(), appName)
                    elif os.path.join(AGTkConfig.instance().GetSharedAppDir(), appName):
                        appDir = os.path.join(AGTkConfig.instance().GetSharedAppDir(), appName)
                    else:
                        raise Exception, "Couldn't find shared app client"
                        
                    try:
                        os.chdir(appDir)
                    except:
                        log.warn("Couldn't Change dir to app directory")
                        return
                        
                    processManager = self.appProcessManager
                else:
                    self.gui.Notify("You have no client for this Shared Application.", "Notification")
                    return
                    
            if IsWindows():
                if command.find("%1") != -1:
                    command = command.replace("%1", "")
            else:
                if command.find("%s") != -1:
                    command = command.replace("%s", "")

            command = command.replace("\"\"", "")
            command = command.strip()
            
            if len(command) > 1:
                if command.find("%") == -1:
                    #command = "\""+command+"\" \"%(appUrl)s\""
                    command = command+" %(appUrl)s"
            else:
                command = "\""+command+"\""

        #
        # Build up named vars
        #
        namedVars = dict()
        if verb != None:
            namedVars['appCmd'] = verb
        namedVars['appName'] = objDesc.name.replace(" ", "_")
        namedVars['appDesc'] = objDesc.description
        # This is NOT on every description type, so we're not using it yet
        # namedVars['appMimeType'] = objDesc.mimeType
        namedVars['appUrl'] = objDesc.uri
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

        if IsWindows():
            #shell = os.environ['ComSpec']
            #realCommand = "%s %s %s" % (shell, "/c", realCommand)
            log.info("StartCmd starting command: %s", realCommand)
            cmd = realCommand
            argList = []
        else:
            log.info("StartCmd starting command: %s", realCommand)
            aList = realCommand.split(' ')
            cmd = aList[0]
            argList = aList[1:]
        
        processManager.StartProcess(cmd,argList)
        
    def StopApplications(self):
        self.appProcessManager.TerminateAllProcesses()

    #
    # Other
    #

    def GetInstalledApps(self):
        return self.__venueClientApp.GetInstalledApps()
        
    def GetMyVenues(self):
        return self.__venueClientApp.GetMyVenues()
        

    # end General Implementation
    #
    ##########################################################################



class VenueClientApp:
    """
    The VenueClientApp class embodies all of the user-level application
    data and access to it
    """

    def __init__(self):
        # MyVenues
        self.myVenuesDict = dict()
        self.userConf = UserConfig.instance()
        self.myVenuesFile = os.path.join(self.userConf.GetConfigDir(),
                                         "myVenues.txt" )
        self.__LoadMyVenues()
        
        # Venue History
        self.history = []
        
        # Application Databases
        self.userAppDatabase = AppDb(path=UserConfig.instance().GetConfigDir())
        self.systemAppDatabase = AppDb(path=AGTkConfig.instance().GetConfigDir())
        # Mime Config
        self.mimeConfig = Config.MimeConfig.instance()
        
    #
    # MyVenues Methods
    #
    
    def __SaveMyVenuesToFile(self):
        """
        This method synchs the saved venues list to disk
        """
        if os.path.exists(self.myVenuesFile):
            myVenuesFileH = open(self.myVenuesFile, 'w')
        else:
            myVenuesFileH = open(self.myVenuesFile, 'aw')
        
        myVenuesFileH = open(self.myVenuesFile, 'aw')
        cPickle.dump(self.myVenuesDict, myVenuesFileH)
        myVenuesFileH.close()
        
    def __LoadMyVenues(self):
        """
        This method 

        **Arguments:**
        
        """
        if os.path.exists(self.myVenuesFile):
            try:
                myVenuesFileH = open(self.myVenuesFile, 'r')
            except:
                myVenuesFileH = None
                log.exception("Failed to load MyVenues file")
            else:
                self.myVenuesDict = cPickle.load(myVenuesFileH)
                myVenuesFileH.close()
        else:
            log.debug("There is no personal venues file to load.")

    def AddToMyVenues(self,name,url):
        self.myVenuesDict[name] = url
        self.__SaveMyVenuesToFile()
    
    def SetMyVenues(self,myVenuesDict):
        """
        This method sets the user's saved venues list
        """
        self.myVenuesDict = myVenuesDict
        self.__SaveMyVenuesToFile()

    def GetMyVenues(self):
        """
        This method returns the user's saved venues list
        """
        return self.myVenuesDict
        
    #
    # Applications Methods
    # 
    
    def GetInstalledApps(self):
        adm = dict()

        for app in self.userAppDatabase.ListAppsAsAppDescriptions():
            adm[app.GetName()] = app
            
        for app in self.systemAppDatabase.ListAppsAsAppDescriptions():
            if not adm.has_key(app.GetName()):
                adm[app.GetName()] = app
                
        return adm.values()
        
        
    #
    # (Application/Mime) Command Methods
    #
    def GetCommands(self,objDesc):
        commandList = None
        if isinstance(objDesc,ServiceDescription):
            # Data and Service commands are retrieved from the mime db
            list = objDesc.name.split('.')
            ext = ""
            if len(list) == 2:
                ext = list[1]
            commandList = self.mimeConfig.GetMimeCommands(
                                        mimeType = objDesc.mimeType,
                                        ext = ext)
        elif isinstance(objDesc,DataDescription):
            # Data and Service commands are retrieved from the mime db
            list = objDesc.name.split('.')
            ext = ""
            if len(list) == 2:
                ext = list[1]
            commandList = self.mimeConfig.GetMimeCommands(ext = ext)
        elif isinstance(objDesc,ApplicationDescription):
            # Application commands are retrieved from the app db
            commandList = dict()
            commandList.update(self.userAppDatabase.GetCommands(objDesc.mimeType))
            commandList.update(self.systemAppDatabase.GetCommands(objDesc.mimeType))
            
        return commandList

    def GetNameForMimeType(self,mimeType):
        """
        Get the name for the given mime type
        """
        
        # Check the user app db first, the system app db second
        name = self.userAppDatabase.GetNameForMimeType(mimeType)
        if not name:
            name = self.systemAppDatabase.GetNameForMimeType(mimeType)
        return name
    
    #
    # Venue History methods
    #
    
    def PushHistory(self,uri):
        # Add the url to the history list if
        # - the history list is empty, or
        # - the url is not the same as the last entry added
        if(len(self.history) == 0 or self.history[-1] != uri):
            self.history.append(uri)
            
    def PopHistory(self):
        uri = None
        if(len(self.history)>0):
            # Get last venue in the history list
            uri = self.history[-1]
            del self.history[-1]
        return uri

