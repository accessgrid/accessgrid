#-----------------------------------------------------------------------------
# Name:        Win32ServiceManager.py
# Purpose:     This service should run the Service Manager as a windows 
#              service. That means it can be automatically started and stopped 
#              at login and logoff.
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32ServiceManager.py,v 1.3 2003-03-14 15:18:12 judson Exp $
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
        # Initialize Logging
        ntl = logging.handlers.NTEventLogHandler("AG Node Service Manager")
        self.log = logging.getLogger("AG.ServiceManager")
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(ntl)

        # Initialize Service
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        # Make a Service Manager
        self.serviceManager = AGServiceManager()
        
        # Make a hosting environment
        self.server = Server(self.defaultPort, auth_callback=AuthCallback)
        
        # Make a Service Manager Service
        self.service = self.server.CreateServiceObject("ServiceManager")
        self.serviceManager._bind_to_service(self.service)
        
        # tell the world we are here
        self.log.info("Created Service Manager.")

    def SvcStop(self):
        # Service status report
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Wait for a stop event
        win32event.SetEvent(self.hWaitStop)

        # Stop the server
        self.server.stop()

        # Tell the world
        self.log.info("Stopped Service Manager.")

    def SvcDoRun(self):
        # Run the service
        self.server.run_in_thread()
        
        # Tell the world
        self.log.info("Started Service Manager.")
        
        # Wait for a stop
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32ServiceManager)
