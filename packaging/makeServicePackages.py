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
    print "Usage : ", sys.argv[0], " <serviceDir> <optionalOutputDir> "

if len(sys.argv) < 2:
    usage()

inputDir = sys.argv[1]
outputDir = sys.argv[1]

if len(sys.argv) == 3:
    outputDir = sys.argv[2]
elif len(sys.argv) > 3:
    usage()

services = ["AudioService", "VideoConsumerService", "VideoProducerService"]
if not os.path.isdir(inputDir):
    print "The following directory does not exist: ", inputDir

os.chdir(inputDir)

for service in services:

    servDesc = service + ".svc"
    servImplPy = service + ".py"
    servImplWin = service + ".exe"
    servImplLin = service

    if not os.path.isfile(servDesc):
        continue
    
    # if associated file found, zip em up together in the outputDir
    serviceZipFile = service + ".zip"
    long_serviceZipFile = os.path.join(outputDir, serviceZipFile)
    print "Writing Package File:", long_serviceZipFile
    zf = zipfile.ZipFile( long_serviceZipFile, "w" )
    zf.write( servDesc )
    # check for various implementations
    if os.path.isfile(servImplPy):
        zf.write(servImplPy)

    if os.path.isfile(servImplWin):
        zf.write(servImplWin)

    if os.path.isfile(servImplLin):
        zf.write(servImplLin)

    zf.close()

