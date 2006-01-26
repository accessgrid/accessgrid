#!/usr/bin/python
#
#  Build Vic
#

import os
import sys

SOURCE=sys.argv[1]
DEST=sys.argv[2]

TARGETDIR = os.path.join(SOURCE,'common')


def build_win(dir):
    p = os.path.join(dir, "common.2003.sln")
    os.system('devenv %s /rebuild "Release"' % (p,))
    
def build_linux(dir):
    os.chdir(dir)
    os.system('./configure; make')

# Set plat-specific bits
if sys.platform == 'win32':
    TARGET = os.path.join(TARGETDIR,'src','Release','uclmm.lib')
    copyExe = 'copy'
    build = build_win
elif sys.platform in ['linux2','darwin','freebsd5']:
    TARGET = os.path.join(TARGETDIR,'src','libuclmmbase.a')
    copyExe = 'cp -p'
    build = build_linux
else:
    raise Exception, 'Unsupported platform: ' + sys.platform
    
# Build if necessary
if not os.path.exists(TARGET):
   build(TARGETDIR)

if os.path.exists(TARGET):
    copyCmd = "%s %s %s" % (copyExe, TARGET, DEST)
    os.system(copyCmd)
else:
    print '** Error : %s does not exist; not copying' % (TARGET,)


