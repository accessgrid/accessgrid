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

os.makedirs(build_dir)
os.chdir(build_dir)

cvsroot = ":pserver:anonymous@fl-cvs.mcs.anl.gov:/cvsroot"

os.environ['CVSROOT'] = cvsroot

if 1:
    cmd = 'cvs login'
    print "cmd=", cmd
    (wr, rd) = os.popen4(cmd)
    wr.write("\n")
    wr.close()
    while 1:
        l = rd.readline()
        print "read ", l,
        if l == '':
            break

    rd.close()

    os.system("cvs export -D now AccessGrid")

#
# Okay, we've got our code checked out. Create
# the tarball for RPM.
#

os.rename("AccessGrid", "AccessGrid-2.0")
r = os.system("tar czf /usr/src/redhat/SOURCES/AccessGrid-2.0.tar.gz AccessGrid-2.0")
if r != 0:
    print "tar failed with rc ", rc
    sys.exit(1)

#
# Copy the spec file into the redhat dir.
#


shutil.copyfile("AccessGrid-2.0/packaging/redhat/AccessGrid.spec",
                "/usr/src/redhat/SPECS/AccessGrid.spec")

os.chdir("/usr/src/redhat/SPECS")

os.system("rpm -ba AccessGrid.spec")
