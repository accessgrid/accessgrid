import sys
import os
import time
import signal
import base64

if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc

from AccessGrid.hosting import Client
from AccessGrid import Events
from AccessGrid import EventClient
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import UserConfig, SystemConfig
from AccessGrid import DataStore
from AccessGrid.GUID import GUID
from AccessGrid.DataStoreClient import GetVenueDataStore

from AccessGrid.ClientProfile import ClientProfile

# Generic exception to indicate failure.  More precision should come later.
class VNCServerException(Exception):
    pass

class VNCAppServerException(Exception):
    pass

class vncServer:
    def __init__(self,displayID,geometry="1024x768",depth=24):
        if sys.platform == "win32":
            print "ERROR! Invalid system type"
            print "MUST RUN vncServer on a posix-compliant system!"
            raise VNCServerException("Invalid System Type - POSIX Required");

        # Initialize the contact string, construct it from the hostname and the
        # display ID
        hostname=SystemConfig.instance().GetHostname()
        self.contactString="%s%s"%(hostname,displayID);
        self.displayID=displayID;

        # Initialize internal representation of the desired geometry
        self.geometry={};
        (tmpWidth,tmpHeight)=geometry.split('x');
        self.geometry["Width"]=eval(tmpWidth);
        self.geometry["Height"]=eval(tmpHeight);

        # And depth
        self.depth=depth;

        # Initialize other random bits, mostly path/file names
        self.guid=str(GUID());
        self.passwdFilename=os.path.join(UserConfig.instance().GetTempDir(),"passwd-%s.vnc"%(self.guid));
        self.logFilename=os.path.join(UserConfig.instance().GetTempDir(),"Xvnc-%s.log"%(self.guid));
        self.lockFilename=os.path.join(UserConfig.instance().GetTempDir(),"Xvnc-%s.lock"%(self.guid));
        #self.passwdFilename="passwd-%s.vnc"%(self.guid);
        #self.logFilename="Xvnc-%s.log"%(self.guid);
        #self.lockFilename="Xvnc-%s.lock"%(self.guid);

        # No child process running...
        self.pid_set=0;

        # Initialize the password file.  Requires 'vncrandpwd' to be in the
        # current directory
        os.system("./vncrandpwd %s"%(self.passwdFilename));

    def getAuthFile(self):
        return self.passwdFilename;

    def getContactString(self):
        return self.contactString;

    def getGeometry(self):
        return "%dx%d"%(self.geometry["Width"],self.geometry["Height"]);

    def getDepth(self):
        return "%d"%(self.depth);

    def isRunning(self):
        try:
            import posix;
            if self.pid_set:
                if posix.access(self.lockFilename,posix.O_RDONLY):
                    return 1;
                else:
                    posix.waitpid(self.pid_set,posix.WNOHANG);
                    self.pid_set=0;
                    return 0;
            else:
                return 0;
        except:
            print "Exception ", sys.exc_type, sys.exc_value
            
        
    def start(self):
        if self.isRunning():
            raise VNCServerException("Start attempted while already running");
        try:
            import posix;

            self.pid_set=posix.fork();
            if self.pid_set:
                time.sleep(2);
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
                        "twm &\n"
                    f.write(defaultStartup)
                    f.close()
                    #print "chmod %s 755" % xstartup
                    os.system("chmod 755 %s " % xstartup)

                if os.path.exists(xstartup):
                    print "Running", xstartup
                    posix.system("env DISPLAY=%s sh %s &"%(self.displayID, xstartup));
                else:
                    posix.system("env DISPLAY=%s twm &"%(self.displayID));
                    print "TWM Running...";
                return 0;
            else:
                self.pid_set=posix.getpid();
                posix.close(posix.open(self.lockFilename,posix.O_CREAT));
                # Note: Xvnc *MUST* be in the CWD
                execline="/bin/bash -c './Xvnc %s -geometry %dx%d -depth %d -alwaysshared -rfbauth %s >& %s 2>&1'"%(self.displayID,self.geometry["Width"],
                                                                                                                    self.geometry["Height"],self.depth,
                                                                                                                    self.passwdFilename,self.logFilename);
                posix.system(execline);
                posix.unlink(self.lockFilename);
                posix._exit(0)
        except:
            print "Exception ", sys.exc_type, sys.exc_value

    def stop(self):
        import posix;
        if self.pid_set:
            if posix.access(self.lockFilename,posix.O_RDONLY):
                posix.kill(self.pid_set,9);
                posix.unlink(self.lockFilename);
                posix.waitpid(self.pid_set,posix.WNOHANG);
                self.pid_set=0;
                return 0;
            else:
                posix.waitpid(self.pid_set,posix.WNOHANG);
                self.pid_set=0;
                return 0;
        else:
            return 0;

    def destroy(self):
        self.stop();
        try:
            import posix;
            posix.unlink(self.passwdFilename);
            posix.unlink(self.logFilename);
        except:
            print "Exception ", sys.exc_type, sys.exc_value

