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
print "*********** Building elementtree\n"
SetupModule("elementtree-1.2.6-20050316", SOURCE, DEST)

print "*********** Building bajjer\n"
SetupModule("Bajjer-0.2.5", SOURCE, DEST)

print "*********** Building feedparser\n"
SetupModule("feedparser", SOURCE, DEST)

print "*********** Building pyxml\n"
SetupModule("PyXML-0.8.4", SOURCE, DEST )

print "*********** Building zope interface\n"
SetupModule("zope.interface-3.3.0", SOURCE, DEST, moreinstallopts=['--single-version-externally-managed', '--root=/' ] )
# add module identifer to zope package; this is required as long as we're 
# using the 'single-version-externally-managed' flag above
# to avoid using eggs
initfile = os.path.join(BuildPath,'zope','__init__.py')
if not os.path.exists(initfile):
    file(initfile,'w').close()

print "*********** Building zsi\n"
SetupModule("zsi", SOURCE, DEST, moreinstallopts=['--single-version-externally-managed', '--root=/' ] )
print "*********** Building m2crypto\n"
SetupModule("m2crypto-0.17", SOURCE, DEST, ['--openssl=%s' % os.path.join(SOURCE,'openssl-0.9.8g')], moreinstallopts=['--single-version-externally-managed', '--root=/' ] )
print "*********** Building twisted\n"
SetupModule("TwistedCore-2.5.0", SOURCE, DEST)

print "*********** Building bonjour-py\n"
SetupModule("bonjour-py-0.3", SOURCE, DEST)

print "*********** Building common\n"
SetupModule(os.path.join("common","examples", "_common"), SOURCE, DEST,['--debug'])

