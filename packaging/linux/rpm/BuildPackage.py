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
                  metavar="PYTHONVERSION", default="2.3",
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

TmpDir = os.tmpnam()
if not os.path.exists(TmpDir):
    os.mkdir(TmpDir)
RpmDir = os.path.join(TmpDir,"AccessGrid-%s" % (version,))
if not os.path.exists(RpmDir):
    os.mkdir(RpmDir)
StartDir = os.getcwd()

# 	 
# Build globus rpm      
#   
os.chdir(StartDir)    
cmd = "rpmbuild -ba globus.spec"     
print "cmd = ", cmd     
os.system(cmd)      
cmd = "cp /usr/src/redhat/RPMS/i386/globus-accessgrid-2.4-1.i386.rpm %s" % (RpmDir,)   
print "cmd = ", cmd     
os.system(cmd)      

#
# Build AccessGrid rpms
#
print "** Building AccessGrid RPMs"
# - build the targz file for the AG rpms
os.chdir(DestDir)
tar_dst_filename = "AccessGrid-%s.tar.gz" % (version,)

rpm_srcdir = "/usr/src/redhat/SOURCES"
tar_command = "tar czhf %s ." % ( os.path.join(rpm_srcdir, tar_dst_filename), )
print "tar_command = ", tar_command
rc = os.system(tar_command)
if rc != 0:
    print "tar command \"", tar_command, "\" failed with rc ", rc
    sys.exit(1)
    
# - build the rpms
os.chdir(StartDir)
cmd = "rpmbuild -ba AccessGrid.spec" 
print "cmd = ", cmd
os.system(cmd)

# - copy the rpms to the dist dir
print "** Copying RPMs to the RPM directory"
cmd = "cp /usr/src/redhat/RPMS/i386/AccessGrid-%s-1.i386.rpm %s" % (version,RpmDir)
print "cmd = ", cmd
os.system(cmd)

#
# Copy the install.sh script into the dist dir
#
installsh = os.path.join(BuildDir,'packaging','linux','rpm','install.sh')
os.chmod(installsh,755)
cmd = "cp %s %s" % (installsh,
                    RpmDir)
print "cmd = ", cmd
os.system(cmd)

#
# Create the targz file including the rpms and install script
#
print "Creating the AccessGrid install bundle"
targzfile = 'AccessGrid-%s.tar.gz' % version
targzpath=os.path.join(SourceDir,targzfile)
os.chdir(TmpDir)
cmd = "tar czf %s AccessGrid-%s" % (targzpath,version)
print "cmd = ", cmd
os.system(cmd)

# Clean up the rpm dir
print "** Cleaning up the RPM dir"
os.chdir(StartDir)
cmd = "rm -rf %s" % (TmpDir,)
print "cmd = ", cmd
os.system(cmd)
