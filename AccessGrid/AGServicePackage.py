#-----------------------------------------------------------------------------
# Name:        AGServicePackage.py
# Purpose:     
#
# Created:     2003/23/01
# RCS-ID:      $Id: AGServicePackage.py,v 1.5 2007/08/15 19:20:27 eolson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AGServicePackage.py,v 1.5 2007/08/15 19:20:27 eolson Exp $"
__docformat__ = "restructuredtext en"

import string
import os
import zipfile
import sys
import StringIO
import ConfigParser

from AccessGrid import Log
from AccessGrid.Descriptions import AGServicePackageDescription
from AccessGrid import Utilities

log = Log.GetLogger("AGServicePackage")

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

    def __init__( self, packageFile ):
        
        # Initialize attributes
        self.packageFile = None
        self.name = None
        self.description = None
        self.resourceNeeded = 0
        self.version = None
        self.inlineClass = 0
        
        self.svcFile = None

        self.__ReadPackageFile(packageFile)
        
            
    def __ReadPackageFile(self,packageFile):
    
    
        self.packageFile = packageFile

        #
        # examine content of package file
        #
        try:
            # examine service package content
            zf = zipfile.ZipFile(packageFile, "r" )
            files = zf.namelist()
            zf.close()
            for f in files:
                if f.endswith(".svc"):
                    self.svcFile = f
            if not self.svcFile:
                raise InvalidServicePackage("Service package does not contain a description file")
        except zipfile.BadZipfile:
            raise InvalidServicePackage(sys.exc_value)

        #
        # extract svc file content from zip
        #
        try:
            zf = zipfile.ZipFile( packageFile, "r" )
            svcFileContent = zf.read( self.svcFile )
            zf.close()
        except zipfile.BadZipfile:
            log.exception("Bad zipfile: %s", self.packageFile)
            raise InvalidServicePackage(sys.exc_value)

        # set up string io from svc file content
        sp = StringIO.StringIO(svcFileContent)
        
        # read config from string io
        c = ConfigParser.ConfigParser()
        c.optionxform = str
        c.readfp( sp )
        
        # read parameters
        try:
            self.name = c.get( "ServiceDescription", "name" )
            self.description = c.get( "ServiceDescription", "description" )
            self.executable = c.get( "ServiceDescription", "executable" )
            if c.has_option("ServiceDescription","resourceType"):
                self.resourceType = c.get( "ServiceDescription", "resourceType" )
            self.version = c.get("ServiceDescription","version")
            if c.has_option("ServiceDescription","resourceNeeded"):
                self.resourceNeeded = c.get( "ServiceDescription", "resourceNeeded" )
            
			# Note:  This is a hack for now; it should be specified in the node service code
			# 		 unless it is decided that services should be inlined generally
            self.inlineClass = self.name
            if c.has_option("ServiceDescription","inlineClass"):
                self.inlineClass = c.get("ServiceDescription","inlineClass")
        except Exception, e:
            log.exception("AGServicePackage.__ReadPackageFile: failed")
            raise InvalidServiceDescription(str(e))

    def Extract( self, path ):
        try:
            Utilities.ExtractZip(self.packageFile, path)
        except zipfile.BadZipfile:
            log.exception("BadZipFile")
            raise InvalidServicePackage(self.packageFile)
            
    def GetName(self):
        return self.name

    def GetVersion(self):
        return self.version

    def GetDescriptionFilename(self):
        return self.svcFile
        
    def GetResourceNeeded(self):
        return self.resourceNeeded
        
    def GetDescription(self):
        return AGServicePackageDescription(self.name,
                                           self.description,
                                           self.packageFile,
                                           self.resourceNeeded)
                                           
        
if __name__ == "__main__":
    servicePackageFile = sys.argv[1]
    servicePackage = AGServicePackage(servicePackageFile)
    servicePackageDesc = servicePackage.GetDescription()
    print "ServicePackage: ", servicePackageFile
    print "  name: ", servicePackageDesc.name
    print "  description: ", servicePackageDesc.description
    print "  packageFile: ", servicePackageDesc.packageFile
    print "  resourceNeeded: ", servicePackageDesc.resourceNeeded
    
    path = '/tmp/b'
    print "Extracting package to", path
    servicePackage.Extract(path)
    
    f = os.path.join(path,servicePackage.svcFile)
    if os.path.exists(f):
        print "  ** success"
    else:
        print "  ** failure"
