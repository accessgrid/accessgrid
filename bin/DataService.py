import os
import sys
import signal

from AccessGrid.DataStore import DataService
from AccessGrid import Toolkit


dataService = None

# Signal handler to catch signals and shutdown
def SignalHandler(signum, frame):
    """
    SignalHandler catches signals and shuts down the DataService
    """
    print "Shutting down..."
    dataService.Shutdown()


def Main():
        
        global dataService

        path = 'DATA'
        dataPort = 8886
        servicePort = 8500

        index = len(sys.argv) - 1

        try:
            opts, args = getopt.getopt(sys.argv[1:], "l:d:s:h",
                                       ["location=", "dataPort=",
                                        "servicePort=", "help"])
        except getopt.GetoptError:
            Usage()
            sys.exit(2)

        for o, a in opts:
            if o in ("-l", "--location"):
                path = a
            elif o in ("-d", "--dataPort"):
                dataPort = int(a)
            elif o in ("-s", "--servicePort"):
                servicePort = int(a)
            elif o in ("-h", "--help"):
                Usage()
                sys.exit(0)
            else:
                Usage()
                sys.exit(0)

        app = Toolkit.CmdlineApplication()
        app.InitGlobusEnvironment()
                           
        # Register a signal handler so we can shut down cleanly
        signal.signal(signal.SIGINT, SignalHandler)

        dataService = DataService(path, dataPort, servicePort)

        import time
        while dataService.IsRunning():
            time.sleep(1)

        os._exit(1)
   
def Usage():
    print "%s:" % (sys.argv[0])
    print "  --help: Print usage"
    print "  -l|--location: Base path for data storage"
    print "  -d|--dataPort: Port used for data communication"
    print "  -s|--servicePort: Port used for SOAP interface"
    

if __name__ == "__main__":
    
    import getopt
       
    Main()
