#!/usr/bin/python2

import os
import sys
import cmd
import string

if sys.platform != 'win32':
    import readline


from optparse import Option

from AccessGrid.Toolkit import CmdlineApplication
from AccessGrid.GUID import GUID
from AccessGrid.Venue import VenueIW
from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Descriptions import VenueDescription


class CmdProcessor(cmd.Cmd):
    """
    The GnuplotCmdProcessor presents a gnuplot-like command-line interface
    with the option of registering callbacks to handle the commands entered
    """
    def __init__(self, venueserverurl, log):
        """
        The constructor for the gnuplot command processor.
        """
        cmd.Cmd.__init__(self)

        self.venueserverurl = venueserverurl
        self.log = log
        
        self.prompt = "venueserver> "
        
        self.venueList = []
        self.connectionList = []
        self.connectionListVenueIndex = -1

    def emptyline(self):
        """
        Method to process empty lines.
        """
        pass
        
    def isValidIndex(self,index):
        if index >= len(self.venueList):
            print "Venue index must be between 0 and ", len(self.venueList)-1
            return 0
        return 1
        
    def do_GetVenues(self,line):
        
        venueserverurl = line
        if not venueserverurl:
            if self.venueserverurl:
                venueserverurl = self.venueserverurl
            else:
                print "no venue server url given"
                return
            
        self.venueList = VenueServerIW(venueserverurl).GetVenues()
        i = 0
        for venue in self.venueList:
            print i, venue.name
            i += 1
            
    def do_GetName(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return
            
        name = VenueIW(self.venueList[index].uri).GetName()
        print name
        
    def do_SetName(self,line):

        words = line.split()
        index = int(words[0])
        if not self.isValidIndex(index):            
            return
            
        name = string.join(words[1:],' ')
        print "Setting name to ", name
        VenueIW(self.venueList[index].uri).SetName(name)

    def do_GetDescription(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return
            
        print VenueIW(self.venueList[index].uri).GetDescription()
        
    def do_SetDescription(self,line):

        words = line.split()
        index = int(words[0])
        if not self.isValidIndex(index):            
            return
            
        text = string.join(words[1:],' ')
        print "Setting description to ", text
        VenueIW(self.venueList[index].uri).SetDescription(text)

    def do_GetStreams(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return

        streamList = VenueIW(self.venueList[index].uri).GetStreams()
        for stream in streamList:
            print stream
            
    def do_GetStaticStreams(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return

        streamList = VenueIW(self.venueList[index].uri).GetStaticStreams()
        for stream in streamList:
            print stream
            
    def do_RegenerateEncryptionkeys(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return
            
        print VenueIW(self.venueList[index].uri).RegenerateEncryptionKeys()
        
    def do_GetEncryptMedia(self,line):

        index = int(line)
        if not self.isValidIndex(index):            
            return
            
        print VenueIW(self.venueList[index].uri).GetEncryptMedia()
        
    def do_SetEncryptMedia(self,line):

        words = line.split()
        index = int(words[0])
        if not self.isValidIndex(index):            
            return

        encryptFlag = words[1]
        encryptKey = None
        if len(words) > 2:
            encryptKey = words[2]
        
        print "Setting encrypt to ", encryptFlag, encryptKey
        VenueIW(self.venueList[index].uri).SetEncryptMedia(encryptFlag,encryptKey)

    def do_GetConnections(self,line):
        index = int(line)
        if not self.isValidIndex(index):            
            return
            
        from AccessGrid.Descriptions import CreateConnectionDescription

        self.connectionListVenueIndex = index
        connectionList = VenueIW(self.venueList[index].uri).GetConnections()
        self.connectionList = []
        for conn in connectionList:
            self.connectionList.append(CreateConnectionDescription(conn))
        self.ListConnections(index)
        
    def ListConnections(self,line):
    
        print "Connections from venue", self.connectionListVenueIndex, \
                                        self.venueList[self.connectionListVenueIndex].name

        i = 0
        for connection in self.connectionList:
            print i,connection
            i += 1
            
    def do_SetConnectionName(self,line):
        words = line.split()
        index = int(words[0])
        if index >= len(self.connectionList):   
            print "Invalid connection id: ", index         
            return
            
        name = string.join(words[1:],' ')
        print "Setting name to ", name
        self.connectionList[index].name = name
        self.ListConnections(self.connectionListVenueIndex)
        
    def do_SetConnections(self,line=None):
        index = int(line)
        if not self.isValidIndex(index):            
            return

        VenueIW(self.venueList[index].uri).SetConnections(self.connectionList)
        
    def do_AddVenue(self,line=None):
        
        venueName = raw_input('Enter venue name:')
        venueDescription = raw_input('Enter venue description:')
        encryptFlag = raw_input('Encrypt streams? (y/n):')
        encryptKey = None
        if encryptFlag[0] == 'y':
            encryptKey = raw_input('Encryption key:')
            
        venueDescription = VenueDescription(venueName,
                                            venueDescription,
                                            (encryptFlag,encryptKey))
        
        venueUri = VenueServerIW(self.venueserverurl).AddVenue(venueDescription)
        print "Venue uri: ", venueUri
        
        
    def do_quit(self,line):
        # Just do what the man says and everything'll be cool
        os._exit(0)
        
        
        
        
       
def main():
    """
    The main routine.
    """
    # Instantiate the app
    app = CmdlineApplication()

    # Handle command-line arguments
    urlOption = Option("-u","--url",
                      dest = "url", default = 0,
                      help = "URL for the venue server to manage.")
    app.AddCmdLineOption(urlOption)

    # Initialize the application
    try:
        app.Initialize("VenueMgmt")
    except Exception, e:
        print "Exception: ", e
        sys.exit(0)
        
    cmd = CmdProcessor(app.GetOption('url'), app.GetLog())
    
    # Loop forever (or until we're told to quit)
    cmd.cmdloop()
    

if __name__ == "__main__":
    main()
