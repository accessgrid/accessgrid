#-----------------------------------------------------------------------------
# Name:        PersonalNode.py
# Purpose:     Support for PersonalNode startup using unix pipes for synchronization.
#
# Author:      Robert Olson
#
# Created:     2003/05/05
# RCS-ID:      $Id: PersonalNode.py,v 1.1 2004-03-05 16:26:24 eolson Exp $
# Copyright:   (c) 2002-2004
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

"""
Classes for managing the startup and synchronization of the components
of a Personal Node.

This is the Linux (well, nonWindows) version. It uses standard unix pipes
to synchronize the service and app startup.

We can use fewer pipes than we needed for the event-object implementation, as
we can utilize the bidirectional nature of pipes and the detection of their
closure to detect process death.

The protocol is as follows:

VC: Create svc-mgr-pipe, node-svc-pipe, synch-pipe
    Start service mgr, pass svc-mgr-pipe and synch-pipe.write
    Start node mgr, pass node-svc-pipe and synch-pipe.read
    read svc-mgr-url from svc-mgr-pipe
    read node-mgr-url from node-svc-pipe
    go

Node svc:
    init pipes from cmdline
    read svc-mgr-url from synch-pipe.read
    init node svc
    write node svc url to node-svc-pipe
    go

Svc mgr:
    init pipes from cmdline
    init svc mgr
    write svc mgr url to synch-pipe.write
    write svc mgr url to svc-mgr-pipe
    go

"""

__revision__ = "$Id: PersonalNode.py,v 1.1 2004-03-05 16:26:24 eolson Exp $"
__docformat__ = "restructuredtext en"

import sys
import time
import os
import signal
import threading
import urlparse
import re
import errno
import struct
import string

import logging

from AccessGrid.Platform import Platform

log = logging.getLogger("AG.PersonalNode")

class Pipe:
    """
    Simple wrapper for a pipe endpoint, solely for the purposes of this module

    Operations supported are writeURL, readURL, close.

    """

    def __init__(self, readFD = None, writeFD = None):
        self.readFD = readFD
        self.writeFD = writeFD

        if self.readFD:
            self.readFP = os.fdopen(self.readFD, "r")

        if self.writeFD:
            self.writeFP = os.fdopen(self.writeFD, "w")

    def __del__(self):

        self.close()

    def close(self):

        self.closeRead()
        self.closeWrite()

    def closeRead(self):

        if self.readFD is not None:
            log.debug("Close read %d", self.readFD)
            self.readFP.close()
            self.readFP = None
            self.readFD = None

    def closeWrite(self):

        if self.writeFD is not None:
            log.debug("Close write %d", self.writeFD)
            self.writeFP.close()
            self.writeFP = None
            self.writeFD = None
        
    def writeURL(self, url):

        if self.writeFD is None:
            raise Exception, "Cannot write to pipe: writeFD unavailable"
        
        #
        # Ensure it's a string.
        #
        urlstr = str(url)
        l = len(urlstr)
        s = struct.pack("<l%ss" % (l,), l, urlstr)
        self.writeFP.write(s)
        self.writeFP.flush()

    def readURL(self):

        if self.readFD is None:
            raise Exception, "Cannot read from pipe: readFD unavailable"

        log.debug("waiting on read on %d", self.readFD)
        lsiz = struct.calcsize("<l")
        lstr = self.readFP.read(lsiz)

        if lstr is None or lstr == "":
            log.debug("first read %d returns none", self.readFD)
            return None

        (n,) = struct.unpack("<l", lstr)
        
        print "Got len '%s'" % (n,)
        str = self.readFP.read(n)

        if str is None or str == "":
            log.debug("second read %d returns none", self.readFD)
            return None
            
        print "Read url ", str

        return str

