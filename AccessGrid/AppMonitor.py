from wxPython.wx import *

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.EventClient import EventClient
from AccessGrid.Events import ConnectEvent
from AccessGrid.Events import Event
from AccessGrid.Platform import isWindows
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.ClientProfile import ClientProfile

import logging, logging.handlers

import os
import getopt
from time import localtime , strftime

log = logging.getLogger("AG.AppMonitor")

class AppMonitor:
    '''
    An Application Monitor connects to an Application Service and
    displays current application state such as participants and their status,
    application name, and description. It also includes an event window
    that shows when participants joined, data changed, and so forth.
    '''
 
    def __init__(self, parent, appUrl):
        '''
        Opens the Application Monitor frame and loads it with
        current application state. Also, register callbacks for
        events that updates the state.
        
        **Arguments**
        *parent* Parent frame
        *appUrl* The URL to the application service
        '''
        self.appUrl = appUrl
        self.participants = {}
           
        # Open UI frame
        self.frame = AppMonitorFrame(parent, -1, "Application Monitor", self)
        self.frame.Show()

        # Get a handle to the application object
        self.appProxy = Client.Handle(self.appUrl).GetProxy()

        # Join the application session
        self.publicId, self.privateId = self.appProxy.Join()
        channelId, esl = self.appProxy.GetDataChannel(self.privateId)

        # Start event client
        self.eventClient = EventClient(self.privateId, esl, channelId)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(channelId, self.privateId))

        # Register callbacks
        self.RegisterCallbacks()

        # Connect to application and get state info
        self.GetApplicationInfo()

    def RegisterCallbacks(self):
        '''
        Register methods called when the application service distributes
        an event
        '''
        self.eventClient.RegisterCallback(Event.APP_PARTICIPANT_JOIN, self.ParticipantJoined)
        self.eventClient.RegisterCallback(Event.APP_PARTICIPANT_LEAVE, self.ParticipantLeft)
        self.eventClient.RegisterCallback(Event.APP_SET_DATA, self.SetData)
        self.eventClient.RegisterCallback(Event.APP_UPDATE_PARTICIPANT, self.UpdateParticipant)

    #
    # Callbacks. Every UI access have to be made by using wxCallAfter.
    #
        
    def ParticipantJoined(self, event):
        '''
        This method is called when a new participant joined the application session.
        '''
        appParticipantDescription = event.data
        wxCallAfter(self.frame.AddParticipant, appParticipantDescription)
                
    def ParticipantLeft(self, event):
        '''
        This method is called when a participant left the application session.
        '''
        appParticipantDescription = event.data
        wxCallAfter(self.frame.RemoveParticipant, appParticipantDescription)

    def SetData(self, event):
        '''
        This method is called when data changed in application service.
        '''
        appDataDescription = event.data
        wxCallAfter(self.frame.AddData, appDataDescription)

    def UpdateParticipant(self, event):
        '''
        This method is called when a participant changed profile or status.
        '''
        
        appParticipantDescription = event.data
        wxCallAfter(self.frame.UpdateParticipant, appParticipantDescription)

    #
    # ----- Callbacks end.
    #
    
    def ShutDown(self):
        '''
        Stop event client and leave the application session.
        '''
        self.eventClient.Stop()
        self.appProxy.Leave(self.privateId)
                
    def GetApplicationInfo(self):
        '''
        Get state from applicaton service and update UI frame.
        '''
        appState = self.appProxy.GetState(self.privateId) 
        participants = self.appProxy.GetParticipants(self.privateId)
        dataKeys = self.appProxy.GetDataKeys(self.privateId)

        # Set participants
        for appParticipantDesc in participants:
            self.frame.AddInitParticipant(appParticipantDesc)

        dataDict = {}
        for key in dataKeys:
            data = self.appProxy.GetData(self.privateId, key)
            dataDict[key] = data
            self.frame.AddInitData(dataDict)
                      
        # Set application information
        self.frame.SetName(appState.name)
        self.frame.SetDescription(appState.description)
    
        
