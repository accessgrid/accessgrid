#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        AGNodeService.py
# Purpose:     
#
# Author:      Thomas D. Uram
#
# Created:     2003/08/02
# RCS-ID:      $Id: AGNodeService.py,v 1.6 2003-02-10 15:22:15 leggett Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server


def AuthCallback(server, g_handle, remote_user, context):
    return 1

nodeService = AGNodeService()

# start the service
port = 11000
if len(sys.argv) > 1:
    port = int(sys.argv[1])
server = Server( port , auth_callback=AuthCallback )
service = server.create_service_object("NodeService")
nodeService._bind_to_service( service )
print "Starting service; URI: ", nodeService.get_handle()
server.run()

