#-----------------------------------------------------------------------------
# Name:        Voyager.py
# Purpose:     Tool for recording and playback of AG sessions. 
# 
# Author:      Susanne Lefvert 
# 
# Created:     $Date: 2004-12-22 21:46:06 $ 
# RCS-ID:      $Id: Voyager.py,v 1.2 2004-12-22 21:46:06 lefvert Exp $ 
# Copyright:   (c) 2002 
# Licence:     See COPYING.TXT 
#----------------------------------------------------------------------------- 
 
import getopt 
import sys 
import time 
import os 
 
from wxPython.wx import * 
from ObserverPattern import Observer, Model 
 
from AccessGrid.Toolkit import WXGUIApplication 
from AccessGrid import icons 
from AccessGrid.Venue import VenueIW 
from AccessGrid.Platform.Config import UserConfig 
from AccessGrid.Platform.ProcessManager import ProcessManager 
from AccessGrid.Utilities import LoadConfig, SaveConfig

class Recording: 
    ''' 
    Description class for recordings including name, description, 
    start and stop time, and a venue url describing where the source 
    for the recording is located. 
    ''' 
    def __init__(self, name, description, venueUrl): 
        ''' 
        Initialize the Recording instance. 
        ''' 
        self.__name = name 
        self.__description = description

        # Always set start time since that is the key for
        # recordings
        self.__startTime = int(time.mktime(time.localtime()))
        self.__stopTime = None 
        self.__venueUrl = venueUrl
       
    def Save(self, path):
        # Write config file to path
        config = {}
        config['Recording.name'] = self.__name
        config['Recording.description'] = self.__description
        config['Recording.startTime'] = self.__startTime
        config['Recording.stopTime'] = self.__stopTime
        config['Recording.venueUrl'] = self.__venueUrl
        
        SaveConfig(path, config)

    def LoadRecording(path):
        config = LoadConfig(path)
        r = Recording(config["Recording.name"], config["Recording.description"], config["Recording.venueUrl"])
        r.SetStartTime(int(config["Recording.startTime"]))
        r.SetStopTime(int(config["Recording.stopTime"]))
        return r

    # Makes it possible to access the method without an instance.
    LoadRecording = staticmethod(LoadRecording)
        
    # Set methods 
 
    def SetName(self, name): 
        self.__name = name 

    def SetDescription(self, desc):
        self.__description = desc

    def SetStartTime(self, startTime = None):
        # Be careful not to change the start time
        # on a recording since this is the unique
        # key.  The start time is automatically set
        # when a recording is created so you should
        # not have to set this parameter.

        if startTime != None:
            self.__startTime = int(startTime)
        else:
            # Convert to int so we can use this value as key in the ui.
            self.__startTime = int(time.mktime(time.localtime()))
                     
    def SetStopTime(self, stopTime = None):
        if stopTime:
            self.__stopTime = int(stopTime)
        else:
            # Convert to int so we can use this value as key in the ui.
            self.__stopTime = int(time.mktime(time.localtime()))
 
    # Get methods 
 
    def GetVenueUrl(self): 
        return self.__venueUrl 
         
    def GetStartTime(self):
        return self.__startTime 
             
    def GetStopTime(self): 
        return self.__stopTime 
 
    def GetName(self): 
        return self.__name 
 
    def GetDescription(self): 
        return self.__description 
     
 
