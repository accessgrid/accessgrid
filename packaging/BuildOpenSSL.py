import sys, os

DEST=sys.argv[1]

def BuildLinux():
    os.system("./config")
    os.system("make")
    os.system("make test")

def BuildWindows():
    
    os.system("perl Configure VC-WIN32")

    masmPath = os.path.join(os.getcwd(), 'ms', 'do_masm.bat')
    os.system(masmPath)

    ntPath = os.path.join(os.getcwd(), 'ms', 'ntdll.mak')
    os.system('nmake -f %s' %ntPath)

    out32dllPath = os.path.join(os.getcwd(), "out32dll")

    cmd = "copy %s %s" % (os.path.join(out32dllPath, "ssleay32.dll"),
                        os.path.join(DEST,'install'))
    os.system(cmd)
    
    cmd = "copy %s %s" % (os.path.join(out32dllPath, "libeay32.dll"),
                        os.path.join(DEST,'install'))
    os.system(cmd)
    
def BuildDarwin():
    os.system("./config --openssldir=%s" % DEST)
    os.system("make")

os.chdir(os.path.abspath(os.path.join(os.environ['AGBUILDROOT'],
                                      "openssl-0.9.8g")))

if sys.platform == 'linux2':
    BuildLinux()
elif sys.platform == 'win32':
    BuildWindows()
elif sys.platform == 'darwin':
    BuildDarwin()
else:
    print "Can't build for you!"
    
