import sys, os

def BuildLinux():
    os.system("./config")
    os.system("make")
    os.system("make test")

def BuildWindows():
    os.system("perl Configure VC-WIN32")
    os.system("ms/do_masm.bat")
    os.system("nmake -f ms/ntdll.mak")
    os.system("nmake -f ms/nt.mak")

def BuildDarwin():
    pass

os.chdir(os.path.abspath(os.path.join(os.environ['AGBUILDROOT'],
                                      "openssl-0.9.7d")))

if sys.platform == 'linux2':
    BuildLinux()
elif sys.platform == 'win32':
    BuildWindows()
elif sys.platform == 'darwin':
    BuildDarwin()
else:
    print "Can't build for you!"
    
