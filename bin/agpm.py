#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        RegisterApp.py
# Purpose:     This registers an application with the users venue client.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: agpm.py,v 1.7 2004-03-15 21:44:59 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is used to register applications with the users AGTk
installation.
"""
__revision__ = "$Id: agpm.py,v 1.7 2004-03-15 21:44:59 judson Exp $"

import os
import re
from types import StringType
import sys
import getopt
import zipfile
import tempfile

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.Utilities import LoadConfig
from AccessGrid.Platform import GetTempDir

tempfile.tmpdir = GetTempDir()

def Usage():
    """
    This 'splains how to use this program. You can get help with -h.
    """
    
    print "%s:" % sys.argv[0]
    print "     -n|--name : specify a name other than the default one "
    print "                 (from the .app file for this shared application"
    print "     -u|--unregister : unregister the application"
    print "     -f|--file : <.app file>"
    print "     -d|--dir : <directory containing a .app file>"
    print "     -z|--zip : <zip archive containing a .app file>"
    print "     -p|--package : <package archive containing a .app file>"
    print "     -h|--help : This help."
    print """
    By default this program registers/installs a shared application
    with the users environment. Using the -u argument applications can
    be unregistered/uninstalled.
    """

def UnpackZip(filename):
    """
    This function takes the name of a zip file and unpacks it returning the
    directory it unpacked the zip into.
    """
    zipArchive = zipfile.ZipFile(filename)
    # We have to unpack things some where we can use them
    workingDir = tempfile.mktemp()
    os.mkdir(workingDir)
    for filename in zipArchive.namelist():
        parts = filename.split('.')
        if len(parts) == 2 and (parts[1] == 'app'
                                or parts[1] == 'shared_app_pkg'):
            appFile = filename
        bytes = zipArchive.read(filename)
        out = file(os.path.join(workingDir, filename), "wb")
        out.write(bytes)
        out.close()

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

def main():
    """
    This is the main, this function processes command line arguments,
    then digs the files out of the directory, or archive and installs them.
    It registers the application with the users AG environment.
    """
    workingDir = os.getcwd()
    appFile = None
    zipFile = None
    commands = dict()
    files = list()
    origDir = os.getcwd()
    appName = None
    verbose = 0
    unregister = 0
    cleanup = 0
    
    app = CmdlineApplication()
    appdb = app.GetAppDatabase()

    # We're going to assume there's a .app file in the current directory,
    # but only after we check for a command line argument that specifies one.
    # We also have the ability to pass in a zip file that contains a .app
    # file and the other parts of the shared application.
    
    try:
        opts = getopt.getopt(sys.argv[1:], "f:d:z:n:p:huv", ["file=",
                                                             "dir=",
                                                             "zip=",
                                                             "name=",
                                                             "package=",
                                                             "unregister",
                                                             "verbose",
                                                             "help"])[0]
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    if len(opts) == 0:
        Usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ("-f", "--file"):
            if os.path.isabs(arg):
                workingDir = os.path.dirname(arg)
                appFile = os.path.basename(arg)
            else:
                appFile = arg
        elif opt in ("-d", "--dir"):
            workingDir = os.path.abspath(arg)
        elif opt in ("-z", "--zip", "-p", "--package"):
            # Unpack the zip archive
            # We get back the appfile and directory
            appFile, workingDir = UnpackZip(arg)
            cleanup = 1
        elif opt in ("-u", "--unregister"):
            unregister = 1
        elif opt in ("-n", "--name"):
            appName = arg
        elif opt in ("-v", "--verbose"):
            verbose = 1
        elif opt in ("-h", "--help"):
            Usage()
            sys.exit(0)

    # If no appfile is specified, search the current directory for one
    if appFile == None:
        files = os.listdir(os.getcwd())
        for filename in files:
            spList = filename.split('.')
            if len(spList) == 2:
                (name, ext) = spList
                if ext == "app":
                    appFile = filename

    # Otherwise we go through and do the registration stuff...
    if workingDir != None and workingDir != '':
        # Change to the appropriate directory
        # This won't work for zipfiles
        os.chdir(workingDir)

    # Process the App File we've gotten
    appInfo = None
    if appFile:
        appInfo, commands = ProcessAppFile(appFile)
                
    # If we unregister, we do that then exit
    if unregister:
        if appInfo != None and appName == None:
            appName = appInfo["application.name"]
        if appName != None:
            appdb.UnregisterApplication(name=appName)
        else:
            print "No application name discovered, exiting without doing \
                   unregister."
        sys.exit(0)

    if verbose:
        print "Name: %s" % appName
        print "Mime Type: %s" % appInfo["application.mimetype"]
        print "Extension: %s" % appInfo["application.extension"]
        print "From: %s" % workingDir

    # Register the App
    if appName == None:
        appName = appInfo["application.name"]
    files = appInfo["application.files"]
    if type(files) is StringType:
        files = re.split(r',\s*|\s+', files)

    appdb.RegisterApplication(appName,
                              appInfo["application.mimetype"],
                              appInfo["application.extension"],
                              commands, files,
                              workingDir)

    # Clean up, remove the temporary directory and files from
    # unpacking the zip file
    if cleanup:
        import shutil
        os.chdir(origDir)
        shutil.rmtree(workingDir)
        
if __name__ == "__main__":
    main()
