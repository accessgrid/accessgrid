#-----------------------------------------------------------------------------
# Name:        RegisterApp.py
# Purpose:     This registers an application with the users venue client.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: RegisterApp.py,v 1.1 2003-09-15 15:09:17 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

import os
import sys
import getopt
import ConfigParser

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.Utilities import LoadConfig

"""
This program registers a shared application with a users AGTk installation.
"""

def Usage():
    """
    'splains how to use this program.
    """
    
    print "%s:" % sys.argv[0]
    print "     -u|--unregister : unregister the application"
    print "     -f|--file : <.app file>"
    print "     -d|--dir : <directory containing a .app file>"
    print "     -z|--zip : <zip archive containing a .app file>"
    print "     -h|--help : This help."
    print "\nBy default this program registers/installs a shared application with the users environment. Using the -u argument applications can be unregistered/uninstalled."
    
def main():
    """
    """
    workingDir = None
    appFile = None
    commands = dict()
    files = list()
    
    # We're going to assume there's a .app file in the current directory,
    # but only after we check for a command line argument that specifies one.
    # Later we can add support for zipfiles, it should be pretty simple
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "f:d:z:hu", ["file=",
                                                               "dir=",
                                                               "zip=",
                                                               "unregister",
                                                               "help"])
    except getopt.GetopError:
        Usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-f", "--file"):
            workingDir = dirname(appFile)
            appFile = basename(appFile)
        elif o in ("-d", "--dir"):
            workingDir = a
        elif o in ("-z", "--zip"):
            print "Zip file support is not complete."
            print "Please specify the .app file with --file."
        elif o in ("-u", "--unregister"):
            print "Unregistering applications does not work yet."
        elif o in ("-h", "--help"):
            Usage()
            sys.exit(0)

    if workingDir != None and workingDir != '':
        # Change to the appropriate directory
        # This won't work for zipfiles
        os.chdir(workingDir)

    # If no appfile is specified, search the current directory for one
    if appFile == None:
        files = os.listdir(os.getcwd())
        for f in files:
            spList = f.split('.')
            if len(spList) > 1:
                (name, ext) = spList
                if ext == "app":
                    appFile = f
                    
    # Read in .app file
    appInfo = LoadConfig(appFile)
    
    # get setup for registration
    name = appInfo["application.name"]
    mimeType = appInfo["application.mimetype"]
    extension = appInfo["application.extension"]
    files = appInfo["application.files"].split(' ')

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
                
    # Register the App
    app = CmdlineApplication()
    appdb = app.GetAppDatabase()
    appdb.RegisterApplication(name, mimeType, extension, commands, files,
                              os.getcwd())

if __name__ == "__main__":
    main()
