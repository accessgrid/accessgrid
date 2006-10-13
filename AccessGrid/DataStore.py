#-----------------------------------------------------------------------------
# Name:        DataStore.py
# Purpose:     This is a data storage server.
# Created:     2002/12/12
# RCS-ID:      $Id: DataStore.py,v 1.101 2006-10-13 21:43:50 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: DataStore.py,v 1.101 2006-10-13 21:43:50 turam Exp $"

import os
import time
import threading
import re
import string
import md5
import ConfigParser
import stat
import urlparse
import urllib

from AccessGrid import Log
import AccessGrid.GUID
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.Descriptions import DataDescription, DirectoryDescription, FileDescription, DataDescription3
from AccessGrid.Events import Event
from AccessGrid import FTPSClient,FTPSServer

log = Log.GetLogger(Log.DataStore)

class NotAPlainFile(Exception):
    pass

class DuplicateFile(Exception):
    pass

class FileNotFound(Exception):
    pass

class LegacyCallInvalid(Exception):
    pass

class LegacyCallOnDir(Exception):
    pass

class NotAuthorized(Exception):
    pass

class UploadFailed(Exception):
    pass

class DownloadFailed(Exception):
    pass

class DataAlreadyPresent(Exception):
    pass

class DataNotFound(Exception):
    pass

class DirectoryNotFound(Exception):
    pass

class UserCancelled(Exception):
    pass

class DataDescriptionContainer:
    
    """
    A DataDescriptionContainer includes all DataDescription representations of
    data in the DataStore. The DataStore calls this class to manage the Descriptions.
    """

    def __init__(self):
        self.channelId = None 
        self.data = dict()
       
    def AddData(self, dataDescription):
        """
        Replace the current description for dataDescription.name with
        this one.

        **Arguments:**
            *dataDescription* A real data description.
            
        **Raises:**
            *DataAlreadyPresent* Raised when the data is not found in the Venue.

        """
        name = dataDescription.name
        log.debug("DataDescriptionContainer::AddData with name %s " %name)
             
        if self.data.has_key(dataDescription.id):
            log.exception("DataDescriptionContainer::AddData: data already present: %s", name)
            raise DataAlreadyPresent

        self.data[dataDescription.id] = dataDescription

    def UpdateData(self, dataDescription):
        """
        **Arguments:**
            *dataDescription* DataDescription to update
            
        **Raises:**
            *DataNotFound* Raised when the data is not found in the Venue.
        """

        name = dataDescription.name

        if not self.data.has_key(dataDescription.id):
            log.exception("UpdateData: data not already present: %s", name)
            raise DataNotFound

        self.data[dataDescription.id] = dataDescription

    def GetDataFromId(self, id):
        if self.data.has_key(id):
            return self.data[id]
        else:
            return None
        
    
    def GetData(self, fileName):
        """
        GetData retreives the DataDescription associated with fileName.
        
        **Arguments:**
            *fileName* The name of the data to be retrieved.
        
        **Returns:**
            *dataDescription* A data description that corresponds
            to the name passed in.
        
            *None* When the data is not found
        
        """
        desc = None

        for dataDesc in self.data.values():
            if dataDesc.name == fileName:
                desc = dataDesc

        return desc
    
    
    def RemoveData(self, dataDescription):
        """
        RemoveData removes a DataDescription 

        **Arguments:**
            *dataDescription* A data description.

        **Raises:**
            *DataNotFound* Raised when the data is not found.
        """
        if self.data.has_key(dataDescription.id):
            del self.data[ dataDescription.id ]
            
        else:
            log.exception("DataDescriptionContainer::RemoveData: Data not found.")
            raise DataNotFound
        
    def AsINIBlock(self):
        """
        AsINIBlock serializes the data as an INI formatted
        block of text.

        **Returns**
        *iniblock* string of serialized data. If no data is present,
        
        """

        string = ""
        string +="".join(map(lambda data: data.AsINIBlock(), self.GetDataDescriptions()))
        return string
    
    def LoadPersistentData(self, dataList):
        '''
        Adds a list of DataDescriptions without distributing events

        **Arguments**
        *dataList* List of DataDescriptions you want to add
        '''
      
        for description in dataList:
            self.data[description.id] = description
           
    def GetDataDescriptions(self):
        """
        This methods returns a list containing all present DataDescriptions.

        **Returns**
            *data* A list of DataDescription
        
        """
        dList = []
       
        for data in self.data.values():
            dList.append(data)

        return dList

      

