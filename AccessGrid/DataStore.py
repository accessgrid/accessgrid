#-----------------------------------------------------------------------------
# Name:        DataStore.py
# Purpose:     This is a data storage server.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: DataStore.py,v 1.60 2004-03-02 22:43:58 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: DataStore.py,v 1.60 2004-03-02 22:43:58 judson Exp $"
__docformat__ = "restructuredtext en"

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
from time import localtime , strftime
import logging
import BaseHTTPServer

from pyGlobus.io import GSITCPSocketException
from pyGlobus import io

import AccessGrid.GUID
from AccessGrid import Platform
from AccessGrid.NetUtilities import GetHostname
from AccessGrid.Descriptions import DataDescription, CreateDataDescription
from AccessGrid.EventServiceAsynch import EventService
from AccessGrid.Events import RemoveDataEvent, UpdateDataEvent,  AddDataEvent
from AccessGrid.EventClient import EventClient, EventClientWriteDataException
from AccessGrid.Events import Event, ConnectEvent, HeartbeatEvent
from AccessGrid.Security import Utilities

log = logging.getLogger("AG.DataStore")

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
       
    def SetEventDistributor(self, eventDistributor, channelId):
        '''
        Sets the object used to send events

        **Arguments**

        *eventDistributor* Object that sends events
        *channelId* channel ID to use for events
        '''
        
        self.eventDistributor = eventDistributor
        self.channelId = channelId
            
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

    def UpdateData(self, dataDescription,):
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
        name = dataDescription.name

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
        self.transfer_engine.RegisterPrefix(prefix,self)

        self.cbLock = threading.Lock()
        self.transferEngineLock = threading.Lock()

        self.dataDescContainer = DataDescriptionContainer()
        
        self.__CheckPath()
        self.persistenceFileName = os.path.join(self.path, "DataStore.dat")
        self.LoadPersistentInfo()

    def __CheckPath(self):
        if not os.path.exists(self.path):
            log.exception("DataStore::init: Datastore path %s does not exist" % (self.path))
            try:
                os.mkdir(self.path)
            except OSError:
                log.exception("Could not create Data Service.")
                self.path = None
       
    def LoadPersistentInfo(self):
        cp = ConfigParser.ConfigParser()
        cp.read(self.persistenceFileName)

        log.debug("Reading persisted data from: %s", self.persistenceFileName)
        persistentData = []
        
        for sec in cp.sections():
            dd = DataDescription(cp.get(sec, 'name'))
            dd.SetId(sec)
            try:
                dd.SetDescription(cp.get(sec, 'description'))
            except ConfigParser.NoOptionError:
                log.info("LoadPersistentVenues: Data has no description")
            dd.SetStatus(cp.get(sec, 'status'))
            dd.SetSize(cp.getint(sec, 'size'))
            dd.SetChecksum(cp.get(sec, 'checksum'))
            dd.SetOwner(cp.get(sec, 'owner'))
            dd.SetType(cp.get(sec, 'type'))

            try:
                dd.SetLastModified(cp.get(sec, 'lastModified'))
            except:
                log.info("LoadPersistentVenues: Data has no last modified date. Probably old DataDescription")
            
            url = self.GetDownloadDescriptor(dd.name)
            if url != None:
                dd.SetURI(url)
                # Only load if url not None (means file exists)
                persistentData.append(dd)
                self.dataDescContainer.LoadPersistentData(persistentData)
            else:
                log.info("File " + dd.name + " was not found, so it was not loaded.")
                
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
        self.dataDescContainer.LoadPersistentData(persistentData)
        self.cbLock.release()
        
    def AsINIBlock(self):
        '''
        This serializes the data in the DataStore as a INI formatted
        block of text.

        **Returns**
            *string* The INI formatted list of DataDescriptions in the DataStore.
        '''
        self.cbLock.acquire()
        block = self.dataDescContainer.AsINIBlock()
        self.cbLock.release()   
                
        return block

    def GetDataDescriptions(self):
        '''
        Retreive data in the DataStore as a list of DataDescriptions.
        
        **Returns**
            *dataDescriptionList* A list of DataDescriptions representing data currently in the DataStore
        '''
        self.cbLock.acquire()
        dataDescriptionList = self.dataDescContainer.GetDataDescriptions()
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
        for file in files:
            stat = os.stat(os.path.join(self.path,file))
            fileList.append( (file,stat.st_size) )

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
                
        if errorFlag:
            raise FileNotFound(filesWithError)

    def ModifyData(self, data):
        
        log.debug("Datastore.ModifyData: %s", data.name)
        oldName = None
        errorFlag = None

        self.cbLock.acquire()
        oldName = self.dataDescContainer.GetDataFromId(data.id).name
        self.cbLock.release()

        if oldName != data.name:
            oldPath = os.path.join(self.pathname, oldName)
            newPath = os.path.join(self.pathname, data.name)
                        
            if not os.path.exists(oldPath):
                errorFlag = 1
                log.error("DataStore.ModifyData: The path does not exist %s"%path)
           
            try:
                os.rename(oldPath, newPath)
            except:
                log.exception("DataStore.ModifyFiles: raised error")
                errorFlag = 1

        self.cbLock.acquire()
        data.uri = self.GetDownloadDescriptor(data.name)
        self.dataDescContainer.UpdateData(data)
        self.cbLock.release()

        if errorFlag:
            raise FileNotFound()

    def GetTime(self):
        '''
        Get current time to use in descriptions.
        '''
        return strftime("%a, %b %d, %Y, %H:%M:%S", localtime() )
        
    def UploadLocalFiles(self, fileList, dn, id):
        '''
        Add file to a local datastore
        '''
        for filename in fileList:
            try:
                # Transfer file from local path to local data store path
                input = open(filename, 'rb')
                fileString = input.read()
                
                path, name = os.path.split(filename)

                if not os.path.exists(self.pathname):
                    log.debug("DataStore::AddFile: Personal data storage directory does not exist, create it")
                    os.mkdir(self.pathname)

                self.cbLock.acquire()
                desc = self.dataDescContainer.GetData(name)
                self.cbLock.release()
                
                if desc == None:
                    dataStorePath = os.path.join(self.pathname, name)
                    log.debug("DataStore::AddFile: Personal datastorage is located at %s"%dataStorePath)
                    output = open(dataStorePath, 'wb')
                    output.write(fileString)
                    input.close()
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
                    desc.SetURI(self.transfer_engine.GetDownloadDescriptor(self.prefix,
                                                                               name))
                    self.transferEngineLock.release()

                    log.debug("DataStore::AddFile: updating with %s %s", desc, desc.__dict__)

                    self.cbLock.acquire()
                    self.dataDescContainer.AddData(desc)
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
        descriptor = self.transfer_engine.GetUploadDescriptor(self.prefix)
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
        descriptor = self.transfer_engine.GetDownloadDescriptor(self.prefix, filename)
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
        # print "OpenFile: dn=%s filename=%s" % (dn, filename)

        #
        # Authorization check for dn goes here
        #

        
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

        filename = file_info['name']

        self.cbLock.acquire()
        desc = self.dataDescContainer.GetData(filename)
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

        #
        # First verify that we have a state=pending description in the venue.
        #

        filename = file_info['name']
        
        self.cbLock.acquire()
        desc = self.dataDescContainer.GetData(filename)
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
        desc = self.dataDescContainer.GetData(file_info['name'])
        self.cbLock.release()
        
        log.debug("Datastore::CompleteUpload: got desc %s %s", desc, desc.__dict__)
        desc.SetChecksum(file_info['checksum'])
        desc.SetSize(int(file_info['size']))
        desc.SetStatus(DataDescription.STATUS_PRESENT)
        desc.SetOwner(identityToken.dn)
        desc.SetURI(self.GetDownloadDescriptor(file_info['name']))
        desc.SetLastModified(self.GetTime())
        
        log.debug("Datastore::CompleteUpload: updating with %s %s", desc, desc.__dict__)

        url = self.GetDownloadDescriptor(desc.name)
        
        log.debug("Checking file %s for validity", desc.name)
        
        if url is None:
            log.warn("File %s has vanished", name)
            self.cbLock.acquire()
            self.dataDescContainer.RemoveData(desc)
            self.cbLock.release()
        else:
            desc.SetURI(url)
            self.cbLock.acquire()
            self.dataDescContainer.UpdateData(desc)
            self.callbackClass.UpdateData(desc)
            self.cbLock.release()
                      
    def AddPendingUpload(self, identityToken, filename):
        """
        Create a data description for filename with a state of 'pending' and
        add to the venue.

        """

        desc = DataDescription(filename)
        desc.SetStatus(DataDescription.STATUS_PENDING)
        desc.SetOwner(identityToken.dn)

        self.cbLock.acquire()
        self.dataDescContainer.AddData(desc)
        self.callbackClass.AddData(desc)
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
        self.callbackClass.DistributeEvent(Event( Event.REMOVE_DATA, self.callbackClass.uniqueId, desc ))
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



class HTTPTransferHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        log.info("%s - - [%s] %s", self.address_string(),
                 self.log_date_time_string(), format % args)
        
    def do_GET(self):

        #
        # Retrieve an identity token from the TransferServer. 
        # We pass the transfer handler through so that the
        # protocol-specific code in TransferServer can have access
        # to the connection-specific information in the handler
        # instance.
        #

        identityToken = self.server.GetIdentityToken(self)
        log.debug("HTTPTransferHandler::do_GET: GET identity token %s", identityToken)
        
        try:
            log.debug("HTTPTransferHandler::do_GET: ProcessGet")
            self.ProcessGet(identityToken)

        except FileNotFound:
            log.exception("HTTPTransferHandler::do_GET: File not found")
            self.send_error(404, "File not found")

        except NotAuthorized:
            log.exception("HTTPTransferHandler::do_GET: Not authorized")
            self.send_error(403, "Not authorized")

    def do_POST(self):
        #
        # Retrieve an identity token from the TransferServer. 
        # We pass the transfer handler through so that the
        # protocol-specific code in TransferServer can have access
        # to the connection-specific information in the handler
        # instance.
        #

        identityToken = self.server.GetIdentityToken(self)
        log.debug("HTTPTransferHandler::do_POST: POST identity token %s", identityToken)
        
        #
        # Split path into components, and verify
        # that it started with /. (path_parts[0] is
        # empty if that is the case).
        #

        log.debug("HTTPTransferHandler::do_POST: path=%s", self.path)

        path_parts = self.path.split('/')
        if path_parts[0] != '':
            log.debug("HTTPTransferHandler::do_POST: File not found")
            self.send_error(404, "File not found")
            return None

        #
        # This is always empty, so nuke it.
        #

        del path_parts[0]

        #
        # Check for /<prefix>/manifest
        #
        if len(path_parts) == 2 and path_parts[1] == "manifest":
            return self.ProcessManifest(path_parts[0], identityToken)

        #
        # Check for /<prefix>/<transfer_key>/<file_num>, designating a file upload.
        #

        if len(path_parts) == 3:
            prefix = path_parts[0]
            transfer_key = path_parts[1]
            file_num = path_parts[2]

            #
            # Ensure file_num is numeric
            #

            if not re.search("^\d+$", file_num):
                self.send_error(404, "File not found")
                return None

            #
            # This might be right. Pass control off
            # to the method that handles the details of
            # file uploads.
            
            return self.ProcessFileUpload(identityToken, prefix, transfer_key, file_num)
            
        #
        # Default.
        #
        self.send_error(404, "File not found")
        return None

    def ProcessFileUpload(self, identityToken, prefix, transfer_key, file_num):
        """
        Process a possible file upload.

        Look up the prefix to get the handler for that prefix.

        Look up the transfer key in the server to get the
        manifest.

        Look in the manifest for the metadata about the file.

        Do some preliminary checks (see if the Content-Length
        matches the size in the manifest, etc).

        Create a local file in the right location for the download.

        Copy the data from the socket into the file location, collecting
        a md5 checksum along the way.

        Verify the checksum, and nuke the file if it's wrong.
        """


        #
        # Find the transfer handler for this prefix.
        #
        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            log.debug("HTTPTransferHandler::ProcessFileUpload: Error, Path not found")
            self.send_error(404, "Path not found")
            return None

        #
        # Find the manifest information for this file.
        #

        file_info = self.server.LookupUploadInformation(transfer_key, file_num)
        log.debug("HTTPTransferHandler::ProcessFileUpload: Got this for %s: %s", file_num, file_info)

        #
        # Verify the filesize is what we expect
        #

        size = int(file_info['size'])
        content_len = int(self.headers['Content-Length'])
        if size != content_len:
            log.debug("HTTPTransferHandler::ProcessFileUpload: Error, Size in manifest(%s) != size in Content-Length(%s)", size, content_len)
            self.send_error(405, "Size in manifest != size in Content-Length")
            return None

        #
        # Query the handler for the pathname we shoudl use
        # to upload the file.
        #

        upload_file_path = transfer_handler.GetUploadFilename(identityToken, file_info)
        if upload_file_path is None:
            log.debug("HTTPTransferHandler::ProcessFileUpload: Error, Upload file not found")
            self.send_error(404, "Upload file not found")
            return None

        #
        # See if we have enough disk space for this. Put a 5% fudge factor on the space
        # available so we won't consume all.
        #

        try:
            upload_dir = os.path.dirname(upload_file_path)
            bytesFree = Platform.GetFilesystemFreeSpace(upload_dir)
            # bytesFree = 10
            if bytesFree is None:
                log.debug("HTTPTransferHandler::ProcessFileUpload: Cannot determine free space for %s", upload_Dir)
            else:
                if size > (0.95 * bytesFree):
                    log.info("HTTPTransferHandler::ProcessFileUpload: Upload failing: not enough disk space. Free=%d needed=%d",
                             bytesFree, size)
                    self.send_error(405, "Not enough disk space for upload")
                    return None
                else:
                    log.debug("HTTPTransferHandler::ProcessFileUpload: Allowing upload. Free spae=%d needed=%d",
                             bytesFree, size)
        except:
            log.exception("Platform.GetFilesystemFreeSpace threw exception")
            
        #
        # Open up destination file and initialize digest.
        #

        filename = file_info['name']
        fp = None

        try:
            log.debug("HTTPTransferHandler::ProcessFileUpload: opening upload file %s", upload_file_path)
            fp = open(upload_file_path, "wb")
        except EnvironmentError:
            log.exception("HTTPTransferHandler::ProcessFileUpload: Cannot open output file")
            self.send_error(405, "Cannot open output file")
            return None

        if fp is None:
            #
            # Wups, something bad happened.
            #

            log.debug("HTTPTransferHandler::ProcessFileUpload: Could not get upload filehandle for %s", filename)
            self.send_error(400, "Could not get upload filehandle for %s"
                            % filename)
            return None

        digest = md5.new()

        #
        # Start the transfer. We need to read exactly size bytes.
        #

        try:

            left = int(size)
            bufsize = 4096
            while left > 0:
                if left < 4096:
                    n = left
                else:
                    n = 4096

                buf = self.rfile.read(n)

                left -= len(buf)

                if buf == "":
                    break

                digest.update(buf)
                fp.write(buf)

                if left == 0:
                    break;
            fp.close()
            
        except EnvironmentError, e:
            log.exception("HTTPTransferHandler::ProcessFileUpload: Error on upload: %s" % (str(e)))
            self.send_error(400, "Error on upload: %s" % (str(e)))
            fp.close()
            return None

        #
        # Transfer done.
        # Compute the checksum and test against what was
        # advertised in the manifest.
        #

        checksum = digest.hexdigest()
        if checksum == file_info['checksum']:
            #
            # We got the file fine. Declare success.
            #
            # print "Checksms match!"

            self.send_response(200, "File transfer OK")
            self.end_headers()

        else:
            #
            # Something happened in the upload.
            #
            # Delete the file we created (TODO: figure out a clean
            # way to do this; we're not doing it at the moement)
            # and report an error.
            #
            
            log.warn("HTTPTransferHandler::ProcessFileUpload: Checksum mismatch on upload." )
            transfer_handler.CancelPendingUpload(filename)
            try:
                self.send_error(405, "Checksum mismatch on upload")
            except:
                log.warn("connection closed before could send_error for checksum mismatch")
            return None
            
        #
        # OKAY, we handled the upload properly.
        # Let the transfer handler know things are cool.
        #
        
        transfer_handler.CompleteUpload(identityToken, file_info)

    def ProcessManifest(self, prefix, identityToken):
        """
        Read the manifest from the input.

        We can't just let the ConfigParser read as it will read until EOF,
        and the server is leaving the socket open so it can write the
        transfer key back. So we need to obey the Content-Length header, reading
        that many bytes, stuff them into a StringIO, and pass that to the
        ConfigParser to parse.
        """

        #
        # First get the transfer handler for this prefix.
        #

        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            self.send_error(404, "Path not found")
            return None

        #
        # Woo, the int cast is important, as the header comes back
        # as a string and self.rfile.read() complains bitterly if it
        # gets a string as an argument.
        #
        
        read_len = int(self.headers['Content-Length'])
        buf = self.rfile.read(read_len)

        #
        # Construct the StringIO and read the manifest from it.
        #

        io = cStringIO.StringIO(buf)
    
        manifest = ConfigParser.ConfigParser()

        #
        # Upload status variables.
        #
        upload_okay = 1
        upload_error_list = []

        #
        # List of files to be uploaded; cache them
        # here so we don't have to run throught the manifest multiple times.
        #
        file_list = []

        #
        # We've created a ConfigParser object for the manifest.
        # All actions touching this manifest are in a
        # try block so that if there are *any* problems
        # with the manifest the transfer is aborted as failing.
        #
        try:
            manifest.readfp(io)
