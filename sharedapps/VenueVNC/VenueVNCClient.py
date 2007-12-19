#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueVNCClient.py
# RCS-ID:      
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import os
import sys
import base64

from AccessGrid import Events
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Platform import IsWindows,IsLinux,IsOSX,IsFreeBSD
from AccessGrid import DataStore
from AccessGrid import Platform
from AccessGrid.GUID import GUID
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.SharedApplication import SharedApplicationIW

from AccessGrid import Log
log = Log.GetLogger("VenueVNCClient")

class vncSharedAppClient:
    """
    """
    def __init__( self, appUrl, clientProfile ):

        self.appUrl = appUrl

        self.appProxy=SharedApplicationIW(self.appUrl)
        print( "Application URL: %s" %(self.appUrl) )
        #print( "Application URL Valid? " + self.appProxy.isValid( ) )
        # Join the application
        #  ** NEW METHOD **
        (self.publicId, self.privateId) = self.appProxy.Join(clientProfile)
        #  ** OLD METHOD **
        #self.privateId=self.appProxy.Join(ClientProfile('./profile'))

        #
        # Retrieve the channel id
        #
        (self.channelId, address, port ) = self.appProxy.GetDataChannel(self.privateId)

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
        self.vncContact = self.appProxy.GetData(self.privateId, "VNC_Contact");
        self.vncGeometry = self.appProxy.GetData(self.privateId, "VNC_Geometry");
        self.vncDepth = self.appProxy.GetData(self.privateId, "VNC_Depth");
        # Read password from app object
        encoded_pwd = self.appProxy.GetData(self.privateId, "VNC_Pwd")

        print "VNC Server at %s (%s, %s-bits):"%(self.vncContact,self.vncGeometry,self.vncDepth);
        self.passwdFilename=os.path.join(UserConfig.instance().GetTempDir(), ("passwd-" + str(GUID()) + ".vnc"))
        # Write password to file so it can be passed to vnc.
        pwd_file = file(self.passwdFilename, 'wb')
        pwd_file.write(base64.decodestring(encoded_pwd))
        pwd_file.close()


        # Change to the location of the application before running, since helper executables are located here.
        print "Running from directory", os.getcwd()

        execString = ""
        if IsWindows():
            width=eval(self.vncGeometry.split('x')[0]);
            if width >= 5120:
                execString='vncviewer -shared -scale 1/4 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            elif width >= 4096:
                execString='vncviewer -shared -scale 1/3 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            elif width >= 3072:
                execString='vncviewer -shared -scale 1/2 -passwd %s %s'%(self.passwdFilename,self.vncContact)
            else:
                execString='vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)                
        elif IsLinux():
            if os.path.exists("/usr/local/bin/vncviewer") or os.path.exists("/usr/bin/vncviewer"):
		execString='vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)
            else:
		execString='chmod +x ./vncviewer; ./vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)
        elif IsFreeBSD():
            if os.path.exists("/usr/local/bin/vncviewer") or os.path.exists("/usr/X11R6/bin/vncviewer"):
		execString='vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)
            else:
		execString='chmod +x ./vncviewer; ./vncviewer -shared -passwd %s %s'%(self.passwdFilename,self.vncContact)
        elif IsOSX():
            vncviewer='./Chicken\ of\ the\ VNC'
            execString='%s --PasswordFile %s %s' % (vncviewer,self.passwdFilename,self.vncContact)
        else:
            raise Exception("Unsupported platform")
        print "About the execute: %s"%(execString)
        log.info("Starting vnc client: %s", execString)
        os.system(execString);
        os.unlink(self.passwdFilename);

if __name__ == "__main__":
    app = CmdlineApplication.instance()
    app.Initialize("VenueVNCClient")

    log = app.GetLog()

    if len(sys.argv) < 2:
        print "Usage: %s <appObjectUrl>" % sys.argv[0]
        sys.exit(1)

    appUrl = sys.argv[1]

    clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(),
                                     "profile")
    clientProfile = ClientProfile(clientProfileFile)
    sb = vncSharedAppClient( appUrl, clientProfile )

