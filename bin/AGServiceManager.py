#-----------------------------------------------------------------------------
# Name:        AGServiceManager.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGServiceManager.py,v 1.5 2003-02-10 14:49:02 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

serviceManager = AGServiceManager()

port = 12000
if len(sys.argv) > 1:
    port = int(sys.argv[1])
server = Server( port, auth_callback=AuthCallback )
service = server.create_service_object("ServiceManager")
serviceManager._bind_to_service( service )
print "Starting service; URI: ", serviceManager.get_handle()
server.run()
