import sys
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

serviceManager = AGServiceManager()
server = Server( int(sys.argv[1]) )
service = server.create_service_object("ServiceManager")
serviceManager._bind_to_service( service )
print "Starting service; URI: ", serviceManager.get_handle()
server.run()
