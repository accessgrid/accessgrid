#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.91 2005-10-07 22:10:09 eolson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Toolkit.py,v 1.91 2005-10-07 22:10:09 eolson Exp $"

# Standard imports
import os
import sys
import md5
from optparse import OptionParser, Option
import time

# AGTk imports
from AccessGrid import Log
from AccessGrid.Preferences import Preferences
#from AccessGrid.Security import CertificateManager
#from AccessGrid.Security import CertificateRepository
from AccessGrid.Platform.Config import AGTkConfig, MimeConfig
from AccessGrid.Platform.Config import SystemConfig, UserConfig
from AccessGrid.Platform import IsWindows
from AccessGrid.ServiceProfile import ServiceProfile
from AccessGrid.Version import GetVersion
from AccessGrid.Security import X509Subject
from AccessGrid.NetUtilities import GetSNTPTime
from AccessGrid.wsdl import SchemaToPyTypeMap

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
       raise Exception, "This should never be called directly."
       
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
       """
       The application constructor that enforces the singleton pattern.
       """

       # Load client preferences
       self.preferences = Preferences()
       
       self.parser = OptionParser()
       self.parser.add_option("-d", "--debug", action="store_true",
                              dest="debug", default=0,
                              help="Set the debug level of this program.")
       self.parser.add_option("-l", "--logfile", dest="logfilename",
                              metavar="LOGFILE", default=None,
                              help="Specify a log file to output logging to.")
       self.parser.add_option("--numlogfiles", dest="numlogfiles",
                              metavar="NUMLOGFILES", default=1, type="int",
                              help="Specify the number of log files to retain")
       self.parser.add_option("--logfilesize", dest="logfilesize",
                              metavar="LOGFILESIZE", default=10000000, type="long",
                              help="Specify the size of log files to retain")
       self.parser.add_option("-c", "--configfile", dest="configfilename",
                              metavar="CONFIGFILE", default=None,
                         help="Specify a configuration file for the program.")
       self.parser.add_option("--version", action="store_true", dest="version",
                              default=0,
                         help="Print out what version of the toolkit this is.")
       self.parser.add_option("-i", "--secure", action="store_true",
                              dest="secure", default=0,
                              help="Use secure communications.")
       self.parser.add_option("--cert", dest="cert",
                              metavar="CERTFILE", default=None,
                         help="Specify a configuration file for the program.")
       self.parser.add_option("--key", dest="key",
                              metavar="KEYFILE", default=None,
                         help="Specify a configuration file for the program.")
       self.parser.add_option("--cadir", dest="cadir",
                              metavar="CADIR", default=None,
                         help="Specify a configuration file for the program.")

       self.options = None
       self.certMgrUI = None
       self.userConfig = None
       self.agtkConfig = None
       self.systemConfig = SystemConfig.instance()
       self.log = None
       
       self.certificateManager = None
       
       # This initializes logging
       self.log = Log.GetLogger(Log.Toolkit)
       self.log.debug("Initializing AG Toolkit version %s", GetVersion())

    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None, args=None):
       """
       This method sets up everything for reasonable execution.
       At the first sign of any problems it raises exceptions and exits.
       """
       self.name = name

       # 1. Process Command Line Arguments
       argvResult = self.ProcessArgs(args=args)

       # 2. Load the Toolkit wide configuration.
       try:
           self.agtkConfig = AGTkConfig.instance(0)
       except Exception:
           self.log.exception("Toolkit Initialization failed.")
           sys.exit(-1)

       # 3. Load the user configuration, creating one if necessary.
       try:
           self.userConfig = UserConfig.instance(initIfNeeded=1)
       except Exception:
           self.log.exception("User Initialization failed.")
           sys.exit(-1)
       
       # 4. Redirect logging to files in the user's directory,
       #    purging memory to file

       fh = Log.defLogHandler

       if self.options.logfilename is not None:
           if not self.options.logfilename.endswith(".log"):
               self.name = self.options.logfilename + ".log"
           else:
               self.name = self.options.logfilename
       elif self.name is not None:
           if not self.name.endswith(".log"):
               self.name = self.name + ".log"

       self.log.info("Logfile Name: %s", self.name)
       
       if self.name:
           if not self.name.startswith(os.sep) \
                                     and not self.name.startswith("."):
               filename = os.path.join(self.userConfig.GetLogDir(), self.name)
           else:
               filename = self.name
           
           fh = Log.RotatingFileHandler(filename,"a",
                                        self.options.logfilesize,
                                        self.options.numlogfiles)
                                        
           fh.setFormatter(Log.GetFormatter())
           self.fhLoggerLevels = Log.HandleLoggers(fh, Log.GetDefaultLoggers())
           self.fhLoggerLevels.SetLevel(Log.DEBUG)
           self.fhLoggerLevels.SetLevel(Log.WARN, Log.RTPSensor)
           self.loggerLevels = self.fhLoggerLevels

           # Send the log in memory to stream (debug) or file handler.
       if self.options.debug or int(self.preferences.GetPreference(Preferences.LOG_TO_CMD)):
          Log.mlh.setTarget(Log.defStreamHandler)
       else:
          Log.mlh.setTarget(fh)
       Log.mlh.close()
       Log.RemoveLoggerLevels(Log.memLevels,Log.GetLoggers())

       self.__SetLogPreference()

       # Check if machine clock is synchronized.
       self.__CheckForInvalidClock()

       return argvResult

    def __SetLogPreference(self):
        """
        Set correct log level for each log category according
        to preferences.
        """
        logFiles = Log.GetCategories()
        
        for name in logFiles:
            # Get level from preferences.
            logLevel = int(self.preferences.GetPreference(name))
            fLevels = self.GetFileLogLevels()
            sLevels = self.GetStreamLogLevels()

            # Level for files
            if fLevels:
                fLevels.SetLevel(logLevel, name)
            # Level for streams
            if sLevels:
                sLevels.SetLevel(logLevel, name)
            
    def __CheckForInvalidClock(self):
       """
       Check to see if the local clock is out of synch, a common reason for a
       failed authentication.
       
       This routine loggs a warningString.
       """
       
       timeserver = "ntp-1.accessgrid.org"
       timeout = 0.3
       maxOffset = 10
       
       try:
           serverTime = GetSNTPTime(timeserver, timeout)
       except:
           self.log.exception("Toolkit.__CheckForValidClock: Connection to sntp server at %s failed", timeserver)
           serverTime = None
           
       if serverTime is not None:

           diff = int(time.time() - serverTime)
           absdiff = abs(diff)

           if absdiff > maxOffset:
               
               if diff > 0:
                   direction = "fast"
               else:
                   direction = "slow"
                   
               warningString = ("The machine clock is incorrect on\n" + \
                                "your computer: it is %s seconds %s with respect\n" + \
                                "to the time server at %s.") % \
                                (absdiff, direction, timeserver)

               self.log.warn("Toolkit.__CheckForValidClock: %s" %warningString)
                 
    def ProcessArgs(self, args=None):
       """
       Process toolkit wide standard arguments. Then return the modified
       argv so the app can choose to parse more if it requires that.
       """
       
       if args == None:
           (self.options, ret_args) = self.parser.parse_args()
       else:
           (self.options, ret_args) = self.parser.parse_args(args=args)

       if self.options.version:
           print "Access Grid Toolkit Version: ", GetVersion()
           sys.exit(0)
           
       if self.options.debug or int(self.preferences.GetPreference(Preferences.LOG_TO_CMD)):
           self.streamLoggerLevels = Log.HandleLoggers(Log.defStreamHandler,
                                           Log.GetDefaultLoggers())
           self.streamLoggerLevels.SetLevel(Log.DEBUG)
           # When in debug mode, we'll make the stream the primary handler.
           self.loggerLevels = self.streamLoggerLevels
       else:
           # If not in debug, we only used the StreamHandler before Logging was initialized.
           #    so we don't have a StreamLoggerLevels.  
           self.streamLoggerLevels = None
           
       if self.options.cert:
           self.options.secure = 1
           
       return ret_args

    def AddCmdLineOption(self, option):
        self.parser.add_option(option)

    def GetPreferences(self):
        '''
        Get client preferences. 
        '''
        return self.preferences

    def SetPreferences(self, preferences):
        '''
        Set preferences and save them to configuration file.
        '''
        self.preferences = preferences
        self.preferences.StorePreferences()
            
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
    
    def GetConfigFilename(self):
        """
        """
        return self.GetOption("configfilename")
    
    def GetLog(self):
        """
        Return a toolkit wide log.
        """
        return self.log

    def GetLogLevels(self):
        """
        Return the primary loggingLevels object.
          in debug mode: self.streamLoggerLevels
          otherwise:     self.fhLoggerLevels

        Should be called after initialization.
        Levels can be set like this:
            ll = GetFileLevels()
            ll.SetLevel(Log.DEBUG)
        and tuned like this:
            ll.SetLevel(Log.WARN, Log.Hosting)
        """
        return self.loggerLevels

    def GetFileLogLevels(self):
        """
        Return the loggingLevels object for the current log file.
        """
        return self.fhLoggerLevels

    def GetStreamLogLevels(self):
        """
        Return the loggingLevels object for the current output stream.
        Returns None when not in debug mode.
        """
        return self.streamLoggerLevels

    def GetToolkitConfig(self):
        return self.agtkConfig

    def GetUserConfig(self):
        return self.userConfig

    def GetDefaultSubject(self):
        subject = None
        return subject

