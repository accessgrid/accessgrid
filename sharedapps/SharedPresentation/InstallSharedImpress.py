#-----------------------------------------------------------------------------
# Name:        InstallSharedImpress.py
# Purpose:     This is to install the Shared Presentation Software.  
#
# Author:      Eric C. Olson
#
# Created:     2003/10
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------    

# Normal import stuff
import os
import sys
import getopt
import logging
from threading import Thread
import Queue
import shutil

from wxPython.wx import *

# Imports we need from the Access Grid Module
from AccessGrid.Events import ConnectEvent, Event
from AccessGrid import Platform
from AccessGrid import DataStore
from AccessGrid.Toolkit import CmdlineApplication, UserConfig
from AccessGrid.AppDb import AppDb
from AccessGrid import Toolkit


def registerApp(fileNames):
    import AccessGrid.Toolkit as Toolkit
    #app = Toolkit.GetApplication()
    #if app == None:
        #app = Toolkit.CmdlineApplication()
    app = Toolkit.CmdlineApplication.instance()

    appdb = AppDb()

    fn_list = []
    for f in fileNames:
        fn_list.append(os.path.basename(f))

    exeCmd = sys.executable + " " + fn_list[0] + " -v %(venueUrl)s -a %(appUrl)s"

    # Call the registration method on the applications database
    appdb.RegisterApplication("Shared Presentation",
                              "application/x-ag-shared-presentation",
                              "sharedpresentation",
                              {"Open" : exeCmd },
                              fn_list, os.getcwd())


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Utility functions
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def Usage():
    print "\n%s:" % (sys.argv[0])
    print " -o|--oohomedir:                 (required) Path to OpenOffice home directory"
    print "                                     (example: /usr/lib/openoffice)"
    print " -p|--systempythonpackages:      (optional) Location of python's AccessGrid and"
    print "                                     supporting packages."
    print "                                     (default: /usr/lib/python2.2/lib/site-packages)"
    print " -a|--additionalpythonpackages:  (optional) Additional location to search for"
    print "                                     AccessGrid or supporting packages."
    print "                                     (i.e. if first location is AG cvs)"
    print " -h|--help:                      print usage"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# MAIN block
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":

    if sys.platform == Platform.WIN:
        PythonPackageDir = "\Python22\Lib\site-packages"
    else:
        PythonPackageDir = "/usr/lib/python2.2/site-packages"
    # Directory to copy additional packages from.
    AdditionalPyPackageDir = ""
    OOHomeDir = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:p:a:i:h",
                                   ["oohomedir=", "systempythonpackages=", "additionalpythonpackages=", "help"])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    # Process args
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            self.__Usage()
            sys.exit(0)
        elif opt in ('--oohomedir', '-o'):
            OOHomeDir = arg
        elif opt in ('--systempythonpackages', '-p'):
            PythonPackageDir = arg
        elif opt in ('--additionalpythonpackages', '-a'):
            AdditionalPyPackageDir = arg

    if len(OOHomeDir) < 1:
        Usage()
        print "\nPlease specify the path to OpenOffice home directory ( -o flag ).\n"
        sys.exit(2)

    if not os.path.exists(OOHomeDir):
        Usage()
        print "\nOpenOffice home directory specified does not exist.\n"
        sys.exit(2)

    if not os.path.exists(PythonPackageDir):
        print "\nPython packages directory does not exist.  Please specify correct path ( -p flag ).\n"
        sys.exit(2)

    if len(AdditionalPyPackageDir) > 0 and not os.path.exists(AdditionalPyPackageDir):
        print "\nAdditional Python packages directory does not exist.  Please specify correct path ( -p flag ).\n"
        sys.exit(2)

    app = CmdlineApplication.instance()

    #AGPackages = ["wxPython","OpenSSL_AG", "pyGlobus", "logging", "AccessGrid"]
    AGPackages = ["wxPython","OpenSSL_AG", "pyGlobus", "logging", "AccessGrid", "fpconst.py"]
    
    # Unregister old version
    #appdb = app.GetAppDatabase()
    #appName = "Shared Presentation"
    #if appdb.GetMimeType(appName) != None:
        #print "Unregistering old version of Shared Presentation"
        #appdb.UnregisterApplication(appName)

    # Creating file to store the paths the user has given us.
    GetPathsTmpFile = 'GetPaths.py'
    f=file(GetPathsTmpFile, 'w')
    # write a command to get the path to OpenOffice
    f.write("\ndef GetOOHomeDir():\n    return r\"" + OOHomeDir + "\"\n")
    f.close()

    print "Registering."
    try:
        registerApp(["StartImpress.py", "SharedPresentation.py", "ImpressViewer.py", GetPathsTmpFile])
    except Exception, e:
        print "Unable to register application."
        raise e


    # To control OpenOffice, we need to use its python because of
    #   compiled in support (this may change later).
    appdb = AppDb()
    name = appdb.GetNameForMimeType("application/x-ag-shared-presentation")
    appDir = None
    if name != None:
        appName = '_'.join(name.split(' '))
        appDir = os.path.join(Toolkit.UserConfig.instance().GetSharedAppDir(), appName)
    if not appDir or not os.path.exists(appDir):
        print "Unable to determine app path."
        sys.exit(2)

    AGPackages = ["wxPython","OpenSSL_AG", "pyGlobus", "logging", "AccessGrid", "SOAPpy"]
    print "Copying/Refreshing AG modules to shared presentation installation."
    try:
        for package in AGPackages:
            src = os.path.join(PythonPackageDir, package)
            if not os.path.exists(src):
                if len(AdditionalPyPackageDir) > 0:
                    src1 = src
                    src = os.path.join(AdditionalPyPackageDir, package)
                    if not os.path.exists(src):
                        raise "Packages paths do not exist:" + src1 + ", " + src
                if not os.path.exists(src):
                    raise "Packages path does not exist:" + src
            dst = os.path.join(appDir, package)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    except Exception, e:
        print "Unable to copy files."
        raise e

    # Clean up temporary files.
    os.remove(GetPathsTmpFile)

    print "Done.  (Run this installer again if you update your AccessGrid software.)"

