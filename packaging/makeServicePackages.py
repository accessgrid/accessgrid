import sys
import os
import zipfile

"""
Make Access Grid service packages
Looks in specified input directory for same-named .svc and
implementation files, and zips them into the specified output
directory.
"""

def usage():
    print "Usage : ", sys.argv[0], " <sourceDir> <serviceDir> <optionalOutputDir> "

if len(sys.argv) < 3:
    usage()
    sys.exit(1)

sourceDir = sys.argv[1]
agSourceDir = sys.argv[2]

inputDir = os.path.join(agSourceDir,'services','node')
outputDir = inputDir

if len(sys.argv) == 4:
    outputDir = sys.argv[3]
elif len(sys.argv) > 4:
    usage()
    sys.exit(1)
    
absOutputDir = os.path.abspath(outputDir)
if not os.path.exists(absOutputDir):
    os.makedirs(absOutputDir)
    
services = ["AudioService", "VideoConsumerService", "VideoProducerService", "VideoService"]
if not os.path.isdir(inputDir):
    print "The following directory does not exist: ", inputDir

sdir = os.getcwd()

os.chdir(inputDir)

for service in services:

    servDesc = service + ".svc"
    servImplPy = service + ".py"
    serviceBuildPy = service + '.build.py'
    serviceManifest = service + '.manifest'

    if not os.path.isfile(servDesc):
        continue

    # Execute the service build script
    if os.path.isfile(serviceBuildPy):
        print 'Calling build script: ', serviceBuildPy
        buildCmd = '%s %s %s %s %s' % (sys.executable,
                                       serviceBuildPy,
                                       sourceDir,
                                       agSourceDir,
                                       outputDir)
        os.system(buildCmd)

    
    # if associated file found, zip em up together in the outputDir
    serviceZipFile = service + ".zip"
    long_serviceZipFile = os.path.join(absOutputDir, serviceZipFile)
    print "Writing Package File:", long_serviceZipFile
    zf = zipfile.ZipFile( long_serviceZipFile, "w" )
    zf.write( servDesc )
    # check for various implementations
    if os.path.isfile(servImplPy):
        zf.write(servImplPy)

    # Include files from manifest
    if os.path.isfile(serviceManifest):
    
        # Read the service files list
        f = open(serviceManifest,'r')
        fileList = f.readlines()
        f.close()
    
        for f in fileList:
            f = f.strip()
            if os.path.isfile(f):
                zf.write(f)

    zf.close()

os.chdir(sdir)