#    def GetCertificateManager(self):
#       return self.certificateManager

    def GetHostname(self):
        return self.systemConfig.GetHostname()
        
    def FindConfigFile(self, configFile):
        """
        Locate given file in configuration directories:
        first check user dir, then system dir;
        return None if not found
        """
        if self.userConfig is None:
            self.userConfig = UserConfig.instance()
            
        pathToFile = os.path.join(self.userConfig.GetConfigDir(), configFile)
        self.log.debug("Looking for: %s", pathToFile)
        if os.path.exists( pathToFile ):
            return pathToFile
        
        pathToFile = os.path.join(self.agtkConfig.GetConfigDir(), configFile)
        self.log.debug("Looking for: %s", pathToFile)
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
    def Initialize(self, name=None, args=None):
       """
       This method sets up everything for reasonable execution.
       At the first sign of any problems it raises exceptions and exits.
       """
       argvResult = AppBase.Initialize(self, name, args=args)
       
       # 5. Initialize Certificate Management
       # This has to be done by sub-classes
#       configDir = self.userConfig.GetConfigDir()
#       self.certificateManager = \
#                               CertificateManager.CertificateManager(configDir)

       # 6. Do one final check, if we don't have a default
       #    Identity we warn them, but they can still request certs.
       #
       self.log.warn("Toolkit initialized with no default identity.")
           
       return argvResult

