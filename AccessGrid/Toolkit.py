#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.30 2004-03-23 22:14:13 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Toolkit.py,v 1.30 2004-03-23 22:14:13 judson Exp $"

# Standard imports
import os
import sys
import getopt
import md5
from optparse import OptionParser, Option

# AGTk imports
from AccessGrid import Log
from AccessGrid.Security import CertificateManager
from AccessGrid.Security import CertificateRepository
from AccessGrid.Platform.Config import AGTkConfig, GlobusConfig
from AccessGrid.Platform.Config import SystemConfig, UserConfig
from AccessGrid.ServiceProfile import ServiceProfile
from AccessGrid.Version import GetVersion

class AppBase:
    """
    The application object is one of the top level objects used to
    build new parts of the AGTk. The application object is required to
    be a singleton in any process.
    """
    # The singleton
    theInstance = None

    # The class method for retrieving/creating the singleton
    def instance():
       """
       The interface for getting the one true instance of this object.
       """
       raise "This should never be called directly."

    # The real constructor
    def __init__(self):
       """
       The application constructor that enforces the singleton pattern.
       """
       self.parser = OptionParser()
       self.parser.add_option("-d", "--debug", action="store_true",
                              dest="debug", default=0,
                              help="Set the debug level of this program.")
       self.parser.add_option("-l", "--logfile", dest="logfilename",
                              metavar="LOGFILE", default=None,
                              help="Specify a log file to output logging to.")
       self.parser.add_option("-c", "--configfile", dest="configfilename",
                              metavar="CONFIGFILE", default=None,
                         help="Specify a configuration file for the program.")
       self.parser.add_option("--version", action="store_true", dest="version",
                              default=0,
                         help="Print out what version of the toolkit this is.")
       
       self.certMgrUI = None
       self.userConfig = None
       self.agtkConfig = None
       self.globusConfig = None
       
    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None):
       """
       This method sets up everything for reasonable execution.
       At the first sign of any problems it raises exceptions and exits.
       """
       self.name = name

       self.defLogHandler = Log.StreamHandler()
       self.defLogHandler.setFormatter(Log.GetFormatter())

       # 0. Initialize logging, storing in log data memory
       mlh = Log.handlers.MemoryHandler(8192, flushLevel=Log.ERROR,
                                        target=self.defLogHandler)

       mlh.setFormatter(Log.GetFormatter())
       
       # This initializes logging
       self.log = Log.GetLogger(Log.Toolkit)
       levelHandler = Log.HandleLoggers(mlh, Log.GetDefaultLoggers())
       
       # 1. Process Command Line Arguments
       argvResult = self.ProcessArgs()

       # 2. Load the Toolkit wide configuration.
       try:
           self.agtkConfig = AGTkConfig.instance()
       except Exception, e:
           self.log.exception("Toolkit Initialization failed.")
           sys.exit(-1)

       # 3. Load the user configuration, creating one if necessary.
       try:
           self.userConfig = UserConfig.instance(initIfNeeded=1)
       except Exception, e:
           self.log.exception("User Initialization failed.")
           sys.exit(-1)
       
       # 4. Redirect logging to files in the user's directory,
       #    purging memory to file

       fh = self.defLogHandler

       if self.options.logfilename is not None:
           if not self.options.logfilename.endswith(".log"):
               self.name = self.options.logfilename + ".log"
       elif self.name is not None:
           if not self.name.endswith(".log"):
               self.name = self.name + ".log"

       if self.name is not None:
           filename = os.path.join(self.userConfig.GetConfigDir(), self.name)
           fh = Log.FileHandler(filename)
           
       fh.setFormatter(Log.GetFormatter())
       levelHandler = Log.HandleLoggers(fh, Log.GetDefaultLoggers())

       mlh.setTarget(fh)
       mlh.close()
       
       # 5. Retrieve the Globus Configuration from the system.
       #     (this will implicitly initialize globus if it's not
       #       already initialized)
       #     (including the GLOBUS_HOSTNAME)
       try:
           self.globusConfig = GlobusConfig.instance(initIfNeeded=0)
       except Exception, e:
           log.exception("Globus Initialization failed.")
           sys.exit(-1)
       
       return argvResult

    def ProcessArgs(self):
       """
       Process toolkit wide standard arguments. Then return the modified
       argv so the app can choose to parse more if it requires that.
       """
       
       (self.options, args) = self.parser.parse_args()

       if self.options.version:
           print "Access Grid Toolkit Version: ", GetVersion()
           sys.exit(0)
           
       if self.options.debug:
           levelHandler = Log.HandleLoggers(self.defLogHandler,
                                           Log.GetDefaultLoggers())
           levelHandler.SetLevel(Log.DEBUG)
           
       return args

    def AddCmdLineOption(self, option):
        self.parser.add_option(option)
        
    def GetOption(self, arg):

        if hasattr(self.options, arg):
            return getattr(self.options, arg)
        else:
            return None

    def GetDebugLevel(self):
        """
        """
        return self.GetOption("debug")

    def GetLogFilename(self):
        """
        """
        return self.GetOption("logfilename")
    
    def GetLogFilename(self):
        """
        """
        return self.GetOption("configfilename")
    
    def GetLog(self):
        """
        Return a toolkit wide log.
        """
        return self.log

    def GetToolkitConfig(self):
        return self.agtkConfig

    def GetUserConfig(self):
        return self.userConfig

    def GetGlobusConfig(self):
        return self.globusConfig

    def GetDefaultIdentityDN(self):
        ident = self.certificateManager.GetDefaultIdentity()
        if ident is None:
            return None
        else:
            return str(ident.GetSubject())

    def GetCertificateManager(self):
       return self.certificateManager

    def GetCertMgrUI(self):
       return self.certMgrUI
   
    def FindConfigFile(self, configFile):
        """
        Locate given file in configuration directories:
        first check user dir, then system dir;
        return None if not found
        """
        
        userConfigPath = self.userConfig.GetConfigDir()
        pathToFile = os.path.join(userConfigPath, configFile)
        if os.path.exists( pathToFile ):
            return pathToFile
        
        systemConfigPath = self.agtkConfig.GetConfigDir()
        pathToFile = os.path.join(systemConfigPath,configFile)
        if os.path.exists( pathToFile ):
            return pathToFile
        
        raise Exception, "File Not Found"

