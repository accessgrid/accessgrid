import Client

#h = Client.Handle('https://localhost:8000/Foobar/Baz')
h = Client.Handle('https://localhost:8000/100')

ret = h.get_proxy().method(3)
print "Got '%s' from method"  % (map(lambda x: str(x), ret))
