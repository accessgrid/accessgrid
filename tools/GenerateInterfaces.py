#!/usr/bin/python2
import os

dstPath = os.path.join("..", "AccessGrid", "interfaces")
srcPath = os.path.join("..", "AccessGrid", "wsdl")

if not os.path.exists(dstPath):
    os.mkdir(dstPath)

initFile = os.path.join(dstPath, "__init__.py")
if not os.path.exists(initFile):
    open(initFile, "w").close()

# FIXME: this call shouldn't need the server wsdl to create the AccessGrid_Types.py
command = "wsdl2py -f %s -e -o %s -t AccessGrid_Types --simple-naming -m AccessGrid.wsdl.SchemaToPyTypeMap" % ( os.path.join(srcPath, "VenueServerBinding.wsdl"), dstPath)
print "* ", command
os.system(command)

command = "wsdl2py -f %s -e -o %s -t AG_VenueServer_Types --simple-naming --clientClassSuffix=IW -m AccessGrid.wsdl.SchemaToPyTypeMap" % ( os.path.join(srcPath, "VenueServerBinding.wsdl"),dstPath)
print "* ", command
os.system(command)
command = "wsdl2dispatch -f %s -e -o %s -t AG_VenueServer_Types --simple-naming" %  ( os.path.join(srcPath, "VenueServerBinding.wsdl"), dstPath)
print "* ", command
os.system(command)
command = "wsdl2py -f %s -e -o %s -t AG_Venue_Types --simple-naming --clientClassSuffix=IW -m AccessGrid.wsdl.SchemaToPyTypeMap" %  ( os.path.join(srcPath, "VenueBinding.wsdl"), dstPath )
print "* ", command
os.system(command)
command = "wsdl2dispatch -f %s -e -o %s -t AG_Venue_Types --simple-naming" %   ( os.path.join(srcPath, "VenueBinding.wsdl"), dstPath )
print "* ", command
os.system(command)

