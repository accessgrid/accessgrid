#-----------------------------------------------------------------------------
# Name:        NodeManagementUIClasses.py
# Purpose:
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: NodeManagementUIClasses.py,v 1.65 2004-05-21 05:39:15 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NodeManagementUIClasses.py,v 1.65 2004-05-21 05:39:15 turam Exp $"
__docformat__ = "restructuredtext en"
import sys

from wxPython.wx import *
from wxPython.lib.dialogs import wxMultipleChoiceDialog

# AG2 imports
from AccessGrid import Log
from AccessGrid import icons
from AccessGrid import Platform
from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid.hosting import Client
from AccessGrid.UIUtilities import AboutDialog
from AccessGrid.Types import Capability
from AccessGrid.AGParameter import ValueParameter, RangeParameter
from AccessGrid.AGParameter import OptionSetParameter
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid.AGNodeService import AGNodeServiceIW
from AccessGrid.AGServiceManager import AGServiceManagerIW
from AccessGrid.AGService import AGServiceIW
from AccessGrid.Types import AGResource

# imports for Debug menu; can be removed if Debug menu is removed
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation

log = Log.GetLogger(Log.NodeManagementUIClasses)
Log.SetDefaultLevel(Log.NodeManagementUIClasses, Log.WARN)

###
### MENU DEFS
###

ID_FILE_EXIT  = 100
ID_FILE_LOAD_CONFIG = 101
ID_FILE_STORE_CONFIG = 102

ID_VIEW_REFRESH = 200

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


class MultiTextFieldDialog(wxDialog):
    """
    MultiTextFieldDialog accepts a dictionary and presents its
    contents as label/textfield pairs in a dialog.  The GetData
    method returns a list of the values, possibly modified.
    """
    def __init__(self, parent, id, title, fieldNames ):

        wxDialog.__init__(self, parent, id, title, style =
                          wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)
              
        # Set up sizers
        gridSizer = wxFlexGridSizer(len(fieldNames), 2, 5, 5)
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxHORIZONTAL)
        sizer2.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
       
        gridSizer.AddGrowableCol(1)

        # Create label/textfield pairs for field names
        self.textCtrlList = []
        for name,value in fieldNames.items():
            labelCtrl = wxStaticText( self, -1, name)
            textCtrl = wxTextCtrl( self, -1, value, size = wxSize(200, 20))
            self.textCtrlList.append( textCtrl )
                    
            gridSizer.Add( labelCtrl)
            gridSizer.Add( textCtrl, 0, wxEXPAND)
          
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
        
    def GetData(self):
        # Get data from textfields
        fieldValues = []
        for textCtrl in self.textCtrlList:
            fieldValues.append( textCtrl.GetValue() )
        return fieldValues

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
        self.configList = wxListBox(self,-1, style=wxLB_SINGLE, choices=choices)
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
        self.configText.SetValue( event.GetString() )
        self.okButton.Enable(true)

    def __TextEnteredCallback(self,event):

        # Enable the ok button if text in text field
        if self.configText.GetValue():
            self.okButton.Enable(true)
        else:
            self.okButton.Enable(false)

    def GetValue(self):
        # Get value of textfield and checkbox
        return (self.configText.GetValue(), self.defaultCheckbox.IsChecked())


class ServiceListCtrl( wxListCtrl ):

    def __init__(self, parent, ID, pos=wxDefaultPosition,
                  size=wxDefaultSize, style=wxLC_REPORT):
        listId = wxNewId()
        wxListCtrl.__init__(self, parent, listId, pos, size, style=style)
        self.InsertColumn( 0, "Service Name", width=100 )
        self.InsertColumn( 1, "Resource", width=wxLIST_AUTOSIZE )
        self.InsertColumn( 2, "Status", width=wxLIST_AUTOSIZE )

        bmap = icons.getDefaultServiceBitmap()
        imageList = wxImageList( bmap.GetWidth(), bmap.GetHeight() )
        imageList.Add( bmap )
        self.AssignImageList( imageList, wxIMAGE_LIST_NORMAL)
        
        self.colWidths = [ .4, .4, .2 ]
        
        EVT_LIST_COL_END_DRAG(self,listId,self.OnColEndDrag)

        if IsWindows():
            # This breaks on linux
            EVT_SIZE(self, self.OnSize)

        self.Layout()

    def OnSize(self, event):
        """
        Sets correct column widths.
        """
        w,h = self.GetSize()
        numCols = self.GetColumnCount()
        for i in range(numCols):
            self.SetColumnWidth(i, w * self.colWidths[i] )
            
    def OnColEndDrag(self,event):
        """
        Sets correct column widths after drag
        """
        w,h = self.GetSize()
        numCols = self.GetColumnCount()
        total = 0
        for i in range(numCols-1):
            self.colWidths[i] = self.GetColumnWidth(i) / float(w)
            total += self.colWidths[i]
            
        # Make the last column take all available space
        i = numCols-1
        self.colWidths[i] = 1.0 - total
        self.SetColumnWidth(i,w * self.colWidths[i])
        
              
