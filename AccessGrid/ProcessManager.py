#-----------------------------------------------------------------------------
# Name:        ProcessManager.py
# Purpose:     Interface definitions for ProcessManager
# Created:     2003/08/02
# RCS-ID:      $Id: ProcessManager.py,v 1.7 2004-09-09 22:12:12 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: ProcessManager.py,v 1.7 2004-09-09 22:12:12 turam Exp $"

class ProcessManager:
    def __init__(self):
        raise Exception, "This should not be called directly, but by a subclass."

    def StartProcess(self, command, arglist, detached = 1):
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
        raise Exception, "This should not be called directly, but by a subclass."

    def TerminateAllProcesses(self):
        """
        Cleanly shutdown all processes this manager has created.
        """
        raise Exception, "This should not be called directly, but by a subclass."

    def TerminateProcess(self, pid):
        """
        Cleanly shutdown the specified process this manager has created.

        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """

    def KillAllProcesses(self):
        """
        Kill all processes this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        """
        raise Exception, "This should not be called directly, but by a subclass."

    def KillProcess(self, pid):
        """
        Kill a single process this manager has created.

        @warning: this is not a clean shutdown, but a forced shutdown
        that may result in system cruft.
        
        @param pid: the id of the process to terminate.
        @type pid: string? integer?
        """
        raise Exception, "This should not be called directly, but by a subclass."

    def ListProcesses(self):
        """
        Return a list of process id's for this process manager.
        @returns: a list of process id's
        """
        raise Exception, "This should not be called directly, but by a subclass."
