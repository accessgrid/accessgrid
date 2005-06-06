#!/usr/bin/python2
import sys
import os
import zipfile
import re
from optparse import OptionParser

"""
Make Access Grid service packages
Looks in specified input directory for same-named .svc and
implementation files, and zips them into the specified output
directory.
"""

#
# Parse command line options
#

parser = OptionParser()
parser.add_option("--sourcedir", dest="sourcedir", metavar="SOURCEDIR",
                  default=None,
                  help="Directory in which needed source (ag-media, etc) is located")
parser.add_option("--agsourcedir", dest="agsourcedir", metavar="AGSOURCEDIR",
                  default=None,
                  help="Directory in which the AG source code is located")
parser.add_option("--outputdir", dest="outputdir", metavar="OUTPUTDIR",
                  default=None,
                  help="Directory in which the AG source code is located")
parser.add_option("--servicefile", dest="servicefile", metavar="SERVICEFILE",
                  default=None,
                  help="File containing list of services to build")
options, args = parser.parse_args()


sourceDir = options.sourcedir
agSourceDir = options.agsourcedir

inputDir = os.path.join(agSourceDir,'services','node')
if options.outputdir:
    outputDir = options.outputdir
else:
    outputDir = inputDir
    
absOutputDir = os.path.abspath(outputDir)
if not os.path.exists(absOutputDir):
    os.makedirs(absOutputDir)
    

# Bail if input dir does not exist
if not os.path.isdir(inputDir):
    print "The input directory does not exist: ", inputDir
    sys.exit(1)

# Determine services to build
if options.servicefile:
    # Build services identified in service file
    f = file(options.servicefile,'r')
    services = map( lambda x: x.strip(), f.readlines())
    f.close()
else:
    # Build all services in input directory
    svcexp = re.compile(".*svc$", re.IGNORECASE)
    services = map(lambda x: os.path.splitext(x)[0],
                   filter(svcexp.search, os.listdir(inputDir)))
    dirlist = os.listdir(inputDir)
    services = []
    for dir in dirlist:
        thisdir = os.path.join(inputDir,dir)
        if os.path.isdir(thisdir):
            thisServiceList = map(lambda x: os.path.splitext(x)[0],
                           filter(svcexp.search, os.listdir(thisdir)))
            if thisServiceList:
                services += thisServiceList
        
    

sdir = os.getcwd()
os.chdir(inputDir)

print "Building services:", services

for service in services:
    
    
    # Get in the right directory
    os.chdir(os.path.join(inputDir,service))
    
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

# Change back to the original dir
os.chdir(sdir)