class PersonalNodeManager:
    def __init__(self, setNodeServiceCallback, debugMode, progressCallback):
        self.setNodeServiceCallback = setNodeServiceCallback
        self.debugMode = debugMode
        self.progressCallback = progressCallback

        self.initPipes()

    def Run(self):
        """
        Start the subprocesses, and drop into the interlock sequence.
        """

        #
        # Start processes
        #
        
        self.startServiceManager()
        self.startNodeService()

        self.closeUnusedPipeEnds()

        #
        # Wait for the service mgr to initialize.
        #

        url = self.svc_mgr_init_pipe.readURL()

        log.debug("Service manager running at %s", url)
        self.progressCallback("Started service manager.")
        
        self.svc_mgr_init_pipe.close()

        #
        # Now wait for the node service to initialize
        #

        url = self.node_svc_init_pipe.readURL()

        log.debug("Node service running at %s", url)
        self.progressCallback("Started node service.")

        self.node_svc_init_pipe.close()

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

        We do this by closing the pipes to the nodes, and waiting
        a bit. If they don't die, then call TerminateProcess.

        """

        log.debug("Stop node service")
        

        log.debug("Stop svc mgr")
        self.svc_mgr_term_pipe.close()

        log.debug("Stop node svc")
        self.node_svc_term_pipe.close()

        log.debug("Wait for node service %s to die", self.nodeServicePInfo)
        ensureProcessDead(self.nodeServicePInfo)

        log.debug("Wait for service manager %s to die", self.serviceManagerPInfo)
        ensureProcessDead(self.serviceManagerPInfo)

    def initPipes(self):
        """
        Create the pipes used to communicate between
        the venue client and the service mgrs.

        

        """

        all_fds = []
        for obj in ['svc_mgr_init_pipe',
                    'svc_mgr_term_pipe',
                    'svc_mgr_node_svc_synch_pipe',
                    'node_svc_init_pipe',
                    'node_svc_term_pipe']:

            (r, w) = os.pipe()

            all_fds.append(str(r))
            all_fds.append(str(w))

            pobj = Pipe(r, w)

            print "%s: r=%d w=%d" % (obj, r, w)

            setattr(self, obj, pobj)

        all_str = string.join(all_fds, ",")
        self.nodeServiceArg = "%s:%s:%s:%s" % (self.node_svc_init_pipe.writeFD,
                                               self.svc_mgr_node_svc_synch_pipe.readFD,
                                               self.node_svc_term_pipe.readFD,
                                               all_str)

        self.serviceManagerArg = "%s:%s:%s:%s" % (self.svc_mgr_init_pipe.writeFD,
                                                  self.svc_mgr_node_svc_synch_pipe.writeFD,
                                                  self.svc_mgr_term_pipe.readFD,
                                                  all_str)

    def closeUnusedPipeEnds(self):
        """
        Close the ends of the pipes that the venue client isn't using.
        Must be done *after* the children are created.
        """

        log.debug("Closing unused pipe ends")
        self.node_svc_init_pipe.closeWrite()
        self.node_svc_term_pipe.closeRead()
        self.svc_mgr_init_pipe.closeWrite()
        self.svc_mgr_term_pipe.closeRead()
        self.svc_mgr_node_svc_synch_pipe.close()
        

class PN_NodeService:
    def __init__(self, terminateCallback):
        self.terminateCallback = terminateCallback


    def RunPhase1(self, initArg):
        """
        First part of initialization.

        Returns the URL to the service manager.
        """

        try:
            (init, synch, term, all) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_NodeService: %s", initArg)
            log.exception("Invalid argument to PN_NodeService: %s", initArg)
            raise e


        #
        # Close all the pipe fds except the ones we want
        #

        init = int(init)
        synch = int(synch)
        term = int(term)
        want = {init: 1, synch: 1, term: 1}

        for fd in all.split(","):
            fd = int(fd)
            if not fd in want:
                os.close(fd)

        self.initPipe = Pipe(writeFD = init)
        self.synchPipe = Pipe(readFD = synch)
        self.termPipe = Pipe(readFD = term)

        #
        # Start the interlock protocol.
        #

        url = self.synchPipe.readURL()
        log.debug("Node service: synch wait completes with url %s", url)

        self.synchPipe.close()

        return url

    def RunPhase2(self, myURL):
        """
        Second part of initialization.

        myURL is the handle for our node service.

        """

        log.debug("signalling node svc event")
        self.initPipe.writeURL(myURL)
        self.initPipe.close()

        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEnd)
        self.thread.start()

    def waitForEnd(self):
        log.debug("NS waiting for termination")

        ret = self.termPipe.readURL()
        log.debug("NS terminating ret=%s", ret)
        self.terminateCallback()

class PN_ServiceManager:
    def __init__(self, getMyURLCallback, terminateCallback):
        self.getMyURLCallback = getMyURLCallback
        self.terminateCallback = terminateCallback

    def Run(self, initArg):
        try:
            (init, synch, term, all) = initArg.split(":")
        except ValueError, e:
            log.error("Invalid argument to PN_ServiceManager: %s", initArg)
            log.exception("Invalid argument to PN_ServiceManager: %s", initArg)
            raise e

        #
        # Close all the pipe fds except the ones we want
        #

        init = int(init)
        synch = int(synch)
        term = int(term)
        want = {init: 1, synch: 1, term: 1}

        for fd in all.split(","):
            fd = int(fd)
            if not fd in want:
                os.close(fd)

        self.initPipe = Pipe(writeFD = init)
        self.synchPipe = Pipe(writeFD = synch)
        self.termPipe = Pipe(readFD = term)


        #
        # Start the interlock protocol.
        #

        myURL = self.getMyURLCallback()
        log.debug("signalling synch event")
        self.initPipe.writeURL(myURL)
        self.synchPipe.writeURL(myURL)

        self.initPipe.close()
        self.synchPipe.close()
    
        #
        # Create a thread to wait for termination
        #

        self.thread = threading.Thread(target=self.waitForEnd)
        self.thread.start()

    def waitForEnd(self):
        log.debug("SM waiting for termination")
        r = self.termPipe.readURL()
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
