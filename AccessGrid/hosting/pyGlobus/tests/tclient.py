from AccessGrid.hosting.pyGlobus import Client
import sys
import os

def cb(server, g_handle, remote_user, context):
    print "got callback"
    return 1


import time
gt = time.time

h = Client.Handle('https://localhost:8000/100', authCallback = None)

n = 1

t1 = gt()

ret = None

alen = 50
a = []
for i in range(alen):
    a.append(i)

for n in range(100):
    try:
#	print n
        ret = h.get_proxy().method(a)
    except Client.FaultType, f:
        print "call raised fault ", f
        print "faultcode='%s'" % (f.faultcode)
        print "string='%s'" % ( f.faultstring)
        print "detail='%s'" % (f.detail)

t2 = gt()
print "t1=%s t2=%s" % (t1, t2)
print "dur =", t2 - t1
print "avg=", (t2 - t1) / n

