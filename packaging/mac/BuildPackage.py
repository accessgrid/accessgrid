#!/usr/bin/python

import sys, os, time, shutil
import tempfile
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

print "SourceDir = ", SourceDir
print "BuildDir = ", BuildDir
print "DestDir = ", DestDir
print "metainfo = ", metainfo
print "version = ", version


# ----- Finish creating the DestDir -----
# Ensure empty Services directory is created
os.mkdir(os.path.join(DestDir, "Services"))

# copy AGNodeServiceMac.cfg to AGNodeService.cfg
shutil.copy2(os.path.join(BuildDir, "packaging", "config", "AGNodeServiceMac.cfg"), os.path.join(DestDir, "Config", "AGNodeService.cfg"))

# Remove services that are not being used yet (should add a platform-specific servicesToInclude file)
servicesToRemove = ["AudioService.zip", "VideoService.zip", "VideoConsumerService.zip", "VideoProducerService.zip"]
for s in servicesToRemove:
    servicePath = os.path.join(DestDir, "NodeServices", s)
    if os.path.exists( servicePath ):
        os.remove(servicePath)


# ----- Make package tree and copy files there -----

TmpDir = tempfile.mkdtemp()
print "TmpDir:", TmpDir
pkgContentsDir = os.path.join(TmpDir, "pkg_contents")
pkgResourcesDir = os.path.join(TmpDir, "pkg_resources")
bundleDir = os.path.join(pkgContentsDir, "AccessGridToolkit.app")
contentsDir = os.path.join(pkgContentsDir, "AccessGridToolkit.app", "Contents")
resourcesDir = os.path.join(pkgContentsDir, "AccessGridToolkit.app", "Contents", "Resources")
macosDir = os.path.join(pkgContentsDir, "AccessGridToolkit.app", "Contents", "MacOS")

# move previous bundle build dir if it exists
if os.path.exists( pkgContentsDir ):
    backupCDir = os.path.join(TmpDir, "pkg_contents.bak")
    if os.path.exists( backupCDir ):
        shutil.rmtree( backupCDir )
    os.rename(pkgContentsDir, backupCDir)

if os.path.exists( pkgResourcesDir ):
    backupRDir = os.path.join(TmpDir, "pkg_resources.bak")
    if os.path.exists( backupRDir ):
        shutil.rmtree( backupRDir )
    os.rename(pkgResourcesDir, backupRDir)

os.makedirs(contentsDir)
os.mkdir(resourcesDir)
os.mkdir(pkgResourcesDir)
os.mkdir(macosDir)
shutil.copy2("Info.plist", contentsDir)

globusLocation = os.environ["GLOBUS_LOCATION"]
shutil.copytree(globusLocation, os.path.join(resourcesDir, "globus") )

#shutil.copy2("AGTk.icns", resourcesDir)
shutil.copy2("runag.sh.template", resourcesDir)

# resources
shutil.copy2(os.path.join(BuildDir, "COPYING.txt"), os.path.join(pkgResourcesDir, "License.txt") )
shutil.copy2(os.path.join(BuildDir, "README"), os.path.join(pkgResourcesDir, "ReadMe.txt") )
shutil.copy2("postflight", pkgResourcesDir)

# Copy dist files to the resource directory for the package.
fileList = os.listdir(DestDir)
for f in fileList:
    fpath = os.path.join(DestDir, f)
    if os.path.isdir(fpath):
        shutil.copytree(fpath, os.path.join(resourcesDir, f))
    else:
        shutil.copy2(fpath, resourcesDir)

# Create package with package manager
shutil.copy2("agtk.pmsp", TmpDir)
pmspDestFile = os.path.join(TmpDir, "agtk.pmsp")

print "\n\nInsert the following information into the Package Manager UI:"
print "---Description---"
print "Title: Access Grid Toolkit"
print "Version:", str(version)
print "Description:\nVersion 2.3 of the Access Grid ToolKit.\n\nSee http://www.accessgrid.org for more details."
print "---Files---"
print "Root:", pkgContentsDir
print "---Resources---"
print "Resources:", pkgResourcesDir
print "---Display---"
print "Display name: Access Grid Toolkit"
print "Identifier: edu.uchicago.accessgrid"
print "Get-Info string: AccessGrid Toolkit 2.3"
print "Short Version:", str(version)
print "Verify Major and Minor versions are correct"

print
print "Waiting for you to Create the package in an empty folder and quit the Package Manager"

os.system("/Developer/Applications/Utilities/PackageMaker.app/Contents/MacOS/PackageMaker %s" % pmspDestFile)


print "Now create a Disk Image with the Disk Utility"
print "Under Images->New->Image From Folder"
print "(note: your .pkg file should be in a folder by itself so you can make an image of that folder.)"
print "Waiting for you to finish creating the disk image and quit Disk Utility"

# Create dmg with /Applications/Utilities/Disk Utility.app
os.system("/Applications/Utilities/Disk\ Utility.app/Contents/MacOS/Disk\ Utility")


# gzip package to reduce size by 1/3

dmgLocation = ""
while (not os.path.exists(dmgLocation)):
    dmgLocation = raw_input("Please enter the location of the .dmg file you created (or q to quit): ")

    if len(dmgLocation) > 0:
        if dmgLocation[0] == 'q':
            print "Received user's command to (q)uit."
            sys.exit(1)

    if not os.path.exists(dmgLocation):
        print "file does not exist: ", dmgLocation

print "gzipping:", dmgLocation
os.system("gzip " + dmgLocation)

print "Your final package:", dmgLocation + ".gz" 