class CmdlineApplication(Application):
    """
    An application that's going to run without a gui.
    """
    # The singleton
    theAppInstance = None
    
    # The class method for retrieving/creating the singleton
    def instance():
        """
        The interface for getting the one true instance of this object.
        """
        if CmdlineApplication.theAppInstance == None:
            CmdlineApplication()
         
        return CmdlineApplication.theAppInstance
      
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
        """
        The application constructor that enforces the singleton pattern.
        """
        Application.__init__(self)
       
        if CmdlineApplication.theAppInstance is not None:
            raise Exception, "Only one instance of Application is allowed"
       
        # Create the singleton instance
        CmdlineApplication.theAppInstance = self
#        self.certMgrUI = CertificateManager.CertificateManagerUserInterface()

class WXGUIApplication(Application):
    def __init__(self):
        Application.__init__(self)
#        from AccessGrid.Security.wxgui import CertificateManagerWXGUI
#        self.certMgrUI = CertificateManagerWXGUI.CertificateManagerWXGUI()

        # Register .agpkg mime type
        if not IsWindows():
            agpmFile = os.path.join(AGTkConfig.instance().GetBinDir(),
                                    "agpm.py")
            agpmCmd = agpmFile + " --package %f"
            MimeConfig.instance().RegisterMimeType(
                "application/x-ag-pkg",
                ".agpkg", "agpkg file",
                "Access Grid Package",
                [ ("agpm.py", agpmCmd, "open") ] )

        # Register .vv2d
        if not IsWindows():
            vcFile = os.path.join(AGTkConfig.instance().GetBinDir(),
                                  "GoToVenue.py")
            vcCmd = vcFile + " --file %f"
            MimeConfig.instance().RegisterMimeType(
                "application/x-ag-venueclient",
                ".vv2d",
                "AG Virtual Venues File",
                "Access Grid Virtual Venue Description",
                [ ("GoToVenue.py", vcCmd, "Open") ] )

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

