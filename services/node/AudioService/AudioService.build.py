#!/usr/bin/python2
#
# Build rat and copy it to the local dir
#

import sys, os

SOURCE=sys.argv[1]
AGDIR=sys.argv[2]
DEST=sys.argv[3]

servicesDir = os.path.join(AGDIR,'services','node')

# Identify platform and set plat-specific bits
if sys.platform == 'win32':
    ratFiles = [ 'rat.exe',
                 'ratmedia.exe',
                 'ratui.exe',
                 'rat-kill.exe' ]
    copyExe = 'copy'
elif sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
    ratFiles = [ 'rat',
                 'rat-4.4.00',
                 'rat-4.4.00-media',
                 'rat-4.4.00-ui',
                 'rat-kill' ]
    copyExe = 'cp'
elif sys.platform == 'darwin':
    ratFiles = [ 'rat',
                 'rat-4.4.01',
                 'rat-4.4.01-media',
                 'rat-4.4.01-ui',
                 'rat-kill' ]
    copyExe = 'cp -p'
else:
    print "** Error: Unsupported platform by AudioService: " + sys.platform
    

# Check whether we need to build
needBuild = 0
for f in ratFiles:
    if not os.path.exists(os.path.join(servicesDir,f)):
        needBuild = 1
        break

# Build rat if necessary
if needBuild:
    print "source dist = ", SOURCE, DEST
    buildCmd = '%s %s %s %s' % (sys.executable,
                                os.path.join(AGDIR,'packaging','BuildRat.py'),
                                SOURCE, servicesDir)
    os.system(buildCmd)

# Write the service manifest
f = open('AudioService.manifest','w')
for filename in ratFiles:
    f.write(filename + "\n")
f.close()

