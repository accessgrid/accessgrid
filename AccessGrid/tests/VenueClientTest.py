#-----------------------------------------------------------------------------
# Name:        VenueServerTest.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueClientTest.py,v 1.2 2003-02-17 17:24:59 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import threading
import os

from wxPython.wx import *

from pyGlobus.io import GSITCPSocketException

import AccessGrid.Types
import AccessGrid.ClientProfile
from AccessGrid.Platform import GPI 
from AccessGrid.VenueClient import VenueClient, EnterVenueException
from AccessGrid.VenueClientUIClasses import WelcomeDialog
from AccessGrid.VenueClientUIClasses import VenueClientFrame, ProfileDialog
from AccessGrid.VenueClientUIClasses import UrlDialog, UrlDialogCombo
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.UIUtilities import ErrorDialog

import sys
from AccessGrid.hosting.pyGlobus.Server import Server
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.Types import *


class VenueClientTest(VenueClient):
    def __init__(self, url):
        VenueClient.__init__(self)
        print '--------------- SET PROFILE'
        profile = ClientProfile('userProfileExample')
        self.SetProfile(profile)
        self.profile.Dump()
     
        print '\n--------------- CREATE PROXY'
        try:
            venueUri = Client.Handle(url).get_proxy().GetDefaultVenue()
            print 'get url for default venue from server ', url

        except:
            venueUri = url

        print 'venue url: ', url
        print 'get proxy for venue', venueUri
        self.client = Client.Handle(venueUri).get_proxy()

        print '\n--------------- ENTER VENUE'
        self.EnterVenue(venueUri)

        print '\n--------------- ADD DATA'
        data = DataDescription('dataName')
        self.client.AddData(data)

        print '\n--------------- ADD SERVICE'
        service = ServiceDescription('serviceName', 'serviceDescription', 'serviceUri',\
                                     'serviceIcon', 'serviceStoragetype')
        self.client.AddService(service)

        print '\n--------------- REMOVE DATA'    
        self.client.RemoveData(data)

        print '\n--------------- REMOVE SERVICE'  
        self.client.RemoveService(service)

        nodeUrl = 'http://nodeserviceurl'
        print '\n--------------- SET NODE SERVICE URL', nodeUrl  
        self.SetNodeServiceUri(nodeUrl)
        print '--------------- NODE SERVICE URL: ', self.nodeServiceUri

   
        print '\n--------------- CHANGE PROFILE'
        profile2 = ClientProfile('nodeProfile')
        self.SetProfile(profile2)
        self.profile.Dump()
        
        print '\n--------------- EXIT VENUE'
        self.ExitVenue()
          
    def ModifyUserEvent(self, data):
        print '--------------- MODIFY PARTICIPANT EVENT'
        pass

    def AddDataEvent(self, data):
        print '--------------- ADD DATA EVENT'
        pass

    def RemoveDataEvent(self, data):
        print '--------------- REMOVE DATA EVENT'
        pass

    def AddServiceEvent(self, data):
        print '--------------- ADD SERVICE EVENT'
        pass

    def RemoveServiceEvent(self, data):
        print '--------------- REMOVE SERVICE EVENT'
        pass

    def AddConnectionEvent(self, data):
        print '--------------- ADD CONNECTION EVENT'
        pass

    def SetConnectionsEvent(self, data):
        print '--------------- SET CONNECTION EVENT'
        pass

    def EnterVenue(self, URL):
        VenueClient.EnterVenue( self, URL )
        venueState = self.venueState
        
        print 'venue name: ', venueState.description.name
        print 'venue description: ',venueState.description.description
      
        users = venueState.users.values()
        
        print '\n-------------USERS/NODES'
        for user in users:
            if(user.profileType == 'user'):
                print 'user: ', user.name
            else:
                print 'node: ', user.name

        print '\n-------------DATA'
        data = venueState.data.values()
        for d in data:
            print 'data: ', d.name

        print '\n-------------NODES'
        nodes = venueState.nodes.values()
        for node in nodes:
            print 'node: ', node.name

        print '\n-------------SERVICES'
        services = venueState.services.values()
        for service in services:
            print 'service: ', service.name

        print '\n------------- EXITS'
        exits = venueState.connections.values()
        for exit in exits:
            print 'exit: ', exit.name
         
        pass
       
    def ExitVenue(self):
        VenueClient.ExitVenue(self)
        os._exit(1)
        
if __name__ == "__main__":       
    venueServerPort = 8000
    if len(sys.argv) > 1:
        venueServerPort = sys.argv[1]
    venueServerUri = 'https://localhost:%s/VenueServer' % ( venueServerPort )
    VenueClientTest(venueServerUri)
