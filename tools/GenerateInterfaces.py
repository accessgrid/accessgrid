#!/usr/bin/python2
import os, sys

if sys.platform == "win32":
    w2pyExec = "python %s " % os.path.join(sys.prefix, "Scripts", "wsdl2py")
    w2dExec = "python %s " %  os.path.join(sys.prefix, "Scripts", "wsdl2dispatch")
    os.chdir( os.path.join("..", "AccessGrid", "wsdl") )
    dstPath = os.path.join("..", "interfaces")
    srcPath = "."
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
print "* ", command
os.system(command)

wsdlList =  [
            [ 'AG_VenueServer_Types' , 'VenueServerBinding.wsdl' ],
            [ 'AG_Venue_Types', 'VenueBinding.wsdl' ],
            [ 'AG_ServiceManager_Types', 'ServiceManagerBinding.wsdl' ],
            ]



def Generate(typesModule,wsdlFile,dstPath):
    command = w2pyExec + " -f %s -e -o %s -t %s --simple-naming --clientClassSuffix=IW -m AccessGrid.wsdl.SchemaToPyTypeMap" % ( wsdlFile,
                    dstPath,
                    typesMod)
    print "* ", command
    os.system(command)
    
    command = w2dExec + " -f %s -e -o %s -t %s --simple-naming " %  ( wsdlFile, dstPath,typesMod)
    print "* ", command
    os.system(command)


for typesMod,wsdlFile in wsdlList:
    Generate(typesMod,os.path.join(srcPath,wsdlFile),dstPath)