class VoyagerModel(Model): 
    """ 
    The voyager model class includes all logic for the program. There is no user 
    interface code in this class. The ui and the model is separated using the 
    observer pattern for easy separation. When state gets updated in the model, 
    all obervers are notified and updates the view/ui.  The voyager model includes 
    methods for recording and playback of venue media streams, as well as organization 
    and persistence of recordings. 
    """ 
         
    RECORDING = "recording" 
    PLAYING = "playing" 
    STOPPED = "stopped" 
         
    def __init__(self, log): 
        ''' 
        Initialize voyager model including all logic of the program.  
 
        ** Arguments ** 
        *log* log file 
        ''' 
        Model.__init__(self) 
 
        self.__log = log 
        self.__status = self.STOPPED 
        self.__currentRecording = None 
        self.__recordings = {}
        self.__playbackVenueUrl = None
        self.__path = os.path.join(UserConfig.instance().GetConfigDir(), 
                                 "voyager") 
        self.__processManager = ProcessManager() 
 
        if not os.path.exists(self.__path): 
            os.mkdir(self.__path) 
 
        self.__log.debug("VoyagerModel.__init__: Persistence path: %s"%(self.__path)) 

        self.__LoadRecordings()
               
    def __LoadRecordings(self): 
        ''' 
        Load recordings from file. 
        '''

        # For each directory in the voyager path
        # load description config file and create a
        # recording.
        
        dirs = os.listdir(self.__path)
        for dir in dirs:
            path = os.path.join(self.__path, dir)
            if os.path.isdir(path):
                rFile = os.path.join(path, "Recording")
                if os.path.isfile(rFile):
                    recording = Recording.LoadRecording(rFile)
                    self.__recordings[recording.GetStartTime()] = recording

    def SaveRecording(self, recording): 
        ''' 
        Save a recording to file. 
 
        **Arguments** 
         
        *recording* recording instance to save (Recording) 
        '''
        recordingPath = os.path.join(self.__path, str(recording.GetStartTime())) 
        descFile = os.path.join(recordingPath, "Recording")
        recording.Save(descFile)
 
    def PlayInVenue(self, recording, venueUrl): 
        ''' 
        Method for playing a recording in a venue.  This method connects 
        to a venue at venueUrl and retreives multicast information. After that, 
        the recording can be transmitted using rtpplay to the retreived venue 
        addresses. 
 
        ** Arguments ** 
         
        *recording* the recording instance to play (Recording) 
        *venueUrl* venue address where we want to play the recording (string) 
        ''' 
        # Create a venue proxy and send video and audio to 
        # this venue's multicast addresses. 

        self.__playbackVenueUrl = venueUrl
        venueProxy = VenueIW(venueUrl) 
        streams = venueProxy.GetStreams() 
        videoStream = None 
        audioStream = None 
         
        for s in streams: 
            c = s.capability 
            if c.role == "producer": 
                if c.type == "audio": 
                    audioStream = s 
                elif c.type == "video": 
                    videoStream = s 
 
        # Use rtpplay to transmit video and audio 
        recordingPath = os.path.join(self.__path, str(recording.GetStartTime())) 
        
        #Usage:  rtpplay -T -f file host/port 
        rtpplay = "rtpplay" 
         
        # Send audio 
        if audioStream: 
            l = audioStream.location 
            aFile = os.path.join(recordingPath, "audio.rtp")

            # Make sure rtp address is even.
            port = l.port - (l.port%2)
            args = [ 
                "-T", 
                "-f", aFile, 
                l.host+"/"+str(port), 
            ]

            self.__log.debug("Starting process: %s %s"%(rtpplay, str(args))) 
            self.__processManager.StartProcess(rtpplay,args) 
 
        else: 
            self.__log.info("VoyagerModel.PlayInVenue: No audio stream present in %s"%(venueUrl)) 
           
        # Send video 
        if videoStream: 
            l = videoStream.location 
            vFile = os.path.join(recordingPath, "video.rtp") 

            # Make sure rtp address is even.
            port = l.port - (l.port%2)
            args = [ 
                "-T", 
                "-f", vFile, 
                l.host+"/"+str(port), 
            ]
            self.__log.debug("Starting process: %s %s"%(rtpplay, str(args))) 
            self.__processManager.StartProcess(rtpplay,args) 
                        
        else: 
            self.__log.info("VoyagerModel.PlayInVenue: No video stream present in %s"%(venueUrl)) 
 
        # Set state 
        self.__currentRecording = recording 
        self.__status = self.PLAYING 
 
        # Notify ui to update view 
        self.NotifyObservers() 
                          
    def Record(self, recording): 
        ''' 
        Method to record a recording. This method connects 
        to the venue which is specified in the recording parameter 
        to retreive multicast addresses. After that, the rtpdump 
        tool is used to record audio and video streams from the 
        venue. 
 
        ** Arguments ** 
 
        *recording* recording instance to record (Recording) 
         
        '''
        # Create a venue proxy and get venue name and streams 
        venueProxy = VenueIW(recording.GetVenueUrl()) 
        venueName = venueProxy.GetName() 
        streams = venueProxy.GetStreams() 
        videoStream = None 
        audioStream = None 
 
        for s in streams: 
            c = s.capability 
            if c.role == "producer": 
                if c.type == "audio": 
                    audioStream = s 
                elif c.type == "video": 
                    videoStream = s 
 
        # Use rtpdump to record video and audio 
        recordingPath = os.path.join(self.__path, str(recording.GetStartTime())) 
         
        # Create recording directory if it does not exist. 
        if not os.path.exists(recordingPath): 
            os.mkdir(recordingPath) 
 
        # Record video. 
        if videoStream: 
            l = videoStream.location 
            vFile = os.path.join(recordingPath, "video.rtp") 
                        
            #Usage: rtpdump -F dump -o file host/port 
            # Make sure rtp address is even.
            port = l.port - (l.port%2)
            
            rtpdump = "rtpdump" 
            args = [ 
                "-F", "dump", 
                "-o", vFile, 
                l.host+"/"+str(port), 
            ]

            self.__log.debug("Starting process: %s %s"%(rtpdump, str(args))) 
            self.__processManager.StartProcess(rtpdump,args) 
 
        else: 
            self.__log.info("VoyagerModel.Record: No video stream present in %s"%(recording.GetVenueUrl())) 
          
        # Record audio 
        if audioStream: 
            l = audioStream.location 
            aFile = os.path.join(recordingPath, "audio.rtp") 
            #Usage: rtpdump -F dump -o aFile l.host+"/"+l.port 

            # Make sure rtp address is even.
            port = l.port - (l.port%2)
            rtpdump = "rtpdump" 
            args = [ 
                "-F", "dump", 
                "-o", aFile, 
                l.host+"/"+str(port), 
            ]

            self.__log.debug("Starting process: %s %s"%(rtpdump, str(args))) 
            self.__processManager.StartProcess(rtpdump,args) 
        else: 
            self.__log.info("VoyagerModel.Record: No audio stream present in %s"%(recording.GetVenueUrl())) 
            
        # Set state 
        recording.SetName(venueName)
        recording.SetDescription("Recording from %s"%(venueName))
        self.__status = self.RECORDING 
        self.__currentRecording = recording
        self.__recordings[recording.GetStartTime()] = recording 
 
        # Update user interface 
        self.NotifyObservers() 
 
    def Remove(self, recording): 
        ''' 
        Remove a recording. 
 
        ** Arguments ** 
 
        *recording* recording instance to remove (Recording) 
        '''

        dir = os.path.join(self.__path, str(recording.GetStartTime()))
       
        files = os.listdir(dir)
        for file in files:
            os.remove(os.path.join(dir, file))
                      
        os.rmdir(dir)
        del self.__recordings[recording.GetStartTime()]
        self.NotifyObservers() 
                        
    def Stop(self): 
        ''' 
        Stop either playback or a recording. 
        ''' 
        if self.__status == self.RECORDING: 
            self.__currentRecording.SetStopTime() 
            self.SaveRecording(self.__currentRecording) 
 
        # Stop rtp dump or play 
        self.__log.debug("VoyagerModel.Stop: Terminate all processes.") 
        self.__processManager.TerminateAllProcesses() 
 
        # Set state 
        self.__currentRecording = None 
        self.__status = self.STOPPED 
        self.NotifyObservers() 
         
    def GetCurrentRecording(self): 
        ''' 
        Returns recording that is set to current. 
 
        **Returns** 
        *recording* current recording (Recording) 
        ''' 
        return self.__currentRecording 
          
    def GetRecordings(self): 
        ''' 
        Get all recordings. 
 
        **Returns** 
        *recordings* a dictionary of recording objects ( {Recording} ) 
        '''
        return self.__recordings 
         
    def GetStatus(self): 
        ''' 
        Get current status  
 
        **Returns** 
         
        *status* current status (VoyagerModel.PLAYING| 
        VoyagerModel.STOPPED| VoyagerModel.RECORDING) 
        ''' 
        return self.__status 

    def GetPlaybackVenueUrl(self):
        return self.__playbackVenueUrl
                              
