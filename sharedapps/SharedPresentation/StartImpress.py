
# A start script is required because OpenOffice's python is needed in order to
#   communicate with it (through pyuno).

#from AccessGrid import ProcessManager
from AccessGrid import Platform
from GetPaths import GetOOHomeDir
import sys, time, os

#app = Toolkit.GetApplication
#app = Toolkit.CmdlineApplication()
#processManager = ProcessManager.ProcessManager()

StartDir = os.getcwd()

OOProgramDir = os.path.join(GetOOHomeDir(), "program")
os.chdir(OOProgramDir)
#OOPythonInstallDir = GetOOPythonInstallDir()

#OOSharedPresentationPath = os.path.join(OOPythonInstallDir, "SharedPresentation.py")
OOSharedPresentationPath = os.path.join(StartDir, "SharedPresentation.py")
if sys.platform == Platform.WIN:
    # avoid problem with spaces in filename
    import win32api
    OOSharedPresentationPath = win32api.GetShortPathName(OOSharedPresentationPath)
    OOProgramDir = win32api.GetShortPathName(OOProgramDir)

arglist = [OOSharedPresentationPath]
for arg in sys.argv[1:]:
    arglist.append(arg)
print "starting:", arglist

command = os.path.join(OOProgramDir, "python")
arglist.insert(0, command)
arglist = map(lambda a: str(a), arglist)

# Set Python path so files can be imported.
if sys.platform != Platform.WIN:
    old_path = os.environ.get("PYTHONPATH")
    if old_path:
        new_path = StartDir + ":" + old_path
    else:
        new_path = str(StartDir)
    os.environ["PYTHONPATH"] = new_path


# Start our shared presenation.
print "starting:", command, arglist[1:]
if sys.platform == Platform.WIN:
    # windows doesn't have spawnvp()
    pid = os.spawnv(os.P_NOWAIT, command, arglist)
else:
    #pid = os.spawnvp(os.P_NOWAIT, command, arglist)
    pid = os.spawnvpe(os.P_NOWAIT, command, arglist, os.environ)

