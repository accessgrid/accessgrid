import os

from AccessGrid import Log
from AccessGrid.Platform import IsOSX
from AccessGrid.Preferences import Preferences
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Platform.Config import AGTkConfig
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW
from AccessGrid.GUID import GUID
from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE
from AccessGrid.Descriptions import STATUS_ENABLED, STATUS_DISABLED
from AccessGrid.UIUtilities import MessageDialog

from wxPython.wx import *
from wxPython.gizmos import wxTreeListCtrl
import  wx.lib.intctrl
from AccessGrid import icons

log = Log.GetLogger(Log.VenueClient)

class PreferencesDialog(wxDialog):
    ID_WINDOW_LEFT = 0
    ID_WINDOW_RIGHT = 1
    
    def __init__(self, parent, id, title, preferences):
        '''
        Initialize ui components and events.
        '''
        wxDialog.__init__(self, parent, id, title,
                          style = wxRESIZE_BORDER | wxDEFAULT_DIALOG_STYLE,
                          size = wxSize(720, 576))
        self.Centre()
       
      
        self.sideWindow = wxSashWindow(self, self.ID_WINDOW_LEFT,
                                       wxDefaultPosition,
                                       wxSize(150, -1))

        self.sideWindow.SetSashVisible(wxSASH_RIGHT, TRUE)
        
        self.preferencesWindow = wxSashWindow(self, self.ID_WINDOW_RIGHT,
                                              wxDefaultPosition,
                                              wxSize(200, -1))
        self.sideTree = wxTreeCtrl(self.sideWindow, wxNewId(), wxDefaultPosition, 
                                   wxDefaultSize, style = wxTR_HIDE_ROOT)
        self.okButton = wxButton(self, wxID_OK, "Save")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Close")
        self.preferences = preferences

        # Create panels for preferences
        self.preferencesPanel = wxPanel(self.preferencesWindow, wxNewId(),
                                        style = wxSUNKEN_BORDER)
        self.title = wxTextCtrl(self.preferencesPanel, wxNewId(), "TITLE",
                                style = wxTE_READONLY | wxTE_CENTRE )
        self.nodePanel = NodePanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.profilePanel = ProfilePanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.loggingPanel = LoggingPanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.venueConnectionPanel = VenueConnectionPanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.networkPanel = NetworkPanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.proxyPanel = ProxyPanel(self.preferencesPanel, wxNewId(),
                                         self.preferences)
        self.navigationPanel = NavigationPanel(self.preferencesPanel, wxNewId(),
                                               self.preferences)

        self.loggingPanel.Hide()
        self.venueConnectionPanel.Hide()
        self.networkPanel.Hide()
        self.proxyPanel.Hide()
        self.navigationPanel.Hide()
        self.nodePanel.Hide()
        self.currentPanel = self.loggingPanel
        
        EVT_SASH_DRAGGED(self.sideWindow, self.ID_WINDOW_LEFT, self.__OnSashDrag)
        EVT_TREE_SEL_CHANGED(self, self.sideTree.GetId(), self.OnSelect)
        EVT_SIZE(self, self.__OnSize)

        self.__Layout()
        self.__InitTree()

        if IsOSX():
            self.title.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.title.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))

        # Set correct dimensions on current panel.
        if self.currentPanel.GetSizer():
            w,h = self.preferencesWindow.GetSizeTuple()
            self.currentPanel.GetSizer().SetDimension(0,0,w,h)

    def GetPreferences(self):
        """
        Returns a preference object reflecting current state in dialog.

        ** Returns **
        
        *preferences* Preferences object

        """
        # Set all values available in panels.
        self.preferences.SetPreference(Preferences.LOG_TO_CMD,
                                       self.loggingPanel.GetLogToCmd())
        self.preferences.SetPreference(Preferences.STARTUP_MEDIA,
                                       self.nodePanel.GetMediaStartup())
        self.preferences.SetPreference(Preferences.ENABLE_DISPLAY,
                                       self.nodePanel.GetDisplay())
        self.preferences.SetPreference(Preferences.ENABLE_VIDEO,
                                       self.nodePanel.GetVideo())
        self.preferences.SetPreference(Preferences.ENABLE_AUDIO,
                                        self.nodePanel.GetAudio())
        self.preferences.SetPreference(Preferences.NODE_BUILTIN,
                                       self.nodePanel.GetNodeBuiltIn())
        self.preferences.SetPreference(Preferences.NODE_URL,
                                       self.nodePanel.GetDefaultNodeUrl())

        if self.nodePanel.GetDefaultNodeConfig():
            self.preferences.SetPreference(Preferences.NODE_CONFIG,
                                           self.nodePanel.GetDefaultNodeConfig().name)
            self.preferences.SetPreference(Preferences.NODE_CONFIG_TYPE,
                                           self.nodePanel.GetDefaultNodeConfig().type)
        self.preferences.SetPreference(Preferences.RECONNECT,
                                       self.venueConnectionPanel.GetReconnect())
        self.preferences.SetPreference(Preferences.MAX_RECONNECT,
                                       self.venueConnectionPanel.GetMaxReconnects())
        self.preferences.SetPreference(Preferences.RECONNECT_TIMEOUT,
                                       self.venueConnectionPanel.GetReconnectTimeOut())
        self.preferences.SetPreference(Preferences.MULTICAST,
                                       self.networkPanel.GetMulticast())
        self.preferences.SetPreference(Preferences.BEACON,
                                       self.networkPanel.GetBeacon())
        self.preferences.SetPreference(Preferences.BRIDGE_REGISTRY,
                                       self.networkPanel.GetRegistry(-1))
        self.preferences.SetBridges(self.networkPanel.GetBridges())
        self.preferences.SetPreference(Preferences.DISPLAY_MODE,
                                       self.navigationPanel.GetDisplayMode())
        self.preferences.SetPreference(Preferences.PROXY_HOST,
                                       self.proxyPanel.GetHost())
        self.preferences.SetPreference(Preferences.PROXY_PORT,
                                       self.proxyPanel.GetPort())

        cDict = self.loggingPanel.GetLogCategories()
        for category in cDict.keys():
            self.preferences.SetPreference(category, cDict[category])

        p = self.profilePanel.GetNewProfile()
        self.preferences.SetProfile(p)

        self.preferences.SetBridges(self.networkPanel.GetBridges())

        return self.preferences
            
    def OnSelect(self, event):
        '''
        Called when selecting new preference from side menu. Each preference
        is associated with a panel, which is shown when the preference is selected.
        '''
        # Panel associated with the selected preference.
        item = event.GetItem()
        panel = self.sideTree.GetItemData(item).GetData()
        self.title.SetValue(self.sideTree.GetItemText(item))
        
        # Switch displayed panel.
        s = self.preferencesWindow.GetSizer()
        s.Remove(self.currentPanel)
        self.currentPanel.Hide()
        self.currentPanel = panel

        # Fix layout
        self.currentPanel.Show()
                       
        self.__Layout()
        
        w,h = self.preferencesWindow.GetSizeTuple()
        self.preferencesPanel.GetSizer().SetDimension(0,0,w,h)
                    
    def __InitTree(self):
        '''
        Populates the side tree and associates each preference with a panel.
        '''
        self.root = self.sideTree.AddRoot("")
        self.profile = self.sideTree.AppendItem(self.root,
                                                " My Profile")
        self.node = self.sideTree.AppendItem(self.root,
                                                " My Node")
        self.logging = self.sideTree.AppendItem(self.root,
                                                " Logging")
        self.venueConnection = self.sideTree.AppendItem(self.root,
                                                " Venue Connection")
        self.network = self.sideTree.AppendItem(self.root,
                                                " Network")
        self.proxy = self.sideTree.AppendItem(self.root,
                                                " Proxy")
        self.navigation = self.sideTree.AppendItem(self.root,
                                                " Navigation")
        self.sideTree.SetItemData(self.profile,
                                  wxTreeItemData(self.profilePanel))
        self.sideTree.SetItemData(self.node,
                                  wxTreeItemData(self.nodePanel))
        self.sideTree.SetItemData(self.logging,
                                  wxTreeItemData(self.loggingPanel))
        self.sideTree.SetItemData(self.venueConnection,
                                  wxTreeItemData(self.venueConnectionPanel))
        self.sideTree.SetItemData(self.network,
                                  wxTreeItemData(self.networkPanel))
        self.sideTree.SetItemData(self.proxy,
                                  wxTreeItemData(self.proxyPanel))
        self.sideTree.SetItemData(self.navigation,
                                  wxTreeItemData(self.navigationPanel))
        self.sideTree.SelectItem(self.profile)

    def __OnSize(self,event):
        '''
        Called when window is resized.
        '''
        #
        # Work around a suspected wx bug. Get the size of the sideWindow and
        # reset it after the layout is updated. Without this code, the sash
        # gradually shifts right when the window is sized, regardless of
        # of whether the width increases or decreases.
        #
        width, height = self.sideWindow.GetSize()
        self.__Layout()
        self.sideWindow.SetSize((width, -1))
        
    def __OnSashDrag(self, event):
        '''
        Called when sash panel is moved, resizes sash windows accordingly.
        '''
        if event.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
            return
        
        eID = event.GetId()
        
        if eID == self.ID_WINDOW_LEFT:
            width = event.GetDragRect().width
            self.sideWindow.SetSize(wxSize(width, -1))
            
        elif eID == self.ID_WINDOW_RIGHT:
            width = event.GetDragRect().width
            self.preferencesWindow.SetSize(wxSize(width, -1))

        self.__Layout()
        
    def __Layout(self):
        '''
        Fix ui layout
        '''
        mainSizer = wxBoxSizer(wxVERTICAL)
        
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(self.sideWindow,0,wxEXPAND)
        sizer.Add(self.preferencesWindow,1,wxEXPAND)

        mainSizer.Add(sizer, 1, wxEXPAND)
        
        prefPanelBox = wxBoxSizer(wxVERTICAL)
        self.preferencesPanel.SetSizer(prefPanelBox)
        prefPanelBox.Add(self.title, 0, wxEXPAND)
        prefPanelBox.Add(self.currentPanel, 1, wxEXPAND|wxTOP, 5)

        prefBox = wxBoxSizer(wxHORIZONTAL)
        self.preferencesWindow.SetSizer(prefBox)
        prefBox.Add(self.preferencesPanel, 1, wxEXPAND)
        
        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxRIGHT | wxALIGN_CENTER, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALIGN_CENTER)

        mainSizer.Add(buttonSizer, 0, wxALL| wxALIGN_CENTER, 5)

        #w,h = self.preferencesWindow.GetSizeTuple()
        #if self.currentPanel.GetSizer():
        #    self.currentPanel.GetSizer().SetDimension(0,0,w,h)

        self.SetSizer(mainSizer)
        self.Layout()
        
class NodePanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.preferences = preferences
        self.Centre()

        self.nodeText = wxStaticText(self, -1, "Node")
        self.nodeLine = wxStaticLine(self, -1)
        self.mediaButton = wxCheckBox(self, wxNewId(), "  Launch node services on startup ")
        self.nodeUrlText = wxStaticText(self, -1, "Node service")
        self.nodeBuiltInCheckbox = wxRadioButton(self,wxNewId(),'Built-in', style=wxRB_GROUP)
        self.nodeExternalCheckbox = wxRadioButton(self,wxNewId(),'External')
        self.nodeUrlCtrl = wxTextCtrl(self, -1, "", size = wxSize(250, -1))
        self.nodeConfigText = wxStaticText(self, -1, "Node configuration")
        self.nodeConfigRefresh = wxButton(self,-1,'Refresh')
        self.mediaText = wxStaticText(self, -1, "Media")
        self.mediaLine = wxStaticLine(self, -1)
        self.audioButton = wxCheckBox(self, wxNewId(), " Enable Audio")
        self.displayButton = wxCheckBox(self, wxNewId(), " Enable Display")
        self.videoButton = wxCheckBox(self, wxNewId(), " Enable Video")

        if IsOSX():
            self.nodeText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
            self.mediaText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.nodeText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
            self.mediaText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))

        self.mediaButton.SetValue(int(preferences.GetPreference(Preferences.STARTUP_MEDIA)))
        nodeBuiltin = int(preferences.GetPreference(Preferences.NODE_BUILTIN))
        self.nodeBuiltInCheckbox.SetValue(nodeBuiltin)
        self.nodeExternalCheckbox.SetValue(not nodeBuiltin)
        
        nodeUrl = preferences.GetPreference(Preferences.NODE_URL)
        self.nodeUrlCtrl.SetValue(nodeUrl)
        if  nodeBuiltin:
            self.nodeBuiltInCheckbox.SetValue(true)
            self.nodeUrlCtrl.SetEditable(false)
        else:
            self.nodeExternalCheckbox.SetValue(true)
            self.nodeUrlCtrl.SetEditable(true)
            
        self.audioButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_AUDIO)))
        self.displayButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_DISPLAY)))
        self.videoButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_VIDEO)))

        self.configMap = {}
        self.nodeConfigCtrl = wxChoice(self, wxNewId(),
                                       size = wxSize(235, -1))
                                       
        self.OnRefresh()

        # Set events
        EVT_RADIOBUTTON(self,self.nodeBuiltInCheckbox.GetId(),self.OnNodeBuiltIn)
        EVT_RADIOBUTTON(self,self.nodeExternalCheckbox.GetId(),self.OnNodeExternal)
        EVT_TEXT_ENTER(self,self.nodeUrlCtrl.GetId(),self.OnRefresh)
        EVT_BUTTON(self,self.nodeConfigRefresh.GetId(),self.OnRefresh)
        self.__Layout()
        
        
    def OnNodeBuiltIn(self,event):
        self.nodeUrlCtrl.SetEditable( not event.Checked() )

    def OnNodeExternal(self,event):
        self.nodeUrlCtrl.SetEditable( event.Checked() )

    def OnRefresh(self,event=None):
        self.nodeConfigCtrl.Clear()
        
        # Find node service to call
        if self.nodeBuiltInCheckbox.GetValue():
            if not self.preferences.venueClient:
                return
            nodeService = self.preferences.venueClient.builtInNodeService
        else:
            nodeServiceURL = self.nodeUrlCtrl.GetValue()
            if len(nodeServiceURL):
                nodeService = AGNodeServiceIW(self.nodeUrlCtrl.GetValue())
            else:
                return
        
        # Get node configurations
        defaultNodeConfigName = self.preferences.GetPreference(Preferences.NODE_CONFIG)
        
        defaultNodeConfigString = ""

        try:
            nodeConfigs = nodeService.GetConfigurations()
        except:
            log.exception("Failed to retreive node configurations")
            nodeConfigs = []

        for nodeConfig in nodeConfigs:
            self.nodeConfigCtrl.Append('%s (%s)' % (nodeConfig.name, nodeConfig.type))
            nodeConfigString = nodeConfig.name + " ("+nodeConfig.type +")"
            self.configMap[nodeConfigString] = nodeConfig
            if defaultNodeConfigName == nodeConfig.name:
                defaultNodeConfigString = nodeConfigString
            
        if defaultNodeConfigString:
            self.nodeConfigCtrl.SetStringSelection(defaultNodeConfigString)
        # if default node config not found, don't select one
        #self.nodeConfigCtrl.SetSelection(0)

    def GetNodeBuiltIn(self):
        if self.nodeBuiltInCheckbox.GetValue():
            return 1
        
        return 0

    def GetDefaultNodeUrl(self):
        return self.nodeUrlCtrl.GetValue()

    def GetDefaultNodeConfig(self):
        key = self.nodeConfigCtrl.GetStringSelection()

        if key and self.configMap.has_key(key):
            return self.configMap[key]
        else:
            return None

    def GetMediaStartup(self):
        if self.mediaButton.IsChecked():
            return 1
        else:
            return 0

    def GetDisplay(self):
        if self.displayButton.GetValue():
            return 1
        else:
            return 0

    def GetVideo(self):
        if self.videoButton.GetValue():
            return 1
        else:
            return 0

    def GetAudio(self):
        if self.audioButton.GetValue():
            return 1
        else:
            return 0
    
    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.nodeText, 0, wxALL, 5)
        sizer2.Add(self.nodeLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND)

        gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        gridSizer2 = wxFlexGridSizer(3, 1, 5, 5)
        gridSizer.Add(self.nodeUrlText, 0, wxALL, 5)
        gridSizer2.Add(self.nodeBuiltInCheckbox)
        gridSizer2.Add(self.nodeExternalCheckbox)
        gridSizer2.Add(self.nodeUrlCtrl)
        gridSizer.Add(gridSizer2)
        sizer.Add(gridSizer, 0, wxALL, 5)
                
        sizer.Add(self.mediaButton, 0, wxALL|wxEXPAND, 10)
        gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(self.nodeConfigText, 0, wxTOP | wxBOTTOM, 5)
        gridSizer.Add(self.nodeConfigCtrl)
        gridSizer.Add(wxStaticText(self,-1,''))
        gridSizer.Add(self.nodeConfigRefresh,0,wxRIGHT)
        sizer.Add(gridSizer, 0, wxLEFT, 30)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.mediaText, 0, wxALL, 5)
        sizer2.Add(self.mediaLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND)

        sizer.Add(self.audioButton, 0, wxEXPAND|wxALL, 10)
        sizer.Add(self.displayButton, 0, wxEXPAND|wxALL, 10)
        sizer.Add(self.videoButton, 0, wxEXPAND|wxALL, 10)
                                       
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
               
class ProfilePanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:")
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,-1),
                                   validator = TextValidator("Name"))
        self.emailText = wxStaticText(self, -1, "Email:")
        self.emailCtrl = wxTextCtrl(self, -1, "",
                                    validator = TextValidator("Email"))
        
        self.phoneNumberText = wxStaticText(self, -1, "Phone Number:")
        self.phoneNumberCtrl = wxTextCtrl(self, -1, "")
        self.locationText = wxStaticText(self, -1, "Location:")
        self.locationCtrl = wxTextCtrl(self, -1, "")
        self.homeVenue= wxStaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wxTextCtrl(self, -1, "")
        self.profileTypeText = wxStaticText(self, -1, "Profile Type:")
       
        self.profile = None
        self.profileTypeBox = None
        self.dnText = None
        self.dnTextCtrl = None
       
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        self.__Layout()
        self.SetProfile(preferences.GetProfile())
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.emailCtrl.SetEditable(false)
            self.phoneNumberCtrl.SetEditable(false)
            self.locationCtrl.SetEditable(false)
            self.homeVenueCtrl.SetEditable(false)
            #self.profileTypeBox.SetEditable(false)
            self.dnTextCtrl.SetEditable(false)
        else:
            self.nameCtrl.SetEditable(true)
            self.emailCtrl.SetEditable(true)
            self.phoneNumberCtrl.SetEditable(true)
            self.locationCtrl.SetEditable(true)
            self.homeVenueCtrl.SetEditable(true)
            #self.profileTypeBox.SetEditable(true)
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __Layout(self):
        self.sizer1 = wxBoxSizer(wxVERTICAL)
        self.gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        self.gridSizer.Add(self.nameText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.phoneNumberText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wxALIGN_LEFT, 0)
        if self.profileTypeBox:
            self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        if self.dnText:
            self.gridSizer.Add(self.dnText, 0, wxALIGN_LEFT, 0)
            self.gridSizer.Add(self.dnTextCtrl, 0, wxEXPAND, 0)

        self.gridSizer.AddGrowableCol(1)
        self.sizer1.Add(self.gridSizer, 1, wxALL|wxEXPAND, 10)
        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)
        self.SetAutoLayout(1)
        self.Layout()
        
    def GetNewProfile(self):
        if(self.profile != None):
            self.profile.SetName(self.nameCtrl.GetValue())
            self.profile.SetEmail(self.emailCtrl.GetValue())
            self.profile.SetPhoneNumber(self.phoneNumberCtrl.GetValue())
            self.profile.SetLocation(self.locationCtrl.GetValue())
            self.profile.SetHomeVenue(self.homeVenueCtrl.GetValue())
            self.profile.SetProfileType(self.profileTypeBox.GetValue())

            if(self.profileTypeBox.GetSelection()==0):
                self.profile.SetProfileType('user')
            else:
                self.profile.SetProfileType('node')
                
        log.debug("ProfileDialog.GetNewProfile: Got profile information from dialog")
        return self.profile

    def Validate(self):
        self.nameCtrl.Validate()

    def SetProfile(self, profile):
        self.profile = profile
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], 
                                         style = wxCB_DROPDOWN|wxCB_READONLY)
        self.profileTypeBox.SetValue(self.profile.GetProfileType())
        self.__Layout()
        self.nameCtrl.SetValue(self.profile.GetName())
        self.emailCtrl.SetValue(self.profile.GetEmail())
        self.phoneNumberCtrl.SetValue(self.profile.GetPhoneNumber())
        self.locationCtrl.SetValue(self.profile.GetLocation())
        self.homeVenueCtrl.SetValue(self.profile.GetHomeVenue())
        if(self.profile.GetProfileType() == 'user'):
            self.profileTypeBox.SetSelection(0)
        else:
            self.profileTypeBox.SetSelection(1)
       
        self.__SetEditable(true)
        log.debug("ProfileDialog.SetProfile: Set profile information successfully in dialog")

class LoggingPanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.Centre()
        self.preferences = preferences
        self.cmdButton = wxCheckBox(self, wxNewId(), "  Display log messages in command window ")
        self.locationText = wxStaticText(self, -1, "Location of log files")
        self.locationCtrl = wxTextCtrl(self, -1, UserConfig.instance().GetLogDir(),
                                       size = wxSize(30, -1),  style = wxTE_READONLY)
        self.levelText = wxStaticText(self, -1, "Log levels ")
        self.scWindow = wxScrolledWindow(self, -1, size = wxSize(10,50),
                                         style = wxSUNKEN_BORDER)
        self.scWindow.SetBackgroundColour("WHITE")
        self.scWindow.EnableScrolling(true, true)
        self.scWindow.SetScrollbars(20, 20, 10, 10)

        self.logWidgets = {}
        self.logs = Log.GetCategories()
        self.logLevels = Log.GetLogLevels()
        logInt = self.logLevels.keys()
        logInt.sort()
        self.logLevelsSorted = []
        
        for i in logInt:
            self.logLevelsSorted.append(self.logLevels[i])
            
        self.cmdButton.SetValue(int(preferences.GetPreference(Preferences.LOG_TO_CMD)))

        self.__Layout()

    def __GetLogInt(self, logString):
        for value in self.logLevels.keys():
            if self.logLevels[value] == logString:
                return value
        
    def GetLogToCmd(self):
        if self.cmdButton.IsChecked():
            return 1
        else:
            return 0

    def GetLogCategories(self):
        categories = {}
        for category in self.logWidgets.keys():
            stringLevel = self.logWidgets[category].GetValue()
            intLevel = self.__GetLogInt(stringLevel)
            categories[category] = intLevel

        return categories
        
    def __Layout(self):
        self.logWidgets.clear()
        
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.cmdButton, 0, wxALL|wxEXPAND, 10)
       
        gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(self.locationText, 0)
        gridSizer.Add(self.locationCtrl,0 , wxEXPAND)
        gridSizer.AddGrowableCol(1)
        sizer.Add(gridSizer, 0, wxEXPAND| wxALL, 10)
        sizer.Add(self.levelText, 0, wxLEFT, 10)

        gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(wxSize(5,5))
        gridSizer.Add(wxSize(5,5))
        for logName in self.logs:
            gridSizer.Add(wxStaticText(self.scWindow, -1, logName), 0, wxLEFT, 5)
            try:
                logLevel = int(self.preferences.GetPreference(logName))
            except:
                logLevel = Log.DEBUG
           
            combo = wxComboBox(self.scWindow, -1,
                               self.logLevels[logLevel], 
                               choices = self.logLevelsSorted,
                               style = wxCB_DROPDOWN)
            gridSizer.Add(combo, 0, wxEXPAND|wxRIGHT, 5)
            # Save widget so we can retreive value later.
            self.logWidgets[logName] = combo

        gridSizer.Add(wxSize(5,5))
        gridSizer.AddGrowableCol(1)
        self.scWindow.SetSizer(gridSizer)
        gridSizer.Fit(self.scWindow)
        self.scWindow.SetAutoLayout(1)
                
        sizer.Add(self.scWindow, 1, wxEXPAND| wxALL, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class TextValidator(wxPyValidator):
    def __init__(self, fieldName):
        wxPyValidator.__init__(self)
        self.fieldName = fieldName
            
    def Clone(self):
        return TextValidator(self.fieldName)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        profile = win.GetNewProfile()

        if(len(val) < 1 or profile.IsDefault() 
             or profile.name == '<Insert Name Here>'
             or profile.email == '<Insert Email Address Here>'):
            
            if profile.name == '<Insert Name Here>':
                self.fieldName == 'Name'
            elif profile.email ==  '<Insert Email Address Here>':
                self.fieldName = 'Email'
                
            MessageDialog(NULL, "Please, fill in the %s field" %(self.fieldName,))
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.
        
class VenueConnectionPanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.Centre()
        self.titleText = wxStaticText(self, -1, "Recovery")
        self.titleLine = wxStaticLine(self, -1)
        self.shutdownMediaButton = wxCheckBox(self, wxNewId(), "  Shut down media tools on removal from Venue")
        self.reconnectButton = wxCheckBox(self, wxNewId(), "  Reconnect to venue automatically")
        self.maxText = wxStaticText(self, -1, "Recovery attempts ")
        self.maxReconnect = wx.lib.intctrl.IntCtrl(self, -1, 3, size = wxSize(30, -1))
        self.timeoutText = wxStaticText(self, -1, "Recovery timeout (seconds) ")
        self.timeout = wx.lib.intctrl.IntCtrl(self, -1, 10, size = wxSize(30, -1)) 
        shutdownMedia = int(preferences.GetPreference(Preferences.SHUTDOWN_MEDIA))
        self.shutdownMediaButton.SetValue(shutdownMedia)
        reconnect = int(preferences.GetPreference(Preferences.RECONNECT))
        self.reconnectButton.SetValue(reconnect)
        self.maxReconnect.SetValue(int(preferences.GetPreference(Preferences.MAX_RECONNECT)))
        self.timeout.SetValue(int(preferences.GetPreference(Preferences.RECONNECT_TIMEOUT)))
        self.EnableCtrls(reconnect)
                
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
                                
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
                                
        self.__Layout()

        EVT_CHECKBOX(self, self.reconnectButton.GetId(), self.ReconnectCB)

    def GetReconnect(self):
        if self.reconnectButton.IsChecked():
            return 1
        else:
            return 0

    def GetMaxReconnects(self):
        return self.maxReconnect.GetValue()

    def GetReconnectTimeOut(self):
        return self.timeout.GetValue()

    def EnableCtrls(self, value):
        self.maxReconnect.Enable(value)
        self.timeout.Enable(value)

    def ReconnectCB(self, event):
        self.EnableCtrls(event.IsChecked())

    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.titleText, 0, wxALL, 5)#,0,wxEXPAND|wxALL,10)
        sizer2.Add(self.titleLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND)
        sizer.Add(self.shutdownMediaButton, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.reconnectButton, 0, wxALL|wxEXPAND, 10)

        gridSizer = wxGridSizer(0, 2, 5, 5)
        gridSizer.Add(self.maxText, 0, wxLEFT, 30)
        gridSizer.Add(self.maxReconnect)
        gridSizer.Add(self.timeoutText, 0, wxLEFT, 30)
        gridSizer.Add(self.timeout)
        sizer.Add(gridSizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

class EditBridgeRegistryPanel(wxDialog):
    def __init__(self, parent, id, preferences):
        wxDialog.__init__(self, parent, id, 'Edit Bridge Registry URLs',
                                size = (560, 250),
                                style=wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER)

        self.parent = parent
        self.preferences = preferences
        self.maxRegistries = self.preferences.GetMaxBridgeRegistries()
        self.permanentRegistries = self.preferences.GetPermanentRegistries()

        if self.permanentRegistries > 0:
            self.fixedRegistryText = wxStaticText(self, -1, "Fixed: ",
                             size = wxSize(60, -1),
                             style=wxALIGN_RIGHT)
            self.fixedRegistryCtrl = wxTextCtrl(self, -1,
                             size = wxSize(480, 21*self.permanentRegistries),
                             style = wxTE_RICH | wxTE_MULTILINE | wxTE_READONLY)
            self.fixedRegistryCtrl.SetBackgroundColour(self.GetBackgroundColour())
        self.editableRegistryText = wxStaticText(self, -1, "Editable: ",
                             size = wxSize(60, -1),
                             style=wxALIGN_RIGHT)
        self.editableRegistryCtrl = wxTextCtrl(self, -1,
                       size = wxSize(480, 19*(self.maxRegistries-self.permanentRegistries)),
                       style = wxTE_RICH | wxTE_MULTILINE | wxTE_PROCESS_ENTER)

        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.okButton = wxButton(self, wxID_OK, "OK")
                                
        EVT_BUTTON(self, self.cancelButton.GetId(), self.OnCancel)
        EVT_BUTTON(self, self.okButton.GetId(), self.OnOK)
        EVT_CHAR(self.editableRegistryCtrl, self.OnChar)

        # Populate with existing registries.
        # The single registry TextCtrl in the parent has to be split
        # between fixed and editable TextCtrls here.
        #
        for lineNo in range(0,self.maxRegistries):
            lineNoEntry = self.parent.registryCtrl.GetLineText(lineNo)
            if self.permanentRegistries > 0:
                if lineNo < (self.permanentRegistries - 1):
                    self.fixedRegistryCtrl.AppendText(lineNoEntry + '\n')
                elif lineNo == (self.permanentRegistries - 1):
                    self.fixedRegistryCtrl.AppendText(lineNoEntry)
                elif lineNo < (self.maxRegistries - 1):
                    self.editableRegistryCtrl.AppendText(lineNoEntry + '\n')
                elif lineNo == (self.maxRegistries - 1):
                    self.editableRegistryCtrl.AppendText(lineNoEntry)
                else:
                    # Unknown entry index
                    pass
            else:
                if lineNo < (self.maxRegistries - 1):
                    self.editableRegistryCtrl.AppendText(lineNoEntry + '\n')
                elif lineNo == (self.maxRegistries - 1):
                    self.editableRegistryCtrl.AppendText(lineNoEntry)
                else:
                    # Unknown entry index
                    pass

        # Position the InsertionCursor at the end of the first "None" entry
        # of the editable TextCtrl. If there is no 'None" entry, then position
        # it at the end of the end of the first entry.
        #
        self.foundNone = false
        for lineNo in range(0, self.editableRegistryCtrl.GetNumberOfLines()):
            if self.editableRegistryCtrl.GetLineText(lineNo).startswith("None"):
                self.editableRegistryCtrl.SetInsertionPoint(
                      self.editableRegistryCtrl.XYToPosition(
                      self.editableRegistryCtrl.GetLineLength(lineNo), lineNo))
                self.foundNone = true
                break
        if not self.foundNone:
            self.editableRegistryCtrl.SetInsertionPoint(
                                self.editableRegistryCtrl.XYToPosition(
                                self.editableRegistryCtrl.GetLineLength(0), 0))
        wxCallAfter(self.editableRegistryCtrl.SetFocus)

        self.__Layout()
        

    def OnCancel(self, event):
        self.EndModal(wxID_CANCEL)

    def OnOK(self, event):
        # Remove existing editable entries
        self.parent.registryCtrl.Remove(
            self.parent.registryCtrl.XYToPosition(0,self.permanentRegistries),
            self.parent.registryCtrl.GetLastPosition())
        # Add replacement entries
        for lineNo in range(0, self.maxRegistries - self.permanentRegistries):
            if self.editableRegistryCtrl.GetLineLength(lineNo) == 0:
                lineNoEntry = 'None'
            else:
                lineNoEntry = self.editableRegistryCtrl.GetLineText(lineNo)
            self.parent.registryCtrl.AppendText(lineNoEntry + '\n')
        # Remove final '\n'
        self.parent.registryCtrl.Remove(
            self.parent.registryCtrl.GetLastPosition()-1,
            self.parent.registryCtrl.GetLastPosition())
        self.Validate()
        self.TransferDataFromWindow()
        self.EndModal(wxID_OK)


    def OnChar(self, event):
        '''
        Called on keyboard event in Editable Registries Ctrl.
        In particular, we want to catch the following keyboard events:
        1. Return 
            we don't want to add entries beyond the maximum
        2. Backspace
            we don't want to delete whole entries (just characters
            within an entry)
        3. Delete
            allow delete except when it would delete a whole entry
        '''
        k = event.GetKeyCode()
        maxEditableEntries = self.maxRegistries - self.permanentRegistries

        if k == WXK_BACK:
            # Don't process if insertion point is at beginning of entry
            # (and would result in reducing number of entries)
            position = self.editableRegistryCtrl.GetInsertionPoint()
            (x,y) = self.editableRegistryCtrl.PositionToXY(position)
            linelength = self.editableRegistryCtrl.GetLineLength(y)
            if position == self.editableRegistryCtrl.GetLastPosition():
                if linelength < 0:
                    pass
                else:
                    event.Skip()
                pass
            else:
                if linelength <= 0 or x <= 0:
                    pass
                else:
                    event.Skip()
        elif k == WXK_RETURN:
            # Don't process if we'd be adding and extra entry beyond the max
            # (maybe the test itself isn't needed if we've otherwise caught
            #  all possibilites of deleting any entries)
            if self.editableRegistryCtrl.GetNumberOfLines() >= maxEditableEntries:
                pass
            else:
                event.Skip()
        elif k == WXK_DELETE:
            # Don't process if we're at the end of any entry
            position = self.editableRegistryCtrl.GetInsertionPoint()
            (x,y) = self.editableRegistryCtrl.PositionToXY(position)
            linelength = self.editableRegistryCtrl.GetLineLength(y)
            if x == linelength or position == self.editableRegistryCtrl.GetLastPosition():
                pass
            else:
                event.Skip()
        else:
            event.Skip()

    def __Layout(self):
        gridsizer = wxFlexGridSizer(0, 2, 5, 5)
        if self.permanentRegistries > 0:
            gridsizer.Add(self.fixedRegistryText, 0, wxEXPAND | wxALL, 0)
            gridsizer.Add(self.fixedRegistryCtrl, 0, wxEXPAND | wxALL, 0)
        gridsizer.Add(self.editableRegistryText, 0, wxEXPAND | wxALL, 0)
        gridsizer.Add(self.editableRegistryCtrl, 0, wxEXPAND | wxALL, 0)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 10)
        buttonSizer.Add(self.okButton, 0, wxALL, 10)

        sizer = wxBoxSizer(wxVERTICAL)
        sizer.AddSpacer(wxSize(-1,10))
        sizer.Add(gridsizer, 0, wxALIGN_CENTER)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        

class NetworkPanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.preferences = preferences
        self.Centre()
        self.titleText = wxStaticText(self, -1, "Multicast")
        self.titleLine = wxStaticLine(self, -1)
        self.multicastButton = wxCheckBox(self, wxNewId(), "  Use unicast ")
        self.keyMap = {}
        self.selected = None
        self.editBridgeRegistryPanel = None
        self.permanentRegistries = self.preferences.GetPermanentRegistries()
        self.maxRegistries = self.preferences.GetMaxBridgeRegistries()

        bridgeDict = preferences.GetBridges()
        self.bridges = bridgeDict.values()
        
        # make a copy of the bridges, since we modify them in place
        import copy
        self.bridges = map( lambda x: copy.copy(x), self.bridges)
        self.bridges.sort(lambda x,y: cmp(x.rank,y.rank))

        self.multicastButton.SetValue(not int(preferences.GetPreference(Preferences.MULTICAST)))

        self.beaconButton = wxCheckBox(self, wxNewId(), "  Run beacon ")
        
        self.beaconButton.SetValue(int(preferences.GetPreference(Preferences.BEACON)))
        self.listHelpText = wxStaticText(self,-1,'Right-click a bridge below to enable or disable it')


        self.list = wxListCtrl(self, wxNewId(),style=wxLC_REPORT|wxLC_SINGLE_SEL)
        self.list.InsertColumn(0, "Bridge")
        self.list.InsertColumn(1, "Host")
        self.list.InsertColumn(2, "Port")
        self.list.InsertColumn(3, "Type")
        self.list.InsertColumn(4, "Status")
        self.list.InsertColumn(5, "Distance")
        self.list.InsertColumn(6, "Port range")
              
        self.list.SetColumnWidth(0, 90)
        self.list.SetColumnWidth(1, 60)
        self.list.SetColumnWidth(2, 50)
        self.list.SetColumnWidth(3, 80)
        self.list.SetColumnWidth(4, 60)
        self.list.SetColumnWidth(5, 60)
        self.list.SetColumnWidth(6, 90)
        self.__InitList()
        
        self.refreshButton = wxButton(self,-1,'Refresh')
        self.registryText = wxStaticText(self, -1, "Bridge Registries:",
                             size=(120,-1))
        self.registryCtrl = wxTextCtrl(self, -1, size = (350,-1),
                             style = wxTE_RICH | wxTE_MULTILINE | wxTE_READONLY)
        if self.permanentRegistries < self.maxRegistries:
            self.registryEditButton = wxButton(self, -1, 'Edit')
        
        regPrefs = self.preferences.GetPreference(Preferences.BRIDGE_REGISTRY).split('|')
        registriesAdded = 0
        for reg in regPrefs:
            if registriesAdded >= self.maxRegistries:
                break
            if len(reg.strip()) < 1:
                self.registryCtrl.AppendText("None" + "\n")
            else:
                self.registryCtrl.AppendText(reg.strip() + "\n")
            registriesAdded += 1
        for pad in range (registriesAdded, self.maxRegistries):
            self.registryCtrl.AppendText("None" + "\n")
        # Remove final '\n' (which adds an empty line at end of entries)
        self.registryCtrl.Remove(self.registryCtrl.GetLastPosition()-1,self.registryCtrl.GetLastPosition())
        
        EVT_RIGHT_DOWN(self.list, self.OnRightDown)
        EVT_RIGHT_UP(self.list, self.OnRightClick)
        EVT_BUTTON(self,self.refreshButton.GetId(), self.OnRefresh)
        if self.permanentRegistries < self.maxRegistries:
            EVT_BUTTON(self, self.registryEditButton.GetId(), self.OnEdit)
                                      
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
                                
        self.__Layout()
        
    def OnRightDown(self, event):
        """
        Invoked when user righ-click an item in the list
        """
        self.x = event.GetX()
        self.y = event.GetY()
        item, flags = self.list.HitTest((self.x, self.y))

        if flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)
            self.selected = item
   
    def OnRightClick(self, event):
        '''
        Invoked when user releases right click in the list.
        '''
        # only do this part the first time so the events are only bound once
        if not hasattr(self, "enableId"):
            self.enableId = wx.NewId()
            EVT_MENU(self, self.enableId, self.Enable)
            
        # make a menu
        self.menu = wx.Menu()
        self.menu.AppendCheckItem(self.enableId, "Enabled")

        # Check the actual item to see if it is enabled or not
        selectedItem = self.bridges[self.selected]
        if selectedItem.status == STATUS_ENABLED:
            self.menu.Check(self.enableId, 1)
        else: 
            self.menu.Check(self.enableId, 0)

        self.list.PopupMenu(self.menu, wxPoint(self.x, self.y))
        self.menu.Destroy()

    def OnRefresh(self,event):
    
        wxBeginBusyCursor()
    
        try:
            venueClient = self.preferences.venueClient
        
            # Force rescanning of the bridges
            venueClient.SetupBridgePrefs()
            self.bridges = venueClient.LoadBridges(rankBridges=1)     
            self.bridges.sort(lambda x,y: cmp(x.rank,y.rank))

            # Refresh the bridge list in the UI
            self.__InitList()
        finally:
            wxEndBusyCursor()

    def OnEdit(self, event):
        if self.editBridgeRegistryPanel:
            # Edit panel already open
            return

        # This _should_ be redundant, since no Edit button should
        # be available when the condition is true.
        if self.permanentRegistries >= self.maxRegistries:
            MessageDialog(NULL, "There are no editable entries")
            return


        self.editBridgeRegistryPanel = EditBridgeRegistryPanel(self,
                                         wxNewId(), self.preferences)

        if self.editBridgeRegistryPanel.ShowModal() == wxID_OK:
            log.info("Edited bridge registries OK")

        # The Ctrl is displaying the desired registry prefs, but
        # we still need to actually set them as preferences.
        #
        prefString = ''
        for regId in range(0, self.maxRegistries):
            prefString = prefString + "%s | " % self.GetRegistry(regId).strip()
        prefString = prefString.rstrip(' |')
        self.preferences.SetPreference(Preferences.BRIDGE_REGISTRY, prefString)

        self.editBridgeRegistryPanel = None

    def Enable(self, event):
        '''
        Invoked when user selects enable in the item menu.
        '''
        enableFlag = event.IsChecked()
        self.menu.Check(self.enableId, enableFlag)

        selectedItem = self.bridges[self.selected]
        if enableFlag:
            selectedItem.status= STATUS_ENABLED
        else:
            selectedItem.status = STATUS_DISABLED

        self.list.SetStringItem(self.selected, 4, selectedItem.status)

    def GetBridges(self):
        retBridges = {}
        for b in self.bridges:
            retBridges[b.guid] = b
        return retBridges
                                    
    def GetMulticast(self):
        if self.multicastButton.IsChecked():
            return 0
        else:
            return 1

    def GetBeacon(self):
        if self.beaconButton.IsChecked():
            return 1
        else:
            return 0

    def GetRegistry(self, regId):
        if regId < 0:
            regText = ''
            for reg in range(0, self.maxRegistries):
                regText = regText + "%s |" % self.registryCtrl.GetLineText(reg)
            return regText.rstrip(' |')
        else:
            regText = self.registryCtrl.GetLineText(regId)
            if regText.startswith('None'):
                return ''
            else:
                return regText

    def __InitList(self):

        # Clear the list
        self.list.DeleteAllItems()
        
        # Populate the list
        for index in range(len(self.bridges)):
            self.list.InsertStringItem(index, self.bridges[index].name)
            self.list.SetStringItem(index, 1, self.bridges[index].host)
            self.list.SetStringItem(index, 2, str(self.bridges[index].port))
            self.list.SetStringItem(index, 3, self.bridges[index].serverType)
            self.list.SetStringItem(index, 4, self.bridges[index].status)
            if self.bridges[index].rank == BridgeDescription.UNREACHABLE:
                self.list.SetStringItem(index, 5, "Unreachable")
            else:
                self.list.SetStringItem(index, 5, str(self.bridges[index].rank))
            self.list.SetStringItem(index, 6, '%d-%d' % (self.bridges[index].portMin,self.bridges[index].portMax))
          
    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.titleText, 0, wxALL, 5)
        sizer2.Add(self.titleLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND)
        sizer.Add(self.beaconButton, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.multicastButton, 0, wxALL|wxEXPAND, 10)
        gridSizer = wxFlexGridSizer(0, 3, 5, 5)
        gridSizer.Add(self.registryText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.registryCtrl, 0, wxEXPAND, 0)
        if self.permanentRegistries < self.maxRegistries:
            gridSizer.Add(self.registryEditButton, 0, wxLEFT, 5)
        sizer.Add(gridSizer, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.listHelpText, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.list, 1, wxALL|wxEXPAND, 10)
        sizer.Add(self.refreshButton, 0, wxALL, 10)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
        self.Layout()

class ProxyPanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.Centre()
        self.hostText = wxStaticText(self, -1, "Hostname:")
        self.hostCtrl = wxTextCtrl(self, -1, "")
        self.portText = wxStaticText(self, -1, "Port:")
        self.portCtrl = wxTextCtrl(self, -1, "")
       
        self.titleText = wxStaticText(self, -1, "HTTP Proxy Server")
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))

        self.SetHost(preferences.GetPreference(Preferences.PROXY_HOST))
        self.SetPort(preferences.GetPreference(Preferences.PROXY_PORT))
        
        self.__Layout()

    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.titleText, 0, wxALL, 5)
        sizer2.Add(self.titleLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer1.Add(sizer2, 0, wxEXPAND)
        self.gridSizer = wxFlexGridSizer(0, 2, 2, 5)
        self.gridSizer.Add(self.hostText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.hostCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.portText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.portCtrl, 0, wxEXPAND, 0)

        self.gridSizer.AddGrowableCol(1)
        sizer1.Add(self.gridSizer, 1, wxALL|wxEXPAND, 10)
        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        
        self.Layout()
        
    def SetHost(self,host):
        self.hostCtrl.SetValue(host)
        
    def SetPort(self,port):
        self.portCtrl.SetValue(str(port))
        
    def GetHost(self):
        return self.hostCtrl.GetValue()
        
    def GetPort(self):
        return self.portCtrl.GetValue()
                
class NavigationPanel(wxPanel):
    def __init__(self, parent, id, preferences):
        wxPanel.__init__(self, parent, id)
        self.Centre()
        self.titleText = wxStaticText(self, -1, "Navigation View")
        self.titleLine = wxStaticLine(self, -1)
        self.exitsButton = wxRadioButton(self, wxNewId(), "  Show Exits ")
        self.myVenuesButton = wxRadioButton(self, wxNewId(), "  Show My Venues ")
        self.allVenuesButton = wxRadioButton(self, wxNewId(), "  Show All Venues ")

        value = preferences.GetPreference(Preferences.DISPLAY_MODE)
        if value == Preferences.EXITS:
            self.exitsButton.SetValue(1)
        elif value == Preferences.MY_VENUES:
            self.myVenuesButton.SetValue(1)
        elif value == Preferences.ALL_VENUES:
            self.allVenuesButton.SetValue(1)
               
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
                                
        self.__Layout()
         
    def GetDisplayMode(self):
        if self.exitsButton.GetValue():
            return Preferences.EXITS
        elif self.myVenuesButton.GetValue():
            return Preferences.MY_VENUES
        elif self.allVenuesButton.GetValue():
            return Preferences.ALL_VENUES
          
    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.titleText, 0, wxALL, 5)
        sizer2.Add(self.titleLine, 1, wxALIGN_CENTER | wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND)
        sizer.Add(self.exitsButton, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.myVenuesButton, 0, wxALL|wxEXPAND, 10)
        sizer.Add(self.allVenuesButton, 0, wxALL|wxEXPAND, 10)
               
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
if __name__ == "__main__":
    from AccessGrid.Toolkit import WXGUIApplication
    
    pp = wxPySimpleApp()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # Try to initialize
    app.Initialize("Preferences")
    
    p = Preferences()
    pDialog = PreferencesDialog(NULL, -1,
                                'Preferences', p)
    pDialog.ShowModal()
    p = pDialog.GetPreferences()
    p.StorePreferences()
    
