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

import sys
import shutil
import os
import os.path
import time
import re

build_base = "/tmp/snap"

build_tag = time.strftime("%Y-%m%d-%H%M")

build_dir = os.path.join(build_base, build_tag)

print "builddir ", build_dir

#
# Set the version and release that goes into the RPM.
#

build_version = "2.0beta"
build_release = time.strftime("%Y%m%d%H%M")

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
r = os.system("tar czf /usr/src/redhat/SOURCES/AccessGrid-%s.tar.gz AccessGrid-%s" % (build_version, build_version))
if r != 0:
    print "tar failed with rc ", rc
    sys.exit(1)

#
# Copy the spec file into the redhat dir.
#

fh_orig = open("AccessGrid-%s/packaging/redhat/AccessGrid.spec" % (build_version), "r")
fh_new = open("/usr/src/redhat/SPECS/AccessGrid.spec", "w")

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

os.chdir("/usr/src/redhat/SPECS")

os.system("rpm -ba AccessGrid.spec")
