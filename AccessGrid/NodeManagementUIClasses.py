#-----------------------------------------------------------------------------
# Name:        NodeManagementUIClasses.py
# Purpose:
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: NodeManagementUIClasses.py,v 1.48 2003-10-23 21:35:07 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: NodeManagementUIClasses.py,v 1.48 2003-10-23 21:35:07 lefvert Exp $"
__docformat__ = "restructuredtext en"

import sys

from wxPython.wx import *
from wxPython.lib.dialogs import wxMultipleChoiceDialog

# AG2 imports
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.hosting.pyGlobus.Utilities import GetHostname
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType

from AccessGrid.Types import Capability, ServiceConfiguration
from AccessGrid.AGParameter import ValueParameter, RangeParameter, OptionSetParameter, CreateParameter
from AccessGrid.Descriptions import AGServiceManagerDescription
from AccessGrid import icons
from AccessGrid import Platform
from AccessGrid.UIUtilities import AboutDialog
from AccessGrid import Toolkit
from AccessGrid.Platform import isWindows

# imports for Debug menu; can be removed if Debug menu is removed
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import MulticastNetworkLocation

import logging, logging.handlers
log = logging.getLogger("AG.NodeManagementUIClasses")
log.setLevel(logging.WARN)



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
ID_SERVICE_GET_CONFIG = 402
ID_SERVICE_REMOVE = 403
ID_SERVICE_ENABLE = 404
ID_SERVICE_ENABLE_ONE = 405
ID_SERVICE_DISABLE = 406
ID_SERVICE_DISABLE_ONE = 407

ID_VENUE_ARGONNE = 500
ID_VENUE_LOBBY = 501
ID_VENUE_LOCAL = 502
ID_VENUE_TESTROOM = 503

ID_DUM = 600

ID_HELP_ABOUT = 701


def BuildServiceManagerMenu( ):
    """
    Used in the pulldown and popup menus to display the service manager menu
    """
    menu = wxMenu()
    menu.Append(ID_HOST_ADD, "Add...", "Add Service Manager")
    menu.Append(ID_HOST_REMOVE, "Remove", "Remove Service Manager")
    return menu

