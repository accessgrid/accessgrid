#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        RegisterApp.py
# Purpose:     This registers an application with the users venue client.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: agpm.py,v 1.8 2004-03-16 03:09:51 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
This program is used to register applications with the users AGTk
installation.
"""
__revision__ = "$Id: agpm.py,v 1.8 2004-03-16 03:09:51 judson Exp $"

import os
import re
from types import StringType
import sys
import getopt
import zipfile
import tempfile

if sys.version.startswith('2.2'):
    try:
        from optik import OptionParser
    except:
        raise Exception, "Missing module optik necessary for the AG Toolkit."

if sys.version.startswith('2.3'):
    try:
        from optparse import OptionParser
    except:
        raise Exception, "Missing module optparse, check your python installation."

from AccessGrid.AppDb import AppDb
from AccessGrid.Utilities import LoadConfig
from AccessGrid.Platform.Config import SystemConfig

tempfile.tmpdir = SystemConfig.instance().GetTempDir()

def ProcessArgs():
    """
    """
    doc = """
    By default this program registers/installs a shared application
    with the users environment. Using the -u argument applications can
    be unregistered/uninstalled.
    """

    parser = OptionParser(doc)
    parser.add_option("-u", "--unregister", action="store_true",
                      dest="unregister", default=0,
          help="Unregister the application, instead of registering it.")
    parser.add_option("-n", "--name", dest="appname",
          help="specify a name other than the default on from the .app file.")
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=0, help="Be verbose during app processing.")
    parser.add_option("-f", "--file", dest="appfile",
          help="The name of a .app file to install.")
    parser.add_option("-d", "--dir", dest="appdir",
                      help="The name of a directory containing a .app file.")
    parser.add_option("-z", "--zip", dest="appzip",
                      help="The name of a .zip file containing a .app file.")
    parser.add_option("-p", "--package", dest="apppkg",
                    help="The name of an app package containing a .app file.")
    parser.add_option("-l", "--list-apps", action="store_true",
                      dest="listapps", help="List installed shared apps.")
    
    (options, args) = parser.parse_args()

    return options

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
    cleanup = 0
    
    appdb = AppDb()

    # We're going to assume there's a .app file in the current directory,
    # but only after we check for a command line argument that specifies one.
    # We also have the ability to pass in a zip file that contains a .app
    # file and the other parts of the shared application.

    options = ProcessArgs()

    if options.listapps:
        apps = appdb.ListApplications()
        import pprint
        pprint.pprint(apps)
        sys.exit(0)
        
    if options.appfile:
        if os.path.isabs(options.appfile):
            workingDir = os.path.dirname(options.appfile)
            appFile = os.path.basename(options.appfile)
        else:
            appFile = options.appfile

    if options.appdir:
        workingDir = os.path.abspath(options.appdir)

    if options.appzip:
        appFile, workingDir = UnpackZip(options.appzip)
        cleanup = 1

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
    if options.unregister:
        if appInfo != None and options.appname == None:
            options.appname = appInfo["application.name"]
        if options.appname != None:
            appdb.UnregisterApplication(name=options.appname)
        else:
            print "No application name discovered, exiting without doing \
                   unregister."
        sys.exit(0)

    if options.verbose:
        print "Name: %s" % options.appname
        print "Mime Type: %s" % appInfo["application.mimetype"]
        print "Extension: %s" % appInfo["application.extension"]
        print "From: %s" % workingDir

    # Register the App
    if options.appname == None:
        options.appname = appInfo["application.name"]
    files = appInfo["application.files"]
    if type(files) is StringType:
        files = re.split(r',\s*|\s+', files)

    appdb.RegisterApplication(options.appname,
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
