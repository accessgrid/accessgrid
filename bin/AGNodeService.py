import sys
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server


def AuthCallback(server, g_handle, remote_user, context):
    return 1

nodeService = AGNodeService()

# start the service
server = Server( int( sys.argv[1] ) , auth_callback=AuthCallback )
service = server.create_service_object("NodeService")
nodeService._bind_to_service( service )
print "Starting service; URI: ", nodeService.get_handle()
server.run()


