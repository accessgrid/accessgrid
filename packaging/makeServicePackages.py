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

for service in services:

    servDesc = os.path.join(inputDir, service) + ".svc"
    servImplPy = os.path.join(inputDir, service) + ".py"
    servImplWin = os.path.join(inputDir, service) + ".exe"
    servImplLin = os.path.join(inputDir, service)

    if not os.path.isfile(servDesc):
        continue
    
    # if associated file found, zip em up together in the outputDir
    serviceZipFile = os.path.join(outputDir, service) + ".zip"
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

