#-----------------------------------------------------------------------------
# Name:        Log.py
# Purpose:     Manage toolkit wide logging.
#
# Created:     2004/02/20
# Copyright:   (c) 2002-2004
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
AccessGrid Log module
=====================

Enables toolkit wide logging.  Described in AGEP-0118.

Depends on python logging module.

Extends the python logging module by:
  - enabling per logger level settings when using multiple outputs,
  - using dynamic lists of logs instead of a static tree structure, and
  - adding two higher detail logging levels.

EXAMPLE:
from AccessGrid import Log
log = Log.GetLogger(Log.VenueClient)
# OR log = Log.GetLogger("TestApp")

hdlr = Log.FileHandler("TestLog.log")
hdlr.setFormatter(Log.GetFormatter())
hdlr.setLevel(Log.DEBUG)
# handle default loggers
level_hdlr = Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
# OR   level_hdlr = Log.LoggerLevels(hdlr, Log.GetDefaultLoggers())

# Set level for all loggers if desired.
level_hdlr.SetLevel(Log.DEBUG)
# Set per component level(s)
level_hdlr.SetLevel(Log.WARN, Log.EventService)

log.debug("Test debug")
log.warn("Test warn")
"""

import logging
import logging.handlers as handlers
import copy

# ---- Logging module Aliases ----
#   i.e. from AccessGrid import Log.handlers
#   (Log.logging is also accessible if something else is needed)
BufferingFormatter = logging.BufferingFormatter
Filter = logging.Filter
Filterer = logging.Filterer
FileHandler = logging.FileHandler
Formatter = logging.Formatter
Handler = logging.Handler
Logger = logging.Logger
LogRecord = logging.LogRecord
PlaceHolder = logging.PlaceHolder
StreamHandler = logging.StreamHandler

# --- Levels ----
CRITICAL=logging.CRITICAL
ERROR=logging.ERROR
WARN=logging.WARN
INFO=logging.INFO
DEBUG=logging.DEBUG           # Added below
# VERBOSE=logging.VERBOSE       # Added below
# HIGHDETAIL=logging.HIGHDETAIL # Added below
NOTSET=logging.NOTSET
                                                                                
def GetHighestLevel():
    return HIGHEST_LEVEL


# ---- Predefined categories ----
AGService = "AGService"
AppDb = "AppDb"
AppMonitor = "AppMonitor"
AuthorizationUI = "AuthorizationUI"
BridgeServer = "BridgeServer"
CertificateManager = "CertificateManager"
CertificateRepository = "CertificateRepository"
CertificateManagerWXGUI = "CertificateManagerWXGUI"
CertificateRequestTool = "CertificateRequestTool"
CertReqService = "CertReqService"
CRSClient = "CRSClient"
DataStoreClient = "DataStoreClient"
DataStore = "DataStore"
DataService = "DataService"
EventService = "EventService"
Hosting = "Hosting"
Platform = "Platform"
ProcessManager = "ProcessManager"
NodeManagementUIClasses = "NodeManagementUIClasses"
NodeSetupWizard = "NodeSetupWizard"
NodeService = "NodeService"
Security = "Security"
Platform = "Platform"
ProxyGen = "ProxyGen"  # Security
pyGlobus = "pyGlobus"

ServiceManager = "ServiceManager"
SharedApplication = "SharedApplication"

TextClient = "TextClient"
SimpleTextProcessor = "SimpleTextProcessor"
TextConnection = "TextConnection"
TextService = "TextService"

Toolkit = "Toolkit"
Types = "Types"
UIUtilities = "UIUtilities"
Utilities = "Utilities"
VenueManagement = "VenueManagement"

VenueClient = "VenueClient"
VenueClientController = "VenueClientController"
VenueClientUIClasses = "VenueClientUIClasses"
VenueClientUI = "VenueClientUI"

VenueServer = "VenueServer"
EventClient = "EventClient"
Logging = "Logging"
# Not Used by default
Usage = "Usage"


# ---- Add Two Higher Log Levels ----

# Verbose Level
logging.VERBOSE = 7
VERBOSE=logging.VERBOSE
logging._levelNames[VERBOSE] = 'VERBOSE'
logging._levelNames['VERBOSE'] = VERBOSE

# since logging module uses levels as hard-coded functions,
#   define a function and add it to the imported logging module.
def verbose_func(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'VERBOSE'.
    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.
    logger.debug("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    if self.manager.disable >= VERBOSE:
        return
    if VERBOSE >= self.getEffectiveLevel():
        apply(self._log, (VERBOSE, msg, args), kwargs)

logging.Logger.verbose = verbose_func

# HighDetail Level
logging.HIGHDETAIL = 3
HIGHDETAIL=logging.HIGHDETAIL
logging._levelNames[HIGHDETAIL] = 'HIGHDETAIL'
logging._levelNames['HIGHDETAIL'] = HIGHDETAIL

# constant to use when setting defaults, and don't want to use NOTSET
HIGHEST_LEVEL=HIGHDETAIL

# since logging module uses levels as hard-coded functions,
#   define a function and add it to the imported logging module.
def highdetail_func(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'HIGHDETAIL'.
    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.
    logger.debug("Houston, we have a %s", "thorny problem", exc_info=1)
    """
    if self.manager.disable >= HIGHDETAIL:
        return
    if HIGHDETAIL >= self.getEffectiveLevel():
        apply(self._log, (HIGHDETAIL, msg, args), kwargs)
                                                                                   