#            log.debug("have manifest")
#            log.debug(manifest.sections())
#            manifest.write(sys.stdout)

            #
            # Go through the potential files to be uploaded and ensure
            # that the datastore will be able to store them.
            #

            num_files = manifest.getint("manifest", "num_files")

            for file_num in range(0, num_files):

                info = {}
                for opt in manifest.options(str(file_num)):
                    info[opt] = manifest.get(str(file_num), opt)
                
                name = info['name']
                if not transfer_handler.CanUploadFile(identityToken, info):
                    log.info("Cannot upload file %s", name)
                    upload_okay = 0
                    upload_error_list.append("Upload error for file " + name)
                file_list.append(name)


        except ValueError, e:
            log.exception("HTTPTransferHandler::ProcessManifest: ConfigParser error.")
            self.send_error(400, "ConfigParser error: " + str(e))
            return None

        except ConfigParser.Error, e:
            log.exception("HTTPTransferHandler::ProcessManifest: ConfigParser error.")
            self.send_error(400, "ConfigParser error: " + str(e))
            return None

        #
        # Okay, since we got here okay the basic form of the request
        # was fine, so we can return a 200 for the POST itself.
        #

        self.send_response(200)
        self.send_header("Content-type", "text/plain")

        #
        # If all files can be transferred, go ahead and register
        # the manifest with the server, and request the file slots in the
        # datastore (they'll get marked as "pending").
        #
        
        #
        # Collect the response  into a string so we can
        # issue a Content-length header. The GSIHTTP code
        # appears to be happier with that, and it's good
        # practice anyway.
        #
        output = ""
        
        if upload_okay:
            transfer_key = self.server.RegisterManifest(manifest)

            for file in file_list:
                transfer_handler.AddPendingUpload(identityToken, file)

            output += "return_code: 0\n"
            output += "transfer_key: %s\n" % (transfer_key)

        else:
            output += "return_code: 1\n"
            for err in upload_error_list:
                output += "error_reason: %s\n" % (err)

        self.send_header("Content-length", str(len(output)))
        self.end_headers()
        self.wfile.write(output)
        return None

    def ProcessGet(self, identityToken):
        """
        Handle an HTTP GET.

        Extract the name of the file from the path; the path should be
        of the format /<prefix>/<filename>. Any other path is incorrect and
        will cause a FileNotFound exception to be raised.

        Call the datastore's OpenFile method to open the file and
        return a python file handle to it. This method can return FileNotFound
        and NotAuthorized exceptions; return an appropriate error code for each.
        """
        
        path = urllib.unquote(self.path)
        log.debug("HTTPTransferHandler::ProcessGet: has path: %s" %str(path))

        components = path.split('/')

        log.debug("HTTPTransferHandler::ProcessGet: After split component 0: %s, component 1: %s"%(components[0], components[1]))
        #
        # This is always empty, so nuke it.
        #

        del components[0]
        
        if len(components) != 2:
            raise FileNotFound

        prefix = components[0]
        path = components[1]

        log.info("HTTPTransferHandler::ProcessGet: Have path '%s', prefix='%s'", path, prefix)

        #
        # First get the transfer handler for this prefix.
        #

        transfer_handler = self.server.LookupPrefix(prefix)
        if transfer_handler is None:
            log.debug("HTTPTransferHandler::ProcessGet: has no transfer handler")
            self.send_error(404, "Path not found")
            return None

        fp = None
        try:
            log.debug("HTTPTransferHandler::ProcessGet: identitytoken: %s, path: %s" %(identityToken, path))
            ds_path = transfer_handler.GetDownloadFilename(identityToken, path)
            log.debug("HTTPTransferHandler::ProcessGet: Datastore path is %s" %ds_path)
            
            if ds_path is None:
                log.debug("HTTPTransferHandler::ProcessGet: Datastore path is none")
                raise FileNotFound(path)
            fp = open(ds_path, "rb")
        except FileNotFound, e:
            raise e
        except NotAuthorized, e:
            raise e
        except IOError:
            raise FileNotFound(path)

        #
        # Successfully opened the file to be transferred.
        # Write it to the output
        #
        if fp is not None:

            #
            # Figure out how big it is.
            #
            stat = os.stat(ds_path)
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Length", stat.st_size)
            self.end_headers()
            # print "Start copy to output"
            shutil.copyfileobj(fp, self.wfile)
            log.debug("HTTPTransferHandler::ProcessGet: Done copying")
            fp.close()

