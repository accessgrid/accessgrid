#-----------------------------------------------------------------------------
# Name:        Types.py
# Purpose:     
#
# Author:      Thomas Uram
#
# Created:     2003/23/01
# RCS-ID:      $Id: Types.py,v 1.37 2003-09-16 07:20:18 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Types.py,v 1.37 2003-09-16 07:20:18 judson Exp $"
__docformat__ = "restructuredtext en"

import os
import zipfile
import sys

import logging
log = logging.getLogger("AG.Types")

from AccessGrid.AGParameter import ValueParameter, RangeParameter, OptionSetParameter, CreateParameter

class VenueState:
    def __init__( self, uniqueId, name, description, uri, connections, clients,
                  data, eventLocation, textLocation, applications, services, backupServer=None ):
        self.uniqueId = uniqueId
        self.name = name
        self.description = description
        self.uri = uri
        self.eventLocation = eventLocation
        self.textLocation = textLocation
        self.services = services
        self.backupServer = backupServer
        
        self.connections = dict()
        self.clients = dict()
        self.data = dict()
        self.clients = dict()
        self.applications = dict()
        self.services = dict()
        
        for connection in connections:
            self.connections[connection.uri] = connection
        for client in clients:
            self.clients[client.publicId] = client
        for datum in data:
            self.data[datum.name] = datum
        for app in applications:
            self.applications[app.id] = app
        for service in services:
            self.services[service.name] = service

    def SetUniqueId(self, uniqueId):
        self.uniqueId = uniqueId
    def GetUniqueId(self):
        return self.uniqueId

    def SetDescription( self, description ):
        self.description = description
    def GetDescription( self ):
        return self.description

    def SetName( self, name ):
        self.name = name
    def GetName( self ):
        return self.name

    def SetUri( self, uri ):
        self.uri = uri
    def GetUri( self ):
        return self.uri

    def AddUser( self, userProfile ):
        self.clients[userProfile.publicId] = userProfile
    def RemoveUser( self, userProfile ):
        log.debug("removing user name=%s publicId=%s", userProfile.name, userProfile.publicId)
        log.debug("clients = %s", self.clients.items())
        del self.clients[userProfile.publicId]
        log.debug("RemoveUser complete")
    def ModifyUser( self, userProfile ):
        if userProfile.publicId in self.clients.keys():
            self.clients[userProfile.publicId] = userProfile
    def GetUsers( self ):
        return self.clients.values()

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
        self.services[serviceDescription.name] = serviceDescription
    def RemoveService( self, serviceDescription ):
        del self.services[serviceDescription.name]  

    def AddApplication( self, applicationDescription ):
        self.applications[applicationDescription.uri] = applicationDescription
    def RemoveApplication( self, applicationDescription ):
        self.applications[applicationDescription.uri] = applicationDescription

    def SetEventLocation( self, eventLocation ):
        self.eventLocation = eventLocation
    def GetEventLocation( self ):
        return self.eventLocation

    def SetTextLocation( self, textLocation ):
        self.textLocation = textLocation
    def GetTextLocation( self ):
        return self.textLocation

class AGResource:
    def __init__( self, type=None, resource=None, role="" ):
        self.type = type
        self.resource = resource
        self.role = role
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
    def __init__( self, type, resource, role, portTypes ):
        AGResource.__init__( self, type, resource, role )
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

    def __repr__(self):
        string = "%s %s" % (self.role, self.type)
        return string

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

        except zipfile.BadZipfile:
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
        except zipfile.BadZipfile:
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
                                                     c.get( "ServiceDescription", "executable" ),
                                                     None,
                                                     None )

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
        except zipfile.BadZipfile:
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
