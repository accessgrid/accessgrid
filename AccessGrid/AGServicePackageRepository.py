#-----------------------------------------------------------------------------
# Name:        AGServicePackageRepository.py
# Purpose:     
#
# Created:     2004/03/30
# RCS-ID:      $Id: AGServicePackageRepository.py,v 1.2 2004-04-06 00:52:43 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import threading

from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.Types import AGServicePackage, InvalidServicePackage
from AccessGrid import DataStore
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid import Log

log = Log.GetLogger("ServicePackageRepo")

class AGServicePackageRepository:
    """
    AGServicePackageRepository encapsulates knowledge about local service
    packages and avails them to clients (service managers) via http(s)
    """

    def __init__( self, servicesDir, port=0):
        self.servicesDir = servicesDir
        self.port = port
        
        self.baseUrl = ''
        self.s = None
        self.running = 0

    def Start(self):
        #
        # Start the transfer server
        #
        
        # if port is 0, find a free port
        if self.port == 0:
            self.port = NetworkAddressAllocator().AllocatePort()

        # 
        # Define base url
        #
        hn = SystemConfig.instance().GetHostname()
        prefix = "packages"
        self.baseUrl = 'https://%s:%d/%s/' % ( hn, self.port, prefix )
        
        # Start the transfer server
        self.s = DataStore.GSIHTTPTransferServer(('', self.port)) 
        self.s.RegisterPrefix(prefix, self)
        threading.Thread( target=self.s.run, name="PackageRepo TransferServer" )
        self.running = 1

    def Stop(self):
        if self.running:
            self.running = 0
            self.s.stop()

    def GetDownloadFilename(self, id_token, url_path):
        """
        Return the path to the file specified by the given url path
        """
        file = os.path.join(self.servicesDir, url_path)

        # Catch request for non-existent file
        if not os.access(file,os.R_OK):
            log.info("Attempt to download non-existent file: %s" % (file) )
            raise DataStore.FileNotFound(file)
        return file

    def GetPackageUrl( self, file ):
        return self.baseUrl + file
        
    def GetServiceDescription(self, file):
        servicePackage = AGServicePackage( os.path.join(self.servicesDir,file) )
        serviceDesc = servicePackage.GetServiceDescription()
        serviceDesc.servicePackageUri = self.GetPackageUrl(file)
        return serviceDesc
    

    def GetServiceDescriptions( self ):
        """
        Read service packages from local directory and build service descriptions
        """
        serviceDescriptions = []

        invalidServicePackages = 0

        # Catch non-existent service directory
        if not os.path.exists(self.servicesDir):
            return

        files = os.listdir(self.servicesDir)
        for file in files:
            if file.endswith('.zip'):
                try:
                    serviceDesc = self.GetServiceDescription(file)
                    serviceDescriptions.append( serviceDesc )
                except:
                    invalidServicePackages += 1
                    
        if invalidServicePackages:
            log.info("%d invalid service packages skipped", invalidServicePackages)

        return serviceDescriptions
            


if __name__ == "__main__":

    from AccessGrid.Platform.Config import UserConfig, AGTkConfig
    
    # Get descriptions of service files
    servicesDir = os.path.join(AGTkConfig.instance().GetConfigDir(),"services")
    packageRepo = AGServicePackageRepository(servicesDir)
    print "** System services"
    serviceDescList = packageRepo.GetServiceDescriptions()
    for serviceDesc in serviceDescList:
        print " ", serviceDesc.name
    
    # Get descriptions of service files
    servicesDir = os.path.join(UserConfig.instance().GetConfigDir(),"local_services")
    packageRepo = AGServicePackageRepository(servicesDir)
    print "** User local services"
    serviceDescList = packageRepo.GetServiceDescriptions()
    for serviceDesc in serviceDescList:
        print " ", serviceDesc.name
        
    
    




