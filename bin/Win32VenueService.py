#-----------------------------------------------------------------------------
# Name:        Win32VenueService.py
# Purpose:
#
# Author:      Ivan R. Judson
#
# Created:     2003/02/02
# RCS-ID:      $Id: Win32VenueService.py,v 1.3 2004-02-24 21:21:48 judson Exp $
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
    
from AccessGrid.VenueServer import VenueServer
from AccessGrid.hosting.Server import SecureServer as Server

class Win32NodeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AGNodeService"
    _svc_display_name_ = "Access Grid Virtual Venue Service"
    _defaultPort = 8000

    def __init__(self,args):
        # Initialize Logging
        ntl = logging.handlers.NTEventLogHandler("AG VenueServer")
        self.log = logging.getLogger("AG.VenueServer")
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(ntl)
        
        # Initialize Win32 Service stuff
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        # Make a hosting environment
        self.server = Server(self._defaultPort)

        # Make a venue server
        self.venueService = VenueServer(self.server)

        # Make a Service Manager Service
        self.server.RegisterObject(self.venueService, path='/VenueServer')

        # tell the world we are here
        self.log.info("Created VenueServer.")
        
    def SvcStop(self):
        # Service status report
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Wait for a stop event
        win32event.SetEvent(self.hWaitStop)

        # Stop the server
        self.server.stop()

        # Tell the world
        self.log.info("Stopped Venue Server.")
        
    def SvcDoRun(self):
        # Run the service
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

        # Tell the world
        self.server.run()

        # Wait for a stop
        self.log.info("Started Venue Server.")
        
if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Win32NodeService)
