#!/usr/bin/python2
#
# Build rat programs and stick them in the dist directory
#
import os
import sys

SOURCE=sys.argv[1]
DEST=sys.argv[2]

RATDIR=os.path.join(SOURCE,'ag-media')

def build_win(dir):
    os.system('devenv %s\rat\rat.2003.sln /rebuild Release' % (dir,))
    os.system('devenv %s\rat\rat.sln /rebuild Release /project rat-kill' % (dir,))
    
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
        copyCmd = '%s %s %s' % (copyExe,f,DEST)
        os.system(copyCmd)
else:
    print '** Error : rat files do not exist; not copying'

