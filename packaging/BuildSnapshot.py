#!/usr/bin/python
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
import sys, os, time
from optparse import OptionParser
from distutils.spawn import find_executable
from distutils.sysconfig import get_python_lib

def findExecutable(exefile,args=[]):
    pathlist = os.environ['PATH'].split(os.pathsep)
    for path in pathlist:
        pathfile = os.path.join(path,exefile)
        if os.path.exists(pathfile) and os.access(pathfile,os.R_OK|os.X_OK):
            return pathfile
    return None

# Verify Build Environment

# - Perform general checks
#   - setuptools
try:
    import setuptools
except ImportError:
    print '* * Error: Required Python module "setuptools" not found'
    sys.exit(1)

#   - zsi
try:
    import ZSI
except ImportError:
    print '* * Error: Required Python module "ZSI" not found'
    sys.exit(1)

exelist = []
# - Perform Windows-specific checks
if sys.platform == 'win32':
    # check for visual studio
    if not os.environ.has_key('MSVC_VERSION'):
        print "MSVC_VERSION environment must be set, or some modules will not build correctly."
        sys.exit(1)

    exelist = ['cl.exe','swig.exe','perl.exe']

# - Perform OSX-specific checks
elif sys.platform == 'darwin':
    exelist = ['gcc','swig','perl']

# Locate required executables
for exe in exelist:
    print 'Locating', exe,': ',
    pathfile = findExecutable(exe)
    if not pathfile:
        print 'not found; exiting'
        sys.exit(1)
    print pathfile

# Build packages according to the command line
if sys.platform == 'win32':
    bdir = 'windows'
elif sys.platform == 'linux2':
    bdir = 'linux'
elif sys.platform == 'darwin':
    bdir = 'mac'
elif sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    bdir = 'bsd'
else:
    print "Unsupported platform: %s; exiting" % (sys.platform,)
    bdir = None
    sys.exit(1)

# StartDir is the dir where this script lives
StartDir=os.path.dirname(os.path.abspath(__file__))

# Get the version of python used to run this script
# and use it as the default 
pyver = sys.version[:3]


#
# Parse command line options
#

parser = OptionParser()
parser.add_option("-s", "--sourcedir", dest="sourcedir", metavar="SOURCEDIR",
                  default=None,
                  help="The directory the AG source code is in.")
parser.add_option("-t", "--tag", dest="tag", metavar="TAG",
                  default=None,
                  help="Specifies the tag for a revision of code in subversion.")
parser.add_option("-m", "--meta", dest="metainfo", metavar="METAINFO",
                  default=None,
                  help="Meta information string about this release.")
parser.add_option("--no-checkout", action="store_true", dest="nocheckout",
                  default=0,
                  help="A flag that indicates the snapshot should be built from a previously exported source directory.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=0,
                  help="A flag that indicates to build verbosely.")
parser.add_option("-p", "--pythonversion", dest="pyver",
                  metavar="PYTHONVERSION", default=pyver,
                  help="Which version of python to build the installer for.")
if sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    parser.add_option("--dist", action="store", dest="dist",default="rpm",
                       help="Which distribution to build the installer for (linux only).")
parser.add_option("-r", "--rebuild", action="store_true", dest="rebuild",
                  help="Rebuild an installer from a previously used build dir.")
options, args = parser.parse_args()

# Build Name
#  This is the default name we use for the installer
BuildTime = time.strftime("%Y%m%d_%H%M%S")

# Source Directory
#  We assume the following software is in this directory:
#    ag-rat, ag-vic, and AccessGrid
if options.sourcedir is not None:
    SourceDir = options.sourcedir
    os.environ['AGBUILDROOT'] = SourceDir
elif not os.environ.has_key('AGBUILDROOT'):
    print "AGBUILDROOT environment variable must be set (or use --sourcedir)"
    sys.exit(1)
else:
    SourceDir = os.environ['AGBUILDROOT']

# Names for the software
if options.metainfo is not None:
    metainfo = options.metainfo
else:
    metainfo = "Snapshot %s" % BuildTime

# Create the dest dir stamped with the same time stamp
DestDir = os.path.join(SourceDir, "dist-%s" % BuildTime)

# The directory we're building from
if options.nocheckout:
    BuildDirName = "AccessGrid"
else:
    BuildDirName = "AccessGrid-%s" % BuildTime
BuildDir = os.path.join(SourceDir,BuildDirName)

#
# Grab stuff from subversion
#

