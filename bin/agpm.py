#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        RegisterApp.py
# Purpose:     This registers an application with the users venue client.
# Created:     2002/12/12
# RCS-ID:      $Id: agpm.py,v 1.24 2004-10-05 09:40:02 douglask Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is used to register applications with the user or system AGTk
installation.
"""
__revision__ = "$Id: agpm.py,v 1.24 2004-10-05 09:40:02 douglask Exp $"

import os
import re
from types import StringType
import sys
import zipfile
import tempfile
import shutil
from optparse import OptionParser

from AccessGrid.AppDb import AppDb
from AccessGrid.Utilities import LoadConfig
from AccessGrid.Platform.Config import SystemConfig, AGTkConfig, UserConfig

tempfile.tmpdir = SystemConfig.instance().GetTempDir()

def ProcessArgs():
    doc = """
    By default this program registers/installs a shared application
    or node service with the users environment. Using the -u argument applications 
    can be unregistered/uninstalled.  To unregister node services, use 
    the '--unregister-service' argument.
    """
    tkConf = AGTkConfig.instance()

    parser = OptionParser(doc)
    parser.add_option("-u", "--unregister", action="store_true",
                      dest="unregister", default=0,
          help="Unregister the application, instead of registering it. \
                Specify application with '-n'")
    parser.add_option("--unregister-service", action="store_true",
                      dest="unregisterservice", default=0,
          help="Unregister the service, instead of registering it. \
                Specify service with '-n'. (Requires administrative access)")
    parser.add_option("-n", "--name", dest="appname",
          help="specify a name other than the default on from the .app file.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=0, help="Be verbose during app processing.")
    parser.add_option("-f", "--file", dest="appfile",
          help="The name of a .app file to install.")
    parser.add_option("-d", "--dir", dest="appdir",
                      help="The name of a directory containing a .app file.")
    parser.add_option("-z", "--zip", dest="appzip",
                      help="The name of a .zip file containing a .app or .svc file.\
                            (Requires administrative access to install services)")
    parser.add_option("-p", "--package", dest="apppkg",
                    help="The name of an agpkg file containing a .app or .svc \
                    file. (Requires administrative access to install services)")
    parser.add_option("-l", "--list-apps", action="store_true",
                      dest="listapps", help="List installed shared apps.")
    parser.add_option("--list-services", action="store_true",
                      dest="listservices", help="List installed node services.")
    parser.add_option("-s", "--system", action="store_true",
                      dest="sys_install", default=0,
                      help="Install the package for all users. \
                      (This requires administrative access)")
    parser.add_option("--post-install", action="store_true",
                      dest="post_install", default=0,
                      help="Do a post-installation run, which will install \
                      all apps distributed with the toolkit in the system \
                      if possible. (This requires administrative access)")
    parser.add_option("--wait-for-input", action="store_true",
                      dest="wait_for_input", default=0,
                      help="After completing wait for the user to confirm by\
                      pressing a key.")
                      
    (options, args) = parser.parse_args()

    # Validate arguments
    if not (
            # these args imply an action
            options.appzip 
            or options.apppkg 
            or options.appfile 
            or options.appdir 
            
            # these are explicit actions
            or options.post_install
            or options.listservices
            or options.listapps
            or options.unregister
            or options.unregisterservice
            ):
        parser.print_help()
        print "Error: no action specified"
        sys.exit(1)
    
    if options.sys_install or options.post_install:
        appdb = AppDb(path=tkConf.GetConfigDir())
        dest = tkConf.GetSharedAppDir()
    else:
        appdb = AppDb()
        dest = UserConfig.instance().GetSharedAppDir()

    return options, appdb, dest

def UnpackPkg(filename):
    """
    This function takes the name of a zip file and unpacks it returning the
    directory it unpacked the zip into.
    """
    zipArchive = zipfile.ZipFile(filename)
    # We have to unpack things some where we can use them
    if hasattr(tempfile, "mkdtemp"):
        workingDir = tempfile.mkdtemp()
    else:
        workingDir = tempfile.mktemp()
        os.mkdir(workingDir)
    appFile = None
    for filename in zipArchive.namelist():
        parts = filename.split('.')
        if len(parts) == 2 and parts[1] == 'app':
            appFile = filename
        bytes = zipArchive.read(filename)
        out = file(os.path.join(workingDir, filename), "wb")
        out.write(bytes)
        out.close()

    if appFile == None:
        raise Exception, "Invalid Shared Application Package."

    
    return (appFile, workingDir)

def ProcessAppFile(appFile):
    """
    Process the Application File returning the appinfo and the command
    dictionary.
    """
    commands = dict()
    
    # Read in .app file
    appInfo = LoadConfig(appFile)

    # Build command list
    for key in appInfo.keys():
        spList = key.split('.')
        if len(spList) > 1:
            (section, option) = spList
            if section == "commands":
                verb = option
                cmd = appInfo[key]
                # If the named argument python is used, replace it
                if cmd.find("%(python)s") != -1:
                    cmd = cmd.replace("%(python)s", sys.executable)
                commands[verb] = cmd
    return appInfo, commands

def PrepPackageFromCmdLine(options):
    cleanup = 0
    workingDir = None
    appFile = None
    appInfo = None
    commands = None
    
    # specified specific .app file
    if options.appfile:
        if os.path.isabs(options.appfile):
            workingDir = os.path.dirname(options.appfile)
            appFile = os.path.basename(options.appfile)
        else:
            workingDir = os.getcwd()
            appFile = options.appfile

    # specified a directory
    if options.appdir:
        workingDir = os.path.abspath(options.appdir)
        files = os.listdir(workingDir)
        for filename in files:
            spList = filename.split('.')
            if len(spList) == 2:
                (name, ext) = spList
                if ext == "app":
                    appFile = filename

    # specified a .zip or .agpkg file
    if options.appzip:
        return PrepPackage(options.appzip)

    if options.apppkg:
        return PrepPackage(options.apppkg)

    if appFile is not None and workingDir is not None:
        appFile = os.path.join(workingDir, appFile)
        appInfo, commands = ProcessAppFile(appFile)
        
    return appInfo, commands, workingDir, cleanup
    
def PrepPackage(package):
    cleanup = 0
    workingDir = None
    appInfo = None
    commands = None
    appFile = None

    try:
        appFile, workingDir = UnpackPkg(package)
        appFile = os.path.join(workingDir, appFile)
        cleanup = 1
    except Exception:
        if workingDir is not None:
            shutil.rmtree(workingDir)
        raise
            
    if appFile is None:
        raise Exception, "No valid package specified, exiting."
    else:
        appInfo, commands = ProcessAppFile(appFile)
        
    return appInfo, commands, workingDir, cleanup

def UnregisterAppPackage(appdb, appInfo, name):
        if appInfo != None and name == None:
            name = appInfo["application.name"]
        if name != None:
            appdb.UnregisterApplication(name=name)
        else:
            raise Exception, "No application name discovered, exiting without doing unregister."

def RegisterAppPackage(appdb, dest, appInfo, commands, workingDir=None,
                    cleanup=0):
    origDir = os.getcwd()

    # Otherwise we go through and do the registration stuff...
    if workingDir != None and workingDir != '':
        # Change to the appropriate directory
        # This won't work for zipfiles
        os.chdir(workingDir)
        
    # Register the App
    files = appInfo["application.files"]
    if type(appInfo["application.files"]) is StringType:
        files = re.split(r',\s*|\s+', files)

    # Applications are "startable" (i.e. from the VenueClient) by default.
    if "application.startable" not in appInfo.keys():
        appInfo["application.startable"] = "1"

    appdb.RegisterApplication(appInfo["application.name"],
                              appInfo["application.mimetype"],
                              appInfo["application.extension"],
                              commands, files,
                              workingDir,
                              dstPath=dest,
                              startable=appInfo["application.startable"])

    # Clean up, remove the temporary directory and files from
    # unpacking the zip file
    if cleanup:
        os.chdir(origDir)
        if workingDir is not None:
            shutil.rmtree(workingDir)
            
            
def RegisterServicePackage(servicePackage):
    tkConf = AGTkConfig.instance()
    servicePackageFile = os.path.split(servicePackage)[1]
    servicePackagePath = os.path.join(tkConf.GetNodeServicesDir(),servicePackageFile)
    
    try:
        shutil.copy(servicePackage,servicePackagePath)
        # Set the permissions correctly
        os.chmod(servicePackagePath,0644)
    except Exception, e:
        print e
        return
    
    print "Registration of service %s complete." % (servicePackageFile,)
    

def UnregisterServicePackage(servicePackageFile):
    tkConf = AGTkConfig.instance()
    servicePackagePath = os.path.join(tkConf.GetNodeServicesDir(),servicePackageFile)
    
    try:
        os.remove(servicePackagePath)
        print "Unregistration of service package %s complete." % (servicePackageFile,)
    except Exception, e:
        print e


def main():
    """
    This is the main, this function processes command line arguments,
    then digs the files out of the directory, or archive and installs them.
    It registers the application with the users AG environment.
    """
    workingDir = os.getcwd()
    commands = dict()
    files = list()
    cleanup = 0

    tkConf = AGTkConfig.instance()
    
    # We're going to assume there's a .app file in the current directory,
    # but only after we check for a command line argument that specifies one.
    # We also have the ability to pass in a zip file that contains a .app
    # file and the other parts of the shared application.

    options, appdb, dest = ProcessArgs()

    #
    # Handle list-only options
    #
    if options.listapps:
        apps = appdb.ListApplications()
        import pprint
        pprint.pprint(apps)
        sys.exit(0)
        
    if options.listservices:
        files = os.listdir(tkConf.GetNodeServicesDir())
        for f in files:
            print f
        sys.exit(0)
        
        
    # 
    # Handle command-line errors
    #   
    if options.appfile and not os.path.exists(options.appfile):
        print "Error: app file does not exist:", options.appfile
        sys.exit(1)
    if options.appdir and not os.path.exists(options.appdir):
        print "Error: dir does not exist:", options.appdir
        sys.exit(1)
    if options.apppkg and not os.path.exists(options.apppkg):
        print "Error: package file does not exist:", options.apppkg
        sys.exit(1)
    if options.appzip and not os.path.exists(options.appzip):
        print "Error: zip file does not exist:", options.appzip
        sys.exit(1)
        
    #
    # Determine whether it's a service or app package
    #
    isServicePackage = 0
    if options.appzip or options.apppkg:
        
        try:
            filename=options.appzip or options.apppkg
            zipArchive = zipfile.ZipFile(filename)
            for filename in zipArchive.namelist():
                if filename.endswith('.svc'):
                    isServicePackage = 1
                    break
        except zipfile.BadZipfile,e:
            print "Error in zipfile %s: %s" % (filename,e.args[0])
            sys.exit(1)
            
    
    if options.unregisterservice:
        isServicePackage = 1
        
    #
    # Register/Unregister packages
    #    
    if isServicePackage:
    
        #
        # Handle a service package
        #
        if options.sys_install:
            print "(note: the -s flag is ignored for Service Packages since they are always installed in a system-wide location.)"

        filename=options.appzip or options.apppkg or options.appname
        if options.unregisterservice:
            if not options.appname:
                print "No service package specified to unregister"
                sys.exit(1)
            if options.verbose:
                print "Unregistering service package: ", filename
            UnregisterServicePackage(filename)
        else:
            if options.verbose:
                print "Registering service package: ", filename
            RegisterServicePackage(filename)
    
    else:
    
        #
        # Handle an application package
        #

        pkgList = []

        #
        # Post-install setup run
        #
        if options.post_install:
            pkgCache = tkConf.GetSharedAppDir()
            for pkg in os.listdir(pkgCache):
                fnl = pkg.split('.')
                if len(fnl) == 2:
                    (name, ext) = fnl
                    if ext == "agpkg":
                        pkgInfo = PrepPackage(os.path.join(pkgCache, pkg))
                        pkgList.append(pkgInfo)

        else:

            # At this point we have an appFile and workingDir
            try:
                pkgInfo = PrepPackageFromCmdLine(options)
                pkgList.append(pkgInfo)
            except Exception, e:
                print "Error in package file: ", e

        for pkg in pkgList:
            appInfo, commands, workingDir, cleanup = pkg

            if options.verbose:
                print "Name: %s" % appInfo["application.name"]
                print "Mime Type: %s" % appInfo["application.mimetype"]
                print "Extension: %s" % appInfo["application.extension"]
                print "From: %s" % workingDir

            # If we unregister, we do that then exit
            if options.unregister:
                if not options.appname:
                    print "No application specified for unregister"
                    sys.exit(1)
                UnregisterAppPackage(appdb, appInfo, options.appname)
            else:
                RegisterAppPackage(appdb, dest, appInfo, commands,
                                workingDir, cleanup)
    
    if options.wait_for_input:
        try:
            raw_input('AGPM: hit return to exit.')
        except EOFError:
            pass
        
if __name__ == "__main__":
    main()
