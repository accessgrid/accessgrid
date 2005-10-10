#-----------------------------------------------------------------------------
# Name:        NodeManagementUIClasses.py
# Purpose:
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: NodeManagementUIClasses.py,v 1.81 2005-10-10 19:45:29 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NodeManagementUIClasses.py,v 1.81 2005-10-10 19:45:29 lefvert Exp $"
__docformat__ = "restructuredtext en"
import sys

from wxPython.wx import *
from wxPython.lib.dialogs import wxMultipleChoiceDialog
from wxPython.gizmos import wxTreeListCtrl

# AG2 imports
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


class RendezvousServiceDialog(wxDialog):
    """
    """
    def __init__(self, parent, id, title, choices, serviceType ):

        wxDialog.__init__(self, parent, id, title, 
                          style=wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER,
                          )

        self.listCtrl = wxListBox(self,-1,choices=choices)

        # Set up sizers
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxHORIZONTAL)
        sizer2.Add(self.listCtrl, 1, wxEXPAND, 10)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
                 
        # Create ok/cancel buttons
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton( self, wxID_OK, "OK")
        cancelButton = wxButton( self, wxID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wxALL, 10)
        sizer3.Add(cancelButton, 0, wxALL, 10)
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)
        
        self.SetSizer( sizer1 )
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        
        self.browser = ServiceDiscovery.Browser(serviceType,self.BrowseCallback)
        self.browser.Start()

        x,y = wxGetMousePosition()
        w,h = self.GetSize()
        self.Move( (x-w/2,y-h/2) )

        #EVT_TEXT_ENTER(self, self.GetId(), self.OnOK)

    def __del__(self):
        self.browser.Stop()

    def BrowseCallback(self,op,serviceName,url=None):
        if op == ServiceDiscovery.Browser.ADD:
            self.AddItem(serviceName,url)
        
    def AddItem(self,name,url):
        wxCallAfter(self.listCtrl.Append,name,url)
        wxCallAfter(self.listCtrl.Refresh)
        
    def GetValue(self):
        # Get details of selected service
        indx = self.listCtrl.GetSelection()
        url = self.listCtrl.GetClientData(indx)
        return url

class ServiceChoiceDialog(wxDialog):
    def __init__(self, parent, id, title, choices, serviceType, size=wxSize(450,130) ):

        wxDialog.__init__(self, parent, id, title, style =
                          wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER,
                          size=size)
                          
        self.serviceType = serviceType
              
        # Set up sizers
        gridSizer = wxFlexGridSizer(3, 2, 5, 5)
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxHORIZONTAL)
        sizer2.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
       
        gridSizer.AddGrowableCol(0)

        self.comboBoxCtrl = wxComboBox(self,-1, choices=choices)
        gridSizer.Add( self.comboBoxCtrl, 0, wxEXPAND)
        
        browseButton = wxButton(self,-1,'Browse')
        gridSizer.Add( browseButton, 0, wxALIGN_RIGHT)
        EVT_BUTTON(self,browseButton.GetId(),self.OnBrowse)
          
        # Create ok/cancel buttons
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton( self, wxID_OK, "OK")
        cancelButton = wxButton( self, wxID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wxALL, 10)
        sizer3.Add(cancelButton, 0, wxALL, 10)
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)
        
        self.SetSizer( sizer1 )
        
        x,y = wxGetMousePosition()
        w,h = self.GetSize()
        self.Move( (x-w/2,y-h/2) )
        #EVT_TEXT_ENTER(self, self.GetId(), self.OnOK)

    def OnBrowse(self,event):
        dlg = RendezvousServiceDialog(self,-1,'Choose service',
                                      [], self.serviceType)
        ret = dlg.ShowModal()
        if ret == wxID_OK:
            val = dlg.GetValue()
            self.comboBoxCtrl.SetValue(val)
        
    def GetValue(self):
        return self.comboBoxCtrl.GetValue()

def BuildServiceManagerMenu( ):
    """
    Used in the pulldown and popup menus to display the service manager menu
    """
    menu = wxMenu()
    menu.Append(ID_HOST_ADD, "Add...", "Add a ServiceManager")
    menu.Append(ID_HOST_REMOVE, "Remove", "Remove a ServiceManager")
    return menu

