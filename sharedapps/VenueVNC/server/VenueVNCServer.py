#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueVNCServer.py
# RCS-ID:      
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
import sys
import os
import time
import signal
import base64

from optparse import Option

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc

from AccessGrid.hosting import Client
from AccessGrid import Events
from AccessGrid import EventClient
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import UserConfig, SystemConfig
from AccessGrid.Platform import IsWindows, IsLinux, IsOSX
from AccessGrid import DataStore
from AccessGrid.GUID import GUID
from AccessGrid.DataStoreClient import GetVenueDataStore
from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.Platform.ProcessManager import ProcessManager

from AccessGrid.ClientProfile import ClientProfile

log = None

# Generic exception to indicate failure.  More precision should come later.
class VNCServerException(Exception):
    pass

class VNCAppServerException(Exception):
    pass
    
class vncServer:
    def __init__(self,vncserverexe,displayID,geometry="1024x768",depth=24):
            
        # Initialize the vncserver executable
        self.vncserverexe = vncserverexe

        # Initialize the contact string, construct it from the hostname and the
        # display ID
        hostname=Toolkit.CmdlineApplication.instance().GetHostname()
        if IsWindows():
            self.contactString="%s"%(hostname,)
        elif IsOSX():
            self.contactString="%s"%(hostname,)
        elif IsLinux():
            self.contactString="%s%s"%(hostname,displayID)
            
        self.displayID=displayID
        
        # Initialize internal representation of the desired geometry
        self.geometry={}
        (tmpWidth,tmpHeight)=geometry.split('x')
        self.geometry["Width"]=eval(tmpWidth)
        self.geometry["Height"]=eval(tmpHeight)

        # And depth
        self.depth=depth

        # Initialize other random bits, mostly path/file names
        self.guid=str(GUID())
        self.passwdFilename=os.path.join(UserConfig.instance().GetTempDir(),"passwd-%s.vnc"%(self.guid))
        self.lockFilename=os.path.join(UserConfig.instance().GetTempDir(),"Xvnc-%s.lock"%(self.guid))
        
        # Initialize the password file.
        self.genPassword()
        
        self.processManager = ProcessManager()
        
        self.running = 0
        
    def genPassword(self):
        import random
        
        self.password = ''
        for i in range(8):
            self.password += '%x' % random.randint(0,256)

        f = file(self.passwdFilename,'wb')
        f.write(self.password)
        f.close()

    def getAuthFile(self):
        return self.passwdFilename

    def getContactString(self):
        return self.contactString

    def getGeometry(self):
        return "%dx%d"%(self.geometry["Width"],self.geometry["Height"])

    def getDepth(self):
        return "%d"%(self.depth)

    def isRunning(self):
        return self.running
                        
    def start(self):
        if self.isRunning():
            raise VNCServerException("Start attempted while already running")
        try:
            if IsWindows():
                args = [
                        'Password='+self.password,
                        'AlwaysShared=1',
                        ]

                log.info("starting vnc server: %s %s" % (self.vncserverexe,args))
                p = self.processManager.StartProcess(self.vncserverexe,args)
                log.debug("  pid = %s" % (p,))
            elif IsOSX():
                args = [
                        '-rfbauth='+self.passwdFilename,
                        '-alwaysshared',
                        ]
                log.info("starting vnc server: %s %s" % (self.vncserverexe,args))
                p = self.processManager.StartProcess(self.vncserverexe,args)
                log.debug("  pid = %s" % (p,))

            elif IsLinux():
                args = [
                        self.displayID,
                        '-geometry', '%dx%d' % (self.geometry['Width'],self.geometry['Height']),
                        '-depth', self.depth,
                        '-rfbauth', self.passwdFilename,
                        '-alwaysshared'
                        ]
                self.processManager.StartProcess(self.vncserverexe,args)
                
                # Wait, then run xstartup
                time.sleep(2)
                # set paths to find config files
                venuevnc_path = os.path.join(os.environ["HOME"], ".venuevnc")
                xstartup = os.path.join(venuevnc_path, "xstartup")
                # if xstartup file does not exist, create one.
                if not os.path.exists(xstartup):
                    if not os.path.exists(venuevnc_path):
                        os.mkdir(venuevnc_path)
                    f = file(xstartup, "w+")
                    # default is the same as tight vnc's default.
                    defaultStartup= "#!/bin/sh\n\n" +     \
                        "#xrdb $HOME/.Xresources\n" +     \
                        "xsetroot -solid grey\n" +        \
                        "xterm -geometry 80x24+10+10 -ls -title \"VenueVNC Desktop\" &\n" +    \
                        "mwm &\n"
                    f.write(defaultStartup)
                    f.close()
                    os.chmod(xstartup,0755)

                os.environ["DISPLAY"] = self.displayID
                if os.path.exists(xstartup):
                    log.info("Running x startup script %s" % ( xstartup,))
                    self.processManager.StartProcess(xstartup,[])
                else:
                    log.info("Running MWM")
                    self.processManager.StartProcess('mwm',[])
        except:
            log.exception("::start failed")

    def stop(self):
        if os.access(self.lockFilename,os.O_RDONLY):
            self.processManager.TerminateAllProcesses()
            os.unlink(self.lockFilename)
        self.running=0

    def destroy(self):
        self.stop()
        try:
            os.unlink(self.passwdFilename)
        except:
            log.exception("::stop failed")

