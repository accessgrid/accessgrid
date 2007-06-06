#!/usr/bin/python
#
# Build ucl rat program and put them in the dist directory
#
import os
import sys

SOURCE=sys.argv[1]
DEST=sys.argv[2]

UCLDIR=os.path.join(SOURCE,'mmedia')

def build_win(dir):
    raise "no action defined"
    
def build_linux(dir):
    raise "no action defined"

def build_mac(dir):
    os.chdir(dir)
    # For now, look at mac build notes and build separately first.
    print "If ucl rat is not built, please build ucl rat separately before packaging."
    print "	See mac ag build doc for more information."
    #os.system('cd common; ./configure; make; cd ..')
    #os.system('cd tcl-8.0/unix; ./configure; make; cd ..')
    #os.system('cd tk-8.0/unix; ./configure; make; cd ..')
    #os.system('cd rat; ./configure; make')

# Set plat-specific bits
if sys.platform == 'darwin':
    dir = os.path.join(UCLDIR,'rat')
    uclRatFiles = [ os.path.join(dir,'rat'),
                 os.path.join(dir,'rat-4.4.00'),
                 os.path.join(dir,'rat-4.4.00-media'),
                 os.path.join(dir,'rat-4.4.00-ui'),
                 os.path.join(dir,'rat-4.4.00-kill') ]
    copyExe = 'cp -p'
    build = build_mac
else:
    raise Exception, 'Unsupported platform: ' + sys.platform
    

# Check whether we need to build
needBuild = 0
for f in uclRatFiles:
    if not os.path.exists(f):
        needBuild = 1
        break

# Build and copy if necessary
if needBuild:
    build(UCLDIR)

if os.path.exists(uclRatFiles[0]):
    for f in uclRatFiles:
        dest = DEST 
        if f.endswith('kill'):
            dest = os.path.join(DEST,'rat-kill')
        copyCmd = '%s %s %s' % (copyExe,f,dest)
        os.system(copyCmd)
else:
    print '** Error : ucl files do not exist; not copying'

