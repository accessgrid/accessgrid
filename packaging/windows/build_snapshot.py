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
import shutil

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

# Names for the software
long_version_name = "Access Grid Toolkit 2.0 Snapshot %s" % BuildTime
short_version_name = "agtk-%s" % BuildTime

# Innosoft config file names
iss_orig = "agtk.iss"
iss_new  = "build_snap.iss"

# Innosoft path
innopath = ""

# CVS Flag
checkoutnew = 0

# Verbosity flag
verbose = 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "n:s:d:t:i:l:r:chv",
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
    elif o in ("-r", "--shortname"):
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


# Make sure destination directory is valid

if not os.path.exists(DestDir):
    print "Creating desination directory:",DestDir
    try:
        os.mkdir(DestDir)
    except OSError:
        print "\nError: Could not create Desination Dir:",DestDir
        print "\nPlease specify a different Destination Directory with command-line option -d."
        sys.exit()
if not os.path.exists(DestDir):
    print "Destination Dir is invalid:",DestDir
    sys.exit()


build_dir = os.path.join(TempDir, BuildTime)

#
# We keep a rat and vic directory around as these don't change much
#

rat_dir = os.path.join(SourceDir, "ag-rat")
vic_dir = os.path.join(SourceDir, "ag-vic")

#
# Location of the Inno compiler
#

# If innopath specified at command-line, set inno_compiler
if "" != innopath:
    inno_compiler = os.path.join(innopath, "iscc.exe")
    if not os.path.exists(inno_compiler):
        print "command-line innopath not found: ", inno_compiler
        sys.exit()

# If no command-line specified, look in the registry
else:
    try:
        ipreg = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                   "Software\\Bjornar Henden\\ISTool\\Prefs")
        innopath, type = _winreg.QueryValueEx(ipreg, "ExtFolder")
        ip = os.path.join(innopath, "iscc.exe")
        inno_compiler = win32api.GetShortPathName(ip)
    except WindowsError:
        if verbose:
            print "Couldn't find ISXTool from registry key." 

        # If still not found, try default path:
        innopath = r"\Program Files\My Inno Setup Extensions 3"
        inno_compiler = os.path.join(innopath, "ISCC.exe")
        if verbose:
            if os.path.exists(inno_compiler):
                print "Found ISXTool in default path:", inno_compiler
            else:
                print "Could not find ISXTool in default path:", inno_compiler

# Print error and exit if innotool's iscc.exe isn't found yet.
if not os.path.exists(inno_compiler):
        print "Couldn't find ISXTool!"
        print "  Make sure My Inno Setup Extentions are installed, and if" 
        print "  necessary, specify the location of iscc.exe with command-line option -i."
        sys.exit()


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

packaging_dir = os.path.join(SourceDir, r"AccessGrid\packaging\windows")
if verbose:
    print "Packaging Directory:", packaging_dir
os.chdir(packaging_dir)

# Open new (and old) innosoft setup files
file = open(iss_orig)
new_file = open(iss_new, "w")

# build a bunch of regular expressions
fix_srcdir_src = re.escape(r'C:\AccessGridBuild')
fix_srcdir_dst = SourceDir.replace('\\', r'\\')
if verbose:
    print "S SRC:",  fix_srcdir_src, " S DST: ", fix_srcdir_dst

fix_dstdir_src = re.escape(r'C:\AccessGridBuild\AccessGrid-Build')
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

    line = re.sub(fix_dstdir_src, fix_dstdir_dst, line)
    line = re.sub(fix_vic_src, fix_vic_dst, line)
    line = re.sub(fix_rat_src, fix_rat_dst, line)
    # Replace srcdir last is a substring of dstdir, rat_src, and vic_src
    line = re.sub(fix_srcdir_src, fix_srcdir_dst, line)

    # Fix up application version strings
    if line.startswith("#define AppVersionLong"):
        line = '#define AppVersionLong "%s"\n' % (long_version_name)

    if line.startswith("#define AppVersionShort"):
        line = '#define AppVersionShort "%s"\n' % (short_version_name)

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

# Add quotes around command.
inno_compiler_exec = "\"" + inno_compiler + "\""
inno_compiler_command = inno_compiler_exec + " " + iss_new
if verbose:
    print "Executing:",inno_compiler_command, "from directory: ", os.getcwd()
os.system(inno_compiler_command)

#
# Now we clean up
#

os.remove(iss_new)

shutil.rmtree(build_dir)
shutil.rmtree(os.path.join(SourceDir, r"AccessGrid\Release"))
shutil.rmtree(os.path.join(SourceDir, r"AccessGrid\build"))

