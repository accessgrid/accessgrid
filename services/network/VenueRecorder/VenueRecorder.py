#-----------------------------------------------------------------------------
# Name:        VenueRecorder.py
# Purpose:     Tool for recording and playback of AG sessions. 
# 
# Author:      Susanne Lefvert 
# 
# Created:     $Date: 2005-02-25 22:24:53 $ 
# RCS-ID:      $Id: VenueRecorder.py,v 1.1 2005-02-25 22:24:53 lefvert Exp $ 
# Copyright:   (c) 2002 
# Licence:     See COPYING.TXT 
#----------------------------------------------------------------------------- 

import getopt 
import sys 
import time 
import os
import string
import zipfile
 
from wxPython.wx import * 
from ObserverPattern import Observer, Model 
 
from AccessGrid.Toolkit import WXGUIApplication 
from AccessGrid import icons 
from AccessGrid.Venue import VenueIW 
from AccessGrid.Platform.ProcessManager import ProcessManager 
from AccessGrid.Utilities import LoadConfig, SaveConfig
from AccessGrid.Platform import IsWindows, IsLinux
from AccessGrid.GUID import GUID

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
        self.__id = str(GUID()) # unique key for a recording
        self.__startTime = time.mktime(time.localtime())
        self.__stopTime = None 
        self.__venueUrl = venueUrl
       
    def Save(self, path):
        '''
        Write the recording config to file.

        **Arguments**
        
        *path* path to the recording file (string)
        '''
        # Write config file to path
        config = {}
        config['Recording.name'] = self.__name
        config['Recording.description'] = self.__description
        config['Recording.startTime'] = self.__startTime
        config['Recording.stopTime'] = self.__stopTime
        config['Recording.venueUrl'] = self.__venueUrl
        config['Recording.id']= self.__id
        
        SaveConfig(path, config)

    def LoadRecording(path):
        '''
        Static method to load a recording from file.
        
        **Arguments**

        *path* path where recording config file is located (string)

        **Returns**

        *recording* the loaded recording (Recording)
        '''
        config = LoadConfig(path)
        r = Recording(config["Recording.name"],
                      config["Recording.description"],
                      config["Recording.venueUrl"])
        r.SetStartTime(config["Recording.startTime"])
        r.SetStopTime(config["Recording.stopTime"])
        r.SetId(config["Recording.id"])
        return r

    # Makes it possible to access the method without an instance.
    LoadRecording = staticmethod(LoadRecording)

    def ExportToZipFile(self, path, archivePath):
        '''
        Export recording to zip file.

        **Arguments**
        
        *path* path where recording is located. (string)
        *archivePath* path to the zip archive to export to. (string)
        '''
        log.debug("VenueRecorderModel.ExportToZipFile: write %s to archive %s"%(self.__name, archivePath))

        # Get recorded files
        dir = self.GetId()
        recordingPath = os.path.join(path, str(dir))
        
        # open the zip file for writing
        if os.path.isdir(recordingPath):
            file = zipfile.ZipFile(archivePath, "w")

            files = os.listdir(recordingPath)
            for f in files:
                path = os.path.join(recordingPath, f)
                        
                # Write recorded files to zip archive
                if os.path.isfile(path):
                    file.write(str(path), str(f))
                else:
                    log.error("Recording.WriteToZipFile: This is not a file"
                              %path)
                    
            file.close()
        else:
            log.error("Recording.WriteToZipFile: This is not a directory"
                      %recordingPath)
                  
    # Set methods 
 
    def SetName(self, name): 
        self.__name = name 

    def SetDescription(self, desc):
        self.__description = desc
   
    def SetStartTime(self, startTime = None):
        if startTime != None:
            self.__startTime = float(startTime)
        else:
            self.__startTime = time.mktime(time.localtime())
                     
    def SetStopTime(self, stopTime = None):
        if stopTime:
            self.__stopTime = float(stopTime)
        else:
            self.__stopTime = time.mktime(time.localtime())

    def SetId(self, id):
        self.__id = id
 
    # Get methods 
 
    def GetVenueUrl(self): 
        return self.__venueUrl 

    def GetId(self):
        return self.__id
         
    def GetStartTime(self):
        return self.__startTime 
             
    def GetStopTime(self): 
        return self.__stopTime 
 
    def GetName(self): 
        return self.__name 
 
    def GetDescription(self): 
        return self.__description 
     
 
