#-----------------------------------------------------------------------------
# Name:        PersonalNodeLinux.py
# Purpose:     Support for PersonalNode startup on Linux.
#
# Author:      Robert Olson
#
# Created:     2002/12/12
# RCS-ID:      $Id: PersonalNodeLinuxExt.py,v 1.2 2003-08-20 13:05:07 judson Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Classes for managing the startup and synchronization of the components
of a Personal Node.

This is the Linux (well, nonWindows) version. It uses SysV message
queues via the pyipc module to synchronize the service and app startup.

"""

import sys
import time
import os
import signal
import threading
import urlparse
import re
import tempfile
import pyipc
import errno

import logging

from AccessGrid import Platform

log = logging.getLogger("AG.PersonalNodeLinux")

class MQ_CannotAccess(Exception):
    pass

class MQ_OutOfQueues(Exception):
    pass

class MQ_NoQueueAvailable(Exception):
    pass

class MessageQueue:
    """
    Simple wrapper around pyipc.MessageQueue.
    """
    
    def __init__(self, name, key, create = 0):
        self.name = name
        self.key = key

        if create:

            self.__create()

        else:
            self.__get()

        log.debug("created message queue key=%s name=%s", key, name)

    def __create(self):
        """
        Helper for the constructor.

        Create a new message queue.

        """
        
        try:
            self.mq = pyipc.MessageQueue(key, 0600 | pyipc.IPC_CREAT | pyipc.IPC_EXCL)
        except EnvironmentError, e:

            #
            # Handle the various failure modes we might hit.
            #

            log.debug("MQ Create: Handling errno %s %s",
                      e.errno, errno.errorcode[e.errno])
            
            if e.errno == errno.EACCES:
                #
                # Message queue exists, but we don't have permission
                #
                # This is difficult. Best to raise an error
                # that will cause the caller to retry with a different
                # key.
                #
                raise MQ_CannotAccess

            elif e.errno == errno.EEXIST:
                #
                # The message queue already exists. This is also
                # a strange error, as we thought we were
                # creating unique message queue.
                #
                # Handle this by attempting to attach to the queue
                # and clear out any messages that might be in it.
                #

                self.__connectAndClear()

            elif e.errno == errno.EIDRM:
                #
                # Marked for removal .. ?
                #

                raise e

            elif e.errno == errno.ENOENT:
                #
                # we shouldn't see this, as we passed IPC_CREAT (!)
                raise e
            
            elif e.errno == errno.ENOMEM:
                #
                # Ack, fatal, no memory. reraise.
                #

                raise e

            elif e.errno == errno.ENOSPC:
                # 
                # This is likely the common one.
                #
                # We've hit the (low by default) systemwide limit
                # on the number of message queues.
                #
                # There's not much we can do here except try
                # possibly to clear them out.
                # However, we can't do that here as we may be in
                # the middle of creating a whole block of
                # message queues. Hence, all we do where is
                # raise the MQ_OutOfQueues exception, to be caught
                # further up.
                #

                raise MQ_OutOfQueues
            
    def __connectAndClear(self):
        #
        # Get the message queue for this key, and
        # read all the messages out of it (if any).
        #

        self.__get()

        while 1:
            d = self.mq.receive(flags = pyipc.IPC_NOWAIT)
            
            if d is None:
                log.debug("__connectAndClear: done")
                break
            else:
                log.debug("__connectAndClear: got msg of len %s", len(d))
                
    def __get(self):

        try:
            self.mq = pyipc.MessageQueue(self.key, 0600)

            if e.errno == errno.EACCES:
                #
                # Message queue exists, but we don't have permission
                #
                # This is difficult. Best to raise an error
                # that will cause the caller to retry with a different
                # key.
                #
                raise MQ_CannotAccess

            elif e.errno == errno.EEXIST:
                #
                # We should not get this, as we did not assert
                # CREAT and EXCL
                #

                log.exception("Bizarre error: received EEXIST when CREAT and EXCL not asserted")
                raise e

            elif e.errno == errno.EIDRM:
                #
                # Marked for removal .. ?
                #

                raise e

            elif e.errno == errno.ENOENT:
                #
                # Aie, this is a protocol problem. The message queue
                # should already exist here.
                #
                raise MQ_NoQueueAvailable
            
            elif e.errno == errno.ENOMEM:
                #
                # Ack, fatal, no memory. reraise.
                #

                raise e

            elif e.errno == errno.ENOSPC:
                # 
                # We also shouldn't hit this here, as the
                # queue should have been created elsewhere; we are just
                # binding to it here.
                #

                raise MQ_NoQueueAvailable

    def send_p(self, msg):
        log.debug("send_p: queue=%s msg=%s", self.name, msg)
        return self.mq.send_p(msg)
            
    def receive_p(self):
        log.debug("receive_p: queue=%s", self.name)
        ret = self.mq.receive_p(flags = 0)
        log.debug("receive_p: queue=%s got %s", self.name, ret)
        return ret[1]

    def getKey(self):
        return self.key

    def destroy(self):
        pyipc.removeIPC(self.mq)
        self.mq = None

class PersonalNodeManager:
    def __init__(self, setNodeServiceCallback, debugMode):
        self.setNodeServiceCallback = setNodeServiceCallback
        self.debugMode = debugMode

        self.initMessageQueues()

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

        url = self.svc_mgr_init.receive_p()

        self.svc_mgr_init.destroy()

        log.debug("Service manager running at %s", url)

        #
        # Now wait for the node service to initialize
        #

        url = self.node_svc_init.receive_p()

        log.debug("Node service running at %s", url)

        self.node_svc_init.destroy()

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

        self.setNodeServiceCallback(url)

        #
        # Okay, we're done!
        #
        # TODO:
        # Kick off a thread to wait for the processes to terminate,
        # and let the user know if they do.
        #

    def startServiceManager(self):

        path = os.path.join(Platform.GetInstallDir(), "AGServiceManager.py")

        python = sys.executable
        if self.debugMode:
            dflag = "--debug"
        else:
            dflag = ""

        args = [python, path, "--pnode", self.serviceManagerArg]
        if dflag != "":
            args.append(dflag)

        log.debug("Start service manager with %s", args)

        pinfo = os.spawnvp(os.P_NOWAIT, python, args)

        print "info is ", pinfo
        self.serviceManagerPInfo = pinfo

    def startNodeService(self):
        path = os.path.join(Platform.GetInstallDir(), "AGNodeService.py")

        python = sys.executable
        if self.debugMode:
            dflag = "--debug"
        else:
            dflag = ""

        args = [python, path, "--pnode", self.nodeServiceArg]
        if dflag != "":
            args.append(dflag)

        log.debug("Start node service with %s", args)

        pinfo = os.spawnvp(os.P_NOWAIT, python, args)

        print "info is ", pinfo
        self.nodeServicePInfo = pinfo
                                           

    def Stop(self):
        """
        Stop the subprocesses.

        We do this by signalling the terminate event objects, and waiting
        a bit. If they don't die, then call TerminateProcess.

        """

        log.debug("Stop node service")
        self.node_svc_term.send_p("quit")

        log.debug("Stop svc mgr")
        self.svc_mgr_term.send_p("quit")

        log.debug("Wait for node service %s to die", self.nodeServicePInfo)
        ensureProcessDead(self.nodeServicePInfo)

        log.debug("Wait for service manager %s to die", self.serviceManagerPInfo)
        ensureProcessDead(self.serviceManagerPInfo)

        self.node_svc_term.destroy()
        self.svc_mgr_term.destroy()

    def initMessageQueues(self):
        """
        Create the message queues used to communicate between
        the venue client and the service mgrs.

        We create a tempfile that we then use with ftok to create
        a unique name for the message queues.

        """

        tfile = tempfile.mktemp()
        fp = open(tfile, "w")
        fp.close()

        idx = 0
        
        for obj in ['svc_mgr_init',
                    'svc_mgr_term',
                    'svc_mgr_node_svc_synch',
                    'node_svc_init',
                    'node_svc_term']:
            
            key = pyipc.ftok(tfile, idx)
            idx += 1

            eobj = MessageQueue(obj, key, create = 1)
            setattr(self, obj, eobj)

        os.unlink(tfile)

        self.nodeServiceArg = "%s:%s:%s" % (self.node_svc_init.getKey(),
                                            self.svc_mgr_node_svc_synch.getKey(),
                                            self.node_svc_term.getKey())

        self.serviceManagerArg = "%s:%s:%s" % (self.svc_mgr_init.getKey(),
                                               self.svc_mgr_node_svc_synch.getKey(),
                                               self.svc_mgr_term.getKey())
        

class PN_NodeService:
    def __init__(self, terminateCallback):
        self.terminateCallback = terminateCallback


    def RunPhase1(self, initArg):
        """
        First part of initialization.

        Returns the URL to the service manager.
        """

        try:
            (init, synch, term) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_NodeService: %s", initArg)
            log.exception("Invalid argument to PN_NodeService: %s", initArg)
            raise e

        self.initEvent = MessageQueue("init", int(init))
        self.synchEvent = MessageQueue("synch", int(synch))
        self.termEvent = MessageQueue("term", int(term))

        #
        # Start the interlock protocol.
        #

        url = self.synchEvent.receive_p()
        log.debug("Node service: synch wait completes with url %s", url)

        self.synchEvent.destroy()

        return url

    def RunPhase2(self, myURL):
        """
        Second part of initialization.

        myURL is the handle for our node service.

        """

        log.debug("signalling node svc event")
        self.initEvent.send_p(myURL)

        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEnd)
        self.thread.start()

    def waitForEnd(self):
        log.debug("NS waiting for termination")

        ret = self.termEvent.receive_p()
        log.debug("NS terminating ret=%s", ret)
        self.terminateCallback()

class PN_ServiceManager:
    def __init__(self, getMyURLCallback, terminateCallback):
        self.getMyURLCallback = getMyURLCallback
        self.terminateCallback = terminateCallback

    def Run(self, initArg):
        try:
            (init, synch, term) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_ServiceManager: %s", initArg)
            log.exception("Invalid argument to PN_ServiceManager: %s", initArg)
            raise e

        self.initEvent = MessageQueue("init", int(init))
        self.synchEvent = MessageQueue("synch", int(synch))
        self.termEvent = MessageQueue("term", int(term))


        #
        # Start the interlock protocol.
        #

        myURL = self.getMyURLCallback()
        log.debug("signalling synch event")
        self.initEvent.send_p(myURL)
        self.synchEvent.send_p(myURL)
    
        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEnd)
        self.thread.start()

    def waitForEnd(self):
        log.debug("SM waiting for termination")
        r = self.termEvent.receive_p()
        log.debug("SM terminating, got %s", r)
        self.terminateCallback()


def waitForProcessExit(pid, nTries, waitTime):
    for i in range(nTries):
        try:
            rc = os.waitpid(pid, os.WNOHANG)
            if rc[0] != 0:
                status = rc[1]
                if os.WIFEXITED(status):
                    log.debug("process %s exited with return code %s",
                              pid, os.WEXITSTATUS(status))
                    return 1
                elif os.WIFSIGNALED(status):
                    log.debug("process %s exited from signal %s",
                              pid, os.WTERMSIG(status))
                    return 1

            time.sleep(waitTime)
            
        except OSError, e:
            if e[0] == errno.ECHILD:
                log.debug("process %s was already dead", pid)
                return 1
            else:
                log.exception("Unexpected exception in waitForProcessExit")
                return 1
    return 0

def ensureProcessDead(pid):
    """
    Wait for process pid to die. If we have to wait
    too long, kill it and wait some more. If it doesn't
    want to die, shoot it down with SIGKILL. If it
    still doesn't die, log an error.

    Algorithm:
        for nTries times:
            Probe to see if process has exited.
            If not, wait waitTime seconds
        if process has not exited:
            send pid a SIGKILL
            for nTries times:
                Probe to see if process has exited.
                If not, wait waitTime seconds
            if process has not exited:
                send pid a SIGKILL
                

    """

    exited = waitForProcessExit(pid, 20, 0.1)

    if exited:
        return

    log.debug("sending SIGTERM to %s", pid)
    os.kill(pid, signal.SIGTERM)

    exited = waitForProcessExit(pid, 5, 0.1)

    if exited:
        return
    
    log.debug("sending SIGKILL to %s", pid)
    os.kill(pid, signal.SIGKILL)

    exited = waitForProcessExit(pid, 5, 0.1)

    if exited:
        return

    log.error("Process %s would not die", pid)

if __name__ == "__main__":

    top = logging.getLogger("AG")
    top.setLevel(logging.DEBUG)
    top.addHandler(logging.StreamHandler())

    pid = os.spawnlp(os.P_NOWAIT, "sleep", "sleep", "10")
    print "pid is ", pid

    ensureProcessDead(pid)

    pid = os.spawnlp(os.P_NOWAIT, "date", "date")
    print "pid is ", pid

    ensureProcessDead(pid)

    pid = os.spawnlp(os.P_NOWAIT, "python", "python", "AccessGrid/ignore.py")
    print "pid is ", pid

    ensureProcessDead(pid)
