#-----------------------------------------------------------------------------
# Name:        Types.py
# Purpose:     
#
# Author:      Thomas Uram
#
# Created:     2003/23/01
# RCS-ID:      $Id: Types.py,v 1.10 2003-01-24 04:30:08 judson Exp $
# Copyright:   (c) 2002
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

class Event:
    TEST_EVENT = "Test"

    ENTER = "Enter"
    EXIT = "Exit"
    ADD_DATA = "Add data"
    REMOVE_DATA = "Remove data"
    ADD_SERVICE = "Add service"
    REMOVE_SERVICE = "Remove service"
    ADD_CONNECTION = "Add connection"
    REMOVE_CONNECTION = "Remove connection"
    UPDATE_VENUE_STATE = "Update venue state"

    HEARTBEAT = "Client Heartbeat"
    
    def __init__( self, eventType, data ):
        self.eventType = eventType
        self.data = data

from AccessGrid.AGParameter import *
        
class VenueState:
    def __init__( self, description, connections, users,
                  nodes, data, services, coherenceLocation ):
        self.description = description
        self.coherenceLocation = coherenceLocation

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

    def UpdateClient(self, update):
        (id, time) = string.split(update, '-')
        self.clients[id] = string.split(time, ':')
        
    def SetCoherenceLocation( self, coherenceLocation ):
        self.coherenceLocation = coherenceLocation
    def GetCoherenceLocation( self ):
        return self.coherenceLocation

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

# consider using this as the description of the service implementation
# at the NodeService, passing the url of the executable to the ServiceManager.
# Only the executable would reside on the ServiceManager
class AGServiceImplementation:
    def __init__( self, name=None, description=None, uri=None,
                  capabilities=None, commandLineArgs=None ):
        self.name = name                 # user
        self.description = description   # user
        self.uri = uri                   # for system to retrieve executable
        self.capabilities = capabilities # user
        self.executable = None           # system, but can be determined from package content


    def GetServiceDescription( self, file ):

        import ConfigParser
        import string

        #
        # examine service package content
        #
        zf = zipfile.ZipFile( file, "r" )
        files = zf.namelist()
        descfile = None
        exefile = None
        for file in files:
            if file.endswith(".svc"):
                descfile = file
            else:
                exefile = file
                if exefile.endswith(".py"):
                    self.isPython = 1

        #
        # extract executable file from zip
        #
        exefilecontent = zf.read( exefile )
        if self.isPython:
            f = open( "local_services/"+exefile, "w" )
        else:
            f = open( "local_services/"+exefile, "wb" )
        f.write( exefilecontent )
        f.close()

        #
        # extract description file from zip
        #
        descfilecontent = zf.read( descfile )
        f = open( "local_services/"+descfile, "w" )
        f.write( descfilecontent )
        f.close()

        c = ConfigParser.ConfigParser()
        c.read( "local_services/"+descfile )

        # error checking

        #
        # read sections and massage into data structure
        #
        print "----- sections ", c.sections()

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
                                                 "local_services/" + c.get( "ServiceDescription", "executable" ) )
        return serviceDescription

from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator

class AGServiceImplementationRepository:

    def __init__( self, port=MulticastAddressAllocator().AllocatePort()):
        self.httpd_port = port
        self.__ReadServiceImplementations()
        thread.start_new_thread( self.__StartWebServer, () )

    def __ReadServiceImplementations( self ):
        self.serviceImplementations = []

# FIXME - location of services should be configurable by clients
        files = os.listdir("services")
        for file in files:
            if file.endswith(".zip"):
                self.serviceImplementations.append( 'http://%s:%d/services/%s' %
                   ( socket.gethostname(), self.httpd_port, file ) )


    def GetServiceImplementations( self ):
        __doc__ = """Get list of local service implementations"""
        return self.serviceImplementations

    def __StartWebServer( self ):
        print "Starting web server on port ", self.httpd_port
        self.httpd = SocketServer.TCPServer(("",self.httpd_port), SimpleHTTPServer.SimpleHTTPRequestHandler )
        self.httpd.serve_forever()



class ServiceConfiguration:
    def __init__( self, resource, executable, parameters ):
        self.executable = executable
        self.resource = resource
        self.parameters = map( lambda parm: CreateParameter( parm ), parameters )
