#-----------------------------------------------------------------------------
# Name:        Win32ServiceManager.py
# Purpose:     This service should run the Service Manager as a windows 
#              service. That means it can be automatically started and stopped 
#              at login and logoff.
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32ServiceManager.py,v 1.2 2003-03-14 14:51:22 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import win32serviceutil
import win32service
import win32event
import logging, logging.handlers

from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.hosting.pyGlobus.Server import Server

def AuthCallback(server, g_handle, remote_user, context):
    return 1

class Win32ServiceManager(win32serviceutil.ServiceFramework):
    _svc_name_ = "AGServiceManager"
    _svc_display_name_ = "Access Grid Service Manager"
    defaultPort = 12000
    def __init__(self,args):
        ntl = logging.handlers.NTEventLogHandler("AG Node Service Manager")
        self.log = logging.getLogger("AG.ServiceManager")
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(ntl)
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.serviceManager = AGServiceManager()
        self.server = Server(self.defaultPort, auth_callback=AuthCallback)
        self.service = self.server.create_service_object("ServiceManager")
        self.serviceManager._bind_to_service(self.service)
        self.log.info("Created Service Manager.")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.server.stop()
        self.log.info("Stopped Service Manager.")

    def SvcDoRun(self):
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        self.server.run_in_thread()
        self.log.info("Started Service Manager.")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32ServiceManager)
