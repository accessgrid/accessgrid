import sys
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server

nodeService = AGNodeService()

# start the service
server = Server( int( sys.argv[1] ) )
service = server.create_service_object("NodeService")
nodeService._bind_to_service( service )
print "Starting service; URI: ", nodeService.get_handle()
server.run()


