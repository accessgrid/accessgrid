#-----------------------------------------------------------------------------
# Name:        AGServicePackage.py
# Purpose:     
#
# Created:     2003/23/01
# RCS-ID:      $Id: AGServicePackage.py,v 1.2 2005-02-07 21:52:12 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: AGServicePackage.py,v 1.2 2005-02-07 21:52:12 lefvert Exp $"
__docformat__ = "restructuredtext en"

import string
import os
import zipfile
import sys
import StringIO
import ConfigParser

from AccessGrid import Log
from AccessGrid.ServiceCapability import ServiceCapability
from AccessGrid.Descriptions import AGServicePackageDescription

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
        self.resourceType = None
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
        
        # read required parameters
        try:
            self.name = c.get( "ServiceDescription", "name" )
            self.description = c.get( "ServiceDescription", "description" )
            self.executable = c.get( "ServiceDescription", "executable" )
            if c.has_option("ServiceDescription","resourceType"):
                self.resourceType = c.get( "ServiceDescription", "resourceType" )
            self.version = c.get("ServiceDescription","version")
            if c.has_option("ServiceDescription","inlineClass"):
                self.inlineClass = c.get("ServiceDescription","inlineClass")
        except Exception, e:
            log.exception("AGServicePackage.__ReadPackageFile: failed")
            raise InvalidServiceDescription(str(e))
            
                
    def Extract( self, path ):
        """
        Extract files from service package
        """
        
        try:
        
            if not os.path.exists(path):
                os.mkdir(path)
        
            zf = zipfile.ZipFile( self.packageFile, "r" )
            filenameList = zf.namelist()
            for filename in filenameList:
                try:
                    # create subdirs if needed
                    pathparts = string.split(filename, '/')
                    if len(pathparts) > 1:
                        temp_dir = str(path)
                        for i in range(len(pathparts) - 1):
                            temp_dir = os.path.join(temp_dir, pathparts[i])
                        #print "Creating dir if needed:", temp_dir
                        if not os.access(temp_dir, os.F_OK):
                            os.makedirs(temp_dir)

                    destfilename = os.path.join(path,filename)

                    # Extract the file
                    # Treat directory names different than files.
                    if os.path.isdir(destfilename):
                        pass  # skip if dir already exists
                    elif destfilename.endswith("/"):
                        os.makedirs(destfilename) # create dir if needed
                    else: # It's a file so extract it
                        filecontent = zf.read( filename )
                        f = open( destfilename, "wb" )
                        f.write( filecontent )
                        f.close()

                    #print "setting permissions on file", destfilename
                    
                    # Mark the file executable (indiscriminately)
                    os.chmod(destfilename,0755)
                    
                    #s = os.stat(destfilename)
                    #print "%s mode %d" % (destfilename, s[0])
                except:
                    log.exception("Error extracting file %s", filename)

            zf.close()
        except zipfile.BadZipfile:
            raise InvalidServicePackage(self.packageFile)
            
    def GetName(self):
        return self.name

    def GetVersion(self):
        return self.version

    def GetDescriptionFilename(self):
        return self.svcFile
        
    def GetResourceType(self):
        return self.resourceType
        
    def GetDescription(self):
        return AGServicePackageDescription(self.name,
                                           self.description,
                                           self.packageFile,
                                           self.resourceType)
                                           
        
if __name__ == "__main__":
    servicePackageFile = sys.argv[1]
    servicePackage = AGServicePackage(servicePackageFile)
    servicePackageDesc = servicePackage.GetDescription()
    print "ServicePackage: ", servicePackageFile
    print "  name: ", servicePackageDesc.name
    print "  description: ", servicePackageDesc.description
    print "  packageFile: ", servicePackageDesc.packageFile
    print "  resourceType: ", servicePackageDesc.resourceType
    
    path = '/tmp/b'
    print "Extracting package to", path
    servicePackage.Extract(path)
    
    f = os.path.join(path,servicePackage.svcFile)
    if os.path.exists(f):
        print "  ** success"
    else:
        print "  ** failure"
