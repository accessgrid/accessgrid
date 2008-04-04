import os

from AccessGrid import Log
from AccessGrid.Platform import IsOSX
from AccessGrid.Preferences import Preferences
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.Platform.Config import AGTkConfig
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW
from AccessGrid.GUID import GUID
from AccessGrid.Descriptions import BridgeDescription, QUICKBRIDGE_TYPE, UMTP_TYPE
from AccessGrid.Descriptions import STATUS_ENABLED, STATUS_DISABLED
from AccessGrid.UIUtilities import MessageDialog, TextDialog

import wx
import  wx.lib.intctrl
from AccessGrid import icons

log = Log.GetLogger(Log.VenueClient)

class PreferencesDialog(wx.Dialog):
    ID_WINDOW_LEFT = 0
    ID_WINDOW_RIGHT = 1
    
    def __init__(self, parent, id, title, preferences):
        '''
        Initialize ui components and events.
        '''
        wx.Dialog.__init__(self, parent, id, title,
                          style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE,
                          size = wx.Size(720, 576))
        self.Centre()
       
      
        self.sideWindow = wx.SashWindow(self, self.ID_WINDOW_LEFT,
                                       wx.DefaultPosition,
                                       wx.Size(150, -1))

        self.sideWindow.SetSashVisible(wx.SASH_RIGHT, True)
        
        self.preferencesWindow = wx.SashWindow(self, self.ID_WINDOW_RIGHT,
                                              wx.DefaultPosition,
                                              wx.Size(170, -1))
        self.sideTree = wx.TreeCtrl(self.sideWindow, wx.NewId(), wx.DefaultPosition, 
                                   size=(200, -1), style = wx.TR_HIDE_ROOT)

        # wxPython 2.8 workaround - sideWindow width doesn't get set otherwise
        self.sideWindow.SetSize((150, -1))

        self.okButton = wx.Button(self, wx.ID_OK, "Save")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Close")
        self.preferences = preferences

        # Create panels for preferences
        self.preferencesPanel = wx.Panel(self.preferencesWindow, wx.NewId(),
                                        style = wx.SUNKEN_BORDER)
        self.title = wx.TextCtrl(self.preferencesPanel, wx.NewId(), "TITLE",
                                style = wx.TE_READONLY | wx.TE_CENTRE )
        self.nodePanel = NodePanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.profilePanel = ProfilePanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.loggingPanel = LoggingPanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.venueConnectionPanel = VenueConnectionPanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.networkPanel = NetworkPanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.bridgingPanel = BridgingPanel(self.preferencesPanel, wx.NewId(),
                                         self.preferences)
        self.navigationPanel = NavigationPanel(self.preferencesPanel, wx.NewId(),
                                               self.preferences)

        self.loggingPanel.Hide()
        self.venueConnectionPanel.Hide()
        self.networkPanel.Hide()
        self.bridgingPanel.Hide()
        self.navigationPanel.Hide()
        self.nodePanel.Hide()
        self.currentPanel = self.loggingPanel
        
        wx.EVT_SASH_DRAGGED(self.sideWindow, self.ID_WINDOW_LEFT, self.__OnSashDrag)
        wx.EVT_TREE_SEL_CHANGED(self, self.sideTree.GetId(), self.OnSelect)
        wx.EVT_SIZE(self, self.__OnSize)
        
        self.title.Hide()

        self.__Layout()
        self.__InitTree()

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
        self.preferences.SetPreference(Preferences.BEACON,
                                       self.networkPanel.GetBeacon())
        self.preferences.SetPreference(Preferences.MULTICAST_DETECT_HOST,
                                       self.networkPanel.GetMulticastDetectionHost())
        self.preferences.SetPreference(Preferences.MULTICAST_DETECT_PORT,
                                       self.networkPanel.GetMulticastDetectionPort())
        self.preferences.SetPreference(Preferences.PROXY_ENABLED,
                                       self.networkPanel.GetProxyEnabled())
        self.preferences.SetPreference(Preferences.PROXY_HOST,
                                       self.networkPanel.GetProxyHost())
        self.preferences.SetPreference(Preferences.PROXY_PORT,
                                       self.networkPanel.GetProxyPort())
        self.preferences.SetPreference(Preferences.PROXY_USERNAME,
                                       self.networkPanel.GetProxyUsername())
        self.preferences.SetProxyPassword(self.networkPanel.GetProxyPassword())
        self.preferences.SetPreference(Preferences.PROXY_AUTH_ENABLED,
                                       self.networkPanel.GetAuthProxyEnabled())
        self.preferences.SetPreference(Preferences.MULTICAST,
                                       self.bridgingPanel.GetMulticast())
        self.preferences.SetPreference(Preferences.BRIDGE_REGISTRY,
                                       self.bridgingPanel.GetRegistry(-1))
        self.preferences.SetBridges(self.bridgingPanel.GetBridges())
        self.preferences.SetPreference(Preferences.BRIDGE_PING_UPDATE_DELAY,
                                       self.bridgingPanel.GetBridgePingDelay())
        self.preferences.SetPreference(Preferences.ORDER_BRIDGES_BY_PING,
                                       self.bridgingPanel.GetOrderBridgesByPing())
        self.preferences.SetPreference(Preferences.DISPLAY_MODE,
                                       self.navigationPanel.GetDisplayMode())
        self.preferences.SetPreference(Preferences.VENUESERVER_URLS,
                                       self.navigationPanel.GetVenueServers())

        cDict = self.loggingPanel.GetLogCategories()
        for category in cDict.keys():
            self.preferences.SetPreference(category, cDict[category])

        p = self.profilePanel.GetNewProfile()
        self.preferences.SetProfile(p)

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
        self.network = self.sideTree.AppendItem(self.root,
                                                " Network")
        self.bridging = self.sideTree.AppendItem(self.root,
                                                " Bridging")
        self.navigation = self.sideTree.AppendItem(self.root,
                                                " Navigation")
        self.venueConnection = self.sideTree.AppendItem(self.root,
                                                " Venue Connection")
        self.logging = self.sideTree.AppendItem(self.root,
                                                " Logging")
        self.sideTree.SetItemData(self.profile,
                                  wx.TreeItemData(self.profilePanel))
        self.sideTree.SetItemData(self.node,
                                  wx.TreeItemData(self.nodePanel))
        self.sideTree.SetItemData(self.logging,
                                  wx.TreeItemData(self.loggingPanel))
        self.sideTree.SetItemData(self.venueConnection,
                                  wx.TreeItemData(self.venueConnectionPanel))
        self.sideTree.SetItemData(self.network,
                                  wx.TreeItemData(self.networkPanel))
        self.sideTree.SetItemData(self.bridging,
                                  wx.TreeItemData(self.bridgingPanel))
        self.sideTree.SetItemData(self.navigation,
                                  wx.TreeItemData(self.navigationPanel))
        self.sideTree.SelectItem(self.profile)

    def __OnSize(self,event):
        '''
        Called when window is resized.
        '''
        #
        # Work around a suspected wx. bug. Get the size of the sideWindow and
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
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            return
        
        eID = event.GetId()
        
        if eID == self.ID_WINDOW_LEFT:
            width = event.GetDragRect().width
            self.sideWindow.SetSize(wx.Size(width, -1))
            
        elif eID == self.ID_WINDOW_RIGHT:
            width = event.GetDragRect().width
            self.preferencesWindow.SetSize(wx.Size(width, -1))

        self.__Layout()
        
    def __Layout(self):
        '''
        Fix ui layout
        '''
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.sideWindow,0,wx.EXPAND)
        sizer.Add(self.preferencesWindow,1,wx.EXPAND)

        mainSizer.Add(sizer, 1, wx.EXPAND)
        
        prefPanelBox = wx.BoxSizer(wx.VERTICAL)
        self.preferencesPanel.SetSizer(prefPanelBox)
        prefPanelBox.Add(self.title, 0, wx.EXPAND)
        prefPanelBox.Add(self.currentPanel, 1, wx.EXPAND|wx.TOP, 5)

        prefBox = wx.BoxSizer(wx.HORIZONTAL)
        self.preferencesWindow.SetSizer(prefBox)
        prefBox.Add(self.preferencesPanel, 1, wx.EXPAND)
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wx.RIGHT | wx.ALIGN_CENTER, 5)
        buttonSizer.Add(self.cancelButton, 0, wx.ALIGN_CENTER)

        mainSizer.Add(buttonSizer, 0, wx.ALL| wx.ALIGN_CENTER, 5)

        #w,h = self.preferencesWindow.GetSizeTuple()
        #if self.currentPanel.GetSizer():
        #    self.currentPanel.GetSizer().SetDimension(0,0,w,h)

        self.SetSizer(mainSizer)
        self.Layout()
        
class NodePanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.preferences = preferences
        self.Centre()

        self.nodeText = wx.StaticText(self, -1, "Node")
        self.nodeLine = wx.StaticLine(self, -1)
        self.mediaButton = wx.CheckBox(self, wx.NewId(), "  Launch node services on startup ")
        self.nodeUrlText = wx.StaticText(self, -1, "Node service")
        self.nodeBuiltInCheckbox = wx.RadioButton(self,wx.NewId(),'Built-in', style=wx.RB_GROUP)
        self.nodeExternalCheckbox = wx.RadioButton(self,wx.NewId(),'External')
        self.nodeUrlCtrl = wx.TextCtrl(self, -1, "", size = wx.Size(250, -1))
        self.nodeConfigText = wx.StaticText(self, -1, "Node configuration")
        self.nodeConfigRefresh = wx.Button(self,-1,'Refresh')
        self.mediaText = wx.StaticText(self, -1, "Media")
        self.mediaLine = wx.StaticLine(self, -1)
        self.audioButton = wx.CheckBox(self, wx.NewId(), " Enable Audio")
        self.displayButton = wx.CheckBox(self, wx.NewId(), " Enable Display")
        self.videoButton = wx.CheckBox(self, wx.NewId(), " Enable Video")

        self.mediaButton.SetValue(int(preferences.GetPreference(Preferences.STARTUP_MEDIA)))
        nodeBuiltin = int(preferences.GetPreference(Preferences.NODE_BUILTIN))
        self.nodeBuiltInCheckbox.SetValue(nodeBuiltin)
        self.nodeExternalCheckbox.SetValue(not nodeBuiltin)
        
        nodeUrl = preferences.GetPreference(Preferences.NODE_URL)
        self.nodeUrlCtrl.SetValue(nodeUrl)
        if  nodeBuiltin:
            self.nodeBuiltInCheckbox.SetValue(True)
            self.nodeUrlCtrl.SetEditable(False)
        else:
            self.nodeExternalCheckbox.SetValue(True)
            self.nodeUrlCtrl.SetEditable(True)
            
        self.audioButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_AUDIO)))
        self.displayButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_DISPLAY)))
        self.videoButton.SetValue(int(preferences.GetPreference(Preferences.ENABLE_VIDEO)))

        self.configMap = {}
        self.nodeConfigCtrl = wx.Choice(self, wx.NewId(),
                                       size = wx.Size(235, -1))
                                       
        self.OnRefresh()

        # Set events
        wx.EVT_RADIOBUTTON(self,self.nodeBuiltInCheckbox.GetId(),self.OnNodeBuiltIn)
        wx.EVT_RADIOBUTTON(self,self.nodeExternalCheckbox.GetId(),self.OnNodeExternal)
        wx.EVT_TEXT_ENTER(self,self.nodeUrlCtrl.GetId(),self.OnRefresh)
        wx.EVT_BUTTON(self,self.nodeConfigRefresh.GetId(),self.OnRefresh)
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
        nodeConfigs = []
        try:
            if nodeService:
                nodeConfigs = nodeService.GetConfigurations()
        except:
            log.exception("Failed to retreive node configurations")

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
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.nodeText, 0, wx.ALL, 5)
        sizer2.Add(self.nodeLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)

        gridSizer = wx.FlexGridSizer(0, 2, 5, 5)
        gridSizer2 = wx.FlexGridSizer(3, 1, 5, 5)
        gridSizer.Add(self.nodeUrlText, 0, wx.ALL, 5)
        gridSizer2.Add(self.nodeBuiltInCheckbox)
        gridSizer2.Add(self.nodeExternalCheckbox)
        gridSizer2.Add(self.nodeUrlCtrl)
        gridSizer.Add(gridSizer2)
        sizer.Add(gridSizer, 0, wx.ALL, 5)
                
        sizer.Add(self.mediaButton, 0, wx.ALL|wx.EXPAND, 10)
        gridSizer = wx.FlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(self.nodeConfigText, 0, wx.TOP | wx.BOTTOM, 5)
        gridSizer.Add(self.nodeConfigCtrl)
        gridSizer.Add(wx.StaticText(self,-1,''))
        gridSizer.Add(self.nodeConfigRefresh,0,wx.RIGHT)
        sizer.Add(gridSizer, 0, wx.LEFT, 30)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.mediaText, 0, wx.ALL, 5)
        sizer2.Add(self.mediaLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)

        sizer.Add(self.audioButton, 0, wx.EXPAND|wx.ALL, 10)
        sizer.Add(self.displayButton, 0, wx.EXPAND|wx.ALL, 10)
        sizer.Add(self.videoButton, 0, wx.EXPAND|wx.ALL, 10)
                                       
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
               
class ProfilePanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.Centre()
        self.nameText = wx.StaticText(self, -1, "Name:")
        self.nameCtrl = wx.TextCtrl(self, -1, "", size = (400,-1),
                                   validator = TextValidator("Name"))
        self.emailText = wx.StaticText(self, -1, "Email:")
        self.emailCtrl = wx.TextCtrl(self, -1, "",
                                    validator = TextValidator("Email"))
        
        self.phoneNumberText = wx.StaticText(self, -1, "Phone Number:")
        self.phoneNumberCtrl = wx.TextCtrl(self, -1, "")
        self.locationText = wx.StaticText(self, -1, "Location:")
        self.locationCtrl = wx.TextCtrl(self, -1, "")
        self.homeVenue= wx.StaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wx.TextCtrl(self, -1, "")
        self.profileTypeText = wx.StaticText(self, -1, "Profile Type:")
       
        self.profile = None
        self.profileTypeBox = None
        self.dnText = None
        self.dnTextCtrl = None
       
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        self.__Layout()
        self.SetProfile(preferences.GetProfile())
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(False)
            self.emailCtrl.SetEditable(False)
            self.phoneNumberCtrl.SetEditable(False)
            self.locationCtrl.SetEditable(False)
            self.homeVenueCtrl.SetEditable(False)
            #self.profileTypeBox.SetEditable(False)
            self.dnTextCtrl.SetEditable(False)
        else:
            self.nameCtrl.SetEditable(True)
            self.emailCtrl.SetEditable(True)
            self.phoneNumberCtrl.SetEditable(True)
            self.locationCtrl.SetEditable(True)
            self.homeVenueCtrl.SetEditable(True)
            #self.profileTypeBox.SetEditable(True)
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __Layout(self):
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.gridSizer = wx.FlexGridSizer(0, 2, 5, 5)
        self.gridSizer.Add(self.nameText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.phoneNumberText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wx.ALIGN_LEFT, 0)
        if self.profileTypeBox:
            self.gridSizer.Add(self.profileTypeBox, 0, wx.EXPAND, 0)
        if self.dnText:
            self.gridSizer.Add(self.dnText, 0, wx.ALIGN_LEFT, 0)
            self.gridSizer.Add(self.dnTextCtrl, 0, wx.EXPAND, 0)

        self.gridSizer.AddGrowableCol(1)
        self.sizer1.Add(self.gridSizer, 1, wx.ALL|wx.EXPAND, 10)
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
        self.profileTypeBox = wx.ComboBox(self, -1, choices =['user', 'node'], 
                                         style = wx.CB_DROPDOWN|wx.CB_READONLY)
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
       
        self.__SetEditable(True)
        log.debug("ProfileDialog.SetProfile: Set profile information successfully in dialog")

class LoggingPanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.Centre()
        self.preferences = preferences
        self.cmdButton = wx.CheckBox(self, wx.NewId(), "  Display log messages in command window ")
        self.locationText = wx.StaticText(self, -1, "Location of log files")
        self.locationCtrl = wx.TextCtrl(self, -1, UserConfig.instance().GetLogDir(),
                                       size = wx.Size(30, -1),  style = wx.TE_READONLY)
        self.levelText = wx.StaticText(self, -1, "Log levels ")
        self.scWindow = wx.ScrolledWindow(self, -1, size = wx.Size(10,50),
                                         style = wx.SUNKEN_BORDER)
        self.scWindow.SetBackgroundColour("WHITE")
        self.scWindow.EnableScrolling(True, True)
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
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.cmdButton, 0, wx.ALL|wx.EXPAND, 10)
       
        gridSizer = wx.FlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(self.locationText, 0)
        gridSizer.Add(self.locationCtrl,0 , wx.EXPAND)
        gridSizer.AddGrowableCol(1)
        sizer.Add(gridSizer, 0, wx.EXPAND| wx.ALL, 10)
        sizer.Add(self.levelText, 0, wx.LEFT, 10)

        gridSizer = wx.FlexGridSizer(0, 2, 5, 5)
        gridSizer.Add(wx.Size(5,5))
        gridSizer.Add(wx.Size(5,5))
        for logName in self.logs:
            gridSizer.Add(wx.StaticText(self.scWindow, -1, logName), 0, wx.LEFT, 5)
            try:
                logLevel = int(self.preferences.GetPreference(logName))
            except:
                logLevel = Log.DEBUG
           
            combo = wx.ComboBox(self.scWindow, -1,
                               self.logLevels[logLevel], 
                               choices = self.logLevelsSorted,
                               style = wx.CB_DROPDOWN)
            gridSizer.Add(combo, 0, wx.EXPAND|wx.RIGHT, 5)
            # Save widget so we can retreive value later.
            self.logWidgets[logName] = combo

        gridSizer.Add(wx.Size(5,5))
        gridSizer.AddGrowableCol(1)
        self.scWindow.SetSizer(gridSizer)
        gridSizer.Fit(self.scWindow)
        self.scWindow.SetAutoLayout(1)
                
        sizer.Add(self.scWindow, 1, wx.EXPAND| wx.ALL, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class TextValidator(wx.PyValidator):
    def __init__(self, fieldName):
        wx.PyValidator.__init__(self)
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
                
            MessageDialog(None, "Please fill in the %s field" %(self.fieldName,))
            return False
        return True

    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.
        
class VenueConnectionPanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.Centre()
        self.titleText = wx.StaticText(self, -1, "Recovery")
        self.titleLine = wx.StaticLine(self, -1)
        self.shutdownMediaButton = wx.CheckBox(self, wx.NewId(), "  Shut down media tools on removal from Venue")
        self.reconnectButton = wx.CheckBox(self, wx.NewId(), "  Reconnect to venue automatically")
        self.maxText = wx.StaticText(self, -1, "Recovery attempts ")
        self.maxReconnect = wx.lib.intctrl.IntCtrl(self, -1, 3, size = wx.Size(30, -1))
        self.timeoutText = wx.StaticText(self, -1, "Recovery timeout (seconds) ")
        self.timeout = wx.lib.intctrl.IntCtrl(self, -1, 10, size = wx.Size(30, -1)) 
        shutdownMedia = int(preferences.GetPreference(Preferences.SHUTDOWN_MEDIA))
        self.shutdownMediaButton.SetValue(shutdownMedia)
        reconnect = int(preferences.GetPreference(Preferences.RECONNECT))
        self.reconnectButton.SetValue(reconnect)
        self.maxReconnect.SetValue(int(preferences.GetPreference(Preferences.MAX_RECONNECT)))
        self.timeout.SetValue(int(preferences.GetPreference(Preferences.RECONNECT_TIMEOUT)))
        self.EnableCtrls(reconnect)
           
        self.__Layout()

        wx.EVT_CHECKBOX(self, self.reconnectButton.GetId(), self.ReconnectCB)

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
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.titleText, 0, wx.ALL, 5)#,0,wx.EXPAND|wx.ALL,10)
        sizer2.Add(self.titleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.shutdownMediaButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.reconnectButton, 0, wx.ALL|wx.EXPAND, 10)

        gridSizer = wx.GridSizer(0, 2, 5, 5)
        gridSizer.Add(self.maxText, 0, wx.LEFT, 30)
        gridSizer.Add(self.maxReconnect)
        gridSizer.Add(self.timeoutText, 0, wx.LEFT, 30)
        gridSizer.Add(self.timeout)
        sizer.Add(gridSizer)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

