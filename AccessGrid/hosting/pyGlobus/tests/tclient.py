import Client
import os

def cb(server, g_handle, remote_user, context):
    print "got callback"
    return 1


import time
gt = time.time

#h = Client.Handle('https://localhost:8000/Foobar/Baz')
h = Client.Handle('https://localhost:8000/100', authCallback = cb)

n = 1

t1 = gt()

ret = None

try:
    ret = h.get_proxy().method(3)
except Client.FaultType, f:
    print "call raised fault ", f, dir(f)
    print "faultcode='%s'" % (f.faultcode)
    print "string='%s'" % ( f.faultstring)

else:
    t2 = gt()
    print "t1=%s t2=%s" % (t1, t2)
    print "dur =", t2 - t1
    print "avg=", (t2 - t1) / n

    print "Got '%s' '%s' from method"  % (ret, map(lambda x: str(x), ret))