if not options.nocheckout:
    # Either we check out a copy
    svnroot = "https://www.ci.uchicago.edu/svn/accessgrid/trunk"

    if not options.tag:
        tagString = ""
    else:
        tagString = "-r " + options.tag
    
    # Go to the source dir, and checkout using relative path;
    os.chdir(SourceDir)

    checkout_cmd = "svn export %s %s %s" % (tagString, svnroot, BuildDirName)
    if options.verbose:
        print "BUILD: Checking out code with command: ", checkout_cmd

    os.system(checkout_cmd)

#
# Get the version via popen
#
try:
    cmd = "%s %s" % (sys.executable, os.path.join(BuildDir, "AccessGrid", "Version.py"))
    po = os.popen(cmd)
except IOError: 
    print "Error getting AGTk Version."

version = po.read()
po.close()

version = version[:-1]

#
# Run the setup script first to create the distribution directory structure
# and auxillary packages, config, and documentation
#
s = os.getcwd()
os.chdir(BuildDir)

cmd = "%s %s" % (sys.executable, "setup.py")
for c in ["clean", "build"]:
    buildcmd = '%s %s' % (cmd,c)
    ret = os.system(buildcmd)
    if ret:
        print '%s failed with %d; exiting' % (buildcmd,ret)
        sys.exit(1)
buildcmd="%s install --prefix=%s --no-compile" % (cmd, DestDir)
ret = os.system(buildcmd)
if ret:
    print '%s failed with %d; exiting' % (buildcmd,ret)
    sys.exit(1)

os.chdir(s)

# Fix bin/*.py names & pythonpath
#
# Maybe extra pythonpath (eppath) could be a command line option?
eppath = get_python_lib()

cmd = '%s %s %s %s %s' % (sys.executable,
                          os.path.join(StartDir, 'FixAG3Paths.py'),
                          os.path.join(DestDir, 'bin'),
                          eppath,
                          True)
print "cmd = ", cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)

# save the old path
if os.environ.has_key('PYTHONPATH'):
    oldpath = os.environ['PYTHONPATH']
else:
    oldpath = ''

# setup a new python path
if sys.platform == 'win32':
    npath = os.path.join(DestDir, "Lib", "site-packages")
elif sys.platform == 'linux2' or sys.platform == 'darwin' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    npath = os.path.join(DestDir, "lib", "python%s"%(options.pyver,), "site-packages")
if not oldpath:
    nppath = os.pathsep.join([npath, oldpath])
else:
    nppath = npath

os.environ['PYTHONPATH'] = nppath

# Build stuff that needs to be built for modules to work
os.chdir(StartDir)

buildcmd = "BuildOpenSSL.py"
cmd = "%s %s %s" % (sys.executable, buildcmd, DestDir)
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)

if sys.platform == 'win32':
    td = os.getcwd()
    os.chdir(os.path.join(BuildDir, "tools"))
    cmd = "%s %s" % ("MakeVfwScan.bat", DestDir)
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)
    cmd = "%s %s" % ("MakeWdmScan.bat", DestDir)
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)
    os.chdir(td)

elif sys.platform == 'darwin':
    # vic
    td = os.getcwd()
    os.chdir(os.path.join(BuildDir, "tools"))
    cmd = "%s %s" % ("./MakeOsxVGrabberScan.py", os.path.join(DestDir, 'bin') )
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)
    os.chdir(td)

# Build the UCL common library
cmd = "%s %s %s %s" % (sys.executable, "BuildCommon.py", SourceDir, DestDir)
print cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)


# Build the other python modules
cmd = "%s %s %s %s %s" % (sys.executable, "BuildPythonModules.py", SourceDir,
                          BuildDir, DestDir)
if options.verbose:
    print "Building python modules with the command:", cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)


# put the old python path back
if oldpath is not None:
    os.environ['PYTHONPATH'] = oldpath


# Build the QuickBridge executable
if sys.platform == 'linux2' or sys.platform == 'darwin' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    print "Building QuickBridge"
    os.chdir(os.path.join(BuildDir,'services','network','QuickBridge'))
    cmd = "gcc -O -o QuickBridge QuickBridge.c"
    print "cmd = ", cmd
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)


    cmd = "cp QuickBridge %s" % (os.path.join(DestDir,'bin','QuickBridge'))
    print "cmd = ", cmd
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)
elif sys.platform == 'win32':
    print "Building QuickBridge"
    os.chdir(os.path.join(BuildDir,'services','network','QuickBridge'))

    # Find the version of visual studio by peering at cl
    (input, outerr) = os.popen4("cl.exe")
    usageStr = outerr.readlines()
    v = map(int, usageStr[0].split()[7].split('.')[:2])
    
    v = map(int, usageStr[0].split()[7].split('.')[:2])

    proj = None
    if v[0] == 12:
        print "Please do not use visual studio 6.0 to build QuickBridge"
    elif v[0] == 13:
        if v[1] == 0:
            proj = "QuickBridge.sln"
        elif v[1] == 10:
            proj = "QuickBridge.2003.sln"

    if proj is not None:
        os.system("devenv %s /rebuild Release" % proj)

    qbexe = os.path.join(os.getcwd(), "Release", "QuickBridge.exe")
    destDir = os.path.join(DestDir,'bin','QuickBridge.exe')
    cmd = "copy %s %s" % (qbexe, destDir)
    print "cmd = ", cmd
    os.system(cmd)
    