class TransferServer:
    """
    A TransferServer provides file upload and download services.

    It is intended to be subclassed to produce a protocol-specific
    transfer engine. This class handles the connection to the data
    store itself, and the manipulation of manifests.

    The transfer server provides services based on URL prefixes. That
    is, a client (um, a client in the same process as this object that
    is using its services to provide file upload and download
    capabilities) of the transfer server will register its interest in
    upload and downloads for some URL prefix. Access to files under
    that prefix is gated through the registered object.

    A local client registers a callback handler with the
    TransferServer. This handler will be invoked in the following
    situations:

    When a HTTP GET request occurs to initiate a file download, the
    handler's GetDownloadFilename(id_token, url_path) is invoked, and
    expects to be returned a pathname to the file on the local
    filesystem. The url_path does not include the client's transfer
    prefix. id_token is an identifier token representing the identity
    of the downloading client.

    When a HTTP POST request occurs with a transfer manifest, the
    manifest is parsed. For each file, the handler's
    CanUpload(id_token, file_info) callback is invoked.  The callback
    is to determine whether it can accept the upload of the file and
    return 1 if the server will accept the file, 0 otherwise. id_token
    is an identifier token representing the identity of the uploading
    client.

    file_info is a dictionary with the following keys:
    
    	name		Desired name of the file
        size		Size of the file in bytes
        checksum	MD5 checksum of the file

    If the manifest processing indicates that the file upload can
    continue, the transfer handler's AddPendingUpload(id_token,
    filename) method is invoked.

    When a HTTP POST request occurs with an actual file upload, the
    handler's GetUploadFilename(id_token, file_info) method is
    invoked. The handler validates the request and returns the
    pathname to which the file should be uploaded. id_token is an
    identifier token representing the identity of the uploading
    client.

    When the file upload is completed, the handler's
    CompleteUpload(id_token, file_info) method is invoked.
    """

    def __init__(self):

        #
        # upload_manifests is a dictionary mapping from transfer key
        # to the manifest for that transfer.
        #
        self.upload_manifests = {}

        #
        # The prefix_registry maps from a transfer prefix to
        # the handler for that prefix.
        #
        
        self.prefix_registry = {}

    def RegisterPrefix(self, prefix, handler):
        self.prefix_registry[prefix] = handler

    def LookupPrefix(self, prefix):
        if self.prefix_registry.has_key(prefix):
            log.debug("prefix registry has key = %s "% str(prefix))
            return self.prefix_registry[prefix]
        else:
            log.debug("prefix registry does not have key = %s "% str(prefix))
            return None
        
    def GetUploadDescriptor(self, prefix):
        """
        Return the upload descriptor for this transfer server.

        Must be implemented by the protocol-specific subclass.
        """
        
        raise NotImplementedError
                                 
    def GetDownloadDescriptor(self, prefix, path):
        """
        Return the download descriptor for this transfer server.

        Must be implemented by the protocol-specific subclass.
        """
        
        raise NotImplementedError

    def RegisterManifest(self, manifest):
        """
        A client has sent a POST to /<prefix>/manifest to initiate an upload.
        Manifest is the manifest that was transferred.

        Allocate a transfer key for this upload, save the manifest under
        that key, and return the key to the caller.

        """

        transfer_key = str(AccessGrid.GUID.GUID())

        #
        # GUIDs better be unique.
        #
        assert not self.upload_manifests.has_key(transfer_key)

        self.upload_manifests[transfer_key] = manifest
        return transfer_key

    def LookupUploadInformation(self, transfer_key, file_num):
        """
        Look up the information for transfer_key and file_num in the manifest.

        Raise a FileNotFound exception if it isn't there.

        Returns the list of attribute information for that file.

        """

        if not self.upload_manifests.has_key(transfer_key):
            raise FileNotFound

        manifest = self.upload_manifests[transfer_key]

        num_files = manifest.getint("manifest", "num_files")
        if int(file_num) < 0 or int(file_num) >= num_files:
            log.debug("invalid file_num '%s'", file_num)
            log.debug("Have manifest: ")
