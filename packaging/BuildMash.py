#!/usr/bin/python
#
# Build openmash programs and stick them in the dist directory
#
import os
import sys

SOURCE=sys.argv[1]
DEST=sys.argv[2]

OMDIR=os.path.join(SOURCE,'mash-code')

def build_win(dir):
    raise "no action defined"
    
def build_linux(dir):
    raise "no action defined"

def build_mac(dir):
    os.chdir(dir)
    os.system('./build mash vic')

# Set plat-specific bits
if sys.platform == 'darwin':
    dir = os.path.join(OMDIR,'mash','bin')
    omFiles = [ os.path.join(dir,'mash-5.3beta2'),
                 os.path.join(dir,'mash'),
                 os.path.join(dir,'vic') ]
    copyExe = 'cp -p'
    build = build_mac
else:
    raise Exception, 'Unsupported platform: ' + sys.platform
    

# Check whether we need to build
needBuild = 0
for f in omFiles:
    if not os.path.exists(f):
        needBuild = 1
        break

# Build and copy if necessary
if needBuild:
    build(OMDIR)

if os.path.exists(omFiles[0]):
    for f in omFiles:
        dest = DEST 
        copyCmd = '%s %s %s' % (copyExe,f,dest)
        os.system(copyCmd)
else:
    print '** Error : openmash files do not exist; not copying'

