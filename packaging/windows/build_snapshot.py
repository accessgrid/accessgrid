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
import sys
import os
import os.path
import time
import re
import win32api
import win32con
import getopt
import _winreg
from win32com.shell import shell, shellcon

def usage():
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -s|--sourcedir <directory> : source directory"
    print "    -d|--destdir <directory> : destination directory"
    print "    -t|--tempdir <directory> : temporary directory"
    print "    -i|--innopath <directory> : path to isxtool"
    print "    -l|--longname <name> : long name of the release"
    print "    -n|--shortname <name> : short name of the release"
    print "    -c|--checkoutcvs : get a fresh copy from cvs"
    print "    -v|--verbose : be noisy"

def del_dir(path):
    for file in os.listdir(path):
        file_or_dir = os.path.join(path,file)
        if os.path.isdir(file_or_dir) and not os.path.islink(file_or_dir):
            #it's a directory reucursive call to function again
            del_dir(file_or_dir) 
        else:
            try:
                #it's a file, delete it
                os.remove(file_or_dir) 
            except:
                #probably failed because it is not a normal file
                win32api.SetFileAttributes(file_or_dir,
                                           win32con.FILE_ATTRIBUTE_NORMAL)
                #it's a file, delete it
                os.remove(file_or_dir)
        #delete the directory here
        os.rmdir(path) 

# Names for the software
long_version_name = ""
short_version_name = ""

# Source Directory
#  We assume the following software is in this directory:
#    ag-rat, ag-vic, and AccessGrid
SourceDir = r"C:\Software"

# Temporary Directory
#  This is where interim cruft is kept, it should be cleaned out every time
TempDir = win32api.GetTempPath()

#print "TempDir is: ", TempDir

# Destination Directory
#  This is where the installer is left at the end
DestDir = r"C:\xfer"

# Build Name
#  This is the default name we use for the installer
BuildTime = time.strftime("%Y-%m%d-%H%M%S")
BuildName = BuildTime

# Innosoft config file names
iss_orig = "agtk.iss"
iss_new  = "build_snap.iss"

# CVS Flag
checkoutnew = 0

# Verbosity flag
verbose = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "n:s:d:t:i:l:n:chv",
                               ["buildname", "sourcedir", "destdir",
                                "tempdir", "innopath", "longname",
                                "shortname", "checkoutcvs", "help",
                                "verbose"])
except:
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-n", "--buildname"):
        BuildName = a
    elif o in ("-s", "--sourcedir"):
        SourceDir = a
    elif o in ("-d", "--destdir"):
        DestDir = a
    elif o in ("-t", "--tempdir"):
        TempDir = a
    elif o in ("-i", "--innopath"):
        innopath = a
    elif o in ("-l", "--longname"):
        long_version_name = a
    elif o in ("-n", "--shortname"):
        short_version_name = a
    elif o in ("-c", "--checkoutcvs"):
        checkoutnew = 1
    elif o in ("-h", "--help"):
        usage()
        sys.exit(0)
    elif o in ("-v", "--verbose"):
        verbose = 1
    else:
        usage()
        sys.exit(0)

# Obvious variables we can use are SYSTEMDRIVE and HOMEDRIVE.
build_dir = os.path.join(TempDir, BuildTime)

#
# We keep a rat and vic directory around as these don't change much
#

rat_dir = os.path.join(SourceDir, "ag-rat")
vic_dir = os.path.join(SourceDir, "ag-vic")

#
# Location of the Inno compiler
#

try:
    ipreg = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                               "Software\\Bjornar Henden\\ISTool\\Prefs")
    innopath, type = _winreg.QueryValueEx(ipreg, "ExtFolder")
    ip = os.path.join(innopath, "iscc.exe")
    inno_compiler = win32api.GetShortPathName(ip)
except WindowsError:
    print "Cound't find ISXTool!"

if verbose:
    print "ISXTool is: ", inno_compiler

os.mkdir(build_dir)
os.chdir(build_dir)

bd = build_dir
build_dir = win32api.GetShortPathName(bd)

