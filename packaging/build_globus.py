import sys, os

def BuildLinux():
    print "Nothing to be done"

def BuildDarwin():
    print "Nothing to be done"
    
def BuildWindows():
    wdir = "WinProjects/SourceSolution"
    os.system("devenv %s/DebugLib/All_Libs.sln /rebuild Debug" % wdir)
    os.system("devenv %s/DebugThreadedLib/All_Libs.sln /build Debug" % wdir)
    os.system("devenv %s/DebugLib/All_Libs.sln /project gss_assist /rebuild Debug" % wdir)
    os.system("devenv %s/DebugLib/All_Libs.sln /project gssapi /rebuild Debug" % wdir)

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