class EditBridgeRegistryPanel(wx.Dialog):
    def __init__(self, parent, id, preferences):
        wx.Dialog.__init__(self, parent, id, 'Edit Bridge Registry URLs',
                                size = (560, 250),
                                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.parent = parent
        self.preferences = preferences
        self.maxRegistries = self.preferences.GetMaxBridgeRegistries()
        self.permanentRegistries = self.preferences.GetPermanentRegistries()

        if self.permanentRegistries > 0:
            self.fixedRegistryText = wx.StaticText(self, -1, "Fixed: ",
                             size = wx.Size(60, -1),
                             style=wx.ALIGN_RIGHT)
            self.fixedRegistryCtrl = wx.TextCtrl(self, -1,
                             size = wx.Size(480, 21*self.permanentRegistries),
                             style = wx.TE_RICH | wx.TE_MULTILINE | wx.TE_READONLY)
            self.fixedRegistryCtrl.SetBackgroundColour(self.GetBackgroundColour())
        self.editableRegistryText = wx.StaticText(self, -1, "Editable: ",
                             size = wx.Size(60, -1),
                             style=wx.ALIGN_RIGHT)
        self.editableRegistryCtrl = wx.TextCtrl(self, -1,
                       size = wx.Size(480, 19*(self.maxRegistries-self.permanentRegistries)),
                       style = wx.TE_RICH | wx.TE_MULTILINE)

        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.okButton = wx.Button(self, wx.ID_OK, "OK")
                                
        wx.EVT_BUTTON(self, self.cancelButton.GetId(), self.OnCancel)
        wx.EVT_BUTTON(self, self.okButton.GetId(), self.OnOK)
        wx.EVT_CHAR(self.editableRegistryCtrl, self.OnChar)

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
        self.foundNone = False
        for lineNo in range(0, self.editableRegistryCtrl.GetNumberOfLines()):
            if self.editableRegistryCtrl.GetLineText(lineNo).startswith("None"):
                self.editableRegistryCtrl.SetInsertionPoint(
                      self.editableRegistryCtrl.XYToPosition(
                      self.editableRegistryCtrl.GetLineLength(lineNo), lineNo))
                self.foundNone = True
                break
        if not self.foundNone:
            self.editableRegistryCtrl.SetInsertionPoint(
                                self.editableRegistryCtrl.XYToPosition(
                                self.editableRegistryCtrl.GetLineLength(0), 0))
        wx.CallAfter(self.editableRegistryCtrl.SetFocus)

        self.__Layout()
        

    def OnCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

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
        self.EndModal(wx.ID_OK)


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

        if k == wx.WXK_BACK:
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
        elif k == wx.WXK_RETURN:
            # Don't process if we'd be adding and extra entry beyond the max
            # (maybe the test itself isn't needed if we've otherwise caught
            #  all possibilites of deleting any entries)
            if self.editableRegistryCtrl.GetNumberOfLines() >= maxEditableEntries:
                pass
            else:
                event.Skip()
        elif k == wx.WXK_DELETE:
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
        gridsizer = wx.FlexGridSizer(0, 2, 5, 5)
        if self.permanentRegistries > 0:
            gridsizer.Add(self.fixedRegistryText, 0, wx.EXPAND | wx.ALL, 0)
            gridsizer.Add(self.fixedRegistryCtrl, 0, wx.EXPAND | wx.ALL, 0)
        gridsizer.Add(self.editableRegistryText, 0, wx.EXPAND | wx.ALL, 0)
        gridsizer.Add(self.editableRegistryCtrl, 0, wx.EXPAND | wx.ALL, 0)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 10)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 10)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(wx.Size(-1,10))
        sizer.Add(gridsizer, 0, wx.ALIGN_CENTER)
        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        