#            manifest.write(sys.stdout)
            raise FileNotFound

        file_num = str(file_num)

        if not manifest.has_section(file_num):
            log.debug("section not found for %s", file_num)
            raise FileNotFound

        info = {}
        for opt in  manifest.options(file_num):
            info[opt] = manifest.get(file_num, opt)
        return info

class IdentityToken:
    def __init__(self, dn):
        self.dn = dn

    def __repr__(self):
        cname = self.__class__.__name__
        return "%s(dn=%s)" % (cname, self.dn)

class HTTPIdentityToken(IdentityToken):
    pass

class GSIHTTPIdentityToken(IdentityToken):
    pass

class HTTPTransferServer(BaseHTTPServer.HTTPServer, TransferServer):
    """
    A HTTPTransferServer is a HTTP-based implementation of a TransferServer.

    Note that most of the work is done in HTTPTransferHandler.
    """

    def __init__(self, address = ('', 0)):
        TransferServer.__init__(self)
        BaseHTTPServer.HTTPServer.__init__(self, address, HTTPTransferHandler)

    def GetIdentityToken(self, transferHandler):
        """
        Create an identity token for this HTTP-based transfer.

        The token will contain the X-Client-DN header if there is one.
        """

        try:
            dn = transferHandler.headers.getheader("X-Client-DN")
        except KeyError:
             dn = None

        wxLogDebug("GetIdentityToken returns dn = %s" %dn)

        return HTTPIdentityToken(dn)
        

    def GetUploadDescriptor(self, prefix):
        return urlparse.urlunparse(("http",
                                 "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                 prefix,    # Path
                                 "", "", ""))
                                 
    def GetDownloadDescriptor(self, prefix, path):
        return urlparse.urlunparse(("http",
                                    "%s:%d" % (GetHostname(), self.socket.getsockname()[1]),
                                    "%s/%s" % (prefix, urllib.quote(path)),
                                    "", "", ""))
                                 
    def run(self):
        self.done = 0
        self.server_thread = threading.Thread(target = self.thread_run,
                                              name = 'TransferServer')
        self.server_thread.start()

    def stop(self):
        self.done = 1

    def thread_run(self):
        """
        thread_run is the server thread's main function.
        """

        while not self.done:
            self.handle_request()

class GSIHTTPTransferServer(io.GSITCPSocketServer, TransferServer):
    """
    A GSIHTTPTransferServer is a Globus-enabled HTTP-based implementation of a TransferServer.
n
    Note that most of the work is done in HTTPTransferHandler.

    This implementation uses a pool of worker threads to handle the requests.
    We could just use SocketServer.ThreadingMixIn, but I worry about 
    an unbounded number of incoming request overloading the server.

    self.requestQueue is a Queue object. Each worker thread runs __WorkerRun(),
    which blocks on a get on teh request queue.

    Incoming requests are just placed on the queue.
    """

    def __init__(self, address = ('', 0), numThreads = 1, sslCompat = 0):
        TransferServer.__init__(self)

        self.done = 0
        
        self.numThreads = numThreads
        self.requestQueue = Queue.Queue()
        self._CreateWorkers()

        #
        # For now, allow all connections.
        #

        def auth_cb(server, g_handle, remote_user, context):
            # print "Got remote ", remote_user
            return 1
        # tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()

        if sslCompat:
            log.debug("creating ssl compatible server")
            tcpAttr = Utilities.CreateTCPAttrCallbackAuthSSL(auth_cb)
        else:
            tcpAttr = Utilities.CreateTCPAttrCallbackAuth(auth_cb)
        io.GSITCPSocketServer.__init__(self, address, HTTPTransferHandler,
                                    None, None, tcpAttr = tcpAttr)

    def _CreateWorkers(self):
        self.workerThread = {}
        self.startLock = threading.Lock()
        for workerNum in range(self.numThreads):
            log.debug("Creating thread %d", workerNum)
            self.workerThread[workerNum] = threading.Thread(target = self.__WorkerRun,
                                                            name = 'TransferWorker',
                                                            args = (workerNum,))
            self.startLock.acquire()
            log.debug("Starting thread %d", workerNum)
            self.workerThread[workerNum].start()
            log.debug("Waiting thread %d", workerNum)
            self.startLock.acquire()
            self.startLock.release()
        log.debug("Done creating workers")

    def __WorkerRun(self, workerNum):
        log.debug("Worker %d starting", workerNum)
        self.startLock.release()

        while not self.done:
            cmd = self.requestQueue.get(1)
            log.debug("Worker %d gets cmd %s", workerNum, cmd)
            cmdType = cmd[0]
            if cmdType == "quit":
                break
            elif cmdType == "request":
                request = cmd[1]
                client_address = cmd[2]
                log.debug("handle request '%s' '%s'", request, client_address)
                try:
                    self.finish_request(request, client_address)
                    self.close_request(request)
                except:
                    log.exception("Worker %d: Request handling threw exception", workerNum)
        log.debug("Worker %d exiting", workerNum)
            

    def process_request(self, request, client_address):
        log.debug("process_request: request=%s client_address=%s", request, client_address)
        self.requestQueue.put(("request", request, client_address))

    def GetIdentityToken(self, transferHandler):
        """
        Create an identity token for this GSIHTTP-based transfer.

        It contains the DN from the connection's security context.
        """

        context = transferHandler.connection.get_security_context()
        initiator, acceptor, valid_time, mechanism_oid, flags, local_flag, open_flag = context.inquire()
        dn = initiator.display()

        return GSIHTTPIdentityToken(dn)
        
    def _GetListenPort(self):
        return self.port

    def GetUploadDescriptor(self, prefix):
        return urlparse.urlunparse(("https",
                                 "%s:%d" % (GetHostname(), self._GetListenPort()),
                                 prefix,
                                 "", "", ""))
                                 
    def GetDownloadDescriptor(self, prefix, path):
        return urlparse.urlunparse(("https",
                                    "%s:%d" % (GetHostname(), self._GetListenPort()),
                                    "%s/%s" % (prefix, urllib.quote(path)),
                                    "", "", ""))
                                 
    def run(self):
        self.done = 0
        self.server_thread = threading.Thread(target = self.thread_run,
                                              name = 'TransferServer')
        self.server_thread.start()

    def stop(self):
        self.done = 1
        for workerNum in range(self.numThreads):
            self.requestQueue.put("quit")
        self.server_close()

    def thread_run(self):
        """
        thread_run is the server thread's main function.
        """

        while not self.done:
            try:
                self.handle_request()
            except GSITCPSocketException:
                log.info("GSIHTTPTransferServer: GSITCPSocket, interrupted I/O operation, most likely shutting down. ")
                

