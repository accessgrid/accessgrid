#-----------------------------------------------------------------------------
# Name:        NodeManagementUIClasses.py
# Purpose:     
#
# Author:      Thomas D. Uram, Ivan R. Judson
#
# Created:     2003/06/02
# RCS-ID:      $Id: NodeManagementUIClasses.py,v 1.6 2003-02-10 22:10:14 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
import sys
import copy
import time, thread
import pprint
import urlparse

from wxPython.wx import *
from wxPython.lib.dialogs import wxMultipleChoiceDialog

# AG2 imports
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Types import *
from AccessGrid.AGParameter import *
from AccessGrid.Descriptions import StreamDescription
from AccessGrid.NetworkLocation import *
from AccessGrid import icons

#import gc
#gc.set_debug( gc.DEBUG_LEAK )

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
ID_SERVICE_START = 404
ID_SERVICE_START_ONE = 405
ID_SERVICE_STOP = 406
ID_SERVICE_STOP_ONE = 407

ID_VENUE_ARGONNE = 500
ID_VENUE_LOBBY = 501
ID_VENUE_LOCAL = 502
ID_VENUE_TESTROOM = 503

ID_DUM = 600

ID_HELP_ABOUT = 701


class TestTransientPopup(wxPopupTransientWindow):
    """Adds a bit of text and mouse movement to the wxPopupWindow"""
    def __init__(self, parent, style):
        wxPopupTransientWindow.__init__(self, parent, style)
        panel = wxPanel(self, -1)
        panel.SetBackgroundColour("#FFB6C1")
        self.m = BuildServiceMenu()

    def PopThatMenu( self, pos ):
        self.PopupMenuXY( self.m, pos[0], pos[1] )

def BuildServiceMenu( ):
    svcmenu = wxMenu()
    svcmenu.Append(ID_SERVICE_ADD_SERVICE, "Add Service...", "Dum")
    svcmenu.Append(ID_SERVICE_START_ONE, "Start Service", "Start Service")
    svcmenu.Append(ID_SERVICE_STOP_ONE, "Stop Service", "Stop Service")
    svcmenu.Append(ID_SERVICE_REMOVE, "Remove Service", "Remove Service")
    svcmenu.Append(ID_SERVICE_GET_CONFIG, "Get Service Config", "Dum")
    return svcmenu

class HostListCtrl( wxListCtrl ):

    def __init__(self, parent, ID, pos=wxDefaultPosition,
                  size=wxDefaultSize, style=0):
        listId = wxNewId()
        wxListCtrl.__init__(self, parent, listId, pos, size, style=wxLC_REPORT)

        self.InsertColumn( 0, "Service Managers", width=wxLIST_AUTOSIZE )

class ServiceListCtrl( wxListCtrl ):

    def __init__(self, parent, ID, pos=wxDefaultPosition,
                  size=wxDefaultSize, style=0):
        listId = wxNewId()
        wxListCtrl.__init__(self, parent, listId, pos, size, style=wxLC_REPORT)


        self.InsertColumn( 0, "Service Name", width=wxLIST_AUTOSIZE )
        self.InsertColumn( 1, "Status", width=wxLIST_AUTOSIZE )
        self.InsertColumn( 2, "URI", width=wxLIST_AUTOSIZE )

        bmap = icons.getDefaultServiceBitmap()
        imageList = wxImageList( bmap.GetWidth(), bmap.GetHeight() )
        imageList.Add( bmap )
        self.AssignImageList( imageList, wxIMAGE_LIST_NORMAL)

