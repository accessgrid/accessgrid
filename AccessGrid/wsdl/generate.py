#!/usr/bin/python2
import os

dstPath = os.path.join("..", "cache")

if not os.path.exists(dstPath):
    os.mkdir(dstPath)

initFile = os.path.join(dstPath, "__init__.py")
if not os.path.exists(initFile):
    open(initFile, "w").close()

# FIXME: this call shouldn't need the server wsdl to create the AccessGrid_Types.py
command = "wsdl2py -f VenueServerBinding.wsdl -e -o %s -t AccessGrid_Types " % dstPath
print "* ", command
os.system(command)

command = "wsdl2py -f VenueServerBinding.wsdl -e -o %s -t AG_VenueServer_Types " % dstPath
print "* ", command
os.system(command)
command = "wsdl2dispatch -f VenueServerBinding.wsdl -e -o %s -t AG_VenueServer_Types" % dstPath
print "* ", command
os.system(command)
command = "wsdl2py -f VenueBinding.wsdl -e -o %s -t AG_Venue_Types " % dstPath
print "* ", command
os.system(command)
command = "wsdl2dispatch -f VenueBinding.wsdl -e -o %s -t AG_Venue_Types" % dstPath
print "* ", command
os.system(command)