def HTTPDownloadFile(identity, download_url, destination, size, checksum,
                     progressCB = None):
    return HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                                  identity, progressCB)

def GSIHTTPDownloadFile(download_url, destination, size, checksum,
                        progressCB = None):
    """
    Download a file with GSI HTTP.

    Define a local connection class so we can poke about at the
    tcp attributes here.
    """
    
    def GSIConnectionClass(host):
        tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()
        return io.GSIHTTPConnection(host, tcpAttr = tcpAttr)

    return HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                                  None, progressCB, GSIConnectionClass)
                                  
def HTTPFamilyDownloadFile(download_url, destination, size, checksum,
                           identity = None,
                           progressCB = None,
                           connectionClass = httplib.HTTPConnection):
    """
    Download the given url, as user identified by identity,
    and place the new file in destination. 

    We assume the caller has determined that overwriting destination
    is valid, so we do not check for its existence.

    progressCB is a callable that will be invoked with two arguments: the number
    of bytes transferred so far, and a flag that is passed as 1 if the transfer
    is completed. If the call to progressCB returns true, the user has cancelled
    the transfer.

    """

    dest_fp = open(destination, "wb")

    headers = {}
    if identity is not None:
        headers["X-Client-DN"] = identity

    url_info = urlparse.urlparse(download_url)
    host = url_info[1]
    path = url_info[2]
   
    log.debug("Host %s, path %s", host, path)

    log.debug("Connect to %s", host)
    conn = connectionClass(host)

    log.debug("Downloading %s into %s", download_url, destination)

    #
    # We want strict enabled here, otherwise the empty
    # result we get when querying a gsihttp server with an http
    # client results in a valid response, when it should have failed.
    #

    try:
        conn.strict = 1
        log.debug("before connect reqest path %s, headers %s" %(path, str(headers)))
        conn.request("GET", path, headers = headers)
        log.debug("after connect reqest")

        log.debug("request sent to %s", conn)

        resp = conn.getresponse()

        log.debug("response is %s", resp)
        log.debug("Request got status %s", resp.status)
    except httplib.BadStatusLine:
        log.exception("DataStore::HTTPFamilyDownloadFile: bad status from http (server type mismatch?)")
        raise DownloadFailed("bad status from http (server type mismatch?)")
    except:
        log.exception("DataStore::HTTPFamilyDownloadFile: Unknown reason")
        raise DownloadFailed("Unknown reason")

    if int(resp.status) != 200:
        raise DownloadFailed(resp.status, resp.reason)

    try:
        hdr = resp.getheader("Content-Length")
        log.debug("Got hdr %s", hdr)
        log.debug(resp.msg.headers)
        hdr_size = int(hdr)
    except (TypeError, KeyError):
        raise DownloadFailed("server must provide a valid content length")
    except:
        raise DownloadFailed("Unknown reason")

    #
    # See if the file size is what we expect, only if
    # the user has passed in a size.
    #
    if size is not None:
        size = int(size)

        log.debug("got size %s", hdr_size)

        if hdr_size != size:
            raise DownloadFailed("Size mismatch: server says %d, metadata says %d" %
                                 (hdr_size, size))

    #
    # Set up for download
    #

    if checksum is not None:
        digest = md5.new()
    else:
        digest = None
    bytes_left = hdr_size
    buf_size = 4096

    #
    # and GO
    #

    while bytes_left > 0:
        if bytes_left > buf_size:
            bytes_to_read = buf_size
        else:
            bytes_to_read = bytes_left

        # print "Reading %d bytes" % (bytes_to_read)
        buf = resp.read(bytes_to_read)

        if buf == "":
            log.debug("FILE TOO SHORT in download")
            dest_fp.close()
            raise DownloadFailed("End of file before %d bytes read" % (size))

        if digest is not None:
            digest.update(buf)
        #
        # Send a callback if we have a valid callback reference.
        # Handle a cancellation of the transfer.
        #
        if progressCB is not None:
            cancel = progressCB(size - bytes_left, 0)
            if cancel:
                log.debug("DL got cancel!")
                dest_fp.close()
                # remove local file since it was not completed.
                if os.path.exists(destination):
                    os.remove(destination)
                    log.debug("removed file that didn't finish downloading: " + str(destination))
                raise DownloadFailed("Cancelled by user")
        
        dest_fp.write(buf)

        bytes_left -= len(buf)

    #
    # Done reading. Check the checksum and flag an
    # exception if it doesn't match.
    #
    # for now, leave the file in place; need to
    # figure out the right semantics for this case.

    dest_fp.close()


    if progressCB is not None:
        progressCB(size, 1)

    if checksum is not None:
        download_digest = digest.hexdigest()
        if download_digest != checksum:
            raise DownloadFailed("Checksum mismatch on download: download was %s, metadata was %s"
                                 % (download_digest, checksum))
        else:
            log.debug("Download success! %s", download_digest)

