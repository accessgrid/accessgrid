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
# set your environment's PYTHONPATH, AGTK_LOCATION, and AGTK_INSTALL_DIR.
# This program will generate the scripts and ask you to execute the one
# that matches your system/shell.
#


import os
import sys
import shutil
import getopt
import re


# Borrowed from Platform.py
WIN = 'win32'
LINUX = 'linux2'


def PrintUsage():
    print """
 CvsSetup.py [-a] <AG source location> [-d] <destination config directory>

 -a (--agdir)   (optional) set the location of the AccessGrid source tree.
 -d (--dst)     (required) set the destination to put config files.
 -v                        set verbose mode on.
"""


# Defaults
AG_BASE_DIR = ".."  # At least try one default location for AG source: 
                    #    default works if executed from AccessGrid/bin 
DST_CONFIG_DIR = ""
INITIAL_DIR = os.getcwd()
verbose = 0
print ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "a:d:vq", ["agdir=", "dst=", "verbose"] )
except:
    # print help information and exit
    PrintUsage()
    sys.exit(2)

for o, a in opts:
    if o in ("-a", "--agdir"):
        AG_BASE_DIR = a
        print "    AccessGrid source directory: ",AG_BASE_DIR
    if o in ("-d", "--dst"):
        DST_CONFIG_DIR = a
        print "    Destination config location: ",DST_CONFIG_DIR
    if o in ("-v", "--verbose"):
        print "    verbose mode enabled: "
        verbose = 1


# Create destination directory if it doesn't exist.

if DST_CONFIG_DIR != "":
    if not os.path.exists( DST_CONFIG_DIR ):
        os.mkdir(DST_CONFIG_DIR)

# Make sure a destination was specified.

if DST_CONFIG_DIR == "" or not os.path.exists( DST_CONFIG_DIR ):
    PrintUsage()
    if DST_CONFIG_DIR == "":
        print "Error: You did not specify a destination directory.\n"
    elif not os.path.exists( DST_CONFIG_DIR ):
        print "Error: destination directory does not exist:",DST_CONFIG_DIR
    sys.exit()


# Make sure we can find AG source.

file_to_find = os.path.join(AG_BASE_DIR, "AccessGrid", "VenueClientUIClasses.py")
if not (os.path.exists( file_to_find )):
    PrintUsage()
    print "Cannot find AccessGrid source location.", file_to_find, " not found." 
    sys.exit()

# Make sure we can find destination directory.

if not os.path.exists( DST_CONFIG_DIR ):
    PrintUsage()
    print "Cannot find destination config location.", DST_CONFIG_DIR, " not found." 
    sys.exit()


# Get absolute paths for when we need to pass them to python.exe later.
ABS_DST_CONFIG_DIR = os.path.abspath(DST_CONFIG_DIR)
ABS_AG_BASE_DIR = os.path.abspath(AG_BASE_DIR)

# Overview: 
# python packaging/makeServicePackages.py DST_CONFIG_DIR/AccessGrid/services
# mkdir local_services
# mkdir nodeConfig
# create empty file videoresources
# cp packaging/config/defaultWindows DST_CONFIG_DIR/nodeConfig
# cp packaging/config/defaultLinux DST_CONFIG_DIR/nodeConfig
# 

print ""

# Make directories

dir = os.path.join(DST_CONFIG_DIR,"services")
if not os.path.exists(dir):
    os.mkdir (dir)
    if verbose:
        print "   mkdir",dir

dir = os.path.join(DST_CONFIG_DIR,"local_services")
if not os.path.exists(dir):
    os.mkdir (dir)
    if verbose:
        print "   mkdir",dir

dir = os.path.join(DST_CONFIG_DIR,"nodeConfig")
if not os.path.exists(dir):
    os.mkdir (dir)
    if verbose:
        print "   mkdir",dir


# create services
# python packaging/makeServicePackages.py AccessGrid/services

mk_service_exec = sys.executable + " " + os.path.join( AG_BASE_DIR, "packaging", "makeServicePackages.py" )
service_input_dir = "\"" + os.path.join( ABS_AG_BASE_DIR, "services", "node") + "\""
service_output_dir = "\"" + os.path.join( ABS_DST_CONFIG_DIR, "services") + "\""
mk_command = mk_service_exec + " " + service_input_dir + " " + service_output_dir
#mk_command = mk_service_exec + " " + service_input_dir
if verbose:
    print "   ",mk_command
os.system(mk_command)



# Copy default configuration files

