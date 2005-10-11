#!/usr/bin/python

import sys, os, time, commands
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
                  metavar="PYTHONVERSION", default="2.4",
                  help="Which version of python to build the installer for.")

options, args = parser.parse_args()

SourceDir = options.sourcedir
BuildDir = options.builddir
DestDir = options.destdir
metainfo = options.metainfo
version = options.version


print "In fedora/BuildPackage.py"
print "SourceDir = ", SourceDir
print "BuildDir = ", BuildDir
print "DestDir = ", DestDir
print "metainfo = ", metainfo
print "version = ", version

TmpDir = os.tmpnam()
if not os.path.exists(TmpDir):
    os.mkdir(TmpDir)
StartDir = os.getcwd()
BuildArch = commands.getoutput("rpm --eval %{_build_arch}")

cmd = "cp -p ../../../sharedapps/VenueVNC/server/VenueVNCServer.py %s/bin" % DestDir
print "cmd = ", cmd
os.system(cmd)

# copy XDG Gnome/KDE menu related files and delete legacy Gnome/KDE dirs
cmd = "cp -p ../ag-ellipse.png %s/share/AccessGrid/" % DestDir
print "cmd = ", cmd
os.system(cmd)
cmd = "rm -rf %s/share/gnome" % DestDir
print "cmd = ", cmd
os.system(cmd)
cmd = "rm -rf %s/share/applnk" % DestDir
print "cmd = ", cmd
os.system(cmd)

XdgConfigDir = "/etc/xdg"
XdgDataDir   = "share"

xdgDestDir = "%s/%s/applications/AccessGrid" % (DestDir, XdgDataDir)
os.makedirs(xdgDestDir)
cmd = "cp -p ../xdg/*.desktop %s" % xdgDestDir
print "cmd = ", cmd
os.system(cmd)

if os.path.exists("/etc/X11/desktop-menus/applications.menu"):
    xdgDestDir = "%s/%s/desktop-menu-patches" % (DestDir, XdgDataDir)
    os.makedirs(xdgDestDir)
    cmd = "cp -p AccessGrid-menu.patch %s" % xdgDestDir
    print "cmd = ", cmd
    os.system(cmd)

    xdgDestDir = "%s/%s/desktop-menu-files" % (DestDir, XdgDataDir)
    os.makedirs(xdgDestDir)
    cmd = "cp -p ../xdg/*.directory %s" % xdgDestDir
    print "cmd = ", cmd
    os.system(cmd)
else:
    xdgDestDir = "%s/%s/menus/applications-merged" % (DestDir, XdgConfigDir)
    os.makedirs(xdgDestDir)
    cmd = "cp -p ../xdg/AccessGrid.menu %s" % xdgDestDir
    print "cmd = ", cmd
    os.system(cmd)

    xdgDestDir = "%s/%s/desktop-directories" % (DestDir, XdgDataDir)
    os.makedirs(xdgDestDir)
    cmd = "cp -p ../xdg/*.directory %s" % xdgDestDir
    print "cmd = ", cmd
    os.system(cmd)

#
# Build globus rpm if it hasn't already been built and installed
# 
os.chdir(StartDir) 
installedRPM = commands.getoutput("/bin/rpm -q --queryformat='%{VERSION}-%{RELEASE}.%{ARCH}' globus-accessgrid")
toBeBuiltRPM = commands.getoutput("/bin/rpm -q --queryformat='%{VERSION}-%{RELEASE}.' --specfile globus-accessgrid.spec")
toBeBuiltRPM += BuildArch
if (installedRPM != toBeBuiltRPM) :
    cmd = "rpmbuild --target=%s -ba globus-accessgrid.spec" % (BuildArch,)
    print "cmd = ", cmd     
    os.system(cmd)
if installedRPM.endswith('not installed') :
    print "\nUnable to proceed with the build!"
    print "Please install the built globus-accessgrid-" + toBeBuiltRPM + ".rpm file."
    print "and restart the build.\n"
    sys.exit(1)

#
# Build AccessGrid rpms
#
print "** Building AccessGrid RPMs"
# - build the targz file for the AG rpms
os.chdir(DestDir)
tar_dst_filename = "AccessGrid-%s-%s.tar.gz" % (version,metainfo)

rpm_srcdir = "/usr/src/packages/SOURCES"
tar_command = "tar czhf %s ." % ( os.path.join(rpm_srcdir, tar_dst_filename), )
print "tar_command = ", tar_command
rc = os.system(tar_command)
if rc != 0:
    print "tar command \"", tar_command, "\" failed with rc ", rc
    sys.exit(1)

# - set the release number in AccessGrid.spec
os.chdir(StartDir)
spec_in = 'AccessGrid.spec.in'
spec_out = 'AccessGrid.spec'
cmd = 'sed s/RELEASE/%s/ %s > %s' % (metainfo,
                                     spec_in,spec_out)
print "cmd = ", cmd
os.system(cmd)
    
# - build the rpms
cmd = "rpmbuild --target=%s -ba AccessGrid.spec" % (BuildArch,)
print "cmd = ", cmd
os.system(cmd)

# Clean up the rpm dir
print "** Cleaning up the RPM dir"
os.chdir(StartDir)
cmd = "rm -rf %s" % (TmpDir,)
print "cmd = ", cmd
os.system(cmd)
