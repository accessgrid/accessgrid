#-----------------------------------------------------------------------------
# Name:        Toolkit.py
# Purpose:     Toolkit-wide initialization and state management.
# Created:     2003/05/06
# RCS-ID:      $Id: Toolkit.py,v 1.20 2004-03-12 20:51:39 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: Toolkit.py,v 1.20 2004-03-12 20:51:39 judson Exp $"

# Standard imports
import os
import sys
import getopt

from optik import OptionParser

# AGTk imports
from AccessGrid import Log
from AccessGrid.Security import CertificateManager
from AccessGrid.Platform.Config import AGTkConfig, GlobusConfig
from AccessGrid.Platform.Config import SystemConfig, UserConfig

class Application:
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
       if Application.theAppInstance is not None:
          raise Exception, "Only one instance of Application is allowed"
       
       # Create the singleton instance
       Application.theAppInstance = self

       self.parser = None
       self.certMgrUI = None
       self.log = None
       self.debugLevel = 0
       self.userConfig = None
       self.agtkConfig = None
       self.globusConfig = None
       
    # This method implements the initialization strategy outlined
    # in AGEP-0112
    def Initialize(self, argv=[''], name=None):
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

       if self.name is not None:
           if not self.name.endswith(".log"):
               self.name = self.name + ".log"
               
           filename = os.path.join(self.userConfig.GetConfigDir(), self.name)
           fh = Log.FileHandler(filename)
       else:
           fh = self.defLogHandler
           
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
       
       # 6. Initialize Certificate Management
       # This has to be done by sub-classes
       configDir = self.userConfig.GetConfigDir()
       self.certificateManager = \
            CertificateManager.CertificateManager(configDir, self.certMgrUI)

       self.GetCertificateManager().GetUserInterface().InitGlobusEnvironment()

       # 7. Do one final check, if we don't have a default
       #    Identity we bail, there's nothing useful to do.

       if self.GetDefaultIdentityDN() is None:
           log.error("Toolkit initialized with no default identity.")
           log.error("Exiting because there's no default identity.")
           sys.exit(-1)
           
       return argvResult

    def ProcessArgs(self):
       """
       Process toolkit wide standard arguments. Then return the modified
       argv so the app can choose to parse more if it requires that.
       """
       if self.parser == None:
           self.parser = OptionParser()
           
       self.parser.add_option("-d", "--debug", action="store_true", dest="debug",
                              default=0,
                              help="Set the debug level of this program.")
       self.parser.add_option("-l", "--logfile", dest="logfilename",
                              metavar="LOGFILE", default=None,
                              help="Specify a log file to output logging to.")
       self.parser.add_option("-c", "--configfile", dest="configfilename",
                              metavar="CONFIGFILE", default=None,
                              help="Specify a configuration file for the program.")


       (self.options, args) = self.parser.parse_args()

       return args

    def SetOptionParser(self, parser):
        self.parser = parser
    
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

    def GetCertificateManager(self):
       return self.certificateManager

    def GetCertMgrUI(self):
       return self.certMgrUI
   
    def GetDefaultIdentityDN(self):
        ident = self.certificateManager.GetDefaultIdentity()
        if ident is None:
            return None
        else:
            return str(ident.GetSubject())

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

# class ServiceApplicationWithIdentity:
#     """
#     An application that's going to run as a service.

#     This implies no graphical UI, and that the identity cert and key are
#     explicitly specified.
#     """

#     def __init__(self, cert, key):
#         Application.__init__(self)

#         self.cert = cert
#         self.key = key
        
#         userInterface = CertificateManager.CertificateManagerUserInterface()
#         self.certificateManager = \
#             CertificateManager.CertificateManager(self.userConfigDir,
#                                                   userInterface,
#                                                   identityCert = self.cert,
#                                                   identityKey = self.key)
        
