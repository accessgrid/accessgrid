#!/usr/bin/python
import os, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  default=False, help="Run with minimal output.")
parser.add_option("-m", "--with-modules", dest="modules", 
                  default=None, help="Generate interfaces for the specified comma-separated list of modules (only a subset of the Binding.wsdl name is required to match).")
options, args = parser.parse_args()

if sys.platform == "win32":
    w2pyExec = "%s %s " % (sys.executable, os.path.join(sys.prefix, "Scripts", "wsdl2py.py") )
    w2dExec = "%s %s " %  (sys.executable, os.path.join(sys.prefix, "Scripts", "wsdl2dispatch.py") )
    os.chdir( os.path.join("..", "AccessGrid", "wsdl") )
    dstPath = os.path.join("..", "interfaces")
    srcPath = "."
elif sys.platform=="darwin":
    dstPath = os.path.join("..", "AccessGrid", "interfaces")
    srcPath = os.path.join("..", "AccessGrid", "wsdl")
    w2pyExec = "%s %s" % (sys.executable,"/System/Library/Frameworks/Python.framework/Versions/Current/bin/wsdl2py")
    w2dExec = "%s %s" % (sys.executable,"/System/Library/Frameworks/Python.framework/Versions/Current/bin/wsdl2dispatch")
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
            [ 'AG_VenueClient_Types', 'VenueClientBinding.wsdl' ],
            [ 'AG_ServiceManager_Types', 'AGServiceManagerBinding.wsdl' ],
            [ 'AG_NodeService_Types', 'AGNodeServiceBinding.wsdl' ],
            [ 'AG_Service_Types', 'AGServiceBinding.wsdl' ],
            [ 'AG_NetworkService_Types', 'AGNetworkServiceBinding.wsdl' ],
            [ 'AG_SharedApplication_Types', 'SharedApplicationBinding.wsdl' ],
            [ 'AG_AuthorizationManager_Types', 'AuthorizationManagerBinding.wsdl' ],
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


if options.modules:
    targets = options.modules.split(',')
    subWsdlList = []
    for w in wsdlList:
        for t in targets:
            if w[1].find(t) >= 0:
                subWsdlList.append(w)
else:
    subWsdlList = wsdlList

for typesMod,wsdlFile in subWsdlList:
    Generate(typesMod,os.path.join(srcPath,wsdlFile),dstPath)
