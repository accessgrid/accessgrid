import sys, os, re
import shutil
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
    
if not os.path.isdir(inputDir):
    print "The following directory does not exist: ", inputDir
    sys.exit(-1)
else:
    things = os.listdir(inputDir)

for thing in things:
    Desc = None
    adir = os.path.join(inputDir, thing)
    os.chdir(adir)

    files = os.listdir(adir)
    
    appfilter = re.compile(".*app", re.IGNORECASE)

    files = filter(appfilter.search, files)

    if len(files) == 0 or len(files) > 1:
        print "bad shared app: %s, wrong number of .app files (%s)" % (thing,
                                                                       files)
        print "trying to use the one named after the directory."

        for f in files:
            if f.split('.')[0] == thing:
                Desc = f
                ImplPy = thing + ".py"

        if Desc is None:
            continue
    else:
        Desc = files[0]
        ImplPy = Desc.split('.')[0] + ".py"

    if not os.path.isfile(Desc):
        continue

    # if associated file found, zip em up together in the outputDir
    zipFile = thing + ".zip"
    long_zipFile = os.path.join(absOutputDir, zipFile)
    print "Writing Package File:", long_zipFile
    zf = zipfile.ZipFile( long_zipFile, "w" )
    zf.write( Desc )
    # check for various implementations
    if os.path.isfile(ImplPy):
        zf.write(ImplPy)

    zf.close()

    # Copy to app package file name
    shutil.copyfile(long_zipFile, long_zipFile.replace("zip", "agpkg"))