class ServiceConfigurationPanel( wxPanel ):
    def __init__( self, parent, ID, pos=wxDefaultPosition, size=wxDefaultSize, style=0 ):
        wxPanel.__init__( self, parent, ID, pos, size, style )
        self.panel = self
        self.callback = None

    def SetConfiguration( self, serviceConfig ):
        self.config = serviceConfig
        self.guiComponents = []

        self.panelSizer = wxBoxSizer( wxVERTICAL )
        self.panel.SetSizer( self.panelSizer )

        psz= wxBoxSizer( wxHORIZONTAL )
        pt = wxStaticText( self, -1, "Resource", style=wxALIGN_CENTRE )
        psz.Add( pt, 1 )
        pComp = wxTextCtrl( self, -1, serviceConfig.resource.resource )
        pComp.SetEditable( False )
        psz.Add( pComp, 1 )
        self.panelSizer.Add( psz, -1, wxEXPAND )
        self.guiComponents.append( pComp )

        psz= wxBoxSizer( wxHORIZONTAL )
        pt = wxStaticText( self.panel, -1, "Executable", style=wxALIGN_CENTRE )
        psz.Add( pt, -1 )
        pComp = wxTextCtrl( self.panel, -1, serviceConfig.executable )
        psz.Add( pComp, -1 )
        self.panelSizer.Add( psz, -1, wxEXPAND )
        self.guiComponents.append( pComp )


        for parameter in serviceConfig.parameters:

            psz= wxBoxSizer( wxHORIZONTAL )

            pt = wxStaticText( self.panel, -1, parameter.name, style=wxALIGN_CENTRE )
            psz.Add( pt, -1, wxEXPAND )

            pComp = None
            if parameter.TYPE == RangeParameter.TYPE:
                pComp = wxSlider( self.panel, -1, parameter.value, parameter.low, parameter.high, style = wxSL_LABELS )
            elif parameter.TYPE == OptionSetParameter.TYPE:
                pComp = wxComboBox( self.panel, 3, "", style=wxCB_READONLY )
                for option in parameter.options:
                    pComp.Append( option )
                pComp.SetValue( parameter.value )
            else:
                if parameter.TYPE != ValueParameter.TYPE :
                    print "Unknown parameter type", parameter.TYPE
                val = parameter.value
                if type(val) == int:
                    val = '%d' % (val)
                pComp = wxTextCtrl( self.panel, -1, val )

            self.guiComponents.append( pComp )
            psz.Add( pComp, -1 )

            self.panelSizer.Add( psz, -1, wxEXPAND )

        psz = wxBoxSizer( wxVERTICAL )
        b = wxButton( self.panel, 310, "Apply" )
        if self.callback:
            EVT_BUTTON( self, 310, self.callback )

        psz.Add( b, 0, wxALIGN_CENTER )
        self.panelSizer.Add( psz, -1, wxALIGN_CENTER )


        self.panel.Layout()

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

    def Clear( self ):
        self.DestroyChildren()

    def SetCallback( self, callback ):
        self.callback = callback

class NodeManagementClientFrame(wxFrame):
    _defaultURI =  "https://localhost:11000/NodeService"

    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, wxSize(450, 300))

