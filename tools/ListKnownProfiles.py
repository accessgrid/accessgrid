#!/usr/bin/python
#
#

import csv

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.ClientProfile import ClientProfileCache

app = CmdlineApplication()
app.Initialize("ListKnownProfiles")

cache = ClientProfileCache()

profiles = cache.loadAllProfiles()

def makeRow(p):
    d = dict()
    d['name'] = p.name
    d['email'] = p.email
    d['phone'] = p.phoneNumber
    d['location'] = p.location
    d['home venue'] = p.homeVenue
    return d

pKeys = ('name', 'email', 'phone', 'location', 'home venue')
outfile = csv.DictWriter(file("KnownUsers.csv", "w"), pKeys, lineterminator="\n")
for row in map(lambda p: makeRow(p), profiles):
    outfile.writerow(row)


