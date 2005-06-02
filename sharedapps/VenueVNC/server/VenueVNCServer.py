#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueVNCServer.py
# RCS-ID:      
# Copyright:   (c) 2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

#  
#  Execute the vnc server and create an application session in the specified
#  venue.  
#
#  Notes:
#  - the vnc server is assumed to be installed, and varies by platform:
#    - Linux: tightvnc, realvnc
#    - Windows: RealVNC
#    - OSX: OSXvnc
#  - the vnc server executable is searched for in the expected location (varies
#    per platform, see code) and in the user's path
#  - On Linux, the vnc server is started on display ':9' by default
#    On Windows and OSX, only the primary display can be shared
#  - On Linux, an xstartup file is executed from ~/.venuevnc/xstartup; customize
#    this file as appropriate
#  - If your machine is behind a firewall, you'll have to open ports to allow people
#    to access your vnc server:
#    - On Linux, the vnc server uses port (5900 + the display number)
#    - On Windows and OSX, the vnc server uses port 5900
#
import sys
import os
import time
import signal
import base64

from optparse import Option

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc

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
from AccessGrid.Venue import VenueIW
from AccessGrid.SharedApplication import SharedApplicationIW

from AccessGrid.ClientProfile import ClientProfile

from SOAPpy import faultType
from pyGlobus.io import GSITCPSocketException
if IsLinux():
    import commands

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
        self.passwdFilename = None
        
        # Initialize the password file.
        self.genPassword()
        
        self.processManager = ProcessManager()
        
        self.running = 0
        
    def genPassword(self):
    
        log.debug('vncServer.genPassword')
        import random
        
        self.password = ''
        for i in range(8):
            self.password += chr(random.randint(0,255))

    def writePasswordFile(self):
    
        # Create the password filename
        self.passwdFilename=os.path.join(UserConfig.instance().GetTempDir(),"passwd-%s.vnc"%(self.guid))
        
        # Write password file
        f = file(self.passwdFilename,'wb')
        f.write(self.password)
        f.close()

    def getPassword(self):
        return self.password

    def getContactString(self):
        return self.contactString

    def getGeometry(self):
        return "%dx%d"%(self.geometry["Width"],self.geometry["Height"])

    def getDepth(self):
        return "%d"%(self.depth)

    def isRunning(self):
        return self.running
                        
    def start(self):
        log.debug('vncServer.start')
        if self.isRunning():
            raise VNCServerException("Start attempted while already running")
        try:
            if IsWindows():
                # Convert the password to hex for windows command line
                password = ''
                for ch in self.password:
                    password += '%x' % (ord(ch),)
                args = [
                        'Password='+password,
                        'AlwaysShared=1',
                        ]

                log.info("starting vnc server: %s %s" % (self.vncserverexe,args))
                p = self.processManager.StartProcess(self.vncserverexe,args)
                log.debug("  pid = %s" % (p,))
            elif IsOSX():
                self.writePasswordFile()
                args = [
                        '-rfbauth',
                        self.passwdFilename,
                        '-alwaysshared',
                        ]
                log.info("starting vnc server: %s %s" % (self.vncserverexe,args))
                p = self.processManager.StartProcess(self.vncserverexe,args)
                log.debug("  pid = %s" % (p,))

            elif IsLinux():
                # Add entry in the xauthority file similar to the way
                #     vncserver does.
                cookie = commands.getoutput("/usr/bin/mcookie")
                hostname = commands.getoutput("uname -n")
                command = "xauth add %s%s . %s" % (hostname, self.displayID, cookie)
                os.system(command)
                command = "xauth add %s/unix%s . %s" %(hostname, self.displayID, cookie)
                os.system(command)

                self.writePasswordFile()
                args = [
                        self.displayID,
                        '-geometry', '%dx%d' % (self.geometry['Width'],self.geometry['Height']),
                        '-depth', self.depth,
                        '-rfbauth', self.passwdFilename,
                        '-alwaysshared'
                        ]
                log.info("starting vnc server: %s %s" % (self.vncserverexe,args))
                p = self.processManager.StartProcess(self.vncserverexe,args)
                log.debug("  pid = %s" % (p,))
                
                # Wait, then run xstartup
                time.sleep(2)
                # set paths to find config files
                venuevnc_path = os.path.join(os.environ["HOME"], ".venuevnc")
                xstartup = os.path.join(venuevnc_path, "xstartup")
                # if xstartup file does not exist, create one.
                if not os.path.exists(xstartup):
                    log.info("Creating xstartup file")
                    if not os.path.exists(venuevnc_path):
                        os.mkdir(venuevnc_path)
                    f = file(xstartup, "w+")
                    # default is the same as tight vnc's default, but use mwm
                    # instead of twm if it is available 
                    windowmanager = "twm"
                    if os.path.exists("/usr/X11R6/bin/mwm"):
                        windowmanager = "/usr/X11R6/bin/mwm" 
                    defaultStartup= "#!/bin/sh\n\n" +     \
                        "#xrdb $HOME/.Xresources\n" +     \
                        "xsetroot -solid grey\n" +        \
                        "xterm -geometry 80x24+10+10 -ls -title \"VenueVNC Desktop\" &\n" +    \
                        windowmanager + " &\n"
                    f.write(defaultStartup)
                    f.close()
                    os.chmod(xstartup,0755)
                else:
                    log.info("Using existing xstartup file")

                os.environ["DISPLAY"] = self.displayID
                if os.path.exists(xstartup):
                    log.info("Running x startup script %s" % ( xstartup,))
                    self.processManager.StartProcess(xstartup,[])
                else:
                    log.info("Running MWM")
                    self.processManager.StartProcess('mwm',[])
                    
                    
                self.running = 1
        except:
            log.exception("Failed to start vncServer")
            raise

    def stop(self):
        log.info("vncServer.stop")
        if self.running:
            log.info('- terminating vnc server process')
            self.processManager.TerminateAllProcesses()
        else:
            log.info("- not running, not terminating")
        self.running=0

    def destroy(self):
        log.debug('vncServer.destroy')
        self.stop()
        try:
            if self.passwdFilename:
                os.unlink(self.passwdFilename)
        except:
            log.exception("Failed to unlink password file")

