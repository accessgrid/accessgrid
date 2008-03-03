#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: ProcessManager.py,v 1.7 2007/04/16 19:40:56 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.7 2007/04/16 19:40:56 turam Exp $"
__docformat__ = "restructuredtext en"

import signal
import os
import time
from AccessGrid import Log

log = Log.GetLogger(Log.ProcessManager)

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.callback = None
        
    def WaitForChildren(self,callback):
        signal.signal(signal.SIGCHLD,self.OnSigChild)
        self.callback = callback
        
    def OnSigChild(self,num,event):
        if not self.processes:
            log.info('OnSigChild:  ---- no processes; returning')
            return
            
        while 1:
            try:
                ret = os.waitpid(-1,os.WNOHANG)
            except:
                log.exception('Exception in waitpid; breaking')
                break
        
            try:
                pid = ret[0]
                log.debug('OnSigChild: pid = %d', pid)
                
                # break if no process found
                if not pid:
                    log.debug('OnSigChild got zero pid; breaking')
                    break
                    
                if pid in self.processes:
                    self.processes.remove(pid)
                    if self.callback:
                        self.callback(self,pid)
                else:
                    log.info("Got sigchild for unexpected process pid=%d", pid)
            except:
                log.exception("Exception in sigchld handler; breaking. [MUST fix]")
                break



    def StartProcess(self, command, arglist, detached = 1):
        """
        Start a new process.
        Command is the name of the command to be started. It can either be
        a full pathname or a command name to be found on the default path.
        Arglist is a list of the arguments to the command.
        """
        arglist = map(lambda a: str(a), arglist)
        arglist.insert(0, str(command))
        
        if detached:
            pid = os.spawnvp(os.P_NOWAIT, command, arglist)
        else:
            pid = os.spawnvp(os.P_WAIT, command, arglist)
            
        self.processes.append(pid)

        return pid

    def TerminateAllProcesses(self):
        """
        Cleanly shutdown all processes this manager has created.
        """
        # Use a copy of the process list
        processList = self.processes[:]
        
        for pid in processList:
            try:
                self.TerminateProcess(pid)   
            except OSError, e:
                log.debug( "couldn't terminate process: %s", e )
                
    def TerminateProcess(self, pid):
        """
        Cleanly shutdown the specified process this manager has created.

        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """
        os.kill(pid, signal.SIGINT)
        elapsedWaits = 0
        maxWaits = 5
        waitTime = 0.1
        retpid = 0
        try:
            while elapsedWaits < maxWaits:
                (retpid,status) = os.waitpid(pid, os.WNOHANG )
                if retpid == pid and os.WIFEXITED(status):
                    break
                time.sleep(waitTime)
                elapsedWaits += 1
        except OSError, e:
                log.debug( "_terminate_process( %i ): %s", pid, e )

        if retpid == pid:
            if os.WIFEXITED(status):
                rc = os.WEXITSTATUS(status)
            elif os.WIFSIGNALED(status):
                sig = os.WTERMSIG(status)
            self.processes.remove(pid)
        else:
            self.KillProcess(pid)

    def KillAllProcesses(self):
        """
        Kill all processes this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        """
        processList = self.processes[:]
        
        for pid in processList:
            try:
                self.KillProcess(pid)   
            except OSError, e:
                log.debug ("couldn't kill process: %s", e)

    def KillProcess(self, pid):
        """
        Kill a single process this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        
        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """
        os.kill(pid,signal.SIGKILL)
        maxWaits = 5
        waitTime = 0.1
        elapsedWaits = 0
        retpid = 0
        try:
            while elapsedWaits < maxWaits:
                (retpid,status) = os.waitpid(pid, os.WNOHANG )
                if retpid == pid and os.WIFSIGNALED(status):
                    break
                time.sleep(waitTime)
                elapsedWaits += 1
        except OSError, e:
            log.debug ( "_kill_process, waitpid %i : %s", pid, e )

        if retpid == pid:
            if os.WIFEXITED(status):
                rc = os.WEXITSTATUS(status)
            elif os.WIFSIGNALED(status):
                sig = os.WTERMSIG(status)
        else:
            log.debug("Process %i not killed or waitpid() failed.", pid)

        self.processes.remove(pid)

    def ListProcesses(self):
        """
        Return a list of process id's for this process manager.
        @returns: a list of process id's
        """
        return self.processes
    
    def IsRunning(self, pid):
        """
        Returns a flag to indicate whether the specified process is running
        @returns: 0 if process is not running, 1 if it is
        """
        try:
            os.kill(pid, 0)
            return 1
        except OSError, err:
            # err 3 (no such process) is the expected value; others should be logged
            if err.args[0] != 3:
                log.exception('Unexpected exception; MUST examine')
            return 0
        except:
            log.exception('Exception in IsRunning')
            return 0

            
if __name__ == "__main__":
    mgr = ProcessManager()

    try:
        mgr.StartProcess("date", [])
    except Exception, e:
        print "Exception starting process: ", e

    try:
        print mgr.ListProcesses()
    except Exception, e:
        print "Exception listing processes: ", e

    time.sleep(5)

    try:
        mgr.TerminateAllProcesses()
    except Exception, e:
        print "Exception terminating processes: ", e

    
