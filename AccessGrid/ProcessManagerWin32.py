#-----------------------------------------------------------------------------
# Name:        ProcessManagerWin32.py
# Purpose:     
#
# Author:      Robert D. Olson
#
# Created:     2003/08/02
# RCS-ID:      $Id: ProcessManagerWin32.py,v 1.8 2003-09-16 07:20:18 judson Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManagerWin32.py,v 1.8 2003-09-16 07:20:18 judson Exp $"
__docformat__ = "restructuredtext en"

import win32process

import logging

log = logging.getLogger("AG.ProcessManagerWin32")

class ProcessManagerWin32:
    def __init__(self):
        self.processes = []

    def start_process(self, command, arglist):
        """
        Start a new process.
        Command is the name of the command to be
        started. It can either be a full pathname or a command name to
        be found on the default path.  Arglist is a list of the
        arguments to the command.  On windows, these will all be
        joined together into a string to be passed to CreateProcess.
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

            self.processes.append(info[0])

            rc = info[0]

        except win32process.error, e:
            log.exception("process creation failed: %s", e)

        return rc

    def terminate_all_processes(self):
        for phandle in self.processes:
            try:
                win32process.TerminateProcess(phandle, 0)
            except win32process.error, e:
                log.exception("couldn't terminate process %s: %s", phandle, e)
        self.processes = []

    def terminate_process(self, phandle):
        try:
            win32process.TerminateProcess(phandle, 0)
            self.processes.remove(phandle)
        except win32process.error, e:
            log.exception("couldn't terminate process %s: %s", phandle, e)

if __name__ == "__main__":

    import time

    mgr = ProcessManagerWin32()
    mgr.start_process("notepad", [r"\boot.ini"])

    time.sleep(5)

    mgr.terminate_all_processes()

    
