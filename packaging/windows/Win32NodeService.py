#-----------------------------------------------------------------------------
# Name:        Win32NodeService.py
# Purpose:     This service should run the Node Service as a windows service.
#              That means it can be automatically started and stopped at login
#              and logoff.
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32NodeService.py,v 1.1 2004-03-19 03:42:09 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import win32serviceutil
import win32service
import win32event
import sys
from AccessGrid import Log

if sys.platform != "win32":
    print "This is a win32 service!"
    sys.exit(1)
    
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.hosting.Server import SecureServer as Server

class Win32NodeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AGNodeService"
    _svc_display_name_ = "Access Grid Node Service"
    _defaultPort = 11000

    def __init__(self,args):
        # Initilialize Logging
        self.ntl = Log.handlers.NTEventLogHandler("AG Node Service")
        self.ntl.setLevel(Log.DEBUG)
        self.log = Log.GetLogger(Log.NodeService)
        Log.HandleLoggers(self.ntl, Log.GetDefaultLoggers())

        # Initialize Win32 Service stuff
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        # Make a node service
        self.nodeService = AGNodeService()

        # Make a hosting environment
        self.server = Server(self._defaultPort)

        # Make a node service service
        self.server.RegisterObject(self.nodeService, path='/NodeService')

        # Tell the world we're here
        self.log.info("Created Node Service.")

    def SvcStop(self):
        # Service status report
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Wait for a stop event
        win32event.SetEvent(self.hWaitStop)

        # Stop the server
        self.server.stop()

        # Tell the world
        self.log.info("Stopping Node Service.")

    def SvcDoRun(self):
        # Run the service
        self.server.run_in_thread()
        
        # Tell the world
        self.log.info("Starting service; URI: ", self.nodeService.get_handle())

        # Wait for a stop
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32NodeService)
