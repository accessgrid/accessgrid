import sys, os, time
from optparse import OptionParser
import win32api, _winreg
from win32com.shell import shell, shellcon

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
                  metavar="PYTHONVERSION", default="2.2",
                  help="Which version of python to build the installer for.")

options, args = parser.parse_args()

# Run precompile scripts
for cmd in [
    "BuildVic.cmd",
    "BuildRat.cmd",
    "BuildPythonModules.cmd"
    ]:
    cmd = "%s %s %s %s %s" % (cmd, options.sourcedir, options.builddir,
                              options.destdir, options.version)
    if options.verbose:
        print "BUILD: Running: %s" % cmd

    os.system(cmd)

# Grab innosetup from the environment
try:
    ipreg = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            "Software\\Bjornar Henden\\ISTool4\\Prefs")
    innopath, type = _winreg.QueryValueEx(ipreg, "InnoFolder")
    ip = os.path.join(innopath, "iscc.exe")
    inno_compiler = win32api.GetShortPathName(ip)
except WindowsError:
    print "BUILD: Couldn't find iscc from registry key." 
    
    # If still not found, try default path:
    innopath = r"\Program Files\ISTool 4"
    inno_compiler = os.path.join(innopath, "iscc.exe")

if options.verbose:
    if os.path.exists(inno_compiler):
        print "BUILD: Found ISXTool in default path:", inno_compiler
    else:
        print "BUILD: Couldn't find ISXTool!"
        print "BUILD:   Make sure My Inno Setup Extentions are installed."
        print "BUILD:   If necessary, specify the location of iscc.exe "
        print "BUILD:   with command-line option -i."
        sys.exit()

# Add quotes around command.
iscc_cmd = "%s agtk.iss /dAppVersion=\"%s\" /dVersionInformation=\"%s\" \
            /dSourceDir=\"%s\" /dBuildDir=\"%s\" /dPythonVersion=\"%s\"" % \
            (inno_compiler, options.version,
             options.metainfo.replace(' ', '_'), 
             options.sourcedir, options.destdir, options.pyver)

if options.verbose:
    print "BUILD: Executing:", iscc_cmd

# Compile the installer
os.system(iscc_cmd)