def HTTPUploadFiles(identity, upload_url, file_list, progressCB):
    """
    Upload the given list of files to the server using HTTP.

    Identity is the DN of the client submitting the files.

    progressCB is a callback that will be invoked this way:

       progressCB(filename, bytes_sent, total_bytes, file_done, transfer_done)

    filename is the file to which the progress update applies
    bytes_sent and total_bytes denote the file's progress
    file_done is set when the given file upload is complete
    transfer_done is set when the entire transfer is complete

    If progressCB returns true, the transfer is to be cancelled.

    """

    uploader = HTTPUploadEngine(identity, upload_url, progressCB)
    uploader.UploadFiles(file_list)

def GSIHTTPUploadFiles(upload_url, file_list, progressCB):
    """
    Upload the given list of files to the server using HTTP.

    progressCB is a callback that will be invoked this way:

       progressCB(filename, bytes_sent, total_bytes, file_done, transfer_done)

    filename is the file to which the progress update applies
    bytes_sent and total_bytes denote the file's progress
    file_done is set when the given file upload is complete
    transfer_done is set when the entire transfer is complete

    If progressCB returns true, the transfer is to be cancelled.

    """

    def GSIConnectionClass(host):
        tcpAttr = Utilities.CreateTCPAttrAlwaysAuth()
        return io.GSIHTTPConnection(host, tcpAttr = tcpAttr)

    uploader = HTTPUploadEngine(None, upload_url, progressCB,
                                GSIConnectionClass)
    uploader.UploadFiles(file_list)

class HTTPUploadEngine:
    """
    An HTTPUploadEngine bundles up the functionality need to implement
    HTTPUploadFiles.
    """
    
    def __init__(self, identity, upload_url, progressCB,
                 connectionClass = httplib.HTTPConnection):
        self.identity = identity
        self.upload_url = upload_url

        self.connectionClass = connectionClass

        if progressCB is not None:
            if not callable(progressCB):
                raise UploadFailed("Progress callback not a callable object")
        self.progressCB = progressCB

    def UploadFiles(self, file_list):
        """
        Upload the list of files to the datastore.

        We only support files, not directories, so do a pass over
        them to ensure that they are all files.
        """

        log.debug("Upload: check files")

        for file in file_list:
            if not os.path.exists(file):
                raise FileNotFound(file)
            elif not os.path.isfile(file):
                raise NotAPlainFile(file)

        log.debug("Upload: create manifest")
        (manifest, file_info) = self.constructManifest(file_list)

        log.debug("Upload: Created manifest")

        try:
            parsed = urlparse.urlparse(self.upload_url)
            host = parsed[1]
            base_path = parsed[2]

            log.debug("upload mainfest: host='%s' base_path='%s'", host, base_path)

            #
            # We want strict enabled here, otherwise the empty
            # result we get when querying a gsihttp server with an http
            # client results in a valid response, when it should have failed.
            #
            conn = self.connectionClass(host)
            conn.strict = 1
            
            transfer_key = self.uploadManifest(conn, base_path, manifest)
            
            log.debug("Manifest upload returns '%s'", transfer_key)
        
            for idx, file, basename in file_info:
                conn = self.connectionClass(host)
                conn.strict = 1
                url_path = string.join([base_path, transfer_key, str(idx)], "/")
                self.uploadFile(conn, file, url_path)

            if self.progressCB is not None:
                self.progressCB('', 0, 0, 0, 1)

        except UploadFailed, e:
             log.exception("Upload failed.")
             if self.progressCB is not None:
                 self.progressCB('', 0, 0, 0, 1)

             raise e

    def uploadFile(self, conn, file, url_path):
        """
        Upload file to the HTTPConnection conn, placing it at url_path.

        We open the file for reading, and read from it in chunks, sending
        the data to the HTTP connection.
        """

        #
        # Determine the length of the file.
        # The paranoid part of me worries about a race condition
        # between doing the stat and opening the file, and wishes
        # for the unix fstat() call. Probably not a real-life problem tho.
        #

        st = os.stat(file)
        size = st.st_size

        #
        # Open file (do it now before we waste the server's time
        # on a connection that might fail if the file doesn't open).
        #
        # Important to remember the "b" in the spec, otherwise we will
        # have problems on Windows.
        #

        fp = open(file, "rb")

        #
        # Fire up the connection and send headers
        #

        log.debug("Send headers")

        conn.connect()
        conn.putrequest("POST", url_path)
        conn.putheader("X-Client-DN", self.identity)
        conn.putheader("Content-type", "application/octet-stream")
        conn.putheader("Content-Length", size)
        conn.endheaders()

        #
        # Now we can stream the file across.
        #

        if self.progressCB is not None:
            self.progressCB(file, 0, size, 0, 0)

        n_sent = 0

        log.debug("sending file")

        try:
            left = 0
            while size - n_sent > 0:
                buf = fp.read(4096)
                if buf == "":
                    break
                conn.send(buf)
                n_sent += len(buf)
                if self.progressCB is not None:
                    cancel = self.progressCB(file, n_sent, size, 0, 0)
                    if cancel:
                        log.debug("UL got cancel!")
                        conn.close()
                        raise UploadFailed("Cancelled by user")

        except socket.error, e:
            if self.progressCB is not None:
                self.progressCB(file, n_sent, size, 1, 1)
            log.debug("Hm, got a socket error.")
            conn.close()
            raise UploadFailed(e[1])

        if self.progressCB is not None:
            self.progressCB(file, n_sent, size, 1, 0)
        #
        # All done!
        #

        resp = conn.getresponse()

        log.debug("Upload got status %s", resp.status)

        conn.close()
        
    def uploadManifest(self, conn, base_path, manifest):
        """
        Upload the manifest to the upload server.

        This is done with a POST to the /manifest path.
        The server will return the string "transfer_key: <keystring>"

        """

        # conn.debuglevel = 10
        headers = {"X-Client-DN": self.identity}

        upload_url = string.join([base_path, "manifest"], "/")
        
        conn.request("POST", upload_url, manifest, headers)
        resp = conn.getresponse()

        log.debug("post returns %s", resp)

        if resp.status != 200:
            raise UploadFailed((resp.status, resp.reason))

        transfer_key = None
        error_reasons = []

        log.debug("Reading response, headers are %s", resp.msg.headers)
        result = resp.read()
        
        return_code = -1

        for tline in result.split("\n"):
            log.debug("got tline <%s>", tline)
            if tline == "":
                continue
            m = re.search("^(\S+):\s+(.*)", tline)

            if m is None:
                raise UploadFailed("Invalid line in manifest return: %s" % (tline))

            key = m.group(1)
            value = m.group(2)

            if key == "transfer_key":
                transfer_key = value
            elif key == "return_code":
                return_code = int(value)
            elif key == "error_reason":
                error_reasons.append(value)

        if return_code == 0:
            return transfer_key
        else:
            log.debug("Upload failed:")
            for r in error_reasons:
                log.debug("   %s", r)
            raise UploadFailed((return_code, error_reasons))
        
    
    def constructManifest(self, file_list):
        """
        Construct a transfer manifest from the given file list.
        """

        manifest = ConfigParser.ConfigParser()

        manifest.add_section("manifest")

        manifest.set("manifest", "num_files", len(file_list))

        #
        # First iterate through the files computing the shortname.
        # Ensure that we don't have any duplicates.
        # Also check to ensure that each is a normal file, not
        # a directory or anything goofy.
        #

        file_map = {}
        file_info = []
        idx = 0
        for file in file_list:

            if not os.path.exists(file):
                raise FileNotFound(file)
            elif not os.path.isfile(file):
                raise NotAPlainFile(file)

            base = os.path.basename(file)

            if file_map.has_key(base):
                raise DuplicateFile((file, file_map[base]))
            else:
                file_map[base] = file

            file_info.append((idx, file, base))
            idx += 1

        del file_map

        #
        # Now compute checksums and complete the manifest
        #

        for idx, file, base in file_info:

            log.debug("Checksum %s", file)

            s = os.stat(file)

            fp = open(file, "rb")

            digest = md5.new()
            while 1:
                buf = fp.read(32768)
                if not buf:
                    break
                digest.update(buf)
            fp.close()

            section = str(idx)
            manifest.add_section(section)
            manifest.set(section, "name", base)
            manifest.set(section, "size", s.st_size)
            manifest.set(section, "checksum", digest.hexdigest())

        #
        # Retrieve the manifest as a string
        #
        io = cStringIO.StringIO()
        manifest.write(io)
        mstr = io.getvalue()
        io.close()

        return (mstr, file_info)

