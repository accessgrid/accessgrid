#!/usr/bin/python

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
def SetupModule(modName, source, dest, morebuildopts=[],moreinstallopts=[]):
    os.chdir(os.path.join(source,modName))
    ret = os.spawnl(os.P_WAIT,sys.executable,sys.executable,"setup.py","clean","--all")
    if ret:
        print 'Clean of Python module %s failed' % modName
        sys.exit(1)

    buildopts = [ sys.executable, 'setup.py','build'] + morebuildopts
    print 'build options ', buildopts
    ret = os.spawnv(os.P_WAIT,sys.executable,buildopts)
    if ret:
        print 'Build of Python module %s failed' % modName
        sys.exit(1)

    installopts = [sys.executable, 'setup.py','install','--prefix=%s'%(dest,),'--no-compile'] + moreinstallopts
    ret = os.spawnv(os.P_WAIT,sys.executable,installopts)
    if ret:
        print 'Install of Python module %s failed' % modName
        sys.exit(1)



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

# appscript is required for SharedPresentation to work on OSX
print "*********** Building appscript\n"
SetupModule("appscript-0.17.2", SOURCE, DEST, moreinstallopts=['--single-version-externally-managed', '--root=%s' % DEST] )

# LaunchServices is required by appscript; HACK!
# http://svn.red-bean.com/bob/Python23Compat/trunk/LaunchServices
print "*********** Building LaunchServices\n"
SetupModule("LaunchServices/python/dist/src/Mac/Modules/launch", SOURCE, DEST)

