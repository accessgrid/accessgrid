import os
import sys

from AccessGrid.DataStore import DataService

def Main():
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
            elif o in ("-s", "--serviePort"):
                servicePort = int(a)
            elif o in ("-h", "--help"):
                Usage()
                sys.exit(0)
            else:
                Usage()
                sys.exit(0)
                           
        dataService = DataService(path, dataPort, servicePort)
   
def Usage():
    print "%s:" % (sys.argv[0])
    print "  --help: Print usage"
    print "  -l|--location: Base path for data storage"
    print "  -d|--dataPort: Port used for data communication"
    print "  -s|--servicePort: Port used for SOAP interface"
    

if __name__ == "__main__":
    
    import getopt
       
    Main()
