#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     Support for PersonalNode startup on Windows.
# Created:     2002/12/12
# RCS-ID:      $Id: PersonalNode.py,v 1.5 2004-03-16 03:28:05 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Classes for managing the startup and synchronization of the components
of a Personal Node.

"""

__revision__ = "$Id: PersonalNode.py,v 1.5 2004-03-16 03:28:05 judson Exp $"
__docformat__ = "restructuredtext en"

import os
import threading
import urlparse
import re

import win32api
import win32event
import win32process
import win32con
import _winreg

from AccessGrid.Platform.Config import AGTkConfig
from AccessGrid.Platform.ProcessManager import ProcessManager
from AccessGrid import Log

log = Log.GetLogger(Log.PersonalNode)

NodeServiceURIKey = "NodeServiceURI"
ServiceManagerURIKey = "ServiceManagerURI"

class EventObj:
    def __init__(self, name, create = 0):
        self.name = name
        if create:
            self.eventObj = win32event.CreateEvent(None, 1, 0, name)
        else:
            self.eventObj = win32event.OpenEvent(win32event.EVENT_ALL_ACCESS,
                                                 0, name)

    def GetName(self):
        return self.name
    
    def GetHandle(self):
        return self.eventObj

    def Set(self):
        log.debug("SetEvent on %s", self.name)
        win32event.SetEvent(self.eventObj)

    def Reset(self):
        log.debug("ResetEvent on %s", self.name)
        win32event.ResetEvent(self.eventObj)

    def Wait(self):
        log.debug("Waiting on %s", self.name)
        win32event.WaitForSingleObject(self.eventObj, -1)
        log.debug("Done waiting on %s", self.name)

class PersonalNodeManager:
    def __init__(self, debugMode, progressCallback):
        self.agtkConf = AGTkConfig.instance()
        self.debugMode = debugMode
        self.progressCallback = progressCallback
        self.processManager = ProcessManager()
        self.initEventObjects()

    def Run(self):
        """
        Start the subprocesses, and drop into the interlock sequence.
        """

        #
        # Start processes
        #
        
        self.startServiceManager()
        self.startNodeService()

        #
        # Wait for the service mgr to initialize.
        #

        self.svc_mgr_init.Wait()

        url = readServiceManagerURL()
        self.progressCallback("Started service manager.")

        log.debug("Service manager running at %s", url)
        
        #
        # Now wait for the node service to initialize
        #

        self.node_svc_init.Wait()
        url = readNodeServiceURL()

        log.debug("Node service running at %s", url)
        self.progressCallback("Started node service.")
        
        comps = urlparse.urlparse(url)
        if comps[1] != "":
            #
            # if we parsed properly, and have a hostname, parse it into
            # hostname/port and replace hostname with localhost.
            #
            # TODO: This is a hack that needs to be fixed by the proper
            # setting of GLOBUS_HOSTNAME.
            #

            m = re.match("^([^:]+):(\d+)$", comps[1])
            if m:
                oldhost = m.group(1)
                port = m.group(2)
                log.debug("Parsed name: host='%s' port='%s'", oldhost, port)
                ncomps = list(comps)
                ncomps[1] = "localhost:%s" % (port)
                url = urlparse.urlunparse(ncomps)
                log.debug("Reconstituted url as %s", url)

        return url
        #self.setNodeServiceCallback(url)

        #
        # Okay, we're done!
        #
        # TODO:
        # Kick off a thread to wait for the processes to terminate,
        # and let the user know if they do.
        #

    def startServiceManager(self):

        path = os.path.join(self.agtkConf.GetInstallDir(),
                            "AGServiceManager.py")

        if self.debugMode:
            python = "python"
            dflag = "--debug"
        else:
            python = "pythonw"
            dflag = ""

        arg = "%s --pnode %s %s" % (path,  self.serviceManagerArg, dflag)

        log.debug("Start service manager with %s", arg)

        pinfo = self.processManager.StartProcess(python, arg.split(" "))

        log.debug("info is %s", pinfo)
        self.serviceManagerPInfo = pinfo

    def startNodeService(self):
        path = os.path.join(self.agtkConf.GetInstallDir(),
                            "AGNodeService.py")

        if self.debugMode:
            python = "python"
            dflag = "--debug"
        else:
            python = "pythonw"
            dflag = ""

        arg = "%s --pnode %s %s" % (path, self.nodeServiceArg, dflag)

        log.debug("Start node service with %s", arg)

        pinfo = self.processManager.StartProcess(python, arg.split(" "))

        log.debug("info is %s", pinfo)

        self.nodeServicePInfo = pinfo

    def Stop(self):
        """
        Stop the subprocesses.

        We do this by signalling the terminate event objects, and waiting
        a bit. If they don't die, then call TerminateProcess.

        """

        log.debug("Stop node service")
        self.node_svc_term.Set()
        rc = win32event.WaitForSingleObject(self.nodeServicePInfo[0], 1000)
        log.debug("Wait returns %d", rc)

        log.debug("Stop svc mgr")
        self.svc_mgr_term.Set()
        rc = win32event.WaitForSingleObject(self.serviceManagerPInfo[0], 1000)
        log.debug("Wait returns %d", rc)

    def initEventObjects(self):
        for obj in ['svc_mgr_init',
                    'svc_mgr_term',
                    'svc_mgr_node_svc_synch',
                    'node_svc_init',
                    'node_svc_term']:
            name = "AG_" + obj

            eobj = EventObj(name, create = 1)
            setattr(self, obj, eobj)

        # OK, OK, so this isn't initializing event objects but it is sort
        # of related.
        myid = win32api.GetCurrentProcessId()

        self.nodeServiceArg = "AG_node_svc_init:AG_svc_mgr_node_svc_synch:AG_node_svc_term:%s"  % (myid)
        self.serviceManagerArg = "AG_svc_mgr_init:AG_svc_mgr_node_svc_synch:AG_svc_mgr_term:%s" % (myid)

class PN_NodeService:
    def __init__(self, terminateCallback):
        self.terminateCallback = terminateCallback

    def RunPhase1(self, initArg):
        """
        First part of initialization.

        Returns the URL to the service manager.
        """
        try:
            (init, synch, term, self.parentPID) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_NodeService: %s", initArg)
            log.exception("Invalid argument to PN_NodeService: %s", initArg)
            raise e

        self.initEvent = EventObj(init)
        self.synchEvent = EventObj(synch)
        self.termEvent = EventObj(term)

        #
        # Start the interlock protocol.
        #

        self.synchEvent.Wait()
        url = readServiceManagerURL()
        log.debug("Node service: synch wait completes with url %s", url)

        return url

    def RunPhase2(self, myURL):
        """
        Second part of initialization.

        myURL is the handle for our node service.

        """
        writeNodeServiceURL(myURL)

        log.debug("signalling node svc event")
        self.initEvent.Set()

        #
        # Get the process handle for the parent
        #
        self.hParent = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,
                                            0, int(self.parentPID))
        log.debug("got parent handle %s", self.hParent)
        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEndMult)
        self.thread.start()

    def waitForEnd(self):
        log.debug("Waiting for termination")

        # self.termEvent.Wait()
        ret = win32event.WaitForSingleObject(self.hParent, -1)
        log.debug("Terminating ret=%s", ret)
        self.terminateCallback()

    def waitForEndMult(self):
        log.debug("Waiting for termination")

        hlist = (self.hParent, self.termEvent.GetHandle())

        ret = win32event.WaitForMultipleObjects(hlist, 0, win32event.INFINITE)

        if ret == 0:
            log.debug("NS: Terminating due to parent death")
        elif ret == 1:
            log.debug("NS: Terminating due to signal on term event")
        else:
            log.debug("NS: Other return: %s", ret)

        log.debug("NS: Terminating")
        deleteNodeServiceURL()
        self.terminateCallback()

class PN_ServiceManager:
    def __init__(self, url, terminateCallback):
        self.serviceMgrURL = url
        self.terminateCallback = terminateCallback

    def Run(self, initArg):
        try:
            (init, synch, term, parentPID) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_ServiceManager: %s", initArg)
            log.exception("Invalid argument to PN_ServiceManager: %s", initArg)
            raise e

        self.initEvent = EventObj(init)
        self.synchEvent = EventObj(synch)
        self.termEvent = EventObj(term)

        #
        # Start the interlock protocol.
        #

        myURL = self.serviceMgrURL
        writeServiceManagerURL(myURL)
        log.debug("signalling synch event")
        self.initEvent.Set()
        self.synchEvent.Set()
    
        #
        # Get the process handle for the parent
        #

        self.hParent = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,
                                            0, int(parentPID))
        log.debug("got parent handle %s", self.hParent)

        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEndMult)
        self.thread.start()

    def waitForEnd(self):
        log.debug("Waiting for termination")
        self.termEvent.Wait()
        log.debug("Terminating")
        self.terminateCallback()

    def waitForEndMult(self):
        log.debug("Waiting for termination")

        hlist = (self.hParent, self.termEvent.GetHandle())

        ret = win32event.WaitForMultipleObjects(hlist, 0, win32event.INFINITE)

        if ret == 0:
            log.debug("SM: Terminating due to parent death")
        elif ret == 1:
            log.debug("SM: Terminating due to signal on term event")
        else:
            log.debug("SM: Other return: %s", ret)

        log.debug("SM: Terminating")
        deleteServiceManagerURL()
        self.terminateCallback()

def readServiceManagerURL():
    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, AGTkConfig.AGTkRegBaseKey)
    (val, type) = _winreg.QueryValueEx(k, ServiceManagerURIKey)
    k.Close()
    return str(val)

def writeServiceManagerURL(url):
    k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                          AGTkConfig.AGTkRegBaseKey)
    _winreg.SetValueEx(k, ServiceManagerURIKey, 0, _winreg.REG_SZ, url)
    k.Close()

def deleteServiceManagerURL():
    try:
        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            AGTkConfig.AGTkRegBaseKey,
                            0, _winreg.KEY_ALL_ACCESS)
        _winreg.DeleteValue(k, ServiceManagerURIKey)
        
    except EnvironmentError:
        #
        # It's okay for this to fail.
        #
        log.exception("Ignoring exception on deleteServiceManagerURL()")
    
    k.Close()


def readNodeServiceURL():
    k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, AGTkConfig.AGTkRegBaseKey)
    (val, type) = _winreg.QueryValueEx(k, NodeServiceURIKey)
    k.Close()
    return str(val)

def writeNodeServiceURL(url):
    k = _winreg.CreateKey(_winreg.HKEY_CURRENT_USER,
                          AGTkConfig.AGTkRegBaseKey)
    _winreg.SetValueEx(k, NodeServiceURIKey, 0, _winreg.REG_SZ, url)
    k.Close()
    
def deleteNodeServiceURL():
    try:
        k = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                            AGTkConfig.AGTkRegBaseKey,
                            0, _winreg.KEY_ALL_ACCESS)
        _winreg.DeleteValue(k, NodeServiceURIKey)
    except EnvironmentError:
        #
        # It's okay for this to fail.
        #
        log.exception("Ignoring exception on deleteServiceManagerURL()")
    
    k.Close()

    
if __name__ == "__main__":
    log = Log.GetLogger(Log.PersonalNode)
    slh = Log.StreamHandler()
    levelHandler = Log.HandleLoggers(slh, Log.GetDefaultLoggers())

    def progress(status):
        print "PROGRESS CALLBACK: ", status

    pm = PersonalNodeManager(1, progress)
    pm.Run()
        