class DataStore:
    """
    A DataStore implements a per-venue data storage server.
    Obsolete! Not used anymore.
    """
    
    #Modified by NA2-HPCE
    def __init__(self, callbackClass, pathname, prefix, transferEngine):
        """
        Create the datastore.

        Files will be stored in the directory named by <pathname>.
        The URL prefix for this data store is <prefix>.

        """
        self.callbackClass = callbackClass
        self.pathname = pathname
        self.path = pathname
        self.prefix = prefix
        log.debug("__init__: Datastore path is %s ", self.path)
        self.transfer_engine = transferEngine
        #self.transfer_engine.RegisterPrefix(prefix,self)

        self.cbLock = threading.Lock()
        self.transferEngineLock = threading.Lock()
        #self.dataDescContainer = DataDescriptionContainer()
        #self.curDDC = self.dataDescContainer
        #self.curDD = None
        self.descriptionDict = dict()

        #data storage root object
        self.root = DirectoryDescription("Root")
        self.root.SetLevel(0)
        self.root.description ="Root node of data storage"
        self.root.SetObjectType(DataDescription3.TYPE_DIR)
        self.root.SetLocation("")
        
        self.__CheckPath()
        self.persistenceFileName = os.path.join(self.path, "DataStore.dat")
        self.descriptionDict = dict()
        self.LoadPersistentInfo()
        
        

    def __CheckPath(self):
        if self.path == None or not os.path.exists(self.path):
            log.exception("DataStore::init: Datastore path %s does not exist" % (self.path))
            try:
                os.mkdir(self.path)
            except OSError:
                log.exception("Could not create Data Service.")
                self.path = None
       
    def LoadPersistentInfo(self, pParent=None):
# FIXME: not using metadata yet
#         cp = ConfigParser.ConfigParser()
#         cp.read(self.persistenceFileName)
# 
        log.debug ("=================== ENTERED LoadPersistentInfo ==================")
        log.debug("Reading persisted data from: %s", self.persistenceFileName)
        persistentData = []
        dd = None
        
        if pParent==None:
            log.debug("Loading a directory in root-dir!")
            parent = self.root
            level = 0
            parentID = "-1"
        else:
            log.debug("Loading a directory in subtree!")
            parent = pParent
            level = parent.GetLevel()+1
            parentID = parent.GetId()
        
        log.debug("LoadPersistentInfo: Server Path: %s", self.path)
        serverPath = self.path + os.path.sep +  parent.GetLocation()   
        #serverPath = self.path + os.path.sep + parent.GetLocation()
            
        log.debug("Getting file list of %s ", os.curdir +"/"+ serverPath)
        
        
        if not os.path.exists(serverPath):
            log.debug("Directory doesn't exist on server!")
            raise DirectoryNotFound
        
        searchPath = os.path.abspath(serverPath)
        
        files = os.listdir(searchPath)
        log.debug("LOADPERSISTENTINFO: Path to use is %s", searchPath)
        if 'DataStore.dat' in files:
            files.remove('DataStore.dat')
        for f in files:   
            if os.path.isfile(searchPath+ os.path.sep+f):
                log.debug("Found file %s !", f)
                dd = DataDescription3(f)
                dd.SetId(str(AccessGrid.GUID.GUID()))
                dd.SetObjectType(DataDescription3.TYPE_FILE)
                dd.SetLevel(-2)
                dd.SetParentId(parentID)
                log.debug("LoadPersistentInfo: Adding file %s to location %s", f, parent.GetLocation())
            elif os.path.isdir(searchPath+ os.path.sep+f):
                log.debug("Found directory %s !" , f)
                dd = DirectoryDescription(f)
                dd.SetId(str(AccessGrid.GUID.GUID()))
                dd.SetObjectType(DataDescription3.TYPE_DIR)
                dd.SetLevel(level)
                dd.SetParentId(parentID)
                if parent.GetLocation() == "":
                    dd.SetLocation(f)
                    log.debug("LoadPersistentInfo: Location of dir %s is %s", f, f)
                else:
                    dd.SetLocation(parent.GetLocation() + os.path.sep + f)
                    log.debug("LoadPersistentInfo: Location of dir %s is %s", f, parent.GetLocation() + os.path.sep + f)
                self.LoadPersistentInfo(dd)
            else:
                log.debug("Type of data not determined for object named %s!", f)
                return
                
                
#             try:
#                 dd.SetDescription(cp.get(sec, 'description'))
#             except ConfigParser.NoOptionError:
#                 log.info("LoadPersistentVenues: Data has no description")
            dd.SetStatus(DataDescription3.STATUS_PRESENT)
            stat = os.stat(os.path.join(serverPath,f))
            dd.SetSize(stat.st_size)
