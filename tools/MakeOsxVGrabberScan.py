#!/usr/bin/python
#
# This script builds osx-vgrabber-scan.
#
import os, sys, shutil

if len(sys.argv) > 1:
    dstPath = sys.argv[1]
else:
    dstPath = None

cmd = 'gcc -framework Carbon -framework QuickTime osx-vgrabber-scan.c -o osx-vgrabber-scan'
print cmd
os.system(cmd)

if dstPath != None:
    shutil.copy2('osx-vgrabber-scan', dstPath)  

