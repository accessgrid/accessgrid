#-----------------------------------------------------------------------------
# Name:        Types.py
# Purpose:     
#
# Author:      Thomas Uram
#
# Created:     2003/23/01
# RCS-ID:      $Id: Types.py,v 1.22 2003-02-21 18:05:16 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import thread
import zipfile
import socket
import time
import SimpleHTTPServer
import SocketServer
import string
import os
from AccessGrid.hosting.pyGlobus.Utilities import GetHostname

from AccessGrid.AGParameter import *
        
class VenueState:
    def __init__( self, description, connections, users,
                  nodes, data, services, eventLocation, textLocation ):
        self.description = description
        self.eventLocation = eventLocation
        self.textLocation = textLocation

        self.connections = dict()
        self.users = dict()
        self.nodes = dict()
        self.data = dict()
        self.services = dict()
        self.clients = dict()

        for connection in connections:
            self.connections[connection.uri] = connection
        for user in users:
            self.users[user.publicId] = user
            self.clients[user.publicId] = time.localtime()
        for node in nodes:
            self.nodes[node.publicId] = node
            self.clients[nodes.publicId] = time.localtime()
        for datum in data:
            self.data[datum.name] = datum
        for service in services:
            self.services[service.uri] = service

    def SetDescription( self, description ):
        self.description = description
    def GetDescription( self ):
        return self.description

    def AddUser( self, userProfile ):
        self.users[userProfile.publicId] = userProfile
    def RemoveUser( self, userProfile ):
        del self.users[userProfile.publicId]
    def ModifyUser( self, userProfile ):
        if userProfile.publicId in self.users.keys():
            self.users[userProfile.publicId] = userProfile
    def GetUsers( self ):
        return self.users.values()

    def AddNode( self, nodeProfile ):
        self.nodes[nodeProfile.publicId] = nodeProfile
    def RemoveNode( self, nodeProfile ):
        del self.nodes[nodeProfile.publicId]

    def AddConnection( self, connectionDescription ):
        self.connections[connectionDescription.uri] = connectionDescription
    def RemoveConnection( self, connectionDescription ):
        del self.connections[connectionDescription.uri]
    def SetConnections( self, connectionList ):
        for connection in connectionList:
            self.connections[connection.uri] = connection

    def AddData( self, dataDescription ):
        self.data[dataDescription.name] = dataDescription
    def UpdateData( self, dataDescription ):
        self.data[dataDescription.name] = dataDescription
    def RemoveData( self, dataDescription ):
        del self.data[dataDescription.name]

    def AddService( self, serviceDescription ):
        self.services[serviceDescription.uri] = serviceDescription
    def RemoveService( self, serviceDescription ):
        del self.services[serviceDescription.uri]

    def AddConnection( self, connectionDescription ):
        self.connections[connectionDescription.uri] = connectionDescription
    def RemoveConnection( self, connectionDescription ):
        del self.connections[connectionDescription.uri]

    def SetEventLocation( self, eventLocation ):
        self.eventLocation = eventLocation
    def GetEventLocation( self ):
        return self.eventLocation

    def SetTextLocation( self, textLocation ):
        self.textLocation = textLocation
    def GetTextLocation( self ):
        return self.textLocation

class AGResource:
    def __init__( self, type=None, resource=None ):
        self.type = type
        self.resource = resource
        self.inUse = 0

    def GetType( self ):
        return self.type
    def SetType( self, type ):
        self.type = type

    def GetResource( self ):
        return self.resource
    def SetResource( self, resource ):
        self.resource = resource

class AGVideoResource( AGResource ):
    def __init__( self, type, resource, portTypes ):
        AGResource.__init__( self, type, resource )
        self.portTypes = portTypes

class Capability:

    PRODUCER = "producer"
    CONSUMER = "consumer"

    AUDIO = "audio"
    VIDEO = "video"
    TEXT  = "text"

    def __init__( self, role=None, type=None ):
        self.role = role
        self.type = type
        self.parms = dict()

    def matches( self, capability ):
        if self.type != capability.type:
            # type mismatch
            return 0
        """
        for key in self.parms.keys():
            if key not in capability.parms.keys():
                # keyword mismatch
                return 0

            if self.parms[key] != capability.parms[key]:
                # value mismatch
                return 0
        """

        # capability match
        return 1

