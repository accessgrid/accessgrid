#-----------------------------------------------------------------------------
# Name:        AGServicePackageRepository.py
# Purpose:     
#
# Created:     2004/03/30
# RCS-ID:      $Id: AGServicePackageRepository.py,v 1.9 2004-05-04 18:57:49 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import threading

from AccessGrid.Toolkit import Application
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.Types import AGServicePackage, InvalidServicePackage
from AccessGrid import DataStore
from AccessGrid import Log

log = Log.GetLogger("ServicePackageRepo")

class AGServicePackageRepository:
    """
    AGServicePackageRepository encapsulates knowledge about local service
    packages and avails them to clients (service managers) via http(s)
    """

    def __init__( self, servicesDir, port=0, prefix=None, secure=1):
        self.servicesDir = servicesDir
        self.port = port
        self.secure = secure
        
        self.baseUrl = ''
        self.s = None
        self.running = 0
        self.prefix = prefix

    def Start(self):
        # Start the transfer server
        
        # if port is 0, find a free port
        if self.port == 0:
            self.port = NetworkAddressAllocator().AllocatePort()

        # Define base url
        hn = Application.instance().GetHostname()
        if self.prefix is None:
            self.prefix = "packages"
        
        # Start the transfer server
        if self.secure:
            self.baseUrl = 'https://%s:%d/%s/' % ( hn, self.port, self.prefix )
            self.s = DataStore.GSIHTTPTransferServer((hn, self.port))
        else:
            self.baseUrl = 'http://%s:%d/%s/' % ( hn, self.port, self.prefix )
            self.s = DataStore.HTTPTransferServer((hn, self.port))

        self.s.RegisterPrefix(self.prefix, self)

        threading.Thread( target=self.s.run,
                          name="PackageRepo TransferServer" ).start()
        self.running = 1
        log.debug("Started AGServicePackageRepository Transfer Server at: %s",
                  self.baseUrl)

    def Stop(self):
        if self.running:
            self.running = 0
            self.s.stop()

    def GetDownloadFilename(self, id_token, url_path):
        """
        Return the path to the file specified by the given url path
        """
        filename = os.path.join(self.servicesDir, url_path)

        # Catch request for non-existent file
        if not os.access(filename,os.R_OK):
            log.info("Attempt to download non-existent file: %s" % (filename) )
            raise DataStore.FileNotFound(filename)
        return filename

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

        servicePackages = self.GetServicePackages()
        for servicePackage in servicePackages:
            serviceDescriptions.append(servicePackage.GetServiceDescription())

        return serviceDescriptions
        
    def GetServicePackages( self ):
        """
        Read service packages from local directory
        """
        servicePackages = []

        invalidServicePackages = 0

        # Catch non-existent service directory
        if not os.path.exists(self.servicesDir):
            log.info("Non-existent service directory")
            return []

        files = os.listdir(self.servicesDir)
        for file in files:
            if file.endswith('.zip'):
                try:
                    servicePkg = AGServicePackage(os.path.join(self.servicesDir,file))
                    
                    # Minimal test to validate service package
                    servicePkg.GetServiceDescription()
                    
                    servicePackages.append(servicePkg)
                except:
                    invalidServicePackages += 1
                    
        if invalidServicePackages:
            log.info("%d invalid service packages skipped", invalidServicePackages)

        return servicePackages
            
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
        
    
    




