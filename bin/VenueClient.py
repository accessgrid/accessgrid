from AccessGrid.VenueClient import VenueClient
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
        VenueClient.__init__(self)        
        self.frame = VenueClientFrame(NULL, -1,"", self)
        self.frame.SetSize(wxSize(300, 400))
        self.SetTopWindow(self.frame)
        return true

    def ConnectToServer(self, file = None):
        venueServerUri = "https://localhost:8000/VenueServer"
        venueUri = Client.Handle( venueServerUri ).get_proxy().GetDefaultVenue()
        myHomePath = os.environ['HOME']
        accessGridDir = '.AccessGrid'
        profilePath = myHomePath+'/'+accessGridDir+'/profile'

        if file:
            profile = ClientProfile(file)
        else:
            try:
                os.listdir(myHomePath+'/'+accessGridDir)
            except:
                os.mkdir(myHomePath+'/'+accessGridDir)

            profile = ClientProfile(profilePath)
                  
        if profile.IsDefault():  # not your profile
            profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', profile)

            if (profileDialog.ShowModal() == wxID_OK): # when click ok
                profile.SetName(profileDialog.nameCtrl.GetValue())
                profile.SetEmail(profileDialog.emailCtrl.GetValue())
                profile.SetPhoneNumber(profileDialog.phoneNumberCtrl.GetValue())
                profile.SetTechSupportInfo(profileDialog.supportCtrl.GetValue())
                profile.SetLocation(profileDialog.locationCtrl.GetValue())
                profile.SetHomeVenue(profileDialog.homeVenueCtrl.GetValue())
                profile.SetProfileType(profileDialog.profileTypeBox.GetValue())
                profileDialog.Destroy()
                profile.Save(profilePath)
                self.__startMainLoop(venueUri, profile)
            
            else:  # when click cancel
                profileDialog.Destroy()

        else:
            self.__startMainLoop(venueUri, profile)

               
    def __startMainLoop(self, uri, profile):
        if uri:
            self.SetProfile(profile)
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
                        
        elif event.eventType == Event.EXIT:
            print 'remove data'
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
        print 'enter venue'
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
            print '--------------------- user -----------------'
            print user.name
            self.frame.contentListPanel.AddParticipant(user)

        data = venueState.data.values()
        for d in data:
            self.frame.venueListPanel.list.AddData(d)

        nodes = venueState.nodes.values()
        for node in nodes:
            self.frame.venueListPanel.list.AddNode(node)

        services = venueState.services.values()
        for service in services:
            self.frame.venueListPanel.list.AddService(service)

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
   

    
  