class NetworkPanel(wx.Panel):
    
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.preferences = preferences
        self.Centre()
        
        # multicast detection and monitoring
        self.titleText = wx.StaticText(self, -1, "Multicast detection and monitoring")
        self.titleLine = wx.StaticLine(self, -1)
        self.keyMap = {}
        self.selected = None
        
        self.beaconButton = wx.CheckBox(self, wx.NewId(), "  Run integrated multicast beacon client ")
        self.beaconButton.SetValue(int(preferences.GetPreference(Preferences.BEACON)))
        
        self.multicastDetectionLabel = wx.StaticText(self,-1,'Detect multicast connectivity using the following multicast group')
        self.multicastDetectionHostLabel = wx.StaticText(self,-1,'Host')
        self.multicastDetectionHost = wx.TextCtrl(self,-1,
                                        preferences.GetPreference(Preferences.MULTICAST_DETECT_HOST))
        self.multicastDetectionPortLabel = wx.StaticText(self,-1,'Port')
        self.multicastDetectionPort = wx.TextCtrl(self,-1,
                                        str(preferences.GetPreference(Preferences.MULTICAST_DETECT_PORT)))
        
        # proxy configuration                  
        self.proxyTitleText = wx.StaticText(self, -1, "Proxy server configuration")
        self.proxyTitleLine = wx.StaticLine(self, -1)
        self.proxyButton = wx.CheckBox(self,-1,"Use an HTTP proxy server for network connections")
        proxyEnabled = int(preferences.GetPreference(Preferences.PROXY_ENABLED))
        self.proxyButton.SetValue(proxyEnabled)
        self.hostText = wx.StaticText(self, -1, "Host:")
        self.hostCtrl = wx.TextCtrl(self, -1, "")
        self.portText = wx.StaticText(self, -1, "Port:")
        self.portCtrl = wx.TextCtrl(self, -1, "")
       
        
        self.usernameText = wx.StaticText(self, -1, "Username:")
        self.usernameCtrl = wx.TextCtrl(self, -1, "")
        self.passwordText = wx.StaticText(self, -1, "Password:")
        
        # Intel OS X has issues with the password control, but we aren't
        # granular enough to know if this is an Intel chip or not.
        # This might be fixed in the latest wxPython, but AG won't
        # run with it because of deprecated functionality
        if IsOSX() and wx.VERSION <= (2,8,0,0):
            self.passwordCtrl = wx.TextCtrl(self, -1, "")
        else:
            self.passwordCtrl = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
            
        self.authProxyButton = wx.CheckBox(self, wx.NewId(), "Authenticate with the following user information")
        authProxyEnabled = int(preferences.GetPreference(Preferences.PROXY_AUTH_ENABLED))
        self.authProxyButton.SetValue(authProxyEnabled)

        self.SetProxyHost(preferences.GetPreference(Preferences.PROXY_HOST))
        self.SetProxyPort(preferences.GetPreference(Preferences.PROXY_PORT))
        self.SetProxyUsername(preferences.GetPreference(Preferences.PROXY_USERNAME))
        self.SetProxyPassword(preferences.GetProxyPassword())
        
        wx.EVT_CHECKBOX(self,self.proxyButton.GetId(),self.OnEnableProxy)
        wx.EVT_CHECKBOX(self,self.authProxyButton.GetId(),self.OnAuthProxy)
        
        self.EnableProxy(proxyEnabled)
        self.EnableAuthProxy(proxyEnabled and authProxyEnabled)
                    
        self.__Layout()
    
    def __Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # multicast
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.titleText, 0, wx.ALL, 5)
        sizer2.Add(self.titleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.beaconButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.multicastDetectionLabel, 0, wx.ALL|wx.EXPAND,10)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.multicastDetectionHostLabel, 0, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.multicastDetectionHost, 1, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.multicastDetectionPortLabel, 0, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.multicastDetectionPort, 0, wx.ALL|wx.EXPAND,10)
        sizer.Add(sizer3,0,wx.EXPAND)
        
        # proxy server configuration
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.proxyTitleText, 0, wx.ALL, 5)
        sizer2.Add(self.proxyTitleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.proxyButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.hostText, 0, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.hostCtrl, 1, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.portText, 0, wx.ALL|wx.EXPAND,10)
        sizer3.Add(self.portCtrl, 0, wx.ALL|wx.EXPAND,10)
        sizer.Add(sizer3,0,wx.EXPAND)
                
        sizer.Add(self.authProxyButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add(self.usernameText, 0, wx.ALL|wx.EXPAND,10)
        sizer4.Add(self.usernameCtrl, 1, wx.ALL|wx.EXPAND,10)
        sizer4.Add(self.passwordText, 0, wx.ALL|wx.EXPAND,10)
        sizer4.Add(self.passwordCtrl, 1, wx.ALL|wx.EXPAND,10)
        sizer.Add(sizer4,0,wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
        self.Layout()
        
    
        
    def EnableProxy(self,enableFlag):
        # this method just makes the proxy controls clickable or not
        self.hostText.Enable(enableFlag)
        self.hostCtrl.Enable(enableFlag)
        self.portText.Enable(enableFlag)
        self.portCtrl.Enable(enableFlag)
        self.authProxyButton.Enable(enableFlag)
        self.EnableAuthProxy(enableFlag)
        
    def EnableAuthProxy(self,enableFlag):
        # this method just makes the auth proxy controls clickable or not
        self.usernameCtrl.Enable(enableFlag)
        self.usernameText.Enable(enableFlag)
        self.passwordCtrl.Enable(enableFlag)
        self.passwordText.Enable(enableFlag)
           
    def OnEnableProxy(self,event):
        self.EnableProxy(event.IsChecked())
        
    def OnAuthProxy(self,event):
        self.EnableAuthProxy(event.IsChecked())

    def GetBeacon(self):
        if self.beaconButton.IsChecked():
            return 1
        else:
            return 0
          
    def GetMulticastDetectionHost(self):
        return self.multicastDetectionHost.GetValue()
        
    def GetMulticastDetectionPort(self):
        return int(self.multicastDetectionPort.GetValue())
        
    def SetProxyHost(self,host):
        self.hostCtrl.SetValue(host)
        
    def SetProxyPort(self,port):
        self.portCtrl.SetValue(str(port))
        
    def GetProxyHost(self):
        return self.hostCtrl.GetValue()
        
    def GetProxyPort(self):
        returnValue = 0;
        
        port = self.portCtrl.GetValue()
        
        try:
            returnValue = int(port)
        except Exception, e:
            returnValue = 0;
                    
        return returnValue
            
    def SetProxyUsername(self,username):
        self.usernameCtrl.SetValue(username)
        
    def SetProxyPassword(self,password):
        self.passwordCtrl.SetValue(password)
    
    def GetProxyUsername(self):
        return self.usernameCtrl.GetValue()
    
    def GetProxyPassword(self):
        return str(self.passwordCtrl.GetValue())
            
    def GetProxyEnabled(self):
        if self.proxyButton.IsChecked():
            return 1
        else:
            return 0
                
    def GetAuthProxyEnabled(self):
        if self.authProxyButton.IsChecked():
            return 1
        else:
            return 0
                


class BridgingPanel(wx.Panel):
    
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.preferences = preferences
        self.Centre()
        self.bridgingTitleText = wx.StaticText(self, -1, "Bridging")
        self.bridgingTitleLine = wx.StaticLine(self, -1)
        self.registriesTitleText = wx.StaticText(self, -1, "Bridge Registries")
        self.registriesTitleLine = wx.StaticLine(self, -1)
        self.bridgesTitleText = wx.StaticText(self, -1, "Bridges")
        self.bridgesTitleLine = wx.StaticLine(self, -1)
        self.multicastButton = wx.CheckBox(self, wx.NewId(), "  Always use unicast bridges instead of multicast ")
        self.keyMap = {}
        self.selected = None
        self.editBridgeRegistryPanel = None
        self.bridgePingDelay = self.preferences.GetPreference(Preferences.BRIDGE_PING_UPDATE_DELAY)
        self.orderBridgesByPing = int(self.preferences.GetPreference(Preferences.ORDER_BRIDGES_BY_PING))
        self.registries = self.preferences.GetPreference(Preferences.BRIDGE_REGISTRY).split('|')
        bridgeDict = preferences.GetBridges()
        self.bridges = bridgeDict.values()
        self.regSelected = None
        
        # make a copy of the bridges, since we modify them in place
        import copy
        self.bridges = map( lambda x: copy.copy(x), self.bridges)
        self.bridges.sort(lambda x,y: BridgeDescription.sort(x, y, self.orderBridgesByPing))

        self.multicastButton.SetValue(not int(preferences.GetPreference(Preferences.MULTICAST)))

        self.listHelpText = wx.StaticText(self,-1,'Right-click a bridge below to enable or disable it')
        
        self.orderBridgesByPingButton = wx.CheckBox(self, wx.NewId(), "  Measure closeness to bridges and use the closest bridge")
        self.bridgePingTimeText = wx.StaticText(self, -1, "How often to measure bridge closeness (seconds):  ")
        self.bridgePingTimeBox = wx.TextCtrl(self, -1, str(self.bridgePingDelay), size = wx.Size(40, -1));
        self.orderBridgesByPingButton.SetValue(int(self.orderBridgesByPing))

        self.list = wx.ListCtrl(self, wx.NewId(),style=wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.list.InsertColumn(0, "Bridge")
        self.list.InsertColumn(1, "Host")
        self.list.InsertColumn(2, "Port")
        self.list.InsertColumn(3, "Type")
        self.list.InsertColumn(4, "Status")
        self.list.InsertColumn(5, "Ping Time (s)")
        self.list.InsertColumn(6, "Port range")
              
        self.list.SetColumnWidth(0, 90)
        self.list.SetColumnWidth(1, 60)
        self.list.SetColumnWidth(2, 50)
        self.list.SetColumnWidth(3, 80)
        self.list.SetColumnWidth(4, 60)
        self.list.SetColumnWidth(5, 90)
        self.list.SetColumnWidth(6, 90)
        self.__InitList()
        
        self.upButton = wx.Button(self, wx.NewId(), 'Move Up')
        self.downButton = wx.Button(self, wx.NewId(), 'Move Down')
        self.refreshButton = wx.Button(self, -1, 'Find Additional Bridges')
        self.updatePingButton = wx.Button(self, -1, 'Update Ping Times')
        self.orderByPingButton = wx.Button(self, -1, 'Order Bridges by Ping Time')
        self.purgeCacheButton = wx.Button(self, -1, 'Purge Bridge Cache')
        self.registryList = wx.ListCtrl(self, wx.NewId(), style = wx.LC_LIST | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        self.addRegistryButton = wx.Button(self, wx.NewId(), 'Add')
        self.removeRegistryButton = wx.Button(self, wx.NewId(), 'Remove')
        self.editRegistryButton = wx.Button(self, wx.NewId(), 'Edit')
        
        for index in range(len(self.registries)):
            self.registryList.InsertStringItem(index, self.registries[index])
        
        if self.orderBridgesByPing == 1:
            self.updatePingButton.Enable(0)
            self.orderByPingButton.Enable(0)
            self.upButton.Enable(0)
            self.downButton.Enable(0)
        
        wx.EVT_RIGHT_DOWN(self.list, self.OnRightDown)
        wx.EVT_RIGHT_UP(self.list, self.OnRightClick)
        wx.EVT_LIST_ITEM_SELECTED(self, self.list.GetId(), self.OnSelect)
        wx.EVT_BUTTON(self, self.refreshButton.GetId(), self.OnRefresh)
        wx.EVT_BUTTON(self, self.updatePingButton.GetId(), self.OnUpdatePing)
        wx.EVT_BUTTON(self, self.orderByPingButton.GetId(), self.OnOrderByPing)
        wx.EVT_CHECKBOX(self, self.orderBridgesByPingButton.GetId(), self.OnChangeOrderByPing)
        wx.EVT_BUTTON(self, self.upButton.GetId(), self.MoveUp)
        wx.EVT_BUTTON(self, self.downButton.GetId(), self.MoveDown)
        wx.EVT_LIST_ITEM_SELECTED(self, self.registryList.GetId(), self.OnSelectReg)
        wx.EVT_LIST_ITEM_DESELECTED(self, self.registryList.GetId(), self.OnDeselectReg)
        wx.EVT_BUTTON(self, self.editRegistryButton.GetId(), self.OnEditReg)
        wx.EVT_BUTTON(self, self.addRegistryButton.GetId(), self.OnAddReg)
        wx.EVT_BUTTON(self, self.removeRegistryButton.GetId(), self.OnRemoveReg)
        wx.EVT_BUTTON(self, self.purgeCacheButton.GetId(), self.OnPurgeCache)
            
        self.__Layout()
    
    def __InitList(self):

        # Clear the list
        self.list.DeleteAllItems()
        
        # Populate the list
        for index in range(len(self.bridges)):
            self.list.InsertStringItem(index, self.bridges[index].name)
            self.SetBridgeListRow(index)
          
    def __Layout(self):
    
        # bridging config
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.bridgingTitleText, 0, wx.ALL, 5)
        sizer2.Add(self.bridgingTitleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.multicastButton, 0, wx.ALL|wx.EXPAND, 10)
        

        # bridge registries
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.registriesTitleText, 0, wx.ALL, 5)
        sizer2.Add(self.registriesTitleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        registrySizer = wx.BoxSizer(wx.HORIZONTAL)
        registrySizer.Add(self.registryList, 1, wx.EXPAND, 0)
        registryButtonSizer = wx.BoxSizer(wx.VERTICAL)
        registryButtonSizer.Add(self.addRegistryButton, 0, 0, 0)
        registryButtonSizer.Add(self.removeRegistryButton, 0, wx.TOP, 10)
        registryButtonSizer.Add(self.editRegistryButton, 0, wx.TOP, 10)
        registrySizer.Add(registryButtonSizer, 0, wx.LEFT|wx.EXPAND, 10)
        sizer.Add(registrySizer, 0, wx.ALL|wx.EXPAND, 10)
        
        # bridges
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.bridgesTitleText, 0, wx.ALL, 5)
        sizer2.Add(self.bridgesTitleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.orderBridgesByPingButton, 0, wx.ALL|wx.EXPAND, 10)
        sizerBridgePingTime = wx.BoxSizer(wx.HORIZONTAL)
        sizerBridgePingTime.Add(self.bridgePingTimeText, 0, wx.RIGHT, 0)
        sizerBridgePingTime.Add(self.bridgePingTimeBox, 0, wx.LEFT, 0)
        sizer.Add(sizerBridgePingTime, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.listHelpText, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        bridgeListSizer = wx.BoxSizer(wx.HORIZONTAL)
        bridgeListSizer.Add(self.list, 1, wx.ALL|wx.EXPAND, 0)
        updownSizer = wx.BoxSizer(wx.VERTICAL)
        updownSizer.Add(self.upButton, 0, wx.LEFT|wx.EXPAND, 10)
        updownSizer.Add(self.downButton, 0, wx.LEFT|wx.EXPAND, 10)
        bridgeListSizer.Add(updownSizer,0,wx.LEFT|wx.ALIGN_CENTER_VERTICAL,10)
        sizer.Add(bridgeListSizer, 1, wx.ALL|wx.EXPAND, 10)
        sizerButtons = wx.BoxSizer(wx.HORIZONTAL)
        sizerButtons.Add(self.refreshButton, 0, wx.LEFT, 10)
        sizerButtons.Add(self.updatePingButton, 0, wx.LEFT, 10)
        sizerButtons.Add(self.orderByPingButton, 0, wx.LEFT, 10)
        sizerButtons.Add(self.purgeCacheButton, 0, wx.LEFT, 10)
        sizer.Add(sizerButtons, 0, wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
        self.Layout()


    def OnSelectReg(self, event):
        self.regSelected = event.GetIndex()
        
    def OnDeselectReg(self, event):
        if self.regSelected == event.GetIndex():
            self.regSelected = None
            
    def OnEditReg(self, event):
        if self.regSelected != None:
            d = TextDialog(self, "Enter the new URL", "Registry URL", text = self.registries[self.regSelected])
            if d.ShowModal() == wx.ID_OK:
                newreg = d.GetChars()
                d.Destroy()
                self.registries[self.regSelected] = newreg
                self.registryList.SetStringItem(self.regSelected, 0, newreg)
    
    def OnRemoveReg(self, event):
        if self.regSelected != None:
            d = wx.MessageDialog(self, "Are you sure that you want to remove this registry?", "Confirm", wx.YES_NO)
            if d.ShowModal() == wx.ID_YES:
                self.registries.pop(self.regSelected)
                self.registryList.DeleteItem(self.regSelected)
    
    def OnAddReg(self, event):
        d = TextDialog(self, "Enter the new URL", "Registry URL")
        if d.ShowModal() == wx.ID_OK:
            newreg = d.GetChars()
            d.Destroy()
            self.registries.append(newreg)
            self.registryList.InsertStringItem(len(self.registries) - 1, newreg)
    
    def OnSelect(self, event):
        self.selected = event.m_itemIndex
        
    def OnChangeOrderByPing(self, event):
        if self.orderBridgesByPingButton.IsChecked():
            self.bridges.sort(lambda x,y: BridgeDescription.sort(x, y, 1))
            self.orderBridgesByPing = 1
            self.updatePingButton.Enable(0)
            self.orderByPingButton.Enable(0)
            self.upButton.Enable(0)
            self.downButton.Enable(0)
        else:
            self.bridges.sort(lambda x,y: BridgeDescription.sort(x, y, 0))
            self.orderBridgesByPing = 0
            self.updatePingButton.Enable(1)
            self.orderByPingButton.Enable(1)
            self.upButton.Enable(1)
            self.downButton.Enable(1)
        self.__InitList()
        
    def OnOrderByPing(self, event):
        for b in self.bridges:
            b.userRank = b.rank
        self.bridges.sort(lambda x,y: BridgeDescription.sort(x, y, self.orderBridgesByPing))
        self.__InitList()
        
    def OnUpdatePing(self, event):
        venueClient = self.preferences.venueClient
        registryClient = venueClient.registryClient
        if registryClient != None:
            for b in self.bridges:
                registryClient.PingBridge(b)
        self.__InitList()
        
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
            self.moveupId = wx.NewId()
            self.movedownId = wx.NewId()
            wx.EVT_MENU(self, self.enableId, self.Enable)
            wx.EVT_MENU(self, self.moveupId, self.MoveUp)
            wx.EVT_MENU(self, self.movedownId, self.MoveDown)
            
        # make a menu
        self.menu = wx.Menu()
        self.menu.AppendCheckItem(self.enableId, "Enabled")
        if self.orderBridgesByPing == 0:
            self.menu.AppendSeparator()
            self.menu.Append(self.moveupId, "Move Up")
            self.menu.Append(self.movedownId, "Move Down")

        # Check the actual item to see if it is enabled or not
        selectedItem = self.bridges[self.selected]
        if selectedItem.status == STATUS_ENABLED:
            self.menu.Check(self.enableId, 1)
        else: 
            self.menu.Check(self.enableId, 0)
        
        # Disable moving up for top item and down for bottom item
        if self.selected == 0:
            self.menu.Enable(self.moveupId, 0)
        if self.selected == (len(self.bridges) - 1):
            self.menu.Enable(self.movedownId, 0)

        self.list.PopupMenu(self.menu, wx.Point(self.x, self.y))
        self.menu.Destroy()
    
    def OnPurgeCache(self, event):
        self.preferences.SetBridges({})
        self.OnRefresh(event)

    def OnRefresh(self,event):
        wx.BeginBusyCursor()
    
        try:
            venueClient = self.preferences.venueClient
        
            # Force rescanning of the bridges
            venueClient.SetupBridgePrefs()
            self.bridges = venueClient.LoadBridges()
            self.bridges.sort(lambda x,y: BridgeDescription.sort(x, y, self.orderBridgesByPing))

            # Refresh the bridge list in the UI
            self.__InitList()
        except:
            log.exception("Exception refreshing bridge list")
            
        wx.EndBusyCursor()

    def OnEdit(self, event):
        if self.editBridgeRegistryPanel:
            # Edit panel already open
            return

        # This _should_ be redundant, since no Edit button should
        # be available when the condition is True.
        if self.permanentRegistries >= self.maxRegistries:
            MessageDialog(None, "There are no editable entries")
            return


        self.editBridgeRegistryPanel = EditBridgeRegistryPanel(self,
                                         wx.NewId(), self.preferences)

        if self.editBridgeRegistryPanel.ShowModal() == wx.ID_OK:
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
            selectedItem.status = STATUS_ENABLED
        else:
            selectedItem.status = STATUS_DISABLED

        self.list.SetStringItem(self.selected, 4, selectedItem.status)
    
    def SetBridgeListRow(self, index):
        self.list.SetStringItem(index, 0, self.bridges[index].name)
        self.list.SetStringItem(index, 1, self.bridges[index].host)
        self.list.SetStringItem(index, 2, str(self.bridges[index].port))
        self.list.SetStringItem(index, 3, self.bridges[index].serverType)
        self.list.SetStringItem(index, 4, self.bridges[index].status)
        if self.bridges[index].rank == BridgeDescription.UNREACHABLE:
            self.list.SetStringItem(index, 5, "Unreachable")
        else:
            self.list.SetStringItem(index, 5, str(self.bridges[index].rank))
        self.list.SetStringItem(index, 6, '%d-%d' % (self.bridges[index].portMin,self.bridges[index].portMax))
        
    def MoveUp(self, event):
        if self.selected != None and self.selected > 0:
            aboveBy1Rank = 0;
            aboveRank = self.bridges[self.selected - 1].userRank
            if self.selected > 1:
                aboveBy1Rank = self.bridges[self.selected - 2].userRank
            self.bridges[self.selected].userRank = float(aboveBy1Rank + ((aboveRank - aboveBy1Rank) / 2))
            temp = self.bridges[self.selected - 1]
            self.bridges[self.selected - 1] = self.bridges[self.selected]
            self.bridges[self.selected] = temp
            self.SetBridgeListRow(self.selected - 1)
            self.SetBridgeListRow(self.selected)
            self.selected = self.selected - 1
            self.list.Select(self.selected)
            self.list.ScrollList(0, -10)
    
    def MoveDown(self, event):
        if self.selected != None and self.selected < (len(self.bridges) - 1):
            selectedItem = self.bridges[self.selected]
            belowBy1Rank = 0;
            belowRank = self.bridges[self.selected + 1].userRank
            if self.selected < (len(self.bridges) - 2):
                belowBy1Rank = self.bridges[self.selected + 2].userRank
            selectedItem.userRank = float(belowRank + ((belowBy1Rank - belowRank) / 2))
            temp = self.bridges[self.selected + 1]
            self.bridges[self.selected + 1] = self.bridges[self.selected]
            self.bridges[self.selected] = temp
            self.SetBridgeListRow(self.selected + 1)
            self.SetBridgeListRow(self.selected)
            self.selected = self.selected + 1
            self.list.Select(self.selected)
            self.list.ScrollList(0, 10)

    def GetBridges(self):
        retBridges = {}
        for b in self.bridges:
            retBridges[b.GetKey()] = b
        return retBridges
                                    
    def GetMulticast(self):
        if self.multicastButton.IsChecked():
            return 0
        else:
            return 1

    def GetRegistry(self, regId):
        return "|".join(self.registries)
    
    def GetOrderBridgesByPing(self):
        if self.orderBridgesByPingButton.IsChecked():
            return 1
        else:
            return 0
        
    def GetBridgePingDelay(self):
        try:
            return int(self.bridgePingDelayBox.GetText())
        except:
            log.debug("Bridge Delay was not an int")
            return self.bridgePingDelay




class NavigationPanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.Centre()
        self.titleText = wx.StaticText(self, -1, "Navigation View")
        self.titleLine = wx.StaticLine(self, -1)
        self.exitsButton = wx.RadioButton(self, wx.NewId(), "  Show exits from the current venue ")
        self.myVenuesButton = wx.RadioButton(self, wx.NewId(), "  Show my saved venues")
        self.allVenuesButton = wx.RadioButton(self, wx.NewId(), "  Show all venues on the current server")
        self.venueCacheTitleText = wx.StaticText(self, -1, "Venue Cache")
        self.venueCacheTitleLine = wx.StaticLine(self, -1)
        self.venueServerUrlText = wx.TextCtrl(self,-1,style=wx.TE_MULTILINE)
        self.venueCacheRefreshButton = wx.Button(self,-1,"Refresh")

        value = preferences.GetPreference(Preferences.DISPLAY_MODE)
        if value == Preferences.EXITS:
            self.exitsButton.SetValue(1)
        elif value == Preferences.MY_VENUES:
            self.myVenuesButton.SetValue(1)
        elif value == Preferences.ALL_VENUES:
            self.allVenuesButton.SetValue(1)

        venueServerUrls = preferences.GetPreference(Preferences.VENUESERVER_URLS)
        venueServerUrls = venueServerUrls.split('|')
        for url in venueServerUrls:
            self.venueServerUrlText.AppendText(url+"\n")
        
        wx.EVT_BUTTON(self,self.venueCacheRefreshButton.GetId(), self.OnRefresh)
        self.preferences = preferences
        self.__Layout()
        
    def OnRefresh(self,event):
        val = str(self.venueServerUrlText.GetValue())
        urls = val.split('\n')
        for u in urls:
            u = u.strip()
            if u and u not in self.preferences.venueClient.venueCache.venueServers:
                self.preferences.venueClient.venueCache.venueServers.append(str(u))
        self.preferences.venueClient.venueCache.Update()
        self.preferences.venueClient.venueCache.Store()
         
    def GetDisplayMode(self):
        if self.exitsButton.GetValue():
            return Preferences.EXITS
        elif self.myVenuesButton.GetValue():
            return Preferences.MY_VENUES
        elif self.allVenuesButton.GetValue():
            return Preferences.ALL_VENUES
          
    def __Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.titleText, 0, wx.ALL, 5)
        sizer2.Add(self.titleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.exitsButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.myVenuesButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.allVenuesButton, 0, wx.ALL|wx.EXPAND, 10)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.venueCacheTitleText, 0, wx.ALL, 5)
        sizer2.Add(self.venueCacheTitleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.venueServerUrlText, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.venueCacheRefreshButton, 0)
               
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def GetVenueServers(self):
        urls = (self.venueServerUrlText.GetValue())
        urls = urls.split('\n')
        ret = []
        for u in urls:
            if not u:
                continue
            ret.append(u)
        ret = '|'.join(ret)
        return ret
            
        
        
class JabberPanel(wx.Panel):
    def __init__(self, parent, id, preferences):
        wx.Panel.__init__(self, parent, id)
        self.Centre()
        self.titleText = wx.StaticText(self, -1, "Jabber Preferences")
        self.titleLine = wx.StaticLine(self, -1)

        self.useDynamicJabberAccount = wx.RadioButton(self, wx.NewId(), "Use dynamic Jabber account")
        self.useSpecificJabberAccount = wx.RadioButton(self, wx.NewId(), "Use specific Jabber account")
        self.jabberUsernameText = wx.StaticText(self, -1, "Account")
        self.jabberUsernameCtrl = wx.TextCtrl(self, -1, preferences.GetJabberUsername())
        self.jabberPasswordText = wx.StaticText(self, -1, "Password")
        try:
            p = preferences.GetJabberPassword()
        except:
            import traceback
            traceback.print_exc()
            p = ""
        self.jabberPasswordCtrl = wx.TextCtrl(self, -1, p)    
        
        # default to using dynamic Jabber account
        useJabberAccount = preferences.UseJabberAccount()
        self.useDynamicJabberAccount.SetValue( not useJabberAccount)
        self.useSpecificJabberAccount.SetValue(bool(useJabberAccount))
        self.EnableJabberAccountInfo(bool(useJabberAccount))

        wx.EVT_RADIOBUTTON(self,self.useSpecificJabberAccount.GetId(),self.OnUseJabberAccount)
                                
        self.__Layout()
         
    def GetJabberUsername(self):
        return self.jabberUsernameCtrl.GetValue()
    
    def GetJabberPassword(self):
        return self.jabberPasswordCtrl.GetValue()
    
    def UseJabberAccount(self):
        return self.useSpecificJabberAccount.GetValue()
    
    def OnUseJabberAccount(self,event):
        self.EnableJabberAccountInfo(event.IsChecked())   
            
    def EnableJabberAccountInfo(self,enabledFlag):
        self.jabberUsernameText.Enable(enabledFlag)
        self.jabberUsernameCtrl.Enable(enabledFlag)
        self.jabberPasswordText.Enable(enabledFlag)
        self.jabberPasswordCtrl.Enable(enabledFlag)

    def __Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.titleText, 0, wx.ALL, 5)
        sizer2.Add(self.titleLine, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
        sizer.Add(self.useDynamicJabberAccount, 0, wx.ALL|wx.EXPAND, 10)
        sizer.Add(self.useSpecificJabberAccount, 0, wx.ALL|wx.EXPAND, 10)
        sizer2 = wx.GridSizer(rows=2,cols=2)
        sizer2.Add(self.jabberUsernameText, 0, wx.ALL, 5)
        sizer2.Add(self.jabberUsernameCtrl, 1, wx.EXPAND, 5)
        sizer2.Add(self.jabberPasswordText, 0, wx.ALL, 5)
        sizer2.Add(self.jabberPasswordCtrl, 1, wx.EXPAND, 5)
        sizer.Add(sizer2, 0, wx.EXPAND)
               
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
if __name__ == "__main__":
    from AccessGrid.Toolkit import WXGUIApplication
    
    pp = wx.PySimpleApp()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # Try to initialize
    app.Initialize("Preferences")
    
    p = Preferences()
    pDialog = PreferencesDialog(None, -1,
                                'Preferences', p)
    pDialog.ShowModal()
    p = pDialog.GetPreferences()
    p.StorePreferences()
    
