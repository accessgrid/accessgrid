#!/usr/bin/python2

import sys, os, time
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-s", dest="sourcedir", metavar="SOURCEDIR",
                  default=None,
                  help="The source directory for the AGTk build.")
parser.add_option("-b", dest="builddir", metavar="BUILDDIR",
                  default=None,
                  help="The working directory the AGTk build.")
parser.add_option("-d", dest="destdir", metavar="DESTDIR",
                  default=None,
                  help="The destination directory of the AGTk build.")
parser.add_option("-m", dest="metainfo", metavar="METAINFO",
                  default=None,
                  help="Meta information string about this release.")
parser.add_option("-v", dest="version", metavar="VERSION",
                  default=None,
                  help="Version of the toolkit being built.")
parser.add_option("--verbose", action="store_true", dest="verbose",
                  default=0,
                  help="A flag that indicates to build verbosely.")
parser.add_option("-p", "--pythonversion", dest="pyver",
                  metavar="PYTHONVERSION", default="2.2",
                  help="Which version of python to build the installer for.")

options, args = parser.parse_args()

SourceDir = options.sourcedir
BuildDir = options.builddir
DestDir = options.destdir
metainfo = options.metainfo
version = options.version


print "In rpm/build_package.py"
print "SourceDir = ", SourceDir
print "BuildDir = ", BuildDir
print "DestDir = ", DestDir
print "metainfo = ", metainfo
print "version = ", version

"""
cmd =  /usr/bin/python2 build_package.py --verbose   \
    -s /home/turam/build               \
    -b /home/turam/build/AccessGrid    \
    -d /home/turam/build/dist          \
    -p 2.2 -m Snapshot_20040413-174909 \
    -v 2.2
"""

CurDir = os.getcwd()

#
# Build rpms for infrastructure packages
#
for pkg in [ "logging-0.4.7", "Optik-1.4.1", "fpconst-0.6.0", "SOAPpy"]:
    os.chdir(SourceDir)
    os.chdir(pkg)
    cmd = "%s setup.py bdist_rpm --binary-only --dist-dir %s" % (sys.executable,
                                                   DestDir)
    print "cmd = ", cmd
    os.system(cmd)

# Build pyOpenSSL 
# (must build with our spec file)
# - create tar file for the rpmbuild
os.chdir(SourceDir)
if os.path.exists('pyOpenSSL'):
    cmd = "ln -s pyOpenSSL pyOpenSSL_AG-0.5.1"
    print "cmd = ", cmd
    os.system(cmd)
cmd = "tar czhf /usr/src/redhat/SOURCES/pyOpenSSL_AG-0.5.1.tar.gz pyOpenSSL_AG-0.5.1"
print "cmd = ", cmd
os.system(cmd)

# - build the rpm
os.chdir("pyOpenSSL")
cmd = "rpmbuild -bb pyOpenSSL.spec"
print "cmd = ", cmd
os.system(cmd)

# - copy the rpm to the dest dir
cmd = "cp /usr/src/redhat/RPMS/i386/pyOpenSSL_AG-0.5.1-4.i386.rpm %s" % (DestDir,)
print "cmd = ", cmd
os.system(cmd)

#
# Build the pyGlobus rpm
#
# - create tar file for the rpm
os.chdir(SourceDir)
if os.path.exists('pyGlobus'):
    cmd = "ln -s pyGlobus pyGlobus-cvs"
    print "cmd = ", cmd
    os.system(cmd)
cmd = "tar czhf /usr/src/redhat/SOURCES/pyGlobus-cvs.tar.gz pyGlobus-cvs"
print "cmd = ", cmd
os.system(cmd)

# - build the rpm
os.chdir(CurDir)
cmd = "rpmbuild -ba pyGlobus.spec"
print "cmd = ", cmd
os.system(cmd)

# - copy it to the dest dir
cmd = "cp /usr/src/redhat/RPMS/i386/pyGlobus-cvs-11.i386.rpm %s" % (DestDir,)
print "cmd = ", cmd
os.system(cmd)

#
# Build AccessGrid rpms
#
# - build the targz file for the AG rpms
os.chdir(DestDir)
tar_dst_filename = "AccessGrid-%s.tar.gz" % (version)

rpm_srcdir = "/usr/src/redhat/SOURCES"
tar_command = "tar czhf %s ." % ( os.path.join(rpm_srcdir, tar_dst_filename), )
print "tar_command = ", tar_command
rc = os.system(tar_command)
if rc != 0:
    print "tar command \"", tar_command, "\" failed with rc ", rc
    sys.exit(1)
    
# - build the rpms
os.chdir(BuildDir)
os.chdir(os.path.join("packaging","linux","rpm"))
cmd = "rpmbuild -ba AccessGrid.spec" 
print "cmd = ", cmd
os.system(cmd)

# - copy the rpms to the dist dir
cmd = "cp /usr/src/redhat/RPMS/i386/AccessGrid-%s-1.i386.rpm %s" % (version,DestDir)
print "cmd = ", cmd
os.system(cmd)
cmd = "cp /usr/src/redhat/RPMS/i386/AccessGrid-VenueClient-%s-1.i386.rpm %s" % (version,DestDir)
print "cmd = ", cmd
os.system(cmd)
cmd = "cp /usr/src/redhat/RPMS/i386/AccessGrid-VenueServer-%s-1.i386.rpm %s" % (version,DestDir)
print "cmd = ", cmd
os.system(cmd)
cmd = "cp /usr/src/redhat/RPMS/i386/AccessGrid-BridgeServer-%s-1.i386.rpm %s" % (version,DestDir)
print "cmd = ", cmd
os.system(cmd)

#
# Copy the install.sh script into the dist dir
#
cmd = "cp %s %s" % (os.path.join(BuildDir,"packaging","linux","rpm","install.sh"),
                    DestDir)
print "cmd = ", cmd
os.system(cmd)

#
# Create the targz file including the rpms and install script
#
targz=os.path.join(SourceDir,"AccessGrid-2.2.tar.gz")
os.chdir(DestDir)
cmd = "tar czf %s *.rpm install.sh" % (targz,)
print "cmd = ", cmd
os.system(cmd)