class Application(AppBase):
    """
    The application object is one of the top level objects used to
    build new parts of the AGTk. The application object is required to
    be a singleton in any process.
    """
    # The singleton
    theAppInstance = None

    # The class method for retrieving/creating the singleton
    def instance():
       """
       The interface for getting the one true instance of this object.
       """
       if Application.theAppInstance == None:
          Application()
         
       return Application.theAppInstance
      
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
       """
       The application constructor that enforces the singleton pattern.
       """
       AppBase.__init__(self)
       
       if Application.theAppInstance is not None:
          raise Exception, "Only one instance of Application is allowed"
       
       # Create the singleton instance
       Application.theAppInstance = self

    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None):
       """
       This method sets up everything for reasonable execution.
       At the first sign of any problems it raises exceptions and exits.
       """
       argvResult = AppBase.Initialize(self, name)
       
       # 6. Initialize Certificate Management
       # This has to be done by sub-classes
       configDir = self.userConfig.GetConfigDir()
       self.certificateManager = \
            CertificateManager.CertificateManager(configDir, self.certMgrUI)

       self.GetCertificateManager().GetUserInterface().InitGlobusEnvironment()

       # 7. Do one final check, if we don't have a default
       #    Identity we bail, there's nothing useful to do.

       if self.GetDefaultIdentityDN() is None:
           self.log.error("Toolkit initialized with no default identity.")
           self.log.error("Exiting because there's no default identity.")
           sys.exit(-1)
           
       return argvResult

class CmdlineApplication(Application):
    """
    An application that's going to run without a gui.
    """
    def __init__(self):
        Application.__init__(self)
        self.certMgrUI = CertificateManager.CertificateManagerUserInterface()

class WXGUIApplication(Application):
    def __init__(self):
        Application.__init__(self)
        from AccessGrid.Security.wxgui import CertificateManagerWXGUI
        self.certMgrUI = CertificateManagerWXGUI.CertificateManagerWXGUI()

