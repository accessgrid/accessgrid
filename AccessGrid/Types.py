#-----------------------------------------------------------------------------
# Name:        Types.py
# Purpose:     
#
# Created:     2003/23/01
# RCS-ID:      $Id: Types.py,v 1.49 2004-05-06 17:53:10 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Types.py,v 1.49 2004-05-06 17:53:10 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import zipfile
import sys

from AccessGrid import Log
log = Log.GetLogger(Log.Types)

from AccessGrid.AGParameter import ValueParameter, RangeParameter, OptionSetParameter, CreateParameter

class AGResource:
    def __init__( self, type=None, resource="", role="" ):
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
        self.serviceDesc = None

        try:
            # examine service package content
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

            self.GetServiceDescription()

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
        
        if self.serviceDesc:
            return self.serviceDesc

        serviceDescription = None
        
        try:
            #
            # extract description file content from zip
            #
            zf = zipfile.ZipFile( self.file, "r" )
            descfilecontent = zf.read( self.descriptionFile )
            zf.close()
        except zipfile.BadZipfile:
            log.exception("Bad zipfile: %s", self.file)
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
            version = 0
            if c.has_option("ServiceDescription","version"):
                version = c.getfloat("ServiceDescription","version")
            serviceDescription = AGServiceDescription( c.get( "ServiceDescription", "name" ),
                                                     c.get( "ServiceDescription", "description" ),
                                                     None,
                                                     capabilities,
                                                     None,
                                                     c.get( "ServiceDescription", "executable" ),
                                                     None,
                                                     None,
                                                     version )

        except:
            log.exception("Invalid service desc: %s", self.file)
            raise InvalidServiceDescription(sys.exc_value)
            
        self.serviceDesc = serviceDescription
            
        return serviceDescription
        
    def SetServiceDescription(self,serviceDesc):
        self.serviceDesc = serviceDesc

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

        f = open( path + os.sep + self.exeFile, "wb" )
        f.write( exefilecontent )
        f.close()

    def ExtractPackage( self, path ):
        """
        Extract files from service package
        """
        
        try:
            zf = zipfile.ZipFile( self.file, "r" )
            filenameList = zf.namelist()
            for filename in filenameList:
                try:
                    destfilename = os.path.join(path,filename)
                
                    # Skip the file if it already exists
                    if os.path.exists(destfilename):
                        continue
                
                    # Extract the file
                    filecontent = zf.read( filename )
                    f = open( destfilename, "wb" )
                    f.write( filecontent )
                    f.close()
                    #print "setting permissions on file", destfilename
                    
                    # Mark the file executable (indiscriminately)
                    os.chmod(destfilename,0755)
                    
                    s = os.stat(destfilename)
                    #print "%s mode %d", destfilename, s[0]
                except:
                    log.exception("Error extracting file %s", filename)

            zf.close()
        except zipfile.BadZipfile:
            raise InvalidServicePackage(self.file)
            
    def GetName(self):
        return self.serviceDesc.name

class ServiceConfiguration:
    """
    ServiceConfiguration encapsulates the configuration of 
    AGServices
    """
    def __init__( self, resource=AGResource(), executable="", parameters=dict() ):
        self.resource = resource
        self.executable = executable
        self.parameters = map( lambda parm: CreateParameter( parm ), parameters )
