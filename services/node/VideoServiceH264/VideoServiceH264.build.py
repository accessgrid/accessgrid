#!/usr/bin/python2
#
# Build vic and copy it to the local dir
#

import sys, os

SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]

# choices: ["openmash", "vic"]
executableToBuild = "vic"

servicesDir = os.path.join(AGDIR,'services','node')

# Identify platform and set plat-specific bits
if sys.platform == 'win32':
    VIC_EXE = 'vic.exe'
    vicFiles = [VIC_EXE]
    copyExe = 'copy'
elif sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    VIC_EXE = 'vic'
    vicFiles = [VIC_EXE]
    copyExe = 'cp'
elif sys.platform == 'darwin':
    if executableToBuild == "vic":
        VIC_EXE = 'vic'
        vicFiles = [VIC_EXE]
        copyExe = 'cp -p'
    elif executableToBuild == "openmash":
        VIC_EXE = 'vic'
        vicFiles = [VIC_EXE, 'mash', 'mash-5.3beta2']
        copyExe = 'cp -p'
else:
    print "** Error: Unsupported platform: " + sys.platform
    

VIC_EXE_PATH = os.path.join(servicesDir,VIC_EXE)

# Build vic if necessary
needBuild = 0
for f in vicFiles:
    if not os.path.exists(os.path.join(servicesDir,f)):
        needBuild = 1
        break

if needBuild:
    # Build vic
    if executableToBuild == "openmash":
        buildCmd = '%s %s %s %s' % (sys.executable,
                                os.path.join(AGDIR,'packaging','BuildMash.py'),
                                SOURCE, servicesDir)
    else:
        buildCmd = '%s %s %s %s' % (sys.executable,
                                os.path.join(AGDIR,'packaging','BuildVic.py'),
                                SOURCE, servicesDir)
    os.system(buildCmd)

# Write the service manifest
f = open('VideoServiceH264.manifest','w')
f.write(VIC_EXE + '\n')
f.close()


