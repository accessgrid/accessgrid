#-----------------------------------------------------------------------------
# Name:        Win32NodeService.py
# Purpose:     This service should run the Node Service as a windows service.
#              That means it can be automatically started and stopped at login
#              and logoff.
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32NodeService.py,v 1.1 2003-02-27 20:15:50 judson Exp $
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

ntl = logging.handlers.NTEventLogHandler("AG Node Service")
logger = logging.getLogger("AG.NodeService")
logger.setLevel(logging.DEBUG)
logger.addHandler(ntl)

class Win32NodeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AGNodeService"
    _svc_display_name_ = "Access Grid Node Service"
    _defaultPort = 11000
    _ickyPathMunge = 'C:\Software\AccessGrid;C:\Software\globus\python'
    def __init__(self,args):
        sys.path.append(self._ickyPathMunge)
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.nodeService = AGNodeService()
        self.server = Server(self._defaultPort, auth_callback=AuthCallback)
        self.service = self.server.create_service_object("NodeService")
        self.nodeService._bind_to_service(self.service)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.server.stop()

    def SvcDoRun(self):
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        log.info("Starting service; URI: ", self.nodeService.get_handle())
        self.server.run_in_thread()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32NodeService)
