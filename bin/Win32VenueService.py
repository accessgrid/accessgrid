#-----------------------------------------------------------------------------
# Name:        Win32VenueService.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32VenueService.py,v 1.2 2003-03-14 14:51:22 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import win32serviceutil
import win32service
import win32event
import sys
import logging, logging.handlers

if sys.platform != "win32":
    print "This is a win32 service!"
    sys.exit(1)
    
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.pyGlobus.Server import Server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

class Win32NodeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AGNodeService"
    _svc_display_name_ = "Access Grid Node Service"
    _defaultPort = 11000

    def __init__(self,args):
        ntl = logging.handlers.NTEventLogHandler("AG VenueServer")
        self.log = logging.getLogger("AG.VenueServer")
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(ntl)
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.nodeService = AGNodeService()
        self.server = Server(self._defaultPort, auth_callback=AuthCallback)
        self.service = self.server.create_service_object("NodeService")
        self.nodeService._bind_to_service(self.service)
        self.log.info("Created VenueServer.")
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.server.stop()
        self.log.info("Stopped Venue Server.")
        
    def SvcDoRun(self):
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        self.server.run()
        self.log.info("Started Venue Server.")
        
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32NodeService)