#             dd.SetChecksum(cp.get(sec, 'checksum'))
#             dd.SetOwner(cp.get(sec, 'owner'))
#             dd.SetType(cp.get(sec, 'type'))
# 
#             try:
#                 dd.SetLastModified(cp.get(sec, 'lastModified'))
#             except:
#                 log.info("LoadPersistentVenues: Data has no last modified date. Probably old DataDescription")
            
            path=urlparse.urlparse(serverPath)
                        
            if dd.GetObjectType() == DataDescription3.TYPE_DIR:
                if not parent.uri == None:
                    dd.SetURI(parent.uri + "/" + dd.name)
                else:
                    dd.SetURI(dd.name)
                persistentData.append(dd)                               
            else:
                #url = self.GetDownloadDescriptor(path[2]+os.path.sep+dd.name)
                if parent.GetLocation() == "":
                    log.debug("LoadPersistentInfo: Filename %s", dd.name)
                    url = self.GetDownloadDescriptor(dd.name)
                else:
                    url = self.GetDownloadDescriptor(parent.GetLocation() + os.path.sep + dd.name)
                if url != None:
                    if dd.GetObjectType() == DataDescription3.TYPE_FILE:
                        dd.SetURI(url)
                    else:
                        dd.SetURI(url + os.path.sep + dd.GetLocation())
                    # Only load if url not None (means file exists)
                    persistentData.append(dd)
                else:
                    log.info("File " + dd.name + " was not found, so it was not loaded.")

        for data in persistentData:
            log.debug("Adding Description %s ", data.name)
            self.descriptionDict[data.GetId()] = data
            parent.AddChild(data.GetId())
            
        log.debug ("=================== EXITED LoadPersistentInfo ==================")
    
                
    def Shutdown(self):
        self.StorePersistentData()


    def StorePersistentData(self):
        # Open the persistent store
        store = file(self.persistenceFileName, "w")
        store.write(self.AsINIBlock())
        store.close()
        
                   
    def LoadPersistentData(self, dataList):
        '''
        Adds a list of DataDescriptions.  If the datastore location
        has changed, url of data passed in is changed. If data is no
        longer present in the file system, the DataDescription
        is not ignored.
        '''

        persistentData = []
        
        for data in dataList:
            url = self.GetDownloadDescriptor(data.name)

            #
            # Remove data that has vanished
            #
            if url is None:
                log.debug("DataStore.LoadPersistentData: File %s is not valid, remove it" %data.name)

                try:
                    del self.descriptionDict[data.GetId()] 
                except:
                    # Data has vanished
                    pass

            #
            # Change url if data storage location has changed
            #
            else:
                data.SetURI(url)
                persistentData.append(data)

        self.cbLock.acquire()

        try:
            for data in persistentData:
                self.descriptionDict[data.GetId()] = data  
        except:
            log.exception("DataStore.LoadPersistentData: Failed")
            
        self.cbLock.release()
        
    def AsINIBlock(self):
        '''
        This serializes the data in the DataStore as a INI formatted
        block of text.

        **Returns**
            *string* The INI formatted list of DataDescriptions in the DataStore.
        '''
        self.cbLock.acquire()
        block = ""

        try:
            for item in self.descriptionDict:
                dataItem = self.GetDescById(item)
                block += dataItem.AsINIBlock()
        except:
            log.exception("DataStore.AsINIBlock: Failed")

        self.cbLock.release()   
                
        return block

    def GetDataDescriptions3(self):
        '''
        Retreive data in the DataStore as a list of DataDescriptions.
        This is the new interface method version.
        
        **Returns**
            *dataDescriptionList* A list of DataDescriptions representing data currently in the DataStore
        '''
        self.cbLock.acquire()
        try:
            dataDescriptionList = self.descriptionDict.values()
        except:
            log.exception("DataStore.GetDataDescription: Failed")

        self.cbLock.release()
                
        return dataDescriptionList

    def GetDataDescriptions(self):
        '''
        Retreive data in the DataStore as a list of DataDescriptions.
        Method for legacy support for AG 3.0.2. clients
        
        **Returns**
            *dataDescriptionList* A list of DataDescriptions representing data currently in the DataStore
        '''
        self.cbLock.acquire()
        try:
            dataDescriptionList = self.descriptionDict.values()
        except:
            log.exception("DataStore.GetDataDescription: Failed")

        self.cbLock.release()
                
        return dataDescriptionList

    def GetFiles(self):
        """
        Retrieve list of files in the data store

        Note: files are represented as a tuple (name,size)
        """

        fileList = []

        # Get files in data store path
        files = os.listdir(self.path)
        for fileN in files:
            stat = os.stat(os.path.join(self.path,fileN))
            fileList.append( (fileN,stat.st_size) )

        return fileList

    def RemoveFiles3(self, dataDescriptionList):
        """
        Removes the files specified by the DataDescriptions in the given list.
        This is the new interface method version.
        """
        filesWithError = ""

        # 
        # Try to remove all files in the list.  If an error occurs, raise a FileNotFound error
        # with a string containing all names of files that couldn't be removed errors.
        #
        for data in self.descriptionDict.values():
            log.debug("RemoveFiles: Content of TOC for data storage: %s", data.id)
        

        #Block with possible long duration; acquire lock

        self.cbLock.acquire()
        
        for data in dataDescriptionList:
            errorFlag = 0
            
            log.debug("Datastore.RemoveFiles: %s", data.name)
            log.debug("Datastore.RemoveFiles: data id %s", data.id)
            
            #Removed due to the fact that AG normally uses RemoveData to eliminate the data 
            #from the server.
            #Remove description from global description list
            del self.descriptionDict[data.id] 
            
            log.debug("RemoveFiles: Parent of file is: %s", data.GetParentId())
                
            #Determine level of file
            if data.GetParentId() == "-1":
                parentDD = self.root
            else:
                parentDD = self.descriptionDict[data.GetParentId()]
            
            log.debug("RemoveFiles: Parent is %s", parentDD.name)

            #Create path for deletion of file
            if parentDD == self.root:
                path = os.path.join(self.pathname, data.name)
            else:
                path = os.path.join(self.pathname, parentDD.GetLocation() + os.path.sep + data.name)
            log.debug("RemoveFiles: File location is: %s", path)
            
            #Perform delete at parent description
            parentDD.RemoveChild(data.id)

            #Check for valid path
            if not os.path.exists(path):
                errorFlag = 1
                log.error("DataStore.RemoveFiles: The path does not exist %s"%path)
                                
            #Actually remove the file from disk
            try:
                os.remove(path)
            except:
                log.exception("DataStore.RemoveFiles: raised error")
                errorFlag = 1
            
            if errorFlag:
                filesWithError = filesWithError + " "+data.name

        #Release lock 
        self.cbLock.release()
                
        log.debug("Reached end of RemoveFiles3")
        if filesWithError:
            raise FileNotFound(filesWithError)

    def RemoveFiles(self, dataDescriptionList):
        """
        Removes the files specified by the DataDescriptions in the given list.
        Method for legacy support for AG 3.0.2. clients
        """
        filesWithError = ""



        # 
        # Try to remove all files in the list.  If an error occurs, raise a FileNotFound error
        # with a string containing all names of files that couldn't be removed errors.
        #
        for data in self.descriptionDict.values():
            log.debug("RemoveFiles: Content of TOC for data storage: %s", data.id)
        

        #Block with possible long duration; acquire lock
        legacyCallInvalid = False
        legacyCallOnDir = False

        self.cbLock.acquire()
        
        for data in dataDescriptionList:

            errorFlag = 0
            
            log.debug("Datastore.RemoveFiles: %s", data.name)
            log.debug("Datastore.RemoveFiles: data id %s", data.id)
            
            #Removed due to the fact that AG normally uses RemoveData to eliminate the data 
            #from the server.
            #Remove description from global description list
            dataDescription = self.descriptionDict[data.id]
            if not isinstance(dataDescription, DirectoryDescription):
                if dataDescription.GetParentId() == "-1":
                    del self.descriptionDict[dataDescription.id] 
            
                                
                    #Determine level of file
                    parentDD = self.root
            
                
                    #Create path for deletion of file
                    path = os.path.join(self.pathname, dataDescription.name)
                
                    #Perform delete at parent description
                    parentDD.RemoveChild(dataDescription.id)

                    #Check for valid path
                    if not os.path.exists(path):
                        errorFlag = 1
                        log.error("DataStore.RemoveFiles: The path does not exist %s"%path)
                                
                    #Actually remove the file from disk
                    try:
                        os.remove(path)
                    except:
                        log.exception("DataStore.RemoveFiles: raised error")
                        errorFlag = 1
            
                    if errorFlag:
                        filesWithError = filesWithError + " "+dataDescription.name
                else:
                    legacyCallInvalid= True
            else:
                legacyCallOnDir = True

        #Release lock 
        self.cbLock.release()
                
        log.debug("Reached end of RemoveFiles3")

        if legacyCallInvalid or legacyCallOnDir:
            return True
            #raise NotAuthorized
        
        if filesWithError:
            raise FileNotFound(filesWithError)
        
        return False


    #Added by NA2-HPCE
    def RemoveDir(self, id):
        """
        Removes a directory specified by its DirectoryDescription GUID
        Possibly subentries of the directory will be also deleted
        """
        filesWithError = ""

        # 
        # Try to remove all files in the list.  If an error occurs, raise a FileNotFound error
        # with a string containing all names of files that couldn't be removed errors.
        #

        self.cbLock.acquire()
        #Get description of directory to be removed                       
        remDir = self.descriptionDict[id]

        #Determine level of directory in hierarchy
        if remDir.parentId == "-1":
            remDirParent = self.root
        else:
            remDirParent = self.descriptionDict[remDir.parentId]
        
        log.debug("Datastore.RemoveDirectory: %s", remDir.name)
                
        entryList= []

        log.debug("Entries in dataContainer: %s" , remDir.dataContainer)


        
        tempListOfIdsToRemove = []
        for item in remDir.dataContainer:
            tempListOfIdsToRemove.append(item)

        self.cbLock.release()
        
        for id in tempListOfIdsToRemove:
            self.cbLock.acquire()
            entry = self.GetDescById(id)
            if entry.IsOfType(DataDescription3.TYPE_DIR):
                #Remove Directory; descend recursively the whole directory subtree
                log.debug("RemoveDir: Removing subdirectory: %s", entry.name)
                self.cbLock.release()
                self.RemoveDir(entry.id)
            else:
                #Remove files if any left in the directory
                log.debug("RemoveDir: Removing file: %s", entry.name)
                entryList.append(entry)
                self.cbLock.release()
        
        if len(entryList) != 0:
            log.debug("RemoveDir: Number of files to remove: %s", len(entryList))
            self.RemoveFiles(entryList)
            
            #As the removal of data within a possibly non-empty directory
            #is not signaled to the clients, the deletion from the global
            #list in the DataStore has to be done here
            for item in entryList:
                del self.descriptionDict[item.id]
        
        self.cbLock.acquire()
        #Remove Directory from parent description
        log.debug("RemoveDir: ID of directory to be romved is: %s", remDir.id)
        log.debug("RemoveDir: Entry for ID in dictionary is: %s", self.descriptionDict[remDir.id].name)
        remDirParent.RemoveChild(remDir.id)
        del self.descriptionDict[remDir.id]

        #Create path for delete command and actually delete directory
        path = os.path.abspath(self.path + os .path.sep + remDir.location)
        log.debug(" Removing directory at: %s", path)
        os.rmdir(path)
        self.cbLock.release()
                    
        

    def ModifyData(self, data):
        
        log.debug("Datastore.ModifyData: %s", data.name)
        oldName = None
        errorFlag = None

        self.cbLock.acquire()
        try:
            oldName = self.descriptionDict[data.id].name
        except:
            log.exception("DataStore.ModifyData: Failed")
            
        self.cbLock.release()

        if oldName != data.name:
            oldPath = os.path.join(self.pathname, oldName)
            newPath = os.path.join(self.pathname, data.name)
                        
            if not os.path.exists(oldPath):
                errorFlag = 1
                log.error("DataStore.ModifyData: The path does not exist %s"%oldPath)
           
            try:
                os.rename(oldPath, newPath)
            except:
                log.exception("DataStore.ModifyFiles: raised error")
                errorFlag = 1

        self.cbLock.acquire()
        try:
            data.uri = self.GetDownloadDescriptor(data.name)
            self.descriptionDict[data] = data  
        except:
            log.exception("DataStore.ModifyFiles: Failed")
            
        self.cbLock.release()

        if errorFlag:
            raise FileNotFound()

    def GetTime(self):
        '''
        Get current time to use in descriptions.
        '''
        return time.strftime("%a, %b %d, %Y, %H:%M:%S", time.localtime() )
        
    def GetUploadDescriptor(self):
        """
        Return the upload descriptor for this datastore.

        """
        self.transferEngineLock.acquire()

        try:
            descriptor = self.transfer_engine.GetUploadDescriptor(self.prefix)
        except:
            log.exception("DataStore.GetUploadDescriptor: Failed")
        
        self.transferEngineLock.release()
                
        return descriptor

    def GetDownloadDescriptor(self, filename):
        """
        Return the download descriptor for filename.

        If filename is not present in the datastore, return None.

        """
        log.debug("GetDownLoadDescriptor: Pathname is %s", self.pathname)
        log.debug("GetDownLoadDescriptor: Filename is %s", filename)

        path = os.path.join(self.pathname, filename)
        
        log.debug("GetDownLoadDescriptor: Joined Path is %s", path)
        
        path = os.path.abspath(path)

             
        if not os.path.exists(path):
            log.error("GetDownLoadDescriptor: File path %s is not existing!", path)
            return None

        self.transferEngineLock.acquire()
        try:
            descriptor = self.transfer_engine.GetDownloadDescriptor(self.prefix, filename)
        except:
            log.exception("DataStore.GetDownloadDescriptor")
            
        self.transferEngineLock.release()
             
        return descriptor

    def GetDownloadFilename(self, id_token, url_path):
        """
        Return the full path of the given filename in this datastore.

        Used by the transfer engine to find a requested file.
        This method must perform an authorization check on dn, the
        distinguished name of the client requesting the file. If this fails,
        raise a NotAuthorized exception. If the file does not exist,
        raise a FileNotFound exception.

        """
        log.debug("Get download: id='%s' path='%s'", id_token, url_path)
        # Authorization check for dn goes here
        path = os.path.join(self.pathname, url_path)
        
        log.debug("DataStore::GetDownloadFilename: path %s, pathname: %s, url_path: %s"
            %(path, self.pathname, url_path))
        if not os.path.isfile(path):
            log.debug("DataStore::GetDownloadFilename: File is not found")
            raise FileNotFound

        return path

    def CanUploadFile(self, dn, file_info):
        """
        Used by the transfer engine to determine if a client is able to
        upload a new file.

        Arguments:
         - dn is the distinguished name of the client
         - file_info is a file information dict for hte file the client is trying to upload

        Current test is just to see if the file exists.
        Need to test to see if the client is currently logged into the venue.
        """

        log.debug("CanUploadFile: dn %s fi %s", dn, file_info)
        
        filename = file_info['name']

        try:
            # Don't allow upload filenames that can't be decoded by us-ascii until
            #   the rest of the toolkit supports unicode better.
            unicode(filename, 'us-ascii')
        except UnicodeDecodeError:
            desc = "InvalidFileName"
            log.info("CanUploadFile: returning 0, desc='%s'", desc)
            return 0

        self.cbLock.acquire()
        try:
            desc = self.GetDescbyName(filename)
        except:
            log.exception("DataStore.GetData: Failed")
            
        self.cbLock.release()

        if desc is None or desc == "":
            return 1
        else:
            log.info("CanUploadFile: returning 0, desc='%s'", desc)
            return 0

    def GetUploadFilename(self, dn, file_info):
        """
        Return the filename for a file to be uploaded.

        file_info is a file information dictionary.

        The client is running with identity "dn".

        This is used by the transfer engine to provide a
        destination for a file upload.

        """
        log.debug("GetUploadFilename: dn %s fi %s", dn, file_info)

        # First verify that we have a state=pending description in the venue.
        filename = file_info['name']
        
        self.cbLock.acquire()
        try:
            desc = self.GetDescbyName(filename) # TODO: Add dict retrieval based on filename
        except:
            log.exception("DataStore.GetUploadFilename: Failed")
            
        self.cbLock.release()
                        
        if desc is None:
            log.debug("Datastore::GetUploadFilenameVenue: data for %s not present", filename)
            return None

        if desc.GetStatus() != DataDescription.STATUS_PENDING:
            log.debug("Datastore::GetUploadFilenameVenue: Invalid status in GetUploadFileHandle()")
            return None

        #
        # Okay, we should be cool. Open up the file for creation.
        # (Ignoring whether the file is there or not - the metadata
        # assures us we have the right to do so).
        #

        path = os.path.join(self.pathname, filename)

        return path

    #Modified by NA2-HPCE
    def AddFile(self,identityToken,filename):
    
        url = self.GetDownloadDescriptor(filename)
        url = urllib.unquote(url) # Keep quoted chars out of the URL used as uri in the descriptions
        
        path = os.path.join(self.pathname,filename)

        log.debug("AddFile: URL to download location is: %s", url)
        log.debug("AddFile: Path to FTP location of file is: %s", path)
        
        #split file-path to only name the description after its filename
        fileList = filename.split(os.path.sep)
                
        if len(fileList) == 1:
            parentID = "-1" # direct insertion under root (len(fileList)=1 means only filename with no dir is contained)
        else:
            #insertion in a subdirectory
            #Time consuming action, get lock
            self.cbLock.acquire()
            parentID = self.root.Search(self.descriptionDict,fileList[0:len(fileList)-1])
            #Unlock
            self.cbLock.release()

                
        log.debug("AddFile: Determined parentID is: %s", parentID)
        
        desc = DataDescription3(fileList[len(fileList)-1]) # Last item in list is the filename
        desc.SetSize(int(os.stat(path)[stat.ST_SIZE]))
        desc.SetStatus(DataDescription3.STATUS_PRESENT)
        desc.SetOwner(identityToken)
        desc.SetParentId(parentID)
        desc.SetObjectType(DataDescription3.TYPE_FILE)
        desc.SetLevel(-2)
        desc.SetURI(url)
        log.debug("AddFile: URI is %s", url)
        desc.SetLastModified(self.GetTime())
        


        if self.GetDescbyName(filename):
            #Perform actual file adding; get lock
            self.cbLock.acquire()
            desc.SetURI(url)
            self.cbLock.acquire()
            try:
                self.descriptionDict[desc] = desc
                self.callbackClass.UpdateData(desc, 1)
            except:
                log.exception("DataStore.RemoveData: Failed")
            self.cbLock.release()
        else:
            print "Add new file to datastore"
            self.cbLock.acquire()
            self.descriptionDict[desc.GetId()] = desc

            if not desc.GetParentId() == "-1":
                self.descriptionDict[desc.GetParentId()].GetChildren().append(desc.GetId())
            else:
                self.root.GetChildren().append(desc.GetId())
                
            self.callbackClass.AddData(desc)
            self.cbLock.release()
            
    def GetDescbyName(self, name):
        """
        Retrieves a DataDescription specified by its name property. 
        """

        ItemExists = False
        
        for item in self.descriptionDict.values():
            log.debug("GetDescbyName Name: %s", item.name)
            if item.name == name:
                ItemExists = True
                        
        return ItemExists

    def CompleteUpload(self, identityToken, file_info):
        """
        The upload is done. Get the data description, update with the
        information from the file_info dict (which contains the information
        from the manifest).
        """
        self.cbLock.acquire()

        try:
            desc = self.dataDescContainer.GetData(file_info['name'])
        except:
            log.exception("DataStore.CompleteUpload: Failed")

        self.cbLock.release()
        
        log.debug("Datastore::CompleteUpload: got desc %s %s", desc, desc.__dict__)
        desc.SetChecksum(file_info['checksum'])
        desc.SetSize(int(file_info['size']))
        desc.SetStatus(DataDescription3.STATUS_PRESENT)
        desc.SetOwner(identityToken)
        desc.SetURI(self.GetDownloadDescriptor(file_info['name']))
        desc.SetLastModified(self.GetTime())
        
        log.debug("Datastore::CompleteUpload: updating with %s %s", desc, desc.__dict__)

        url = self.GetDownloadDescriptor(desc.name)
        
        log.debug("Checking file %s for validity", desc.name)
        
        if url is None:
            log.warn("File %s has vanished", desc.name)
            self.cbLock.acquire()
            try:
                del self.descriptionDict[desc.getId()]
            except:
                log.exception("DataStore.RemoveData: Failed")
                
            self.cbLock.release()
        else:
            desc.SetURI(url)
            self.cbLock.acquire()
            try:
                self.descriptionDict[desc.GetId()] = desc
                self.callbackClass.UpdateData(desc, 1)
            except:
                log.exception("DataStore.RemoveData: Failed")
                
            self.cbLock.release()
                      
    def AddPendingUpload3(self, identityToken, filename):
        """
        Create a data description for filename with a state of 'pending' and
        add to the venue.
        This is the new interface method version.
        """
        log.debug("AddPendingUpload ENTERED!!!!!!!")

        desc = FileDescription(filename)
        desc.SetStatus(DataDescription3.STATUS_PENDING)
        #desc.SetOwner(identityToken.dn)
        desc.SetOwner(identityToken)
        desc.SetLevel(-2) # Files are per definition level = -2 to distinguish from 
        desc.SetParentID(self.curParentID) # set ID of the parent DataDescription

                
        """
        Changing code here to allow addign DDs to different hierarchy levels
        """
        if not self.curDDC == None:
            self.cbLock.acquire()
            self.curDDC.AddData(desc)
            self.callbackClass.AddData(desc)
            self.cbLock.release()
        else:
            self.cbLock.acquire()
            self.dataDescContainer.AddData(desc)
            self.callbackClass.AddData(desc)
            self.cbLock.release()
                                                
        return desc

    def AddPendingUpload(self, identityToken, filename):
        """
        Create a data description for filename with a state of 'pending' and
        add to the venue.
        Method for legacy support for AG 3.0.2. clients
        """
        log.debug("AddPendingUpload ENTERED!!!!!!!")

        desc = FileDescription(filename)
        desc.SetStatus(DataDescription.STATUS_PENDING)
        #desc.SetOwner(identityToken.dn)
        desc.SetOwner(identityToken)
        desc.SetLevel(-2) # Files are per definition level = -2 to distinguish from 
        desc.SetParentID(self.curParentID) # set ID of the parent DataDescription

                
        """
        Changing code here to allow addign DDs to different hierarchy levels
        """
        if not self.curDDC == None:
            self.cbLock.acquire()
            self.curDDC.AddData(desc)
            self.callbackClass.AddData(desc)
            self.cbLock.release()
        else:
            self.cbLock.acquire()
            self.dataDescContainer.AddData(desc)
            self.callbackClass.AddData(desc)
            self.cbLock.release()
                                                
        return desc
    
    #Added by NA2-HPCE
    def Dump(self, desc=None):
        """
        Dumps the contents of this DataDescContainer and all subsequent containers
        Used for debugging the data structure of the directory storage on the 
        venue server.
        """

        if desc == None:
            children = self.root.GetChildren()
            desc = self.root
        else:
            children = desc.GetChildren() 
            
        log.debug("===========================================================")
        log.debug("Data hierarchy dump: Level %s",desc.GetLevel())
        log.debug("- %s : Type: %s : Parent: %s", desc.GetName(), desc.GetObjectType(), desc.GetParentId())
        
        for item in children:
            newDesc = self.descriptionDict[item]
            self.Dump(newDesc)
        
        log.debug("===========================================================")
        
        
    def DumpDataStack(self):
        """
        Dumps the data in the file data stack to the log file, printing the names
        of the files and directories
        
        Used for local debug only
        """

        log.debug("Data Stack Dump")
        log.debug("===================================================")
        print "Data Stack Dump"
        print "==================================================="
    
        for item in self.descriptionDict:
            dataObject = self.GetDescById(item)
            if dataObject.IsOfType(DataDescription3.TYPE_DIR):
                log.debug("Dir - %s", dataObject.GetName())
                print "Dir - ", dataObject.GetName()
            else:
                log.debug("File - %s", dataObject.GetName())
                print "File - ", dataObject.GetName()
        
        
    #ZSI:HO
    def GetDirSize(self, path):
        """
        Calculates the size of a given directory 
        """
        size = 0
        
        list = os.listdir(path)
        
        
        for item in list:
            checkItem = os.path.join(path,item)
            log.debug("Path to check: %s", checkItem)
            if os.path.isfile(os.path.abspath(checkItem)):
                log.debug("Is file!")
                size += os.path.getsize(checkItem)
            else:
                log.debug("Is dir!")    
                size += self.GetDirSize(os.path.abspath(checkItem))

        return size
    
    def GetDataSize(self):
        """
        Calculates the overall size of the data store.
        """
        size = self.GetDirSize(os.path.abspath(self.path)) / 1024
        log.debug("DATASTORE: Data size of path %s is: %s", os.path.abspath(self.path), size)
        strSize = str(size)
        log.debug("DATASTORE: String object: %s", strSize)
        return size
        
        
    #Added by NA2-HPCE
    def AddDir(self, name, desc, level, parentUID):
        """
        Adds a directory specified by its name, a description and the level in the hierarchy 
        it should be inserted. The parentUID specifies the GUID of the DataDescription object
        of the parent of the directory to be added
        """
        locDir = DirectoryDescription(name)
        locDir.SetStatus(DataDescription3.STATUS_PRESENT)
        locDir.SetDescription(desc)
        locDir.SetLevel(level)
        log.debug("ParentId to be set: %s", parentUID)
        log.debug("Root is %s", self.root)
        
        #Search for parent
        if parentUID == "0":
            log.debug("Found parent to be 0!")
            locParent = self.root
            locDir.SetParentId(-1)
            os.mkdir(self.pathname + "/" + locDir.GetName())
            locDir.SetLocation(name)
            locDir.SetURI("/" + name)
        else:
            log.debug("Found parent to be <>0!")
            locDir.SetParentId(parentUID)
            locParent = self.descriptionDict[parentUID]
            os.mkdir(self.pathname + "/" + locParent.GetLocation() + "/" + locDir.GetName())
            locDir.SetLocation(locParent.GetLocation() + "/" + locDir.GetName())
            locDir.SetURI(locParent.GetLocation() + "/" + locDir.GetName())
        
        log.debug("URI is %s", locDir.GetURI())
            
        log.debug("Determined parent is %s ", locParent)
        
        self.cbLock.acquire()
        locParent.AddChild(locDir.GetId())
        self.descriptionDict[locDir.GetId()] = locDir
        self.cbLock.release()
                
        return locDir


    def CancelPendingUpload(self, filename):
        desc = self.GetDescription(filename)

        # Make sure datadescription exists in datastore.
        if desc == None:
            log.warn("CancelPendingUpload: didn't find file description that should be pending.")
            return

        # Make sure file is still pending upload
        if desc.GetStatus() != DataDescription.STATUS_PENDING:
            log.error("CancelPendingUpload: found file description but status was not pending.")
            return

        # Remove the file from the datastore
        self.RemoveFiles([desc])
        # distribute updated event.

        self.cbLock.acquire()
       
        try:
            self.callbackClass.DistributeEvent(Event.REMOVE_DATA, desc )
        except:
            log.exception("DataStore.CancelPendingUpload: Failed")
            
        self.cbLock.release()
        
    def GetDescription(self, filename):
        """
        Method for legacy support for AG 3.0.2. clients
        """
        return self.descriptionDict.GetData(filename) #get description by filename

    def GetDescription3(self, filename):
        return self.descriptionDict.GetData(filename) #get description by filename

    def SetDescription(self, filename, description):
        """
        Given a data description and a filename,
        set the data description if the file exists
        Method for legacy support for AG 3.0.2. clients
        """

        path = os.path.join(self.pathname, filename)
        if os.path.exists(path):
            description.uri = self.GetDownloadDescriptor(filename)
            self.descriptionDict[description.GetId()] = description

    def SetDescription3(self, filename, description):
        """
        Given a data description and a filename,
        set the data description if the file exists
        """

        path = os.path.join(self.pathname, filename)
        if os.path.exists(path):
            description.uri = self.GetDownloadDescriptor(filename)
            self.descriptionDict[description.GetId()] = description         
    
    #Added by NA2-HPCE
    def GetCurDataDesc(self):
        """
        Retrieves the DataDescription currently set as current 
        DataDescription
        """
        return self.root

    def GetDescById(self,id):
        """
        Retrieves the DataDescription currently set as current 
        DataDescription
        """
        return self.descriptionDict[id]