def BuildServiceMenu( ):
    """
    Used in the pulldown and popup menus to display the service menu
    """
    svcmenu = wxMenu()
    svcmenu.Append(ID_SERVICE_ADD_SERVICE, "Add...", "Add Service")
    svcmenu.Append(ID_SERVICE_REMOVE, "Remove", "Remove Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_ENABLE_ONE, "Enable", "Enable Service")
    svcmenu.Append(ID_SERVICE_DISABLE_ONE, "Disable", "Disable Service")
    svcmenu.AppendSeparator()
    svcmenu.Append(ID_SERVICE_GET_CONFIG, "Configure...", "Configure")
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
        self.InsertColumn( 0, "Service Name", width=wxLIST_AUTOSIZE )
        self.InsertColumn( 1, "Status", width=wxLIST_AUTOSIZE )

        bmap = icons.getDefaultServiceBitmap()
        imageList = wxImageList( bmap.GetWidth(), bmap.GetHeight() )
        imageList.Add( bmap )
        self.AssignImageList( imageList, wxIMAGE_LIST_NORMAL)

        if isWindows():
            # This breaks on linux
            EVT_SIZE(self, self.OnSize)

        self.Layout()

    def OnSize(self, event):
        """
        Sets correct column widths.
        """
        w,h = self.GetClientSizeTuple()
        self.SetColumnWidth(0, w*(0.70) )
        self.SetColumnWidth(1, w*(0.30) )
              
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

    def SetConfiguration( self, serviceConfig ):
        self.config = serviceConfig
        self.guiComponents = []

        rows = len(serviceConfig.parameters)

        self.boxSizer = wxBoxSizer(wxHORIZONTAL)

        self.panelSizer = wxFlexGridSizer( rows, 2, 5, 5 ) #rows, cols, hgap, vgap
        self.panelSizer.AddGrowableCol(1)
        
        pt = wxStaticText( self, -1, "Resource", style=wxALIGN_LEFT)
        if serviceConfig.resource == "None":
            resource = "None"
        else:
            resource = serviceConfig.resource.resource
        pComp = wxTextCtrl( self, -1, resource, size = wxSize(300, 20))
        pComp.SetEditable( false )

        self.panelSizer.Add( pt)
        self.panelSizer.Add( pComp, 0, wxEXPAND )
        self.guiComponents.append( pComp )

        pt = wxStaticText( self, -1, "Executable", style=wxALIGN_LEFT )
        pComp = wxTextCtrl( self, -1, serviceConfig.executable )

        self.panelSizer.Add( pt )
        self.panelSizer.Add( pComp, 0, wxEXPAND )
        self.guiComponents.append( pComp )

        for parameter in serviceConfig.parameters:
            pt = wxStaticText( self, -1, parameter.name, style=wxALIGN_LEFT )
            self.panelSizer.Add(pt, -1, wxEXPAND)
            
            pComp = None
            if parameter.TYPE == RangeParameter.TYPE:
                pComp = wxSlider( self, -1, parameter.value, parameter.low, parameter.high, style = wxSL_LABELS )
                
            elif parameter.TYPE == OptionSetParameter.TYPE:
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
        #self.panel.Layout()
        #self.panel.Fit()

    def GetConfiguration( self ):

        # build modified configuration from ui

        self.config.executable = self.guiComponents[1].GetValue()

        for i in range( 2, len(self.guiComponents) ):
            parmindex = i-2
            if isinstance( self.guiComponents[i], wxRadioBox ):
                self.config.parameters[parmindex].value = self.guiComponents[i].GetStringSelection()
            else:
                self.config.parameters[parmindex].value = self.guiComponents[i].GetValue()

        return self.config

    def SetCallback( self, callback ):
        self.callback = callback

    def Cancel(self, event):
        self.parent.Destroy()

class ServiceConfigurationDialog(wxDialog):
    """
    """
    def __init__(self, parent, id, title, serviceConfig ):

        wxDialog.__init__(self, parent, id, title, style =
                          wxDEFAULT_DIALOG_STYLE|wxRESIZE_BORDER)

        # Set up sizers
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        self.serviceConfigPanel = ServiceConfigurationPanel( self, -1 )
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

#FIXME - decide whether to use status bar
        """
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")
        """

        self.SetTitle(title)
        self.SetIcon(icons.getAGIconIcon())
        self.serviceManagers = []
        self.services = []
        self.nodeServiceHandle = Client.Handle("")

        self.app = Toolkit.GetApplication()

        menuBar = wxMenuBar()

        ## FILE menu

        menu = wxMenu()
        menu.Append(ID_FILE_ATTACH, "Attach to Node...", "Attach")
        menu.AppendSeparator()
        menu.Append(ID_FILE_LOAD_CONFIG, "Load Configuration...", "Load Configuration")
        menu.Append(ID_FILE_STORE_CONFIG, "Store Configuration...", "Store Configuration")
        menu.AppendSeparator()
        menu.Append(ID_FILE_EXIT, "E&xit", "Terminate the program")
        menuBar.Append(menu, "&File");

        ## VIEW menu

        viewmenu = wxMenu()
        viewmenu.Append(ID_VIEW_REFRESH, "Update", "Update")
        menuBar.Append(viewmenu, "&View");

        ## HOST menu
        menu = BuildServiceManagerMenu()
        menuBar.Append(menu, "&ServiceManager");
        self.hostMenu = menu
        
        ## SERVICE menu

        menu = BuildServiceMenu()
        menuBar.Append(menu, "&Service");
        self.serviceMenu = menu
        
        ## DEBUG menu
        """
        debugMenu = wxMenu()
        debugMenu.Append(ID_VENUE_TESTROOM, "Go to Test Room", "Dum")
        debugMenu.Append(ID_VENUE_ARGONNE, "Go to Argonne", "Dum")
        debugMenu.Append(ID_VENUE_LOBBY, "Goto Lobby", "")
        debugMenu.Append(ID_VENUE_LOCAL, "Goto Local", "")
        debugMenu.AppendSeparator()
        debugMenu.Append(ID_DUM, "Kill Services", "")
        menuBar.Append(debugMenu, "&Debug");
        """

        ## HELP menu
        helpMenu = wxMenu()
        helpMenu.Append(ID_HELP_ABOUT, "&About",
                    "More information about this program")
        menuBar.Append(helpMenu, "&Help");

        self.SetMenuBar(menuBar)

        mainsz = wxBoxSizer( wxVERTICAL )
        self.SetSizer( mainsz )

        hortizontalSizer = wxBoxSizer( wxHORIZONTAL )
        mainsz.Add( hortizontalSizer, -1, wxEXPAND )

        #
        # Create Hosts panel
        #
        statBoxPanel = wxPanel( self, -1 )
        statBox = wxStaticBox(statBoxPanel, -1, "ServiceManagers")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        hortizontalSizer.Add( statBoxPanel, -1, wxEXPAND )
        statBoxPanel.SetSizer( statBoxSizer )
        self.hostList = wxListCtrl( statBoxPanel, -1, style=wxLC_LIST )
        statBoxSizer.Add( self.hostList, -1, wxEXPAND )

        # Handle events in the service managers list
        EVT_LIST_ITEM_RIGHT_CLICK(self, self.hostList.GetId(), self.PopupHostMenu)
        EVT_LIST_ITEM_SELECTED( self, self.hostList.GetId(), self.ServiceManagerSelectedCB )
        EVT_LIST_ITEM_DESELECTED( self, self.hostList.GetId(), self.UpdateServiceList )
   
        #
        # Create Services panel
        #
        statBoxPanel = wxPanel( self, wxNewId())
        statBox = wxStaticBox(statBoxPanel, -1, "Services")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        hortizontalSizer.Add( statBoxPanel, -1, wxEXPAND )
        statBoxPanel.SetSizer( statBoxSizer )
        self.serviceList = ServiceListCtrl( statBoxPanel, wxNewId(), style=wxLC_REPORT )

        statBoxSizer.Add( self.serviceList, -1, wxEXPAND )

        # Handle events in the services list
        EVT_LIST_ITEM_RIGHT_CLICK(self, self.serviceList.GetId(), self.PopupServiceMenu)
        EVT_LIST_ITEM_ACTIVATED(self, self.serviceList.GetId(), self.GetServiceConfiguration )
       
        # Associate menu items with callbacks
        EVT_MENU(self, ID_FILE_ATTACH            ,  self.Attach )
        EVT_MENU(self, ID_FILE_EXIT              ,  self.TimeToQuit )
        EVT_MENU(self, ID_FILE_LOAD_CONFIG       ,  self.LoadConfiguration )
        EVT_MENU(self, ID_FILE_STORE_CONFIG      ,  self.StoreConfiguration )
        EVT_MENU(self, ID_HELP_ABOUT             ,  self.OnAbout)
        EVT_MENU(self, ID_HOST_ADD               ,  self.AddHost )
        EVT_MENU(self, ID_HOST_REMOVE            ,  self.RemoveHost )
        EVT_MENU(self, ID_SERVICE_ADD_SERVICE    ,  self.AddService )
        EVT_MENU(self, ID_SERVICE_GET_CONFIG     ,  self.GetServiceConfiguration )
        EVT_MENU(self, ID_SERVICE_REMOVE         ,  self.RemoveService )
        EVT_MENU(self, ID_SERVICE_ENABLE         ,  self.EnableServices )
        EVT_MENU(self, ID_SERVICE_ENABLE_ONE     ,  self.EnableService )
        EVT_MENU(self, ID_SERVICE_DISABLE        ,  self.DisableServices )
        EVT_MENU(self, ID_SERVICE_DISABLE_ONE    ,  self.DisableService )
        EVT_MENU(self, ID_VENUE_ARGONNE          ,  self.GotoArgonne )
        EVT_MENU(self, ID_VENUE_LOBBY            ,  self.GotoLobby )
        EVT_MENU(self, ID_VENUE_LOCAL            ,  self.GotoLocal )
        EVT_MENU(self, ID_VENUE_TESTROOM         ,  self.GotoTestRoom )
        EVT_MENU(self, ID_VIEW_REFRESH           ,  self.UpdateUI )

    def Connected(self):
        try:
            self.nodeServiceHandle.IsValid()
            return 1
        except:
            return 0

   

    ############################
    ## FILE menu
    ############################

    def Attach( self, event ):
        """
        Attach to a node service
        """

        # Prompt for service manager location
        names = { "Hostname" : "", "Port":"11000" }
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
                host = GetHostname()

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
            self.nodeServiceHandle = Client.Handle( nodeServiceUri )
            self.nodeServiceHandle.IsValid()
            self.SetTitle( "Access Grid Node Management - Connected" )
        except:
            self.SetTitle( "Access Grid Node Management" )
            self.ClearUI()
            log.exception("NodeManagementClientFrame.AttachToNode: Invalid Node Service URI: %s" % nodeServiceUri)

    def LoadConfiguration( self, event ):
        """
        Load a configuration for the node service
        """
        configs = self.nodeServiceHandle.GetProxy().GetConfigurations()

        d = wxSingleChoiceDialog( self, "Select a configuration file to load", "Load Configuration Dialog", configs.data )
        ret = d.ShowModal()

        if ret == wxID_OK:
            conf = d.GetStringSelection()

            if len( conf ) == 0:
                self.Error( "No selection made" )
                return

            try:
                self.nodeServiceHandle.GetProxy().LoadConfiguration( conf )
            except faultType, e:
                log.exception("NodeManagementClientFrame.LoadConfiguration: Can not load configuration from node service")
                self.Error(e.faultstring)

            self.UpdateHostList()
            self.UpdateServiceList()

    def StoreConfiguration( self, event ):
        """
        Store a node service configuration
        """

        # Get known configurations from the Node Service
        configs = self.nodeServiceHandle.GetProxy().GetConfigurations().data

        # Prompt user to name the configuration
        d = StoreConfigDialog(self,-1,"Store Configuration", configs )
        ret = d.ShowModal()

        if ret == wxID_OK:
            ret = d.GetValue()
            if ret:
                (configName,isDefault) = ret

                # Handle error cases
                if len( configName ) == 0:
                    self.Error( "Invalid config name specified" )
                    return

                # Store the configuration
                try:
                    self.nodeServiceHandle.GetProxy().StoreConfiguration( configName )
                except faultType,e:
                    log.exception("NodeManagementClientFrame.StoreConfiguration: Can not store configuration in node service")
                    self.Error(e.faultstring)

                # Set the default configuration
                if isDefault:
                    self.nodeServiceHandle.GetProxy().SetDefaultConfiguration( configName )

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
        names = { "Hostname" : "", "Port":"12000" }
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
                host = GetHostname()

            # Add the service manager to the node service
            uri = 'https://%s:%s/ServiceManager' % (host,port)
            name = '%s:%s' % (host,port)
            try:
                self.nodeServiceHandle.GetProxy().AddServiceManager( AGServiceManagerDescription( name, uri ) )
            except faultType, e:
                log.exception("NodeManagementClientFrame.AddHost: Can not add service manager to node service")
                self.Error(e.faultstring)
                self.ClearUI()
                self.UpdateHostList()
                return
            
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
            self.nodeServiceHandle.GetProxy().RemoveServiceManager( self.serviceManagers[index] )

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

        self.serviceManagers = self.nodeServiceHandle.GetProxy().GetServiceManagers()
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
        self.UpdateServiceList()

    def ServiceManagerSelectedCB(self, event):
        index = self.hostList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
        uri = self.serviceManagers[index]
        try:
            Client.Handle(uri).IsValid
        except:
            log.exception("NodeManagementClientFrame.ServiceManagerSelectedCB: Service manager is valid call failed.")
            self.Error("Service Manager is unreachable (%s)" % uri)
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
        availServices =  self.nodeServiceHandle.GetProxy().GetAvailableServices()
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


            #
            # Prompt for resource to assign
            #
            resourceToAssign = None
            resources = Client.Handle( serviceManager.uri ).GetProxy().GetResources().data
            if len(resources) > 0:

                applicableResources1 = []
                serviceCapabilityTypes = map( lambda cap: cap.type, serviceToAdd.capabilities )
                for resource in resources:
                    if resource.type in serviceCapabilityTypes:
                        applicableResources1.append( resource )

                applicableResources = []
                for resource in applicableResources1:
                    for cap in serviceToAdd.capabilities:
                        if resource.role == cap.role:
                            applicableResources.append( resource )

                if len(applicableResources) > 0:
                    choices = ["None"]
                    choices = choices + map( lambda res: res.resource, applicableResources )
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


            try:
                #
                # Add the service
                #
                if serviceToAdd == None:
                    raise Exception("Can't add NULL service")
                self.nodeServiceHandle.GetProxy().AddService( serviceToAdd.servicePackageUri,
                               serviceManager.uri,
                               resourceToAssign,
                               None )
            except faultType, e:
                log.exception("NodeManagementClientFrame.AddService: Exception in AddService")
                #self.Error( "Add Service failed :" + serviceToAdd.name )
                self.Error(e.faultstring)

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
                self.nodeServiceHandle.GetProxy().SetServiceEnabled(self.services[index].uri, 1)

            # Update the services list
            self.UpdateServiceList()

        except faultType,e:
            log.exception("NodeManagementClientFrame.EnableService")
            self.Error(e.faultstring)

    def EnableServices( self, event ):
        """
        Enable all known services
        """
        services = self.nodeServiceHandle.GetProxy().GetServices()
        for service in services:
            self.nodeServiceHandle.GetProxy().SetServiceEnabled(service.uri,1)

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
                self.nodeServiceHandle.GetProxy().SetServiceEnabled(self.services[index].uri,0)

            # Update the service list
            self.UpdateServiceList()
        except faultType,e:
            log.exception("NodeManagementClientFrame.DisableService.")
            self.Error(e.faultstring)


    def DisableServices( self, event ):
        """
        Disable all known services
        """
        svcs = self.nodeServiceHandle.GetProxy().GetServices()
        for svc in svcs:
            self.nodeServiceHandle.GetProxy().SetServiceEnabled(svc.uri,0)

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
            Client.Handle( self.services[index].serviceManagerUri ).GetProxy().RemoveService( self.services[index] )

        # Update the service list
        self.UpdateServiceList()

    def GetServiceConfiguration( self, event=None ):
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
            Client.Handle( self.services[index].uri ).IsValid()
        except:
            log.exception("NodeManagementClientFrame.GetServiceConfiguration.")
            self.Error("Service is unreachable")
            return
            
        # Get configuration
        config = Client.Handle( self.services[index].uri ).GetProxy().GetConfiguration()
        if config == None or len(config) == 0 or config=="None":
            self.Error("No configurable parameters for service")
            return

        # Display the service configuration panel
        parameters = map( lambda parm: CreateParameter( parm ), config.parameters )
        self.config = ServiceConfiguration( config.resource, config.executable, parameters )
        self.LayoutConfiguration()

    def LayoutConfiguration( self ):
        """
        Display the service configuration dialog
        """
        dlg = ServiceConfigurationDialog(self,-1,"Service Config Dialog",self.config)
        ret = dlg.ShowModal()
        if ret == wxID_OK:
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
        Client.Handle( self.services[index].uri ).GetProxy().SetConfiguration( serviceConfig )


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
                self.services = Client.Handle( self.serviceManagers[index].uri ).GetProxy().GetServices()
                for svc in self.services:
                    itemindex = self.serviceList.InsertStringItem( i, svc.name )
                    self.serviceList.SetItemImage( itemindex, 0, 0 )
                    try:
                        if Client.Handle( svc.uri ).GetProxy().GetEnabled() == 1:
                            self.serviceList.SetStringItem( i,1, "Enabled" )
                        else:
                            self.serviceList.SetStringItem( i,1, "Disabled" )
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
    def GotoTestRoom( self, event=None ):
        streamDs = []
        streamDs.append( StreamDescription( "Test Room",
                             MulticastNetworkLocation( "233.2.171.39", 42000, 127 ),
                             Capability( Capability.CONSUMER, Capability.AUDIO ) ,
                             0, None, 0 ))
        streamDs.append( StreamDescription( "Test Room",
                             MulticastNetworkLocation( "233.2.171.38", 42002, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ),
                             0, None, 0 ) )
        try:
            self.nodeServiceHandle.GetProxy().SetStreams( streamDs )
        except faultType, e:
            log.exception("NodeManagementClientFrame.GotoTestRoom.")
            self.Error(e.faultstring)

        self.UpdateServiceList()

    def GotoArgonne( self, event=None ):
        streamDs = []
        streamDs.append( StreamDescription( "ANL",
                             MulticastNetworkLocation( "233.2.171.251", 59988, 127 ),
                             Capability( Capability.CONSUMER, Capability.AUDIO ),
                             0, None, 0 ) )
        streamDs.append( StreamDescription( "ANL",
                             MulticastNetworkLocation( "233.2.171.251", 59986, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ),
                             0, None, 0 ) )
        self.nodeServiceHandle.GetProxy().SetStreams( streamDs )

        self.UpdateServiceList()

    def GotoLobby( self, event=None ):
        streamDs = []
        streamDs.append( StreamDescription( "Lobby",
                             MulticastNetworkLocation( "224.2.177.155", 55524, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ),
                             0, None, 0 ) )
        streamDs.append( StreamDescription( "Lobby",
                             MulticastNetworkLocation( "224.2.211.167", 16964, 127 ),
                             Capability( Capability.CONSUMER, Capability.AUDIO ),
                             0, None, 0 ) )
        self.nodeServiceHandle.GetProxy().SetStreams( streamDs )
        self.UpdateServiceList()

    def GotoLocal( self, event=None ):
        streamDs = []
        streamDs.append( StreamDescription( "",
                             MulticastNetworkLocation( "localhost", 55524, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ),
                             0, None, 0 ) )
        self.nodeServiceHandle.GetProxy().SetStreams( streamDs )

        self.UpdateServiceList()

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
        self.PopupMenu(self.hostMenu, pos)

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
    from AccessGrid.AGService import AGResource
    
    app = wxPySimpleApp()

    # Service config dialog test
    resource = AGResource()
    resource.resource = "resource"
    config = ServiceConfiguration(resource, 'executable', [] )

    dlg = ServiceConfigurationDialog(None, -1, "Service Config Dialog", config)
    ret = dlg.ShowModal()
    dlg.Destroy()
   