class AppMonitorFrame(wxFrame):
    '''
    The AppMonitor Frame includes all user interface components for the
    Application Monitor.
    '''
    
    def __init__(self, parent, id, title, appMonitor, **kw):
        wxFrame.__init__(self, parent, id, title, **kw)
        self.appMonitor = appMonitor

        self.SetSize(wxSize(400,300))
        self.panel = wxPanel(self, -1)

        self.textCtrl = wxTextCtrl(self.panel, -1, style = wxTE_MULTILINE | wxTE_READONLY)

        self.nameText = wxStaticText(self.panel, -1, "This is the name", style = wxALIGN_CENTER)
        font = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)
        self.nameText.SetFont(font)

        self.descriptionText = wxTextCtrl(self.panel, -1, "test",
                                          size = wxSize(10, 50), style = wxTE_MULTILINE)
       
        self.partListCtrl = wxListCtrl(self.panel, -1, style = wxLC_REPORT)
        self.partListCtrl.InsertColumn(0, "Participants")
        self.partListCtrl.InsertColumn(1, "Status")

        self.idToProfile = {}
        self.profileToId = {}

        self.idToData = {}
        self.dataToId = {}
        
        self.__setEvents()
        self.__layout()

        EVT_CLOSE(self, self.OnExit)
      
    def OnSize(self, event):
        """
        Sets correct column widths.
        """
        w,h = self.GetClientSizeTuple()
        self.partListCtrl.SetColumnWidth(0, w*(0.70) )
        self.partListCtrl.SetColumnWidth(1, w*(0.30) )

        event.Skip()

    def OnExit(self, event):
        '''
        Called when window is closed.
        '''
        self.appMonitor.ShutDown()
        
        self.Destroy()
        
    def SetName(self, name):
        '''
        Set application name.
        '''
        self.nameText.SetLabel(name)

    def SetDescription(self, desc):
        '''
        Set application description.
        '''
        self.descriptionText.SetValue(desc)

    def AddParticipant(self, pDesc):
        '''
        Adds participant to list and displays an event message.
        '''

        # Ignore participants without client profile (a monitor for example)
        if pDesc.clientProfile == "None" or pDesc.clientProfile == None:
            return
        
        self.AddInitParticipant(pDesc)
        
        # Add event text
        message = pDesc.clientProfile.name + " joined this session "
        
        # Add time to event message
        dateAndTime = strftime("%a, %d %b %Y, %H:%M:%S", localtime() )
        message = message + " ("+dateAndTime+")" 
        
        # Events are coloured blue
        self.textCtrl.SetDefaultStyle(wxTextAttr(wxBLUE))
        self.textCtrl.AppendText(message+'\n')
        self.textCtrl.SetDefaultStyle(wxTextAttr(wxBLACK))
                        
    def AddInitParticipant(self, pDesc):
        """
        Add a participant to the list. Initially done when connecting to a
        service. No event message is displayed.
        """
        
        # Ignore participants without client profile (a monitor for example)
        if pDesc.clientProfile == "None" or pDesc.clientProfile == None:
            return

        idx = self.partListCtrl.GetItemCount()

        self.idToProfile[idx] = pDesc
        self.profileToId[pDesc.appId] = idx
        
        self.partListCtrl.InsertStringItem(idx, pDesc.clientProfile.name)
        self.partListCtrl.SetStringItem(idx, 1, pDesc.status)
        self.partListCtrl.SetItemData(idx, idx)
        
        self.partListCtrl.SetColumnWidth(0, wxLIST_AUTOSIZE)

        self.Layout()

    def RemoveParticipant(self, pDesc):
        '''
        Remove a participant.
        '''
        if self.profileToId.has_key(pDesc.appId):
            id = self.profileToId[pDesc.appId]
            
            item = self.partListCtrl.FindItemData(-1, id)
        
            self.partListCtrl.DeleteItem(item)
        

    def GetProfile(self, appId):
        '''
        Converts applicaiton ID to client profile.
        '''
        if not self.profileToId.has_key(appId):
            return None

        id = self.profileToId[appId]

        if not self.idToProfile.has_key(id):
            return None
                
        profile = self.idToProfile[id]

        return profile
        
    def UpdateParticipant(self, pDesc):
        """
        Update a participant.
        """
        # Ignore participants without client profile (a monitor for example)
        if pDesc.clientProfile == "None":
            return
                       
        if self.profileToId.has_key(pDesc.appId):
            id = self.profileToId[pDesc.appId]
            
            self.partListCtrl.SetStringItem(id, 0, pDesc.clientProfile.name)
            self.partListCtrl.SetStringItem(id, 1, pDesc.status)

                             
    def AddData(self, appDataDesc):
        '''
        Print data event in text window.
        '''
        appProfile = self.GetProfile(appDataDesc.appId)
        
        # Ignore participants without client profile (a monitor for example)
        if appProfile == None:
            return

        name = appProfile.clientProfile.name
        text = name+" changed: "+str(appDataDesc.key) + " = " + str(appDataDesc.value) + '\n'
        self.textCtrl.AppendText(text)

    def AddInitData(self, dataDict):
        """
        Display data text in event window. Initially done when connecting to service. No time
        stamp is included in text.
        """
        # Data is coloured red
        self.textCtrl.SetDefaultStyle(wxTextAttr(wxRED))
       
        for key in dataDict.keys():
            text = key + "=" + dataDict[key] + '\n'
            self.textCtrl.AppendText(text)

        self.textCtrl.SetDefaultStyle(wxTextAttr(wxBLACK))
                            
    def __setEvents(self):
        '''
        Initialize events.
        '''
        if isWindows():
            EVT_SIZE(self.panel, self.OnSize)
    
    def __layout(self):
        '''
        Handles UI layout.
        '''
        sizer = wxBoxSizer(wxVERTICAL)
        
        vs = wxBoxSizer(wxVERTICAL)
      
        vs.Add(self.nameText, 0, wxEXPAND | wxALL, 4)
        
        vs.Add(self.descriptionText, 0, wxEXPAND | wxALL, 4)
        vs.Add(wxStaticLine(self.panel, -1), 0, wxEXPAND)
        vs.Add(5,5)
        vs.Add(self.partListCtrl, 2, wxEXPAND | wxALL, 4)
        vs.Add(self.textCtrl, 1, wxEXPAND | wxALL, 4)
        
        sizer.Add(vs, 1, wxEXPAND|wxALL, 5)

        w,h = self.GetClientSizeTuple()
        self.partListCtrl.SetColumnWidth(0, w*(0.70) - 10)
        self.partListCtrl.SetColumnWidth(1, w*(0.30) - 10)

        self.panel.SetSizer(sizer)
        self.panel.SetAutoLayout(1)
        self.panel.Layout()
        self.Layout()
         
