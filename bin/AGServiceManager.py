import sys
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

serviceManager = AGServiceManager()

port = 12000
if len(sys.argv) > 1:
    port = sys.argv[1]
server = Server( port, auth_callback=AuthCallback )
service = server.create_service_object("ServiceManager")
serviceManager._bind_to_service( service )
print "Starting service; URI: ", serviceManager.get_handle()
server.run()
