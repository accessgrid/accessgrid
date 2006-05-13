#!/usr/bin/env python

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
                  metavar="PYTHONVERSION", default="2.4",
                  help="Which version of python to build the installer for.")
parser.add_option("--dist", dest="dist",
                  metavar="DISTRIBUTION", default="freebsd",
                  help="Which distribution to build")
options, args = parser.parse_args()

SourceDir = options.sourcedir
BuildDir = options.builddir
DestDir = options.destdir
metainfo = options.metainfo
version = options.version

StartDir = os.getcwd()

#
# Define packages to include in src distribution
#
d,agsourcedir = os.path.split(BuildDir)
distDirs = [agsourcedir,
            "ag-media",
            "pyxml",
            "pyOpenSSL",
            "zsi",
            ]

#
# Create the targz from the source dir
#
os.chdir(StartDir)
targz = os.path.join(SourceDir, "AccessGrid-%s-%s.src.tar.gz" % (version,metainfo))
cmd = "tar cvzhf %s --directory %s %s" % (targz, SourceDir, distDirStr)
print "cmd = ", cmd
os.system(cmd)


#
# Build the next level package
#
pkg_script = "BuildPackage.py"
DistDir = os.path.join(StartDir,options.dist)
if os.path.exists(DistDir):
    os.chdir(DistDir)
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
    print "Error building distribution %s; directory not found." % (options.dist,)