#FIXME - decide whether to use status bar
        """
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")
        """

        self.SetTitle( "Access Grid Node Management")
        self.SetIcon(icons.getAGIconIcon())

        self.vc = None
        
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
        hostmenu = wxMenu()
        hostmenu.Append(ID_HOST_ADD, "Add Host...", "Add Host")
        hostmenu.Append(ID_HOST_REMOVE, "Remove Host", "Remove Host")
        menuBar.Append(hostmenu, "&Host");

        ## SERVICE menu

        svcmenu = BuildServiceMenu()
        menuBar.Append(svcmenu, "&Service");

        ## DEBUG menu

        debugMenu = wxMenu()
        debugMenu.Append(ID_VENUE_TESTROOM, "Go to Test Room", "Dum")
        debugMenu.Append(ID_VENUE_ARGONNE, "Go to Argonne", "Dum")
        debugMenu.Append(ID_VENUE_LOBBY, "Goto Lobby", "")
        debugMenu.Append(ID_VENUE_LOCAL, "Goto Local", "")
        debugMenu.AppendSeparator()
        debugMenu.Append(ID_DUM, "Kill Services", "")
        menuBar.Append(debugMenu, "&Debug");

        ## HELP menu
        helpMenu = wxMenu()
        helpMenu.Append(ID_HELP_ABOUT, "&About",
                    "More information about this program")
        menuBar.Append(helpMenu, "&Help");

        self.SetMenuBar(menuBar)

        mainsz = wxBoxSizer( wxVERTICAL )
        self.SetSizer( mainsz )

        sz = wxBoxSizer( wxHORIZONTAL )



        #
        # Create Hosts panel
        #
        statBoxPanel = wxPanel( self, -1 )
        statBox = wxStaticBox(statBoxPanel, -1, "ServiceManagers")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        sz.Add( statBoxPanel, -1, wxEXPAND )
        statBoxPanel.SetSizer( statBoxSizer )
        self.hostList = wxListCtrl( statBoxPanel, -1, style=wxLC_LIST )
        statBoxSizer.Add( self.hostList, -1, wxEXPAND )

        EVT_LIST_ITEM_SELECTED( self, self.hostList.GetId(), self.UpdateServiceList )
        EVT_LIST_ITEM_DESELECTED( self, self.hostList.GetId(), self.UpdateServiceList )


        #
        # Create Services panel
        #
        statBoxPanel = wxPanel( self, -1 )
        statBox = wxStaticBox(statBoxPanel, -1, "Services")
        statBoxSizer = wxStaticBoxSizer( statBox, wxVERTICAL )
        sz.Add( statBoxPanel, -1, wxEXPAND )
        statBoxPanel.SetSizer( statBoxSizer )
        self.serviceList = ServiceListCtrl( statBoxPanel, -1, style=wxLC_ICON )
        statBoxSizer.Add( self.serviceList, -1, wxEXPAND )

        EVT_LIST_ITEM_ACTIVATED( self, self.serviceList.GetId(), self.GetServiceConfiguration )

        mainsz.Add( sz, -1, wxEXPAND )

        EVT_MENU(self, ID_DUM                    ,  self.Dum )
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
        EVT_MENU(self, ID_SERVICE_START          ,  self.StartServices )
        EVT_MENU(self, ID_SERVICE_START_ONE      ,  self.StartService )
        EVT_MENU(self, ID_SERVICE_STOP           ,  self.StopServices )
        EVT_MENU(self, ID_SERVICE_STOP_ONE       ,  self.StopService )
        EVT_MENU(self, ID_VENUE_ARGONNE          ,  self.GotoArgonne )
        EVT_MENU(self, ID_VENUE_LOBBY            ,  self.GotoLobby )
        EVT_MENU(self, ID_VENUE_LOCAL            ,  self.GotoLocal )
        EVT_MENU(self, ID_VENUE_TESTROOM         ,  self.GotoTestRoom )
        EVT_MENU(self, ID_VIEW_REFRESH           ,  self.Update )

        EVT_LIST_ITEM_RIGHT_CLICK(self, self.serviceList.GetId(), self.OnShowPopupTransient)
        EVT_LIST_ITEM_DESELECTED(self, self.serviceList.GetId(), self.OnServiceDeselected)

        self.serviceManagers = []
        self.services = []

    def Connected(self):
        if self.vc != None:
            return true
        else:
            return false

    ############################
    ## FILE menu
    ############################

    def Attach( self, event ):

        d = wxTextEntryDialog( self, "Enter uri of running AGNodeService",
                               "Node Attach Dialog" )
        ret = d.ShowModal()

        if ret == wxID_OK:
            uri = d.GetValue()

            if len( uri ) == 0:
                self.Error( "No selection made" )
                return

            try:
                self.vc = Client.Handle( uri ).get_proxy()
            except:
                self.Error( "Could not attach to AGNodeService " + hostname
                            + port  )
                return

            self.SetTitle( "Access Grid Node Management - " )

            self.UpdateHostList()
            self.UpdateServiceList()

    def LoadConfiguration( self, event ):

        configs = self.vc.GetConfigurations()

        d = wxSingleChoiceDialog( self, "Select a configuration file to load", "Load Configuration Dialog", configs.data )
        ret = d.ShowModal()

        if ret == wxID_OK:
            conf = d.GetStringSelection()

            if len( conf ) == 0:
                self.Error( "No selection made" )
                return

            self.vc.LoadConfiguration( conf )
            self.UpdateHostList()
            self.UpdateServiceList()

    def StoreConfiguration( self, event ):

        d = wxTextEntryDialog( self, "Enter configuration name", "Store Configuration Dialog" )
        ret = d.ShowModal()

        if ret == wxID_OK:
            configName = d.GetValue()

            if len( configName ) == 0:
                self.Error( "No selection made" )
                return

            self.vc.StoreConfiguration( configName )

    def TimeToQuit(self, event):
        self.Close(true)

    ############################
    ## VIEW menu
    ############################
    def Update( self, event=None ):
        #vc.Refresh()
        self.UpdateHostList()
        self.UpdateServiceList()


    ############################
    ## HOST menu
    ############################
    def AddHost( self, event ):

        dlg = wxTextEntryDialog( self, "Enter uri of running host (e.g., https://myhost:8200/ServiceManager )", \
                 "Add Host Dialog" )
        dlg.Show()
        str = dlg.GetValue()
        if str != None and len(str)>0:
            uri = str

            name = urlparse.urlparse(uri)[1]

            try:
                self.vc.AddServiceManager( AGServiceManagerDescription( name, "agsm description", uri ) )
            except:
                print "Exception in AddHost", sys.exc_type, sys.exc_value
                self.Error( "Add Host failed" )
                return

            self.UpdateHostList()

    def RemoveHost( self, event ):
        if self.hostList.GetSelectedItemCount() == 0:
            self.Error( "No host selected!" )
            return

        index = -1
        for i in range( self.hostList.GetSelectedItemCount() ):
            index = self.hostList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            self.vc.RemoveServiceManager( self.serviceManagers[index] )

        self.UpdateHostList()

    def UpdateHostList( self, event=None ):
        self.hostList.DeleteAllItems()

        i = 0
        self.serviceManagers = self.vc.GetServiceManagers()
        for serviceManager in self.serviceManagers:
            print serviceManager
            self.hostList.InsertStringItem( i, serviceManager.name )
            i = i + 1

        #self.serviceConfigPanel.Clear()

    ############################
    ## SERVICE menu
    ############################

    def AddService( self, event=None ):


        if self.hostList.GetSelectedItemCount() == 0:
            self.Error( "No host selected for service!")
            return
        if self.hostList.GetSelectedItemCount() > 1:
            self.Error("Multiple hosts selected")
            return

        index = self.hostList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
        serviceManager = self.serviceManagers[index]

        resources = Client.Handle( serviceManager.uri ).get_proxy().GetResources()
        for resource in resources:
            print "resource ", resource.type, resource.resource, resource.inUse


        availServices = self.vc.GetAvailableServices().data
        print availServices
        dlg = wxSingleChoiceDialog( self, "Select Service to Add", "Add Service: Select Service", availServices )

        ret = dlg.ShowModal()

        if ret == wxID_OK:
            service = dlg.GetStringSelection()

            choices = ["None"]
            choices = choices + map( lambda res: res.resource, resources )
            dlg = wxSingleChoiceDialog( self, "Select resource for service", "Add Service: Select Resource",
                   choices )

            ret = dlg.ShowModal()

            if ret != wxID_OK:
                return

            res = dlg.GetStringSelection()

            resourceToAssign = None
            for resource in resources:
                if res == resource.resource:
                    resourceToAssign = resource
                    break

            if resourceToAssign != None:
                print "assigning resource ", resourceToAssign.resource
            else:
                print "assigning NO resource"
                resourceToAssign = AGResource()

            try:
                if len(service) == 0:
                    raise Exception()
                Client.Handle( serviceManager.uri ).get_proxy().AddService( service, resourceToAssign )
            except:
                print "Exception in AddService : ", sys.exc_type, sys.exc_value
                self.Error( "Add Service failed :" + service )

            self.UpdateServiceList()

    def StartService( self, event=None ):

        try:

            if self.serviceList.GetSelectedItemCount() == 0:
                self.Error( "No service selected!" )
                return

            index = -1
            for i in range( self.serviceList.GetSelectedItemCount() ):
                index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
                print "** Starting service ", index
                ret = Client.Handle( self.services[index].uri ).get_proxy().Start()
                print "return value = ", ret, ret.__class__
                print "** Called Start ! !! ! "

            self.UpdateServiceList()

        except:
            print "Exception in StartService ", sys.exc_type, sys.exc_value

    def StartServices( self, event ):
        """ Start all known services
        """
        services = self.vc.GetServices()
        for service in services:
            Client.Handle( service.uri ).get_proxy().Start()

        self.UpdateServiceList()

    def StopService( self, event=None ):

        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        index = -1
        for i in range( self.serviceList.GetSelectedItemCount() ):
            index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            Client.Handle( self.services[index].uri ).get_proxy().Stop()

        self.UpdateServiceList()

    def StopServices( self, event ):
        svcs = self.vc.GetServices()
        for svc in svcs:
            Client.Handle( svc.uri ).get_proxy().Stop()

        self.UpdateServiceList()

    def RemoveService( self, event ):

        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        index = -1
        for i in range( self.serviceList.GetSelectedItemCount() ):
            index = self.serviceList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            print "smuri  = ", self.services[index].name, self.services[index].uri, self.services[index].serviceManagerUri, index, len(self.services)
            Client.Handle( self.services[index].serviceManagerUri ).get_proxy().RemoveService( self.services[index] )

        self.UpdateServiceList()

    def GetServiceConfiguration( self, event=None ):

        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return

        index = self.serviceList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )
        print "index = ", index
        print "len = ", len(self.services)

        config = Client.Handle( self.services[index].uri ).get_proxy().GetConfiguration()

        if config == None or len(config) == 0 or config=="None":
            return

        parameters = map( lambda parm: CreateParameter( parm ), config.parameters )
        self.config = ServiceConfiguration( config.resource, config.executable, parameters )
        self.LayoutConfiguration()

    def LayoutConfiguration( self ):

        dlg = wxDialog( self, -1, "Service Configuration Dialog",
                        style = wxRESIZE_BORDER|wxCAPTION|wxSYSTEM_MENU,
                        size = (300,300) )

        dlgSizer = wxBoxSizer( wxVERTICAL )
        dlg.SetSizer( dlgSizer )

        self.serviceConfigPanel = ServiceConfigurationPanel( dlg, -1 )
        self.serviceConfigPanel.SetCallback( self.SetConfiguration )
        self.serviceConfigPanel.SetConfiguration( self.config )
        self.serviceConfigPanel.Layout()

        dlgSizer.Add( self.serviceConfigPanel, -1, wxEXPAND )

        dlg.Layout()
        dlg.ShowModal()
        dlg.Destroy()

        self.serviceConfigPanel = None


    def SetConfiguration( self, event=None ):
        if self.serviceList.GetSelectedItemCount() == 0:
            self.Error( "No service selected!" )
            return


        serviceConfig = self.serviceConfigPanel.GetConfiguration()
        index = self.serviceList.GetNextItem( -1, state = wxLIST_STATE_SELECTED )

        for s in self.services:
            print "smuri  = ", s.name, s.uri, s.serviceManagerUri


        print " ---SetConfiguration ", serviceConfig.__class__

        for parm in serviceConfig.parameters:
            print "    ---SetConfiguration--parameter", parm.name, parm.value, parm.__class__

        # send the modified configuration to the service
        Client.Handle( self.services[index].uri ).get_proxy().SetConfiguration( serviceConfig )


    def UpdateServiceList( self, event=None ):

        self.serviceList.DeleteAllItems()

        i = 0

        hosts = self.vc.GetServiceManagers()

        index = -1
        indices = []
        for i in range( self.hostList.GetSelectedItemCount() ):
            index = self.hostList.GetNextItem( index, state = wxLIST_STATE_SELECTED )
            indices.append( index )

        self.services = self.vc.GetServices()
        print "selfservices = ", self.services.__class__, self.services.data
        if len(self.serviceManagers) > 0 and index >= 0:
            for index in indices:
                print "index = ", index, " len sermgr = ", len(self.serviceManagers)
                print "------ ", self.serviceManagers[index]
                services = Client.Handle( self.serviceManagers[index].uri ).get_proxy().GetServices()