class AGServiceManagerDescription:
    def __init__( self, name=None, description=None, uri=None ):
        self.name = name
        self.description = description
        self.uri = uri

class AGServiceDescription:
    def __init__( self, name=None, description=None, uri=None, capabilities=None,
                  resource=None, serviceManagerUri=None, executable=None ):
        self.name = name
        self.description = description
        self.uri = uri
        self.capabilities = capabilities
        self.resource = resource
        self.serviceManagerUri = serviceManagerUri
        self.executable = executable


class AGServicePackage:
    def __init__( self, file ):
        self.file = file
        self.exeFile = None
        self.descriptionFile = None

        #
        # examine service package content
        #
        zf = zipfile.ZipFile( self.file, "r" )
        files = zf.namelist()
        zf.close()
        for file in files:
            if file.endswith(".svc"):
                self.descriptionFile = file
            else:
                self.exeFile = file
                if self.exeFile.endswith(".py"):
                    self.isPython = 1

    def GetServiceDescription( self ):

        import ConfigParser
        import string
        import StringIO



        try:
            #
            # extract description file content from zip
            #
            zf = zipfile.ZipFile( self.file, "r" )
            descfilecontent = zf.read( self.descriptionFile )
            zf.close()

            # set up string io from description file content
            sp = StringIO.StringIO(descfilecontent)

            # read config from string io
            c = ConfigParser.ConfigParser()
            c.readfp( sp )

            #
            # read sections and massage into data structure
            #
            capabilities = []
            capabilitySectionsString = c.get( "ServiceDescription", "capabilities" )
            capabilitySections = string.split( capabilitySectionsString, ' ' )
            for section in capabilitySections:
                cap = Capability( c.get( section, "role" ), c.get( section, "type" ) )
                capabilities.append( cap )
            serviceDescription = AGServiceDescription( c.get( "ServiceDescription", "name" ),
                                                     c.get( "ServiceDescription", "description" ),
                                                     None,
                                                     capabilities,
                                                     None,
                                                     None,
                                                     c.get( "ServiceDescription", "executable" ) )

        except:
            print "Exception in GetServiceDescription ", sys.exc_type, sys.exc_value

        return serviceDescription

    def ExtractExecutable( self, path ):
        #
        # extract executable file from zip
        #
        zf = zipfile.ZipFile( self.file, "r" )
        exefilecontent = zf.read( self.exeFile )
        zf.close()

        if self.isPython:
            f = open( path + os.sep + self.exeFile, "w" )
        else:
            f = open( path + os.sep + self.exeFile, "wb" )
        f.write( exefilecontent )
        f.close()




from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator

class AGServiceImplementationRepository:

    def __init__( self, port, servicesDir):

        # if port is 0, find a free port
        if port == 0:
            port = MulticastAddressAllocator().AllocatePort()

        self.httpd_port = port
        self.servicesDir = servicesDir
        self.serviceDescriptions = []
        thread.start_new_thread( self.__StartWebServer, () )

    def __ReadServicePackages( self ):
        self.serviceDescriptions = []

        if os.path.exists(self.servicesDir):
            files = os.listdir(self.servicesDir)
            for file in files:
                if file.endswith(".zip"):
                    servicePackage = AGServicePackage( self.servicesDir + os.sep + file)
                    serviceDesc = servicePackage.GetServiceDescription()
                    serviceDesc.uri = 'http://%s:%d/%s/%s' % ( GetHostname(), self.httpd_port, 
                                                               self.servicesDir, file )
                    self.serviceDescriptions.append( serviceDesc )


    def GetServiceImplementations( self ):
        """Get list of local service descriptions"""
        self.__ReadServicePackages()
        return self.serviceDescriptions

    def __StartWebServer( self ):
        print "Starting web server on port ", self.httpd_port
        self.httpd = SocketServer.TCPServer(("",self.httpd_port), SimpleHTTPServer.SimpleHTTPRequestHandler )
        self.httpd.serve_forever()



class ServiceConfiguration:
    def __init__( self, resource, executable, parameters ):
        self.executable = executable
        self.resource = resource
        self.parameters = map( lambda parm: CreateParameter( parm ), parameters )
