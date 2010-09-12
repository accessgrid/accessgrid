#!/usr/bin/python
#
# Avahi's d-bus glib main loop interferes with the AG3 VenueClient's
# so this application is called from ServiceDiscovery.py using
# subprocess.Popen to discover when AG3 ZeroConf services are added and
# removed.
#

import sys, getopt

try:
    import avahi, gobject, dbus
except ImportError:
    print "Sorry, to use this tool you need to install Avahi, pygtk and python-dbus."
    sys.exit(1)

try:
    import dbus.glib
except ImportError, e:
    pass


def usage(retval = 0):
    print "%s [options] <type>\n" % sys.argv[0]
    print "   -h --help      Show this help"
    print "   -t --time      timeout duration in milliseconds before quitting"
    sys.exit(retval)

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:", ["help", "time="])
except getopt.GetoptError:
    usage(2)

timeout = 0

for o, a in opts:
    if o in ("-h", "--help"):
        usage()

    if o in ("-t", "--time"):
        timeout = int(a)

if len(args) < 1:
    usage(2)

stype = args[0]


def NewServiceCallback(interface, protocol, serviceName, regtype, replyDomain, flags):
    global server

    # Get service info and print url in TXT record
    interface, protocol, serviceName, regtype, replyDomain, \
    host, aprotocol, address, port, txtRecord, flags = \
    server.ResolveService(int(interface),
                          int(protocol),
                          serviceName,
                          regtype,
                          replyDomain,
                          avahi.PROTO_UNSPEC,
                          dbus.UInt32(0))

    parts = avahi.txt_array_to_string_array(txtRecord)
    
    for txt in parts:
        txtparts = txt.split('=')
        url = ''
        if txtparts and len(txtparts) > 1 and txtparts[0] == 'url':
            url = txtparts[1]
            print "+%s=%s" % (serviceName, url)
            try:
                sys.stdout.flush() # avoids blocking in ServiceDiscovery.py
            except IOError, e:
                pass

def RemoveServiceCallback(interface, protocol, serviceName, regtype, replyDomain, flags):
    print "-%s" % serviceName
    try:
        sys.stdout.flush() # avoids blocking in ServiceDiscovery.py
    except IOError, e:
        pass

def QuitCallback():
    global mainloop

    print "QuitCallback"
    mainloop.quit();

bus = dbus.SystemBus()
remote_object = bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER)
server  = dbus.Interface(remote_object, avahi.DBUS_INTERFACE_SERVER)

browser = dbus.Interface(bus.get_object(avahi.DBUS_NAME, server.ServiceBrowserNew(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC, stype, 'local.', dbus.UInt32(0))), avahi.DBUS_INTERFACE_SERVICE_BROWSER)

browser.connect_to_signal('ItemNew', NewServiceCallback)
browser.connect_to_signal('ItemRemove', RemoveServiceCallback)

if timeout > 0 :
    gobject.timeout_add(timeout, QuitCallback)

mainloop = gobject.MainLoop()
mainloop.run()

