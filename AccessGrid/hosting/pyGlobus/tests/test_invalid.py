from AccessGrid.hosting.pyGlobus import Client
import os

def try_url(url):

    print "test ", url

    h = Client.Handle(url)

    ret = h.IsValid()
    print "IsValid %s returns '%s'" % (url, ret)

    ret = h.Implements("method")
    print "Implements 'method' returns %s" % (ret)

    ret = h.Implements("methodX")
    print "Implements 'methodX' returns %s" % (ret)
    
    print ""

try_url('https://localhost:8000/100')
try_url('https://localhost:8000/101')
try_url('https://localhost:8001/100')

