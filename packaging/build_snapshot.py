#!/usr/bin/python2
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


if not os.environ.has_key('AGBUILDROOT'):
    print "AGBUILDROOT environment variable must be set"
    sys.exit(1)

# Source Directory
#  We assume the following software is in this directory:
#    ag-rat, ag-vic, and AccessGrid
SourceDir = os.environ['AGBUILDROOT']

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
parser.add_option("--no-checkout", action="store_true", dest="nocheckout",
                  default=0,
                  help="A flag that indicates the snapshot should be built from a previously exported source directory.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  default=0,
                  help="A flag that indicates to build verbosely.")
parser.add_option("-p", "--pythonversion", dest="pyver",
                  metavar="PYTHONVERSION", default="2.2",
                  help="Which version of python to build the installer for.")
parser.add_option("-r", "--rebuild", action="store_true", dest="rebuild",
                  help="Rebuild an installer from a previously used build dir.")
options, args = parser.parse_args()

#
# The openssl in winglobus is critical put it in our path
#
if sys.platform == 'win32':
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
if options.nocheckout:
    BuildDirName = "AccessGrid"
else:
    BuildDirName = "AccessGrid-%s" % BuildTime
BuildDir = os.path.join(SourceDir,BuildDirName)

#
# Grab stuff from cvs
#

if not options.nocheckout:
    # Either we check out a copy
    cvsroot = ":pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl"

    # WE ASSUME YOU HAVE ALREADY LOGGED IN WITH:
    # cvs -d :pserver:anonymous@cvs.mcs.anl.gov:/cvs/fl login
    
    # Go to the source dir, and checkout using relative path;
    # cvs (linux) complains about checking out to an absolute path
    os.chdir(SourceDir)

    cvs_base = "cvs -z6 -d %s export -d %s -D now AccessGrid" % (cvsroot,
                                                              BuildDirName)
    
    if options.verbose:
        print "BUILD: Checking out code with command: ", cvs_cmd

    os.system(cvs_cmd)

#
# Get the version via popen
#
try:
    cmd = "%s %s" % (sys.executable, os.path.join(BuildDir, "AccessGrid",
                                                  "Version.py"))
    po = os.popen(cmd)
except IOError:
    print "Error getting AGTk Version."

version = po.read()
po.close()

version = version[:-1]

#
# Go to that checkout to build stuff
#

RunDir = os.path.join(BuildDir, "packaging")
if not options.nocheckout:

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

# Do automatic testing
os.chdir(os.path.join(BuildDir, "tests"))

# save the old path
if os.environ.has_key('PYTHONPATH'):
    oldpath = os.environ['PYTHONPATH']
else:
    oldpath = ''

# setup a new python path
os.environ['PYTHONPATH'] = os.path.join(os.path.abspath(os.path.join(DestDir,
                                           "Lib", "site-packages")), oldpath)

# run the tests
testfile = "%s-test.html" % DestDir
os.system("%s test_dist.py --html -o %s -t %s" % (sys.executable,
                                            "%s-test.html" % DestDir,
                                                  BuildTime))

# put the old python path back
os.environ['PYTHONPATH'] = oldpath

# Build packages according to the command line
if sys.platform == 'win32':
    bdir = 'windows'
elif sys.platform == 'linux2':
    bdir = 'linux'
elif sys.platform == 'darwin':
    print "Sorry not supported yet ;-)"
    bdir = 'darwin'
else:
    bdir = None
    
# Change to packaging dir to build packages
os.chdir(os.path.join(BuildDir,'packaging'))

# Build service packages
# makeServicePackages.py AGDIR\services\node DEST\services
cmd = '%s %s %s %s %s' % (sys.executable,
                       'makeServicePackages.py',
                       SourceDir,
                       BuildDir,
                       os.path.join(DestDir,"NodeServices"))
print "cmd = ", cmd
os.system(cmd)

# Build app packages
# makeAppPackages.py AGDIR\sharedapps DEST\sharedapps
cmd = '%s %s %s %s' % (sys.executable,
                       'makeAppPackages.py',
                       os.path.join(BuildDir,"sharedapps"),
                       os.path.join(DestDir, "SharedApplications"))
print "cmd = ", cmd
os.system(cmd)



file_list = os.listdir(SourceDir)

if bdir is not None:
    pkg_script = "build_package.py"
    NextDir = os.path.join(RunDir, bdir)
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
        print "cmd = ", cmd
        os.system(cmd)
    else:
        print "No directory (%s) found." % NextDir

nfl = os.listdir(SourceDir)
for f in file_list:
    nfl.remove(f)

if len(nfl) == 1:
    pkg_file = nfl[0]
else:
    pkg_file = None

hfi = file(os.path.join(testfile), "r")
lines = hfi.readlines()
hfi.close()

hfo = file(os.path.join(testfile), "w+")
for line in lines:
    hfo.write(line.replace("PACKAGEFILE", "%s" % str(pkg_file)))
hfo.close()

    
