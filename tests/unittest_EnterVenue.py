#-----------------------------------------------------------------------------
# Name:        unittest_ftps.py
# Purpose:     
#
# Author:      Tom Uram
#   
# Created:     2003/05/14
# RCS-ID:      $Id: unittest_EnterVenue.py,v 1.1 2005-12-05 17:31:01 turam Exp $
# Copyright:   (c) 2005
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import unittest


import time
import shutil
import os
import sys
import socket
import stat
import threading
import signal 

from AccessGrid.interfaces.VenueServer_client import VenueServerIW

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.VenueClient import VenueClient
from AccessGrid.VenueClientController import VenueClientController
from AccessGrid.ClientProfile import ClientProfile


#  start server
host = socket.gethostbyname(socket.gethostname())
port = 8000
serverUrl = 'https://%s:%d/VenueServer' % (host,port)
venueUrl = 'https://%s:%d/Venues/default' % (host,port)

pid = None
def StartProcess():
    global host,path,serverUrl,pid

    pid= os.spawnv(os.P_NOWAIT,
                   sys.executable,
                   [sys.executable,
                   '../bin/VenueServer.py'])

def StopProcess():
    global pid
    if pid:
        print 'killing pid', pid
        os.kill(pid,signal.SIGKILL)

threading.Thread(target=StartProcess,name='StartProcess').start()
print 'serverUrl = ', serverUrl
venueServer = VenueServerIW(serverUrl)
while 1:
    try:
        venueList = venueServer.GetVenues()
        #print 'got venue list:', venueList
        break
    except Exception,e:
        print 'exception',e
    time.sleep(1)
    




class TestCase(unittest.TestCase):
    def __init__(self,*args):
    
        unittest.TestCase.__init__(self,*args)
        

    def test1_Enter(self):
        vc.EnterVenue(venueUrl)
        print '* venue state'
        print 'clients:', vc.venueState.clients
        print 'data:', vc.venueState.data
        print 'services:', vc.venueState.services
        print 'applications:', vc.venueState.applications
        print 'connections:', vc.venueState.connections
        print 'dataLocation:',vc.venueState.dataLocation
        print 'eventLocation:', vc.venueState.eventLocation
        print 'textLocation:', vc.venueState.textLocation
        
    def test2_Exit(self):
        stuff = vc.ExitVenue()
        

        
    def test99KillServer(self):
        try: StopProcess()
        except: pass
        vc.Shutdown()
        while 0:
            tl = threading.enumerate()
            for t in tl:
                print t
            time.sleep(1)
            


def suite():
    """Returns a suite containing all the test cases in this module."""
    suite1 = unittest.makeSuite(TestCase)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    app = CmdlineApplication()
    app.Initialize('qwe')
    vc = VenueClient(app=app)
    vcc = VenueClientController()
    vcc.SetVenueClient(vc)

    # When this module is executed from the command-line, run the test suite
    unittest.main(defaultTest='suite')

