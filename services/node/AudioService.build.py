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
elif sys.platform == 'linux2':
    ratFiles = [ 'rat',
                 'rat-4.2.22',
                 'rat-4.2.22-media',
                 'rat-4.2.22-ui',
                 'rat-kill' ]
    copyExe = 'cp'
else:
    print "** Error: Unsupported platform: " + sys.platform
    

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
os.chdir(servicesDir)
f = open('AudioService.manifest','w')
for filename in ratFiles:
    f.write(filename + "\n")
f.close()