if __name__ == "__main__":

    logger = logging.getLogger("AG")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.debug)

    from AccessGrid.Events import Event
    
    #
    # Test DataDescriptionContainer
    # 
  
    class FAKEEvent:
        '''
        To test DataDescriptionContainer
        '''
        ADD_DATA = 1
        REMOVE_DATA = 2
        UPDATE_DATA = 3
        
        def __init__(self, arg1, arg2, arg3):
            pass
        
        def Distribute(self, id, event):
            return "DISTRIBUTE"

        def Send(self, event):
            pass
        
    dContainer = DataDescriptionContainer(FAKEEvent(1,2,3), 5)
    d1 = DataDescription("file1")
    d1.description = "noaoin"
    d2 = DataDescription("file2")
    d3 = DataDescription("file3")
    dContainer.AddData(d1)
    dContainer.AddData(d2)
    dContainer.AddData(d3)

    print '*** Test AddData'
    
    dDict = dContainer.GetDataDescriptions()
      
    if (d1 in dDict) & (d2 in dDict) & (d3 in dDict):
        print "OK!"
    else:
        print "FAILED! AddData does not work as expected, should include 'file1', 'file2', 'file3'", dDict

    print '*** Test RemoveData'
    
    dContainer.RemoveData(d2)
    dDict = dContainer.GetDataDescriptions()
    if d2.name in dDict:
        print "FAILED! RemoveData does not work as expected"
    else:
        print "OK!"

    print '*** Test UpdateData'
   
    d4 = DataDescription("file1")
    d4.description = "test"
    dContainer.UpdateData(d4)
    dDict = dContainer.GetDataDescriptions()
    flag = 1
    for x in dDict:
        if x.name == d4.name and x.description == "test":
            flag = 0
            print "OK!"

    if flag:
        print "FAILED! UpdateData does not work as expected ", dDict
      
    print '*** Test GetData'
        
    if dContainer.GetData(d3.name) == d3:
        print "OK!"         
        
    else:
        print "FAILED! GetData does not work as expected"

    print '*** Test AsINIBlock'          
    print dContainer.AsINIBlock()
            
    #
    # Test DataStore
    #

    print '------------ Test DataStore'
    
    class TestCallbackClass:
        def __init__(self):
            self.data = {}
            
        def GetData(self, filename):
            
            if self.data.has_key(filename):
                d = self.data[filename]
            else:
                d = None
            log.debug("GetData %s returning %s", filename, d)
            return d

        def UpdateData(self, desc):
            self.data[desc.GetName()] = desc
            log.debug("UpdateData: %s", desc)

        def AddData(self, desc):
            self.data[desc.GetName()] = desc
            log.debug("AddData: %s", desc)

    v = TestCallbackClass()
    ds = DataStore(v, "./temp", "snap", 1)
    s = GSIHTTPTransferServer(('', 9011))

    class Handler:
        def GetDownloadFilename(self, id_token, url_path):
            log.debug("Get download: id='%s' path='%s'", id_token, url_path)
            return r"c:\temp\junoSetup.exe"

        def GetUploadFilename(self, id_token, file_info):
            log.debug("Get upload filename for %s %s", id_token, file_info)
            return os.path.join("c:\\", "temp", "uploads", file_info['name'])

        def CanUploadFile(self, id_token, file_info):
            log.debug("CanUpload: id=%s file_info=%s", id_token, file_info)
            return 1

        def AddPendingUpload(self, id_token, filename):
            log.debug("AddPendingUpload: %s %s", id_token, filename)

        def CompleteUpload(self, id_token, file_info):
            log.debug("CompleteUpload %s %s", id_token, file_info)

    ds.SetTransferEngine(s)

    prefix = "test"
    s.RegisterPrefix(prefix, Handler())

    log.debug("%s", s.GetDownloadDescriptor(prefix, "JunoSetup.exe"))
    log.debug("%s", s.GetUploadDescriptor(prefix))

    s.run()

    try:
        while 1:
            time.sleep(.1)

    except:
        os._exit(0)