logging.Logger.highdetail = highdetail_func

# constant to use when setting defaults.
HIGHEST_LEVEL=HIGHDETAIL

def GetHighestLevel():
    return HIGHEST_LEVEL

# default loggers to high level of output.  Inputs and outputs to various 
#   handlers can then be set with LoggerLevels object.
logging.root.setLevel(HIGHEST_LEVEL)
# Since we are raising the default level, pyGlobus has debug statements
#    that will complain there's no output file unless we turn it back to normal.
logging.getLogger(pyGlobus).setLevel(WARN)


# ---- Formats ----
_defaultFormatter = Formatter("%(asctime)s %(thread)s %(name)s \
    %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")

# Default Formatter
def GetFormatter():
    return _defaultFormatter

_lowDetailFormatter = Formatter("%(name)-17s %(asctime)s %(levelname)-5s %(message)s", "%x %X")

def GetLowDetailFormatter():
    return _lowDetailFormatter

_usageFormatter = Formatter("\"%(created).0f\",%(asctime)s,%(message)s", "\"%x\",\"%X\"")

def GetUsageFormatter():
    return _usageFormatter


# ---- List of components ----
# Does NOT Need to include all components and can be empty.
# Will optimize if needed.

#_componentNames=[AGService, AppMonitor, AuthorizationUI, BridgeServer , CertificateManager , CertificateRepository , CertificateManagerWXGUI , CertificateRequestTool , CertReqService , CRSClient , DataStoreClient , DataStore , DataService , EventService , ProcessManager , NodeManagementUIClasses , NodeSetupWizard , NodeService , Security , ProxyGen , pyGlobus , ServiceManager , SharedApplication , TextClient , SimpleTextProcessor , TextConnection , TextService , Toolkit , Types , Utilities , VenueManagement , VenueClient , VenueClientController , VenueClientUIClasses , VenueClientUI , VenueServer , EventClient , Logging, Usage]
_componentNames=[]

# Create defaultLoggers
defaultLoggers=copy.copy(_componentNames)
# Don't log Usage in normal log by default.
if Usage in defaultLoggers:
    defaultLoggers.remove(Usage)

# Get the list that stores dynamically defined or predefined default loggers.
def GetDefaultLoggers():
    return defaultLoggers


# ---- Global lists ----

