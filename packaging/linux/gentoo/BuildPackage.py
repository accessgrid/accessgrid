#!/usr/bin/python2

import sys, os, time, string
from optparse import OptionParser

from Dependency import *

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


print "In gentoo/build_package.py"
print "SourceDir = ", SourceDir
print "BuildDir = ", BuildDir
print "DestDir = ", DestDir
print "metainfo = ", metainfo
print "version = ", version

TmpDir = os.tmpnam()
if not os.path.exists(TmpDir):
    os.mkdir(TmpDir)
RpmDir = os.path.join(TmpDir,"AccessGrid-%s-%s" % (version,metainfo))
if not os.path.exists(RpmDir):
    os.mkdir(RpmDir)
StartDir = os.getcwd()



#
# Create source tarballs
#

os.chdir(SourceDir)

# - Create dependency source tarballs
pyglobusTar = '%s-%s.tar.gz' % (PYGLOBUS,PYGLOBUS_VER)
cmd = 'tar czf %s pyGlobus' % (pyglobusTar)
if options.verbose:
    print 'cmd = ', cmd
os.system(cmd)

pyopensslTar = '%s-%s.tar.gz' % (PYOPENSSL,PYOPENSSL_VER)
cmd = 'tar czf %s pyOpenSSL' % (pyopensslTar)
if options.verbose:
    print 'cmd = ', cmd
os.system(cmd)

agmediaTar = '%s-%s.tar.gz' % (AGMEDIA,AGMEDIA_VER)
cmd = 'tar czf %s ag-media' % (agmediaTar)
if options.verbose:
    print 'cmd = ', cmd
os.system(cmd)

# - Create accessgrid source tarball
agTar = 'agtk-%s.tar.gz' % (options.version)
cmd = 'tar czf %s %s' % (agTar,options.builddir)
if options.verbose:
    print 'cmd = ', cmd
os.system(cmd)

# - Build list of tars created, for printing only
tars = [ pyglobusTar, pyopensslTar, agmediaTar ]



#
# Create ebuild package
#

# - Create tarball of custom ebuild tree
os.chdir(StartDir)

# - Move agtk.ebuild to properly versioned name
ag_ebuild = 'agtk-%s.ebuild' % (options.version,)
if not os.access(os.path.join('portage','ag-libs','agtk',ag_ebuild), os.F_OK):
    cmd = 'cd portage/ag-libs/agtk ; mv agtk.ebuild %s' % (ag_ebuild,)
    os.system(cmd)

# - Create digests for ebuilds
os.chdir('portage')
os.environ["ROOT"] = os.getcwd()
f = os.popen('find . -name "*.ebuild"')
ebuilds = map( lambda x: x.strip(), f.readlines() )
f.close()
for ebuild in ebuilds:
    cmd = 'DISTDIR=%s ebuild %s digest' % (SourceDir,ebuild,)
    if options.verbose:
        print "cmd = ", cmd
    os.system(cmd)
    
# - Generate list of ebuild dirs for package
ebuildDirs = []
for ebuild in ebuilds:
    ebuildDir = string.split(ebuild,os.sep)[1]
    if ebuildDir not in ebuildDirs:
        ebuildDirs.append(ebuildDir)

ebuildDirs = " ".join(ebuildDirs)

ebuildPackageFile = 'AccessGrid-%s.tar.gz' % (options.version)
ebuildPackagePath = os.path.join(BuildDir,ebuildPackageFile)
cmd = "tar czf %s %s" % (ebuildPackagePath, ebuildDirs)
if options.verbose:
    print "cmd = ", cmd
os.system(cmd)

# - Move dependency tarballs to dest dir
for tar in tars + [agTar]:
    cmd = 'mv %s/%s %s' % (SourceDir,tar,DestDir)
    if options.verbose:
        print "cmd = ", cmd
    os.system(cmd)


# 
# Output build results
#
print '\n', '-'*50
print 'Build results:'
print 'ebuild file: ', ebuildPackagePath
print 'agtk source tarball:', os.path.join(DestDir,agTar)
print 'tar files in %s:' % (BuildDir)
for tar in tars:
    print "  ", tar


