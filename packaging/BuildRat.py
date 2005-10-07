#!/usr/bin/python
#
# Build rat programs and stick them in the dist directory
#
import os
import sys

SOURCE=sys.argv[1]
DEST=sys.argv[2]

RATDIR=os.path.join(SOURCE,'ag-media')

def build_win(dir):
    # Find the version of visual studio by peering at cl
    (input, outerr) = os.popen4("cl.exe")
    usageStr = outerr.readlines()
    version = map(int, usageStr[0].split()[7].split('.')[:2])

    proj = None
    
    if version[0] == 12:
        proj = "rat.dsw"
    elif version[0] == 13:
        if version[1] == 0:
            proj = "rat.sln"
        elif version[1] == 10:
            proj = "rat.2003.sln"

    if proj is not None:
        os.system("devenv %s /rebuild Release" % os.path.join(dir, "rat-ui",
                                                              proj))
    
def build_linux(dir):
    os.chdir(dir)
    os.system('./rat-build')


# Set plat-specific bits
if sys.platform == 'win32':
    dir = os.path.join(RATDIR,'rat','Release')
    ratFiles = [ os.path.join(dir,'rat.exe'),
                 os.path.join(dir,'ratmedia.exe'),
                 os.path.join(dir,'ratui.exe'),
                 os.path.join(dir,'rat-kill.exe') ]
    copyExe = 'copy'
    build = build_win
elif sys.platform == 'linux2':
    dir = os.path.join(RATDIR,'rat')
    ratFiles = [ os.path.join(dir,'rat'),
                 os.path.join(dir,'rat-4.2.22'),
                 os.path.join(dir,'rat-4.2.22-media'),
                 os.path.join(dir,'rat-4.2.22-ui'),
                 os.path.join(dir,'rat-4.2.22-kill') ]
    copyExe = 'cp'
    build = build_linux
else:
    raise Exception, 'Unsupported platform: ' + sys.platform
    

# Check whether we need to build
needBuild = 0
for f in ratFiles:
    if not os.path.exists(f):
        needBuild = 1
        break

# Build and copy if necessary
if needBuild:
    build(RATDIR)

if os.path.exists(ratFiles[0]):
    for f in ratFiles:
        dest = DEST 
        if f.endswith('kill'):
            dest = os.path.join(DEST,'rat-kill')
        copyCmd = '%s %s %s' % (copyExe,f,dest)
        os.system(copyCmd)
else:
    print '** Error : rat files do not exist; not copying'

