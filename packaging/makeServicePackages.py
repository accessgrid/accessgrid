import sys
import os
import zipfile

"""
Make Access Grid service packages
Looks in specified input directory for same-named .svc and
implementation files, and zips them into the specified output
directory.
"""

if len(sys.argv) < 3:
    print "Usage : ", sys.argv[0], " <inputDir> <outputDir>"

inputDir = sys.argv[1]
outputDir = sys.argv[2]

files = os.listdir( inputDir )
for file in files:

    # pull out service description files only
    if not file.endswith(".svc"):
        continue

    # look for associated service implementation file
    basename = file[:-4]
    fileFound = False
    implFile = None
    for f in files:
        if f == basename + ".py" or f == basename + ".exe" or f == basename:
            fileFound = True
            implFile = f

    # if associated file found, zip em up together in the outputDir
    if fileFound:
        serviceZipFile = outputDir + "/" + basename + ".zip"
        print "Writing Package File:", serviceZipFile
        zf = zipfile.ZipFile( serviceZipFile, "w" )
        zf.write( file )
        zf.write( implFile )
        zf.close()
    else:
        print "Service file found, but no implementation:", file
