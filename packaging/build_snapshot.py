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
    BuildDir = os.path.join(SourceDir, "AccessGrid")
else:
    BuildDir = os.path.join(SourceDir, "AccessGrid-%s" % BuildTime)

#
# Grab stuff from cvs
#

if not options.nocheckout:
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

if not options.nocheckout:
    if sys.platform == 'win32':
        RunDir = os.path.join(BuildDir, "packaging")
    else:
        RunDir = os.path.join(BuildDir, "packaging")

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
# Build packages according to the command line
#

if sys.platform == 'win32':
    bdir = 'windows'
elif sys.platform == 'linux2':
    bdir = 'linux'
elif sys.platform == 'darwin':
    print "Sorry not supported yet ;-)"
    bdir = 'darwin'
else:
    bdir = None

if bdir is not None:
    pkg_script = "build_package.py"
    NextDir = os.path.join(RunDir, options.bdir)
    if os.path.exists(NextDir):
        os.chdir(NextDir)
        os.system("%s %s -s %s -b %s -d %s -p %s -m %s -v %s" % (sys.executable,
                                                                 pkg_script,
                                                                 SourceDir,
                                                                 BuildDir,
                                                                 DestDir,
                                                                 options.pyver,
                                                                 metainfo,
                                                                 version))
    else:
        print "No directory (%s) found." % NextDir


