#
# Build a windows installer snapshot.
#

#
# Basic plan:
#
# Create a snapshot build directory.
# cd to it, and cvs export the ag-vic, ag-rat, and AccessGrid modules
# cd to the AccessGrid/packaging/windows dir
# modify the paths to point at the build dir
# modify AppVersionLong and AppVersionShort to be the snapshot name
# kick off a build
#
# Also need to modify setup.py to change the version there to match
# this snapshot version.
#

import os
import os.path
import time
import re

build_base = r"c:\temp\snap"

build_tag = time.strftime("%Y-%m%d-%H%M")

build_dir = os.path.join(build_base, build_tag)

#
# We keep a rat and vic directory around as these don't change much
#

rat_dir = r"c:\AccessGridBuild\ag-rat"
vic_dir = r"c:\AccessGridBuild\ag-vic"

print "builddir ", build_dir
os.mkdir(build_dir)
os.chdir(build_dir)

cvsroot = ":pserver:anonymous@fl-cvs.mcs.anl.gov:/cvsroot"

os.environ['CVSROOT'] = cvsroot

if 1:
    cmd = '"cvs login"'
    print "cmd=", cmd
    (wr, rd) = os.popen4(cmd)
    wr.write("\n")

    while 1:
        l = rd.readline()
        print "read ", l,
        if l == '':
            break

    wr.close()
    rd.close()

    os.system("cvs co AccessGrid")

#
# Okay, we've got our code checked out. Go to the packaging
# directory and fix up the paths in the iss file
#

os.chdir("AccessGrid\\packaging\\windows")

fp = open("ag-2.0beta.iss", "r")
new_fp = open("build_snap.iss", "w")

fix_dir_src = re.escape(r'C:\AccessGridBuild')
fix_dir_dst = build_dir.replace('\\', r'\\')
print fix_dir_src, fix_dir_dst

fix_vic_src = re.escape(r'C:\AccessGridBuild\ag-vic')
fix_vic_dst = vic_dir.replace('\\', r'\\')

fix_rat_src = re.escape(r'C:\AccessGridBuild\ag-rat')
fix_rat_dst = rat_dir.replace('\\', r'\\')

for l in fp:

    l = re.sub(fix_vic_src, fix_vic_dst, l)
    l = re.sub(fix_rat_src, fix_rat_dst, l)

    l = re.sub(fix_dir_src, fix_dir_dst, l)

    if l.startswith("#define AppVersionLong"):
        l = '#define AppVersionLong "2.0 Snapshot %s"\n' % (build_tag)
    elif l.startswith("#define AppVersionShort"):
        l = '#define AppVersionShort "2.0-%s"\n' % (build_tag)

    new_fp.write(l)

fp.close()
new_fp.close()