#     def _CheckRequestedCert(self, dn):
#         """
#         Check to see if we have a cert with this dn; if we do not,
#         check to see if there's a request pending for it. If there is,
#         install. Otherwise just return.

#         @param dn: Distinguished name of identity to check for.
        
#         """

#         certMgr = self.certificateManager
#         repo = self.certificateManager.GetCertificateRepository()

#         certs = repo.FindCertificatesWithSubject(dn)
#         validCerts = filter(lambda a: not a.IsExpired(), certs)

#         if len(validCerts) > 0:
#             return

#         # No certs found, see if we have a request for this one.
#         pending = certMgr.GetPendingRequests()

#         reqs = filter(lambda a: str(a[0].GetSubject()) == dn, pending)
#         if len(reqs) == 0:
#             self.log.info("No requests found")
#             return

#         if len(reqs) > 1:
#             self.log.warn("Multiple requests found, just picking one")
            
#         request, token, server, created = reqs[0]

#         self.log.info("Found request at %s", server)

#         # Check status. Note that if a proxy is required, we
#         # may not be using it. However, underlying library might
#         # set it up if the environment requires it.
#         status = certMgr.CheckRequestedCertificate(request, token, server)
#         success, certText = status
#         if not success:
#             # Nope, not ready.
#             self.log.info("Certificate not ready: %s", certText)
#             return

#         # Success! we can install the cert.
#         certhash = md5.new(certText).hexdigest()
#         tempfile = os.path.join(UserConfig.instance().GetTempDir(), 
# 				"%s.pem" % (certhash))

#         try:
#             try:
#                 fh = open(tempfile, "w")
#                 fh.write(certText)
#                 fh.close()

#                 impCert = certMgr.ImportRequestedCertificate(tempfile)

#                 self.log.info("Successfully imported certificate for %s", 
#                               str(impCert.GetSubject()))

#             except CertificateRepository.RepoInvalidCertificate, e:
#                 msg = e[0]
#                 self.log.warn("The import of your approved certificate failed: %s", msg)

#             except Exception, e:
#                 self.log.exception("The import of your approved certificate failed")

#         finally:
#             os.unlink(tempfile)

    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None, args=None):
        """
        This method sets up everything for reasonable execution.
        At the first sign of any problems it raises exceptions and exits.
        """
        argvResult = AppBase.Initialize(self, name, args=args)

        self.log.info("Service init: have profile %s", self.options.profile)

        # Deal with the profile if it was passed instead of cert/key pair
        if self.options.profile is not None:
            self.profile = ServiceProfile()
            if not self.options.profile.endswith(".profile"):
                profile = self.options.profile + ".profile"
            else:
                profile = self.options.profile

            if os.path.dirname(profile) == '':
                # There is no directory
                profPath = os.path.join(self.userConfig.GetServicesDir(),
                                       profile)
            else:
                profPath = profile

            self.profile.Import(profPath)

        # 5. Initialize Certificate Management
        # This has to be done by sub-classes
#        configDir = self.userConfig.GetConfigDir()
#        certMgr = self.certificateManager = \
#                  CertificateManager.CertificateManager(configDir)

#        self.log.info("Initialized cert mgmt.")

        # 6. Do one final check, if we don't have a default
        #    Identity we bail, there's nothing useful to do.

        if self.GetDefaultSubject() is None:
            self.log.error("Toolkit initialized with no default identity.")

        self.log.info("Service Initialization Complete.")
        
        return argvResult


def GetDefaultSubject():
    try:
        defaultSubj = Service.instance().GetDefaultSubject()
    except:
        try:
            defaultSubj = Application.instance().GetDefaultSubject()
        except:
            # If these calls all fail, things that need the default
            #   subject will fail.
            defaultSubj = CmdlineApplication.instance().GetDefaultSubject()

    return defaultSubj

