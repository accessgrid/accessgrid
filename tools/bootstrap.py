#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        CvsSetup.py
# Purpose:     Setup configuration files for development purposes without 
#              doing a full install.
#
# Author:      Eric Olson
#
# Created:     2003/04/17
# Copyright:   (c) 2002-2003
# License:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Use this if you want to run from source without having to perform a full
# installation.  See the "README-developers" file if you would like instructions 
# on how to use this setup utility.
#
# This allows us to run from cvs without depending on installed configuration
# files.  It creates the necessary configuration files in a directory you
# specify.
#
# After running this, you'll need to run the appropriate script to correctly 
# set your environment's PYTHONPATH and AGTK_LOCATION.
# This program will generate the scripts and ask you to execute the one
# that matches your system/shell.
#

import os
import sys
import shutil
import getopt
import re
from optparse import OptionParser

# Borrowed from Platform.py
WIN = 'win32'
LINUX = 'linux2'
OSX = 'darwin'

parser = OptionParser()
parser.add_option("-a", "--agdir", dest="agsrcdir", metavar="AGSRCDIR",
                  default="..",
                  help="Location of the AGTk Sources")
parser.add_option("-s", "--srcdir", dest="srcdir", metavar="SRCDIR",
                  default="../..",
                  help="Location of dependency sources (ag-media should reside here)")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  default=0, help="Run with verbose output.")
parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  default=0, help="Run in quiet mode with only error output.")

options, args = parser.parse_args()




#--------------------------------------------------------------------------------
# Initial configuration stuff
#--------------------------------------------------------------------------------


# Make sure we can find AG source.
file_to_find = os.path.join(options.agsrcdir, "AccessGrid", "Version.py")
if not (os.path.exists( file_to_find )):
    parser.print_help()
    print "Cannot find AG source dir.", file_to_find, " not found." 
    sys.exit()

# Get absolute paths for when we need to pass them to python.exe later.
ABS_AG_BASE_DIR = os.path.abspath(options.agsrcdir)
ABS_SRC_DIR = os.path.abspath(options.srcdir)

# Set AGTK_LOCATION so we can use the toolkit's initialization functions.
os.environ["AGTK_LOCATION"] = ABS_AG_BASE_DIR
# Add to PYTHONPATH
sys.path.insert(0, os.path.abspath(options.agsrcdir))

# New config using AGTkConfig
from AccessGrid.Platform.Config import AGTkConfig
# Create directory structure
agtkConfig = AGTkConfig.instance(initIfNeeded=1)
agtk_location = os.path.join(os.path.abspath(options.agsrcdir))
python_path = os.path.abspath(options.agsrcdir)



#--------------------------------------------------------------------------------
# Make shared app packages
#--------------------------------------------------------------------------------
print "Building shared application packages"
# python2 makeAppPackages.py inputdir sharedappconfigdir
cmd = "%s %s %s %s" % (sys.executable,
                       os.path.join( options.agsrcdir, "packaging", "makeAppPackages.py" ),
                       os.path.join(ABS_AG_BASE_DIR,'sharedapps'),
                       AGTkConfig.instance().GetSharedAppDir())
if options.verbose:
    print "   ",cmd
os.system(cmd)




#--------------------------------------------------------------------------------
# Make service packages
#--------------------------------------------------------------------------------
print "Building service packages"
# python packaging/makeServicePackages.py /path/to/AccessGrid  /path/to/source (ag-media should be found under here)

mk_service_exec = sys.executable + " " + os.path.join( options.agsrcdir, "packaging", "makeServicePackages.py" )
service_input_dir = "\"" + ABS_AG_BASE_DIR + "\""
service_output_dir = AGTkConfig.instance().GetNodeServicesDir()
mk_command = "%s --sourcedir %s --agsourcedir %s --outputdir %s" % (mk_service_exec, 
                    ABS_SRC_DIR, service_input_dir, service_output_dir)
if options.verbose:
    print "   ",mk_command
os.system(mk_command)


print "Creating local configuration directories"
#--------------------------------------------------------------------------------
# Make local service directory for caching services.
#--------------------------------------------------------------------------------
localServicePath = os.path.join( AGTkConfig.instance().GetConfigDir(), "local_services")
if not os.path.exists(localServicePath):
    os.mkdir(localServicePath)

