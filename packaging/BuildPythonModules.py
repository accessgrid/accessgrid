#!/usr/bin/python2

import sys
import os

#
#  Build all the python modules and stick them somewhere safe
#

#
# Store command-line args
#
SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]
PYVER=sys.argv[4]


#
# Setup the given module in the given dest directory
#
def SetupModule(modName, dest):
    os.chdir(modName)
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","clean","--all")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","build")
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","install",
              "--prefix=%s"%(dest,), "--no-compile")


#
# Modify the python path to pick up packages as they're built,
# so inter-package dependencies are satisfied
#
BuildPath=SOURCE + os.pathsep + os.path.join(DEST,"lib","python"+PYVER,"site-packages")
if os.environ.has_key("PYTHONPATH"):
   os.environ["PYTHONPATH"] = os.environ["PYTHONPATH"] + os.pathsep + BuildPath
else:
   os.environ["PYTHONPATH"] = BuildPath

os.chdir(SOURCE)


#
# Build python modules
#

if PYVER=="2.2":
	
    print "Building Logging 0.4.7"
    SetupModule("logging-0.4.7", DEST)
    os.chdir(SOURCE)

    print "Building Optik 1.4.1"
    SetupModule("Optik-1.4.1", DEST)
    os.chdir(SOURCE)


print "Building fpconst 0.6.0"
SetupModule("fpconst-0.6.0", DEST)
os.chdir(SOURCE)

print "Building SOAPpy"
SetupModule("SOAPpy", DEST)
os.chdir(SOURCE)

print "Building pyOpenSSL_AG"
SetupModule("pyOpenSSL", DEST)
os.chdir(SOURCE)

# print "Building pyGLobus"
# cd pyGlobus
# python setup.py clean --all
# set GLOBUS_LOCATION=%SOURCE%\WinGlobus
# python setup.py build --flavor=win32
# python setup.py install --flavor=win32 --prefix=%DEST%
# cd %SOURCE% 
# 