def BuildServiceMenu( ):
    """
    Used in the pulldown and popup menus to display the service menu
    """
    svcmenu = wxMenu()
    svcmenu.Append(ID_SERVICE_ADD_SERVICE, "Add...", "Add a Service")
    svcmenu.Append(ID_SERVICE_REMOVE, "Remove", "Remove the selected Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_ENABLE_ONE, "Enable", "Enable the selected Service")
    svcmenu.Append(ID_SERVICE_DISABLE_ONE, "Disable", "Disable the selected Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_CONFIGURE, "Configure...", "Configure the selected Service")
    return svcmenu


class StoreConfigDialog(wxDialog):
    """
    StoreConfigDialog displays the following:
        - a list of configurations
        - a text field (which is filled from selections in the
          list and can be edited)
        - a default checkbox, to specify that the saved config
          should be the default for the node
      
    """
    def __init__(self, parent, id, title, choices ):

        wxDialog.__init__(self, parent, id, title, style =
                          wxDEFAULT_DIALOG_STYLE)

        # Create a display name - config map
        self.configs = {}
        for c in choices:
            displayName = c.name+" ("+c.type+")"
            self.configs[displayName] = c
            
        # Set up sizers
        gridSizer = wxFlexGridSizer(5, 1, 5, 5)
        gridSizer.AddGrowableCol(0)
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxHORIZONTAL)
        sizer2.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        # Create config list label and listctrl
        configLabel = wxStaticText(self,-1,"Configuration name")
        self.configList = wxListBox(self,wxNewId(), style=wxLB_SINGLE, choices=self.configs.keys())
        gridSizer.Add( configLabel, 1 )
        gridSizer.Add( self.configList, 0, wxEXPAND )
        EVT_LISTBOX(self, self.configList.GetId(), self.__ListItemSelectedCallback)

        # Create config text label and field
        self.configText = wxTextCtrl(self,-1,"")
        gridSizer.Add( self.configText, 1, wxEXPAND )
        EVT_TEXT(self,self.configText.GetId(), self.__TextEnteredCallback)

        # Create default checkbox
        self.defaultCheckbox = wxCheckBox(self,-1,"Set as default")
        gridSizer.Add( self.defaultCheckbox, 1, wxEXPAND )

        # Create system checkbox
        self.systemCheckbox = wxCheckBox(self,-1,"Save as system configuration")
        gridSizer.Add( self.systemCheckbox, 1, wxEXPAND )

        # Create ok/cancel buttons
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        self.okButton = wxButton( self, wxID_OK, "OK" )
        cancelButton = wxButton( self, wxID_CANCEL, "Cancel" )
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(cancelButton, 0, wxALL, 10)
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        # Ensure nothing is selected 
        items = self.configList.GetSelections()
        for item in items:
            self.configList.Deselect(item)

        # Disable the ok button until something is selected
        self.okButton.Enable(false)

        sizer1.Fit(self)

    def __ListItemSelectedCallback(self, event):
        name = event.GetString()

        if self.configs.has_key(event.GetString()):
            name = self.configs[event.GetString()].name
        
        self.configText.SetValue(name )

        # If system config is selected, check the system button
        c = None
        if self.configs.has_key(name):
            c = self.configs[event.GetString()]
            
            if c.type == NodeConfigDescription.SYSTEM:
                self.systemCheckbox.SetValue(1)
            else:
                self.systemCheckbox.SetValue(0)

        self.okButton.Enable(true)

    def __TextEnteredCallback(self,event):

        # Enable the ok button if text in text field
        if self.configText.GetValue():
            self.okButton.Enable(true)
        else:
            self.okButton.Enable(false)

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


              
class ServiceConfigurationPanel( wxPanel ):
    """
    A panel that displays service configuration parameters based on
    their type.
    """
    def __init__( self, parent, ID, pos=wxDefaultPosition, size=(400,400), style=0 ):
        wxPanel.__init__( self, parent, ID, pos, size, style )
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
        self.boxSizer = wxBoxSizer(wxHORIZONTAL)
        self.panelSizer = wxFlexGridSizer( rows, 2, 5, 5 ) #rows, cols, hgap, vgap
        self.panelSizer.AddGrowableCol(1)
        
        #
        # Build resource entry
        #
        if self.resource:
            pt = wxStaticText( self, -1, "Resource", style=wxALIGN_LEFT)
            pComp = wxTextCtrl( self, -1, self.resource.name, size = wxSize(300, 20))
            pComp.SetEditable( false )
            self.panelSizer.Add( pt)
            self.panelSizer.Add( pComp, 0, wxEXPAND )

        #
        # Build entries for config parms
        #
        for parameter in self.config:
            pt = wxStaticText( self, -1, parameter.name, style=wxALIGN_LEFT )
            self.panelSizer.Add(pt, -1, wxEXPAND)
            
            pComp = None
            if parameter.type == RangeParameter.TYPE:
                pComp = wxSlider( self, -1, parameter.value, parameter.low, parameter.high, style = wxSL_LABELS )
                
            elif parameter.type == OptionSetParameter.TYPE:
                pComp = wxComboBox( self, -1, "", style=wxCB_READONLY )
                for option in parameter.options:
                    pComp.Append( option )
                pComp.SetValue( parameter.value )

            else:
                val = parameter.value
                if type(val) == int:
                    val = '%d' % (val)
                pComp = wxTextCtrl( self.panel, -1, val )
            
            self.guiComponents.append( pComp )
          
            self.panelSizer.Add( pComp, 0, wxEXPAND )

        self.boxSizer.Add(self.panelSizer, 1, wxALL | wxEXPAND, 10)
        self.panel.SetSizer( self.boxSizer )
        self.panel.SetAutoLayout( true )

    def GetConfiguration( self ):

        # build modified configuration from ui
        
        for i in range( 0, len(self.guiComponents) ):
            if isinstance( self.guiComponents[i], wxRadioBox ):
                self.config[i].value = self.guiComponents[i].GetStringSelection()
            else:
                self.config[i].value = self.guiComponents[i].GetValue()

        return self.config

    def SetCallback( self, callback ):
        self.callback = callback

    def Cancel(self, event):
        self.parent.Destroy()

class ServiceConfigurationDialog(wxDialog):
    """
    """
    def __init__(self, parent, id, title, resource, serviceConfig ):

        wxDialog.__init__(self, parent, id, title, 
                          style = wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)

        # Set up sizers
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        self.serviceConfigPanel = ServiceConfigurationPanel( self, -1 )
        self.serviceConfigPanel.SetResource( resource )
        self.serviceConfigPanel.SetConfiguration( serviceConfig )
        self.serviceConfigPanel.SetSize( wxSize(200,200) )
        self.serviceConfigPanel.SetAutoLayout(true)
        self.serviceConfigPanel.Layout()
        self.serviceConfigPanel.Fit()
        sizer2.Add( self.serviceConfigPanel, 1, wxEXPAND )

        # Create ok/cancel buttons
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton( self, wxID_OK, "OK" )
        cancelButton = wxButton( self, wxID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wxALL, 10)
        sizer3.Add(cancelButton, 0, wxALL, 10)
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        sizer1.Fit(self)
        
        x,y = wxGetMousePosition()
        w,h = self.GetSize()
        self.Move( (x-w/2,y-h/2) )

    def GetConfiguration(self):
        return self.serviceConfigPanel.GetConfiguration()

class NodeManagementClientFrame(wxFrame):
    """
    The main UI frame for Node Management
    """
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, wxSize(450, 300))

        self.SetTitle(title)
        self.SetIcon(icons.getAGIconIcon())
        self.serviceManagers = []
        self.nodeServiceHandle = None

        self.app = Toolkit.Application.instance()

        menuBar = wxMenuBar()

        ## FILE menu
        self.fileMenu = wxMenu()
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
        self.helpMenu = wxMenu()
        self.helpMenu.Append(ID_HELP_ABOUT, "&About",
                    "More information about this program")
        menuBar.Append(self.helpMenu, "&Help");

        self.SetMenuBar(menuBar)

        self.tree = wxTreeListCtrl(self,-1,
                                   style=wxEXPAND|wxALL|wxTR_HIDE_ROOT|wxTR_TWIST_BUTTONS)
        self.tree.AddColumn("Name")
        self.tree.AddColumn("Resource")
        self.tree.AddColumn("Status")
        self.tree.SetMainColumn(0)
        
        self.tree.SetColumnWidth(0,175)
        self.tree.SetColumnWidth(1,175)
        self.tree.SetColumnWidth(2,90)
        
        
        EVT_TREE_ITEM_RIGHT_CLICK(self, self.tree.GetId(), self.PopupThatMenu)
        EVT_TREE_ITEM_ACTIVATED(self, self.tree.GetId(), self.DoubleClickCB )

        wxInitAllImageHandlers()


        imageSize = 19
        imageList = wxImageList(imageSize,imageSize)
        self.smImage = imageList.Add(icons.getHostBitmap())
        self.svcImage = imageList.Add(icons.getServiceBitmap())
        self.tree.SetImageList(imageList)
        self.imageList = imageList
                

        # Create the status bar
        self.CreateStatusBar(2)
        self.SetStatusText("This is the statusbar",1)

        # Associate menu items with callbacks
        EVT_MENU(self, ID_FILE_ATTACH            ,  self.Attach )
        EVT_MENU(self, ID_FILE_EXIT              ,  self.TimeToQuit )
        EVT_MENU(self, ID_FILE_LOAD_CONFIG       ,  self.LoadConfiguration )
        EVT_MENU(self, ID_FILE_STORE_CONFIG      ,  self.StoreConfiguration )
        EVT_MENU(self, ID_HELP_ABOUT             ,  self.OnAbout)
        EVT_MENU(self, ID_HOST_ADD               ,  self.AddHost )
        EVT_MENU(self, ID_HOST_REMOVE            ,  self.RemoveServiceManager )
        EVT_MENU(self, ID_SERVICE_ADD_SERVICE    ,  self.AddService )
        EVT_MENU(self, ID_SERVICE_CONFIGURE      ,  self.ConfigureService )
        EVT_MENU(self, ID_SERVICE_REMOVE         ,  self.RemoveService )
        EVT_MENU(self, ID_SERVICE_ENABLE         ,  self.EnableServices )
        EVT_MENU(self, ID_SERVICE_ENABLE_ONE     ,  self.EnableService )
        EVT_MENU(self, ID_SERVICE_DISABLE        ,  self.DisableServices )
        EVT_MENU(self, ID_SERVICE_DISABLE_ONE    ,  self.DisableService )
        
        EVT_TREE_KEY_DOWN(self.tree, self.tree.GetId(), self.OnKeyDown)
        
        self.menuBar = menuBar
        
        self.EnableMenus(false)
            
        self.recentNodeServiceList = []
        self.recentServiceManagerList = []
        
    def OnKeyDown(self,event):
        key = event.GetKeyCode()
      
        if key == WXK_DELETE:

            dlg = wxMessageDialog(self, "Delete selected items?" , "Confirm",
                                  style = wxICON_INFORMATION | wxOK | wxCANCEL)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wxID_OK:
                self.RemoveSelectedItems()
            
        elif key == WXK_F5:
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
                                  AGNodeService.ServiceType)
        ret = dlg.ShowModal()

        if ret == wxID_OK:
            url = dlg.GetValue()
            if url not in self.recentNodeServiceList:
                self.recentNodeServiceList.append(url)
            
            # Attach (or fail)
            
            
            wxBeginBusyCursor()
            self.AttachToNode(AGNodeServiceIW(url))

            if not self.Connected():
                self.Error( "Could not attach to AGNodeService at " + url  )
                wxEndBusyCursor()
                return

            # Update the servicemanager and service lists
            self.UpdateUI()
            wxEndBusyCursor()
            
    def AttachToNode( self, nodeService ):
        """
        This method does the real work of attaching to a node service
        """

        # self.CheckCredentials()

        # Get proxy to the node service, if the url validates
        self.nodeServiceHandle = nodeService
        self.SetStatusText("Connected",1)
        self.EnableMenus(true)
      
    def LoadConfiguration( self, event ):
        """
        Load a configuration for the node service
        """
        configs = self.nodeServiceHandle.GetConfigurations()

        # Map display name to configurations
        configMap = {}
        for c in configs:
            displayName = c.name+" ("+c.type+")"
            configMap[displayName] = c

        d = wxSingleChoiceDialog( self, "Select a configuration file to load", 
                                  "Load Configuration Dialog", configMap.keys())
        ret = d.ShowModal()

        if ret == wxID_OK:
            conf = d.GetStringSelection()

            if len( conf ) == 0:
                self.Error( "No selection made" )
                return

            # Get correct config name
            if configMap.has_key:
                conf = configMap[conf].name

            try:
                if self.nodeServiceHandle.NeedMigrateNodeConfig(conf):
                    text ="%s should be migrated to %s; do you want to do this now?" % (conf,Version.GetVersion())
                    dlg = wxMessageDialog(self, text, "Confirm",
                                          style = wxICON_INFORMATION | wxOK | wxCANCEL)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret == wxID_OK:
                        self.nodeServiceHandle.MigrateNodeConfig(conf)
            except:
                log.exception("Exception migrating node config")


            config = None
            for c in configs:
                if conf == c.name:
                    config = c

            try:
                wxBeginBusyCursor()
                self.nodeServiceHandle.LoadConfiguration( config )
            except:
                log.exception("NodeManagementClientFrame.LoadConfiguration: Can not load configuration from node service")
                self.Error("Error loading node configuration %s" % (conf,))

            self.UpdateUI()
            wxEndBusyCursor()

    def StoreConfiguration( self, event ):
        """
        Store a node service configuration
        """

        # Get known configurations from the Node Service
        configs = self.nodeServiceHandle.GetConfigurations()

        # Prompt user to name the configuration
        d = StoreConfigDialog(self,-1,"Store Configuration", configs)
        ret = d.ShowModal()

        if ret == wxID_OK:
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
                    dlg = wxMessageDialog(self, text, "Confirm",
                                          style = wxICON_INFORMATION | wxOK | wxCANCEL)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret != wxID_OK:
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
                    wxBeginBusyCursor()
                    self.nodeServiceHandle.StoreConfiguration( config )
                except:
                    log.exception("Error storing node configuration %s" % (configName,))
                    self.Error("Error storing node configuration %s" % (configName,))

                # Set the default configuration
                if isDefault:
                    prefs = self.app.GetPreferences()
                    prefs.SetPreference(Preferences.NODE_CONFIG,configName)
                    
                wxEndBusyCursor()

        d.Destroy()


    def TimeToQuit(self, event):
        """
        Exit
        """
        self.Close(true)

    ############################
    ## VIEW menu
    ############################

    def UpdateUI( self, event=None ):
        """
        Update the service list (bring it into sync with the node service)
        """
        
        selections = self.GetSelectedItems()
        selectionUrls = map( lambda x: x.uri, selections)

        self.serviceManagers = self.nodeServiceHandle.GetServiceManagers()

        import urlparse
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("")    
        if self.serviceManagers:
          for serviceManager in self.serviceManagers:
            name = urlparse.urlsplit(serviceManager.uri)[1]
            sm = self.tree.AppendItem(root,name)
            self.tree.SetItemImage(sm, self.smImage,which=wxTreeItemIcon_Normal)
            self.tree.SetItemImage(sm, self.smImage, which=wxTreeItemIcon_Expanded)
            self.tree.SetItemData(sm,wxTreeItemData(serviceManager))
            services = AGServiceManagerIW( serviceManager.uri ).GetServices()
                        
            if services: 
              for service in services:
                s = self.tree.AppendItem(sm,service.name)
                self.tree.SetItemImage(s, self.svcImage, which = wxTreeItemIcon_Normal)
                self.tree.SetItemData(s,wxTreeItemData(service))
                #resource = AGServiceIW(service.uri).GetResource()
                #if resource:
                #    self.tree.SetItemText(s,resource.name,1)
                if AGServiceIW( service.uri ).GetEnabled():
                    status = "Enabled"
                else:
                    status = "Disabled"
                self.tree.SetItemText(s,status,2)
                
                if service.uri in selectionUrls:
                    self.tree.SelectItem(s)
                
            self.tree.Expand(sm)
            
            if serviceManager.uri in selectionUrls:
                self.tree.SelectItem(sm)
        self.tree.Expand(root)
    
    ############################
    ## HOST menu
    ############################
    def AddHost( self, event ):
        """
        Add a service manager to the node service
        """

        dlg = ServiceChoiceDialog(self,-1,'ServiceManager Dialog',
                                  self.recentServiceManagerList,
                                  AGServiceManager.ServiceType)
        ret = dlg.ShowModal()
        if ret == wxID_OK:

            url = dlg.GetValue()
            if url not in self.recentServiceManagerList:
                self.recentServiceManagerList.append(url)
            try:
                wxBeginBusyCursor()
                self.nodeServiceHandle.AddServiceManager( url )
            except:
                log.exception("Exception in AddHost")
                self.Error("Can not add service manager to node service.")

            # Update the service manager list
            self.UpdateUI()
            
            wxEndBusyCursor()

    def RemoveServiceManager( self, event ):
        """
        Remove a host from the node service
        """
        
        selections = self.GetSelectedServiceManagers()

        # Require a service manager to be selected
        if len(selections) == 0:
            self.Error( "No service manager selected!" )
            return

        # Find selected service manager and remove it
        wxBeginBusyCursor()
        try:
            index = -1
            for obj in selections:
                try:
                    self.nodeServiceHandle.RemoveServiceManager( obj.uri )
                except:
                    log.exception("Error removing service manager %s", self.serviceManagers[index].uri)

            # Update the service list
            self.UpdateUI()
        finally:
            wxEndBusyCursor()

    def ServiceManagerSelectedCB(self, event):
        index = self.serviceManagerList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
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
        
        selections = self.GetSelectedServiceManagers()

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
            wxBeginBusyCursor()
            servicePackages =  AGServiceManagerIW(serviceManager.uri).GetServicePackageDescriptions()
        except:
            log.exception("Exception getting service packages")
        wxEndBusyCursor()
        availServiceNames = map( lambda servicePkg: servicePkg.name, servicePackages )

        #
        # Prompt for service to add
        #
        dlg = wxSingleChoiceDialog( self, "Select Service to Add", "Add Service: Select Service",
                                    availServiceNames )

        dlg.SetSize(wxSize(300,200))
        ret = dlg.ShowModal()

        if ret == wxID_OK:
            #
            # Find the selected service description based on the name
            serviceToAdd = None
            serviceName = dlg.GetStringSelection()
            for servicePkg in servicePackages:
                if serviceName == servicePkg.name:
                    serviceToAdd = servicePkg
                    break

            if serviceToAdd == None:
                raise Exception("Can't add NULL service")

            try:
                #
                # Add the service
                #
                wxBeginBusyCursor()
                serviceDescription = AGServiceManagerIW(serviceManager.uri).AddService( serviceToAdd,
                                                                                        [], [],
                                                                                        self.app.GetPreferences().GetProfile())
                
                # Set identity
                #AGServiceIW(serviceDescription.uri).SetIdentity(self.app.GetPreferences().GetProfile())
                
