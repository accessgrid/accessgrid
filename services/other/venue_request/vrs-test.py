#!/usr/bin/python2
#
#

import sys
import xmlrpclib
import string

f = open("vrs-test.in", "r")
names = map(lambda x: x[:-1], f.readlines())
vrsP = xmlrpclib.ServerProxy("http://ivs.mcs.anl.gov:6100")

count = 0
for n in names:
    vName = "Test Venue %d" % count
    vDesc = "Test Descripion %d" % count
    vEmail = "Test email %d" % count
    vUrl = "http://%s/" % ".".join(string.lower(n).strip('.').split(".")[1:])
    
    print "Requesting: "
    print "name: ", vName
    print "desc: ", vDesc
    print "email: ", vEmail
    print "url: ", vUrl
    
    (ret, ext) = vrsP.RequestVenue(vName, vDesc, vEmail, vUrl)
    if ret:
        print "Created venue at: ", ext
    else:
        print "Failed to create venue, reason: ", ext
    
    count = count + 1