UploadFile = FTPSClient.FTPSUploadFile
_DownloadFile = FTPSClient.FTPSDownloadFile

DataServer = FTPSServer.FTPSServer

def UploadFiles(identity, upload_url, file_list, user=None,passw=None,ssl_ctx=None,progressCB=None):
    log.info('UploadFiles: %s %s', upload_url, str(file_list))
    for f in file_list:
        f = str(f)
        fulluploadurl = os.path.join(upload_url,f)
        log.debug('UploadFiles: %s %s %s', upload_url,fulluploadurl, str(file_list))
        try:
        
            UploadFile(f,upload_url,user=user,passw=passw,
                       ssl_ctx=ssl_ctx,progressCB=progressCB)
        except FTPSClient.UserCancelled:
            raise UserCancelled(f)
    if progressCB:
        progressCB(f,
                   1,
                   0,
                   1,1)


def DownloadFile(identity, download_url, destination, size, checksum,
                     user=None,passw=None,ssl_ctx=None,progressCB = None):
    log.info("DownloadFile: url %s file %s", download_url,destination)
    try:
        download_url = download_url.replace("%20"," ")
        ret = _DownloadFile(download_url,destination,user=user,passw=passw,
                            ssl_ctx=ssl_ctx,progressCB=progressCB)
    except FTPSClient.UserCancelled:
        raise UserCancelled(download_url)
        
    return ret