#                 # Configure resource
#                 if serviceToAdd.resourceNeeded:
#                     service = AGServiceIW(serviceDescription.uri)
#                     resources = service.GetResources()
#                     resourceNames = map(lambda x:x.name,resources)
#                     if len(resources) > 0:
#                         log.info("Prompt for resource")
#                         log.debug("Resources: %s" % (resources,))
# 
#                         dlg = wxSingleChoiceDialog( self, 
#                                                     "Select resource for service", 
#                                                     "Add Service: Select Resource",
#                                                     resourceNames )
# 
#                         dlg.SetSize(wxSize(300,200))
# 
#                         ret = dlg.ShowModal()
# 
#                         if ret != wxID_OK:
#                             return
# 
#                         selectedResourceName = dlg.GetStringSelection()
# 
#                         foundResource = 0
#                         for r in resources:
#                             if r.name == selectedResourceName:
#                                 service.SetResource(r)
#                                 foundResource = 1
#                         if not foundResource:
#                             raise Exception("Unknown resource selected: %s", selectedResourceName)
#                     else:
#                         log.info("No resources for service")
            except:
                wxEndBusyCursor()
                log.exception( "Add Service failed:" + serviceToAdd.name)
                self.Error( "Add Service failed:" + serviceToAdd.name )
                return

            self.UpdateUI()
            wxEndBusyCursor()

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
            wxBeginBusyCursor()

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
            
        wxEndBusyCursor()
        

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
            wxBeginBusyCursor()
            # Disable all selected services
            index = -1
            for service in selections:
                self.nodeServiceHandle.SetServiceEnabled(service.uri,0)

            # Update the service list
            self.UpdateUI()
        except:
            log.exception("Error disabling service")
            self.Error("Error disabling service")

        wxEndBusyCursor()

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
            wxBeginBusyCursor()
            # Remove all selected services
            for s in selections:
                obj = self.tree.GetPyData(s)
                if isinstance(obj,AGServiceDescription):
                    smItem = self.tree.GetItemParent(s)
                    sm = self.tree.GetItemData(smItem).GetData()
                    AGServiceManagerIW( sm.uri ).RemoveService( obj )
                    self.tree.Delete(s)
                    selections.remove(s)

            # Update the service list
            self.UpdateUI()
        finally:
            wxEndBusyCursor()
            
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
            wxBeginBusyCursor()
            config = AGServiceIW( service.uri ).GetConfiguration()
        except:
            wxEndBusyCursor()
            log.exception("Service is unreachable at %s" % (service.uri,))
            self.Error("Service is unreachable at %s" % (service.uri,))
            return
            
        resource = AGServiceIW( service.uri ).GetResource()

        wxEndBusyCursor()
        if config:
            # Display the service configuration panel
            dlg = ServiceConfigurationDialog(self,-1,"Service Config Dialog",
                                             resource, 
                                             config)
            ret = dlg.ShowModal()
            if ret == wxID_OK:
            
                # Get config from the dialog and set it in the service
                config = dlg.GetConfiguration()
                wxBeginBusyCursor()
                try:
                    # Send the modified configuration to the service
                    AGServiceIW( service.uri ).SetConfiguration( config )
                except:
                    log.exception("Exception setting configuration")
                wxEndBusyCursor()
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
        wxMessageDialog( self, message, style = wxOK | wxICON_INFORMATION ).ShowModal()
        
    def PopupThatMenu(self, evt):
    
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
        
            
        menu = wxMenu()
        menu.Append(ID_SERVICE_ENABLE_ONE, "Enable", "Enable the selected service")
        menu.Append(ID_SERVICE_DISABLE_ONE, "Disable", "Disable the selected service")
        menu.Append(ID_SERVICE_CONFIGURE, "Configure...", "Configure the selected service")
        menu.Append(ID_SERVICE_REMOVE, "Remove", "Remove the selected service")

        # Get the Mouse Position on the Screen 
        (windowx, windowy) = wxGetMousePosition() 
        # Translate the Mouse's Screen Position to the Mouse's Control Position 
        pos = self.tree.ScreenToClientXY(windowx, windowy)
        posl = [ pos[0] + 155, pos[1] + 25 ]
        self.PopupMenu(menu,pos)

    def PopupHostMenu(self, evt):
        """
        Popup the service manager menu
        """
        
        menu = wxMenu()
        
        menu.Append(ID_SERVICE_ADD_SERVICE, "Add Service...", "Add a service")
        menu.AppendSeparator()
        menu.Append(ID_HOST_REMOVE, "Remove Service Manager", "Remove a service manager")

        # Get the Mouse Position on the Screen 
        (windowx, windowy) = wxGetMousePosition() 
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
            if not selType or isinstance(obj,selType):
                retList.append(obj)
            
        return retList
        
    def GetSelectedServiceManagers(self):
        return self.GetSelectedItems(AGServiceManagerDescription)

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
            


if __name__ == "__main__":
    
    app = wxPySimpleApp()

    # Service config dialog test
    resource = ResourceDescription("resource")
    config = []

    dlg = ServiceConfigurationDialog(None, -1, "Service Config Dialog", resource,config)
    ret = dlg.ShowModal()
    dlg.Destroy()
   
