#
# Build a windows installer snapshot.
#

#
# Basic plan:
#
# Create a snapshot build directory.
# cd to it, and cvs export the AccessGrid module
# cd to the AccessGrid/packaging/windows dir
# modify the paths to point at the build dir
# modify AppVersionLong and AppVersionShort to be the snapshot name
# run the precompile scripts
# invoke the innosetup compiler on the modified iss file
#
# Also need to modify setup.py to change the version there to match
# this snapshot version.
#
# Arguments:
#   -o outputdir
#   --shortname <short version name>
#   --longname  <long version name>
#

import sys
import os
import os.path
import time
import re
import win32api
import getopt

def usage():
    print """

 build_snapshot [-l] <longname> [-s] <shortname>

 -l        set the long name of the package, i.e. "2.0 Beta 3" 
 -s        set the short name of the package, i.e. "2.0b3" 

"""

long_version_name = ""
short_version_name = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], "l:s:" )
except:
    # print help information and exit
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-l", "--longname"):
        long_version_name = a
        print "Long Name set to: ",long_version_name
    if o in ("-s", "--shortname"):
        short_version_name = a
        print "Short name set to: ",short_version_name

# Obvious variables we can use are SYSTEMDRIVE and HOMEDRIVE.
INSTDRIVE = os.getenv("HOMEDRIVE")

build_base = INSTDRIVE + r"\temp\snap"

build_tag = time.strftime("%Y-%m%d-%H%M")

build_dir = os.path.join(build_base, build_tag)

#
# We keep a rat and vic directory around as these don't change much
#

rat_dir = INSTDRIVE + r"\AccessGridBuild\ag-rat"
vic_dir = INSTDRIVE + r"\AccessGridBuild\ag-vic"

#
# Location of the Inno compiler
#

inno_compiler = INSTDRIVE + r"\Program Files\My Inno Setup Extensions 3\ISCC.exe"

#
# Mangle it to remove spaces; this also ensures it is present.
#

inno_compiler = win32api.GetShortPathName(inno_compiler)
print "compiler is ", inno_compiler

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

    os.system("cvs -z6 export -D now AccessGrid")

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

section_re = re.compile(r"\[\s*(\S+)\s*\]")
prebuild_re = re.compile(r"^Name:\s+([^;]+);\s+Parameters:\s+([^;]+)")

commands = []
section = ""

# Use this to help us replace C: with whatever drive we're using.
drive_replace = re.compile('C:|c:')

for l in fp:

    l = re.sub(fix_vic_src, fix_vic_dst, l)
    l = re.sub(fix_rat_src, fix_rat_dst, l)

    l = re.sub(fix_dir_src, fix_dir_dst, l)

    if l.startswith("#define AppVersionLong"):
        if long_version_name != "":
            l = '#define AppVersionLong "%s"\n' % (long_version_name)
        else:
            l = '#define AppVersionLong "2.0 Snapshot %s"\n' % (build_tag)
    elif l.startswith("#define AppVersionShort"):
        if short_version_name != "":
            l = '#define AppVersionShort "%s"\n' % (short_version_name)
        else:
            l = '#define AppVersionShort "2.0-%s"\n' % (build_tag)

    # Replace a few specific occurences of C: with INSTDRIVE
    if l.startswith("#define SourceDir") or l.startswith("#define OutputDir") or l.startswith("LogFile"):
        l = drive_replace.sub(INSTDRIVE,l)

    m = section_re.search(l)
    if m:
        section = m.group(1)

    if section == "_ISToolPreCompile":
        m = prebuild_re.search(l)
        if m:
            cmd = m.group(1)
            cmd = drive_replace.sub(INSTDRIVE,cmd)
            args = m.group(2)
            args = drive_replace.sub(INSTDRIVE,args)
            print "Have cmd='%s' args='%s'" % (cmd, args)
            commands.append((cmd, args))
    new_fp.write(l)

fp.close()
new_fp.close()

#
# We've created the new ISS file now.
#

#
# Run the stuff that is precompile section
#

for cmd, args in commands:
    rc = os.system(cmd + " " + args)
    if rc != 0:
        print "Command failed: %s %s" % (cmd, args)
        sys.exit(1)

#
# Now we can compile
#

os.system(inno_compiler + " " + "build_snap.iss")