class Service(AppBase):
    """
    The service object is one of the top level objects used to
    build new parts of the AGTk. The service object is required to
    be a singleton in any process.
    """
    # The singleton
    theServiceInstance = None

    # The class method for retrieving/creating the singleton
    def instance():
       """
       The interface for getting the one true instance of this object.
       """
       if Service.theServiceInstance == None:
          Service()
         
       return Service.theServiceInstance
      
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
        """
        The application constructor that enforces the singleton pattern.
        """
        AppBase.__init__(self)

        self.profile = None

        if Service.theServiceInstance is not None:
          raise Exception, "Only one instance of Service is allowed"

        # Create the singleton instance
        Service.theServiceInstance = self

        # Add cert, key, and profile options
        profileOption = Option("--profile", dest="profile", metavar="PROFILE",
                           help="Specify a service profile.")
        self.AddCmdLineOption(profileOption)

    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None):
        """
        This method sets up everything for reasonable execution.
        At the first sign of any problems it raises exceptions and exits.
        """
        argvResult = AppBase.Initialize(self, name)

        print "Service init: have profile ", self.options.profile

        # Deal with the profile if it was passed instead of cert/key pair
        if self.options.profile is not None:
           self.profile = ServiceProfile()
           self.profile.Import(self.options.profile)
           print self.profile.AsINIBlock()

        # 6. Initialize Certificate Management
        # This has to be done by sub-classes
        configDir = self.userConfig.GetConfigDir()
        self.certMgrUI = CertificateManager.CertificateManagerUserInterface()
        certMgr = self.certificateManager = \
            CertificateManager.CertificateManager(configDir, self.certMgrUI)

        #
        # If we have a service profile, load and parse, then configure
        # certificate manager appropriately.
        #

        if self.profile:
           if self.profile.subject is not None:

               self._CheckRequestedCert(self.profile.subject)

               certMgr.SetTemporaryDefaultIdentity(useDefaultDN = self.profile.subject)
           elif self.profile.certfile is not None:
               certMgr.SetTemporaryDefaultIdentity(useCertFile = self.profile.certfile,
                                                   useKeyFile = self.profile.keyfile)

        self.GetCertificateManager().GetUserInterface().InitGlobusEnvironment()

        # 7. Do one final check, if we don't have a default
        #    Identity we bail, there's nothing useful to do.

        if self.GetDefaultIdentityDN() is None:
           log.error("Toolkit initialized with no default identity.")
           log.error("Exiting because there's no default identity.")
           sys.exit(-1)

        return argvResult

    def _CheckRequestedCert(self, dn):
        """
        Check to see if we have a cert with this dn; if we do not,
        check to see if there's a request pending for it. If there is,
        install. Otherwise just return.

        @param dn: Distinguished name of identity to check for.
        
        """

        certMgr = self.certificateManager
        repo = self.certificateManager.GetCertificateRepository()

        certs = repo.FindCertificatesWithSubject(dn)
        validCerts = filter(lambda a: not a.IsExpired(), certs)
        
        if len(validCerts) > 0:
            return

        #
        # No certs found, see if we have a request for this one.
        #

        pending = certMgr.GetPendingRequests()

        reqs = filter(lambda a: str(a[0].GetSubject()) == dn, pending)
        if len(reqs) == 0:
            print "No requests found"
            return

        if len(reqs) > 1:
            print "Multiple requests found, just picking one"
            
        request, token, server, created = reqs[0]

        print "Found request at ", server

        #
        # Check status. Note that if a proxy is required, we
        # may not be using it. However, underlying library might
        # set it up if the environment requires it.
        #
        
        status = certMgr.CheckRequestedCertificate(request, token, server)
        success, certText = status
        if not success:
            #
            # Nope, not ready.
            #
            print "Certificate not ready: ", certText
            return

        #
        # Success! we can install the cert.
        #

        hash = md5.new(certText).hexdigest()
        tempfile = os.path.join(UserConfig.instance().GetTempDir(), "%s.pem" % (hash))

        try:
            try:
                fh = open(tempfile, "w")
                fh.write(certText)
                fh.close()

                impCert = certMgr.ImportRequestedCertificate(tempfile)

                print "Successfully imported certificate for ", \
                      str(impCert.GetSubject())

            except CertificateRepository.RepoInvalidCertificate, e:
                msg = e[0]
                print "The import of your approved certificate failed: ", msg

            except Exception, e:
                print "The import of your approved certificate failed: ", e

        finally:
            os.unlink(tempfile)
            
