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
servicesPath = os.path.join(DestDir, "Services")
if not os.path.exists(servicesPath):
    os.mkdir(servicesPath)

# copy AGNodeServiceMac.cfg to AGNodeService.cfg
shutil.copy2(os.path.join(BuildDir, "packaging", "config", "AGNodeServiceMac.cfg"), os.path.join(DestDir, "Config", "AGNodeService.cfg"))

# ----- Make package tree and copy files there -----

TmpDir = tempfile.mkdtemp()
print "TmpDir:", TmpDir
pkgContentsDir = os.path.join(TmpDir, "pkg_contents")
pkgResourcesDir = os.path.join(TmpDir, "pkg_resources")
bundleDir = os.path.join(pkgContentsDir, "AccessGridToolkit3.app")
contentsDir = os.path.join(pkgContentsDir, "AccessGridToolkit3.app", "Contents")
resourcesDir = os.path.join(pkgContentsDir, "AccessGridToolkit3.app", "Contents", "Resources")
macosDir = os.path.join(pkgContentsDir, "AccessGridToolkit3.app", "Contents", "MacOS")

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
shutil.copy2("Description.plist", pkgResourcesDir)

#shutil.copy2("AGTk.icns", resourcesDir)
shutil.copy2("runag.sh.template", resourcesDir)
shutil.copy2("setupenv.sh.template", resourcesDir)
shutil.copy2("setupenv.csh.template", resourcesDir)

# resources
shutil.copy2(os.path.join(BuildDir, "COPYING.txt"), os.path.join(pkgResourcesDir, "License.txt") )
shutil.copy2(os.path.join(BuildDir, "README"), os.path.join(pkgResourcesDir, "ReadMe.txt") )
shutil.copy2("postflight", pkgResourcesDir)

# Remove shared applications that don't work on the mac yet.
sharedAppDir = os.path.join(DestDir, "SharedApplications")
sharedAppsToRemove = ["SharedBrowser", "SharedPresentation"]
for appName in sharedAppsToRemove:
    for ext in [".agpkg", ".zip"]:
        appPath = os.path.join(sharedAppDir, appName + ext)
        if os.path.exists(appPath):
            os.remove(appPath)

# Copy dist files to the resource directory for the package.
fileList = os.listdir(DestDir)
for f in fileList:
    fpath = os.path.join(DestDir, f)
    if os.path.isdir(fpath):
        shutil.copytree(fpath, os.path.join(resourcesDir, f))
    else:
        shutil.copy2(fpath, resourcesDir)

# Establish filenames and backup any old files.
nameWithVersion="AGTk-%s" % version
pkgDir  = os.path.join("..", nameWithVersion)
pkgPath = os.path.join(pkgDir, "AGTk-%s.pkg" % version)

def makeBackup(filePath, extension=".old"):
    # Rename a file if it exists
    if os.path.exists(filePath):
        backupPath = filePath + ".old"
        print "Backing up old file:", filePath, "to", backupPath
        if os.path.exists(backupPath):
            if os.path.isdir(backupPath):
                print "\tRemoving old backup (directory):", backupPath
                for root, dirs, files in os.walk(backupPath, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            else:
                print "\tRemoving old backup (file):", backupPath
                os.remove(backupPath)
        os.rename(filePath, backupPath)

makeBackup(pkgDir)
os.mkdir(pkgDir)

# Create package.
pkgrExe = "/Developer/Applications/Utilities/PackageMaker.app/Contents/MacOS/PackageMaker"
pkgInfoPlist = os.path.join(contentsDir, "Info.plist")
pkgDescPlist = os.path.join(pkgResourcesDir, "Description.plist")
pkgrArgs = "-build -p %s -f %s -ds -r %s -i %s -d %s" % (pkgPath, pkgContentsDir, pkgResourcesDir, pkgInfoPlist, pkgDescPlist)
cmd = pkgrExe + " " + pkgrArgs
print "Running packaging command:", cmd
os.system(cmd)


# Create disk image (.dmg) with hdiutil.
dmgPath = os.path.join("..", nameWithVersion + ".dmg")
if os.path.exists(dmgPath):
    print "Removing old file:", dmgPath
    os.remove(dmgPath)
cmd = "hdiutil create -fs HFS+ -volname %s -srcfolder %s %s" % (nameWithVersion, pkgPath, dmgPath)
print "Creating dmg:", cmd
os.system(cmd)


# gzip package to reduce size by 1/3

dmgLocation = dmgPath
gzDmgLocation = dmgLocation + ".gz"
makeBackup(gzDmgLocation)
print "gzipping:", dmgLocation
os.system("gzip " + dmgLocation)

print "Your final package:", os.path.abspath(gzDmgLocation)