#--------------------------------------------------------------------------------
# Make nodeConfig directory so we can put configuration files into it.
#--------------------------------------------------------------------------------
nodeConfigPath = os.path.join( AGTkConfig.instance().GetConfigDir(), "nodeConfig")
if not os.path.exists(nodeConfigPath):
    os.mkdir(nodeConfigPath)

#--------------------------------------------------------------------------------
# Copy certificates
#--------------------------------------------------------------------------------
print "Copying certificates to local configuration directories"
srcCACertDir = os.path.join(ABS_AG_BASE_DIR, "packaging", "config", "CAcertificates")
CACertDir = os.path.join(agtkConfig.GetConfigDir(), "CAcertificates")
print "Copying CA certificates from %s to %s" %( srcCACertDir, CACertDir)
if not os.path.exists(CACertDir):
    os.mkdir(CACertDir)
for filename in os.listdir(srcCACertDir):
    if filename in ['.svn']:
        continue
    if "." in filename: 
        shutil.copy2( os.path.join(srcCACertDir, filename), CACertDir)


#--------------------------------------------------------------------------------
# Generate Interfaces
#--------------------------------------------------------------------------------
print "Generating web service interface code"
origDir = os.getcwd()
os.chdir(os.path.join(agtk_location, "tools"))
if sys.platform == WIN:
    os.system( "set PYTHONPATH=%s && " % python_path + " " + sys.executable + " " + os.path.join(".", "GenerateInterfaces.py") + " --quiet" )
else:
    os.system( "export PYTHONPATH=%s; " % python_path + " " + sys.executable + " " + os.path.join(".", "GenerateInterfaces.py") + " --quiet" )
os.chdir(origDir)


#--------------------------------------------------------------------------------
# Build device discovery executables
#--------------------------------------------------------------------------------
os.system("%s\\tools\\makewdmscan.bat %s" % (ABS_AG_BASE_DIR,ABS_AG_BASE_DIR))
os.system("%s\\tools\\makevfwscan.bat %s" % (ABS_AG_BASE_DIR,ABS_AG_BASE_DIR))

#--------------------------------------------------------------------------------
# Write environment initialization files
#--------------------------------------------------------------------------------
from AccessGrid.Platform import isOSX, isLinux, isWindows
print "Writing environment initialization files"
if isLinux() or isOSX():

    #
    # Write bourne/bash shell version
    #
    
    fh = open("env-init.sh", "w")
    fh.write("""
export AGTK_LOCATION=%(agtk_location)s

DELIM=
if [ -n "$PYTHONPATH" ] ; then
    DELIM=:
fi
export PYTHONPATH=${PYTHONPATH}${DELIM}%(python_path)s
""" % locals())
    fh.close()

    #
    # Write csh version
    #

    fh = open("env-init.csh", "w")
    fh.write("""
setenv AGTK_LOCATION %(agtk_location)s
if ($?PYTHONPATH) then
    setenv PYTHONPATH ${PYTHONPATH}:%(python_path)s
else
    setenv PYTHONPATH %(python_path)s
endif
""" % locals())
    fh.close()
    if not options.quiet:
        print "Wrote csh config to env-init.csh, bash config to env-init.sh"
    
elif isWindows():
    fh = open("env-init.bat", "w")
    fh.write("set AGTK_LOCATION=%s\n" % (agtk_location))
    fh.write("set PYTHONPATH=%s\n" % (python_path))
    fh.close()
    if not options.quiet:
        print "Wrote win32 batchfile init to env-init.bat"
else:
    print "Error, a script appropriate for your platform has not been defined.  Please add it to CvsSetup.py"




#--------------------------------------------------------------------------------
# Tell users how to use the new configuration files.
#--------------------------------------------------------------------------------
if not options.quiet:
    print "\n    --------------------------------------------------------------"
    print ""
    print "    To use this configuration:\n"
    print "       Make sure media-related programs (vic, rat, etc.) are in your path."
    if isWindows():
        print "          On Windows: copying the vic and rat related binaries (if needed, "
        print "          from a real install) into their own directory before adding them "
        print "          to your path is recommended.  If you don't want to bother modifying "
        print "          your path, copying them into AccessGrid/bin is a quick fix.\n"
    elif isLinux() or isOSX():
        print "          On linux: if you've installed the vic and rat rpm packages,"
        print "          they should already be in your path.\n"
    else:
        print "Error, your platform is not defined.  Please add it to CvsSetup.py"

    print "       set AGTK_LOCATION to", agtk_location
    print "       set PYTHONPATH to", python_path
    print ""




