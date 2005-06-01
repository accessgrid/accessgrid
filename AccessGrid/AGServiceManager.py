#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.87 2005-06-01 21:12:16 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: AGServiceManager.py,v 1.87 2005-06-01 21:12:16 turam Exp $"
__docformat__ = "restructuredtext en"

import sys
import os
import time
import threading

from AccessGrid import Log
from AccessGrid.GUID import GUID
from AccessGrid import Toolkit
from AccessGrid.Toolkit import Service
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid.Platform.Config import AGTkConfig, UserConfig, SystemConfig
from AccessGrid.AGServicePackage import AGServicePackage
from AccessGrid.NetworkAddressAllocator import NetworkAddressAllocator
from AccessGrid.hosting.SOAPInterface import SOAPInterface, SOAPIWrapper
from AccessGrid.Descriptions import CreateAGServicePackageDescription
from AccessGrid.Descriptions import CreateAGServiceDescription
from AccessGrid.Descriptions import CreateParameter
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.interfaces.AGService_interface import AGService as AGServiceI
from AccessGrid.interfaces.AGService_client import AGServiceIW

log = Log.GetLogger(Log.ServiceManager)

class AGServiceManager:
    """
    """
    
    ServiceType = '_servicemanager._tcp'

    def __init__( self, server, app=None ):
        self.server = server
        if app is not None:
            self.app = app
        else:
            self.app = Service.instance()

        self.name = self.app.GetHostname()
        self.uri = 0
        self.services = dict()
        self.processManager = ProcessManager()
        self.registeringServices = dict()
        self.registerFlag = threading.Event()
        self.allocator = NetworkAddressAllocator()
        self.nodeServiceUri = 0
        
        userConfig = self.app.GetUserConfig()
        self.localServicesDir = userConfig.GetLocalServicesDir()
        
        toolkitConfig = self.app.GetToolkitConfig()
        self.servicesDir = toolkitConfig.GetNodeServicesDir()

    def Shutdown(self):
        log.info("AGServiceManager.Shutdown")
        log.info("Remove services")
        self.RemoveServices()
        log.info("Stop network interface")


    ####################
    ## SERVICE methods
    ####################
    
    def AddServiceByName(self,name):
    
        servicePackage = None
        servicePackages =  self.GetServicePackageDescriptions()
        for s in servicePackages:
            print "name = ", name, "s = ", s.packageFile
            if s.packageFile.endswith(name):
                servicePackage = s
                
        if not servicePackage:
            raise Exception("No service package found for specified name",
                            name)
                            
        return self.AddService(servicePackage)
    
    
    def AddService( self, servicePackageDesc ):
        """
        Add a service package to the service manager.  
        """
        log.info("AGServiceManager.AddService")
        
        servicePackage = \
            self.GetServicePackage(servicePackageDesc.GetPackageFile())
              

        #
        # Extract the service package
        #
        try:
            # Create dir for package
            servicePath = self.__GetServicePath(servicePackage)
            
            log.info("Extracting service package to %s", servicePath)

            # Extract the package
            servicePackage.Extract(servicePath)
                
        except:
            log.exception("Service Manager failed to extract service implementation %s", 
                          servicePackage.packageFile)
            raise Exception("Service Manager failed to extract service implementation")
            
        # Change to the services directory to start the process     
        # Note: services rely on this being true    
        os.chdir(servicePath) 
        
        # Start the service  
        if servicePackage.inlineClass:
            print "* * Service package inlining is disabled * * "
        if 0 and servicePackage.inlineClass:
            serviceUrl,pid = self.__AddInlineService(servicePackage)
        else:
            serviceUrl,pid = self.__ExecuteService(servicePackage)
            
        # Set the package name in the service
        AGServiceIW(serviceUrl).SetPackageFile(servicePackage.packageFile)

        # Get the description from the service
        serviceDescription = AGServiceIW(serviceUrl).GetDescription()

        # Add service to list of services
        self.services[pid] = serviceDescription
            
        return serviceDescription

    def RemoveService( self, serviceToRemove ):
        """Remove a service
        """
        log.info("AGServiceManager.RemoveService")

        exc = None
        pid = None

        try:

            #
            # Find service to stop using uri
            #
            for key in self.services.keys():
                service = self.services[key]
                if service.uri == serviceToRemove.uri:

                    pid = key
                    try:
                        AGServiceIW( service.uri ).Shutdown()
                    except:
                        log.exception("Error shutting down service %s", service.name)

                    if 1: # not service.inlineClass:

                        #
                        # Kill service
                        #
                        self.processManager.TerminateProcess(pid)

                    break

        except:
            log.exception("Exception removing service %s", serviceToRemove.name)
            exc = sys.exc_value

        #
        # Remove service from list
        #
        if pid:
            del self.services[pid]

        # raise exception now, if one occurred
        if exc:
            raise Exception("AGServiceManager.RemoveService failed : ", str( exc ) )



    def RemoveServices( self ):
        """Remove all services
        """
        log.info("AGServiceManager.RemoveServices")
        for service in self.services.values():
            try:
                self.RemoveService( service )
            except Exception:
                log.exception("Exception in AGServiceManager.RemoveServices; continuing")

    def GetServices( self ):
        """Return list of services
        """
        log.info("AGServiceManager.GetServices")
        return self.services.values()

    def StopServices( self ):
        """
        Stop all services on service manager
        """
        log.info("AGServiceManager.StopServices")
        for service in self.services.values():
            AGServiceIW( service.uri ).Stop()

    def RegisterService(self,token,url):
        if token in self.registeringServices.keys():
            self.registeringServices[token] = url
        self.registerFlag.set()
        
    ####################
    ## MISC methods
    ####################
    
    def SetNodeServiceUrl(self,nodeServiceUri):
        log.debug("SetNodeServiceUrl: %s", nodeServiceUri)
        self.nodeServiceUri = nodeServiceUri
        
    def GetNodeServiceUrl(self):
        return self.nodeServiceUri
        
    def SetUri(self,url):
        self.uri = url
        
    def GetUri(self):
        return self.uri
        
    def SetName(self,name):
        self.name = name
        
    def GetName(self):
        return self.name
        
    def GetDescription(self):
        return AGServiceManagerDescription(self.name,self.uri)
        
    def GetServicePackageDescriptions( self ):
        serviceDescriptions = []

        servicePackages = self.GetServicePackages()
        for servicePackage in servicePackages:
            serviceDescriptions.append(servicePackage.GetDescription())

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
        for f in files:
            if f.endswith('.zip'):
                try:
                    servicePkg = self.GetServicePackage(os.path.join(self.servicesDir,f))
                    servicePackages.append(servicePkg)
                except Exception, e:
                    print "exception", e
                    log.exception("Invalid service package: %s", f)
                    invalidServicePackages += 1
                    
        if invalidServicePackages:
            log.info("%d invalid service packages skipped", invalidServicePackages)

        return servicePackages
    
    def GetServicePackage(self,servicePackageFile):
        return AGServicePackage(os.path.join(self.servicesDir,servicePackageFile))
        

    ####################
    ## INTERNAL methods
    ####################

                
    def __GetServicePath(self,servicePackage):
        """
        Return the path in which services files will be unpacked for
        the given service
        """
        serviceDirName = servicePackage.name.replace(' ', '_')
        servicePath = os.path.join(self.localServicesDir,serviceDirName)
        return servicePath
        
    def __AddInlineService(self,servicePackage):
        log.info("Importing inline service class %s", 
                 servicePackage.inlineClass )
    
        # import the service class
        if '.' not in sys.path:
            sys.path.insert(0,'.')
        mod = __import__(servicePackage.name)
    
        # instantiate the service object
        instantiation = 'mod.%s()' % (servicePackage.inlineClass,)
        log.debug("Instantiating service object: %s", instantiation)
        serviceObj = eval(instantiation)
    
        # instantiate the interface object
        serviceObjI = AGServiceI(serviceObj)
    
        # register the interface object
        pid = str(GUID())
        path = '/Services/'+servicePackage.name+'.'+pid
        self.server.RegisterObject(serviceObjI,path=path)
        serviceUrl = self.server.FindURLForObject(serviceObj)
        
        serviceObj.SetUri(serviceUrl)
    
        log.info("Service registered at url %s", serviceUrl)
        
        return serviceUrl,pid
    
    def __ExecuteService(self,servicePackage):
        log.debug("Executing service %s", servicePackage.name)
        #
        # Start the service process
        #
        options = []

        #
        # Determine executable
        #
        servicePath = self.__GetServicePath(servicePackage)
        exeFile = os.path.join(servicePath, servicePackage.executable )
        options.append( exeFile )

        # Set options for service
        # - port
        port = self.allocator.AllocatePort()
        options.append( '--port' )
        options.append( port )

        # - url of service manager to register with
        options.append( '--serviceManagerUri' )
        options.append( self.uri )

        # - a token that the service will pass when registering
        token = str(GUID())
        options.append( '--token' )
        options.append( token )

        # - if service manager is insecure, services will be too
        if self.app.GetOption('secure'):
            options.append( '--secure' )

        log.info("Running Service; options: %s", str(options))

        # Execute the service process 
        pid = self.processManager.StartProcess( sys.executable, options )

        # Wait for service to register with me
        self.registeringServices[token] = None
        self.registerFlag.clear()
        self.registerFlag.wait(10)

        if self.registerFlag.isSet():
            serviceUrl = self.registeringServices[token]
            log.info("Service registered: %s %s", serviceUrl, token)
        else:
            log.info("Service failed to register: %s", token)
            raise Exception("Service failed to become reachable")

        # Remove service from registration list
        del self.registeringServices[token]
        
        return serviceUrl,pid



    def IsValid(self):
        return 1




if __name__ == "__main__":

    from AccessGrid import Toolkit
    
    a = Toolkit.CmdlineApplication()
    a.Initialize('test')
    tc = a.GetToolkitConfig()
    print "tc = ", tc
    
    server = 'dummy'
    serviceManager = AGServiceManager(server,a)
    servicePackages = serviceManager.GetServicePackages()
    for s in servicePackages:
        print "s ", s.name
