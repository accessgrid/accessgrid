import sys
import os
import zipfile

"""
Make Access Grid service packages
Looks in specified input directory for same-named .svc and
implementation files, and zips them into the specified output
directory.
"""

if len(sys.argv) < 2:
    print "Usage : ", sys.argv[0], " <serviceDir>"

inputDir = sys.argv[1]
outputDir = sys.argv[1]

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
    print "Writing Package File:", serviceZipFile
    zf = zipfile.ZipFile( serviceZipFile, "w" )
    zf.write( servDesc )
    # check for various implementations
    if os.path.isfile(servImplPy):
        zf.write(servImplPy)

    if os.path.isfile(servImplWin):
        zf.write(servImplWin)

    if os.path.isfile(servImplLin):
        zf.write(servImplLin)

    zf.close()

