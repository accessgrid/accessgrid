#-----------------------------------------------------------------------------
# Name:        NodeManagementUIClasses.py
# Purpose:
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: NodeManagementUIClasses.py,v 1.118 2007/10/04 17:36:56 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NodeManagementUIClasses.py,v 1.118 2007/10/04 17:36:56 turam Exp $"
__docformat__ = "restructuredtext en"
import sys
import threading
import re
import socket

import wx
from wx.gizmos import TreeListCtrl

# AG imports
from AccessGrid import Log
from AccessGrid import icons
from AccessGrid import Platform
from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import Client
from AccessGrid.UIUtilities import AboutDialog
from AccessGrid.AGParameter import ValueParameter, RangeParameter
from AccessGrid.AGParameter import OptionSetParameter
from AccessGrid.Descriptions import AGServiceManagerDescription, AGServiceDescription
from AccessGrid.Descriptions import NodeConfigDescription
from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW
from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW
from AccessGrid.interfaces.AGService_client import AGServiceIW
from AccessGrid import Version
from AccessGrid.Preferences import Preferences
from AccessGrid.Utilities import BuildServiceUrl

from AccessGrid import ServiceDiscovery

log = Log.GetLogger(Log.NodeManagementUIClasses)
Log.SetDefaultLevel(Log.NodeManagementUIClasses, Log.WARN)

###
### MENU DEFS
###

ID_FILE_EXIT  = 100
ID_FILE_LOAD_CONFIG = 101
ID_FILE_STORE_CONFIG = 102

ID_FILE_ATTACH = 800
ID_NODE_LEASH = 801
ID_NODE_BRIDGE = 802

ID_HOST_ADD = 300
ID_HOST_REMOVE = 301

ID_SERVICE_ADD_SERVICE = 400
ID_SERVICE_CONFIGURE = 402
ID_SERVICE_REMOVE = 403
ID_SERVICE_ENABLE = 404
ID_SERVICE_ENABLE_ONE = 405
ID_SERVICE_DISABLE = 406
ID_SERVICE_DISABLE_ONE = 407

ID_HELP_ABOUT = 701

class ServiceResolveFailed(Exception):  pass
class ServiceResolveTimeout(Exception): pass
class UnresolvableService(Exception):   pass




class ServiceChoiceDialog(wx.Dialog):
    def __init__(self, parent, id, title, choices, serviceType, text, size=wx.Size(450,130) ):
    
    
        wx.Dialog.__init__(self, parent, id, title, style =
                          wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
                          size=size)
                          
        self.serviceType = serviceType
              
        # Set up sizers
        sizer1 = wx.BoxSizer(wx.VERTICAL)
       
        self.text = wx.StaticText(self,-1,text)
        sizer1.Add( self.text,0,border=5,flag=wx.ALL)

        self.comboBoxCtrl = wx.ComboBox(self,-1, choices=choices)
        sizer1.Add( self.comboBoxCtrl, 0, flag=wx.ALL|wx.EXPAND,border=5)
        
        # Create ok/cancel buttons
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button( self, wx.ID_OK, "OK")
        cancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wx.ALL, 10)
        sizer3.Add(cancelButton, 0, wx.ALL, 10)
        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)
        
        self.SetSizer( sizer1 )
        
        x,y = wx.GetMousePosition()
        w,h = self.GetSize()
        self.Move( (x-w/2,y-h/2) )
        wx.EVT_TEXT_ENTER(self, self.comboBoxCtrl.GetId(), self.OnOK)

        self.exists = threading.Event()
        self.exists.set()
        
        self.browser = ServiceDiscovery.Browser(serviceType,self.BrowseCallback)
        self.browser.Start()
        
        self.hostname = SystemConfig.instance().GetHostname()

        self.Fit()

    def OnOK(self,event):
        self.EndModal(wx.ID_OK)
        

    def BrowseCallback(self,op,serviceName,url=None):
        if self.exists.isSet() and op == ServiceDiscovery.Browser.ADD:
            wx.CallAfter(self.AddItem,serviceName,url)
        
    def AddItem(self,name,url):
        if self.comboBoxCtrl.FindString(url) == wx.NOT_FOUND:
            self.comboBoxCtrl.Append(url)
            
            val = self.comboBoxCtrl.GetValue()
            # if the combobox doesn't have a value set, use this one
            if not val:
                self.comboBoxCtrl.SetValue(url)
            # if the found service is local, use it instead of existing one
            elif (val.find(self.hostname) == -1 and url.find(self.hostname) >= 0):
                self.comboBoxCtrl.SetValue(url)

    def GetValue(self):
        return self.comboBoxCtrl.GetValue()

    def Destroy(self):
        self.exists.clear()
        self.browser.Stop()
        wx.Dialog.Destroy(self)

def BuildServiceManagerMenu( ):
    """
    Used in the pulldown and popup menus to display the service manager menu
    """
    menu = wx.Menu()
    menu.Append(ID_HOST_ADD, "Add...", "Add a ServiceManager")
    menu.Append(ID_HOST_REMOVE, "Remove", "Remove a ServiceManager")
    return menu

