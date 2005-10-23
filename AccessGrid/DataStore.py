#-----------------------------------------------------------------------------
# Name:        DataStore.py
# Purpose:     This is a data storage server.
# Created:     2002/12/12
# RCS-ID:      $Id: DataStore.py,v 1.87 2005-10-23 07:39:18 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: DataStore.py,v 1.87 2005-10-23 07:39:18 turam Exp $"

import os
import time
import threading
import re
import urllib
import urlparse
import httplib
import string
import shutil
import sys
import socket
import md5
import ConfigParser
import cStringIO
import Queue
import BaseHTTPServer
import select

from AccessGrid import Log
import AccessGrid.GUID
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.Descriptions import DataDescription, CreateDataDescription
from AccessGrid.Events import Event

from AccessGrid import FTPSClient,FTPSServer

log = Log.GetLogger(Log.DataStore)

class NotAPlainFile(Exception):
    pass

class DuplicateFile(Exception):
    pass

class FileNotFound(Exception):
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
        log.debug("DataDescriptionContainer::AddData: Distribute ADD_DATA event %s", dataDescription)

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
            
        #if self.data.has_key(fileName):
        #    return self.data[fileName]
        #else:
        #    return None
    
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
    """
    
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
        self.transfer_engine = transferEngine
        #self.transfer_engine.RegisterPrefix(prefix,self)

        self.cbLock = threading.Lock()
        self.transferEngineLock = threading.Lock()

        self.dataDescContainer = DataDescriptionContainer()
        
        self.__CheckPath()
        self.persistenceFileName = os.path.join(self.path, "DataStore.dat")
        self.LoadPersistentInfo()

    def __CheckPath(self):
        if self.path == None or not os.path.exists(self.path):
            log.exception("DataStore::init: Datastore path %s does not exist" % (self.path))
            try:
                os.mkdir(self.path)
            except OSError:
                log.exception("Could not create Data Service.")
                self.path = None
       
    def LoadPersistentInfo(self):
# FIXME: not using metadata yet
#         cp = ConfigParser.ConfigParser()
#         cp.read(self.persistenceFileName)
# 
        log.debug("Reading persisted data from: %s", self.persistenceFileName)
        persistentData = []
        
        files = os.listdir(self.path)
        files.remove('DataStore.dat')
        for f in files:   
            dd = DataDescription(f)
            dd.SetId(str(AccessGrid.GUID.GUID()))
#             try:
#                 dd.SetDescription(cp.get(sec, 'description'))
#             except ConfigParser.NoOptionError:
#                 log.info("LoadPersistentVenues: Data has no description")
            dd.SetStatus(DataDescription.STATUS_PRESENT)
            stat = os.stat(os.path.join(self.path,f))
            dd.SetSize(stat.st_size)
#             dd.SetChecksum(cp.get(sec, 'checksum'))
#             dd.SetOwner(cp.get(sec, 'owner'))
#             dd.SetType(cp.get(sec, 'type'))
# 
#             try:
#                 dd.SetLastModified(cp.get(sec, 'lastModified'))
#             except:
#                 log.info("LoadPersistentVenues: Data has no last modified date. Probably old DataDescription")
            
            url = self.GetDownloadDescriptor(dd.name)
            if url != None:
                dd.SetURI(url)
                # Only load if url not None (means file exists)
                persistentData.append(dd)
            else:
                log.info("File " + dd.name + " was not found, so it was not loaded.")

        self.dataDescContainer.LoadPersistentData(persistentData)
                
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
                    self.dataDescContainer.RemoveData(data)
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
            self.dataDescContainer.LoadPersistentData(persistentData)
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

        try:
            block = self.dataDescContainer.AsINIBlock()
        except:
            log.exception("DataStore.AsINIBlock: Failed")

        self.cbLock.release()   
                
        return block

    def GetDataDescriptions(self):
        '''
        Retreive data in the DataStore as a list of DataDescriptions.
        
        **Returns**
            *dataDescriptionList* A list of DataDescriptions representing data currently in the DataStore
        '''
        self.cbLock.acquire()
        try:
            dataDescriptionList = self.dataDescContainer.GetDataDescriptions()
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


    def RemoveFiles(self, dataDescriptionList):
        filesWithError = ""

        # 
        # Try to remove all files in the list.  If an error occurs, raise a FileNotFound error
        # with a string containing all names of files that couldn't be removed errors.
        #
        for data in dataDescriptionList:
            errorFlag = 0
            
            log.debug("Datastore.RemoveFiles: %s", data.name)

            try:
                self.cbLock.acquire()
                self.dataDescContainer.RemoveData(data)
                self.cbLock.release()
            except:
                self.cbLock.release()
                log.error("DataStore.RemoveFiles: Can not remove data from callbackclass")
                #  errorFlag = 1
                # We don't have to raise an exception for this

            path = os.path.join(self.pathname, data.name)
                                   
            if not os.path.exists(path):
                errorFlag = 1
                log.error("DataStore.RemoveFiles: The path does not exist %s"%path)
                                
            try:
                os.remove(path)
            except:
                log.exception("DataStore.RemoveFiles: raised error")
                errorFlag = 1
                
            if errorFlag:
                filesWithError = filesWithError + " "+data.name
                
        if filesWithError:
            raise FileNotFound(filesWithError)

    def ModifyData(self, data):
        
        log.debug("Datastore.ModifyData: %s", data.name)
        oldName = None
        errorFlag = None

        self.cbLock.acquire()
        try:
            oldName = self.dataDescContainer.GetDataFromId(data.id).name
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
            self.dataDescContainer.UpdateData(data)
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
        
    def UploadLocalFiles(self, fileList, dn, id):
        '''
        Add file to a local datastore
        '''
        for filename in fileList:
            try:
                # Transfer file from local path to local data store path
                infile = open(filename, 'rb')
                fileString = infile.read()
                
                path, name = os.path.split(filename)

                if not os.path.exists(self.pathname):
                    log.debug("DataStore::AddFile: Personal data storage directory does not exist, create it")
                    os.mkdir(self.pathname)

                self.cbLock.acquire()
                try:
                    desc = self.dataDescContainer.GetData(name)
                except:
                    log.exception("DataStore.UploadLocalFile: failed")

                self.cbLock.release()
                
                if desc == None:
                    dataStorePath = os.path.join(self.pathname, name)
                    log.debug("DataStore::AddFile: Personal datastorage is located at %s"%dataStorePath)
                    output = open(dataStorePath, 'wb')
                    output.write(fileString)
                    infile.close()
                    output.close()
                    
                    # Create DataDescription
                    size = os.path.getsize(dataStorePath)
                    log.debug("DataStore::AddFile: Size of file %s" %size)
                    
                    # This should be done in a loop in case
                    # the file is big
                    checksum = md5.new(fileString).hexdigest()
                    log.debug("DataStore::AddFile: Checksum %s" %checksum)
                    
                    desc = DataDescription(name)
                    desc.SetOwner(dn)
                    desc.SetType(id) # id shows that this data is personal
                    desc.SetChecksum(checksum)
                    desc.SetSize(int(size))
                    desc.SetStatus(DataDescription.STATUS_PRESENT)
                    desc.SetLastModified(self.GetTime())

                    self.transferEngineLock.acquire()
                    try:
                        desc.SetURI(self.transfer_engine.GetDownloadDescriptor(self.prefix,
                                                                               name))
                    except:
                        log.exception("DataStore.AddFile: Failed")
                        
                    self.transferEngineLock.release()

                    log.debug("DataStore::AddFile: updating with %s %s", desc, desc.__dict__)

                    self.cbLock.acquire()

                    try:
                        self.dataDescContainer.AddData(desc)
                    except:
                        log.exception("DataStore.AddFile: Failed")
                        
                    self.cbLock.release()
                    
                else:
                    raise DuplicateFile(desc) 

            except DuplicateFile, e:
                raise e
        
            except:
                log.exception("DataStore::AddFile: Error when trying to add local data to datastorage")
                raise UploadFailed("Error when trying to add local data to datastorage")
           
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
        path = os.path.join(self.pathname, filename)
             
        if not os.path.exists(path):
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
            desc = self.dataDescContainer.GetData(filename)
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
            desc = self.dataDescContainer.GetData(filename)
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
        desc.SetStatus(DataDescription.STATUS_PRESENT)
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
                self.dataDescContainer.RemoveData(desc)
            except:
                log.exception("DataStore.RemoveData: Failed")
                
            self.cbLock.release()
        else:
            desc.SetURI(url)
            self.cbLock.acquire()
            try:
                self.dataDescContainer.UpdateData(desc)
                self.callbackClass.UpdateData(desc, 1)
            except:
                log.exception("DataStore.RemoveData: Failed")
                
            self.cbLock.release()
                      
    def AddPendingUpload(self, identityToken, filename):
        """
        Create a data description for filename with a state of 'pending' and
        add to the venue.

        """

        desc = DataDescription(filename)
        desc.SetStatus(DataDescription.STATUS_PENDING)
        #desc.SetOwner(identityToken.dn)
        desc.SetOwner(identityToken)

        


        self.cbLock.acquire()
        try:
            self.dataDescContainer.AddData(desc)
            self.callbackClass.AddData(desc)
        except:
            log.exception("DataStore.AddPendingUpload: Failed")
        self.cbLock.release()
                        
        return desc

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
        return self.dataDescContainer.GetData(filename)

    def SetDescription(self, filename, descriptionStruct):
        """
        Given a data description and a filename,
        set the data description if the file exists
        """

        description = CreateDataDescription(descriptionStruct)

        path = os.path.join(self.pathname, filename)
        if os.path.exists(path):
            description.uri = self.GetDownloadDescriptor(filename)
            self.dataDescContainer.AddData(description)



UploadFile = FTPSClient.FTPSUploadFile
_DownloadFile = FTPSClient.FTPSDownloadFile

DataServer = FTPSServer.FTPSServer

def UploadFiles(identity, upload_url, file_list, progressCB):
    log.debug('UploadFiles: %s %s', upload_url, str(file_list))
    for f in file_list:
        f = str(f)
        fulluploadurl = os.path.join(upload_url,f)
        log.debug('UploadFiles: %s %s %s', upload_url,fulluploadurl, str(file_list))
        UploadFile(f,upload_url)

def DownloadFile(identity, download_url, destination, size, checksum,
                     progressCB = None):
    return _DownloadFile(download_url,destination,progressCB=progressCB)