class ServiceConfigurationPanel( wxPanel ):
    """
    A panel that displays service configuration parameters based on
    their type.
    """
    def __init__( self, parent, ID, pos=wxDefaultPosition, size=(400,400), style=0 ):
        wxPanel.__init__( self, parent, ID, pos, size, style )
        self.panel = self
        self.callback = None
        self.CentreOnParent()
        
        self.config = None
        self.resource = None

    def SetResource(self,resourceIn):
        self.resource = resourceIn
        if not resourceIn or resourceIn == "None":
            resource = "None"
        else:
            resource = resourceIn
            
            
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
            pComp = wxTextCtrl( self, -1, self.resource, size = wxSize(300, 20))
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

        wxDialog.__init__(self, parent, id, title, style =
                          wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)

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
        self.services = []
        self.nodeServiceHandle = None

        self.app = Toolkit.Application.instance()

        menuBar = wxMenuBar()

        ## FILE menu

        self.fileMenu = wxMenu()
        self.fileMenu.Append(ID_FILE_ATTACH, "Attach to Node...", 
                             "Connect to a NodeService")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_FILE_LOAD_CONFIG, "Load Configuration...", 
                             "Load a NodeService Configuration")
        self.fileMenu.Append(ID_FILE_STORE_CONFIG, "Store Configuration...", 
                             "Store a NodeService Configuration")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(ID_FILE_EXIT, "E&xit", "Terminate the program")
        menuBar.Append(self.fileMenu, "&File");

        ## VIEW menu

        self.viewMenu = wxMenu()
        self.viewMenu.Append(ID_VIEW_REFRESH, "Update", "Synch to the current NodeService state")
        menuBar.Append(self.viewMenu, "&View");

        ## HOST menu
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

        mainsz = wxBoxSizer( wxVERTICAL )
        self.SetSizer( mainsz )

        hortizontalSizer = wxBoxSizer( wxHORIZONTAL )
        mainsz.Add( hortizontalSizer, -1, wxEXPAND )
        
        self.splitter = wxSplitterWindow(self,-1,style=wxSP_3D)
        self.splitter.SetSize(self.GetSize())
        
        #
        # Create Hosts panel
        #

        hostPanel = wxPanel( self.splitter, -1 )
        statBox = wxStaticBox(hostPanel, -1, "ServiceManagers")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        hortizontalSizer.Add( hostPanel, -1, wxEXPAND )
        hostPanel.SetSizer( statBoxSizer )
        self.hostList = wxListCtrl( hostPanel, -1, style=wxLC_LIST )
        
        statBoxSizer.Add( self.hostList, -1, wxEXPAND )
        
        # Handle events in the service managers list
        EVT_LIST_ITEM_RIGHT_CLICK(self, self.hostList.GetId(), self.PopupHostMenu)
        EVT_LIST_ITEM_SELECTED( self, self.hostList.GetId(), self.ServiceManagerSelectedCB )
        EVT_LIST_ITEM_DESELECTED( self, self.hostList.GetId(), self.UpdateServiceList )
   
        #
        # Create Services panel
        #

        servicesPanel = wxPanel( self.splitter, -1)
        statBox = wxStaticBox(servicesPanel, -1, "Services")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        hortizontalSizer.Add( servicesPanel, -1, wxEXPAND )
        servicesPanel.SetSizer( statBoxSizer )
        self.serviceList = ServiceListCtrl( servicesPanel, wxNewId(), 
                                            style=wxLC_REPORT )

        statBoxSizer.Add( self.serviceList, -1, wxEXPAND )

        # Create the status bar
        self.CreateStatusBar(2)
        self.SetStatusText("This is the statusbar",1)


        # Handle events in the services list
        EVT_LIST_ITEM_RIGHT_CLICK(self, self.serviceList.GetId(), self.PopupServiceMenu)
        EVT_LIST_ITEM_ACTIVATED(self, self.serviceList.GetId(), self.ConfigureService )
       
        # Associate menu items with callbacks
        EVT_MENU(self, ID_FILE_ATTACH            ,  self.Attach )
        EVT_MENU(self, ID_FILE_EXIT              ,  self.TimeToQuit )
        EVT_MENU(self, ID_FILE_LOAD_CONFIG       ,  self.LoadConfiguration )
        EVT_MENU(self, ID_FILE_STORE_CONFIG      ,  self.StoreConfiguration )
        EVT_MENU(self, ID_HELP_ABOUT             ,  self.OnAbout)
        EVT_MENU(self, ID_HOST_ADD               ,  self.AddHost )
        EVT_MENU(self, ID_HOST_REMOVE            ,  self.RemoveHost )
        EVT_MENU(self, ID_SERVICE_ADD_SERVICE    ,  self.AddService )
        EVT_MENU(self, ID_SERVICE_CONFIGURE      ,  self.ConfigureService )
        EVT_MENU(self, ID_SERVICE_REMOVE         ,  self.RemoveService )
        EVT_MENU(self, ID_SERVICE_ENABLE         ,  self.EnableServices )
        EVT_MENU(self, ID_SERVICE_ENABLE_ONE     ,  self.EnableService )
        EVT_MENU(self, ID_SERVICE_DISABLE        ,  self.DisableServices )
        EVT_MENU(self, ID_SERVICE_DISABLE_ONE    ,  self.DisableService )
        EVT_MENU(self, ID_VIEW_REFRESH           ,  self.UpdateUI )
        
        self.menuBar = menuBar
        
        self.EnableMenus(false)
        
        
        EVT_SIZE(self, self.OnSize)
        self.splitter.SetMinimumPaneSize(10)
        self.splitter.SplitVertically(hostPanel,servicesPanel,130)
        

    def OnSize(self,event):
        self.splitter.SetSize(self.GetSize())
        self.serviceList.OnSize(None)
        

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

        # Prompt for node service location
        names = { "Hostname" : "", "Port":"" }
        dlg = MultiTextFieldDialog( self, -1, \
            "Node Attach Dialog", names )

        ret = dlg.ShowModal()

        if ret == wxID_OK:
            host, port = dlg.GetData()

            # Detect bad host/port
            host = host.strip()
            port = port.strip()
            if len(host) == 0 or len(port) == 0:
                self.Error( "Host and Port are required" )
                return

            if host == "localhost":
                host = self.app.GetHostname()

            # Attach (or fail)
            uri = 'https://%s:%s/NodeService' % (host,port)
            self.AttachToNode( uri )
            if not self.Connected():
                self.Error( "Could not attach to AGNodeService at " + uri  )
                return

            # Update the servicemanager and service lists
            self.UpdateHostList()
            self.UpdateServiceList()
            
    def AttachToNode( self, nodeServiceUri ):
        """
        This method does the real work of attaching to a node service
        """

        self.CheckCredentials()

        # Get proxy to the node service, if the url validates
        try:
            self.nodeServiceHandle = AGNodeServiceIW( nodeServiceUri )
            self.nodeServiceHandle.IsValid()
            self.SetStatusText("Connected",1)
            self.EnableMenus(true)
        except:
            self.SetStatusText("Not Connected",1)
            self.EnableMenus(false)
            self.ClearUI()
            log.exception("NodeManagementClientFrame.AttachToNode: Invalid Node Service URI: %s" % nodeServiceUri)

    def LoadConfiguration( self, event ):
        """
        Load a configuration for the node service
        """
        configs = self.nodeServiceHandle.GetConfigurations()

        d = wxSingleChoiceDialog( self, "Select a configuration file to load", "Load Configuration Dialog", configs.data )
        ret = d.ShowModal()

        if ret == wxID_OK:
            conf = d.GetStringSelection()

            if len( conf ) == 0:
                self.Error( "No selection made" )
                return

            try:
                self.nodeServiceHandle.LoadConfiguration( conf )
            except:
                log.exception("NodeManagementClientFrame.LoadConfiguration: Can not load configuration from node service")
                self.Error("Error loading node configuration %s" % (conf,))

            self.UpdateHostList()
            #self.UpdateServiceList()

    def StoreConfiguration( self, event ):
        """
        Store a node service configuration
        """

        # Get known configurations from the Node Service
        configs = self.nodeServiceHandle.GetConfigurations().data

        # Prompt user to name the configuration
        d = StoreConfigDialog(self,-1,"Store Configuration", configs )
        ret = d.ShowModal()

        if ret == wxID_OK:
            ret = d.GetValue()
            if ret:
                (configName,isDefault) = ret
                
                # Handle error cases
                if len( configName ) == 0:
                    self.Error( "Invalid config name specified (%s)", configName )
                    return

                # Confirm overwrite
                if configName in configs:
                    text ="Overwrite %s?" % (configName,)
                    dlg = wxMessageDialog(self, text, "Confirm",
                                          style = wxICON_INFORMATION | wxOK | wxCANCEL)
                    ret = dlg.ShowModal()
                    dlg.Destroy()
                    if ret != wxID_OK:
                        return

                # Store the configuration
                try:
                    self.nodeServiceHandle.StoreConfiguration( configName )
                except:
                    log.exception("Error storing node configuration %s" % (configName,))
                    self.Error("Error storing node configuration %s" % (configName,))

                # Set the default configuration
                if isDefault:
                    self.nodeServiceHandle.SetDefaultConfiguration( configName )

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
        Update the service manager and service lists
        """

        # Update the service manager list
        # (this call updates the services list, too)
        try:
            self.UpdateHostList()
        except Exception:
            log.exception("NodeManagementClientFrame.UpdateUI: Can not update host list.")
            self.Error("Error updating UI")


    ############################
    ## HOST menu
    ############################
    def AddHost( self, event ):
        """
        Add a service manager to the node service
        """

        # Prompt for service manager location
        names = { "Hostname" : "", "Port":"" }
        dlg = MultiTextFieldDialog( self, -1, \
            "Add Service Manager Dialog", names )
     
        ret = dlg.ShowModal()
        if ret == wxID_OK:

            host,port = dlg.GetData()

            # Detect bad host/port
            host = host.strip()
            port = port.strip()
            if len(host) == 0 or len(port) == 0:
                self.Error( "Host and Port are required" )
                return

            if host == "localhost":
                host = self.app.GetHostname()

            # Add the service manager to the node service
            uri = 'https://%s:%s/ServiceManager' % (host,port)
            name = '%s:%s' % (host,port)
            try:
                serviceManagerDesc = AGServiceManagerDescription( name, uri )
                self.nodeServiceHandle.AddServiceManager( serviceManagerDesc )
            except:
                log.exception("Exception in AddHost")
                self.Error("Can not add service manager to node service.")
                self.ClearUI()
                self.UpdateHostList()
                return

            # Update the service manager list
            self.UpdateHostList()

    def RemoveHost( self, event ):
        """
        Remove a host from the node service
        """

        # Require a service manager to be selected
        if self.hostList.GetSelectedItemCount() == 0:
            self.Error( "No host selected!" )
            return

        # Find selected service manager and remove it
        index = -1
        for i in range( self.hostList.GetSelectedItemCount() ):
            index = self.hostList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            self.nodeServiceHandle.RemoveServiceManager( self.serviceManagers[index] )

        # Update the service manager list
        self.UpdateHostList()

    def UpdateHostList( self, event=None ):
        """
        Update the service manager list
        """

        # Find selected service managers, to retain selections after update
        selectedServiceManagerUri = None

       
            
        if self.hostList.GetSelectedItemCount() != 0:
            index = -1
            index = self.hostList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            selectedServiceManagerUri = self.serviceManagers[index].uri

        # Empty the list
        self.hostList.DeleteAllItems()

        # Add service managers to the list
        i = 0

        self.serviceManagers = self.nodeServiceHandle.GetServiceManagers()
        for serviceManager in self.serviceManagers:
            item = self.hostList.InsertStringItem( i, serviceManager.name )

            # Retain selection in host list
            if serviceManager.uri == selectedServiceManagerUri:
                self.hostList.SetItemState( item, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED )

            i = i + 1

        if self.hostList.GetSelectedItemCount() == 0:
            # if no host is selected, select the first item
            try:
                self.hostList.SetItemState(0, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)
            except:
                pass
            
        # Update the service list
        #self.UpdateServiceList()

    def ServiceManagerSelectedCB(self, event):
        index = self.hostList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
        uri = self.serviceManagers[index].uri
        try:
            AGServiceManagerIW(uri).IsValid()
        except:
            log.exception("Service Manager is unreachable (%s)" % (uri,))
            self.Error("Service Manager is unreachable (%s)" % (uri,))
            return

        self.UpdateServiceList()

    ############################
    ## SERVICE menu
    ############################

    def AddService( self, event=None ):
        """
        Add a service to the node service
        """

        # Require a single host to be selected
        if self.hostList.GetSelectedItemCount() == 0:
            self.Error( "No Service Manager selected for service!")
            return
        if self.hostList.GetSelectedItemCount() > 1:
            self.Error("Multiple hosts selected")
            return

        # Determine the selected host
        index = self.hostList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
        serviceManager = self.serviceManagers[index]

        # Get services available
        availServices =  self.nodeServiceHandle.GetAvailableServices()
        availServiceNames = map( lambda serviceDesc: serviceDesc.name, availServices )

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
            for service in availServices:
                if serviceName == service.name:
                    serviceToAdd = service
                    break

            if serviceToAdd == None:
                raise Exception("Can't add NULL service")

            #
            # Prompt for resource to assign
            #
            resourceToAssign = AGResource()
            resources = AGServiceManagerIW( serviceManager.uri ).GetResources()
            if len(resources) > 0:

                # Find resources applicable to this service
                applicableResources = []
                for resource in resources:
                    for cap in serviceToAdd.capabilities:
                        if resource.role == cap.role and resource.type == cap.type:
                            applicableResources.append( resource )

                if len(applicableResources) > 0:
                    log.info("%d resources found; prompt", len(applicableResources))
                    choices = map( lambda res: res.resource, applicableResources )
                    dlg = wxSingleChoiceDialog( self, "Select resource for service", "Add Service: Select Resource",
                           choices )

                    dlg.SetSize(wxSize(300,200))

                    ret = dlg.ShowModal()

                    if ret != wxID_OK:
                        return

                    selectedResource = dlg.GetStringSelection()

                    for resource in applicableResources:
                        if selectedResource == resource.resource:
                            resourceToAssign = resource
                            break
                else:
                    log.info("No applicable resources found")


            try:
                #
                # Add the service
                #
                self.nodeServiceHandle.AddService( serviceToAdd,
                               serviceManager.uri,
                               resourceToAssign,
                               [] )
            except:
                log.exception( "Add Service failed:" + serviceToAdd.name)
                self.Error( "Add Service failed:" + serviceToAdd.name )

            self.UpdateServiceList()

    def EnableService( self, event=None ):
        """
        Enable the selected service(s)
        """

        # Require a service to be selected
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        try:

            # Enable all selected services
            index = -1
            for i in range( self.serviceList.GetSelectedItemCount() ):
                index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
                log.debug("NodeManagementClientFrame.EnableService: Enabling Service: %s" %self.services[index].name)
                self.nodeServiceHandle.SetServiceEnabled(self.services[index].uri, 1)

            # Update the services list
            self.UpdateServiceList()

        except:
            log.exception("Error enabling service")
            self.Error("Error enabling service")

    def EnableServices( self, event ):
        """
        Enable all known services
        """
        services = self.nodeServiceHandle.GetServices()
        for service in services:
            self.nodeServiceHandle.SetServiceEnabled(service.uri,1)

        self.UpdateServiceList()

    def DisableService( self, event=None ):
        """
        Disable the selected service(s)
        """

        # Require a service to be selected
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        try:
            # Disable all selected services
            index = -1
            for i in range( self.serviceList.GetSelectedItemCount() ):
                index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
                self.nodeServiceHandle.SetServiceEnabled(self.services[index].uri,0)

            # Update the service list
            self.UpdateServiceList()
        except:
            log.exception("Error disabling service")
            self.Error("Error disabling service")


    def DisableServices( self, event ):
        """
        Disable all known services
        """
        svcs = self.nodeServiceHandle.GetServices()
        for svc in svcs:
            self.nodeServiceHandle.SetServiceEnabled(svc.uri,0)

        self.UpdateServiceList()

    def RemoveService( self, event ):
        """
        Remove the selected service(s)
        """

        # Require a service to be selected
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        # Remove all selected services
        index = -1
        for i in range( self.serviceList.GetSelectedItemCount() ):
            index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            AGServiceManagerIW( self.services[index].serviceManagerUri ).RemoveService( self.services[index] )

        # Update the service list
        self.UpdateServiceList()

    def ConfigureService( self, event=None ):
        """
        Configure the selected service
        """

        # Require a single service to be selected
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return
        if self.serviceList.GetSelectedItemCount() > 1:
            self.Error("Multiple services selected")
            return

        # Retrieve the service configuration
        index = self.serviceList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )

        # Trap service unreachable
        try:
            AGServiceIW( self.services[index].uri ).IsValid()
        except:
            log.exception("Service is unreachable at %s" % (self.services[index].uri,))
            self.Error("Service is unreachable at %s" % (self.services[index].uri,))
            return
            
        # Get configuration
        config = AGServiceIW( self.services[index].uri ).GetConfiguration()
        resource = AGServiceIW( self.services[index].uri ).GetResource()

        if not config:
            self.Error("Service has no configurable options")
        else:
            # Display the service configuration panel
            dlg = ServiceConfigurationDialog(self,-1,"Service Config Dialog",
                                             resource.resource, 
                                             config)
            ret = dlg.ShowModal()
            if ret == wxID_OK:
            
                # Get config from the dialog and set it in the service
                config = dlg.GetConfiguration()
                self.SetConfiguration( config )


    def SetConfiguration( self, serviceConfig ):
        """
        Configure the service according to the service configuration panel
        """

        # Require a service to be selected (this error should never occur)
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        # Determine the selected service
        index = self.serviceList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )

        # Send the modified configuration to the service
        AGServiceIW( self.services[index].uri ).SetConfiguration( serviceConfig )


    def UpdateServiceList( self, event=None ):
        """
        Update the service list (bring it into sync with the node service)
        """
        self.serviceList.DeleteAllItems()

        index = -1
        indices = []
        for i in range( self.hostList.GetSelectedItemCount() ):
            index = self.hostList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            indices.append( index )

        if len(self.serviceManagers) > 0 and index >= 0:
            for index in indices:
                self.services = AGServiceManagerIW( self.serviceManagers[index].uri ).GetServices()
                for svc in self.services:
                    svccfg = AGServiceIW(svc.uri).GetConfiguration()
                    itemindex = self.serviceList.InsertStringItem( i, svc.name )
                    self.serviceList.SetItemImage( itemindex, 0, 0 )
                    
                    resource = AGServiceIW(svc.uri).GetResource()
                    if resource.resource:
                        self.serviceList.SetStringItem( i,1, resource.resource )
                    else:
                        self.serviceList.SetStringItem( i,1, "" )
                    try:
                        if AGServiceIW( svc.uri ).GetEnabled() == 1:
                            self.serviceList.SetStringItem( i,2, "Enabled" )
                        else:
                            self.serviceList.SetStringItem( i,2, "Disabled" )
                    except:
                        log.exception("NodeManagementClientFrame.UpdateServiceList")
                    i = i + 1


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
        
    def PopupServiceMenu(self, evt):
        """
        Popup the service menu
        """
        list = evt.GetEventObject()
        # This does not work, bug?
        # pos = list.ClientToScreen( evt.GetPoint() )
        pos = evt.GetPoint() + wxPoint(240, 20)
        self.PopupMenu(self.serviceMenu, pos)

    def PopupHostMenu(self, evt):
        """
        Popup the service manager menu
        """
        # Place the menu next to the mouse position.
        list = evt.GetEventObject()
        
        # This does not work, bug?
        #pos = list.ClientToScreen( evt.GetPoint() )
        pos = evt.GetPoint() + wxPoint(20, 20)
        self.PopupMenu(self.serviceManagersMenu, pos)

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
        self.hostList.DeleteAllItems()
        self.serviceList.DeleteAllItems()


if __name__ == "__main__":
    
    app = wxPySimpleApp()

    # Service config dialog test
    resource = AGResource()
    resource.resource = "resource"
    config = []

    dlg = ServiceConfigurationDialog(None, -1, "Service Config Dialog", config)
    ret = dlg.ShowModal()
    dlg.Destroy()
   