if sys.platform == WIN:
    win_config_src = os.path.join( AG_BASE_DIR, "packaging", "config", "defaultWindows")
    win_config_dst = os.path.join( DST_CONFIG_DIR, "nodeConfig", "defaultWindows")
    #if verbose:
        #print "    copying file ", win_config_src, "to ", win_config_dst
    #shutil.copyfile( win_config_src, win_config_dst )

    # Remove the "c:\program files\access grid toolkit" in the defaultWindows file so we don't require a previous installation.
    executable_path_replace = re.compile('c:\\\\program files\\\\access grid toolkit\\\\')

    print "\n    Creating file", win_config_dst, "from", win_config_src
    if verbose:
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
if sys.platform == LINUX:
    unix_config_src = os.path.join( AG_BASE_DIR, "packaging", "config", "defaultLinux")
    unix_config_dst = os.path.join( DST_CONFIG_DIR, "nodeConfig", "defaultLinux")
    if verbose:
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
        if verbose:
            print "    copying file ", filename, "to ", backup_filename
        shutil.copyfile(filename, backup_filename)


# Create empty "videoresources" file

config_file = os.path.join(DST_CONFIG_DIR, "videoresources")
bak_file = os.path.join(DST_CONFIG_DIR, "videoresources.bak")

BackupFile(config_file, bak_file)

vsfile = open(config_file, 'w', )
vsfile.write("\n\n")
vsfile.close()


# Create AGNodeService.cfg

config_file = os.path.join(DST_CONFIG_DIR, "AGNodeService.cfg")
bak_file = os.path.join(DST_CONFIG_DIR, "AGNodeService.cfg.bak")

BackupFile(config_file, bak_file)

nsfile = open(config_file, 'w', )
nsfile.write("[Node Configuration]\n")
nsfile.write("servicesDirectory = services\n")
nsfile.write("configDirectory = nodeConfig\n")
if sys.platform == WIN:
    nsfile.write("defaultNodeConfiguration = defaultWindows\n\n")
elif sys.platform == LINUX:
    nsfile.write("defaultNodeConfiguration = defaultLinux\n\n")
nsfile.close()


# Create AGServiceManager.cfg

config_file = os.path.join(DST_CONFIG_DIR, "AGServiceManager.cfg")
bak_file = os.path.join(DST_CONFIG_DIR, "AGServiceManager.cfg.bak")

BackupFile(config_file, bak_file)

smfile = open(config_file, 'w', )
smfile.write("[Service Manager]\n")
smfile.write("servicesDirectory = local_services\n\n")
smfile.close()


# Tell users how to use the new configuration files.


print "\n    --------------------------------------------------------------"
print ""
print "    If you want to setup video resources for this configuration,"
print "       set the environment as instructed below, "
print "       and run: \"python SetupVideo.py\" \n"

print "    To use this configuration:\n"

print "       Make sure media-related programs (vic, rat, etc.) are in your path."
if sys.platform == WIN:
    print "          On Windows: copying the vic and rat related binaries (if needed, "
    print "          from a real install) into their own directory before adding them "
    print "          to your path is recommended.  If you don't want to bother modifying "
    print "          your path, copying them into AccessGrid/bin is a quick fix.\n"

elif sys.platform == LINUX:
    print "          On linux: if you've installed the vic and rat rpm packages,"
    print "          they should already be in your path.\n"

print "       set AGTK_INSTALL to", os.path.join( os.path.abspath(AG_BASE_DIR), "bin" )
print "       set PYTHONPATH to", os.path.abspath(AG_BASE_DIR)
print "       set AGTK_LOCATION to", os.path.abspath(DST_CONFIG_DIR)
print ""

fh = open("env-init.sh", "w")
fh.write("export AGTK_INSTALL=%s\n" % (os.path.join( os.path.abspath(AG_BASE_DIR), "bin")))
fh.write("export PYTHONPATH=%s\n" % os.path.abspath(AG_BASE_DIR))
fh.write("export AGTK_LOCATION=%s\n" % os.path.abspath(DST_CONFIG_DIR))
fh.close()

fh = open("env-init.csh", "w")
fh.write("setenv AGTK_INSTALL %s\n" % (os.path.join( os.path.abspath(AG_BASE_DIR), "bin")))
fh.write("setenv PYTHONPATH %s\n" % os.path.abspath(AG_BASE_DIR))
fh.write("setenv AGTK_LOCATION %s\n" % os.path.abspath(DST_CONFIG_DIR))
fh.close()

fh = open("env-init.bat", "w")
fh.write("set AGTK_INSTALL=%s\n" % (os.path.join( os.path.abspath(AG_BASE_DIR), "bin")))
fh.write("set PYTHONPATH=%s\n" % os.path.abspath(AG_BASE_DIR))
fh.write("set AGTK_LOCATION=%s\n" % os.path.abspath(DST_CONFIG_DIR))
fh.close()

print "Wrote csh config to env-init.csh, bash config to env-init.sh"
print "Wrote win32 batchfile init to env-init.bat"