#FIXME - temporary
                self.services = services
                print "services = ", services, services.__dict__
                for svc in services:
                    print "   ", svc.uri
                    itemindex = self.serviceList.InsertStringItem( i, svc.name )
                    self.serviceList.SetItemImage( itemindex, 0, 0 )
                    try:
                        if Client.Handle( svc.uri ).get_proxy().IsStarted() == True:
                            self.serviceList.SetStringItem( i,1, "Started" )
                        else:
                            self.serviceList.SetStringItem( i,1, "Stopped" )
                    except:
                        print "Exception wxapp.UpdateServiceList ", sys.exc_type, sys.exc_value
                    self.serviceList.SetStringItem( i,2, svc.uri )
                    i = i + 1


    ############################
    ## HELP menu
    ############################
    def OnAbout(self, event):

        dlg = wxMessageDialog(self, "Access Grid 2.0\n"
                              "www.accessgrid.org\n"
                              "Argonne National Laboratory",
                              "About AG2", wxOK | wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()



    ############################
    ## UTILITY methods
    ############################
    def GotoTestRoom( self, event=None ):


        streamDs = []
        streamDs.append( StreamDescription( "Test Room", "",
                             MulticastNetworkLocation( "233.2.171.39", 42000, 127 ),
                             Capability( Capability.CONSUMER, Capability.AUDIO ) ) )
        streamDs.append( StreamDescription( "Test Room", "",
                             MulticastNetworkLocation( "233.2.171.38", 42002, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ) ) )
        streamDs.append( StreamDescription( "Test Room", "",
                             MulticastNetworkLocation( "233.2.171.38", 42004, 127 ),
                             Capability( Capability.CONSUMER, Capability.TEXT ) ) )
        self.vc.ConfigureStreams( streamDs )

        self.UpdateServiceList()

    def GotoArgonne( self, event=None ):
        streamDs = []
        streamDs.append( StreamDescription( "", "",
                             MulticastNetworkLocation( "233.2.171.251", 59988, 127 ),
                             Capability( Capability.CONSUMER, Capability.AUDIO ) ) )
        streamDs.append( StreamDescription( "", "",
                             MulticastNetworkLocation( "233.2.171.251", 59986, 127 ),
                             Capability( Capability.CONSUMER, Capability.VIDEO ) ) )
        self.vc.ConfigureStreams( streamDs )

        self.UpdateServiceList()

    def GotoLobby( self, event=None ):
        self.vc.SetMediaLocation( "video", "224.2.177.155 55524 127" )

        self.UpdateServiceList()

    def GotoLocal( self, event=None ):
        self.vc.SetMediaLocation( "video", "localhost 55524 127" )

        self.UpdateServiceList()

    def Error( self, message ):
        wxMessageDialog( self, message, style = wxOK ).ShowModal()

    def OnShowPopupTransient(self, evt):
        win = TestTransientPopup(self, wxSIMPLE_BORDER )

        # Show the popup right below or above the button
        # depending on available screen space...
        list = evt.GetEventObject()
        pos = list.ClientToScreen( evt.GetPoint() )
        win.PopThatMenu( pos )

    def OnServiceDeselected( self, event ):
        #self.serviceConfigPanel.Clear()
        pass

    def Dum( self, event = None ):
        pass