class VoyagerUI(wxApp): 
    ''' 
    The main class for user interface control. This class 
    creates a voyager model and view instance. 
    ''' 
 
    def OnInit(self): 
        ''' 
        Expected by wxPython 
        ''' 
        return 1 
 
    def __init__(self, voyagerModel, log): 
        ''' 
        Create ui components and register them as observers to the 
        voyager model. 
        ''' 
        wxApp.__init__(self, False) 
        wxInitAllImageHandlers() 
        self.log = log 
         
        # Create model 
        self.voyagerModel = voyagerModel 
 
        # Create view. The view will use the model interface to 
        # access state. 
        self.voyagerView = VoyagerView(self, voyagerModel, self.log) 
        self.voyagerModel.RegisterObserver(self.voyagerView) 
         
        # Init UI
        self.SetTopWindow(self.voyagerView) 
        self.voyagerView.Show(1) 
                 
class VoyagerView(wxFrame, Observer): 
    ''' 
    View for the moderator showing all sent and received questions. 
    '''
    RECORDING_MENU_REMOVE = wxNewId()
    #RECORDING_MENU_PROPERTIES = wxNewId()
    
    def __init__(self, parent, voyagerModel, log): 
        ''' 
        Create ui components. 
        ''' 
        wxFrame.__init__(self, NULL, -1, "Voyager", size = wxSize(420, 500)) 
        Observer.__init__(self) 
 
        self.log = log 
        self.voyagerModel = voyagerModel 

        self.SetIcon(icons.getAGIconIcon()) 
        self.panel = wxPanel(self, -1)
        self.stopButton = wxButton(self.panel, wxNewId(), "Stop", size = wxSize(50, 40)) 
        self.playButton = wxButton(self.panel, wxNewId(), "Play", size = wxSize(50, 40)) 
        self.recordButton = wxButton(self.panel, wxNewId(), "Record", size = wxSize(50, 40)) 
        self.statusField = wxTextCtrl(self.panel, wxNewId(), "Use the buttons to record from a venue or play a recording from the list below.", 
                                      style= wxTE_MULTILINE | wxTE_READONLY | 
                                      wxTE_RICH, size = wxSize(-1, 32)) 
 
        # Recordings are displayed in a list. They are keyed on the start time of the 
        # recording which is also set as item data used for sorting. 
        self.recordingList = wxListCtrl(self.panel, wxNewId(), size = wxSize(150, 150), 
                                        style=wxLC_REPORT) 
        self.recordingList.InsertColumn(0, "Name") 
        self.recordingList.InsertColumn(1, "Date") 
        self.recordingList.SetColumnWidth(0, 80) 
        self.recordingList.SetColumnWidth(1, 220) 
         
        self.playButton.SetToolTipString("Play a recording") 
        self.recordButton.SetToolTipString("Record from an AG venue") 

        self.recordingMenu = wxMenu()
        self.recordingMenu.Append(self.RECORDING_MENU_REMOVE, "Remove", "Remove this recording.")
        #self.recordingMenu.Append(self.RECORDING_MENU_PROPERTIES, "Properties", "View recording details.")
      
        self.__Layout() 
        self.__SetEvents() 
        self.Update() 
 
    def __SetEvents(self): 
        ''' 
        Set UI event callbacks 
        ''' 
        EVT_BUTTON(self, self.playButton.GetId(), self.PlayCB) 
        EVT_BUTTON(self, self.recordButton.GetId(), self.RecordCB) 
        EVT_BUTTON(self, self.stopButton.GetId(), self.StopCB) 
        EVT_RIGHT_DOWN(self.recordingList, self.OnRightClick) 
        EVT_MENU(self, self.RECORDING_MENU_REMOVE, self.RemoveRecordingCB)
        #EVT_MENU(self, self.RECORDING_MENU_PROPERTIES, self.PropertiesCB)

    def OnRightClick(self, event):
        self.x = event.GetX() + self.recordingList.GetPosition().x
        self.y = event.GetY() + self.recordingList.GetPosition().y
        self.PopupMenu(self.recordingMenu, wxPoint(self.x, self.y))

    #def PropertiesCB(self, event):
    #    print 'show properties'
      
    def RemoveRecordingCB(self, event):
        id = self.recordingList.GetFirstSelected()

        if id < 0:
            dlg = wxMessageDialog(self.panel, "Select recording to remove.", "Play", 
                                  style = wxICON_INFORMATION) 
            val = dlg.ShowModal() 
            dlg.Destroy() 
            return


        # Make sure we are not currently playing or recording to this
        # recording.

        status = self.voyagerModel.GetStatus()
        currentRecording = self.voyagerModel.GetCurrentRecording()
        selectedRecordingId = self.recordingList.GetItemData(id)
        selectedRecording = self.voyagerModel.GetRecordings()[selectedRecordingId]
        val = None
        
        if (status == self.voyagerModel.RECORDING and
            currentRecording == selectedRecording):
            dlg = wxMessageDialog(self.panel, "Stop recording %s ?."%(selectedRecording.GetName()), "Remove", 
                                  style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
            val = dlg.ShowModal() 
            dlg.Destroy()
                                  
        elif (status == self.voyagerModel.PLAYING and
              currentRecording == selectedRecording):
            dlg = wxMessageDialog(self.panel, "Stop playing %s ?."%(selectedRecording.GetName()), "Remove", 
                                  style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
            val = dlg.ShowModal() 
            dlg.Destroy()
                     
        if val == wxID_NO:
            return
        elif val == wxID_YES:
            self.voyagerModel.Stop()
        
        self.voyagerModel.Remove(selectedRecording)
        
    def PlayCB(self, event): 
        ''' 
        Method used when the play button is clicked.  
        ''' 
        # Check if user want to stop current state 
        # (are we playing or recording?) 
        if not self.__TestStop(): 
            return 
 
        # Make sure user has selected a recording
        selectedItem = self.recordingList.GetFirstSelected()

        if selectedItem < 0:
            dlg = wxMessageDialog(self.panel, "Select recording to play.", "Play", 
                                  style = wxICON_INFORMATION) 
            val = dlg.ShowModal() 
            dlg.Destroy() 
            return 
 
        # Get recording instance from model. Unique id is start time. 
        startTime = self.recordingList.GetItemData(selectedItem) 
        recordings = self.voyagerModel.GetRecordings() 
 
        # Check if recording exists. 
        if recordings.has_key(startTime): 
            r = recordings[startTime] 
        else:
            dlg = wxMessageDialog(self.panel, 
                                  "Error when playing; %s was not found"
                                  %(self.voyagerModel.GetSelectedRecording().GetName()), 
                                  "Play", style = wxICON_ERROR) 
            dlg.ShowModal() 
            return 
                     
        # Open a UI where you can enter the venue url 
        dlg = VenueUrlDialog(self, -1, "Play", "Where do you want to play the %s recording?"%(r.GetName()), "https://localhost:9000/Venues/default") 
        if dlg.ShowModal() != wxID_OK: 
            return 
 
 
        wxBeginBusyCursor() 
 
        try: 
            # Start to play the recording in venue entered by user. 
            self.voyagerModel.PlayInVenue(r, dlg.GetVenueUrl()) 
        except: 
            dlg = wxMessageDialog(self.panel, 
                                  "Error when playing", 
                                  "Play", style = wxICON_ERROR) 
            dlg.ShowModal() 
            self.log.exception("VoyagerView.PlayCB: Failed to play recording %s in venue %s" 
                               %(r.GetName(), r.GetVenueUrl())) 
             
        wxEndBusyCursor() 
         
    def __TestStop(self): 
        ''' 
        Check to see if we need/want to stop an ongoing recording/playback 
        ''' 
        status =  self.voyagerModel.GetStatus() 
        current = self.voyagerModel.GetCurrentRecording() 
        dlg = None

        if status == self.voyagerModel.PLAYING and current:
            dlg = wxMessageDialog(self.panel, "Stop playing %s?"%(current.GetName()), "Record", 
                                  style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
 
        if status == self.voyagerModel.RECORDING and current: 
            dlg =  wxMessageDialog(self.panel, "Stop recording %s, %s?" %(current.GetName()), "Record", 
                                   style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
 
        if dlg: 
            val = dlg.ShowModal() 
            dlg.Destroy() 
             
            if val == wxID_NO: 
                return 0 
 
            else: 
                self.voyagerModel.Stop() 
             
        return 1 
 
    def RecordCB(self, event): 
        ''' 
        Method used when record button is clicked.  
        ''' 
        # Check to see if we need to stop a recording or playback 
        # before recording. 
        if not self.__TestStop(): 
            return 
         
        # Open a UI where you can enter the venue url 
        dlg = VenueUrlDialog(self, -1, "Record", 
                           "Which venue do you want to record from?", "https://ivs.mcs.anl.gov:9000/Venues/default") 
        if dlg.ShowModal() != wxID_OK: 
            return 
         
        venueUrl = dlg.GetVenueUrl() 
         
        nr = len(self.voyagerModel.GetRecordings()) 
        name = "Session %i"%(nr) 
         
        # Create a Recording object
        r = Recording(name, "Session 1", venueUrl) 
        wxBeginBusyCursor() 
 
        try: 
            # Start recording 
            self.voyagerModel.Record(r) 
        except: 
            self.log.exception("VoyagerView.RecordCB: Failed to record %s from %s" 
                          %(r.GetName(), r.GetVenueUrl())) 
            dlg = wxMessageDialog(self.panel, 
                                  "Error when recording", 
                                  "Record", style = wxICON_ERROR) 
            dlg.ShowModal() 
                           
        wxEndBusyCursor() 
         
    def StopCB(self, event): 
        ''' 
        Method used when stop button is clicked. 
        ''' 
        try: 
            self.voyagerModel.Stop() 
        except: 
            self.log.exception("VoyagerView.StopCB: Failed to stop") 
            dlg = wxMessageDialog(self.panel, 
                                  "Error when stopping", 
                                  "Stop", style = wxICON_ERROR) 
            dlg.ShowModal() 
         
    def Update(self): 
        ''' 
        Invoked when shared question tool model changes state. 
        ''' 
         
        status = self.voyagerModel.GetStatus() 
        currentRecording = self.voyagerModel.GetCurrentRecording() 
        recordings = self.voyagerModel.GetRecordings() 
         
        if  status == self.voyagerModel.RECORDING: 
            tooltip = "Stop recording" 
 
            statusText = "Recording from venue %s"%(currentRecording.GetVenueUrl()) 
        elif status == self.voyagerModel.PLAYING: 
            tooltip = "Stop playing" 
            statusText = "Playing %s in venue %s"%(currentRecording.GetName(), self.voyagerModel.GetPlaybackVenueUrl()) 
        elif status == self.voyagerModel.STOPPED: 
            tooltip = "Stop" 
            statusText = "Stopped" 
         
        self.stopButton.SetToolTipString(tooltip) 
        self.statusField.SetValue(statusText) 
        j = 0 
        self.recordingList.DeleteAllItems() 
        for startTime in recordings.keys():
            recording = recordings[startTime] 
            item = self.recordingList.InsertStringItem(j, 'item')
            self.recordingList.SetItemData(item, recording.GetStartTime())
            self.recordingList.SetStringItem(j, 0, recording.GetName()) 
 
            stopTime = "... " +  time.strftime("%B %d, %Y", time.localtime(recording.GetStartTime())) 
 
            if recording.GetStopTime(): 
                stopTime = time.strftime("%I:%M %p %B %d, %Y", time.localtime(recording.GetStopTime())) 
            desc = (time.strftime("%I:%M %p", time.localtime(recording.GetStartTime())) +" - "+ stopTime) 
                         
            self.recordingList.SetStringItem(j, 1, desc) 
            j = j + 1 
 
        self.recordingList.SortItems(self.SortCB) 
 
    def SortCB(self, item1, item2): 
        ''' 
        return 0 if the items are equal, negative value if the second item is less 
        than the second one and positive value if the second one is greater than 
        the second one 
        ''' 
        # We want last recording added to be first in the list. 
         
        if item1 == item2: 
            return 0 
        elif item1 < item2: 
            return 1 
        elif item1 > item2: 
            return -1 
          
    def __Layout(self): 
        ''' 
        Layout ui components. 
        ''' 
        mainSizer = wxBoxSizer(wxVERTICAL) 
         
        sizer = wxBoxSizer(wxHORIZONTAL) 
        sizer.Add(self.stopButton, 1, wxALL, 10) 
        sizer.Add(self.playButton, 1, wxALL, 10) 
        sizer.Add(self.recordButton, 1, wxALL, 10) 
        mainSizer.Add(sizer, 0, wxEXPAND|wxLEFT|wxRIGHT|wxTOP, 20) 
        mainSizer.Add(self.statusField, 0, wxEXPAND| wxLEFT | wxRIGHT, 30) 
        mainSizer.Add(wxSize(10,10)) 
        mainSizer.Add(wxStaticLine(self.panel, -1), 0, wxEXPAND | wxLEFT|wxRIGHT, 30) 
        mainSizer.Add(wxSize(10,10)) 
                 
        box = wxStaticBox(self.panel, -1, "My Recordings") 
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)) 
        sizer = wxStaticBoxSizer(box, wxVERTICAL) 
        sizer.Add(self.recordingList, 1, wxEXPAND| wxALL, 10) 
        mainSizer.Add(sizer, 1, wxEXPAND|wxLEFT|wxRIGHT, 30) 
        mainSizer.Add(wxSize(10,10)) 
 
        self.panel.SetSizer(mainSizer) 
        mainSizer.Fit(self.panel) 
        self.panel.SetAutoLayout(1) 
 
class VenueUrlDialog(wxDialog): 
    ''' 
    Dialog for entering venue url. 
    ''' 
    def __init__(self, parent, id, title, text, url): 
        wxDialog.__init__(self, parent, id, title) 
        self.venueText = wxStaticText(self, -1, "Venue URL: ") 
        self.venueUrlCtrl = wxTextCtrl(self, -1, 
                                       url, 
                                       size = wxSize(400, -1)) 
        self.text = wxStaticText(self, -1, text) 
        self.okButton = wxButton(self, wxID_OK, "Ok") 
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel") 
        self.okButton.SetFocus() 

        self.okButton.SetFocus()
        self.__Layout() 
 
    def GetVenueUrl(self): 
        ''' 
        Returns the url entered by the user. 
        ''' 
        return self.venueUrlCtrl.GetValue() 
 
    def __Layout(self): 
        sizer = wxBoxSizer(wxVERTICAL) 
        sizer.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20) 
 
        sizer2 = wxBoxSizer(wxHORIZONTAL) 
        sizer2.Add(self.venueText, 0) 
        sizer2.Add(self.venueUrlCtrl, 1, wxEXPAND) 
 
        sizer.Add(sizer2, 0, wxEXPAND | wxALL, 20) 
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND | wxALL, 5) 
 
        sizer3 =  wxBoxSizer(wxHORIZONTAL) 
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10) 
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10) 
 
        sizer.Add(sizer3, 0, wxALIGN_CENTER) 
        self.SetSizer(sizer) 
        sizer.Fit(self) 
        self.SetAutoLayout(1) 
 
         
if __name__ == "__main__":
    wxapp = wxPySimpleApp()
    app = WXGUIApplication() 
    init_args = ["--debug"] 

    # Initialize AG environment 
    try:
        app.Initialize("Voyager", args = init_args)
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)

   
    if not app.certificateManager.HaveValidProxy():
        sys.exit(-1)
        
    wxapp.Destroy()    

    # Create model and view 
    v = VoyagerModel(app.GetLog()) 
    uiApp = VoyagerUI(v, app.GetLog()) 
    # Start application main thread 
    uiApp.MainLoop() 

