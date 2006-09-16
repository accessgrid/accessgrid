#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.123 2006-09-16 00:01:17 turam Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Toolkit.py,v 1.123 2006-09-16 00:01:17 turam Exp $"

# Standard imports
import os
import sys
from optparse import OptionParser, Option
import time
import socket

# AGTk imports
from AccessGrid import Log
from AccessGrid.Preferences import Preferences
from AccessGrid.Platform.Config import AGTkConfig, MimeConfig
from AccessGrid.Platform.Config import SystemConfig, UserConfig
from AccessGrid.Platform import IsWindows
from AccessGrid.ServiceProfile import ServiceProfile
from AccessGrid.Version import GetVersion
from AccessGrid.NetUtilities import GetSNTPTime
from AccessGrid.wsdl import SchemaToPyTypeMap
from AccessGrid.Security import ProxyGen
from AccessGrid.Security import CertificateRepository

class MissingDependencyError(Exception): pass

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
        return AppBase.theInstance
       
    instance = staticmethod(instance)
    
    def set_instance(obj):
        AppBase.theInstance = obj
    set_instance = staticmethod(set_instance)
    

    # The real constructor
    def __init__(self):
       """
       The application constructor that enforces the singleton pattern.
       """
       if AppBase.instance():
          raise Exception, "Only one instance of AppBase is allowed; already have instance of %s" % (AppBase.instance().__class__,)

       AppBase.set_instance(self)

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
       self.parser.add_option("--secure", type="int",
                              dest="secure", default=0,
                              help="Specify whether the service uses SSL.")
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
       self.userConfig = None
       self.agtkConfig = None
       self.systemConfig = SystemConfig.instance()
       self.log = None
       self.loggerLevels = None
       self.fhLoggerLevels = None
       
       self._certificateManager = None
       self._certMgrUI = None
       
       # This initializes logging
       self.log = Log.GetLogger(Log.Toolkit)
       self.log.debug("Initializing AG Toolkit version %s", GetVersion())
       self.log.info("Command and arguments: %s" % sys.argv )
       
       self.__context = None
       self.__passphrase = None

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

       # Load client preferences
       self.preferences = Preferences()
       self.ProcessArgsThatUsePreferences()
       
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
           self.fhLoggerLevels.SetLevel(Log.CRITICAL, Log.RTPSensor)
           self.loggerLevels = self.fhLoggerLevels

           # Send the log in memory to stream (debug) or file handler.
       if self.options.debug or int(self.preferences.GetPreference(Preferences.LOG_TO_CMD)):
          Log.mlh.setTarget(Log.defStreamHandler)
       else:
          Log.mlh.setTarget(fh)
       Log.mlh.close()
       Log.RemoveLoggerLevels(Log.memLevels,Log.GetLoggers())

       self.__SetLogPreference()

       self.CheckDependencies()

       # Check if machine clock is synchronized.
       # - Disabled for 3.0: clock-sync is important when using proxy certs, which we're not
       #self.__CheckForInvalidClock()  
            
       self.__context = None
           
       return argvResult
       
    def CheckDependencies(self):
        if not hasattr(socket,'ssl'):
            raise MissingDependencyError("SSL")
	
    def GetPassphrase(self,verifyFlag=0,prompt1="Enter the passphrase to your private key.", prompt2='Verify passphrase:'):

        # note: verifyFlag is unused
        if self.__passphrase:
            return self.__passphrase
        else:
            cb = self.GetCertificateManagerUI().GetPassphraseCallback(prompt1,
                                                                      prompt2)
            p1 = cb(0)
            self.__passphrase = ''.join(p1)
            return self.__passphrase
            
    def GetContext(self):
        if not self.__context:
            from M2Crypto import SSL
            self.__context = SSL.Context('sslv23')
            
            # Hack to allow use of proxy certs, until the necessary 
            # interface is exposed through M2Crypto
            os.environ['OPENSSL_ALLOW_PROXY_CERTS'] = '1'
            
            id = self.GetCertificateManager().GetDefaultIdentity()
            caDir = self.GetCertificateManager().caDir
            if id.HasEncryptedPrivateKey():
                # if the private key is encrypted, we need a proxy certificate
                proxycertfile = self.userConfig.GetProxyFile()
                if not ProxyGen.IsValidProxy(proxycertfile):
                    # if a valid proxy cert does not exist, create one
                    ProxyGen.CreateProxy(self.GetPassphrase,
                                         id.GetPath(),
                                         id.GetKeyPath(),
                                         caDir,
                                         proxycertfile)
                id = CertificateRepository.Certificate(proxycertfile)
            self.__context.load_cert_chain(id.GetPath(),id.GetKeyPath())
            self.__context.load_verify_locations(capath=caDir)
            self.__context.set_verify(SSL.verify_peer,10)
            self.__context.set_session_id_ctx('127.0.0.1:8006')
            self.__context.set_cipher_list('LOW:TLSv1:@STRENGTH')
        return self.__context
        
    def VerifyCallback(self,ok,store):
        # unused, except possibly for debugging
        print 'VerifyCallback: ok,store=',ok,store.get_current_cert().get_subject().as_text(),store.get_error()
        return 1
        
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
           
       if self.options.cert:
           self.options.secure = 1
           
       return ret_args

    def ProcessArgsThatUsePreferences(self):
       """
       Process toolkit wide logging arguments. Then return the modified
       argv so the app can choose to parse more if it requires that.
       """

       if self.options.debug or int(self.preferences.GetPreference(Preferences.LOG_TO_CMD)):
           self.streamLoggerLevels = Log.HandleLoggers(Log.defStreamHandler,
                                           Log.GetDefaultLoggers())
           self.streamLoggerLevels.SetLevel(Log.DEBUG)
           self.streamLoggerLevels.SetLevel(Log.CRITICAL, Log.RTPSensor)
           # When in debug mode, we'll make the stream the primary handler.
           self.loggerLevels = self.streamLoggerLevels
       else:
           # If not in debug, we only used the StreamHandler before Logging was initialized.
           #    so we don't have a StreamLoggerLevels.  
           self.streamLoggerLevels = None

    def AddCmdLineOption(self, option):
        self.parser.add_option(option)
        
    def SetCmdLineDefault(self,option,value):
        if self.parser.defaults.has_key(option):
            self.parser.defaults[option] = value
        else:
            self.log.error('SetCmdLineDefault called with invalid option: %s', option)

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
        ident = self.GetCertificateManager().GetDefaultIdentity()

        if ident is not None:
            from AccessGrid.Security import X509Subject
            subject = X509Subject.CreateSubjectFromString(str(ident.GetSubject()))
        else:
            subject = None

        return subject

    def GetCertificateManager(self):
        if self._certificateManager == None:
            from AccessGrid.Security import CertificateManager
            if self.userConfig == None:
                raise Exception("No user config dir, Toolkit may not be initialized.")
            configDir = self.userConfig.GetConfigDir()
            self._certificateManager = CertificateManager.CertificateManager(configDir)
            self.log.info("Initialized certificate manager.")
            self._certificateManager.InitEnvironment()
        return self._certificateManager

    def GetCertificateManagerUI(self):
        if self._certMgrUI == None:
            # 5. Initialize Certificate Management
            # This has to be done by sub-classes
            from AccessGrid.Security import CertificateManager
            self._certMgrUI = CertificateManager.CertificateManagerUserInterface(self.GetCertificateManager())
            # 6. Do one final check, if we don't have a default
            #    Identity we warn them, but they can still request certs.
            #
            self._certMgrUI.InitEnvironment()

            if self.GetDefaultSubject() is None:
                self.log.error("Toolkit initialized with no default identity.")

            self.log.info("Initialized certificate manager UI.")

        return self._certMgrUI

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
    # The class method for retrieving/creating the singleton
    def instance():
        """
        The interface for getting the one true instance of this object.
        """
        if AppBase.instance() == None:
            Application()

        return AppBase.instance()
      
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
       """
       The application constructor that enforces the singleton pattern.
       """
       AppBase.__init__(self)
       
    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, name=None, args=None):
       """
       This method sets up everything for reasonable execution.
       At the first sign of any problems it raises exceptions and exits.
       """
       argvResult = AppBase.Initialize(self, name, args=args)
       
       # 5. Initialize Certificate Management
       # Now done on first request of GetCertificateManager()

       # 6. Do one final check for default identity
       # Now done on first request of GetCertificateManagerUI()
           
       return argvResult

