#
# Build redhat RPMs from a snapshot.
#

#
# Basic plan:
#
# Create a snapshot build directory.
# cd to it, and cvs export the AccessGrid module
# create a tarball for RPM to build from
# copy the tarball to /usr/src/redhat/SOURCES
# copy the spec file to /usr/src/redhat/SPECS
# chdir to /usr/src/redhat/SPECS
# run the build: rpm -ba AccessGrid.spec
#
# You can use command line options --specdir and --rpmsrcdir to change
#   rpm locations for other systems.  If you need do that, you probably
#   need make similar entries in your .rpmrc file.

import sys
import shutil
import os
import os.path
import time
import re
import getopt

def usage():
    print ""
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -n|--buildname <buildversionname> : specify build version name"
    print "           such as: \"2.0beta\""
    print "    -r|--releasename <releasename> : specify release name (such as \"3\")"
    print "    -t|--tempdir <tempdir> : specify temp build directory.  default: /tmp/snaps"
    print "    -p|--specdir <specdir> : specify spec directory. "
    print "           default: /usr/src/redhat/SPECS"
    print "           if not default, should reflect what's in your .rpmrc."
    print "    -o|--rpmsrcdir <rpmsrcdir> : specify rpm src directory."
    print "           default: /usr/src/redhat/SOURCES"
    print "           if not default, should reflect what's in your .rpmrc."
    print "    -v|--verbose : print extra inforation"
    print ""

# temp directory
build_base = "/tmp/snap"

# Default BuildName
build_tag = time.strftime("%Y-%m%d-%H%M%S")

# The version and release that goes into the RPM.
build_version = "2.0beta"
build_release = time.strftime("%Y%m%d%H%M%S")
default_spec_dir = "/usr/src/redhat/SPECS"
spec_dir = default_spec_dir

# Default rpm directories
default_rpm_srcdir = "/usr/src/redhat/SOURCES"
rpm_srcdir = default_rpm_srcdir

# Verbosity flag
verbose = 0


try:
    opts, args = getopt.getopt(sys.argv[1:], "n:r:t:m:p:vh",
                               ["buildname=", "releasename=", "tempdir=",
                                "rpmsrcdir=", "specdir=", "verbose", "help"])
except:
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-n", "--buildname"):
        build_version = a
    elif o in ("-r", "--releasename"):
        build_release = a
    elif o in ("-t", "--tempdir"):
        build_base = a
    elif o in ("-m", "--rpmsrcdir"):
        rpm_srcdir = a
    elif o in ("-p", "--specdir"):
        spec_dir = a
    elif o in ("-v", "--verbose"):
        verbose = 1
    elif o in ("-h", "--help"):
        usage()
        sys.exit(0)

build_dir = os.path.join(build_base, build_tag)

if verbose:
    print "\nbuild version:",build_version
    print "release name:",build_release
    print "temp dir:",build_base
    print "full temp path (build dir):",build_dir

if spec_dir != default_spec_dir:
    print "spec directory:",spec_dir
if rpm_srcdir != default_rpm_srcdir:
    print "rpm source directory:",rpm_srcdir

os.makedirs(build_dir)
os.chdir(build_dir)

cvsroot = ":pserver:anonymous@fl-cvs.mcs.anl.gov:/cvsroot"

os.environ['CVSROOT'] = cvsroot

rc = os.system("cvs export -D now AccessGrid")
if rc != 0:
    print "cvs failed"
    sys.exit(1)

#
# Okay, we've got our code checked out. Create
# the tarball for RPM.
#

os.rename("AccessGrid", "AccessGrid-%s" % (build_version))
tar_dst_filename = "AccessGrid-%s.tar.gz" % (build_version)
tar_src_filename = "AccessGrid-%s" % (build_version)

# default rpm_srcdir = "/usr/src/redhat/SOURCES"
tar_command = "tar czf " + os.path.join(rpm_srcdir, tar_dst_filename + " " + tar_src_filename)
r = os.system(tar_command)
if r != 0:
    print "tar command \"", tar_command, "\" failed with rc ", rc
    sys.exit(1)

#
# Copy the spec file into the redhat dir.
#

fh_orig_filename = "AccessGrid-%s/packaging/redhat/AccessGrid.spec" % (build_version)

fh_orig = open(fh_orig_filename, "r")
fh_new_filename = os.path.join(spec_dir, "AccessGrid.spec")
fh_new = open(fh_new_filename, "w")

#
# Read lines, replacing the version and release with what we want.
#

for l in fh_orig:
    if re.search(r"^%define\s+version\s+", l):
        l = "%define version\t\t" + build_version + "\n"
    elif re.search(r"^%define\s+release\s+", l):
        l = "%define release\t\t" + build_release + "\n"

    fh_new.write(l)

fh_orig.close()
fh_new.close()

#os.chdir("/usr/src/redhat/SPECS")
os.chdir(spec_dir)

rpm_command = "rpm -ba AccessGrid.spec"
if verbose:
    print "rpm command:",rpm_command
    os.system(rpm_command)