# dictionary (keyed on handler) of all LoggerLevels objects.
#   each output handler can only have one LoggerLevels object.
#   Needed if a logger is added that wasn't predefined.
_loggerLevels = {}

# Default initial levels for each logger.  Handlers will use the
#   highest level if not specified here or in the individual file.
_defaultLevels = {}
# _defaultLevels[EventService] = WARN
# Most default levels are usually set in individual files like this:
# Log.SetDefaultLevel(Log.EventService, Log.WARN)

# Get the default levels for a logger.
def GetDefaultLevel(name):
    if name in _defaultLevels.keys():
        return _defaultLevels[name]
    else:
        return NOTSET

# Set the default levels for a logger.
def SetDefaultLevel(name, level):
    # Make sure the level is a valid type
    if type(level) == type(CRITICAL):
        global _defaultLevels
        _defaultLevels[name] = level
    else:
        logging.getLogger(Logging).error("Invalid level type: " + str(type(level)) )


# ---- Main Additional Functions and Classes ----

# Shorthand/user-friendly way to handle loggers (create LoggerLevels)
def HandleLoggers(hdlr, loggerNamesList=defaultLoggers, handleDefaults=1, defaultLoggerList=defaultLoggers):
    return LoggerLevels(hdlr, loggerNamesList, handleDefaults, defaultLoggerList)

# similar to logging.getLogger, but make sure it's handled by default.
#  The defaultHandled flag is normally set to 1 (True) in order to send 
#    input logger's output to any output handlers that expect to handle
#    new loggers that were not predefined.
#  defaultLoggerList is just in case you want to manage multiple lists.
def GetLogger(name, defaultHandled=1, defaultLoggerList=defaultLoggers):
    logger = logging.getLogger(name)
    # If we want to send this logger's output to things handling new
    #   "default" loggers.
    if defaultHandled:
        #   Can only adjust levels of highest parent to avoid handling
        #     the same input twice (if AG.b.c, only add AG)
        parentName = name.split(".")[0]
        # Add to default inputs of not already there.
        if parentName not in defaultLoggerList:
            defaultLoggerList.append(parentName)
            # Add to previously created level handlers
            for lgr_lvl in _loggerLevels:
                # Check if each wants to handle new loggers by default.
                if _loggerLevels[lgr_lvl].handleDefaults:
                    _loggerLevels[lgr_lvl]._handleLogger(parentName)
    return logger