class VNCServerAppObject:
    def __init__(self,venueUrl,vncserverexe,displayID,geometry,depth,name):
        self.running = 0
        # Attach to venue server
        self.venueProxy=Client.SecureHandle(venueUrl).GetProxy()
        # Create VNC server
        self.vncServer=vncServer(vncserverexe,displayID,geometry,depth)
        self.vncServer.start()
        
        # Create the App object
        self.appDescription=self.venueProxy.CreateApplication(name,
                                                      "VNC Server at %s"%(self.vncServer.getContactString()),
                                                      "application/x-ag-venuevnc")

        # Attach to it
        self.appProxy=Client.SecureHandle(self.appDescription.uri).GetProxy()

        log.info("App URL = %s"%(self.appDescription.uri))

        # Join the App Object
        (self.publicID,self.privateID)=self.appProxy.Join()

        # Load the password so it can be uploaded to the app object.
        pwd_file = file(self.vncServer.getAuthFile(), 'rb')
        pwd = pwd_file.read()
        pwd_file.close()
        # Upload the auth file to the app object
        self.appProxy.SetData(self.privateID,"VNC_Pwd",base64.encodestring(pwd))

        # Set the contact string
        self.appProxy.SetData(self.privateID,"VNC_Contact",self.vncServer.getContactString())
        # Set the geometry
        self.appProxy.SetData(self.privateID,"VNC_Geometry",self.vncServer.getGeometry())
        # Set the depth
        self.appProxy.SetData(self.privateID,"VNC_Depth",self.vncServer.getDepth())

        self.appProxy.Leave(self.privateID)

    def run(self):
        self.running = 1
        while self.running:
            time.sleep(1)

    def shutdown(self):
        # Stop while loop
        self.running = 0
        # Stop and cleanup vnc server
        self.vncServer.destroy()
        # Stop application service and remove from venue.
        self.venueProxy.DestroyApplication(self.appDescription.id)
        

if __name__ == "__main__":

    app = CmdlineApplication().instance()
    app.AddCmdLineOption( Option("-v", "--venueUrl", type="string", dest="venueUrl",
                        default='https://localhost:8000/Venues/default', metavar="VENUE_URL",
                        help="Set the venue in which the VenueVNC application should be started.") )
    app.AddCmdLineOption( Option("-n", "--name", type="string", dest="name",
                        default=None, metavar="NAME",
                        help="Set the name by which the server will be identified in the venue.") )
    app.AddCmdLineOption( Option("--vncserverexe", type="string", dest="vncserverexe",
                        default=None, metavar="VNC_SERVER_EXE",
                        help="Set the VNC server executable to use") )

    app.AddCmdLineOption( Option("--display", type="string", dest="display",
                        default=":9", metavar="DISPLAY",
                        help="Set the display the VNC server should run on. (linux only)") )
    app.AddCmdLineOption( Option("-g", "--geometry", type="string", dest="geometry",
                        default="1024x768", metavar="GEOMETRY",
                        help="Set the geometry of the VNC server. (linux only)") )
    app.AddCmdLineOption( Option("--depth", type="int", dest="depth",
                        default=24, metavar="DEPTH",
                        help="Set the bit depth to use for the server. (linux only)") )

    app.Initialize("VenueVNCServer")
    
    log = app.GetLog()
    
    # Use the vnc executable specified on the command line, or...
    vncserverexe = app.GetOption('vncserverexe')
    if vncserverexe and not os.path.exists(vncserverexe):
        msg = "Couldn't find vnc server executable %s ; exiting." % (vncserverexe,)
        print msg
        log.info(msg)
        sys.exit(1)
        
    # ...search for it in the current dir, the expected install dir, 
    # and the user's path
    if not vncserverexe:
        # Find vnc server executable in user's path
        if IsWindows():
            expectedPath = 'c:\\program files\\realvnc\\vnc4'
            exe = 'winvnc4.exe'
        elif IsOSX():
            expectedPath = '/Applications/OSXvnc.app/'
            exe = 'OSXvnc-server'
        elif IsLinux():
            expectedPath = '/usr/bin'
            exe = 'Xvnc'
        vncserverexe = None
        pathList = ['.',expectedPath]
        pathList += os.environ["PATH"].split(os.pathsep)
        for path in pathList:
            f = os.path.join(path,exe)
            if os.path.exists(f):
                vncserverexe = f
                break
        log.debug("found vncserverexe = %s", vncserverexe)

    if not vncserverexe or not os.path.exists(vncserverexe):
        msg = "Couldn't find vnc server executable %s ; exiting." % (vncserverexe,)
        print msg
        log.info(msg)
        sys.exit(1)

    if not app.GetOption('name'):
        timestamp = time.strftime("%I:%M:%S %p %B %d, %Y")
        name = "VenueVNC - %s" % (timestamp)

    appObj=VNCServerAppObject(app.GetOption('venueUrl'),vncserverexe,
                              app.GetOption('display'),
                              app.GetOption('geometry'),
                              app.GetOption('depth'),
                              name)

    def SignalHandler(signum, frame):
        print "Caught Signal", signum, ".  Shutting down and removing VNC service from venue."
        try:
            appObj.shutdown()
        except Exception, e:
            log.exception("Error in shutdown")
            print "Exiting, but exception was caught when shutting down.", e
            os._exit(1)

    # We register signal handlers for the VenueServer. In the event of
    # a signal we just try to shut down cleanly.n
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    appObj.run()