class CmdlineApplication(Application):
    """
    An application that's going to run without a gui.
    """
    # The class method for retrieving/creating the singleton
    def instance():
        """
        The interface for getting the one true instance of this object.
        """
        obj = AppBase.instance()
        if obj == None:
            CmdlineApplication()
        elif obj.__class__ != CmdlineApplication:
            raise Exception("Attempt to retrieve instance of type %s in presence of existing instance of %s" %
                            (CmdlineApplication,obj.__class__))

        return AppBase.instance()
      
    instance = staticmethod(instance)
    
    # The real constructor
    def __init__(self):
        """
        The application constructor that enforces the singleton pattern.
        """
        Application.__init__(self)
        
       
class WXGUIApplication(Application):

    """
    The interface for getting the one true instance of this object.
    """
    # The class method for retrieving/creating the singleton
    def instance():
        obj = AppBase.instance()
        if obj == None:
            WXGUIApplication()
        elif obj.__class__ != WXGUIApplication:
            raise Exception("Attempt to retrieve instance of type %s in presence of existing instance of %s" %
                            (WXGUIApplication,obj.__class__))

        return AppBase.instance()
      
    instance = staticmethod(instance)
    
    def __init__(self):
        Application.__init__(self)

        # Register .agpkg mime type
        if not IsWindows():
            agpmFile = os.path.join(AGTkConfig.instance().GetBinDir(),
                                    "agpm3.py")
            agpmCmd = agpmFile + " --gui --package %f"
            MimeConfig.instance().RegisterMimeType(
                "application/x-ag3-pkg",
                ".agpkg3", "agpkg file",
                "Access Grid Package",
                [ ("agpm3.py", agpmCmd, "open") ] )

        # Register .vv3d
        if not IsWindows():
            vcFile = os.path.join(AGTkConfig.instance().GetBinDir(),
                                  "GoToVenue3.py")
            vcCmd = vcFile + " --file %f"
            MimeConfig.instance().RegisterMimeType(
                "application/x-ag-venueclient",
                ".vv3d",
                "AG Virtual Venues File",
                "Access Grid Virtual Venue Description",
                [ ("GoToVenue.py", vcCmd, "Open") ] )

    def GetCertificateManagerUI(self):
        if self._certMgrUI == None:
            # 5. Initialize Certificate Management
            from AccessGrid.Security.wxgui import CertificateManagerWXGUI
            self._certMgrUI = CertificateManagerWXGUI.CertificateManagerWXGUI(
                                self.GetCertificateManager())

            # 6. Do one final check, if we don't have a default
            #    identity we warn them, but they can still request certs.
            self._certMgrUI.InitEnvironment()

            if self.GetDefaultSubject() is None:
                self.log.error("Toolkit initialized with no default identity.")

        return self._certMgrUI

class Service(AppBase):
    """
    The service object is one of the top level objects used to
    build new parts of the AGTk. The service object is required to
    be a singleton in any process.
    """
    # The class method for retrieving/creating the singleton
    def instance():
        obj = AppBase.instance()
        if obj == None:
            Service()
        elif obj.__class__ != Service:
            raise Exception("Attempt to retrieve instance of type %s in presence of existing instance of %s" %
                            (Service,obj.__class__))

        return AppBase.instance()
      
    instance = staticmethod(instance)

    # The real constructor
    def __init__(self):
        """
        The application constructor that enforces the singleton pattern.
        """
        AppBase.__init__(self)

        self.profile = None

        # Add cert, key, and profile options
        profileOption = Option("--profile", dest="profile", metavar="PROFILE",
                           help="Specify a service profile.")
        self.AddCmdLineOption(profileOption)


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
        # Now done on first call to GetCertificateManager() and GetCertificagteManagerUI()

        # 6. Do one final check
        # Now done on first call to GetCertificateManagerUI()

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


def GetDefaultApplication():
    return AppBase.instance()
