#-----------------------------------------------------------------------------
# Name:        AGServicePackageRepository.py
# Purpose:     
#
# Created:     2004/03/30
# RCS-ID:      $Id: AGServicePackageRepository.py,v 1.12 2004-07-28 22:43:35 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os

from AccessGrid.Types import AGServicePackage, InvalidServicePackage
from AccessGrid import Log

log = Log.GetLogger("ServicePackageRepo")

class AGServicePackageRepository:
    """
    AGServicePackageRepository encapsulates knowledge about local service
    packages and avails them to clients (service managers) via http(s)
    """

    def __init__( self, servicesDir, port=0, prefix=None):
        self.servicesDir = servicesDir

    def GetServicesDir(self):
        return self.servicesDir
        
    def GetServiceDescription(self, file):
        servicePackage = AGServicePackage( os.path.join(self.servicesDir,file) )
        serviceDesc = servicePackage.GetServiceDescription()
        serviceDesc.servicePackageFile = file
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
                    
                    # Set the service package url in the service description
                    sd = servicePkg.GetServiceDescription()
                    sd.servicePackageFile = file
                    servicePkg.SetServiceDescription(sd)
                    
                    servicePackages.append(servicePkg)
                except:
                    log.exception("Invalid service package: %s", file)
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
        
    
    




