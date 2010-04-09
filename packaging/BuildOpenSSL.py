import sys, os

DEST=sys.argv[1]

def BuildLinux():
    ret = os.system("./config")
    if ret:
        return ret
    ret = os.system("make")
    if ret:
        return ret
    ret = os.system("make test")
    
    return ret

def BuildWindows():

    opensslinstalldir = opensslinstalldir.replace('\\','\\\\')
    
    ret = os.system("perl Configure VC-WIN32 --prefix=%s" % opensslinstalldir)
    if ret:
        return ret

    masmPath = os.path.join(os.getcwd(), 'ms', 'do_masm.bat')
    ret = os.system(masmPath)
    if ret:
        return ret

    ntPath = os.path.join(os.getcwd(), 'ms', 'ntdll.mak')
    ret = os.system('nmake -f %s install' %ntPath)
    if ret:
        return ret

    out32dllPath = os.path.join(os.getcwd(), "out32dll")

    cmd = "copy %s %s" % (os.path.join(out32dllPath, "ssleay32.dll"),
                        os.path.join(DEST,'install'))
    ret = os.system(cmd)
    if ret:
        return ret
    
    cmd = "copy %s %s" % (os.path.join(out32dllPath, "libeay32.dll"),
                        os.path.join(DEST,'install'))
    ret = os.system(cmd)
    
    return ret
    
def BuildDarwin():
    ret = os.system("./config shared --prefix=%s" % opensslinstalldir )
    if ret:
        return ret
    ret = os.system("make")
    if ret:
        return ret
    ret = os.system("make install_sw")

    return ret

os.chdir(os.path.abspath(os.path.join(os.environ['AGBUILDROOT'],
                                      "openssl-0.9.8e")))
opensslinstalldir = os.path.abspath(os.path.join(os.getcwd(),'opensslinstall'))

if sys.platform == 'linux2':
    ret = BuildLinux()
elif sys.platform == 'win32':
    ret = BuildWindows()
elif sys.platform == 'darwin':
    ret = BuildDarwin()
else:
    print "Can't build for you!"
    
sys.exit(ret)
