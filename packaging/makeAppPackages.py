import sys, os, re
import string
import shutil
import zipfile
import ConfigParser

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

inputDir = os.path.abspath(sys.argv[1])
outputDir = inputDir

if len(sys.argv) == 3:
    outputDir = os.path.abspath(sys.argv[2])
elif len(sys.argv) > 3:
    usage()

if not os.path.exists(outputDir):
    os.makedirs(outputDir)
    
if not os.path.isdir(inputDir):
    print "The following directory does not exist: ", inputDir
    sys.exit(-1)
else:
    things = [d for d in os.listdir(inputDir) if os.path.isdir(os.path.join(inputDir, d))]
    print "THINGS: ", things
    
for thing in things:
    Desc = None
    adir = os.path.join(inputDir, thing)
    os.chdir(adir)

    files = filter(os.path.isfile, os.listdir('.'))
    print "FILES: ", files
    
    appfilter = re.compile(".*app", re.IGNORECASE)

    files = filter(appfilter.search, files)

    if len(files) == 0 or len(files) > 1:
        print "bad shared app: %s, wrong number of .app files (%s)" % (thing,
                                                                       files)
        print "trying to use the one named after the directory."

        for f in files:
            if f.split('.')[0] == thing:
                Desc = f
    else:
        Desc = files[0]

    if not os.path.isfile(Desc):
        print "Got bad description: %s" % Desc
        continue

    # read the .app file and get the file list from it
    af = ConfigParser.ConfigParser()
    af.read(Desc)
    flist = map(string.strip, af.get('application', 'files').split(','))
    print flist
    
    # if associated file found, zip em up together in the outputDir
    zipFile = thing + ".zip"
    long_zipFile = os.path.join(outputDir, zipFile)
    print "Writing Package File:", long_zipFile
    zf = zipfile.ZipFile( long_zipFile, "w" )
    zf.write( Desc )
    # check for various implementations
    for f in flist:
        print "Adding file: ", f
        zf.write(f)

    zf.close()

    # Copy to app package file name
    shutil.copyfile(long_zipFile, long_zipFile.replace("zip", "agpkg"))

