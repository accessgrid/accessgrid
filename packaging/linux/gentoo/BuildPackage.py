#!/usr/bin/python2

import sys, os, time, string
import tempfile
from optparse import OptionParser

from Dependency import *

parser = OptionParser()
parser.add_option("-s", dest="sourcedir", metavar="SOURCEDIR",
                  default=None,
                  help="The directory the AG source code is in.")
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

TmpDir = tempfile.mkdtemp()
StartDir = os.getcwd()


#
# Print calling state
#
print "\n\n---- Build portage tree\n"
if options.verbose:
    print "SourceDir = ", SourceDir
    print "BuildDir = ", BuildDir
    print "DestDir = ", DestDir
    print "metainfo = ", metainfo
    print "version = ", version

#
# Create source tarballs
#
print "\n\n---- Create source tarballs\n"
os.chdir(SourceDir)

# - Create dependency source tarballs
pyglobusTar = '%s-%s.tar.gz' % (PYGLOBUS,PYGLOBUS_VER)
cmd = 'tar czf %s pyGlobus-%s' % (pyglobusTar,PYGLOBUS_VER)
if options.verbose:
    print "creating", pyglobusTar
    print 'cmd = ', cmd
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)

pyopensslTar = '%s-%s.tar.gz' % (PYOPENSSL,PYOPENSSL_VER)
cmd = 'tar czf %s pyOpenSSL' % (pyopensslTar,)
if options.verbose:
    print "creating", pyopensslTar
    print 'cmd = ', cmd
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)

agmediaTar = '%s-%s.tar.gz' % (AGMEDIA,AGMEDIA_VER)
cmd = 'tar czf %s ag-media' % (agmediaTar,)
if options.verbose:
    print "creating", agmediaTar
    print 'cmd = ', cmd
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)

# - Create accessgrid source tarball
os.chdir(TmpDir)
ag = 'agtk-%s' % (options.version,)
if os.path.exists(ag):
    os.remove(ag)
os.symlink(options.builddir,ag)
agTar = '%s.tar.gz' % (ag,)
cmd = 'tar czhf %s/%s %s' % (SourceDir,agTar,ag)
if options.verbose:
    print "creating", agTar
    print 'cmd = ', cmd
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)

# - Build list of tars created, for printing only
tars = [ pyglobusTar, pyopensslTar, agmediaTar ]



#
# Build portage tree
#
print "\n\n---- Build portage tree\n"

os.chdir(TmpDir)
os.mkdir('portage')

portDirs = []
portDirs.append( '%s/packaging/linux/gentoo' % (BuildDir,))
portDirs.append( '%s/pyOpenSSL' % (SourceDir,))
portDirs.append( '%s/ag-media' % (SourceDir,))
for d in portDirs:
    cmd = 'cp -r %s/portage %s' % (d,TmpDir)
    print 'cmd = ', cmd
    ret = os.system(cmd)
    if ret != 0:
        print "error in build (%s); exiting" % (ret)
        sys.exit(1)

# - Move agtk.ebuild to properly versioned name
ag_ebuild = 'agtk-%s.ebuild' % (options.version,)
cmd = 'cd portage/ag-libs/agtk ; mv agtk.ebuild %s' % (ag_ebuild,)
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)


#
# Generate digests for ebuilds
#
print "\n\n---- Generate ebuild digests\n"
os.chdir(TmpDir)
os.chdir('portage')

# - Create digests for ebuilds
os.environ["ROOT"] = os.getcwd()
f = os.popen('find . -name "*.ebuild"')
ebuilds = map( lambda x: x.strip(), f.readlines() )
f.close()
for ebuild in ebuilds:
    cmd = 'DISTDIR=%s ebuild %s digest' % (SourceDir,ebuild,)
    if options.verbose:
        print "cmd = ", cmd
    ret = os.system(cmd)
    if ret != 0:
        print "error in build (%s); exiting" % (ret)
        sys.exit(1)
    
    
#
# Create ebuild package
#

print "\n\n---- Create ebuild package\n"

# - Generate list of ebuild dirs for package
ebuildDirs = []
for ebuild in ebuilds:
    ebuildDir = string.split(ebuild,os.sep)[1]
    if ebuildDir not in ebuildDirs:
        ebuildDirs.append(ebuildDir)

ebuildDirs = " ".join(ebuildDirs)

ebuildPackageFile = 'AccessGrid-%s.tar.gz' % (options.version)
ebuildPackagePath = os.path.join(DestDir,ebuildPackageFile)
cmd = "tar czf %s %s" % (ebuildPackagePath, ebuildDirs)
if options.verbose:
    print "cmd = ", cmd
ret = os.system(cmd)
if ret != 0:
    print "error in build (%s); exiting" % (ret)
    sys.exit(1)

#
# Cleanup
#
# - Remove temp directory
#os.removedirs(TmpDir)


# 
# Output build results
#
print "\n\n---- Build results\n"
print 'ebuild file:', ebuildPackagePath
print 'agtk source tarball:', os.path.join(DestDir,agTar)
print 'tar files in %s:' % (BuildDir)
for tar in tars:
    print "  ", tar
    
    



