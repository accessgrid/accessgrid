import sys
import os
import zipfile

"""
Make Access Grid shared application packages
Looks in specified input directory for same-named .app and
implementation files, and zips them into the specified output
directory.
"""

def usage():
    print "Usage : ", sys.argv[0], " <appDir> <optionalOutputDir> "

if len(sys.argv) < 2:
    usage()

inputDir = sys.argv[1]
outputDir = sys.argv[1]

if len(sys.argv) == 3:
    outputDir = sys.argv[2]
elif len(sys.argv) > 3:
    usage()

absOutputDir = os.path.abspath(outputDir)
if not os.path.exists(absOutputDir):
    os.makedirs(absOutputDir)
    
things = ["SharedBrowser", "SharedPresentation", "VenueVNC"]
if not os.path.isdir(inputDir):
    print "The following directory does not exist: ", inputDir

for thing in things:
    os.chdir(os.path.join(inputDir, thing))
    
    Desc = thing + ".app"
    ImplPy = thing + ".py"

    if not os.path.isfile(Desc):
        continue
    
    # if associated file found, zip em up together in the outputDir
    zipFile = thing + ".shared_app_pkg"
    long_zipFile = os.path.join(absOutputDir, zipFile)
    print "Writing Package File:", long_zipFile
    zf = zipfile.ZipFile( long_zipFile, "w" )
    zf.write( Desc )
    # check for various implementations
    if os.path.isfile(ImplPy):
        zf.write(ImplPy)

    zf.close()

