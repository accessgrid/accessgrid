#!/usr/bin/python2
#
#  Build Vic
#

import os
import sys

SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]

VICDIR = os.path.join(SOURCE,'ag-media')


def build_win(dir):
    os.system('devenv %s\vic\vic.2003.sln /rebuild "DDraw Release"' % (dir,))
    
def build_linux(dir):
    os.chdir(dir)
    os.system('./vic-build')


# Set plat-specific bits
if sys.platform == 'win32':
    VIC_EXE = os.path.join(VICDIR,'vic','DDraw_release','vic.exe')
    copyExe = 'copy'
    build = build_win
elif sys.platform == 'linux2':
    VIC_EXE = os.path.join(VICDIR,'vic','vic')
    copyExe = 'cp'
    build = build_linux
else:
    raise Exception, 'Unsupported platform: ' + sys.platform
    
    
# Build if necessary
if not os.path.exists(VIC_EXE):
    build(VICDIR)

    if os.path.exists(VIC_EXE):
        copyCmd = "%s %s %s" % (copyExe, VIC_EXE, DEST)
        os.system(copyCmd)
    else:
        print '** Error : %s does not exist; not copying' % (VIC_EXE,)


