#-----------------------------------------------------------------------------
# Name:        Types.py
# Purpose:     
#
# Author:      Thomas Uram
#
# Created:     2003/23/01
# RCS-ID:      $Id: Types.py,v 1.24 2003-02-24 20:56:24 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import os
import thread
import zipfile
import socket
import time
import string
import os
import sys

from AccessGrid.AGParameter import ValueParameter, RangeParameter, OptionSetParameter, CreateParameter

class VenueState:
    def __init__( self, uniqueId, description, connections, users,
                  nodes, data, services, eventLocation, textLocation ):
        self.uniqueId = uniqueId
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

    def SetUniqueId(self, uniqueId):
        self.uniqueId = uniqueId
    def GetUniqueId(self):
        return self.uniqueId

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


class InvalidServicePackage(Exception):
    pass
class InvalidServiceDescription(Exception):
    pass

class AGServicePackage:
    """
    Class to represent a service package, a zipfile containing a 
    service description file (.svc) and an implementation file,
    either a Python script or an executable
    """

    def __init__( self, file ):
        self.file = file
        self.exeFile = None
        self.descriptionFile = None

        try:
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

            if not self.exeFile:
                raise InvalidServicePackage("Service package does not contain an executable file")
            if not self.descriptionFile:
                raise InvalidServicePackage("Service package does not contain a description file")

        except zipfile.BadZipFile:
            raise InvalidServicePackage(sys.exc_value)

    def GetServiceDescription( self ):
        """
        Read the package file and return the service description
        """
        import ConfigParser
        import string
        import StringIO
        from AccessGrid.Descriptions import AGServiceDescription

        serviceDescription = None

        try:
            #
            # extract description file content from zip
            #
            zf = zipfile.ZipFile( self.file, "r" )
            descfilecontent = zf.read( self.descriptionFile )
            zf.close()
        except zipfile.BadZipFile:
            raise InvalidServicePackage(sys.exc_value)

        # set up string io from description file content
        sp = StringIO.StringIO(descfilecontent)

        try:
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
            raise InvalidServiceDescription(sys.exc_value)

        return serviceDescription

    def ExtractExecutable( self, path ):
        """
        Extract executable file from service package
        """
        try:
            zf = zipfile.ZipFile( self.file, "r" )
            exefilecontent = zf.read( self.exeFile )
            zf.close()
        except zipfile.BadZipFile:
            raise InvalidServicePackage(sys.exc_value)

        if self.isPython:
            f = open( path + os.sep + self.exeFile, "wb" )
        f.write( exefilecontent )
        f.close()


class ServiceConfiguration:
    """
    ServiceConfiguration encapsulates the configuration of 
    AGServices
    """
    def __init__( self, resource, executable, parameters ):
        self.executable = executable
        self.resource = resource
        self.parameters = map( lambda parm: CreateParameter( parm ), parameters )
