import os
import sys
import logging
import base64

from AccessGrid.hosting import Client

from AccessGrid import Events
from AccessGrid import EventClient
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Platform import isWindows
from AccessGrid import DataStore
from AccessGrid import Platform
from AccessGrid.GUID import GUID

from AccessGrid.ClientProfile import ClientProfile


log = logging.getLogger("vncSharedAppClient")
def init_logging(appName):
    logger = logging.getLogger("AG")
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler()
    fmt = logging.Formatter("%(name)-17s %(asctime)s %(levelname)-5s %(message)s")
    hdlr.setFormatter(fmt)
    logger.addHandler(hdlr)

    appLogger = logging.getLogger(appName)
    appLogger.setLevel(logging.DEBUG)
    appLogger.addHandler(hdlr)

class vncSharedAppClient:
    """
    """
    def __init__( self, venueUrl ):

        self.venueUrl = venueUrl

        self.venueProxy = Client.SecureHandle(self.venueUrl).GetProxy()
        print( "Application URL: %s" %(self.venueUrl) )
        #print( "Application URL Valid? " + self.venueProxy.isValid( ) )
        # Join the application
        #  ** NEW METHOD **
        (self.publicId, self.privateId) = self.venueProxy.Join()
        #  ** OLD METHOD **
        #self.privateId=self.venueProxy.Join(ClientProfile('./profile'))

        #
        # Retrieve the channel id
        #
        (self.channelId, eventServiceLocation ) = self.venueProxy.GetDataChannel(self.privateId)

        # 
        # Subscribe to the event channel
        #
        #self.eventClient = EventClient.EventClient(eventServiceLocation, self.channelId)
        #self.eventClient.start()
        #self.eventClient.Send(Events.ConnectEvent(self.channelId))

        #
        # Register the 'view' event callback
        #
        # The callback function is invoked with one argument, the data from the call.
        #self.eventClient.RegisterCallback("view", self.ViewCallback )

        # Get the connection state and print it
        self.vncContact = self.venueProxy.GetData(self.privateId, "VNC_Contact");
        self.vncGeometry = self.venueProxy.GetData(self.privateId, "VNC_Geometry");
        self.vncDepth = self.venueProxy.GetData(self.privateId, "VNC_Depth");
        # Read password from app object
        encoded_pwd = self.venueProxy.GetData(self.privateId, "VNC_Pwd")

        print "VNC Server at %s (%s, %s-bits):"%(self.vncContact,self.vncGeometry,self.vncDepth);
        self.passwdFilename=os.path.join(UserConfig.instance().GetTempDir(), ("passwd-" + str(GUID()) + ".vnc"))
        # Write password to file so it can be passed to vnc.
        pwd_file = file(self.passwdFilename, 'wb')
        pwd_file.write(base64.decodestring(encoded_pwd))
        pwd_file.close()


        # Change to the location of the application before running, since helper executables are located here.
        location = UserConfig.instance().GetSharedAppDir()
        os.chdir(os.path.join(location, "VenueVNC")) 
        print "Running from directory", os.getcwd()

        if isWindows():
            width=eval(self.vncGeometry.split('x')[0]);
            if width >= 5120:
                execString='vncviewer -shared -scale 1/4 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            elif width >= 4096:
                execString='vncviewer -shared -scale 1/3 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            elif width >= 3072:
                execString='vncviewer -shared -scale 1/2 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            else:
                execString='vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)                
            print "About the execute: %s"%(execString)
            os.system(execString);
        else:
            execString='chmod +x ./vncviewer; ./vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)
            #print "About the execute: %s"%(execString)
            os.system(execString);

        os.unlink(self.passwdFilename);

if __name__ == "__main__":
    init_logging("watcher")

    if len(sys.argv) < 2:
        print "Usage: %s <appObjectUrl>" % sys.argv[0]
        sys.exit(1)

    venueUrl = sys.argv[1]

    sb = vncSharedAppClient( venueUrl )
