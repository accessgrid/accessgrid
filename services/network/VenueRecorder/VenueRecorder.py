#-----------------------------------------------------------------------------
# Name:        VenueRecorder.py
# Purpose:     Tool for recording and playback of AG sessions. 
# 
# Author:      Susanne Lefvert 
# 
# Created:     $Date: 2005-07-08 21:22:13 $ 
# RCS-ID:      $Id: VenueRecorder.py,v 1.11 2005-07-08 21:22:13 lefvert Exp $ 
# Copyright:   (c) 2002 
# Licence:     See COPYING.TXT 
#----------------------------------------------------------------------------- 

import getopt 
import sys 
import time 
import os
import string
import zipfile
from threading import *
 
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
    def __init__(self, name, description, venueUrl = None): 
        ''' 
        Initialize the Recording instance.
        ''' 
        self.__name = name 
        self.__description = description
        self.__id = str(GUID()) # unique key for a recording
        self.__startTime = None
        self.__stopTime = None
        if not venueUrl:
            self.__venueUrl = ""
        self.__venueUrl = venueUrl
        self.__duration = None # Seconds
        self.__audioHost = None
        self.__videoHost = None
        self.__audioPort = None
        self.__audioAddress = None
              
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

        if not config.has_key("Recording.venueUrl"):
            url = None
        else:
            url = config["Recording.venueUrl"]
        
        r = Recording(config["Recording.name"],
                      config["Recording.description"],
                      url)
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

    def SetMulticast(self, vhost, vport, ahost, aport):
        self.__videoHost = vhost
        self.__videoPort = vport
        self.__audioHost = ahost
        self.__audioPort = aport

    def GetMulticast(self):
        return (self,__videoHost, self.__videoPort, self.__audioHost, self.__audioPort)
 
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

        self.__duration = self.__stopTime - self.__startTime

    def SetId(self, id):
        self.__id = id
 
    # Get methods

    def GetDuration(self):
        return self.__duration 
 
    def GetVenueUrl(self): 
        return self.__venueUrl 

    def GetId(self):
        return self.__id
         
    def GetStartTime(self):
        return self.__startTime
             
    def GetStopTime(self): 
        return self.__stopTime 

    def GetDuration(self):
        return self.__stopTime - self.__startTime
 
    def GetName(self): 
        return self.__name 
 
    def GetDescription(self): 
        return self.__description 
     
 