class VNCServerAppObject:
    def __init__(self,venueUrl,vncserverexe,displayID,geometry,depth,name):
        log.debug('VNCServerAppObject.__init__')
        self.running = 0
        
        # Create VNC server
        self.vncServer=vncServer(vncserverexe,displayID,geometry,depth)
        self.vncServer.start()
        
        # Create the App object
        self.venueProxy=VenueIW(venueUrl)
        try:
            self.appDescription=self.venueProxy.CreateApplication(name,
                                                      "VNC Server at %s"%(self.vncServer.getContactString()),
                                                      "application/x-ag-venuevnc")
        except:
            log.exception("Failed to create application session")
            self.vncServer.destroy()
            raise

        # Attach to it
        self.appProxy=SharedApplicationIW(self.appDescription.uri)

        log.info("App URL = %s"%(self.appDescription.uri))

        try:
            # Join the App Object
            (self.publicID,self.privateID)=self.appProxy.Join()

            # Upload the auth file to the app object
            self.appProxy.SetData(self.privateID,"VNC_Pwd",base64.encodestring(self.vncServer.getPassword()))

            # Set the contact string
            self.appProxy.SetData(self.privateID,"VNC_Contact",self.vncServer.getContactString())
            # Set the geometry
            self.appProxy.SetData(self.privateID,"VNC_Geometry",self.vncServer.getGeometry())
            # Set the depth
            self.appProxy.SetData(self.privateID,"VNC_Depth",self.vncServer.getDepth())

            self.appProxy.Leave(self.privateID)
        except:
            log.exception("Failed to configure application session")
            self.vncServer.destroy()
            raise

    def run(self):
        log.debug('VNCServerAppObject.run')
        self.running = 1
        while self.running:
            time.sleep(1)

    def shutdown(self):
        log.debug('VNCServerAppObject.shutdown')
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

    # Log options in debug mode
    if app.GetOption('debug'):
        log.info("Options:")
        for opt in ['venueUrl','name','vncserverexe','display','geometry','depth']:
            log.info('  %s = %s' % (opt,str(app.GetOption(opt))))
    
    
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
            expectedPath = '/Applications/OSXvnc.app'
            exe = 'OSXvnc-server'
        elif IsLinux():
            expectedPath = '/usr/bin'
            exe = 'Xvnc'
        vncserverexe = None
        pathList = [expectedPath]
        pathList += os.environ["PATH"].split(os.pathsep)
        for path in pathList:
            f = os.path.join(path,exe)
            if os.path.exists(f):
                vncserverexe = f
                break

    if not vncserverexe or not os.path.exists(vncserverexe):
        msg = "Couldn't find vnc server executable %s ; exiting." % (vncserverexe,)
        print msg
        log.info(msg)
        sys.exit(1)
    else:
        log.debug("found vncserverexe = %s", vncserverexe)

    name = app.GetOption('name')
    if not name:
        timestamp = time.strftime("%I:%M:%S %p %B %d, %Y")
        name = "VenueVNC - %s" % (timestamp)
    
    
    try:
        appObj=VNCServerAppObject(app.GetOption('venueUrl'),vncserverexe,
                                  app.GetOption('display'),
                                  app.GetOption('geometry'),
                                  app.GetOption('depth'),
                                  name)
    except faultType, e:
        print "Failed to create VenueVNC session: ",
        if e.faultstring == 'Method Not Found':
            print "Bad venue url"
        sys.stdout.flush()
        os._exit(1)
    except GSITCPSocketException, e:
        print "Failed to create VenueVNC session: ",
        if str(e).endswith('could not be resolved'):
            print str(e)
        elif str(e).endswith('(Connection refused)'):
            print "connection refused (no venue server at given port)"
        
        os._exit(1)
    except Exception, e:
        log.exception("Failure starting VenueVNC session")
        print "Failure starting VenueVNC session (see VenueVNCServer.log for more details)"
        os._exit(1)
        
        

    def SignalHandler(signum, frame):
        log.info("Caught Signal %d. Shutting down and removing VNC service from venue." % (signum,))
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
