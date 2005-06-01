#!/usr/bin/python
import os, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  default=False, help="Run with minimal output.")
options, args = parser.parse_args()

if sys.platform == "win32":
    w2pyExec = "python %s " % os.path.join(sys.prefix, "Scripts", "wsdl2py")
    w2dExec = "python %s " %  os.path.join(sys.prefix, "Scripts", "wsdl2dispatch")
    os.chdir( os.path.join("..", "AccessGrid", "wsdl") )
    dstPath = os.path.join("..", "interfaces")
    srcPath = "."
elif sys.platform=="darwin":
    dstPath = os.path.join("..", "AccessGrid", "interfaces")
    srcPath = os.path.join("..", "AccessGrid", "wsdl")
    w2pyExec = "/System/Library/Frameworks/Python.framework/Versions/Current/bin/wsdl2py"
    w2dExec = "/System/Library/Frameworks/Python.framework/Versions/Current/bin/wsdl2dispatch"
else:
    dstPath = os.path.join("..", "AccessGrid", "interfaces")
    srcPath = os.path.join("..", "AccessGrid", "wsdl")
    w2pyExec = "wsdl2py"
    w2dExec = "wsdl2dispatch"

if not os.path.exists(dstPath):
    os.mkdir(dstPath)

initFile = os.path.join(dstPath, "__init__.py")
if not os.path.exists(initFile):
    open(initFile, "w").close()

# FIXME: this call shouldn't need the server wsdl to create the AccessGrid_Types.py
command = w2pyExec + " -f %s -e -o %s -t AccessGrid_Types --simple-naming -m AccessGrid.wsdl.SchemaToPyTypeMap" % ( os.path.join(srcPath, "VenueServerBinding.wsdl"), dstPath)
if not options.quiet:
    print "* ", command
os.system(command)

wsdlList =  [
            [ 'AG_VenueServer_Types' , 'VenueServerBinding.wsdl' ],
            [ 'AG_Venue_Types', 'VenueBinding.wsdl' ],
            [ 'AG_ServiceManager_Types', 'AGServiceManagerBinding.wsdl' ],
            [ 'AG_NodeService_Types', 'AGNodeServiceBinding.wsdl' ],
            [ 'AG_Service_Types', 'AGServiceBinding.wsdl' ],
            [ 'AG_SharedApplication_Types', 'SharedApplicationBinding.wsdl' ],
            ]



def Generate(typesModule,wsdlFile,dstPath):
    command = w2pyExec + " -f %s -e -o %s -t %s --simple-naming --clientClassSuffix=IW -m AccessGrid.wsdl.SchemaToPyTypeMap" % ( wsdlFile,
                    dstPath,
                    typesMod)
    if not options.quiet:
        print "* ", command
    os.system(command)
    
    command = w2dExec + " -f %s -e -o %s -t %s --simple-naming " %  ( wsdlFile, dstPath,typesMod)
    if not options.quiet:
        print "* ", command
    os.system(command)


for typesMod,wsdlFile in wsdlList:
    Generate(typesMod,os.path.join(srcPath,wsdlFile),dstPath)
