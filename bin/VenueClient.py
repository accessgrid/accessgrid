#qfrom AccessGrid.VenueClient import VenueClient
import AccessGrid.GUID
import AccessGrid.Types
import AccessGrid.Utilities
from AccessGrid.VenueClientUIClasses import *
import threading
import AccessGrid.ClientProfile
import os

class VenueClientUI(wxApp, VenueClient):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event. 
    """
    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        VenueClient.__init__(self)        
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(300, 400))
        self.SetTopWindow(self.frame)
        self.client = None
        self.gotClient = false
        return true

    def ConnectToServer(self, file = None):
        venueServerUri = "https://localhost:8000/VenueServer"
        venueUri = Client.Handle( venueServerUri ).get_proxy().GetDefaultVenue()
        myHomePath = os.environ['HOME']
        accessGridDir = '.AccessGrid'
        self.profilePath = myHomePath+'/'+accessGridDir+'/profile'

        if file:
            self.profile = ClientProfile(file)
            self.profile.Dump()
        else:
            try:
                os.listdir(myHomePath+'/'+accessGridDir)
            except:
                os.mkdir(myHomePath+'/'+accessGridDir)

            self.profile = ClientProfile(self.profilePath)
                  
        if self.profile.IsDefault():  # not your profile
            print 'ConnectToServer'
            self.profile.Dump()
            profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', self.profile)

            if (profileDialog.ShowModal() == wxID_OK): # when click ok
                self.ChangeProfile(profileDialog.GetNewProfile())
                
                profileDialog.Destroy()
               # profile.Save(self.profilePath)
                self.__startMainLoop(venueUri, self.profile)
            
            else:  # when click cancel
                profileDialog.Destroy()

        else:
            self.__startMainLoop(venueUri, profile)

               
    def __startMainLoop(self, uri, profile):
        if uri:
            self.gotClient = true
            self.client = Client.Handle(uri).get_proxy()
           # self.SetProfile(profile)
            self.EnterVenue(uri)
            self.frame.Show(true)
            self.MainLoop()
            
        else:
            ErrorDialog(self.frame, 'No default venue on server')

    def CoherenceCallback(self, event):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations based on coherence events.
        """
        VenueClient.CoherenceCallback(self, event)
        if event.eventType == Event.ENTER :
            print 'somebody enters'
            self.frame.contentListPanel.AddParticipant(event.data)

       # elif event.eventType == Event.MODIFY_USER:
        #    print 'modify user'
                        
        elif event.eventType == Event.EXIT:
            print 'exit'
            self.frame.contentListPanel.RemoveParticipant(event.data)
            
        elif event.eventType == Event.ADD_DATA:
            print 'add data'
            self.frame.contentListPanel.AddData(event.data)
            
        elif event.eventType == Event.ADD_SERVICE:
            print 'add service'
            self.frame.contentListPanel.AddService(event.data)
            
        elif event.eventType == Event.ADD_CONNECTION:
            print 'add connection'
            self.frame.venueListPanel.list.AddVenueDoor(event.data)

        elif event.eventType == Event.REMOVE_CONNECTION:
            print 'remove connection'

        elif event.eventType == Event.UPDATE_VENUE_STATE:
            print 'update venue state'

        else:
            print 'HEARTBEAT!'
    
    def EnterVenue(self, URL):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
        """
        print '-------------------------enter venue'
        VenueClient.EnterVenue( self, URL )
        
        venueState = self.venueState
        self.frame.SetLabel(venueState.description.name)
        text = self.profile.name + ', welcome to:\n' + self.venueState.description.name\
               + '\n' +self.venueState.description.description 
        welcomeDialog = wxMessageDialog(NULL, text ,'', wxOK | wxICON_INFORMATION)
        welcomeDialog.ShowModal()
        welcomeDialog.Destroy()

        users = venueState.users.values()
        for user in users:
            if(user.profileType == 'user'):
                self.frame.contentListPanel.AddParticipant(user)
            else:
                self.frame.contentListPanel.AddNode(user)

        data = venueState.data.values()
        for d in data:
            self.frame.contentListPanel.AddData(d)

        nodes = venueState.nodes.values()
        for node in nodes:
            self.frame.contentListPanel.AddNode(node)

        services = venueState.services.values()
        for service in services:
            self.frame.contentListPanel.AddService(service)

        exits = venueState.connections.values()
        for exit in exits:
            self.frame.venueListPanel.list.AddVenueDoor(exit)
               
    def ExitVenue(self ):
        """
        Note: Overloaded from VenueClient
        This method calls the venue client method and then
        performs its own operations when the client exits a venue.
        """
        VenueClient.ExitVenue( self )
        print "Exited venue ! "

    def GoToVenue(self, URL):
        print 'go to other venue'
        self.ExitVenue()
        self.EnterVenue(URL)
        

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
        self.ExitVenue()

    def AddData(self, path):
        print '------- add data'
        data = DataDescription('myData', path)
        self.client.AddData(data)

    def ChangeProfile(self, profile):
        profile.Dump()
        self.profile = profile
        self.profile.Save(self.profilePath)
        self.SetProfile(self.profile)

     #   if self.gotClient:
     #       self.client.UpdateClientProfile(profile)

        
if __name__ == "__main__":

    import sys
    from AccessGrid.hosting.pyGlobus.Server import Server
    from AccessGrid.hosting.pyGlobus import Client
    from AccessGrid.ClientProfile import ClientProfile
    from AccessGrid.Types import *

    profile = None

    if len(sys.argv) > 1:
        print 'length = 1'
        profile = sys.argv[1]
        
    vc = VenueClientUI()
    print '------------ before save config ------------ '
    # SaveConfig(testFile, profile)
    
    # try:
    vc.ConnectToServer(profile)
    
    
    # except:
    #     text1 = 'Problems getting default venue from server.  '
    #text2 = 'Is the server running?'
    #     ErrorDialog(NULL, text1+text2)
    
    # else:
   

    
  