if verbose:
    print "builddir ", build_dir

if checkoutnew:
    # Either we check out a copy
    cvsroot = ":pserver:anonymous@fl-cvs.mcs.anl.gov:/cvsroot"

    os.environ['CVSROOT'] = cvsroot

    cmd = '"cvs login"'
    if verbose:
        print "cmd=", cmd
    (wr, rd) = os.popen4(cmd)
    wr.write("\n")

    while 1:
        l = rd.readline()
        if verbose:
            print "read ", l,
        if l == '':
            break

    wr.close()
    rd.close()

    os.system("cvs -z6 export -D now AccessGrid")
    
# Okay, we've got our code. Go to the packaging
# directory and fix up the paths in the iss file
os.chdir(os.path.join(SourceDir, r"AccessGrid\packaging\windows"))

# Open new (and old) innosoft setup files
file = open(iss_orig)
new_file = open(iss_new, "w")

# build a bunch of regular expressions
fix_srcdir_src = re.escape(r'C:\AccessGridBuild')
fix_srcdir_dst = SourceDir.replace('\\', r'\\')
if verbose:
    print "S SRC:",  fix_srcdir_src, " S DST: ", fix_srcdir_dst

fix_dstdir_src = re.escape(r'C:\Software\AccessGrid-Build')
fix_dstdir_dst = DestDir.replace('\\', r'\\')
if verbose:
    print "D SRC: ", fix_dstdir_src, " D DST: ", fix_dstdir_dst

fix_vic_src = re.escape(r'C:\AccessGridBuild\ag-vic')
fix_vic_dst = vic_dir.replace('\\', r'\\')
if verbose:
    print "V SRC: ", fix_vic_src, " V DST: ", fix_vic_dst

fix_rat_src = re.escape(r'C:\AccessGridBuild\ag-rat')
fix_rat_dst = rat_dir.replace('\\', r'\\')
if verbose:
    print "R SRC: ", fix_rat_src, " R DST: ", fix_rat_dst

section_re = re.compile(r"\[\s*(\S+)\s*\]")
prebuild_re = re.compile(r"^Name:\s+([^;]+);\s+Parameters:\s+([^;]+)")

commands = []
section = ""

for line in file:

    # Fix up vic, rat, source, and destination paths
    line = re.sub(fix_vic_src, fix_vic_dst, line)
    line = re.sub(fix_rat_src, fix_rat_dst, line)
    line = re.sub(fix_srcdir_src, fix_srcdir_dst, line)
    line = re.sub(fix_dstdir_src, fix_dstdir_dst, line)

    # Fix up application version strings
    if line.startswith("#define AppVersionLong"):
        if long_version_name != "":
            line = '#define AppVersionLong "%s"\n' % (long_version_name)
        else:
            line = '#define AppVersionLong "Snapshot %s"\n' % (BuildTime)
    if line.startswith("#define AppVersionShort"):
        if short_version_name != "":
            line = '#define AppVersionShort "%s"\n' % (short_version_name)
        else:
            line = '#define AppVersionShort "%s"\n' % (BuildTime)

    m = section_re.search(line)

    if m:
        section = m.group(1)
        
    if section == "_ISToolPreCompile":
        m = prebuild_re.search(line)
        if m:
            cmd = m.group(1)
            args = m.group(2)
            commands.append((cmd, args))
    new_file.write(line)

# Close the new (and old) Innosoft setup files
file.close()
new_file.close()

#
# Run the stuff that is precompile section
#

print commands

for cmd, args in commands:
    if verbose:
        print "Executing command: %s %s" % (cmd, args)
    rc = os.system(cmd + " " + args)
    if rc != 0:
        print "Command failed: %s %s" % (cmd, args)
        sys.exit(1)

#
# Now we can compile
#

os.system(inno_compiler + " " + iss_new)

#
# Now we clean up
#

#os.remove(iss_new)

del_dir(build_dir)
del_dir(os.path.join(SourceDir, "AccessGrid\Release"))
del_dir(os.path.join(SourceDir, "AccessGrid\build"))