def BuildServiceMenu( ):
    """
    Used in the pulldown and popup menus to display the service menu
    """
    svcmenu = wx.Menu()
    svcmenu.Append(ID_SERVICE_ADD_SERVICE, "Add...", "Add a Service")
    svcmenu.Append(ID_SERVICE_REMOVE, "Remove", "Remove the selected Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_ENABLE_ONE, "Enable", "Enable the selected Service")
    svcmenu.Append(ID_SERVICE_DISABLE_ONE, "Disable", "Disable the selected Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_CONFIGURE, "Configure...", "Configure the selected Service")
    return svcmenu


class StoreConfigDialog(wx.Dialog):
    """
    StoreConfigDialog displays the following:
        - a list of configurations
        - a text field (which is filled from selections in the
          list and can be edited)
        - a default checkbox, to specify that the saved config
          should be the default for the node
      
    """
    def __init__(self, parent, id, title, choices ):

        wx.Dialog.__init__(self, parent, id, title, style =
                          wx.DEFAULT_DIALOG_STYLE)

        # Create a display name - config map
        sysConfigs = []
        userConfigs = []
        self.configs = {}
        for c in choices:
            displayName = str(c.name+" ("+c.type+")")
            self.configs[displayName] = c
            
            if c.type == 'system':
                sysConfigs.append(displayName)
            elif c.type == 'user':
                userConfigs.append(displayName)
                
        sysConfigs.sort()
        userConfigs.sort()
        displayNames = sysConfigs + userConfigs
            
        # Set up sizers
        gridSizer = wx.FlexGridSizer(5, 1, 5, 5)
        gridSizer.AddGrowableCol(0)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self, -1, ""), wx.HORIZONTAL)
        sizer2.Add(gridSizer, 1, wx.ALL, 10)
        sizer1.Add(sizer2, 1, wx.ALL|wx.EXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        # Create config list label and listctrl
        configLabel = wx.StaticText(self,-1,"Configuration name")
        self.configList = wx.ListBox(self,wx.NewId(), style=wx.LB_SINGLE, choices=displayNames)
        gridSizer.Add( configLabel, 1 )
        gridSizer.Add( self.configList, 0, wx.EXPAND )
        wx.EVT_LISTBOX(self, self.configList.GetId(), self.__ListItemSelectedCallback)

        # Create config text label and field
        self.configText = wx.TextCtrl(self,-1,"")
        gridSizer.Add( self.configText, 1, wx.EXPAND )
        wx.EVT_TEXT(self,self.configText.GetId(), self.__TextEnteredCallback)

        # Create default checkbox
        self.defaultCheckbox = wx.CheckBox(self,-1,"Set as default")
        gridSizer.Add( self.defaultCheckbox, 1, wx.EXPAND )

        # Create system checkbox
        self.systemCheckbox = wx.CheckBox(self,-1,"Save as system configuration")
        gridSizer.Add( self.systemCheckbox, 1, wx.EXPAND )

        # Create ok/cancel buttons
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.okButton = wx.Button( self, wx.ID_OK, "OK" )
        cancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
        sizer3.Add(cancelButton, 0, wx.ALL, 10)
        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        # Ensure nothing is selected 
        items = self.configList.GetSelections()
        for item in items:
            self.configList.Deselect(item)

        # Disable the ok button until something is selected
        self.okButton.Enable(False)

        sizer1.Fit(self)

    def __ListItemSelectedCallback(self, event):
        name = event.GetString()

        if self.configs.has_key(event.GetString()):
            name = self.configs[event.GetString()].name
        
        self.configText.SetValue(name )

        # If system config is selected, check the system button
        c = None
        if self.configs.has_key(event.GetString()):
            c = self.configs[event.GetString()]
            
            if c.type == NodeConfigDescription.SYSTEM:
                self.systemCheckbox.SetValue(1)
            else:
                self.systemCheckbox.SetValue(0)

        self.okButton.Enable(True)

    def __TextEnteredCallback(self,event):

        # Enable the ok button if text in text field
        if self.configText.GetValue():
            self.okButton.Enable(True)
        else:
            self.okButton.Enable(False)

    def GetValue(self):
        # Get value of textfield, default checkbox, and system checkbox
        name = self.configText.GetValue()

        # Check if the config already exists and
        # get the real name
        if self.configs.has_key(name):
            config = self.configs[name]
            name = config.name
                
        return (name,
                self.defaultCheckbox.IsChecked(),
                self.systemCheckbox.IsChecked())


              
class ServiceConfigurationPanel( wx.Panel ):
    """
    A panel that displays service configuration parameters based on
    their type.
    """
    def __init__( self, parent, ID, pos=wx.DefaultPosition, size=(400,400), style=0 ):
        wx.Panel.__init__( self, parent, ID, pos, size, style )
        self.panel = self
        self.parent = parent
        self.callback = None
        self.CentreOnParent()
        
        self.config = None
        self.resource = None

    def SetResource(self,resourceIn):
        self.resource = resourceIn
            
            
    def GetResource(self):
        return 


    def SetConfiguration( self, serviceConfig ):
        self.config = serviceConfig
        
        
    def Layout(self):
        self.guiComponents = []

        rows = len(self.config)
        self.boxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panelSizer = wx.FlexGridSizer( rows, 2, 5, 5 ) #rows, cols, hgap, vgap
        self.panelSizer.AddGrowableCol(1)
        
        #
        # Build resource entry
        #
        if self.resource:
            pt = wx.StaticText( self, -1, "Resource", style=wx.ALIGN_LEFT)
            pComp = wx.TextCtrl( self, -1, self.resource.name, size = wx.Size(300, 20))
            pComp.SetEditable( False )
            self.panelSizer.Add( pt)
            self.panelSizer.Add( pComp, 0, wx.EXPAND )

        #
        # Build entries for config parms
        #
        for parameter in self.config:
            pt = wx.StaticText( self, -1, parameter.name, style=wx.ALIGN_LEFT )
            self.panelSizer.Add(pt, -1, wx.EXPAND)
            
            pComp = None
            if parameter.type == RangeParameter.TYPE:
                pComp = wx.Slider( self, -1, parameter.value, parameter.low, parameter.high, style = wx.SL_LABELS )
                
            elif parameter.type == OptionSetParameter.TYPE:
                pComp = wx.ComboBox( self, -1, "", style=wx.CB_READONLY )
                for option in parameter.options:
                    pComp.Append( option )
                pComp.SetValue( parameter.value )

            else:
                val = parameter.value
                if type(val) == int:
                    val = '%d' % (val)
                pComp = wx.TextCtrl( self.panel, -1, val )
            
            self.guiComponents.append( pComp )
          
            self.panelSizer.Add( pComp, 0, wx.EXPAND )

        self.boxSizer.Add(self.panelSizer, 1, wx.ALL | wx.EXPAND, 10)
        self.panel.SetSizer( self.boxSizer )
        self.panel.SetAutoLayout( True )

    def GetConfiguration( self ):

        # build modified configuration from ui
        
        for i in range( 0, len(self.guiComponents) ):
            if isinstance( self.guiComponents[i], wx.RadioBox ):
                self.config[i].value = self.guiComponents[i].GetStringSelection()
            else:
                self.config[i].value = self.guiComponents[i].GetValue()

        return self.config

    def SetCallback( self, callback ):
        self.callback = callback

    def Cancel(self, event):
        self.parent.Destroy()

class ServiceConfigurationDialog(wx.Dialog):
    """
    """
    def __init__(self, parent, id, title, resource, serviceConfig ):

        wx.Dialog.__init__(self, parent, id, title, 
                          style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

        # Set up sizers
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.StaticBoxSizer(wx.StaticBox(self, -1, ""), wx.VERTICAL)
        sizer1.Add(sizer2, 1, wx.ALL|wx.EXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        self.serviceConfigPanel = ServiceConfigurationPanel( self, -1 )
        self.serviceConfigPanel.SetResource( resource )
        self.serviceConfigPanel.SetConfiguration( serviceConfig )
        self.serviceConfigPanel.SetSize( wx.Size(200,200) )
        self.serviceConfigPanel.SetAutoLayout(True)
        self.serviceConfigPanel.Layout()
        self.serviceConfigPanel.Fit()
        sizer2.Add( self.serviceConfigPanel, 1, wx.EXPAND )

        # Create ok/cancel buttons
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button( self, wx.ID_OK, "OK" )
        cancelButton = wx.Button( self, wx.ID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wx.ALL, 10)
        sizer3.Add(cancelButton, 0, wx.ALL, 10)
        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        sizer1.Fit(self)
        
        x,y = wx.GetMousePosition()
        w,h = self.GetSize()
        self.Move( (x-w/2,y-h/2) )

    def GetConfiguration(self):
        return self.serviceConfigPanel.GetConfiguration()

class NodeManagementClientFrame(wx.Frame):
    """
    The main UI frame for Node Management
    """
    def __init__(self, parent, ID, title,size=wx.Size(450,300),callback=None):
        wx.Frame.__init__(self, parent, ID, title,
                         wx.DefaultPosition, size=size)
                         
        self.callback = callback
        self.Center()
        self.SetTitle(title)
        self.SetIcon(icons.getAGIconIcon())
        self.serviceManagers = []
        self.nodeServiceHandle = None

        self.app = Toolkit.Application.instance()

        menuBar = wx.MenuBar()

        ## FILE menu
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(ID_FILE_ATTACH, "Connect to Node...", 
                             "Connect to a NodeService")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_FILE_LOAD_CONFIG, "Load Configuration...", 
                             "Load a NodeService Configuration")
        self.fileMenu.Append(ID_FILE_STORE_CONFIG, "Store Configuration...", 
                             "Store a NodeService Configuration")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_FILE_EXIT, "E&xit", "Terminate the program")
        menuBar.Append(self.fileMenu, "&File");

        ## SERVICE MANAGERS menu
        self.serviceManagersMenu = BuildServiceManagerMenu()
        menuBar.Append(self.serviceManagersMenu, "&ServiceManager");
        
        ## SERVICE menu

        self.serviceMenu = BuildServiceMenu()
        menuBar.Append(self.serviceMenu, "&Service");
        
        ## HELP menu
        self.helpMenu = wx.Menu()
        self.helpMenu.Append(ID_HELP_ABOUT, "&About",
                    "More information about this program")
        menuBar.Append(self.helpMenu, "&Help");

        self.SetMenuBar(menuBar)

        self.tree = TreeListCtrl(self,-1,
                                   style = wx.TR_MULTIPLE|wx.TR_HIDE_ROOT|wx.TR_TWIST_BUTTONS)
        self.tree.AddColumn("Name")
        self.tree.AddColumn("Resource")
        self.tree.AddColumn("Status")
        self.tree.SetMainColumn(0)
        
        self.tree.SetColumnWidth(0,175)
        self.tree.SetColumnWidth(1,175)
        self.tree.SetColumnWidth(2,90)
        
        
        wx.EVT_TREE_ITEM_RIGHT_CLICK(self, self.tree.GetId(), self.PopupThatMenu)
        wx.EVT_TREE_ITEM_ACTIVATED(self, self.tree.GetId(), self.DoubleClickCB )

        wx.InitAllImageHandlers()

        imageSize = 22
        imageList = wx.ImageList(imageSize,imageSize)

        bm = icons.getComputerBitmap()
        self.smImage = imageList.Add(bm)

        bm = icons.getDefaultServiceBitmap()
        self.svcImage = imageList.Add(bm)
        
        self.tree.SetImageList(imageList)
        self.imageList = imageList
                

        # Create the status bar
        self.CreateStatusBar(2)
        self.SetStatusText("Not Connected",1)

        # Associate menu items with callbacks
        wx.EVT_MENU(self, ID_FILE_ATTACH            ,  self.Attach )
        wx.EVT_MENU(self, ID_FILE_EXIT              ,  self.TimeToQuit )
        wx.EVT_MENU(self, ID_FILE_LOAD_CONFIG       ,  self.LoadConfiguration )
        wx.EVT_MENU(self, ID_FILE_STORE_CONFIG      ,  self.StoreConfiguration )
        wx.EVT_MENU(self, ID_HELP_ABOUT             ,  self.OnAbout)
        wx.EVT_MENU(self, ID_HOST_ADD               ,  self.AddHost )
        wx.EVT_MENU(self, ID_HOST_REMOVE            ,  self.RemoveServiceManager )
        wx.EVT_MENU(self, ID_SERVICE_ADD_SERVICE    ,  self.AddService )
        wx.EVT_MENU(self, ID_SERVICE_CONFIGURE      ,  self.ConfigureService )
        wx.EVT_MENU(self, ID_SERVICE_REMOVE         ,  self.RemoveService )
        wx.EVT_MENU(self, ID_SERVICE_ENABLE         ,  self.EnableServices )
        wx.EVT_MENU(self, ID_SERVICE_ENABLE_ONE     ,  self.EnableService )
        wx.EVT_MENU(self, ID_SERVICE_DISABLE        ,  self.DisableServices )
        wx.EVT_MENU(self, ID_SERVICE_DISABLE_ONE    ,  self.DisableService )
        
        wx.EVT_TREE_KEY_DOWN(self.tree, self.tree.GetId(), self.OnKeyDown)
    
        self.menuBar = menuBar
        
        self.EnableMenus(False)
            
        self.recentNodeServiceList = []
        self.recentServiceManagerList = []
        
    def OnKeyDown(self,event):
        key = event.GetKeyCode()
      
        if key == wx.WXK_DELETE:

            dlg = wx.MessageDialog(self, "Delete selected items?" , "Confirm",
                                  style = wx.ICON_INFORMATION | wx.OK | wx.CANCEL)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wx.ID_OK:
                self.RemoveSelectedItems()
            
        elif key == wx.WXK_F5:
            self.UpdateUI()
        
    def Connected(self):
        try:
            self.nodeServiceHandle.IsValid()
            return 1
        except:
            return 0


    def EnableMenus(self, flag):
        self.fileMenu.Enable(ID_FILE_LOAD_CONFIG,flag)
        self.fileMenu.Enable(ID_FILE_STORE_CONFIG,flag)
        self.menuBar.EnableTop(1,flag)
        self.menuBar.EnableTop(2,flag)
        self.menuBar.EnableTop(3,flag)
        
    

    ############################
    ## FILE menu
    ############################

    def Attach( self, event ):
        """
        Attach to a node service
        """

        dlg = ServiceChoiceDialog(self,-1,'NodeService Dialog',
                                  self.recentNodeServiceList,
                                  AGNodeService.ServiceType,
                                  'Select a Node Service URL from the list, or enter the hostname or \nservice URL of the Node Service')
        dlg.Center()
        ret = dlg.ShowModal()


        if ret == wx.ID_OK:
            url = dlg.GetValue()
            dlg.Destroy()
            
            url = BuildServiceUrl(url,'http',11000,'NodeService')
            
            if url not in self.recentNodeServiceList:
                self.recentNodeServiceList.append(url)
            
            # Attach (or fail)
            wx.BeginBusyCursor()
            self.AttachToNode(AGNodeServiceIW(url))

            if not self.Connected():
                self.Error( "Could not attach to AGNodeService at " + url  )
                wx.EndBusyCursor()
                return

            # Update the servicemanager and service lists
            self.UpdateUI()
            wx.EndBusyCursor()
        else:
            dlg.Destroy()
            
    def AttachToNode( self, nodeService ):
        """
        This method does the real work of attaching to a node service
        """

        # self.CheckCredentials()

        # Get proxy to the node service, if the url validates
        self.nodeServiceHandle = nodeService

        if self.nodeServiceHandle and self.nodeServiceHandle.IsValid():
            self.SetStatusText("Connected",1)
            self.EnableMenus(True)
      
    def LoadConfiguration( self, event ):
        """
        Load a configuration for the node service
        """
        configs = self.nodeServiceHandle.GetConfigurations()

        # Map display name to configurations
        sysConfigs = []
        userConfigs = []
        configMap = {}
        for c in configs:
            displayName = c.name+" ("+c.type+")"
            configMap[displayName] = c
            
            if c.type == 'system':
                sysConfigs.append(displayName)
            elif c.type == 'user':
                userConfigs.append(displayName)

        sysConfigs.sort()
        userConfigs.sort()
        displayNames = sysConfigs + userConfigs

        d = wx.SingleChoiceDialog( self, "Select a configuration file to load", 
                                  "Load Configuration Dialog", displayNames)
        ret = d.ShowModal()

        if ret == wx.ID_OK:
            conf = d.GetStringSelection()

            if len( conf ) == 0:
                self.Error( "No selection made" )
                return

            # Get correct config name
            if configMap.has_key:
                conf = configMap[conf].name

            config = None
            for c in configs:
                if conf == c.name:
                    config = c

            try:
                wx.BeginBusyCursor()
                self.nodeServiceHandle.LoadConfiguration( config )
            except:
                log.exception("NodeManagementClientFrame.LoadConfiguration: Can not load configuration from node service")
                self.Error("Error loading node configuration %s" % (conf,))

            self.UpdateUI()
            
            if self.callback:
                try:
                    self.callback('load_config')
                except:
                    log.exception('exception from registered callback')
            
            wx.EndBusyCursor()

    def StoreConfiguration( self, event ):
        """
        Store a node service configuration
        """

        # Get known configurations from the Node Service
        configs = self.nodeServiceHandle.GetConfigurations()

        # Prompt user to name the configuration
        d = StoreConfigDialog(self,-1,"Store Configuration", configs)
        ret = d.ShowModal()

        if ret == wx.ID_OK:
            ret = d.GetValue()
            if ret:
                (configName,isDefault,isSystem) = ret
                
                # Handle error cases
                if len( configName ) == 0:
                    self.Error( "Invalid config name specified (%s)" % (configName,) )
                    return
                     
                # Confirm overwrite
                if configName in map(lambda x: x.name, configs): #configs:
                    text ="Overwrite %s?" % (configName,)
                    dlg = wx.MessageDialog(self, text, "Confirm",
                                          style = wx.ICON_INFORMATION | wx.OK | wx.CANCEL)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret != wx.ID_OK:
                        return

                config = None
             
                for c in configs:
                    if configName == c.name:
                        config = c

                if not config:
                    # Create a new configuration
                    config = NodeConfigDescription(configName, NodeConfigDescription.USER)

                if isSystem:
                    config.type = NodeConfigDescription.SYSTEM
                                    
                # Store the configuration
                try:
                    wx.BeginBusyCursor()
                    self.nodeServiceHandle.StoreConfiguration( config )
                except:
                    log.exception("Error storing node configuration %s" % (configName,))
                    self.Error("Error storing node configuration %s" % (configName,))

                # Set the default configuration
                if isDefault:
                    prefs = self.app.GetPreferences()
                    prefs.SetPreference(Preferences.NODE_CONFIG,configName)
                    prefs.SetPreference(Preferences.NODE_CONFIG_TYPE,config.type)
                    prefs.StorePreferences()

                if self.callback:
                    try:
                        self.callback('store_config')
                    except:
                        log.exception('exception from registered callback')
                    
                wx.EndBusyCursor()

        d.Destroy()


    def TimeToQuit(self, event):
        """
        Exit
        """
        self.Close(True)

    ############################
    ## VIEW menu
    ############################

    def UpdateUI( self, event=None ):
        """
        Update the service list (bring it into sync with the node service)
        """
        
        selections = self.GetSelectedItems()
        selectionUrls = []
        if len(selections)>0:
            selectionUrls = map( lambda x: x.uri, selections)

        self.serviceManagers = self.nodeServiceHandle.GetServiceManagers()

        import urlparse
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("")    
        if self.serviceManagers:
            for serviceManager in self.serviceManagers:
                name = urlparse.urlsplit(serviceManager.uri)[1]
                sm = self.tree.AppendItem(root,name)
                self.tree.SetItemImage(sm, self.smImage,which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(sm, self.smImage, which=wx.TreeItemIcon_Expanded)
                self.tree.SetItemData(sm,wx.TreeItemData(serviceManager))
                services = serviceManager.GetObject().GetServices()
                        
                if services: 
                    for service in services:
                        s = self.tree.AppendItem(sm,service.name)
                        self.tree.SetItemImage(s, self.svcImage, which = wx.TreeItemIcon_Normal)
                        self.tree.SetItemData(s,wx.TreeItemData(service))
                        resource = service.GetObject().GetResource()
                        if resource:
                            self.tree.SetItemText(s,resource.name,1)
                        if service.GetObject().GetEnabled():
                            status = "Enabled"
                        else:
                            status = "Disabled"
                        self.tree.SetItemText(s,status,2)
                
                        if service.uri in selectionUrls:
                            self.tree.SelectItem(s)
                
                    self.tree.Expand(sm)
                else:
                    s = self.tree.AppendItem(sm,'No services')
                    self.tree.Collapse(sm)
            
                if serviceManager.uri in selectionUrls:
                    self.tree.SelectItem(sm)
                    
                if not self.tree.GetSelections():
                    self.SelectDefault()

            self.tree.Expand(root)
    
    ############################
    ## HOST menu
    ############################
    def AddHost( self, event ):
        """
        Add a service manager to the node service
        """

        dlg = ServiceChoiceDialog(self,-1,'Service Manager Dialog',
                                  self.recentServiceManagerList,
                                  AGServiceManager.ServiceType,
                                  'Select a Service Manager URL from the list, or enter the hostname or \nservice URL of the Service Manager')
        dlg.Center()
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:

            url = dlg.GetValue()
            dlg.Destroy()

            url = BuildServiceUrl(url,'http',11000,'ServiceManager')

            if url not in self.recentServiceManagerList:
                self.recentServiceManagerList.append(url)
            try:
                wx.BeginBusyCursor()
                self.nodeServiceHandle.AddServiceManager( url )
            except (socket.gaierror,socket.error),e:
                log.exception("Exception in AddHost")
                self.Error("Can not add service manager to node service:\n%s"%(e.args[1]))
            except:
                log.exception("Exception in AddHost")
                self.Error("Can not add service manager to node service.")

            # Update the service manager list
            self.UpdateUI()
            
            wx.EndBusyCursor()
        else:
            dlg.Destroy()

    def RemoveServiceManager( self, event ):
        """
        Remove a host from the node service
        """
        
        selections = self.GetSelectedServiceManagers(includeImplicit=1)

        # Require a service manager to be selected
        if len(selections) == 0:
            self.Error( "No service manager selected!" )
            return

        # Find selected service manager and remove it
        wx.BeginBusyCursor()
        try:
            index = -1
            for obj in selections:
                try:
                    self.nodeServiceHandle.RemoveServiceManager( obj.uri )
                except ServiceManagerCannotBeRemovedBuiltIn:
                    self.Error("Cannot remove built in Service Manager")
                except:
                    log.exception("Error removing service manager %s", self.serviceManagers[index].uri)

            # Update the service list
            self.UpdateUI()
        finally:
            wx.EndBusyCursor()

    def ServiceManagerSelectedCB(self, event):
        index = self.serviceManagerList.GetNextItem( -1, state = wx.LIST_STATE_SELECTED )
        uri = self.serviceManagers[index].uri
        #try:
        #    AGServiceManagerIW(uri).IsValid()
        #except:
        #    log.exception("Service Manager is unreachable (%s)" % (uri,))
        #    self.Error("Service Manager is unreachable (%s)" % (uri,))
        #    return

        self.UpdateUI()

    ############################
    ## SERVICE menu
    ############################

    def AddService( self, event=None ):
        """
        Add a service to the node service
        """
        
        selections = self.GetSelectedServiceManagers(includeImplicit=1)

        # Require a single host to be selected
        if len(selections) == 0:
            self.Error( "No Service Manager selected for service!")
            return
        if len(selections) > 1:
            self.Error("Multiple hosts selected")
            return
            
        serviceManager = selections[0]

        # Get services available
        try:
            wx.BeginBusyCursor()
            servicePackages =  serviceManager.GetObject().GetServicePackageDescriptions()
        except:
            log.exception("Exception getting service packages")
        wx.EndBusyCursor()
        availServiceNames = map( lambda servicePkg: servicePkg.name, servicePackages )

        #
        # Prompt for service to add
        #
        dlg = wx.SingleChoiceDialog( self, "Select Service to Add", "Add Service: Select Service",
                                    availServiceNames )

        dlg.SetSize(wx.Size(300,200))
        ret = dlg.ShowModal()

        if ret == wx.ID_OK:
            #
            # Find the selected service description based on the name
            serviceToAdd = None
            serviceName = dlg.GetStringSelection()
            for servicePkg in servicePackages:
                if serviceName == servicePkg.name:
                    serviceToAdd = servicePkg
                    break

            if serviceToAdd == None:
                raise Exception("Can't add None service")

            try:
                #
                # Add the service
                #
                wx.BeginBusyCursor()
                serviceDescription = serviceManager.GetObject().AddService( serviceToAdd,                                                                            
                                                                                        None, [],
                                                                                        self.app.GetPreferences().GetProfile())
                
                # Configure resource
                if serviceToAdd.resourceNeeded:
                    resources = serviceDescription.GetObject().GetResources()
                    resourceNames = map(lambda x:x.name,resources)
                    if len(resources) > 0:
                        log.info("Prompt for resource")
                        log.debug("Resources: %s" % (resources,))

                        dlg = wx.SingleChoiceDialog( self, 
                                                    "Select resource for service", 
                                                    "Add Service: Select Resource",
                                                    resourceNames )

                        dlg.SetSize(wx.Size(300,200))

                        ret = dlg.ShowModal()

                        if ret != wx.ID_OK:
                            return

                        selectedResourceName = dlg.GetStringSelection()

                        foundResource = 0
                        for r in resources:
                            if r.name == selectedResourceName:
                                serviceDescription.GetObject().SetResource(r)
                                foundResource = 1
                                break
                        if not foundResource:
                            raise Exception("Unknown resource selected: %s", selectedResourceName)
                    else:
                        log.info("No resources for service")
                        
                if self.callback:
                    try:
                        self.callback('add_service',serviceDescription)
                    except:
                        log.exception('exception from registered callback')
            except:
                wx.EndBusyCursor()
                log.exception( "Add Service failed:" + serviceToAdd.name)
                self.Error( "Add Service failed:" + serviceToAdd.name )
                return

            self.UpdateUI()
            
            
            wx.EndBusyCursor()

    def EnableService( self, event=None ):
        """
        Enable the selected service(s)
        """
        
        selections = self.GetSelectedServices()

        # Require a service to be selected
        if len(selections) == 0:
            self.Error( "No service selected!" )
            return

        try:
            wx.BeginBusyCursor()

            # Enable all selected services
            index = -1
            for service in selections:
                log.debug("NodeManagementClientFrame.EnableService: Enabling Service: %s" %service.name)
                self.nodeServiceHandle.SetServiceEnabled(service.uri, 1)

            # Update the services list
            self.UpdateUI()

        except:
            log.exception("Error enabling service")
            self.Error("Error enabling service")
            
        wx.EndBusyCursor()
        

    def EnableServices( self, event ):
        """
        Enable all known services
        """
        services = self.nodeServiceHandle.GetServices()
        for service in services:
            self.nodeServiceHandle.SetServiceEnabled(service.uri,1)

        self.UpdateUI()

    def DisableService( self, event=None ):
        """
        Disable the selected service(s)
        """
        
        selections = self.GetSelectedServices()

        # Require a service to be selected
        if len(selections) == 0:
            self.Error( "No service selected!" )
            return

        try:
            wx.BeginBusyCursor()
            # Disable all selected services
            index = -1
            for service in selections:
                self.nodeServiceHandle.SetServiceEnabled(service.uri,0)

            # Update the service list
            self.UpdateUI()
        except:
            log.exception("Error disabling service")
            self.Error("Error disabling service")

        wx.EndBusyCursor()

    def DisableServices( self, event ):
        """
        Disable all known services
        """
        svcs = self.nodeServiceHandle.GetServices()
        for svc in svcs:
            self.nodeServiceHandle.SetServiceEnabled(svc.uri,0)

        self.UpdateUI()

    def RemoveService( self, event ):
        """
        Remove the selected service(s)
        """
        
        selections = self.tree.GetSelections()
        
        # Require a service to be selected
        if len(selections) == 0:
            self.Error( "No service selected!" )
            return
            
        try:
            wx.BeginBusyCursor()
            # Remove all selected services
            for s in selections:
                obj = self.tree.GetPyData(s)
                if isinstance(obj,AGServiceDescription):
                    smItem = self.tree.GetItemParent(s)
                    sm = self.tree.GetItemData(smItem).GetData()
                    AGServiceManagerIW( sm.uri ).RemoveService( obj )
                    self.tree.Delete(s)
                                       
            self.UpdateUI()
            
        finally:
            wx.EndBusyCursor()
            
    def DoubleClickCB(self,event):
        selections = self.GetSelectedItems()
        if len(selections):
            if isinstance(selections[0],AGServiceManagerDescription):
                item = event.GetItem()
                self.tree.Toggle(item)
            elif isinstance(selections[0],AGServiceDescription):
                self.ConfigureService(event)

    def ConfigureService( self, event=None ):
        """
        Configure the selected service
        """
        
        selections = self.GetSelectedServices()

        # Require a single service to be selected
        if len(selections) == 0:
            self.Error( "No service selected!" )
            return
        if len(selections) > 1:
            self.Error("Multiple services selected")
            return
            
        service = selections[0]

        # Get configuration
        try:
            wx.BeginBusyCursor()
            config = service.GetObject().GetConfiguration()
        except:
            wx.EndBusyCursor()
            log.exception("Service is unreachable at %s" % (service.uri,))
            self.Error("Service is unreachable at %s" % (service.uri,))
            return
            
        resource = service.GetObject().GetResource()

        wx.EndBusyCursor()
        if config:
            # Display the service configuration panel
            dlg = ServiceConfigurationDialog(self,-1,"Service Config Dialog",
                                             resource, 
                                             config)
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
            
                # Get config from the dialog and set it in the service
                config = dlg.GetConfiguration()
                wx.BeginBusyCursor()
                try:
                    # Send the modified configuration to the service
                    service.GetObject().SetConfiguration( config )
                except:
                    log.exception("Exception setting configuration")
                wx.EndBusyCursor()
        else:
            self.Error("Service has no configurable options")





    ############################
    ## HELP menu
    ############################
    def OnAbout(self, event):
        """
        Display about AG info
        """
        aboutDialog = AboutDialog(self)
        aboutDialog.ShowModal()
        aboutDialog.Destroy()



    ############################
    ## UTILITY methods
    ############################
    def Error( self, message ):
        wx.MessageDialog( self, message, style = wx.OK | wx.ICON_INFORMATION ).ShowModal()
        
    def PopupThatMenu(self, evt):
    
        # if current item is not selected:
        # - deselect everything else
        # - select the current item
        item = evt.GetItem()
        selections = self.tree.GetSelections()
        if item not in selections:
            self.tree.UnselectAll()
            self.tree.SelectItem(item)

        selections = self.GetSelectedItems()
        
        if len(selections) == 0:
            return
            
        selection = selections[0]
        if isinstance(selection,AGServiceManagerDescription):
            self.PopupHostMenu(evt)
        elif isinstance(selection,AGServiceDescription):
            self.PopupServiceMenu(evt)
    
    def PopupServiceMenu(self, evt):
        """
        Popup the service menu
        """
        
            
        menu = wx.Menu()
        menu.Append(ID_SERVICE_ENABLE_ONE, "Enable", "Enable the selected service")
        menu.Append(ID_SERVICE_DISABLE_ONE, "Disable", "Disable the selected service")
        menu.Append(ID_SERVICE_CONFIGURE, "Configure...", "Configure the selected service")
        menu.Append(ID_SERVICE_REMOVE, "Remove", "Remove the selected service")

        # Get the Mouse Position on the Screen 
        (windowx, windowy) = wx.GetMousePosition() 
        # Translate the Mouse's Screen Position to the Mouse's Control Position 
        pos = self.tree.ScreenToClientXY(windowx, windowy)
        posl = [ pos[0] + 155, pos[1] + 25 ]
        self.PopupMenu(menu,pos)

    def PopupHostMenu(self, evt):
        """
        Popup the service manager menu
        """
        
        menu = wx.Menu()
        
        menu.Append(ID_SERVICE_ADD_SERVICE, "Add Service...", "Add a service")
        menu.AppendSeparator()
        menu.Append(ID_HOST_REMOVE, "Remove Service Manager", "Remove a service manager")

        # Get the Mouse Position on the Screen 
        (windowx, windowy) = wx.GetMousePosition() 
        # Translate the Mouse's Screen Position to the Mouse's Control Position 
        pos = self.tree.ScreenToClientXY(windowx, windowy)
        posl = [ pos[0] + 25, pos[1] + 25 ]
        self.PopupMenu(menu, pos)

    def CheckCredentials(self):
        """
        Check credentials and create a new proxy if necessary
        """
        if not self.app.GetCertificateManager().HaveValidProxy():
            self.app.GetCertificateManager().InitEnvironment()

    def ClearUI(self):
        """
        Clear the UI
        """
        self.tree.DeleteAllItems()
        
    def GetSelectedItems(self,selType=None):
        """
        Get list of selected items
        """
        retList = []
        selections = self.tree.GetSelections()
        
        if len(selections) == 0:
            return retList
            
        for s in selections:
            obj = self.tree.GetItemData(s).GetData()
            if (not selType or isinstance(obj,selType)) and obj :
              retList.append(obj)
            
        return retList
        
    def GetSelectedServiceManagers(self,includeImplicit=0):
        retSel = []
        selections = self.tree.GetSelections()
        for s in selections:
            obj = self.tree.GetItemData(s).GetData()
            if isinstance(obj,AGServiceManagerDescription):
                sm = self.tree.GetItemData(s).GetData()
                if sm not in retSel:
                    retSel.append(sm)
            elif includeImplicit and isinstance(obj,AGServiceDescription):
                smItem = self.tree.GetItemParent(s)
                sm = self.tree.GetItemData(smItem).GetData()
                if sm not in retSel:
                    retSel.append(sm)

        return retSel
        
    def GetSelectedServices(self):
        return self.GetSelectedItems(AGServiceDescription)
        
    def RemoveSelectedItems(self):
    
        selections = self.tree.GetSelections()
        itemsToRemove = []
        
        # Remove services first
        for s in selections:
            obj = self.tree.GetPyData(s)
            if isinstance(obj,AGServiceDescription):
                smItem = self.tree.GetItemParent(s)
                sm = self.tree.GetItemData(smItem).GetData()
                AGServiceManagerIW( sm.uri ).RemoveService( obj )
                itemsToRemove.append(s)

        # Remove service managers
        for s in selections:
            obj = self.tree.GetPyData(s)
            if isinstance(obj,AGServiceManagerDescription):
                self.nodeServiceHandle.RemoveServiceManager( obj.uri )
                itemsToRemove.append(s)
                
        for item in itemsToRemove:
            self.tree.Delete(item)

    def SelectDefault(self):
        rootItem = self.tree.GetRootItem()
        firstChild,cookie = self.tree.GetFirstChild(rootItem)
        self.tree.SelectItem(firstChild)


if __name__ == "__main__":
    
    app = wx.PySimpleApp()

    # Service config dialog test
    resource = ResourceDescription("resource")
    config = []

    dlg = ServiceConfigurationDialog(None, -1, "Service Config Dialog", resource,config)
    ret = dlg.ShowModal()
    dlg.Destroy()
   
