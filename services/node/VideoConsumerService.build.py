#!/usr/bin/python2
#
# Build vic and copy it to the local dir
#

import sys, os

SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]

servicesDir = os.path.join(AGDIR,'services','node')

# Identify platform and set plat-specific bits
if sys.platform == 'win32':
    VIC_EXE = 'vic.exe'
    copyExe = 'copy'
elif sys.platform == 'linux2':
    VIC_EXE = 'vic'
    copyExe = 'cp'
else:
    print "** Error: Unsupported platform: " + sys.platform
    

# Build vic if necessary
VIC_EXE_PATH = os.path.join(DEST,VIC_EXE)

# Build vic if necessary
if not os.path.exists(VIC_EXE_PATH):
    # Build vic
    buildCmd = '%s %s %s %s' % (sys.executable,
                                os.path.join(AGDIR,'packaging','BuildVic.py'),
                                SOURCE, DEST)
    os.system(buildCmd)


# Copy the vic executable    
if os.path.exists(VIC_EXE_PATH):
    print 'Copying %s' % (VIC_EXE_PATH)
    copyCmd = "%s %s %s" % (copyExe,VIC_EXE_PATH,
                            servicesDir)
    os.system(copyCmd)
else:
    print "** Error: %s does not exist, not copying" % (VIC_EXE_PATH)

# Write the service manifest
os.chdir(servicesDir)
f = open('VideoConsumerService.manifest','w')
f.write(VIC_EXE + '\n')
f.close()


