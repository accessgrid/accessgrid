#!/usr/bin/python2
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

options, args = parser.parse_args()

# Make sure we can find AG source.

file_to_find = os.path.join(options.agsrcdir, "AccessGrid", "Version.py")
if not (os.path.exists( file_to_find )):
    PrintUsage()
    print "Cannot find AccessGrid source location.", file_to_find, " not found." 
    sys.exit()

# Get absolute paths for when we need to pass them to python.exe later.
ABS_AG_BASE_DIR = os.path.abspath(options.agsrcdir)
ABS_SRC_DIR = os.path.abspath(options.srcdir)

# Overview: 
# Create Toolkit configuration with AGTkConfig
# python packaging/makeServicePackages.py 
# cp packaging/config/defaultWindows AGTkConfig.instance().GetConfigDir()
# cp packaging/config/defaultLinux AGTkConfig.instance().GetConfigDir()
# cp packaging/config/CACertificates AGTkConfig.instance().GetConfigDir()/CACertificates
# 

print ""

# Set AGTK_LOCATION so we can use the toolkit's initialization functions.
os.environ["AGTK_LOCATION"] = ABS_AG_BASE_DIR
# Add to PYTHONPATH
sys.path.insert(0, os.path.abspath(options.agsrcdir))

# New config using AGTkConfig
from AccessGrid.Platform.Config import AGTkConfig
# Create directory structure
agtkConfig = AGTkConfig.instance(initIfNeeded=1)

# Make shared app packages
#
# python2 makeAppPackages.py inputdir sharedappconfigdir
cmd = "%s %s %s %s" % (sys.executable,
                       os.path.join( options.agsrcdir, "packaging", "makeAppPackages.py" ),
                       os.path.join(ABS_AG_BASE_DIR,'sharedapps'),
                       AGTkConfig.instance().GetSharedAppDir())
if options.verbose:
    print "   ",cmd
os.system(cmd)


# Make service packages
# python packaging/makeServicePackages.py /path/to/AccessGrid  /path/to/source (ag-media should be found under here)

mk_service_exec = sys.executable + " " + os.path.join( options.agsrcdir, "packaging", "makeServicePackages.py" )
service_input_dir = "\"" + ABS_AG_BASE_DIR + "\""
service_output_dir = AGTkConfig.instance().GetNodeServicesDir()
mk_command = "%s %s %s %s" % (mk_service_exec, ABS_SRC_DIR, service_input_dir, service_output_dir)
if options.verbose:
    print "   ",mk_command
os.system(mk_command)

# Make local service directory for caching services.
localServicePath = os.path.join( AGTkConfig.instance().GetConfigDir(), "local_services")
if not os.path.exists(localServicePath):
    os.mkdir(localServicePath)

# Make nodeConfig directory so we can put configuration files into it.
nodeConfigPath = os.path.join( AGTkConfig.instance().GetConfigDir(), "nodeConfig")
if not os.path.exists(nodeConfigPath):
    os.mkdir(nodeConfigPath)

# copy certificates
srcCACertDir = os.path.join(ABS_AG_BASE_DIR, "packaging", "config", "CAcertificates")
CACertDir = os.path.join(agtkConfig.GetConfigDir(), "CAcertificates")
print "Copying CA certificates from %s to %s" %( srcCACertDir, CACertDir)
if not os.path.exists(CACertDir):
    os.mkdir(CACertDir)
for filename in os.listdir(srcCACertDir):
    if "." in filename: 
        shutil.copy2( os.path.join(srcCACertDir, filename), CACertDir)

# Copy default configuration files
if sys.platform == WIN:
    win_config_src = os.path.join( options.agsrcdir, "packaging", "config", "defaultWindows")
    win_config_dst = os.path.join( nodeConfigPath, "defaultWindows")
    #if options.verbose:
        #print "    copying file ", win_config_src, "to ", win_config_dst
    #shutil.copyfile( win_config_src, win_config_dst )

    # Remove the "c:\program files\access grid toolkit" in the defaultWindows file so we don't require a previous installation.
    executable_path_replace = re.compile('c:\\\\program files\\\\access grid toolkit\\\\')

    print "\n    Creating file", win_config_dst, "from", win_config_src
    if options.verbose:
        print "        removing \"c:\\program files\\access grid toolkit\\\" from rat and vic paths"

    file = open(win_config_src) 
    new_file = open(win_config_dst, "w")

    # Remove the path 
    for line in file:
        if line.startswith("executable"): 
            line = executable_path_replace.sub("", line)
        new_file.write(line)

    file.close()
    new_file.close()

# copy defaultLinux file if we are using linux
if sys.platform == LINUX or sys.platform == OSX:
    unix_config_src = os.path.join( options.agsrcdir, "packaging", "config", "defaultLinux")
    unix_config_dst = os.path.join( nodeConfigPath, "defaultLinux")
    if options.verbose:
        print "    copying file ", unix_config_src, "to ", unix_config_dst

    shutil.copyfile( unix_config_src, unix_config_dst )


# Define function to help manage config files.
# Copies filename to backup_filename if it exists.
def BackupFile(filename, backup_filename):

    # Remove backup file if it already exists

    if os.path.exists(backup_filename):
        os.remove(backup_filename)

    # Copy file to backup if needed.

    if os.path.exists(filename):
        if options.verbose:
            print "    copying file ", filename, "to ", backup_filename
        shutil.copyfile(filename, backup_filename)



# Create AGNodeService.cfg
config_file = os.path.join(AGTkConfig.instance().GetConfigDir(),
                           "AGNodeService.cfg")
bak_file = os.path.join(AGTkConfig.instance().GetConfigDir(),
                        "AGNodeService.cfg.bak")

BackupFile(config_file, bak_file)

nsfile = open(config_file, 'w', )
nsfile.write("[Node Configuration]\n")
nsfile.write("configDirectory = " + os.path.join("Config", "nodeConfig") + "\n")
if sys.platform == WIN:
    nsfile.write("defaultNodeConfiguration = defaultWindows\n\n")
elif sys.platform == LINUX or sys.platform == OSX:
    nsfile.write("defaultNodeConfiguration = defaultLinux\n\n")
nsfile.close()

agtk_location = os.path.join(os.path.abspath(options.agsrcdir))
python_path = os.path.abspath(options.agsrcdir)

# Tell users how to use the new configuration files.
print "\n    --------------------------------------------------------------"
print ""
print "    To use this configuration:\n"
print "       Make sure media-related programs (vic, rat, etc.) are in your path."
from AccessGrid.Platform import isOSX, isLinux, isWindows
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
    print "Wrote csh config to env-init.csh, bash config to env-init.sh"
    
elif isWindows():
    fh = open("env-init.bat", "w")
    fh.write("set AGTK_LOCATION=%s\n" % (agtk_location))
    fh.write("set PYTHONPATH=%s\n" % (python_path))
    fh.close()
    print "Wrote win32 batchfile init to env-init.bat"
else:
    print "Error, a script appropriate for your platform has not been defined.  Please add it to CvsSetup.py"

