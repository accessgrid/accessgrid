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

# Don't pass this in anymore
PYVER=sys.version[:3]

#
# Setup the given module in the given dest directory
#
def SetupModule(modName, source, dest):
    os.chdir(os.path.join(source,modName))
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


#
# Build python modules
#

print "Python: ", PYVER

if PYVER=="2.2":
	
    print "Building Logging 0.4.7"
    SetupModule("logging-0.4.7", SOURCE, DEST)

    print "Building Optik 1.4.1"
    SetupModule("Optik-1.4.1", SOURCE, DEST)


print "Building fpconst 0.6.0"
SetupModule("fpconst-0.6.0", SOURCE, DEST)

print "Building SOAPpy 0.11.4"
SetupModule("SOAPpy-0.11.4", SOURCE, DEST)

print "Building pyOpenSSL_AG"
SetupModule("pyOpenSSL", SOURCE, DEST)

print "Building pyGlobus"
if sys.platform == 'win32':
    os.environ['GLOBUS_LOCATION']=os.path.join(SOURCE,'WinGlobus')
    flavor = 'win32'
elif sys.platform == 'linux2':
    flavor = 'gcc32pthr'
else:
    print "Couldn't build pyGlobus; unsupported platform :", sys.platform
    sys.exit(1)

os.chdir(os.path.join(SOURCE,'pyGlobus'))

os.spawnl(os.P_WAIT,sys.executable,sys.executable,'setup.py','clean',
          '--all', '--flavor=%s'%(flavor,))
if sys.platform == 'win32':
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,'setup.py','build',
              '--flavor=%s' % (flavor,))
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,'setup.py','install',
              '--flavor=%s' % (flavor,),
              '--prefix=%s' % (DEST,), 
              '--no-compile')
else:
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,'setup.py','build',
              '--with-modules=io,security,util',
              '--flavor=%s' % (flavor,))
    os.spawnl(os.P_WAIT,sys.executable,sys.executable,'setup.py','install',
              '--with-modules=io,security,util',
              '--flavor=%s' % (flavor,),
              '--prefix=%s' % (DEST,), 
              '--no-compile')
    
