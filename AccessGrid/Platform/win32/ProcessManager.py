#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     
# Created:     2003/08/02
# RCS-ID:      $Id: ProcessManager.py,v 1.4 2004-03-12 21:54:28 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.4 2004-03-12 21:54:28 judson Exp $"
__docformat__ = "restructuredtext en"

import win32process
from AccessGrid import Log

log = Log.GetLogger(Log.ProcessManager)

class ProcessManager:
    def __init__(self):
        self.processes = []

    def StartProcess(self, command, arglist, detached = 1, maxWait = 20):
        """
        Start a new process.

        @param command : the name of the command to be started. It can
        either be a full pathname or a command name to be found on the
        default path.
        
        @param arglist : is a list of the arguments to the command.

        @param detached : a flag indicating whether this process
        should be run detached or the process manager should wait for
        it to complete execution to return.
        
        @type command: string
        @type arglist: list of strings
        @type detached: integer
        """
        cmdline = command
        for arg in arglist:
            arg = str(arg)
            if arg.find(" ") != -1:
                #
                # If there are spaces, quote the arg
                #
                arg = '"' + arg + '"'

            cmdline += " " + arg

        rc = None

        try:

            startup_info = win32process.STARTUPINFO()

            log.debug("Creating process: %s", cmdline)

            info = win32process.CreateProcess(
                None,                   # AppName
                cmdline,                # Command line
                None,                   # Process security
                None,                   # Thread security
                0,                      # Inherit handles? 
                win32process.NORMAL_PRIORITY_CLASS,
                None,                   # New environment
                None,                   # Current directory
                startup_info)

            log.debug("Create process returns: %s", info)

            pHandle = info[0]
            
            self.processes.append(pHandle)

            if not detached:
                pHandle = info[0]
                wTime = 0
                tIncr = 1
                # We have to wait for it to finish
                exitCode = win32process.GetExitCodeProcess(pHandle)
                while exitCode == 259 and wTime < maxWait:
                    exitCode = win32process.GetExitCodeProcess(pHandle)
                    time.sleep(tIncr)
                    wTime = wTime + tIncr
                else:
                    # Gotta kill it, sigh
                    self.TerminateProcess(pHandle)
                return exitCode
            else:
                return pHandle
                
        except win32process.error, e:
            log.exception("process creation failed: %s", e)

    def TerminateAllProcesses(self):
        """
        Cleanly shutdown all processes this manager has created.
        """
        for phandle in self.processes:
            try:
                self.TerminateProcess(phandle)
            except Exception, e:
                log.exception("couldn't terminate process %s: %s", phandle, e)

    def TerminateProcess(self, pid):
        """
        Cleanly shutdown the specified process this manager has created.

        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """
        try:
            win32process.TerminateProcess(pid, 0)
            self.processes.remove(pid)
        except win32process.error, e:
            log.exception("couldn't terminate process %s: %s", pid, e)

    def KillAllProcesses(self):
        """
        Kill all processes this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        """
        self.TerminateAllProcesses()

    def KillProcess(self, pid):
        """
        Kill a single process this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        
        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """
        self.TerminateProcess(pid)

    def ListProcesses(self):
        """
        Return a list of process id's for this process manager.
        @returns: a list of process id's
        """
        return self.processes

if __name__ == "__main__":
    import time
    mgr = ProcessManager()

    try:
        mgr.StartProcess("notepad", [r"\boot.ini"])
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

    try:
        mgr.StartProcess("notepad", [r"\boot.ini"], detached = 0)
    except Exception, e:
        print "Exception with non-detached process: ", e
    