class VenueRecorderModel(Model): 
    """ 
    The voyager model class includes all logic for the program. There
    is no user interface code in this class. The ui and the model is
    separated using the observer pattern for easy separation. When
    state gets updated in the model, all obervers are notified and
    updates the view/ui.  The voyager model includes methods for recording
    and playback of venue media streams, as well as organization 
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

        homePath = None
        name = None
        
        if IsWindows():
            from win32com.shell import shell, shellcon
            homePath = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
            name = "VenueRecorder"

        elif IsLinux():
            homePath = os.environ['HOME']
            name = ".VenueRecorder"
             
        else:
            self.__log.debug("VenueRecorderModel.__init__: VenueRecorder only supports windows and linux for now.")
            sys.exit(-1)
            
        if not homePath:
            self.__log.debug("VenueRecorderModel.__init__: Home path not found")
            sys.exit(-1)
       
        self.__path = os.path.join(homePath, 
                                   name) 
        self.__processManager = ProcessManager() 
 
        if not os.path.exists(self.__path): 
            os.mkdir(self.__path) 
 
        self.__log.debug("VenueRecorderModel.__init__: Persistence path: %s"
                         %(self.__path)) 
        self.__LoadRecordings()
               
    def __LoadRecordings(self): 
        ''' 
        Load recordings from file. 
        '''
        # For each directory in the voyager path
        # load description config file and create a
        # recording.

        if not os.path.exists(self.__path):
            self.__log.error("VenueRecorderModel.__LoadRecordings: home path does not exist %s"%(self.__path))
                      
        dirs = os.listdir(self.__path)
        for dir in dirs:
            path = os.path.join(self.__path, dir)
            if os.path.isdir(path):
                rFile = os.path.join(path, dir +".txt")
                if os.path.isfile(rFile):
                    recording = Recording.LoadRecording(rFile)
                    self.__recordings[recording.GetId()] = recording
                else:
                    self.__log.error("VenueRecorderModel.__LoadRecordings: This is not a file %s"%rFile)
            else:
                self.__log.error("VenueRecorderModel.__LoadRecordings: This is not a directory %s"%path)

    def GetRecordingFromZipFile(self, archivePath):
        '''
        Get a recording instance from a zip file.

        **Arguments**

        *archivePath* Path to the archive to examine (string)
        '''
        # Open zip file
        dirName = None
        try:
            self.__log.debug("VenueRecorderModel.ImportFromZipFile: open zipfile %s"%archivePath)
            file = zipfile.ZipFile(archivePath, "r")
        except:  
            self.__log.error("VenueRecorderModel.ImportFromZipFile: bad zip file %s"%archivePath)
            raise Exception, "VenueRecorderModel.ImportFromZipFile: failed to import zip archive"
            
        # Read files
        for name in file.namelist():
            self.__log.debug("VenueRecorderModel.ImportFromZipFile: examine %s in %s"%(name, archivePath))
            if name.endswith(".txt"): 
                # The description file is named after the
                # unique id of the recording.
                dirName = name.split(".")[0]

        file.close()

        if dirName:
            path = os.path.join(self.__path, dirName, dirName+".txt")
            if os.path.exists(path):
                recording = Recording.LoadRecording(path)
                return recording
            else:
                return None
        else:
            self.__log.error("Could not get id from zip file %s"%archivePath)
            raise Exception, "Could not get id from zip file %s"%archivePath
                    

    def ExportToZipFile(self, recordings, archivePath):
        '''
        Export a recording to a zip file.

        **Arguments**
        
        *recordings* list of recording instances to export (Recording)

        *archivePath* path to the zip archive (string)
        '''
        for recording in recordings:
            recording.ExportToZipFile(self.__path, archivePath)

    def ImportFromZipFile(self, archivePath):
        '''
        Import a recording from a zip file.

        **Arguments**
        
        *archivePath* Path to the zip archive to import. (string)
        '''
        self.__log.debug("VenueRecorderModel.ImportFromZipFile: Import from zip archive %s"%(archivePath))

        # Open zip file
        self.__log.debug("VenueRecorderModel.ImportFromZipFile: open zipfile %s"%archivePath)
        file = zipfile.ZipFile(archivePath, "r")
            
        # Read files
        for name in file.namelist():
            self.__log.debug("VenueRecorderModel.ImportFromZipFile: examine %s in %s"%(name, archivePath))
            if name.endswith(".txt"): 
                # The description file is named after the
                # unique id of the recording.
                dirName = name.split(".")[0]
                descFileName = name
                descFile = file.read(name)
                
            elif name.endswith("video.rtp"):
                videoFileName = name
                videoFile = file.read(name)
                
            elif name.endswith("audio.rtp"):
                audioFileName = name
                audioFile = file.read(name)
                                    
            else:
                self.__log.error("VenueRecorderModel.ImportFromZipFile: Wrong file format for voyager %s"%name)
                
        file.close()

        if not dirName:
            self.__log("there is no description file %s present in this zip file, import failed."%(dirName))
            return

        # Save files in voyager directory named after
        # unique id of recording.
        newDir = os.path.join(self.__path, dirName)
        self.__log.debug("VenueRecorderModel.ImportFromZipFile: Import files to %s"%self.__path)
      
        if not os.path.exists(newDir):
            os.mkdir(newDir)
              
        # Try to write the files
        descFilePath = os.path.join(newDir, descFileName)
        f = open(descFilePath, "w" )
        f.write(str(descFile))
        f.close()
        
        videoFilePath = os.path.join(newDir, videoFileName)
        f = open(videoFilePath, "w")
        f.write(str(videoFile))
        f.close()

        audioFilePath = os.path.join(newDir, audioFileName)
        f = open(audioFilePath, "w")
        f.write(str(audioFile))
        f.close()
        
        # Create  a recording object
        recording = Recording.LoadRecording(descFilePath)
        self.__recordings[recording.GetId()] = recording
        self.NotifyObservers()

    def UpdateRecording(self, recording):
        '''
        Update data for a recording

        **Arguments**
        
        *recording* The new recording instance (Recording)
        '''
        # Unique ID remains the same.
        self.__recordings[recording.GetId()] = recording
        self.SaveRecording(recording)

        self.NotifyObservers()

    def SaveRecording(self, recording): 
        ''' 
        Save a recording to file. 
 
        **Arguments** 
         
        *recording* recording instance to save (Recording) 
        '''
        recordingPath = os.path.join(self.__path,
                                     str(recording.GetId()))
        name = str(recording.GetId())+".txt"
        descFile = os.path.join(recordingPath, name)
        recording.Save(descFile)
 
    def PlayInVenue(self, recording, venueUrl): 
        ''' 
        Method for playing a recording in a venue.  This method connects 
        to a venue at venueUrl and retreives multicast information.
        After that, the recording can be transmitted using rtpplay to
        the retreived venue addresses. 
 
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
        recordingPath = os.path.join(self.__path,
                                     str(recording.GetId())) 
        
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
            self.__log.info("VenueRecorderModel.PlayInVenue: No audio stream present in %s"%(venueUrl)) 
           
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
            self.__log.info("VenueRecorderModel.PlayInVenue: No video stream present in %s"%(venueUrl)) 
 
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
        recordingPath = os.path.join(self.__path,
                                     str(recording.GetId())) 
         
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
            self.__log.info("VenueRecorderModel.Record: No video stream present in %s"%(recording.GetVenueUrl())) 
          
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
            self.__log.info("VenueRecorderModel.Record: No audio stream present in %s"%(recording.GetVenueUrl())) 
            
        # Set state 
        recording.SetName(venueName)
        recording.SetDescription("Recording from %s"%(venueName))
        self.__status = self.RECORDING 
        self.__currentRecording = recording
        self.__recordings[recording.GetId()] = recording 
 
        # Update user interface 
        self.NotifyObservers() 
 
    def Remove(self, recording): 
        ''' 
        Remove a recording. 
 
        ** Arguments ** 
 
        *recording* recording instance to remove (Recording) 
        '''
        dir = os.path.join(self.__path, str(recording.GetId()))
       
        files = os.listdir(dir)
        for file in files:
            os.remove(os.path.join(dir, file))
                      
        os.rmdir(dir)
        del self.__recordings[recording.GetId()]
        self.NotifyObservers() 
                        
    def Stop(self): 
        ''' 
        Stop either playback or a recording. 
        '''
        if self.__status == self.RECORDING: 
            self.__currentRecording.SetStopTime() 
            self.SaveRecording(self.__currentRecording) 
 
        # Stop rtp dump or play 
        self.__log.debug("VenueRecorderModel.Stop: Terminate all processes.") 
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
         
        *status* current status (VenueRecorderModel.PLAYING| 
        VenueRecorderModel.STOPPED| VenueRecorderModel.RECORDING) 
        '''        
        return self.__status 

    def GetPlaybackVenueUrl(self):
        '''
        Get the venue we are playing back in.

        **Returns**
        
        *venueUrl* a venue url (string)
        '''
        return self.__playbackVenueUrl

    def GetPath(self):
        '''
        Returns base path for voyager.

        **Returns**
        
        *path* voyager base path (string)
        '''
        return self.__path
                              
class VenueRecorderUI(wxApp): 
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
        self.voyagerView = VenueRecorderView(self, voyagerModel, self.log) 
        self.voyagerModel.RegisterObserver(self.voyagerView) 
         
        # Init UI
        self.SetTopWindow(self.voyagerView) 
        self.voyagerView.Show(1) 
                 
class VenueRecorderView(wxFrame, Observer): 
    ''' 
    View for voyager containing ui components.
    '''
    RECORDING_MENU_REMOVE = wxNewId()
    RECORDING_MENU_EXPORT = wxNewId()
    RECORDING_MENU_EXPORT_ALL = wxNewId()
    RECORDING_MENU_IMPORT = wxNewId()
    RECORDING_MENU_PROPERTIES = wxNewId()
    
    def __init__(self, parent, voyagerModel, log): 
        ''' 
        Create ui components. 
        ''' 
        wxFrame.__init__(self, NULL, -1, "Personal AG Recorder", size = wxSize(420, 500)) 
        Observer.__init__(self) 
 
        self.log = log 
        self.voyagerModel = voyagerModel 
        self.intToGuid = {}
        
        self.SetIcon(icons.getAGIconIcon()) 
        self.panel = wxPanel(self, -1)
        self.stopButton = wxButton(self.panel, wxNewId(), "Stop",
                                   size = wxSize(50, 40)) 
        self.playButton = wxButton(self.panel, wxNewId(), "Play",
                                   size = wxSize(50, 40)) 
        self.recordButton = wxButton(self.panel, wxNewId(), "Record",
                                     size = wxSize(50, 40)) 
        self.statusField = wxTextCtrl(self.panel, wxNewId(), "Use the buttons to record from a venue or play a recording from the list below.", 
                                      style= wxTE_MULTILINE | wxTE_READONLY | 
                                      wxTE_RICH, size = wxSize(-1, 32)) 
 
        # Recordings are displayed in a list. They are keyed on the
        # unique id returned from recording.GetId()
        self.recordingList = wxListCtrl(self.panel, wxNewId(),
                                        size = wxSize(150, 150), 
                                        style=wxLC_REPORT) 
        self.recordingList.InsertColumn(0, "Name") 
        self.recordingList.InsertColumn(1, "Date") 
        self.recordingList.SetColumnWidth(0, 80) 
        self.recordingList.SetColumnWidth(1, 220) 
         
        self.playButton.SetToolTipString("Play a recording") 
        self.recordButton.SetToolTipString("Record from an AG venue") 

        self.recordingMenu = wxMenu()
        self.recordingMenu.Append(self.RECORDING_MENU_REMOVE, "Remove",
                                  "Remove this recording.")
        self.recordingMenu.AppendSeparator()
        self.recordingMenu.Append(self.RECORDING_MENU_IMPORT, "Import",
                                  "Load recordings")
        self.recordingMenu.Append(self.RECORDING_MENU_EXPORT, "Export",
                                  "Save this recording to file")
        self.recordingMenu.AppendSeparator()
        self.recordingMenu.Append(self.RECORDING_MENU_PROPERTIES, "Properties", "View recording details.")

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
        EVT_RIGHT_DOWN(self.recordingList, self.OnRightClickCB) 
        EVT_MENU(self, self.RECORDING_MENU_REMOVE, self.RemoveRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_EXPORT, self.ExportRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_EXPORT_ALL,
                 self.ExportRecordingAllCB)
        EVT_MENU(self, self.RECORDING_MENU_IMPORT, self.ImportRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_PROPERTIES, self.PropertiesCB)

    def ShowMessage(self, parent, text, title, style):
        '''
        Show a message dialog.
        '''
        dlg = wxMessageDialog(parent, text,
                              title, 
                              style) 
        val = dlg.ShowModal() 
        dlg.Destroy()
        return val

    def OnRightClickCB(self, event):
        '''
        Invoked when a user right clicks on the recording list.
        '''
        self.x = event.GetX() + self.recordingList.GetPosition().x
        self.y = event.GetY() + self.recordingList.GetPosition().y
        self.PopupMenu(self.recordingMenu, wxPoint(self.x, self.y))

    def PropertiesCB(self, event):
        '''
        Invoked when a user selects the properties menu item for
        a recording.
        '''
        # Get selected recording
        id = self.recordingList.GetFirstSelected()
        
        if id < 0:
            val = self.ShowMessage(self.panel, "Select a recording.",
                                  "Properties", 
                                  style = wxICON_INFORMATION)
            return

        uniqueId = self.intToGuid[id]
        recording = self.voyagerModel.GetRecordings()[uniqueId]

        # Open a UI to display properties 
        dlg = PropertiesDialog(self, -1,
                               recording,
                               self.voyagerModel)
        if dlg.ShowModal() == wxID_OK:
            r = dlg.GetRecording()
            # Only update if recording properties changed
            if r:
                self.voyagerModel.UpdateRecording(r)
              
    def ImportRecordingCB(self, event):
        '''
        Invoked when a user selects the import menu item for a recording.
        '''
        wildcard = "AG Recordings |*.agrcd|" \
                   "All Files |*.*"
        
        # Get path from user.
        dlg = wxFileDialog(self, "Choose file(s):",
                           wildcard = wildcard,
                           style = wxOPEN)
        if dlg.ShowModal() == wxID_OK:
            fileName = dlg.GetPath()
            
            dlg.Destroy()

        else:
            return

        recording = None
        try:
            recording = self.voyagerModel.GetRecordingFromZipFile(fileName)
        except:
            self.log.exception("VenueRecorderView.ImportRecordingCB: Get recording from zip file failed %s "%(fileName))

            val = self.ShowMessage(self.panel,
                                   "Failed to import %s."
                                   %(fileName),
                                   "Error", 
                                   style = wxICON_ERROR) 
            return
            
        if recording:
            val = self.ShowMessage(self.panel, "The recording already exists with name %s, do you want to overwrite it?."%(recording.GetName()),
                                   "Export", 
                                   style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
            if not val == wxID_YES:
                return
        try:
            self.voyagerModel.ImportFromZipFile(fileName)
        except:
            val = self.ShowMessage(self.panel,
                                   "Failed to import %s."
                                   %(fileName),
                                   "Error", 
                                   style = wxICON_ERROR) 
               
    def ExportRecordingCB(self, event):
        '''
        Invoked when a user selects the export menu item of a recording.
        '''
        # Get selected recording
        id = self.recordingList.GetFirstSelected()

        if id < 0:
            val = self.ShowMessage(self.panel, "Select recording to export.",
                                   "Export", 
                                   style = wxICON_INFORMATION) 
            return
        
        uniqueId = self.intToGuid[id]
        recording = self.voyagerModel.GetRecordings()[uniqueId]

        # Set default name
        noSpacesName = string.replace(recording.GetName(), " ", "_")
        startTime = time.strftime("%m_%d_%Y",
                                  time.localtime(recording.GetStartTime())) 

        name = noSpacesName+'--'+startTime+".agrcd"
      
        # Get path from user.
        wildcard = "AG Recordings |*.agrcd|" \
                   "All Files |*.*"


        notOverwrite = 1
        while notOverwrite:
          
            dlg = wxFileDialog(self, "Choose file(s):",
                               wildcard = wildcard, 
                               defaultFile = name,
                               style = wxSAVE)
            if dlg.ShowModal() == wxID_OK:
                fileName = dlg.GetPath()
                
                dlg.Destroy()
                
            else:
                return

            # Check to see if we have this already and if user wants to
            # overwrite the archive.
        
            if os.path.exists(fileName):
                val = self.ShowMessage(self.panel, 
                                       "The archive %s already exists, do you want to overwrite?" %(fileName),
                                       "Overwrite?",
                                       style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
                if val == wxID_YES:
                    notOverwrite = 0
                    try:
                        self.voyagerModel.ExportToZipFile([recording], fileName)
                    except:
                        self.log.exception("VenueRecorderModel.ExportRecordingCB: Export to zip file failed. %s"%(fileName))

                        val = self.ShowMessage(self.panel,
                                               "Export recording failed.",
                                               "Export", 
                                               style = wxICON_ERROR)               
            else:
                notOverwrite = 0
                self.voyagerModel.ExportToZipFile([recording], fileName)
               
    def ExportRecordingAllCB(self, event):
        defaultName = os.path.join(os.getcwd(), "RecordingList.agrcd)") 
        # Get path from user.
        dlg = wxFileDialog(self, "Choose file(s):",
                           defaultFile = defaultName,
                           style = wxSAVE)
        if dlg.ShowModal() == wxID_OK:
            fileName = dlg.GetPath()
            dlg.Destroy()

        else:
            return

        self.voyagerModel.ExportAllToZipFile(fileName)
      
    def RemoveRecordingCB(self, event):
        '''
        Invoked when a user selects remove from the recording menu.
        '''
        id = self.recordingList.GetFirstSelected()

        if id < 0:
            val = self.ShowMessage(self.panel, "Select recording to remove.",
                                   "Remove", 
                                   style = wxICON_INFORMATION) 
            return

        status = self.voyagerModel.GetStatus()
        currentRecording = self.voyagerModel.GetCurrentRecording()
        selectedRecordingId = self.intToGuid[id]
        selectedRecording = self.voyagerModel.GetRecordings()[selectedRecordingId]
        val = None

        # Maker sure user really wants to remove the recording.
        val = self.ShowMessage(self.panel, "Are you sure you want to remove %s."%(selectedRecording.GetName()),
                               "Remove", 
                               style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
        # Make sure we are not currently playing or recording to this
        # recording.
        if (status == self.voyagerModel.RECORDING and
            currentRecording == selectedRecording):
            val = self.ShowMessage(self.panel, "Stop recording %s ?."
                             %(selectedRecording.GetName()), "Remove", 
                             style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT)                                   
        elif (status == self.voyagerModel.PLAYING and
              currentRecording == selectedRecording):
            val = self.ShowMessage(self.panel, "Stop playing %s ?."
                                   %(selectedRecording.GetName()), "Remove", 
                                   style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
                               
        if val == wxID_NO:
            return
        elif val == wxID_YES:
            try:
                self.voyagerModel.Stop()
            except:
                self.log.exception("VenueRecorderView.RemoveRecordingCB: failed to stop player.")
        try:
            self.voyagerModel.Remove(selectedRecording)
        except:
            val = self.ShowMessage(self.panel, "Error when removing.",
                                   "Error", 
                                   style = wxICON_ERROR) 

    def PlayCB(self, event): 
        ''' 
        Invoked when the play button is clicked.  
        ''' 
        # Check if user want to stop current state 
        # (are we playing or recording already?) 
        if not self.__TestStop(): 
            return 
 
        # Make sure user has selected a recording
        selectedItem = self.recordingList.GetFirstSelected()

        if selectedItem < 0:
            val = self.ShowMessage(self.panel, "Select recording to play.",
                                   "Play", 
                                   style = wxICON_INFORMATION) 
            return 
 
        # Get recording instance from model. Unique id is start time. 
        id = self.intToGuid[selectedItem]
        name = self.recordingList.GetItemText(selectedItem)
               
        recordings = self.voyagerModel.GetRecordings() 
 
        # Check if recording exists. 
        if recordings.has_key(id): 
            r = recordings[id] 
        else:
            val = self.ShowMessage(self.panel, 
                                   "Error when playing; %s was not found"
                                   %(self.voyagerModel.GetSelectedRecording().GetName()), 
                                   "Play", style = wxICON_ERROR) 
            return 
                     
        # Open a UI where you can enter the venue url 
        dlg = VenueUrlDialog(self, -1, "Play",
                             "Where do you want to play the %s recording?"
                             %(r.GetName()),
                             "https://localhost:9000/Venues/default") 
        if dlg.ShowModal() != wxID_OK: 
            return 
 
 
        wxBeginBusyCursor() 
        
        venueUrl = dlg.GetVenueUrl()
 
        try: 
            # Start to play the recording in venue entered by user. 
            self.voyagerModel.PlayInVenue(r, venueUrl) 
        except:
            val = self.ShowMessage(self.panel, 
                                   "Error when playing", 
                                   "Play", style = wxICON_ERROR) 
            self.log.exception("VenueRecorderView.PlayCB: Failed to play recording %s in venue %s" 
                               %(r.GetName(), venueUrl)) 
            
        wxEndBusyCursor() 
         
    def __TestStop(self): 
        ''' 
        Check to see if we need/want to stop an ongoing recording/playback 
        ''' 
        status =  self.voyagerModel.GetStatus() 
        current = self.voyagerModel.GetCurrentRecording() 
        dlg = None

        if status == self.voyagerModel.PLAYING and current:
            dlg = wxMessageDialog(self.panel, "Stop playing %s?"
                                  %(current.GetName()), "Record", 
                                  style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
 
        if status == self.voyagerModel.RECORDING and current: 
            dlg =  wxMessageDialog(self.panel, "Stop recording %s ?"
                                   %(current.GetName()), "Record", 
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
        Invoked when the record button is clicked.  
        ''' 
        # Check to see if we need to stop a recording or playback 
        # before recording. 
        if not self.__TestStop(): 
            return 
         
        # Open a UI where you can enter the venue url 
        dlg = VenueUrlDialog(self, -1, "Record", 
                             "Which venue do you want to record from?",
                             "https://ivs.mcs.anl.gov:9000/Venues/default") 
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
            self.log.exception("VenueRecorderView.RecordCB: Failed to record %s from %s" 
                          %(r.GetName(), r.GetVenueUrl())) 

            val = self.ShowMessage(self.panel, 
                                   "Error when recording", 
                                   "Record", style = wxICON_ERROR) 
                                       
        wxEndBusyCursor() 
         
    def StopCB(self, event): 
        ''' 
        Invoked when the stop button is clicked. 
        ''' 
        try: 
            self.voyagerModel.Stop() 
        except: 
            self.log.exception("VenueRecorderView.StopCB: Failed to stop")
            val = self.ShowMessage(self.panel, 
                                   "Error when stopping", 
                                   "Stop", style = wxICON_ERROR) 
                    
    def Update(self): 
        ''' 
        Invoked when the voyager model changes state. This
        methods updates the ui based on current state of the model
        based on the Model-View-Controller pattern.
        ''' 
        # match up a GUID with an integer since
        # only integers are allowed as data in wxListCtrl.
        self.intToGuidDict = {}

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
        for id in recordings.keys():
            recording = recordings[id] 
            
            item = self.recordingList.InsertStringItem(j, 'item')
            self.recordingList.SetStringItem(j, 0, recording.GetName()) 
            self.intToGuid[item] = recording.GetId()
 
            stopTime = "... " +  time.strftime("%b %d, %Y",
                                               time.localtime(recording.GetStartTime())) 
 
            if recording.GetStopTime(): 
                stopTime = time.strftime("%I:%M %p %b %d, %Y",
                                         time.localtime(recording.GetStopTime())) 
            desc = (time.strftime("%I:%M %p",
                                  time.localtime(recording.GetStartTime())) +" - "+ stopTime) 
                         
            self.recordingList.SetStringItem(j, 1, desc) 
            j = j + 1 
 
        self.recordingList.SortItems(self.SortCB) 
 
    def SortCB(self, item1, item2): 
        ''' 
        return 0 if the items are equal, positive value if first 
        item is greater than the second one and negative value if the
        second one is greater than the first one. Used to sort the
        list.
        ''' 
        # We want last recording added to be first in the list. 
         
        if item1 == item2: 
            return 0 
        elif item1 > item2: 
            return 1 
        elif item1 < item2: 
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
        mainSizer.Add(wxStaticLine(self.panel, -1), 0,
                      wxEXPAND | wxLEFT|wxRIGHT, 30) 
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
        '''
        Layout of UI components.
        '''
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

class PropertiesDialog(wxDialog): 
    ''' 
    Dialog for displaying recording properties. 
    ''' 
    def __init__(self, parent, id, recording, voyagerModel): 
        wxDialog.__init__(self, parent, id, "Recording Properties")
        self.recording = recording
        self.voyagerModel = voyagerModel
        
        start = time.strftime("%I:%M:%S %p, %b-%d-%Y",
                              time.localtime(recording.GetStartTime())) 
        stop = time.strftime("%I:%M:%S %p, %b-%d-%Y",
                             time.localtime(recording.GetStopTime()))

        duration = recording.GetStopTime()-recording.GetStartTime()# Seconds

        # Calculate audio and video file sizes in bytes
        video = os.path.join(self.voyagerModel.GetPath(),
                             str(recording.GetId()), "video.rtp")
        audio = os.path.join(self.voyagerModel.GetPath(),
                             str(recording.GetId()), "audio.rtp")
        videoSize = str(os.path.getsize(video))
        audioSize = str(os.path.getsize(audio))
        # Must be a library somewhere that does this...

        # Calculate duration.

        # hours
        durationText = ""
        hours = int(duration / 3600.0)

        if hours >= 1:
            duration - (hours*3600.0)
            durationText = str(hours)+" hours "
            
        # minutes
        minutes = int(duration/60.0)
        
        if minutes >= 1:
            duration = duration - (minutes*60.0)
            durationText = durationText + str(minutes) + " min. "
            
        # seconds
        durationText = durationText + str(duration) + " sec."
                           
        self.nameText = wxStaticText(self, -1, "Name: ") 
        self.nameCtrl = wxTextCtrl(self, -1, 
                                   recording.GetName())
        self.descText = wxStaticText(self, -1, "Description: ") 
        self.descCtrl = wxTextCtrl(self, -1, recording.GetDescription(), 
                                   style = wxTE_MULTILINE, 
                                   size = wxSize(300, 50))
        self.startText = wxStaticText(self, -1, "Start Time:  ") 
        self.startCtrl = wxTextCtrl(self, -1, 
                                    start,
                                    style = wxTE_READONLY)
        self.stopText = wxStaticText(self, -1, "Stop Time: ") 
        self.stopCtrl = wxTextCtrl(self, -1, 
                                   stop,
                                   style = wxTE_READONLY)
        self.durationText = wxStaticText(self, -1, "Duration: ") 
        self.durationCtrl = wxTextCtrl(self, -1, 
                                       durationText,
                                       style = wxTE_READONLY)
        self.audioSizeText = wxStaticText(self, -1, "Audio Size: ") 
        self.audioSizeCtrl = wxTextCtrl(self, -1, 
                                        audioSize+" bytes",
                                        style = wxTE_READONLY,
                                        size = wxSize(70, -1))
        self.videoSizeText = wxStaticText(self, -1, "Video Size: ") 
        self.videoSizeCtrl = wxTextCtrl(self, -1, 
                                        videoSize+" bytes",
                                        style = wxTE_READONLY,
                                        size = wxSize(70, -1)) 
        self.okButton = wxButton(self, wxID_OK, "Ok") 
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel") 
        
        self.okButton.SetFocus()
        self.__Layout()
 
    def GetRecording(self): 
        ''' 
        Returns the url entered by the user. 
        '''
        oldName = self.recording.GetName()
        newName = self.nameCtrl.GetValue()
        oldDesc = self.recording.GetDescription()
        newDesc = self.descCtrl.GetValue()
        changed = 0
        
        if oldName != newName:
            self.recording.SetName(newName)
            changed = 1
        if oldDesc != newDesc:
            self.recording.SetDescription(newDesc)
            changed = 1

        if changed:
            return self.recording
        else:
            return None
 
    def __Layout(self):
        '''
        Layout of UI components.
        '''
        sizer = wxBoxSizer(wxVERTICAL) 
        
        s2 =  wxFlexGridSizer(0, 2, 5, 5)
        s2.Add(self.nameText, 0) 
        s2.Add(self.nameCtrl, 1, wxEXPAND)
        s2.Add(self.descText, 0)
        s2.Add(self.descCtrl, 1, wxEXPAND)
        s2.AddGrowableCol(1)
        sizer.Add(s2, 0, wxEXPAND | wxALL, 10) 

        s4 = wxFlexGridSizer(3, 4, 5, 5)
        s4.Add(self.startText)
        s4.Add(self.startCtrl, 1, wxEXPAND|wxRIGHT, 5)
        s4.Add(self.audioSizeText)
        s4.Add(self.audioSizeCtrl, 1, wxEXPAND)
        s4.Add(self.stopText)
        s4.Add(self.stopCtrl, 1, wxEXPAND|wxRIGHT, 5)
        s4.Add(self.videoSizeText)
        s4.Add(self.videoSizeCtrl, 1, wxEXPAND)
        s4.Add(self.durationText)
        s4.Add(self.durationCtrl, 1, wxEXPAND|wxRIGHT, 5)
        s4.AddGrowableCol(1)
        sizer.Add(s4, 0, wxEXPAND|wxLEFT|wxRIGHT|wxBOTTOM, 10)
        
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND, 5) 
 
        sizer3 =  wxBoxSizer(wxHORIZONTAL) 
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10) 
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10) 
 
        sizer.Add(sizer3, 0, wxALIGN_CENTER) 
        self.SetSizer(sizer) 
        sizer.Fit(self) 
        self.SetAutoLayout(1) 
 
         
if __name__ == "__main__":

    # We need the simple wx app for when the
    # app.HaveValidProxy() call opens a
    # passphrase dialog.
    wxapp = wxPySimpleApp()
    
    # Initialize AG environment
    app = WXGUIApplication() 
    init_args = ["--debug"]
    
    try:
        app.Initialize("VenueRecorder", args = init_args)
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
   
    if not app.certificateManager.HaveValidProxy():
        sys.exit(-1)

    # Create model and view 
    v = VenueRecorderModel(app.GetLog())
    log = app.GetLog()
    uiApp = VenueRecorderUI(v, app.GetLog()) 

    # Start application main thread
    uiApp.MainLoop()
   
