#
# Build a windows installer snapshot.
#

#
# Basic plan:
#
# This script assumes there is a build directory somewhere with
# basically everything in place to build a distribution.
# invoke the innosetup compiler on the modified iss file
# Also need to modify setup.py to change the version there to match
# this snapshot version.
#
import sys
import os
import time
import getopt
import shutil
import win32api
import _winreg
import logging
from optparse import OptionParser

from win32com.shell import shell, shellcon

# Source Directory
#  We assume the following software is in this directory:
#    ag-rat, ag-vic, and AccessGrid
SourceDir = os.environ['AGBUILDROOT']

#
# Get the version via popen
#
try:
    cmd = "%s %s" % (sys.executable, os.path.join(SourceDir, "AccessGrid",
                                                  "AccessGrid", "Version.py"))
    po = os.popen(cmd)
except IOError:
    print "Error getting AGTk Version."

version = po.read()
po.close()

version = version[:-1]

#
# Parse command line options
#

parser = OptionParser()
parser.add_option("-s", "--sourcedir", dest="sourcedir", metavar="SOURCEDIR",
                  default=None,
                  help="The directory the AG source code is in.")
parser.add_option("-m", "--meta", dest="metainfo", metavar="METAINFO",
                  default=None,
                  help="Meta information string about this release.")
parser.add_option("-c", "--checkoutcvs", action="store_true", dest="cvs",
                  default=1,
                  help="A flag that indicates the snapshot should be built from anexported cvs checkout.")
parser.add_option("-i", "--innopath", dest="innopath", metavar="INNOPATH",
                  default="", help="The path to the isxtool.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=0,
                  help="A flag that indicates to build verbosely.")
parser.add_option("-p", "--pythonversion", dest="pyver",
                  metavar="PYTHONVERSION", default="2.2",
                  help="Which version of python to build the installer for.")

options, args = parser.parse_args()

#
# The openssl in winglobus is critical put it in our path
#
oldpath = os.environ['PATH']
os.environ['PATH'] = os.path.join(SourceDir, "WinGlobus", "bin")+";"+oldpath

# Build Name
#  This is the default name we use for the installer
BuildTime = time.strftime("%Y%m%d-%H%M%S")

# Names for the software
if options.metainfo is not None:
    metainfo = options.metainfo
else:
    metainfo = "Snapshot %s" % BuildTime

# Create the dest dir stamped with the same time stamp
DestDir = os.path.join(SourceDir, "dist-%s" % BuildTime)

# The directory we're building from
BuildDir = os.path.join(SourceDir, "AccessGrid-%s" % BuildTime)

# Grab innosetup from the environment
try:
    ipreg = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            "Software\\Bjornar Henden\\ISTool4\\Prefs")
    innopath, type = _winreg.QueryValueEx(ipreg, "InnoFolder")
    ip = os.path.join(innopath, "iscc.exe")
    inno_compiler = win32api.GetShortPathName(ip)
except WindowsError:
    print "BUILD: Couldn't find iscc from registry key." 
    
    # If still not found, try default path:
    innopath = r"\Program Files\ISTool 4"
    inno_compiler = os.path.join(innopath, "iscc.exe")

# Innosoft config file names
iss_orig = "agtk.iss"

#
# Location of the Inno compiler
#
if options.innopath != "":
    # It was set on the command line
    inno_compiler = os.path.join(options.innopath, "iscc.exe")
    if options.verbose:
        if os.path.exists(inno_compiler):
            print "BUILD: Found ISXTool in default path:", inno_compiler
        else:
            print "BUILD: Couldn't find ISXTool!"
            print "BUILD:   Make sure My Inno Setup Extentions are installed."
            print "BUILD:   If necessary, specify the location of iscc.exe "
            print "BUILD:   with command-line option -i."
            sys.exit()
#
# Grab stuff from cvs
#

if options.cvs:
    # Either we check out a copy
    cvsroot = ":pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl"

    # WE ASSUME YOU HAVE ALREADY LOGGED IN WITH:
    # cvs -d :pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl login

    cvs_cmd = "cvs -z6 -d %s export -d %s -D now AccessGrid" % (cvsroot,
                                                                BuildDir)
    if options.verbose:
        print "BUILD: Checking out code with command: ", cvs_cmd

    os.system(cvs_cmd)

#
# Go to that checkout to build stuff
#

RunDir = os.path.join(BuildDir, "packaging", "windows")

if options.verbose:
    print "BUILD: Changing to directory: %s" % RunDir
    
os.chdir(RunDir)

#
# Run the setup script first to create the distribution directory structure
# and auxillary packages, config, and documentation
#
s = os.getcwd()
os.chdir(BuildDir)

cmd = "%s %s" % (sys.executable, "setup.py")
for c in ["clean", "build"]:
    os.system("%s %s" % (cmd, c))

os.system("%s install --prefix=%s --no-compile" % (cmd, DestDir))

os.chdir(s)

#
# Run precompile scripts
#

for cmd in [
    "BuildVic.cmd",
    "BuildRat.cmd",
    # I have decided we'll assume these are built *outside* of our build
    # process, so we don't build globus in either packaging anymore.
    #"BuildGlobus.cmd",
    "BuildPythonModules.cmd"
    ]:
    cmd = "%s %s %s %s %s" % (cmd, SourceDir, BuildDir, DestDir, options.pyver)
    if options.verbose:
        print "BUILD: Running: %s" % cmd

    os.system(cmd)

#
# Now we can compile
#

# Add quotes around command.
iscc_cmd = "%s %s /dAppVersion=\"%s\" /dVersionInformation=\"%s\" \
            /dSourceDir=\"%s\" /dBuildDir=\"%s\" /dPythonVersion=\"%s\"" % \
            (inno_compiler, iss_orig, version, metainfo.replace(' ', '_'), \
             SourceDir, DestDir, options.pyver)

if options.verbose:
    print "BUILD: Executing:", iscc_cmd

os.system(iscc_cmd)

