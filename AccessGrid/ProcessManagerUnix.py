import signal
import string
import os

class ProcessManagerUnix:

    def __init__(self):
        self.processes = []

    def start_process(self, command, arglist):
        """
        Start a new process.
        Command is the name of the command to be started. It can either be a full pathname
        or a command name to be found on the default path.
        Arglist is a list of the arguments to the command.
         """

        arglist.insert(0, command)

        arglist = map(lambda a: str(a), arglist)
        pid = os.spawnvp(os.P_NOWAIT, command, arglist)

        self.processes.append(pid)

    def terminate_all_processes(self):
        for pid in self.processes:
            try:
                os.kill(pid, signal.SIGINT)
                ret = os.waitpid(pid, 0)
                print "waitpid returns ", ret
                status = ret[1]
                if os.WIFEXITED(status):
                    rc = os.WEXITSTATUS(status)
                    print "processes exited normally with rc ", rc
                elif os.WIFSIGNALED(status):
                    sig = os.WTERMSIG(status)
                    print "Process was killed with signal ", sig
                    
            except OSError, e:
                print "couldn't terminate process: ", e

        self.processes = []

if __name__ == "__main__":

    import time

    mgr = ProcessManagerUnix()
    mgr.start_process("date",[])

    time.sleep(3)

    mgr.terminate_all_processes()

    