class VNCServerAppObject:
    def __init__(self,venueUrl,displayID=":9",geometry="1024x768",depth=24):
        self.running = 0
        print venueUrl
        # Attach to venue server
        self.venueProxy=Client.SecureHandle(venueUrl).GetProxy();
        # Create VNC server
        self.vncServer=vncServer(displayID,geometry,depth);
        self.vncServer.start();

        # Create the App object
        self.appDescription=self.venueProxy.CreateApplication("VNC",
                                                      "VNC Server at %s"%(self.vncServer.getContactString()),
                                                      "application/x-ag-venuevnc");

        # Attach to it
        self.appProxy=Client.SecureHandle(self.appDescription.uri).GetProxy();

        print "App URL = %s"%(self.appDescription.uri);

        # Join the App Object
        #  ** NEW METHOD **
        (self.publicID,self.privateID)=self.appProxy.Join();

        # Load the password so it can be uploaded to the app object.
        pwd_file = file(self.vncServer.getAuthFile(), 'rb')
        pwd = pwd_file.read()
        pwd_file.close()
        # Upload the auth file to the app object
        self.appProxy.SetData(self.privateID,"VNC_Pwd",base64.encodestring(pwd));

        # Set the contact string
        self.appProxy.SetData(self.privateID,"VNC_Contact",self.vncServer.getContactString());
        # Set the geometry
        self.appProxy.SetData(self.privateID,"VNC_Geometry",self.vncServer.getGeometry());
        # Set the depth
        self.appProxy.SetData(self.privateID,"VNC_Depth",self.vncServer.getDepth());

        self.appProxy.Leave(self.privateID);

    def run(self):
        self.running = 1
        while self.running:
            time.sleep(1);

    def shutdown(self):
        # Stop while loop
        self.running = 0
        # Stop and cleanup vnc server
        self.vncServer.destroy()
        # Stop application service and remove from venue.
        self.venueProxy.DestroyApplication(self.appDescription.id)
        

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print "USAGE: %s <Venue URL> <Display ID> [Geometry [Depth]]"%(sys.argv[0]);
        sys.exit(0);

    venueURL=sys.argv[1];
    displayID=sys.argv[2];

    if len(sys.argv) > 3:
        geometry=sys.argv[3];
    else:
        geometry = '1024x768';

    if len(sys.argv) > 4:
        depth = eval(sys.argv[4]);
    else:
        depth = 24;

    appObj=VNCServerAppObject(venueURL,displayID,geometry,depth);

    def SignalHandler(signum, frame):
        print "Caught Signal", signum, ".  Shutting down and removing VNC service from venue."
        try:
            appObj.shutdown()
        except Exception, e:
            print "Exiting, but exception was caught when shutting down.", e
            os._exit(1)

    # We register signal handlers for the VenueServer. In the event of
    # a signal we just try to shut down cleanly.n
    signal.signal(signal.SIGINT, SignalHandler)
    signal.signal(signal.SIGTERM, SignalHandler)

    appObj.run();