def SetLogging():
    logFile = None
    debugMode = 1
    
    log = logging.getLogger("AG")
    log.setLevel(logging.DEBUG)
        
    if logFile is None:
        logname = os.path.join(GetUserConfigDir(), "NodeSetupWizard.log")
    else:
        logname = logFile
        
    hdlr = logging.FileHandler(logname)
    extfmt = logging.Formatter("%(asctime)s %(thread)s %(name)s %(filename)s:%(lineno)s %(levelname)-5s %(message)s", "%x %X")
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%x %X")
    hdlr.setFormatter(extfmt)
    log.addHandler(hdlr)
    
    if debugMode:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)


class ArgumentManager:
    def __init__(self):
        self.debugMode = 0
        self.argDict = {}
        self.argDict['appUrl'] = None
      
    def GetArguments(self):
        return self.argDict
        
    def Usage(self):
        """
        How to use the program.
        """
        print "%s:" % (sys.argv[0])
        print "  -a|--appUrl: Application URL"
        print "  -h|--help: print usage"
            
    def ProcessArgs(self):
        """
        Handle any arguments we're interested in.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:], "a:h",
                                       ["appUrl=", "help"])

        except getopt.GetoptError:
            self.Usage()
            sys.exit(2)
            
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                self.Usage()
                sys.exit(0)
            
            elif opt in ('-a', '--appUrl'):
                self.argDict['appUrl'] = arg


        if not self.argDict['appUrl']:
            self.Usage()
            sys.exit(0)
        
if __name__ == "__main__":
    SetLogging()
    am = ArgumentManager()
    am.ProcessArgs()
    arguments = am.GetArguments()

    appUrl = arguments['appUrl']
    
    pp = wxPySimpleApp()
    monitor = AppMonitor(None, appUrl)
    
    pp.MainLoop()
