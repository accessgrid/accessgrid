import sys
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

serviceManager = AGServiceManager()
server = Server( int(sys.argv[1]), auth_callback=AuthCallback )
service = server.create_service_object("ServiceManager")
serviceManager._bind_to_service( service )
print "Starting service; URI: ", serviceManager.get_handle()
server.run()
