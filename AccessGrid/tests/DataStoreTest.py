#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        DataStoreTest.py
# Purpose:     Test for data store.
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: DataStoreTest.py,v 1.1 2003-11-20 20:52:04 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#---------------------------------------------------------------------------

from AccessGrid.GUID import GUID
import logging, logging.handlers
import os, time
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.DataStore import GSIHTTPTransferServer
from AccessGrid import DataStore

class StartTest:
    '''
    Creates a transfer engine and a datastore. Also, creates DataStoreClient that
    uses datastore method to test datastore.
    '''
    
    def __init__(self):
        self.dataPort = 9988
        self.dataStoreClientList = []
        self.uniqueId = GUID()
        
        # Start transfer service
        self.dataTransferServer = GSIHTTPTransferServer(('',
                                                         int(self.dataPort)),
                                                        numThreads = 4,
                                                        sslCompat = 0)
        self.dataTransferServer.run()
                
        self.CreateDataStore()

        # Basic test
        d = DataStoreClient(self.dataStore, 0)
        d.StartDataOperations()
               
        # Thread test
        #self.StartDataStoreClients()
      
        self.ShutDown()

    def CreateDataStore(self):
        self.dataStorePath  = 'DataStoreTestDir'
        #self.dataStorePath = os.path.join(self.dataStoreLocation, str(self.uniqueId))
        if not os.path.exists(self.dataStorePath):
            try:
                os.mkdir(self.dataStorePath)
            except OSError:
                self.dataStorePath = None

        self.dataStore = DataStore.DataStore(self, self.dataStorePath, str(self.uniqueId),
                                             self.dataTransferServer)

    #def StartDataStoreClients(self):
    #    '''Creates several data store clients, and starts methods in threads to
    #    stress test datastore'''
    #    
    # Create data store clients
    #    index = 1
    #    for client in range(nrOfClients):
    #        d = DataStoreClient(self.dataStore, index)
    #        self.dataStoreClientList.append(d)
    #        index = index + 1
    #
    #    self.threadList = []
    #    # Start data operations in threads
    #    for d in self.dataStoreClientList:
    #        thread = threading.Thread(target = d.StartDataStoreOperations)
    #        self.threadList.append(thread)
    #    
    #    for thread in self.threadList:
    #        thread.start()
    #        
    #    # Join threads
    #    for thread in self.threadList:
    #        thread.join()
    
    def ShutDown(self):
        '''Stop server and datastore'''
        self.dataTransferServer.stop()
        self.dataStore.Shutdown()


    def AddData(self, data):
        '''Callback for datastore'''
        pass

    def UpdateData(self, data):
        '''Callback for datastore'''
        pass

    def GetData(self):
        '''Callback for datastore'''
        return none

class DataStoreClient:
    '''
    Calls datastore methods to test datastore.
    '''
    def __init__(self, dataStore, index):
        '''
        Start datastoreclient
        **Arguments**
        *datastore* DataStore to test
        *index* Unique identifier
        '''
        self.dataStore = dataStore
        self.name = 'datastore'+str(index)
                
    def StartDataOperations(self):
        '''
        Calls datastore methods.
        '''
        uploadFile = 'dataStoreTest.txt'
        localFile = 'dataStoreTest2.txt'

        #
        # GetUploadDescriptor
        #
        self.uploadUrl = self.dataStore.GetUploadDescriptor()
        print self.name, 'GetUploadDescriptor', self.uploadUrl, '\n'

        #
        # GetDataDescriptions
        #
        dList = self.dataStore.GetDataDescriptions()
        print self.name, 'GetDataDescriptions', dList,'\n'

        #
        # GSIHTTPUploadFiles
        #
        print self.name, 'GSIHTTPUploadFiles ', uploadFile,'\n'

        try:
            DataStore.GSIHTTPUploadFiles(self.uploadUrl, [uploadFile], None)
        except DataStore.UploadFailed, e:
            log.exception(self.name+" Upload failed")

        #
        # GetDescription
        #
        data = self.dataStore.GetDescription(uploadFile)
        print self.name, 'GetDescription ', uploadFile, data,'\n'

        try:
            DataStore.GSIHTTPDownloadFile(data.uri, localFile, data.size, data.checksum)
        except DataStore.DownloadFailed, e:
            log.exception(self.name+"Download failed")

        #
        # UploadLocalFiles
        #      
        print self.name, 'UploadLocalFiles',localFile,'\n'
        self.dataStore.UploadLocalFiles([localFile], 'dn', 1)
        data1 = self.dataStore.GetDescription(localFile)
        data2 = self.dataStore.GetDescription(uploadFile)
        print self.name, 'GetDescription', localFile, data1,'\n'

        #
        # LoadPersistentInfo()
        # 
        print self.name,'LoadPersistentInfo()','\n'
        self.dataStore.LoadPersistentInfo()

        #
        # RemoveFiles
        # 
        print self.name, 'RemoveFiles', data1.name, data2.name,'\n'
        self.dataStore.RemoveFiles([data1, data2])

        #
        # AsINIBlock
        # 
        block = self.dataStore.AsINIBlock()
       

def SetLogging():
    debugMode = 1
    logFile = None
    
    log = logging.getLogger("AG")
    log.setLevel(logging.WARN)
    
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "Test.log")
    else:
        logname = logFile
        
    hdlr = logging.FileHandler(logname)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)
    
    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)
       
if __name__ == "__main__":

    SetLogging()
    StartTest()
    
