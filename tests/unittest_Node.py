#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        unittest_Node.py
# Purpose:     
#
# Created:     2004/05/07
# RCS-ID:    
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

"""
Unittest for a Node

This test starts a node service and service manager, and performs basic
nodey operations on them.

Note that PyUnit (and JUnit as well) execute setUp() and tearDown() once for
EACH test and make it difficult to setUp and tearDown something across multiple
tests.  This is not ideal for our server tests, but we work around it to keep a
server running for multiple tests.


"""

import time, sys, os
import unittest
import logging, logging.handlers

from AccessGrid.AGNodeService import AGNodeService, AGNodeServiceI
from AccessGrid.AGServiceManager import AGServiceManager, AGServiceManagerI, AGServiceManagerIW
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.hosting import SecureServer as Server
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import AGTkConfig, UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.AGService import AGServiceIW

nodeService = None
serviceManager = None

server = None
log = None
smurl = None

ConfigName = 'NodeServiceTest.cfg'
NumSavedServiceManagers = 0
NumSavedServices = 0

class NodeTestCase(unittest.TestCase):
    """A test case for a whole Node."""

    def test_100_Setup(self):
        global nodeService, server, log, smurl, serviceManager

        # initialize toolkit and environment
        app = Toolkit.Service.instance()
        app.Initialize("Node_test", sys.argv[:1])
        log = app.GetLog()
        
        # Create a hosting environment
        server = Server(('localhost', 4000))

        # Create a Node Service
        nodeService = AGNodeService()
        
        # Create the Node Service Service
        nsurl = server.RegisterObject(AGNodeServiceI(nodeService),
                                      path="/NodeService")
        
        print "URL " , server.FindURLForObject(nodeService)

        print "NS URL: %s" % nsurl
        
        # Tell the world where to find the service
        log.info("Started node service; URI: %s", nsurl)

        # Create a Service Manager
        serviceManager = AGServiceManager(server)

        # Create the Service Manager Service
        smurl = server.RegisterObject(AGServiceManagerI(serviceManager),
                                      path="/ServiceManager")
                                      
        print "URL ", server.FindURLForObject(serviceManager)

        print "SM URL: %s" % smurl
        
        serviceManager = AGServiceManagerIW(smurl)
        
        # Tell the world where to find the service
        log.info("Started service manager; URI: %s", smurl)

        # Run the service
        server.RunInThread()
        
        
        # Remove some service packages from the local services
        # dir, to force the service manager to retrieve some packages
        # from the node service
        servicesDir = os.path.join(UserConfig.instance().GetConfigDir(),
                                   'local_services')
        serviceFileList = os.listdir(servicesDir)
        halfTheServices = len(serviceFileList) / 2
        for i in range(halfTheServices):
            print "removing service dir ", serviceFileList[i]
            
            dir = os.path.join(servicesDir,serviceFileList[i])
            
            if os.path.isdir(dir):
                dirFiles = os.listdir(dir)
                # remove files in the dir
                map( lambda f: os.remove(os.path.join(dir,f)), dirFiles)

                # remove the dir
                os.rmdir(dir)
        
        
    def test_110_AddServiceManager(self):
        
        global nodeService, server, smurl
        
        serviceMgrDesc = AGServiceManagerDescription("test",
                                smurl)
        
        nodeService.AddServiceManager(serviceMgrDesc)
        
        smList = nodeService.GetServiceManagers()
        
        assert len(smList) == 1
        
    def test_120_GetResources(self):
        global nodeService
        
        smList = nodeService.GetServiceManagers()
        for sm in smList:
            rList = AGServiceManagerIW(sm.uri).GetResources()
            for r in rList:
                print "Resource: ", r.resource
        
    def test_140_GetAvailableServices(self):
        
        global serviceManager, server, smurl
        
        svcList = serviceManager.GetAvailableServices()
        
        nsDir = AGTkConfig.instance().GetNodeServicesDir()
        svcFileList = os.listdir(nsDir)
        
        print "Number of service files:", len(svcFileList)
        print "Number of reported services:", len(svcList)
        assert len(svcList) == len(svcFileList)
        
    def test_130_AddServices(self):
        
        global nodeService, server, smurl, serviceManager
        
        serviceMgrDesc = AGServiceManagerDescription("test",
                                smurl)
                                
        svcList = serviceManager.GetAvailableServices()
        for svc in svcList:
            nodeService.AddService(svc,smurl,None,[])
        
        installedSvcList = nodeService.GetServices()
        print "*\n*\n*\n*\n"
        for svc in installedSvcList:
            print "svc = ", svc.name, svc.servicePackageFile
        
        print "Number of known services:", len(svcList)
        print "Number of installed services:", len(installedSvcList)
        assert len(svcList) == len(installedSvcList)
        
    def test_150_SetIdentity(self):
        
        global nodeService
        
        profile = ClientProfile(UserConfig.instance().GetProfile())
        
        nodeService.SetIdentity(profile)
        
    def test_160_SetServiceConfiguration(self):
        
        global nodeService
        
        installedSvcList = nodeService.GetServices()
        
        problemSvcList = []
        
        for svc in installedSvcList:
            try:
                svciw = AGServiceIW(svc.uri)
                
                config = svciw.GetConfiguration()
                
                svciw.SetConfiguration(config)
            except:
                traceback.print_exc()
                problemSvcList.append(svc.name)
                
        if problemSvcList:  
            raise Exception("Set service configuration failed for: %s", problemSvcList)
        
    def test_200_StoreConfiguration(self):
    
        global nodeService, server, smurl
        global NumSavedServiceManagers, NumSavedServices
        global ConfigName
        
        
        svcList = nodeService.GetServices()
        NumSavedServices = len(svcList)
        
        smList = nodeService.GetServiceManagers()
        NumSavedServiceManagers = len(smList)
        
        nodeService.StoreConfiguration(ConfigName)
        
    def test_450_RemoveServices(self):
        
        global nodeService, server, smurl
        
        serviceMgrDesc = AGServiceManagerDescription("test",
                                smurl)
                                
        smList = nodeService.GetServiceManagers()
        
        for sm in smList:
            AGServiceManagerIW(sm.uri).RemoveServices()

        installedSvcList = nodeService.GetServices()
        
        print "Number of installed services:", len(installedSvcList)
        assert len(installedSvcList) == 0
        
    def test_500_RemoveServiceManagers(self):
        global nodeService, server, smurl
        
        smList = nodeService.GetServiceManagers()
        
        for sm in smList:
            nodeService.RemoveServiceManager(sm)
                          
        smList = nodeService.GetServiceManagers()
        
        print "Number of service managers after Removal: ", len(smList)
        
        assert len(smList) == 0
        
    def test_600_LoadConfiguration(self):
        
        global nodeService, server, smurl
        global NumSavedServiceManagers, NumSavedServices
        nodeService.LoadConfiguration(ConfigName)
        
        svcList = nodeService.GetServices()
        smList = nodeService.GetServiceManagers()
        
        print "Number of services loaded/saved: ", len(svcList),NumSavedServices
        print "Number of service managers loaded/saved", len(smList),NumSavedServiceManagers
        
        assert len(smList) == NumSavedServiceManagers
        assert len(svcList) == NumSavedServices


    # Cleanup things set up in the test suite init above.
    #   Unittest suites don't have a proper way to cleanup things used 
    #   in the entire suite.
    def test_999_TearDown(self):
        global nodeService
        nodeService.Stop()
        server.Stop() 

def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(NodeTestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