# Contains multiple input LevelHandlers
#   and usually a single output handler.
class LoggerLevels:
    # Allows setting separate levels for each input logger
    #   Contains a list of inputs, a buffering handler for
    #    each one (to set their level), and an ouput (or many outputs).
    # Needs a list of inputs and an output
    # Use default logger list, override if using many lists.
    def __init__(self, handler, loggerNamesList, handleDefaults=1, defaultLoggerList=defaultLoggers):
        # if using default list, and handleDefaults flag was not set to false.
        if loggerNamesList == defaultLoggerList and handleDefaults == 1:
            # Automatically log entries from any new loggers that were not
            #  originally defined.
            self.handleDefaults = 1
        else:
            # not using default list or handleDefaults was explicitly set to false.
            self.handleDefaults = 0
        self.loggerNamesList = copy.copy(loggerNamesList) # Mostly informational
        self.levelHandlers={}   # dict by input logger name
        self.outputHandlers=[]  # usually only one output
        self.defaultLevel = HIGHEST_LEVEL
        for name in loggerNamesList:
            lhdlr = LevelHandler(handler)
            if GetDefaultLevel(name) != NOTSET:
                lhdlr.level = GetDefaultLevel(name)
            else:
                lhdlr.level = self.defaultLevel
            logging.getLogger(name).addHandler(lhdlr)
            self.levelHandlers[name] = lhdlr
            lhdlr.addHandler(handler)

        self.outputHandlers.append(handler)
        # Keep track of instances globally in case new loggers are created.
        _loggerLevels[handler] = self

    # Set the level of a logger.
    # inputLoggerNames argument can be a list or a single name.
    def SetLevel(self, level, inputLoggerName=None):
        # Make sure the level is a valid type
        if type(level) == type(CRITICAL):
            self.defaultLevel = level
        else:
            logging.getLogger(Logging).error("Invalid level type: " + str(type(level)) )
            return

        # Handle list or name
        if type(inputLoggerName) == type([]): 
            inputLoggerNameList = inputLoggerName
        else:
            inputLoggerNameList = [inputLoggerName]

        for loggerName in inputLoggerNameList:
            # if no name is used, set the level for all inputs.
            if loggerName == None:
                for name in self.levelHandlers:
                    self.levelHandlers[name].SetLevel(level)
            elif loggerName in self.levelHandlers.keys():
                # exists, just set the level.
                self.levelHandlers[loggerName].SetLevel(level)
            else:
                # doesn't exist here yet. (not a common occurrence)
                #   can happen when input logger is not predefined.
    
                # handle new input logger
                self._handleLogger(loggerName)
                # and set the level.
                self.levelHandlers[loggerName].SetLevel(level)

    # Add this as one of the input loggers that is handled.
    # Usually only called when an input logger has been created 
    #    that wasn't predefined.
    def _handleLogger(self, inputLoggerName):
        if inputLoggerName not in self.levelHandlers.keys():
            # self shouldn't exist without an entry in self.outputHandlers.
            self.levelHandlers[inputLoggerName] = LevelHandler(self.outputHandlers[0])            # skip the first element that was just added.
            for h in self.outputHandlers[1:]:
                self.levelHandlers[inputLoggerName].addHandler(h)
            self.levelHandlers[inputLoggerName].SetLevel(self.defaultLevel)
            GetLogger(inputLoggerName).addHandler(self.levelHandlers[inputLoggerName])
            self.loggerNamesList.append(inputLoggerName) # Mostly informational.

# A middle layer -- an in-between handler that allows levels to be set on
#    inputs specific to each output when using multiple outputs.
# Don't allow its creation without a handler -- to ensure that
#   no log messages are getting through without being handled.
class LevelHandler(logging.handlers.BufferingHandler):
    def __init__(self, handler, level=HIGHEST_LEVEL):
        if not handler:
            GetLogger(Logger).error("LevelHandler requires a handler argument")
        # Not too concerned about a buffer for the handler.
        #   We just need a handler to redirect output.
        logging.handlers.BufferingHandler.__init__(self, capacity=1)
        self.level=level
        # output handlers, typically only one will be here.
        self.handlers = []
        self.handlers.append(handler)

    # Override parent class flush
    def flush(self):
        for h in self.handlers:
            for record in self.buffer:
                if record.levelno >= h.level:
                    h.handle(record)
        # Don't clear if nothing handled it.
        if len(self.handlers) > 0:
            self.buffer=[]

    # add output handler (usually only one)
    def addHandler(self, handler):
        if handler not in self.handlers:
            self.handlers.append(handler)

    def SetLevel(self, level):
        if type(level) == type(CRITICAL):
            self.level=level
        else:
            logging.getLogger(Logging).error("Invalid level type: " + str(type(level)) )
            return

        # Make sure handler is accepting at this level or with more detail.
        for handler in self.handlers:
            if handler.level > level: # closer to zero means more detail
                handler.setLevel(level)



# 0. Initialize logging, storing in log data memory
defLogHandler = StreamHandler()
defLogHandler.setFormatter(GetFormatter())
mlh = handlers.MemoryHandler(16384, flushLevel=ERROR, target=defLogHandler)
mlh.setFormatter(GetFormatter())
memLevels = HandleLoggers(mlh, GetDefaultLoggers())
memLevels.SetLevel(DEBUG)
                                                                                

