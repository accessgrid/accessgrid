import sys, os

def BuildLinux():
    os.system("./config")
    os.system("make")
    os.system("make test")

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
    
    os.system("perl Configure VC-WIN32")

    masmPath = os.path.join(os.getcwd(), 'ms', 'do_masm.bat')
    os.system(masmPath)

    ntdllPath = os.path.join(os.getcwd(), 'ms', 'ntdll.mak')
    os.system('nmake -f %s' %ntdllPath)

    ntPath = os.path.join(os.getcwd(), 'ms', 'nt.mak')
    os.system('nmake -f %s' %ntPath)
    
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
    
