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
pyver = options.pyver


print "In slackware/build_package.py"
print "SourceDir = ", SourceDir
print "BuildDir = ", BuildDir
print "DestDir = ", DestDir
print "metainfo = ", metainfo
print "version = ", version
print "pyver = ", pyver

TmpDir = os.tmpnam()
if not os.path.exists(TmpDir):
    os.mkdir(TmpDir)
RpmDir = os.path.join(TmpDir,"AccessGrid-%s-%s" % (version,metainfo))
if not os.path.exists(RpmDir):
    os.mkdir(RpmDir)
StartDir = os.getcwd()

## Build the globus Slackware package
##
os.chdir(StartDir)    
cmd = "sh Slack.build-globus"     
print "cmd = ", cmd     
os.system(cmd)      
os.chdir(StartDir)    
cmd = "cp globus-accessgrid-2.4-i486-1.tgz %s" % (RpmDir,)   
print "cmd = ", cmd     
os.system(cmd)      

# Now that the globus pkg has been copied to the "RpmDir" for packaging,
# remove it from here
cmd = "rm -f globus-accessgrid-2.4-i486-1.tgz"
os.system(cmd)

#
# Build AccessGrid packages for Slackware
#
print "** Building AccessGrid RPMs"
# - build the targz file name for the AG packages
os.chdir(DestDir)
tar_dst_filename = "AccessGrid-%s-%s.tar.gz" % (version,metainfo)

# Set the release number in Slack.build-ag
# Also set the python version
os.chdir(StartDir)
spec_in = 'Slack.build-ag.in'
spec_out = 'Slack.build-ag'
cmd = 'sed -e s/RELEASE/%s/ -e s/pythonPYVER/python%s/ %s > %s' % (metainfo,pyver,spec_in,spec_out)
os.system(cmd)

# Copy ALSA devices setup script
cmd = "cp snddevices %s" % (RpmDir,)   
print "cmd = ", cmd     
os.system(cmd)      
    
# - build the packages
cmd = 'sh Slack.build-ag %s' % (DestDir)
print "cmd = ", cmd
os.system(cmd)

# - copy the rpms to the dist dir
print "** Copying RPMs to the RPM directory **"
cmd = "cp AccessGrid-%s-i486-%s.tgz %s" % (version,metainfo,RpmDir)
print "cmd = ", cmd
os.system(cmd)

# Now that the AccessGrid pkg has been copied to the "RpmDir" for packaging,
# remove it from here
cmd = "rm -f AccessGrid-%s-i486-%s.tgz" % (version,metainfo)
os.system(cmd)

#
# Copy the install.sh script into the dist dir
#
installsh_in = os.path.join(BuildDir,'packaging','linux','slackware','install.sh')
installsh_out = os.path.join(RpmDir,'install.sh')
cmd = 'sed -e s/AG_VER=VER/AG_VER=\\"%s-i486-%s\\"/ -e s/pythonPYVER/python%s/ %s > %s' % (version,metainfo,pyver,installsh_in,installsh_out)
print "cmd = ", cmd
os.system(cmd)
os.chmod(installsh_out,0755)

#
# Until the XDG stuff is built in, patch "Applications" menu to include AG menus
#
cmd = "cp applications-all-users.vfolder-info.diff %s" % (RpmDir)
print "cmd = ", cmd
os.system(cmd)


#
# Create the targz file including the rpms and install script
#
print "Creating the AccessGrid install bundle"
targzfile = 'AccessGrid-%s-%s.tar.gz' % (version,metainfo)
targzpath=os.path.join(SourceDir,targzfile)
os.chdir(TmpDir)
cmd = "tar czf %s AccessGrid-%s-%s" % (targzpath,version,metainfo)
print "cmd = ", cmd
os.system(cmd)


# Clean up the rpm dir
print "** Cleaning up the RPM dir"
os.chdir(StartDir)
cmd = "rm -rf %s" % (TmpDir,)
print "cmd = ", cmd
os.system(cmd)


###################################################################################
print "DONE build for Slackware"
###################################################################################