class VenueRecorderModel(Model): 
    """ 
    The venue recorder model class includes all logic for the program. There
    is no user interface code in this class. The ui and the model is
    separated using the observer pattern for easy separation. When
    state gets updated in the model, all obervers are notified and
    updates the view/ui.  The venue recorder model includes methods for recording
    and playback of venue media streams, as well as organization 
    and persistence of recordings. 
    """ 
         
    RECORDING = "recording" 
    PLAYING = "playing" 
    STOPPED = "stopped"
    MODE_MULTICAST = "multicast"
    MODE_VENUE = "venue"
               
    def __init__(self, log): 
        ''' 
        Initialize venue recorder model including all logic of the program.  
 
        ** Arguments ** 
        *log* log file 
        ''' 
        Model.__init__(self) 
 
        self.__log = log 
        self.__status = self.STOPPED 
        self.__currentRecording = None 
        self.__recordings = {}
        self.__playbackVenueUrl = "https://localhost:8000/Venues/default"
        self.__recordingVenueUrl = "https://ivs.mcs.anl.gov:9000/Venues/default"
        self.__playVideoHost = "224.2.3.4"
        self.__playVideoPort = "8888"
        self.__playAudioHost = "224.2.3.6"
        self.__playAudioPort = "9999"
        self.__recordVideoHost = "224.2.3.4"
        self.__recordVideoPort = "2222"
        self.__recordAudioHost = "224.2.3.6"
        self.__recordAudioPort = "4444"
        self.__playbackMode = self.MODE_VENUE
        self.__recordingMode = self.MODE_VENUE

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
        self.__preferencesPath = os.path.join(self.__path, "Preferences")  
        self.__processManager = ProcessManager() 
 
        if not os.path.exists(self.__path): 
            os.mkdir(self.__path) 
 
        self.__log.debug("VenueRecorderModel.__init__: Persistence path: %s"
                         %(self.__path)) 

        self.__LoadRecordings()
        self.LoadPreferences()
        
                     
    def __LoadRecordings(self): 
        ''' 
        Load recordings from file. 
        '''
        # For each directory in the venue recorder path
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
             
    def SavePreferences(self):
        '''
        Write preferences config file to path
        '''
        config = {}

        # Store modes
        config['Preferences.playbackMode'] = self.__playbackMode 
        config['Preferences.recordingMode'] = self.__recordingMode

        # Store playback preferences
        config['Preferences.playbackVenue'] = self.__playbackVenueUrl
        config['Preferences.playVideoHost'] = self.__playVideoHost
        config['Preferences.playVideoPort'] = self.__playVideoPort
        config['Preferences.playAudioHost'] = self.__playAudioHost
        config['Preferences.playAudioPort'] = self.__playAudioPort

        # Store recording preferences
        config['Preferences.recordingVenue'] = self.__recordingVenueUrl
        config['Preferences.recordVideoHost'] = self.__recordVideoHost
        config['Preferences.recordVideoPort'] = self.__recordVideoPort 
        config['Preferences.recordAudioHost'] = self.__recordAudioHost
        config['Preferences.recordAudioPort'] = self.__recordAudioPort

        SaveConfig(self.__preferencesPath, config)

    def LoadPreferences(self):
        '''
        Load preferences from config file at path
        '''
            
        if os.path.exists(self.__preferencesPath):
        
            config = LoadConfig(self.__preferencesPath)
            
            # Get play preferences
            self.__playbackMode = config['Preferences.playbackMode']
            self.__playbackVenueUrl = config['Preferences.playbackVenue']
            self.__playVideoHost = config['Preferences.playVideoHost']
            self.__playVideoPort = config['Preferences.playVideoPort'] 
            self.__playAudioHost = config['Preferences.playAudioHost'] 
            self.__playAudioPort =  config['Preferences.playAudioPort']
            
            # Get recording preferences
            self.__recordingMode = config['Preferences.recordingMode']
            self.__recordingVenueUrl = config['Preferences.recordingVenue']
            self.__recordVideoHost = config['Preferences.recordVideoHost']
            self.__recordVideoPort = config['Preferences.recordVideoPort']
            self.__recordAudioHost = config['Preferences.recordAudioHost'] 
            self.__recordAudioPort = config['Preferences.recordAudioPort']
               
    def GetPlayVenue(self):
        '''
        Get url for venue for playback
        '''
        return self.__playbackVenueUrl

    def GetPlayMulticast(self):
        '''
        Get host and port for playback
        '''
        return (self.__playVideoHost, self.__playVideoPort,
                self.__playAudioHost, self.__playAudioPort)

    def SetPlayVenue(self, url):
        '''
        Set url for venue playback
        '''
        self.__playbackVenueUrl = url

    def SetPlayMulticast(self, val):
        '''
        Set host and port for playback
        '''
        vhost, vport, ahost, aport = val
        self.__playVideoHost = vhost
        self.__playAudioHost = ahost

        # Make sure port is event
        self.__playVideoPort = int(vport) - (int(vport)%2)
        self.__playAudioPort = int(aport) - (int(aport)%2)

    def GetRecordVenue(self):
        '''
        Get url where recordings will be sent for playback
        '''
        return self.__recordingVenueUrl

    def GetRecordMulticast(self):
        '''
        Get address and port where recordings will be sent for
        playback
        '''
        return (self.__recordVideoHost, self.__recordVideoPort,
                self.__recordAudioHost, self.__recordAudioPort)

    def SetRecordVenue(self, url):
        '''
        Set url for venue recording
        '''
        self.__recordingVenueUrl = url

    def SetRecordMulticast(self, val):
        '''
        Set host and port for recording
        '''
        vhost, vport, ahost, aport = val
        self.__recordVideoHost = vhost
        self.__recordAudioHost = ahost

        # Make sure port is even.
        self.__recordVideoPort = int(vport) - (int(vport)%2)
        self.__recordAudioPort = int(aport) - (int(aport)%2) 

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
                self.__log.error("VenueRecorderModel.ImportFromZipFile: Wrong file format for venue recorder %s"%name)
                
        file.close()

        if not dirName:
            self.__log("there is no description file %s present in this zip file, import failed."%(dirName))
            return

        # Save files in venue recorder directory named after
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
 
    def PlayInVenue(self, recording, venueUrl, startTime = 0): 
        ''' 
        Method for playing a recording in a venue.  This method connects 
        to a venue at venueUrl and retreives multicast information.
        After that, the recording can be transmitted using rtpplay to
        the retreived venue addresses. 
 
        ** Arguments ** 
         
        *recording* the recording instance to play (Recording) 
        *venueUrl* venue address where we want to play the recording (string) 
        *startTime* where in the recording we should start the playback 
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
        rtpplay =  os.path.join(os.getcwd(),"rtpplay") 
         
        # Send audio 
        if audioStream: 
            l = audioStream.location 
            aFile = os.path.join(recordingPath, "audio.rtp")

            # Make sure rtp address is even.
            port = l.port - (l.port%2)
            args = [ 
                "-T",
                "-b", startTime,
                "-f", aFile, 
                l.host+"/"+str(port)+"/127", 
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
                "-b", startTime,
                "-f", vFile, 
                l.host+"/"+str(port)+"/127", 
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

    def PlayMulticast(self, recording, startTime = 0):
        ''' 
        Method for playing at a multicast location.  
       
        ** Arguments ** 
         
        *recording* the recording instance to play (Recording) 
        *startTime* where in the recording we should start the playback 
        '''
      
        # Use rtpplay to transmit video and audio 
        recordingPath = os.path.join(self.__path,
                                     str(recording.GetId())) 

        
        #Usage:  rtpplay -T -f file host/port 
        rtpplay =  os.path.join(os.getcwd(),"rtpplay") 
         
        # Send audio 
       
        aFile = os.path.join(recordingPath, "audio.rtp")

        args = [ 
            "-T",
            "-b", startTime,
            "-f", aFile, 
            self.__playAudioHost +"/"+str(self.__playAudioPort)+"/127", 
            ]
        self.__log.debug("Starting process: %s %s"%(rtpplay, str(args))) 
        self.__processManager.StartProcess(rtpplay,args) 
            
        # Send video 
        vFile = os.path.join(recordingPath, "video.rtp") 
                      
        args = [ 
            "-T",
            "-b", startTime,
            "-f", vFile, 
            # l.host+"/"+str(port)+"/127",
            self.__playVideoHost+"/"+str(self.__playVideoPort)+"/127", 
            ]
        self.__log.debug("Starting process: %s %s"%(rtpplay, str(args))) 
        self.__processManager.StartProcess(rtpplay,args) 
         
        # Set state 
        self.__currentRecording = recording 
        self.__status = self.PLAYING 
 
        # Notify ui to update view 
        self.NotifyObservers()

    def RecordMulticast(self, recording):
        # Use rtpdump to record video and audio 
        recordingPath = os.path.join(self.__path,
                                     str(recording.GetId())) 
         
        # Create recording directory if it does not exist. 
        if not os.path.exists(recordingPath): 
            os.mkdir(recordingPath) 

        rtpdump = os.path.join(os.getcwd(),"rtpdump")
        
        # Record video. 
        vFile = os.path.join(recordingPath, "video.rtp") 
        
        #Usage: rtpdump -F dump -o file host/port 
        
        args = [ 
            "-F", "dump", 
            "-o", vFile, 
            self.__recordVideoHost+"/"+str(self.__recordVideoPort), 
            ]
        
        self.__log.debug("Starting process: %s %s"%(rtpdump, str(args))) 
        self.__processManager.StartProcess(rtpdump,args) 
           
        # Record audio 
        
        aFile = os.path.join(recordingPath, "audio.rtp") 
        #Usage: rtpdump -F dump -o aFile l.host+"/"+l.port 
        
        args = [ 
            "-F", "dump", 
            "-o", aFile, 
            #l.host+"/"+str(port), 
            self.__recordAudioHost+"/"+str(self.__recordAudioPort)
            ]

        self.__log.debug("Starting process: %s %s"%(rtpdump, str(args))) 
        self.__processManager.StartProcess(rtpdump,args) 
                    
        # Set state
        recording.SetName("video %s/%s audio %s/%s"%(self.__recordVideoHost, self.__recordVideoPort,
                                                     self.__recordAudioHost, self.__recordAudioPort))
        recording.SetDescription("Recording from video %s/%s audio %s/%s"%(self.__recordVideoHost, self.__recordVideoPort,
                                                                           self.__recordAudioHost, self.__recordAudioPort))
        recording.SetStartTime() 
        self.__status = self.RECORDING 
        self.__currentRecording = recording
        self.__recordings[recording.GetId()] = recording 
 
        # Update user interface 
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

        rtpdump = os.path.join(os.getcwd(),"rtpdump")
        
        # Record video. 
        if videoStream: 
            l = videoStream.location 
            vFile = os.path.join(recordingPath, "video.rtp") 
                        
            #Usage: rtpdump -F dump -o file host/port 
            # Make sure rtp address is even.
            port = l.port - (l.port%2)
         
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
        recording.SetStartTime() 
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
        #self.__currentRecording = None 
        self.__status = self.STOPPED 
        self.NotifyObservers() 

    def SetPlaybackMode(self, mode):
        '''
        Set playback mode. You can either playback a recording in a venue
        or to multicast locations for audio and video.
        '''
        self.__playbackMode = mode

    def SetRecordingMode(self, mode):
        '''
        Set recording mode. You can either record from a venue
        or from multicast locations for audio and video.
        '''
        self.__recordingMode = mode

    def GetRecordingMode(self):
        '''
        Returns the recording mode, either VenueRecorderModel.MODE_VENUE,
        or VenueRecorderModel.MODE_LOCALLY
        '''
        return self.__recordingMode

    def GetPlaybackMode(self):
        '''
        Returns mode for playback

        **Returns**
        *playbackMode* either VenueRecorderModel.MODE_ LOCALLY or
        VenueRecorderModel.MODE_VENUE
        '''
        return self.__playbackMode
         
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

    def GetPath(self):
        '''
        Returns base path for venue recorder.

        **Returns**
        
        *path* venue recorder base path (string)
        '''
        return self.__path
                              
class VenueRecorderUI: 
    ''' 
    The main class for user interface control. This class 
    creates a venue recorder model and view instance. 
    ''' 
 
    def OnInit(self): 
        ''' 
        Expected by wxPython 
        '''
        return 1 
 
    def __init__(self, venueRecorderModel, log): 
        ''' 
        Create ui components and register them as observers to the 
        venue recorder model. 
        '''
        wxInitAllImageHandlers()
        self.log = log 

        # Create model 
        self.venueRecorderModel = venueRecorderModel 
 
        # Create view. The view will use the model interface to 
        # access state.
        self.venueRecorderView = VenueRecorderView(self, venueRecorderModel, self.log) 
        self.venueRecorderModel.RegisterObserver(self.venueRecorderView) 
         
        # Init UI
        self.venueRecorderView.Show(1) 
                         
class VenueRecorderView(wxFrame, Observer): 
    ''' 
    View for venue recorder containing ui components.
    '''
    RECORDING_MENU_REMOVE = wxNewId()
    RECORDING_MENU_EXPORT = wxNewId()
    RECORDING_MENU_EXPORT_ALL = wxNewId()
    RECORDING_MENU_IMPORT = wxNewId()
    RECORDING_MENU_PROPERTIES = wxNewId()
    
    MENU_PREFERENCES = wxNewId()
     
    def __init__(self, parent, venueRecorderModel, log): 
        ''' 
        Create ui components. 
        ''' 
        wxFrame.__init__(self, NULL, -1, "Personal AG Recorder", size = wxSize(420, 500)) 
        Observer.__init__(self) 
 
        self.log = log 
        self.venueRecorderModel = venueRecorderModel 
        self.intToGuid = {}
        
        self.SetIcon(icons.getAGIconIcon()) 
        self.panel = wxPanel(self, -1)
        self.stopButton = wxButton(self.panel, wxNewId(), "Stop",
                                   size = wxSize(50, 40)) 
        self.playButton = wxButton(self.panel, wxNewId(), "Play",
                                   size = wxSize(50, 40)) 
        self.recordButton = wxButton(self.panel, wxNewId(), "Record",
                                     size = wxSize(50, 40)) 

        self.slider = wxSlider(self.panel, wxNewId(), 0, 0, 100, style = wxSL_LABELS)
        self.statusField = wxTextCtrl(self.panel, wxNewId(), "Use the buttons to record from a venue or play a recording from the list below.", 
                                      style= wxTE_MULTILINE | wxTE_READONLY | 
                                      wxTE_RICH, size = wxSize(-1, 70)) 

         
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

        self.menubar = wxMenuBar()
        self.SetMenuBar(self.menubar)

        self.playMenu = wxMenu()
        self.playMenu.Append(self.MENU_PREFERENCES, "Preferences", "Set your prefered options")
        self.menubar.Append(self.playMenu, "Menu")
        self.sliderThread = None
        
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
        EVT_LIST_ITEM_SELECTED(self, self.recordingList.GetId(), self.OnRecordingSelectedCB)
        EVT_MENU(self, self.RECORDING_MENU_REMOVE, self.RemoveRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_EXPORT, self.ExportRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_EXPORT_ALL,
                 self.ExportRecordingAllCB)
        EVT_MENU(self, self.RECORDING_MENU_IMPORT, self.ImportRecordingCB)
        EVT_MENU(self, self.RECORDING_MENU_PROPERTIES, self.PropertiesCB)

        EVT_MENU(self, self.MENU_PREFERENCES, self.PreferencesCB)
 
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

    def OnRecordingSelectedCB(self, event):
        id = self.recordingList.GetFirstSelected()
        uniqueId = self.intToGuid[id]
        recording = self.venueRecorderModel.GetRecordings()[uniqueId]

        status = self.venueRecorderModel.GetStatus()
        
        if (status != self.venueRecorderModel.PLAYING and
            status != self.venueRecorderModel.RECORDING):
            self.slider.SetRange(0, int(recording.GetDuration()))
                
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
        recording = self.venueRecorderModel.GetRecordings()[uniqueId]

        # Open a UI to display properties 
        dlg = PropertiesDialog(self, -1,
                               recording,
                               self.venueRecorderModel)
        if dlg.ShowModal() == wxID_OK:
            r = dlg.GetRecording()
            # Only update if recording properties changed
            if r:
                self.venueRecorderModel.UpdateRecording(r)

    def PreferencesCB(self, event):
        '''
        Invoked when a user selects the preferences menu.
        '''

        self.venueRecorderModel.LoadPreferences()
        
        dlg = PreferencesDialog(self, -1, "Preferences", self.venueRecorderModel)
        if dlg.ShowModal() == wxID_OK:

            playTooltip = ""
            recordTooltip = ""
            
            # Get preferences for playback
            self.playbackMode = dlg.GetPlaybackMode()
         
            if self.playbackMode == self.venueRecorderModel.MODE_VENUE:
                self.venueRecorderModel.SetPlayVenue(dlg.GetPlayVenue())
            else:
                self.venueRecorderModel.SetPlayMulticast(dlg.GetPlayAddress())
                            
            self.venueRecorderModel.SetPlaybackMode(self.playbackMode)

            # Get preferences for recording
            self.recordingMode = dlg.GetRecordingMode()
                      
            if self.recordingMode == self.venueRecorderModel.MODE_VENUE:
                self.venueRecorderModel.SetRecordVenue(dlg.GetRecordVenue())
            else:
                self.venueRecorderModel.SetRecordMulticast(dlg.GetRecordAddress())
                
            self.venueRecorderModel.SetRecordingMode(self.recordingMode)

            # Save the preferences to file
            self.venueRecorderModel.SavePreferences()
            self.SetTooltips()
                                
        dlg.Destroy()

    def SetTooltips(self):
        '''
        Set ui tool tips
        '''
        recordTooltip = ""
        playTooltip = ""

        # Record button 
        if self.venueRecorderModel.GetRecordingMode() == self.venueRecorderModel.MODE_VENUE:
            recordTooltip = "%s"%(self.venueRecorderModel.GetRecordVenue())
        else:
            recordTooltip = "Video:%s/%s Audio: %s/%s"%(self.venueRecorderModel.GetRecordMulticast())

        # Play button
        if self.venueRecorderModel.GetPlaybackMode() == self.venueRecorderModel.MODE_VENUE:
            playTooltip = "%s"%(self.venueRecorderModel.GetPlayVenue())
        else:
            playTooltip = "Video:%s/%s Audio: %s/%s"%(self.venueRecorderModel.GetPlayMulticast())

        # Set button tooltips
        self.playButton.SetToolTipString(playTooltip)
        self.recordButton.SetToolTipString(recordTooltip)
                              
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
            recording = self.venueRecorderModel.GetRecordingFromZipFile(fileName)
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
            self.venueRecorderModel.ImportFromZipFile(fileName)
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
        recording = self.venueRecorderModel.GetRecordings()[uniqueId]

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
                        self.venueRecorderModel.ExportToZipFile([recording], fileName)
                    except:
                        self.log.exception("VenueRecorderModel.ExportRecordingCB: Export to zip file failed. %s"%(fileName))

                        val = self.ShowMessage(self.panel,
                                               "Export recording failed.",
                                               "Export", 
                                               style = wxICON_ERROR)               
            else:
                notOverwrite = 0
                self.venueRecorderModel.ExportToZipFile([recording], fileName)
               
    def ExportRecordingAllCB(self, event):
        '''
        Export all recordings to file.
        '''
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

        self.venueRecorderModel.ExportAllToZipFile(fileName)
      
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

        status = self.venueRecorderModel.GetStatus()
        currentRecording = self.venueRecorderModel.GetCurrentRecording()
        selectedRecordingId = self.intToGuid[id]
        selectedRecording = self.venueRecorderModel.GetRecordings()[selectedRecordingId]
        val = None

        # Maker sure user really wants to remove the recording.
        val = self.ShowMessage(self.panel, "Are you sure you want to remove %s."%(selectedRecording.GetName()),
                               "Remove", 
                               style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
        # Make sure we are not currently playing or recording to this
        # recording.
        if (status == self.venueRecorderModel.RECORDING and
            currentRecording == selectedRecording):
            val = self.ShowMessage(self.panel, "Stop recording %s ?."
                             %(selectedRecording.GetName()), "Remove", 
                             style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT)                                   
        elif (status == self.venueRecorderModel.PLAYING and
              currentRecording == selectedRecording):
            val = self.ShowMessage(self.panel, "Stop playing %s ?."
                                   %(selectedRecording.GetName()), "Remove", 
                                   style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
                               
        if val == wxID_NO:
            return
        elif val == wxID_YES:
            try:
                self.venueRecorderModel.Stop()
            except:
                self.log.exception("VenueRecorderView.RemoveRecordingCB: failed to stop player.")
        try:
            self.venueRecorderModel.Remove(selectedRecording)
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
 
        # Get recording instance from model. 
        id = self.intToGuid[selectedItem]
        name = self.recordingList.GetItemText(selectedItem)
        startTime = int(self.slider.GetValue())
        recordings = self.venueRecorderModel.GetRecordings() 
 
        # Check if recording exists. 
        if recordings.has_key(id): 
            r = recordings[id] 
        else:
            val = self.ShowMessage(self.panel, 
                                   "Error when playing; %s was not found"
                                   %(r.GetName()), 
                                   "Play", style = wxICON_ERROR) 
            return 

        # Open a UI where you can enter the venue url
             
        if  self.venueRecorderModel.GetPlaybackMode() == VenueRecorderModel.MODE_VENUE:
            venueUrl = self.venueRecorderModel.GetPlayVenue()

            
            try: 
                # Start to play the recording in venue entered by user. 
                self.venueRecorderModel.PlayInVenue(r, venueUrl, startTime) 
            except:
                wxEndBusyCursor() 
                val = self.ShowMessage(self.panel, 
                                       "Error when playing %s \nin venue %s"
                                       %(r.GetName(), venueUrl), 
                                       "Play", style = wxICON_ERROR)  
                self.log.exception("VenueRecorderView.PlayCB: Failed to play recording %s in venue %s" 
                                   %(r.GetName(), venueUrl)) 
            
            wxEndBusyCursor() 

        else:
            self.venueRecorderModel.PlayMulticast(r, startTime)
 
         
    def __TestStop(self): 
        ''' 
        Check to see if we need/want to stop an ongoing recording/playback 
        ''' 
        status =  self.venueRecorderModel.GetStatus() 
        current = self.venueRecorderModel.GetCurrentRecording() 
        dlg = None

        if status == self.venueRecorderModel.PLAYING and current:
            dlg = wxMessageDialog(self.panel, "Stop playing %s?"
                                  %(current.GetName()), "Record", 
                                  style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
 
        if status == self.venueRecorderModel.RECORDING and current: 
            dlg =  wxMessageDialog(self.panel, "Stop recording %s ?"
                                   %(current.GetName()), "Record", 
                                   style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT) 
 
        if dlg: 
            val = dlg.ShowModal() 
            dlg.Destroy() 
             
            if val == wxID_NO: 
                return 0 
 
            else: 
                self.venueRecorderModel.Stop() 
             
        return 1 
 
    def RecordCB(self, event): 
        ''' 
        Invoked when the record button is clicked.  
        ''' 
        # Check to see if we need to stop a recording or playback 
        # before recording.

        if not self.__TestStop():
            return 

        if  self.venueRecorderModel.GetRecordingMode() == VenueRecorderModel.MODE_VENUE:
            venueUrl = self.venueRecorderModel.GetRecordVenue()
         
            nr = len(self.venueRecorderModel.GetRecordings()) 
            name = "Session %i"%(nr) 
         
            # Create a Recording object
            r = Recording(name, "Session 1", venueUrl) 
            wxBeginBusyCursor() 
            
            try: 
                # Start recording
                self.venueRecorderModel.Record(r) 
            except: 
                self.log.exception("VenueRecorderView.RecordCB: Failed to record %s from %s" 
                                   %(r.GetName(), r.GetVenueUrl())) 

                val = self.ShowMessage(self.panel, 
                                       "Error when recording %s \nfrom venue %s"%(r.GetName(), r.GetVenueUrl()), 
                                       "Record", style = wxICON_ERROR) 
                                       
            wxEndBusyCursor() 

        else:
            nr = len(self.venueRecorderModel.GetRecordings()) 
            name = "Session %i"%(nr) 
         
            # Create a Recording object
            r = Recording(name, "Session 1") 
            self.venueRecorderModel.RecordMulticast(r)
          
    def StopCB(self, event): 
        ''' 
        Invoked when the stop button is clicked. 
        ''' 
        try: 
            self.venueRecorderModel.Stop() 
        except: 
            self.log.exception("VenueRecorderView.StopCB: Failed to stop")
            val = self.ShowMessage(self.panel, 
                                   "Error when stopping", 
                                   "Stop", style = wxICON_ERROR) 

                         
    def Update(self): 
        ''' 
        Invoked when the venueRecorder model changes state. This
        methods updates the ui based on current state of the model
        based on the Model-View-Controller pattern.
        '''

        # match up a GUID with an integer since
        # only integers are allowed as data in wxListCtrl.
        self.intToGuidDict = {}

        status = self.venueRecorderModel.GetStatus() 
        currentRecording = self.venueRecorderModel.GetCurrentRecording() 
        recordings = self.venueRecorderModel.GetRecordings() 

        if  status == self.venueRecorderModel.RECORDING: 
            tooltip = "Stop recording"

            if self.venueRecorderModel.GetRecordingMode() == VenueRecorderModel.MODE_VENUE:
                statusText = "Recording from venue %s"%(currentRecording.GetVenueUrl()) 
            else:
                vhost, vport, ahost, aport = self.venueRecorderModel.GetRecordMulticast() 
                statusText = "Recording %s at \nVideo: %s/%s \nAudio: %s/%s"%(currentRecording.GetName(), vhost, vport, ahost, aport)
            
            
        elif status == self.venueRecorderModel.PLAYING: 
            tooltip = "Stop playing"
            
            if self.venueRecorderModel.GetPlaybackMode() == VenueRecorderModel.MODE_VENUE:
                statusText = "Playing %s at %s"%(currentRecording.GetName(), self.venueRecorderModel.GetPlayVenue())

            else:
                vhost, vport, ahost, aport = self.venueRecorderModel.GetPlayMulticast() 
                statusText = "Playing %s at \nVideo: %s/%s \nAudio: %s/%s"%(currentRecording.GetName(), vhost, vport, ahost, aport)
            
            # Start thread for moving the slider.
            self.sliderThread = SliderThread(self, int(self.slider.GetValue()), int(currentRecording.GetDuration()+1))
                       
            
        elif status == self.venueRecorderModel.STOPPED: 
            tooltip = "Stop" 
            statusText = "Stopped"
            if self.sliderThread:
                self.sliderThread.abort()
                self.sliderThread = None
               
        self.stopButton.SetToolTipString(tooltip)
        
        self.statusField.SetValue(statusText) 
        j = 0 


        currentId = None
        if currentRecording:
            currentId = currentRecording.GetId()
                
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

        i = 0

        if currentId is not None:
            for id in self.intToGuid.keys():
                if self.intToGuid[id] == currentId:
                    i = 1
                    self.recordingList.Select(id)


        self.SetTooltips()
                                                    
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
        mainSizer.Add(self.slider, 0, wxEXPAND | wxLEFT | wxRIGHT, 30)
        mainSizer.Add(wxSize(10,10)) 
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


class SliderThread(Thread):
    '''
    Thread that moves the slider during
    playback.
    '''

    def __init__(self, app, startTime, endTime):
        Thread.__init__(self)
        self.terminate = 0
        self.app = app
        self.startTime = startTime
        self.endTime = endTime
        self.start()

    def run(self):
        
        for i in range(self.startTime, self.endTime):
            time.sleep(1)
            if self.terminate:
                return
       
            wxCallAfter(self.app.slider.SetValue, i)
            wxCallAfter(self.app.slider.Refresh)

        time.sleep(1)

        # When this is finished, we should automatically stop
        wxCallAfter(self.app.StopCB, None)
        
    def abort(self):
        # If user stops, the thread should abort
        self.terminate = 1
        

class PropertiesDialog(wxDialog): 
    ''' 
    Dialog for displaying recording properties. 
    ''' 
    def __init__(self, parent, id, recording, venueRecorderModel): 
        wxDialog.__init__(self, parent, id, "Recording Properties")
        self.recording = recording
        self.venueRecorderModel = venueRecorderModel
        
        start = time.strftime("%I:%M:%S %p, %b-%d-%Y",
                              time.localtime(recording.GetStartTime())) 
        stop = time.strftime("%I:%M:%S %p, %b-%d-%Y",
                             time.localtime(recording.GetStopTime()))

        duration = recording.GetDuration()

        # Calculate audio and video file sizes in bytes
        video = os.path.join(self.venueRecorderModel.GetPath(),
                             str(recording.GetId()), "video.rtp")
        audio = os.path.join(self.venueRecorderModel.GetPath(),
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
                                    start, size = wxSize(200, 20),
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
                                        size = wxSize(120, -1))
        self.videoSizeText = wxStaticText(self, -1, "Video Size: ") 
        self.videoSizeCtrl = wxTextCtrl(self, -1, 
                                        videoSize+" bytes",
                                        style = wxTE_READONLY,
                                        size = wxSize(120, -1)) 
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


class PreferencesDialog(wxDialog):
    '''
    Dialog to diplay user preferences for recording and playback.
    '''
    def __init__(self, parent, id, title, model):
        wxDialog.__init__(self, parent, id, title)
        self.SetSize(wxSize(100,100))
        self.model = model
        self.playbackText = wxStaticText(self, -1, "Playback Mode")
        self.playbackText.SetForegroundColour(wxBLUE)
        self.playInVenueButton = wxRadioButton(self, wxNewId(), "Play in venue",
                                               style = wxRB_GROUP)
        self.playInVenueText = wxStaticText(self, -1, "Venue URL:")
        self.playInVenueUrl = wxTextCtrl(self, -1, self.model.GetPlayVenue(), size = wxSize(300,-1))
        self.playInMulticastButton = wxRadioButton(self, wxNewId(),
                                                   "Play at multicast location",
                                                   size = wxSize(200, -1))

        vhost, vport, ahost, aport = self.model.GetPlayMulticast()
        
        self.playVideoAddressText = wxStaticText(self, -1, "Video Address: ")
        self.playVideoAddress = wxTextCtrl(self, -1, vhost)
        self.playVideoPortText = wxStaticText(self, -1, "Video Port: ")
        self.playVideoPort = wxTextCtrl(self, -1, vport)

        self.playAudioAddressText = wxStaticText(self, -1, "Audio Address: ")
        self.playAudioAddress = wxTextCtrl(self, -1, ahost)
        self.playAudioPortText = wxStaticText(self, -1, "Audio Port: ")
        self.playAudioPort = wxTextCtrl(self, -1, aport)

        vhost, vport, ahost, aport = self.model.GetRecordMulticast()
        
        self.recordingText = wxStaticText(self, -1, "Recording Mode")
        self.recordingText.SetForegroundColour(wxBLUE)
        self.recordInVenueButton = wxRadioButton(self, wxNewId(),
                                                 "Record from venue",
                                                 style = wxRB_GROUP)
        self.recordInVenueText = wxStaticText(self, -1, "Venue URL:")
        self.recordInVenueUrl = wxTextCtrl(self, -1, self.model.GetRecordVenue())
        self.recordInMulticastButton = wxRadioButton(self, wxNewId(),
                                                     "Record from multicast location")
        self.recordVideoAddressText = wxStaticText(self, -1, "Video Address: ")
        self.recordVideoAddress = wxTextCtrl(self, -1, vhost)
        self.recordVideoPortText = wxStaticText(self, -1, "Video Port: ")
        self.recordVideoPort = wxTextCtrl(self, -1, vport)

        self.recordAudioAddressText = wxStaticText(self, -1, "Audio Address: ")
        self.recordAudioAddress = wxTextCtrl(self, -1, ahost)
        self.recordAudioPortText = wxStaticText(self, -1, "Audio Port: ")
        self.recordAudioPort = wxTextCtrl(self, -1, aport)
        
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.Centre()

        self.__Layout()

        EVT_RADIOBUTTON(self, self.playInVenueButton.GetId(), self.PlayVenueCB)
        EVT_RADIOBUTTON(self, self.playInMulticastButton.GetId(), self.PlayMulticastCB)
        EVT_RADIOBUTTON(self, self.recordInVenueButton.GetId(), self.RecordVenueCB)
        EVT_RADIOBUTTON(self, self.recordInMulticastButton.GetId(), self.RecordMulticastCB)

        if self.model.GetPlaybackMode() == VenueRecorderModel.MODE_VENUE:
            self.EnablePlayVenue(0)
        else:
            self.EnablePlayVenue(1)

        if self.model.GetRecordingMode() == VenueRecorderModel.MODE_VENUE:
            self.EnableRecordVenue(0)
        else:
            self.EnableRecordVenue(1)

    def EnablePlayVenue(self, val):
        self.playInVenueText.Enable(not val)
        self.playInVenueUrl.Enable(not val)

        self.playInVenueButton.SetValue(not val)
        self.playInMulticastButton.SetValue(val)
        
        self.playVideoAddressText.Enable(val)
        self.playVideoPortText.Enable(val)
        self.playVideoAddress.Enable(val)
        self.playVideoPort.Enable(val)

        self.playAudioAddressText.Enable(val)
        self.playAudioPortText.Enable(val)
        self.playAudioAddress.Enable(val)
        self.playAudioPort.Enable(val)

    def EnableRecordVenue(self, val):
        self.recordInVenueText.Enable(not val)
        self.recordInVenueUrl.Enable(not val)

        self.recordInVenueButton.SetValue(not val)
        self.recordInMulticastButton.SetValue(val)
        
        self.recordVideoAddress.Enable(val)
        self.recordVideoPort.Enable(val)
        self.recordVideoAddressText.Enable(val)
        self.recordVideoPortText.Enable(val)

        self.recordAudioAddress.Enable(val)
        self.recordAudioPort.Enable(val)
        self.recordAudioAddressText.Enable(val)
        self.recordAudioPortText.Enable(val)
                    
    def PlayVenueCB(self, event):
        self.EnablePlayVenue(not event.Checked())
              
    def PlayMulticastCB(self, event):
        self.EnablePlayVenue(event.Checked())
        
    def RecordVenueCB(self, event):
        self.EnableRecordVenue(not event.Checked())

    def RecordMulticastCB(self, event):
        self.EnableRecordVenue(event.Checked())

    
    def GetPlaybackMode(self):
        '''
        Returns 1 if we want to play in venue.
        Otherwise, 0.
        '''
        if self.playInVenueButton.GetValue():
            return VenueRecorderModel.MODE_VENUE
        else:
            return VenueRecorderModel.MODE_MULTICAST
                        
    def GetPlayVenue(self):
        return self.playInVenueUrl.GetValue()

    def GetPlayAddress(self):
        return (self.playVideoAddress.GetValue(), self.playVideoPort.GetValue(),
                self.playAudioAddress.GetValue(), self.playAudioPort.GetValue())

    def GetRecordingMode(self):
        '''
        Returns 1 if we want to record from venue.
        Otherwise, 0.
        '''
        if self.recordInVenueButton.GetValue():
            return VenueRecorderModel.MODE_VENUE
        else:
            return VenueRecorderModel.MODE_MULTICAST
      
    def GetRecordVenue(self):
        return self.recordInVenueUrl.GetValue()

    def GetRecordAddress(self):
        return (self.recordVideoAddress.GetValue(), self.recordVideoPort.GetValue(),
                self.recordAudioAddress.GetValue(), self.recordAudioPort.GetValue())
        
    def __Layout(self):
        mainSizer = wxBoxSizer(wxVERTICAL)

        sizer1 = wxBoxSizer(wxHORIZONTAL)
        sizer1.Add(self.playbackText, 0, wxALL, 10)
        sizer1.Add(wxStaticLine(self, -1), 1, wxALL|wxCENTER, 5)
        mainSizer.Add(sizer1, 0, wxEXPAND)
        
        mainSizer.Add(self.playInVenueButton, 0, wxALL, 5)
        
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.playInVenueText, 0, wxALL, 5)
        sizer2.Add(self.playInVenueUrl, 1, wxALL, 5)
        mainSizer.Add(sizer2, 0, wxEXPAND|wxLEFT|wxRIGHT, 5)
               
        mainSizer.Add(self.playInMulticastButton, 0, wxALL, 5)
        mainSizer.Add(wxSize(5, 5))
        
        sizer3 = wxFlexGridSizer(2,4,5,5)
        sizer3.Add(self.playVideoAddressText)
        sizer3.Add(self.playVideoAddress, 0, wxEXPAND)
        sizer3.Add(self.playVideoPortText)
        sizer3.Add(self.playVideoPort)
        sizer3.Add(self.playAudioAddressText)
        sizer3.Add(self.playAudioAddress, 0, wxEXPAND)
        sizer3.Add(self.playAudioPortText)
        sizer3.Add(self.playAudioPort)
        sizer3.AddGrowableCol(1)
        mainSizer.Add(sizer3, 0, wxEXPAND |wxLEFT|wxRIGHT, 10)
       
        sizer4 = wxBoxSizer(wxHORIZONTAL)
        sizer4.Add(self.recordingText, 0, wxALL, 10)
        sizer4.Add(wxStaticLine(self, -1), 1, wxALL | wxCENTER, 5)
        mainSizer.Add(sizer4, 0, wxEXPAND)

        mainSizer.Add(self.recordInVenueButton, 0 ,wxALL, 5)

        sizer5 = wxBoxSizer(wxHORIZONTAL)
        sizer5.Add(self.recordInVenueText, 0, wxALL, 5)
        sizer5.Add(self.recordInVenueUrl, 1, wxALL, 5)
        mainSizer.Add(sizer5, 0, wxEXPAND| wxLEFT|wxRIGHT, 5)
       
        mainSizer.Add(self.recordInMulticastButton, 0, wxALL, 5)
        mainSizer.Add(wxSize(5,5))
        
        sizer6 = wxFlexGridSizer(2,4,5,5)
        sizer6.Add(self.recordVideoAddressText)
        sizer6.Add(self.recordVideoAddress, 0, wxEXPAND)
        sizer6.Add(self.recordVideoPortText)
        sizer6.Add(self.recordVideoPort)
        sizer6.Add(self.recordAudioAddressText)
        sizer6.Add(self.recordAudioAddress, 0, wxEXPAND)
        sizer6.Add(self.recordAudioPortText)
        sizer6.Add(self.recordAudioPort)
        sizer6.AddGrowableCol(1)
        mainSizer.Add(sizer6, 0, wxLEFT | wxRIGHT | wxEXPAND, 10)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
     
        mainSizer.Add(buttonSizer, 0, wxCENTER | wxALL, 5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
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
        print "\n **** Check your certificates ***\n"
        sys.exit(-1)
    
    # Create model and view 
    v = VenueRecorderModel(app.GetLog())
    uiApp = VenueRecorderUI(v, app.GetLog())

    # Needed for class recording. It really should
    # get the log file as parameter so we don't need to
    # have this global variable.
    log = app.GetLog()


    #pref = PreferencesDialog(None, -1, "test")
    #pref.Show()
        
    # Start main ui thread
    wxapp.MainLoop() 
