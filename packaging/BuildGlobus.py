import sys, os

def BuildLinux():
    print "Nothing to be done"

def BuildDarwin():
    print "Nothing to be done"

def vs_version():
    try:
        cmd = "cl"
        po = os.popen4(cmd)
    except IOError:
        print "Error getting AGTk Version."
        
    version = po[1].read()
    po[0].close()
    po[1].close()
        
    v = version.split('\n')[0].split('Version')[1].strip().split(' ')[0]
    major, minor, patch = map(int, v.split('.'))

    if major != 13 or (major == 13 and minor > 0):
        print "Please use MS Visual Studio v 7.0 to build globus."
        sys.exit(-1)
        
def BuildWindows():
    vs_version()
    
    ntsln = "WinProjects/SourceSolution/DebugLib/All_Libs.sln"
    tsln  = "WinProjects/SourceSolution/DebugThreadedLib/All_Libs.sln"
    # I think what really needs to happen here is something like:
    # build everything non-threaded
    # then build common, io threaded
    os.system("devenv %s /rebuild Debug" % ntsln)
    os.system("devenv %s /project common /rebuild Debug" % tsln)
    os.system("devenv %s /project io /rebuild Debug" % tsln)

os.chdir(os.path.abspath(os.path.join(os.environ['AGBUILDROOT'],
                                      "WinGlobus")))

if sys.platform == 'linux2':
    BuildLinux()
elif sys.platform == 'win32':
    BuildWindows()
elif sys.platform == 'darwin':
    BuildDarwin()
else:
    print "Can't build for you!"