# Change to packaging dir to build packages
os.chdir(StartDir)

# Fix service *.py files before they're packaged
#
print "Fixing service *.py files before they're packaged"
services2fix = [
    os.path.join(BuildDir, 'services', 'node', 'AudioService'),
    os.path.join(BuildDir, 'services', 'node', 'VideoService'),
    os.path.join(BuildDir, 'services', 'node', 'VideoConsumerService'),
    os.path.join(BuildDir, 'services', 'node', 'VideoProducerService')
    ]
for d in services2fix:
    cmd = '%s %s %s %s %s' % (sys.executable,
			os.path.join(StartDir, 'FixAG3Paths.py'),
			d,
			eppath,
			False)
    print "cmd = ", cmd
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)


# Build service packages
# makeServicePackages.py AGDIR\services\node DEST\services
cmd = '%s %s --sourcedir %s --agsourcedir %s --outputdir %s --servicefile %s' % (sys.executable,
                       'makeServicePackages.py',
                       SourceDir,
                       BuildDir,
                       os.path.join(DestDir,"NodeServices"),
                       'servicesToShip')
print "\n********** cmd = ", cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)


# copy media tools to bin directory
cmd = '%s %s %s %s'%(sys.executable, 'BuildRat.py', SourceDir, os.path.join(DestDir,"bin"))
print "\n ********* cmd = ",cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)


cmd = '%s %s %s %s'%(sys.executable, 'BuildVic.py', SourceDir, os.path.join(DestDir,"bin"))
print "\n ********* cmd = ",cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)

# Fix shared app *.py files before they're packaged
#
print "Fixing shared app *.py files before they're packaged"
pkgs2fix = [
    os.path.join(BuildDir, 'sharedapps', 'SharedBrowser'),
    os.path.join(BuildDir, 'sharedapps', 'SharedPresentation'),
    os.path.join(BuildDir, 'sharedapps', 'VenueVNC'),
    ]
for d in pkgs2fix:
    cmd = '%s %s %s %s %s' % (sys.executable,
			os.path.join(StartDir, 'FixAG3Paths.py'),
			d,
			eppath,
			False)
    print "cmd = ", cmd
    ret = os.system(cmd)
    if ret:
        print '%s failed with %d; exiting' % (cmd,ret)
        sys.exit(1)

# Build app packages
# makeAppPackages.py AGDIR\sharedapps DEST\sharedapps
cmd = '%s %s %s %s' % (sys.executable,
                       'makeAppPackages.py',
                       os.path.join(BuildDir,"sharedapps"),
                       os.path.join(DestDir, "SharedApplications"))
print "cmd = ", cmd
ret = os.system(cmd)
if ret:
    print '%s failed with %d; exiting' % (cmd,ret)
    sys.exit(1)

file_list = os.listdir(SourceDir)

if bdir is not None:
    pkg_script = "BuildPackage.py"
    NextDir = os.path.join(StartDir, bdir)
    if os.path.exists(NextDir):
        os.chdir(NextDir)
        cmd = "%s %s --verbose -s %s -b %s -d %s -p %s -m %s -v %s" % (sys.executable,
                                                                 pkg_script,
                                                                 SourceDir,
                                                                 BuildDir,
                                                                 DestDir,
                                                                 options.pyver,
                                                                 metainfo.replace(' ', '_'),
                                                                 version)
        if sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
            cmd += ' --dist %s' % (options.dist,)
        print "cmd = ", cmd
        ret = os.system(cmd)
        if ret:
            print '%s failed with %d; exiting' % (cmd,ret)
            sys.exit(1)
    else:
        print "No directory (%s) found." % NextDir

nfl = os.listdir(SourceDir)
for f in file_list:
    nfl.remove(f)

if len(nfl) == 1:
    pkg_file = nfl[0]
else:
    pkg_file = None

