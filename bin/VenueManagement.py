#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueManagement.py
# Purpose:     This is the user interface for Virtual Venues Server Management
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueManagement.py,v 1.58 2003-04-07 21:46:17 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from AccessGrid.hosting.pyGlobus import Client

from AccessGrid.Descriptions import StreamDescription, ConnectionDescription
from AccessGrid.Descriptions import VenueDescription, CreateVenueDescription
from AccessGrid.Descriptions import Capability
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.Utilities import formatExceptionInfo, HaveValidProxy
from AccessGrid import icons
from AccessGrid.Platform import GPI
from AccessGrid.UIUtilities import MyLog

import logging, logging.handlers
import string
import time

from pyGlobus.io import GSITCPSocketException

class VenueManagementClient(wxApp):
    """
    VenueManagementClient.

    The VenueManagementClient class creates the main frame of the
    application as well as the VenueManagementTabs and statusbar.
    """
    server = None
    serverUrl = None
    currentVenueClient = None
    currentVenue = None
    encrypt = false
    administrators = {}
    venueList = []

    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.frame = wxFrame(NULL, -1, "Venue Management" )
        self.address = VenueServerAddress(self.frame, self)
        self.tabs = VenueManagementTabs(self.frame, -1, self)
        self.statusbar = self.frame.CreateStatusBar(1)
        self.__doLayout()
        self.__setProperties()
        self.__setLogger()
        return true

    def __setLogger(self):
        log = logging.getLogger("AG.VenueManagement")
        log.setLevel(logging.DEBUG)
        hdlr = logging.FileHandler("VenueManagement.log")
        fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s",
                                "%x %X")
        hdlr.setFormatter(fmt)
        log.addHandler(hdlr)

        wxLog_SetActiveTarget(wxLogGui())
        wxLog_SetActiveTarget(wxLogChain(MyLog(log)))
        wxLogInfo(" ")
        wxLogDebug("--------- START VenueManagement")

    def __setProperties(self):
        self.frame.SetIcon(icons.getAGIconIcon())
        self.frame.SetSize(wxSize(540, 405))
        self.SetTopWindow(self.frame)
        self.frame.Show()

    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
        box.Add(self.address, 0, wxEXPAND|wxALL)
        box.Add(self.tabs, 1, wxEXPAND)
        self.frame.SetSizer(box)

    def OnExit(self):
        wxLogInfo("--------- END VenueManagement")

    def ConnectToServer(self, URL):
        wxLogDebug("Connect to server %s" %URL)

        handle = Client.Handle(URL)

        if not HaveValidProxy():
            wxLogDebug("You do not have a valid proxy run Platform.GPI()")
            GPI()

        if(handle.IsValid()):
            wxLogDebug("You have a valid proxy")
            try:
                wxBeginBusyCursor()
                wxLogDebug("Connect to server")
                self.server = handle.get_proxy()
                wxLogDebug("Get venues from server")
                self.venueList = {}
                vl = self.server.GetVenues()
                for v in vl:
                    self.venueList[v.uri] = CreateVenueDescription(v)

                self.serverUrl = URL

                vp = self.tabs.venuesPanel
                vlp = vp.venuesListPanel

                # Clear out old ones
                vlp.venuesList.Clear()
                vp.venueProfilePanel.ClearAllFields()
                
                # fill in venues
                self.tabs.Enable(true)
                if len(self.venueList) != 0 :
                    for venue in self.venueList.values():
                        wxLogDebug("Add venue: %s" % venue.name)
                        vlp.venuesList.Append(venue.name, venue)
                    currentVenue = vlp.venuesList.GetClientData(0)
                    vp.venueProfilePanel.ChangeCurrentVenue(currentVenue)
                    vlp.venuesList.SetSelection(0)

                else:
                    wxLogDebug("No venues in server")
                    vp.venueProfilePanel.ChangeCurrentVenue(None)

                # fill in administrators
                administratorList = self.server.GetAdministrators()
                s = ""
                for admin in administratorList:
                    s = s+" "+admin

                wxLogDebug("Add administrators %s"  %s)
                alp = self.tabs.configurationPanel.administratorsListPanel
                alp.administratorsList.Clear()
                if len(administratorList) != 0 :
                    for admin in administratorList:
                        cn = self.GetCName(admin)
                        alp.administratorsList.Append(cn, admin)
                        alp.administratorsList.SetSelection(0)

                # fill in multicast address
                ip = self.server.GetBaseAddress()
                mask = str(self.server.GetAddressMask())
                method = self.server.GetAddressAllocationMethod()

                dp = self.tabs.configurationPanel.detailPanel
                dp.ipAddress.SetLabel(ip+'/'+mask)

                if method == MulticastAddressAllocator.RANDOM:
                    wxLogDebug("Set multicast address to: RANDOM")
                    dp.ipAddress.Enable(false)
                    dp.changeButton.Enable(false)
                    dp.randomButton.SetValue(true)
                else:
                    wxLogDebug("Set multicast address to: INTERVAL, ip: %s, mask: %s" %(ip, mask))
                    dp.ipAddress.Enable(true)
                    dp.changeButton.Enable(true)
                    dp.intervalButton.SetValue(true)

                # fill in storage location
                storageLocation = self.server.GetStorageLocation()
                wxLogDebug("Set storage location: %s" %storageLocation)
                dp.storageLocation.SetLabel(storageLocation)

                # fill in address
                if self.address.addressText.FindString(self.serverUrl) == wxNOT_FOUND:
                    wxLogDebug("Set address: %s" %self.serverUrl)
                    self.address.addressText.Append(self.serverUrl)

                # fill in encryption
                key = self.server.GetEncryptAllMedia()
                wxLogDebug("Set server encryption key: %s" % key)
                dp.encryptionButton.SetValue(key)
                self.encrypt = key
                wxEndBusyCursor()

            except:
                wxEndBusyCursor()
                wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                       str(sys.exc_value)))
                wxLog_GetActiveTarget().Flush()

        else:
            if not HaveValidProxy():
                text = 'You do not have a valid proxy.' +\
                       '\nPlease, run "grid-proxy-init" on the command line"'
                text2 = 'Invalid proxy'
                wxLogDebug(text)

            else:
                text = 'The venue URL you specified is not valid'
                text2 = 'Invalid URL'

                if(self.serverUrl != None):
                    self.address.addressText.SetValue(self.serverUrl)
                else:
                    self.address.addressText.SetValue('https://localhost:8000/VenueServer')

            dlg = wxMessageDialog(self.frame, text, text2, style = wxOK|wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            wxLogDebug(text)

    def GetCName(self, distinguishedName):
        index = distinguishedName.find("CN=")
        if(index > -1):
            cn = distinguishedName[index+3:]
        else:
            cn = distinguishedName
        return cn

    def SetCurrentVenue(self, venue = None):
        """
        """
        if venue == None:
            wxLogDebug("Set current venue to none")
            self.currentVenue = None
            self.currentVenueClient = None

        elif self.currentVenue == None or self.currentVenue.uri != venue.uri:
            wxLogDebug("Set current venue to: %s, %s" % (str(venue.name),
                                                         str(venue.uri)))
            self.currentVenue = venue
            self.currentVenueClient = Client.Handle(venue.uri).get_proxy()

    def DisableStaticStreams(self, venue):
        self.SetCurrentVenue(venue)
        streamList = self.currentVenueClient.GetStaticStreams()
        wxLogDebug("Disable static streams for venue: %s" %str(venue.uri))
        for stream in streamList:
            l = stream.location
            wxLogDebug("Remove stream - type:%s host:%s port:%s ttl:%s"
                       % (stream.capability.type, l.host, l.port, l.ttl))
            self.currentVenueClient.RemoveStream(stream)

    def EnableStaticVideo(self, venue, videoAddress, videoPort, videoTtl):
        location = MulticastNetworkLocation(videoAddress, int(videoPort),
                                            int(videoTtl))
        capability = Capability( Capability.PRODUCER, Capability.VIDEO)
        videoStreamDescription = StreamDescription( "", "", location,
                                                    capability, 1)
        self.SetCurrentVenue(venue)
        wxLogDebug("Enable static video: %s addr: %s, port: %s, ttl %s" 
                     % (str(venue.uri), str(videoAddress),
                        str(videoPort), str(videoTtl)))
        self.currentVenueClient.AddStream(videoStreamDescription)

    def EnableStaticAudio(self, venue, audioAddress, audioPort, audioTtl):
        location = MulticastNetworkLocation(audioAddress, int(audioPort),
                                            int(audioTtl))
        capability = Capability( Capability.PRODUCER, Capability.AUDIO)
        audioStreamDescription = StreamDescription( "", "", location,
                                                    capability, 1)
        wxLogDebug("Enable static audio: %s addr: %s, port: %s, ttl %s"
                   % (str(venue.uri), str(audioAddress), str(audioPort),
                      str(audioTtl)))
        self.SetCurrentVenue(venue)
        self.currentVenueClient.AddStream(audioStreamDescription)

    def SetVenueEncryption(self, venue, value = 0, key = ''):
        self.SetCurrentVenue(venue)
        wxLogDebug("Set venue encryption: %s using key: %s for venue: %s" 
                     % (str(value), str(key), str(venue.uri)))
        self.currentVenueClient.SetEncryptMedia(int(value), str(key))

    def DeleteVenue(self, venue):
        wxLogDebug("Delete venue: %s" %str(venue.uri))
        self.server.RemoveVenue(venue.uri)
        if self.venueList.has_key(venue.uri):
            del self.venueList[venue.uri]

    def ConvertVenuesToConnections(self, list):
        wxLogDebug("Convert venue to connections %s" %str(list))

        connectionsList = []
        for venue in list:
            c = ConnectionDescription(venue.name, venue.description,
                                      venue.uri)
            connectionsList.append(c)

        return connectionsList

    def AddAdministrator(self, dnName):
        wxLogDebug("Add administrator: %s" %dnName)
        self.server.AddAdministrator(dnName)

    def DeleteAdministrator(self, dnName):
        wxLogDebug("Delete administrator: %s" %dnName)
        self.server.RemoveAdministrator(dnName)

    def ModifyAdministrator(self, oldName, dnName):
        wxLogDebug("Modify administrator: %s with new dnName: %s" %
                   (oldName,dnName))
        if(dnName != oldName):
            self.server.AddAdministrator(dnName)
            self.server.RemoveAdministrator(oldName)

    def SetRandom(self):
        wxLogDebug("Set random address allocation method")
        self.server.SetAddressAllocationMethod(MulticastAddressAllocator.RANDOM)

    def SetInterval(self, address, mask):
        wxLogDebug("Set interval address allocation method with address: %s, mask: %s" %(str(address), mask))
        self.server.SetBaseAddress(address)
        self.server.SetAddressMask(mask)
        self.server.SetAddressAllocationMethod(MulticastAddressAllocator.INTERVAL)

    def SetEncryption(self, value):
        wxLogDebug("Set encryption: %s" %str(value))
        self.server.SetEncryptAllMedia(int(value))
        self.encrypt = int(value)

    def SetStorageLocation(self, location):
        wxLogDebug("Set storage location: %s" %location)
        self.server.SetStorageLocation(location)

class VenueServerAddress(wxPanel):
    ID_BUTTON = wxNewId()
    ID_ADDRESS = wxNewId()

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
                        wxDefaultSize, wxNO_BORDER)
        self.application = application
        self.addressLabel =  wxStaticText(self, -1,'Venue Server Address:')
        self.defaultServer = 'https://localhost:8000/VenueServer'
        self.serverList = ['https://localhost:8000/VenueServer']
        self.addressText = wxComboBox(self, self.ID_ADDRESS,
                                      self.defaultServer,
                                      choices = self.serverList,
                                      style = wxCB_DROPDOWN)

        self.goButton = wxButton(self, self.ID_BUTTON, "Go",
                                 wxDefaultPosition, wxSize(20, 10))
        self.line = wxStaticLine(self, -1)
        self.__doLayout()
        self.__addEvents()

    def __addEvents(self):
        EVT_BUTTON(self, self.ID_BUTTON, self.CallAddress)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.CallAddress)

    def CallAddress(self, event):
        URL = self.addressText.GetValue()
        wxBeginBusyCursor()
        self.application.ConnectToServer(URL)
        wxEndBusyCursor()

    def __doLayout(self):
        venueServerAddressBox = wxBoxSizer(wxVERTICAL)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.addressLabel, 0, wxEXPAND|wxRIGHT|wxLEFT|wxTOP, 5)
        box.Add(self.addressText, 1, wxEXPAND|wxRIGHT|wxTOP, 5)
        box.Add(self.goButton, 0, wxEXPAND|wxRIGHT|wxTOP, 5)
        venueServerAddressBox.Add(box, 0, wxEXPAND)
        venueServerAddressBox.Add(self.line, 0, wxEXPAND|wxALL, 5)
        self.SetSizer(venueServerAddressBox)
        venueServerAddressBox.Fit(self)
        self.SetAutoLayout(1)


class VenueManagementTabs(wxNotebook):
    """
    VenueManagementTabs

    VenueManagementTabs is a notebook that initializes 3 pages,
    containing the VenuesPanel, ConfigurationPanel, and ServicesPanel.
    """

    def __init__(self, parent, id, application):


        wxNotebook.__init__(self, parent, id)
        self.parent = parent
        self.venuesPanel = VenuesPanel(self, application)
        self.configurationPanel = ConfigurationPanel(self, application)
        # Services are commented out for now
        # self.servicesPanel = ServicesPanel(self, application)
        self.AddPage(self.venuesPanel, "Venues")
        self.AddPage(self.configurationPanel, "Configuration")
        # Services are commented out for now
        # self.AddPage(self.servicesPanel, "Services")
        self.Enable(false)

# --------------------- TAB 1 -----------------------------------

class VenuesPanel(wxPanel):
    """
    VenuesPanel.

    This is the first page in the notebook.  This page has a list of
    venues that are present in the server.  When selecting a venue
    from the list its spcific information profile is displayed.  A
    user can manipulate the list by either add, modify, of delete a
    venue.  The contents of the VenuesPanel is split up into two
    panels; VenueProfilePanel and VenueListPanel.
    """

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition,
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.parent = parent
        self.venueProfilePanel = VenueProfilePanel(self, application)
        self.venuesListPanel = VenueListPanel(self, application)
        self.__doLayout()

    def __doLayout(self):
        venuesPanelBox = wxBoxSizer(wxHORIZONTAL)
        venuesPanelBox.Add(self.venuesListPanel, 0, wxEXPAND|wxALL, 10)
        venuesPanelBox.Add(self.venueProfilePanel, 2, wxEXPAND|wxALL, 10)

        self.SetSizer(venuesPanelBox)
        venuesPanelBox.Fit(self)
        self.SetAutoLayout(1)


class VenueProfilePanel(wxPanel):
    """
    VenueProfilePanel.

    Contains specific information about one venue, such as title,
    icon, url, and exits to other venues.
    """

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition,
                         wxDefaultSize, wxNO_BORDER|wxSW_3D,
                         name = "venueProfilePanel")
        self.application = application
        self.venueProfileBox = wxStaticBox(self, -1, "")
        self.description = wxTextCtrl(self, -1,'', size = wxSize(20,50),
                                      style = wxSIMPLE_BORDER
                                      | wxNO_3D | wxTE_MULTILINE
                                      | wxTE_RICH2 | wxTE_READONLY)
        self.line = wxStaticLine(self, -1)
        self.urlLabel = wxStaticText(self, -1, 'URL:', size = wxSize(50, 20),
                                     name = "urlLabel", style = wxALIGN_RIGHT)
        self.url = wxTextCtrl(self, -1, '', name = 'url', style = wxALIGN_LEFT
                              | wxTE_READONLY)
        self.exitsLabel = wxStaticText(self, -1, 'Exits:',
                                       size = wxSize(50, 20),
                                       name = "exitsLabel",
                                       style = wxALIGN_RIGHT |wxLB_SORT)
        self.exits = wxListBox(self, 10, size = wxSize(250, 100),
                               style = wxTE_READONLY | wxLB_SORT)
        self.description.SetValue("Not connected to server")
        self.description.SetBackgroundColour(self.GetBackgroundColour())
        self.url.SetBackgroundColour(self.GetBackgroundColour())
        self.description.Enable(true)
        self.__hideFields()
        self.__doLayout()

    #def EvtListBox(self, event):
    #    list = event.GetEventObject()
    #    data = list.GetClientData(list.GetSelection())
    #    if data is not None:
    #        try:
    #            #CLIENT
    #            exits = Client.Handle(data.uri).get_proxy().GetConnections()
    #            venueProfilePanel.ChangeCurrentVenue(data, exits)
    #        except:
    #            ErrorDialog(self, 'An error has occured!', "Error dialog")

    def ClearAllFields(self):
        self.venueProfileBox.SetLabel('')
        self.description.SetValue('')
        self.url.SetValue('')
        self.exits.Clear()

    def __hideFields(self):
        self.exitsLabel.Hide()
        self.exits.Hide()
        self.urlLabel.Hide()
        self.url.Hide()

    def ChangeCurrentVenue(self, venue = None):
        if venue == None:
            self.ClearAllFields()
            self.__hideFields()
            self.description.SetValue("No venues in server")
            self.application.SetCurrentVenue(None)

        else:
            # Set normal stuff
            self.application.SetCurrentVenue(venue)
            self.venueProfileBox.SetLabel(venue.name)
            self.url.SetValue(venue.uri)

            # clear the exit list
            self.exits.Clear()

            for e in venue.connections.values():
                self.exits.Append(e.name, e)

            self.exitsLabel.Show()
            self.url.Show()
            self.urlLabel.Show()
            self.description.SetValue(venue.description)
            self.exits.Show()

    def __doLayout(self):
        venueListProfileSizer = wxStaticBoxSizer(self.venueProfileBox,
                                                 wxVERTICAL)
        venueListProfileSizer.Add(5, 20)
        venueListProfileSizer.Add(self.description, 4,
                                  wxEXPAND|wxLEFT|wxRIGHT, 15)
        venueListProfileSizer.Add(5, 10)
        venueListProfileSizer.Add(self.line, 0, wxEXPAND)

        paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
        paramGridSizer.Add(self.urlLabel, 0, wxEXPAND, 0)
        paramGridSizer.Add(self.url, 1, wxALIGN_LEFT | wxEXPAND|wxRIGHT, 15)
        paramGridSizer.Add(self.exitsLabel, 0, wxEXPAND, 0)
        paramGridSizer.Add(self.exits, 2, wxEXPAND|wxRIGHT|wxBOTTOM, 15)
        paramGridSizer.AddGrowableCol(1)
        paramGridSizer.AddGrowableRow(1)
        venueListProfileSizer.Add(paramGridSizer, 10, wxEXPAND|wxTOP, 10)

        self.SetSizer(venueListProfileSizer)
        venueListProfileSizer.Fit(self)
        self.SetAutoLayout(1)


class VenueListPanel(wxPanel):
    '''VenueListPanel.

    Contains the list of venues that are present on the server and buttons
    to execute modifications of the list (add, delete, and modify venue).
    '''
    ID_LIST = wxNewId()
    ID_ADD = wxNewId()
    ID_MODIFY = wxNewId()
    ID_DELETE = wxNewId()

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition,
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.parent = parent
        self.application = application
        self.venuesListBox = wxStaticBox(self, -1, "Venues",
                                         name = 'venueListBox')
        self.venuesList = wxListBox(self, self.ID_LIST, name = 'venueList',
                                    style = wxLB_SORT)
        self.addButton = wxButton(self, self.ID_ADD, 'Add',
                                  size = wxSize(50,20), name = 'addButton')
        self.modifyButton = wxButton(self, self.ID_MODIFY, 'Modify',
                                     size = wxSize(50, 20),
                                     name = 'modifyButton')
        self.deleteButton = wxButton(self, self.ID_DELETE, 'Delete',
                                     size = wxSize(50, 20),
                                     name = 'deleteButton')
        self.__doLayout()
        self.__addEvents()

    def __addEvents(self):
        EVT_BUTTON(self, self.ID_ADD, self.OpenAddVenueDialog)
        EVT_BUTTON(self, self.ID_MODIFY, self.OpenModifyVenueDialog)
        EVT_BUTTON(self, self.ID_DELETE, self.DeleteVenue)
        EVT_LISTBOX(self, self.ID_LIST, self.EvtListBox)
        EVT_LISTBOX_DCLICK(self,self.ID_LIST, self.OnDoubleClick)
        EVT_KEY_UP(self.venuesList, self.OnKey)

    def OnKey(self, event):
        key = event.GetKeyCode()
        if key == WXK_DELETE:
            self.DeleteVenue()

    def OnDoubleClick(self, event):
        modifyVenueDialog = ModifyVenueFrame(self, -1, "", 
                                             self.venuesList, self.application)

    def EvtListBox(self, event):
        list = event.GetEventObject()
        data = list.GetClientData(list.GetSelection())
        if data is not None:
            try:
                wxLogInfo("Change current venue")
                self.parent.venueProfilePanel.ChangeCurrentVenue(data)

            except:
                wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                       str(sys.exc_value)))
                wxLog_GetActiveTarget().Flush()

    def OpenAddVenueDialog(self, event):
        addVenueDialog = AddVenueFrame(self, -1, "", self.venuesList,
                                       self.application)
        addVenueDialog.Destroy()

    def OpenModifyVenueDialog(self, event):
        if(self.venuesList.GetSelection() != -1):
            modifyVenueDialog = ModifyVenueFrame(self, -1, "", 
                                                 self.venuesList,
                                                 self.application)

            modifyVenueDialog.Destroy()

    def DeleteVenue(self, event = None):
        if (self.venuesList.GetSelection() != -1):
            index = self.venuesList.GetSelection()
            venueToDelete = self.venuesList.GetClientData(index)

            text =  "Are you sure you want to delete " + venueToDelete.name
            text2 = "Delete venue"
            message = wxMessageDialog(self, text, text2,
                                      style = wxOK|wxCANCEL|wxICON_INFORMATION)

            if(message.ShowModal()==wxID_OK):

                try:
                    wxLogInfo("Delete venue")
                    self.application.DeleteVenue(venueToDelete)

                except:
                    wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                          str(sys.exc_value)))
                    wxLog_GetActiveTarget().Flush()

                else:
                    self.venuesList.Delete(index)

                    if self.venuesList.Number() > 0:
                        self.venuesList.SetSelection(0)
                        venue = self.venuesList.GetClientData(0)

                        try:
                            wxLogInfo("Change current venue")
                            self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

                        except:
                            wxLogError("\ntype: %s \nvalue: %s" %
                                       (str(sys.exc_type), str(sys.exc_value)))
                            wxLog_GetActiveTarget().Flush()
                    else:
                        self.parent.venueProfilePanel.ChangeCurrentVenue()

    def AddVenue(self, venue):
        # ICKY ICKY ICKY
        venue.connections = venue.connections.values()
        newUri = self.application.server.AddVenue(venue)
        venue.uri = newUri

        if newUri:
            exits = venue.connections
            venue.connections = {}
            for e in exits:
                venue.connections[e.uri] = e
            
            self.venuesList.Append(venue.name, venue)
            self.venuesList.Select(self.venuesList.Number()-1)
            self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

    def ModifyVenue(self, venue):
        if venue.uri != None:
            # ICKY HACK
            connectionDict = venue.connections
            venue.connections = venue.connections.values()
            self.application.server.ModifyVenue(venue.uri, venue)
            item = self.venuesList.GetSelection()
            self.venuesList.SetClientData(item, venue)
            self.venuesList.SetString(item, venue.name)

            venue.connections = connectionDict
            self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

        self.DisableStaticStreams()

    def SetEncryption(self, value, key):
        item = self.venuesList.GetSelection()
        venue =  self.venuesList.GetClientData(item)
        wxLogDebug("Set encryption value:%s key:%s"%(value,key))
        self.application.SetVenueEncryption(venue, value, key)

    def SetStaticVideo(self, videoAddress, videoPort, videoTtl):
        item = self.venuesList.GetSelection()
        venue =  self.venuesList.GetClientData(item)

        self.application.EnableStaticVideo(venue, videoAddress,
                                           videoPort, videoTtl)

    def SetStaticAudio(self, audioAddress, audioPort, audioTtl):
        item = self.venuesList.GetSelection()
        venue =  self.venuesList.GetClientData(item)
        self.application.EnableStaticAudio(venue, audioAddress,
                                           audioPort, audioTtl)

    def DisableStaticStreams(self):
        item = self.venuesList.GetSelection()
        venue =  self.venuesList.GetClientData(item)
        self.application.DisableStaticStreams(venue)

    def __doLayout(self):
        venueListPanelSizer = wxStaticBoxSizer(self.venuesListBox, wxVERTICAL)
        venueListPanelSizer.Add(self.venuesList, 8, wxEXPAND|wxALL, 5)
        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.addButton, 1,  wxLEFT| wxBOTTOM | wxALIGN_CENTER,
                        5)
        buttonSizer.Add(self.modifyButton, 1, wxLEFT | wxBOTTOM
                        | wxALIGN_CENTER, 5)
        buttonSizer.Add(self.deleteButton, 1, wxLEFT | wxBOTTOM | wxRIGHT
                        | wxALIGN_CENTER, 5)
        venueListPanelSizer.Add(buttonSizer, 0, wxEXPAND)

        self.SetSizer(venueListPanelSizer)
        venueListPanelSizer.Fit(self)

        self.SetAutoLayout(1)


# --------------------- TAB 2 -----------------------------------
"""
ConfigurationPanel.

This is the second page in the notebook.  This page has a list of
administrators that are authorized to modify the list of venues on the
server and also entitled to add and remove other administrators.  When
selecting a name from the list, the spcific information profile of the
administrator is shown.  The contents of the AdministratorsPanel is
split up into two panels; AdministratorsProfilePanel and
AdministratorsListPanel.
"""

class ConfigurationPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, 
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
        self.administratorsListPanel = AdministratorsListPanel(self,
                                                               application)
        self.detailPanel = DetailPanel(self, application)
        self.__doLayout()

    def __doLayout(self):
        configurationPanelSizer = wxBoxSizer(wxHORIZONTAL)
        configurationPanelSizer.Add(self.administratorsListPanel, 0,
                                    wxEXPAND|wxALL, 10)
        configurationPanelSizer.Add(self.detailPanel, 2, wxEXPAND|wxALL, 10)

        self.SetSizer(configurationPanelSizer)
        configurationPanelSizer.Fit(self)
        self.SetAutoLayout(1)


"""
AdministratorsListPanel.

Contains the list of administratos that are authorized to manipulate
venues and administrators.  This panel also has buttons to execute
modifications of the list (add, delete, and modify an administrator).
"""

class AdministratorsListPanel(wxPanel):
    ID_ADD = wxNewId()
    ID_MODIFY = wxNewId()
    ID_DELETE = wxNewId()
    ID_LISTBOX = wxNewId()

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition,
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
        self.administratorsListBox = wxStaticBox(self, -1, "Administrators",
                                                 name = 'venueListBox')
        self.administratorsList = wxListBox(self, self.ID_LISTBOX,
                                            name = 'venueList',
                                            style = wxLB_SORT)
        self.addButton = wxButton(self, self.ID_ADD, 'Add', 
                                  size = wxSize(50, 20), name = 'addButton')
        self.deleteButton = wxButton(self, self.ID_DELETE, 'Delete',
                                     size = wxSize(50, 20),
                                     name = 'deleteButton')
        self.modifyButton = wxButton(self, self.ID_MODIFY, 'Modify',
                                     size = wxSize(50, 20),
                                     name = 'modifyButton')
        self.__addEvents()
        self.__doLayout()

    def __addEvents(self):
        EVT_BUTTON(self, self.ID_ADD, self.OpenAddAdministratorDialog)
        EVT_BUTTON(self, self.ID_DELETE, self.DeleteAdministrator)
        EVT_BUTTON(self, self.ID_MODIFY, self.OpenModifyAdministratorDialog)
        EVT_LISTBOX_DCLICK(self, self.ID_LISTBOX, self.OnDoubleClick)
        EVT_KEY_UP(self.administratorsList, self.OnKey)

    def OnKey(self, event):
        key = event.GetKeyCode()
        if key == WXK_DELETE:
            self.DeleteAdministrator()

    def OnDoubleClick(self, event):
        self.OpenModifyAdministratorDialog()

    def DeleteAdministrator(self, event = None):
        index = self.administratorsList.GetSelection()
        if (index != -1):
            adminToDelete = self.administratorsList.GetClientData(index)
            text =  "Are you sure you want to delete " + self.application.GetCName(adminToDelete)
            text2 = "Delete administrator"
            message = wxMessageDialog(self, text, text2,
                                      style = wxOK|wxCANCEL|wxICON_INFORMATION)

            if(message.ShowModal()==wxID_OK):

                try:
                    wxLogInfo("Delete administrator")
                    self.application.DeleteAdministrator(adminToDelete)

                except:
                    wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                           str(sys.exc_value)))
                    wxLog_GetActiveTarget().Flush()

                else:
                    self.administratorsList.Delete(index)
                    if self.administratorsList.Number > 1 :
                        self.administratorsList.SetSelection(0)

    def OpenAddAdministratorDialog(self, title):
        addAdministratorDialog = AddAdministratorFrame(self, -1,
                                             "Add Venue Server Administrator")

    def OpenModifyAdministratorDialog(self, event = None):
        index = self.administratorsList.GetSelection()

        if index > -1:
            name = self.administratorsList.GetClientData(index)
            modifyAdministratorDialog = ModifyAdministratorFrame(self, -1,
                                         "Modify Venue Server Administrator",
                                                                 name)

    def InsertAdministrator(self, data):
        try:
            wxLogInfo("Add administrator")
            self.application.AddAdministrator(data)
        except:
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

        else:
            self.administratorsList.Append(self.application.GetCName(data),
                                           data)
            self.administratorsList.Select(self.administratorsList.Number()-1)

    def ModifyAdministrator(self, oldName, newName):
        try:
            wxLogInfo("Modify administrator")
            index = self.administratorsList.GetSelection()
            self.application.ModifyAdministrator(oldName, newName)

        except:
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

        else:
            self.administratorsList.Delete(index)
            self.administratorsList.Append(self.application.GetCName(newName),
                                           newName)
            self.administratorsList.Select(self.administratorsList.Number()-1)

    def __doLayout(self):
        administratorsListSizer = wxStaticBoxSizer(self.administratorsListBox, wxVERTICAL)
        administratorsListSizer.Add(self.administratorsList, 8,
                                    wxEXPAND|wxALL, 5)
        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        administratorsListSizer.Add(buttonSizer, 0)
        buttonSizer.Add(self.addButton, 1,
                        wxLEFT| wxBOTTOM | wxALIGN_CENTER, 5)
        buttonSizer.Add(self.modifyButton, 1,
                        wxLEFT | wxBOTTOM |wxALIGN_CENTER, 5)
        buttonSizer.Add(self.deleteButton, 1, wxLEFT | wxBOTTOM |wxRIGHT
                        | wxALIGN_CENTER, 5)

        self.SetSizer(administratorsListSizer)
        administratorsListSizer.Fit(self)
        self.SetAutoLayout(1)


class DetailPanel(wxPanel):
    ID_CHANGE = wxNewId()
    ID_BROWSE = wxNewId()
    ID_RANDOM = wxNewId()
    ID_INTERVAL = wxNewId()
    ID_ENCRYPT = wxNewId()

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
        self.multicastBox = wxStaticBox(self, -1, "Multicast Address",
                                        size = wxSize(50, 50),
                                        name = 'multicastBox')
        self.storageBox = wxStaticBox(self, -1, "Storage Location",
                                      size = wxSize(500, 50),
                                      name = 'storageBox')
        self.encryptionBox = wxStaticBox(self, -1, "Encryption",
                                         size = wxSize(500, 50),
                                         name = 'encryptionBox')
        self.randomButton = wxRadioButton(self, self.ID_RANDOM,
                                          "Standard Range")
        self.intervalButton = wxRadioButton(self, self.ID_INTERVAL,
                                            "Custom Range: ")
        self.ipAddress = wxStaticText(self, -1, "111.111.111.111/24",
                                      style = wxALIGN_LEFT)
        self.changeButton = wxButton(self, self.ID_CHANGE, "Change")
        self.storageLocation = wxStaticText(self, -1,
                                            "/home/lefvert/cool_files/")
        self.encryptionButton = wxCheckBox(self, self.ID_ENCRYPT,
                                           " Encrypt media ")
        self.browseButton = wxButton(self, self.ID_BROWSE, "Change")
        self.ipString = "111.111.111.111"
        self.maskString = "24"
        self.__doLayout()
        self.__setEvents()
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)

    def __setEvents(self):
        EVT_BUTTON(self, self.ID_CHANGE, self.OpenIntervalDialog)
        EVT_BUTTON(self, self.ID_BROWSE, self.OpenBrowseDialog)
        EVT_RADIOBUTTON(self, self.ID_RANDOM, self.ClickedOnRandom)
        EVT_RADIOBUTTON(self, self.ID_INTERVAL, self.ClickedOnInterval)
        EVT_CHECKBOX(self, self.ID_ENCRYPT, self.ClickedOnEncrypt)

    def ClickedOnEncrypt(self, event):
        try:
            wxLogInfo("Set encryption")
            self.application.SetEncryption(event.Checked())
        except:
            self.encryptionButton.SetValue(not event.Checked())
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

    def ClickedOnRandom(self, event):
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)
        try:
            wxLogInfo("Set multicast address to random")
            self.application.SetRandom()
        except:
            self.ipAddress.Enable(true)
            self.changeButton.Enable(true)
            self.intervalButton.SetValue(true)
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

    def ClickedOnInterval(self, event):
        self.ipAddress.Enable(true)
        self.changeButton .Enable(true)
        maskInt = int(self.maskString)

        try:
            wxLogInfo("Set multicast address to interval")
            self.application.SetInterval(self.ipString, maskInt)

        except:
            self.ipAddress.Enable(false)
            self.changeButton.Enable(false)
            self.randomButton.SetValue(true)
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

    def SetAddress(self, ipAddress, mask):
        oldIpAddress = self.ipAddress.GetLabel()

        try:
            wxLogInfo("Set static addressing")
            self.ipAddress.SetLabel(ipAddress+'/'+mask)
            self.ipString = ipAddress
            self.maskString = mask
            maskInt = int(mask)
            self.application.SetInterval(self.ipString, maskInt)

        except:
            self.ipAddress.SetLabel(oldIpAddress)
            wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                   str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()

    def OpenBrowseDialog(self, event):
        dlg = wxDirDialog(self, "Choose a directory:")
        if dlg.ShowModal() == wxID_OK:
            try:
                wxLogInfo("Set storage location")
                self.application.SetStorageLocation(dlg.GetPath())
            except:
                wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                       str(sys.exc_value)))
                wxLog_GetActiveTarget().Flush()

            else:
                self.storageLocation.SetLabel(dlg.GetPath())

        dlg.Destroy()

    def OpenIntervalDialog(self, event):
        MulticastDialog(self, -1, "Enter Multicast Address")

    def __doLayout(self):
        serviceSizer = wxBoxSizer(wxVERTICAL)
        multicastBoxSizer = wxStaticBoxSizer(self.multicastBox, wxVERTICAL)

        multicastBoxSizer.Add(self.randomButton, 0, wxALL, 5)
        flexSizer = wxFlexGridSizer(0, 3, 1, 1)
        flexSizer.Add(self.intervalButton, 0)
        flexSizer.Add(self.ipAddress, 0,
                      wxCENTER|wxEXPAND|wxALIGN_CENTER|wxTOP)
        multicastBoxSizer.Add(flexSizer, 0, wxEXPAND | wxALL, 5)
        multicastBoxSizer.Add(self.changeButton, 0, wxBOTTOM|wxALIGN_CENTER, 5)

        serviceSizer.Add(multicastBoxSizer, 0,  wxBOTTOM|wxEXPAND, 10)
        serviceSizer.Add(5,5)

        storageBoxSizer = wxStaticBoxSizer(self.storageBox, wxVERTICAL)
        storageBoxSizer.Add(5,5)
        storageBoxSizer.Add(self.storageLocation, 5, wxALL, 10)
        storageBoxSizer.Add(self.browseButton, 0, wxCENTER|wxBOTTOM, 5)

        serviceSizer.Add(storageBoxSizer, 0, wxEXPAND| wxBOTTOM, 10)

        encryptionBoxSizer = wxStaticBoxSizer(self.encryptionBox, wxVERTICAL)
        encryptionBoxSizer.Add(self.encryptionButton, 5, wxALL, 10)

        serviceSizer.Add(encryptionBoxSizer, 0, wxEXPAND| wxBOTTOM, 10)

        self.SetSizer(serviceSizer)
        serviceSizer.Fit(self)
        self.SetAutoLayout(1)


# --------------------- TAB 3 -----------------------------------

"""
ServicesPanel.

This is the third page in the notebook.  The page lets the user
specify different options for services for the venue server.
Currently, a user can choose random or interval multicast address and
the storage location for the server.
"""

class ServicesPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
        self.__doLayout()

    def __doLayout(self):
        self.SetAutoLayout(1)


#--------------------- DIALOGS -----------------------------------
IP = 1
IP_1 = 2
MASK = 4
TTL = 5
PORT = 6

class MulticastDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.SetSize(wxSize(400, 350))
        self.parent = parent
        self.ipAddressLabel = wxStaticText(self, -1, "IP Address: ")
        self.ipAddress1 = wxTextCtrl(self, -1, "", size = (30,20),
                                     validator = DigitValidator(IP_1))
        self.ipAddress2 = wxTextCtrl(self, -1, "", size = (30,20),
                                     validator = DigitValidator(IP))
        self.ipAddress3 = wxTextCtrl(self, -1, "", size = (30,20),
                                     validator = DigitValidator(IP))
        self.ipAddress4 = wxTextCtrl(self, -1, "", size = (30,20),
                                     validator = DigitValidator(IP))
        self.maskLabel = wxStaticText(self, -1, "Mask: ")
        self.mask = wxTextCtrl(self, -1, "", size = (30,20),
                               validator = DigitValidator(MASK))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__doLayout()
        if (self.ShowModal() == wxID_OK ):
            address = self.ipAddress1.GetValue() + "." +\
                      self.ipAddress2.GetValue() + "." +\
                      self.ipAddress3.GetValue() + "." +\
                      self.ipAddress4.GetValue()
            self.parent.SetAddress(address, self.mask.GetValue())
        self.Destroy();

    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        theSizer = wxFlexGridSizer(0, 5, 10, 10)
        theSizer.Add(self.ipAddressLabel, 0, wxALIGN_RIGHT)
        theSizer.Add(self.ipAddress1)
        theSizer.Add(self.ipAddress2)
        theSizer.Add(self.ipAddress3)
        theSizer.Add(self.ipAddress4)
        theSizer.Add(self.maskLabel, 0, wxALIGN_RIGHT)
        theSizer.Add(self.mask)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxRIGHT, 5)
        buttonSizer.Add(self.cancelButton, 0, wxLEFT, 5)

        sizer.Add(theSizer, 0, wxALL, 20)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER|wxBOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class VenueParamFrame(wxDialog):
    venue = None
    exitsList = []
    streams = []
    encryptionType = (0, None)
    
    ID_TRANSFER = wxNewId()
    ID_REMOVE_EXIT = wxNewId()
    ID_LOAD = wxNewId()

    def __init__(self, parent, id, title, application):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.SetSize(wxSize(400, 350))
        self.application = application
        self.informationBox = wxStaticBox(self, -1, "Information")
        self.exitsBox = wxStaticBox(self, -1, "Exits")
        self.titleLabel =  wxStaticText(self, -1, "Title:")
        self.title =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20),
                                 validator = TextValidator())
        self.descriptionLabel = wxStaticText(self, -1, "Description:")
        self.description =  wxTextCtrl(self, -1, "", size = wxSize(200, 100),
                                       style = wxTE_MULTILINE |
                                       wxTE_RICH2, validator = TextValidator())
        self.staticAddressingPanel = StaticAddressingPanel(self, -1)
        self.encryptionPanel = EncryptionPanel(self, -1)
        self.venuesLabel = wxStaticText(self, -1, "Available Venues:")
        # This is actually available exits
        self.venues = wxListBox(self, -1, size = wxSize(250, 100),
                                style = wxLB_SORT)
        self.transferVenueLabel = wxStaticText(self, -1, "Add Exit")
        self.transferVenueButton = wxButton(self, self.ID_TRANSFER, ">>",
                                            size = wxSize(30, 20))
        self.address = wxComboBox(self, -1, self.application.serverUrl,\
                                  choices = [self.application.serverUrl],
                                  style = wxCB_DROPDOWN)
        self.goButton = wxButton(self, self.ID_LOAD, "Go",
                                 size = wxSize(20, 10))
        self.removeExitButton = wxButton(self, self.ID_REMOVE_EXIT,
                                         "     Remove Exit     ")
        self.exitsLabel = wxStaticText(self, -1, "Exits for your venue:")
        # This is the exits this venue has
        self.exits = wxListBox(self, -1, size = wxSize(250, 100),
                               style = wxLB_SORT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")

	self.__doLayout() 
	self.__addEvents()

    def __doLayout(self):
        boxSizer = wxBoxSizer(wxVERTICAL)

        topSizer =  wxBoxSizer(wxHORIZONTAL)

        paramFrameSizer = wxFlexGridSizer(10, 2, 5, 5)
        paramFrameSizer.Add(self.titleLabel, 0, wxALIGN_RIGHT)
        paramFrameSizer.Add(self.title, 0, wxEXPAND)
        paramFrameSizer.AddGrowableCol(1)

        topParamSizer = wxStaticBoxSizer(self.informationBox, wxVERTICAL)
        topParamSizer.Add(paramFrameSizer, 0, wxEXPAND | wxALL, 10)
        topParamSizer.Add(10,10)
        topParamSizer.Add(self.descriptionLabel, 0, wxALIGN_LEFT |wxLEFT, 10)
        topParamSizer.Add(self.description, 1,
                          wxEXPAND |wxLEFT | wxRIGHT| wxBOTTOM, 10)

        topSizer.Add(topParamSizer, 1, wxRIGHT | wxEXPAND, 5)

        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.encryptionPanel, 0, wxLEFT|wxBOTTOM | wxEXPAND, 5)
        sizer.Add(self.staticAddressingPanel, 0, wxLEFT|wxTOP| wxEXPAND, 5)
        topSizer.Add(sizer)

        boxSizer.Add(topSizer, 0, wxALL | wxEXPAND, 10)

        bottomParamSizer = wxStaticBoxSizer(self.exitsBox, wxVERTICAL)
        exitsSizer = wxFlexGridSizer(10, 3, 5, 5)
        exitsSizer.Add(self.venuesLabel, 0)
        exitsSizer.Add(10,10, wxEXPAND)
        exitsSizer.Add(self.exitsLabel, 0)

        exitsSizer.Add(self.venues, 0, wxEXPAND)

        transferbuttonSizer = wxBoxSizer(wxVERTICAL)
        transferbuttonSizer.Add(self.transferVenueLabel, 0, wxEXPAND|wxCENTER)
        transferbuttonSizer.Add(self.transferVenueButton, 0, wxEXPAND|wxTOP, 2)
        exitsSizer.Add(transferbuttonSizer, 0, wxALL|wxALIGN_CENTER, 5)
        exitsSizer.Add(self.exits, 0, wxEXPAND)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.address, 2, wxEXPAND| wxRIGHT, 1)
        buttonSizer.Add(self.goButton, 0, wxEXPAND | wxLEFT, 1)
        exitsSizer.Add(buttonSizer, 1, wxEXPAND)

        exitsSizer.Add(10,10)
        exitsSizer.Add(self.removeExitButton, 0, wxEXPAND)
        exitsSizer.AddGrowableCol(0)
        exitsSizer.AddGrowableCol(2)

        bottomParamSizer.Add(exitsSizer, 0, wxEXPAND | wxALL, 10)

        buttonSizer =  wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(20, 20, 1)
        buttonSizer.Add(self.okButton, 0)
        buttonSizer.Add(10, 10)
        buttonSizer.Add(self.cancelButton, 0)
        buttonSizer.Add(20, 20, 1)


        boxSizer.Add(bottomParamSizer, 0,
                     wxEXPAND | wxLEFT | wxBOTTOM | wxRIGHT, 10)
        boxSizer.Add(buttonSizer, 5, wxEXPAND | wxBOTTOM, 5)

        self.SetSizer(boxSizer)
        boxSizer.Fit(self)
        self.SetAutoLayout(1)

    def __addEvents(self):
        #EVT_BUTTON(self, 160, self.BrowseForImage)
        EVT_BUTTON(self, self.ID_TRANSFER, self.AddExit)
        EVT_BUTTON(self, self.ID_REMOVE_EXIT, self.RemoveExit)
        EVT_BUTTON(self, self.ID_LOAD, self.LoadRemoteVenues)

    def LoadRemoteVenues(self, event = None):
        URL = self.address.GetValue()
        self.__loadVenues(URL)
        if self.address.FindString(URL) == wxNOT_FOUND:
            wxLogDebug("Append address to combobox: %s " % URL)
            self.address.Append(URL)

    def LoadLocalVenues(self):
        self.__loadVenues(self.application.serverUrl)
        """
        for venue in self.application.venueList:
            if(venue.name != self.title.GetValue()):
                cd = ConnectionDescription(venue.name, venue.description,
                                           venue.uri)
                self.venues.Append(cd.name, cd)
        """

    def __loadVenues(self, URL):
        validVenue = false

        try:
            wxBeginBusyCursor()
            wxLogDebug("Load venues from: %s " % URL)
            server = Client.Handle(URL)
            if(server.IsValid()):
                venueList = []
                vl = server.get_proxy().GetVenues()
                for v in vl:
                    venueList.append(CreateVenueDescription(v))
                
                wxLogDebug("Got venues from server")
                validVenue = true
                self.venues.Clear()

                for venue in venueList:
                    if(venue.name != self.title.GetValue()):
                        cd = ConnectionDescription(venue.name,
                                                   venue.description,
                                                   venue.uri)
                        self.venues.Append(cd.name, cd)

                self.currentVenueUrl = URL
                self.address.SetValue(URL)

            else:
                wxLogMessage("Could not connect to venue\nat: %s " % URL)
                wxLog_GetActiveTarget().Flush()
                self.address.SetValue(self.currentVenueUrl)

            wxEndBusyCursor()

        except:
            wxEndBusyCursor()
            wxLogError("\ntype: %s \nvalue: %s" %(str(sys.exc_type) ,str(sys.exc_value)))
            wxLog_GetActiveTarget().Flush()                                              

    #def BrowseForImage(self, event):
    #    initial_dir = '/'
    #   imageDialog = ImageDialog(self, initial_dir)
    #   imageDialog.Show()
    #   if (imageDialog.ShowModal() == wxID_OK):
    #       file = imageDialog.GetFile()
    #       self.bitmap =  wxBitmap(file, wxBITMAP_TYPE_GIF)
    #       self.icon.SetBitmap(self.bitmap)
    #       self.Layout()
    #   imageDialog.Destroy()

    def AddExit(self, event):
        index = self.venues.GetSelection()
        if index != -1:
            venue = self.venues.GetClientData(index)
            
            existingExit = 0
            numExits = self.exits.GetCount()
            for index in range(numExits):
                exit = self.exits.GetClientData(index)
                if exit.uri == venue.uri:
                    existingExit = 1
                    break
            if existingExit:
                text = ""+venue.name+" is added already"
                exitExistDialog = wxMessageDialog(self, text, '',
                                                  wxOK | wxICON_INFORMATION)
                exitExistDialog.ShowModal()
                exitExistDialog.Destroy()
            else:
                self.exits.Append(venue.name, venue)

    def RemoveExit(self, event):
        index = self.exits.GetSelection()
        if index != -1:
            self.exits.Delete(index)
                
    def SetEncryption(self):
        toggled = self.encryptionPanel.encryptMediaButton.GetValue()
        key = ''
        if toggled:
            key = self.encryptionPanel.keyCtrl.GetValue()

        self.parent.SetEncryption(toggled, key)

    def SetStaticAddressing(self):
        sap = self.staticAddressingPanel
        if(sap.staticAddressingButton.GetValue()==1):
            
            self.parent.SetStaticVideo(sap.GetVideoAddress(), 
                                       sap.GetVideoPort(), 
                                       sap.GetVideoTtl())

            self.parent.SetStaticAudio(sap.GetAudioAddress(), 
                                       sap.GetAudioPort(), 
                                       sap.GetAudioTtl())

    def Ok(self):
        exitsList = []
        streams = []
        encryptTuple = (0, '')
        
        # Get Exits
        for index in range(0, self.exits.Number()):
            exit = self.exits.GetClientData(index)
            exitsList.append(exit)

        # Get Static Streams
        sap = self.staticAddressingPanel
        if(sap.staticAddressingButton.GetValue()==1):
            # Static Video
            svml = MulticastNetworkLocation(sap.GetVideoAddress(),
                                            int(sap.GetVideoPort()),
                                            int(sap.GetVideoTtl()))
            staticVideoCap = Capability(Capability.PRODUCER, Capability.VIDEO)
            streams.append(StreamDescription("Static Video",
                                                  "Static Video",
                                                  svml, staticVideoCap,
                                                  None, 1))
            # Static Audio
            saml = MulticastNetworkLocation(sap.GetAudioAddress(),
                                            int(sap.GetAudioPort()),
                                            int(sap.GetAudioTtl()))
            staticAudioCap = Capability(Capability.PRODUCER, Capability.AUDIO)
            streams.append(StreamDescription("Static Audio",
                                                  "Static Audio",
                                                  saml, staticAudioCap,
                                                  None, 1))

        # Get Encryption
        if self.encryptionPanel.encryptMediaButton.GetValue():
            encryptTuple = (1, self.encryptionPanel.keyCtrl.GetValue())

        # Make a venue description
        venue = VenueDescription(self.title.GetValue(),
                                 self.description.GetValue(),
                                 # Administrators missing
                                 (), encryptTuple, exitsList,
                                 streams)
        self.venue = venue

class EncryptionPanel(wxPanel):
    ID_BUTTON = wxNewId()

    def __init__(self, parent, id):
        wxPanel.__init__(self, parent, id)
        self.encryptMediaButton = wxCheckBox(self, self.ID_BUTTON,
                                             " Encrypt media ")
        self.keyText = wxStaticText(self, -1, "Optional key: ",
                                    size = wxSize(100,20))
        self.keyCtrl = wxTextCtrl(self, -1, "", size = wxSize(200,20))
        self.keyText.Enable(false)
        self.keyCtrl.Enable(false)
        self.__doLayout()
        self.__setEvents()

    def ClickEncryptionButton(self, event = None, value = None):
        if event == None:
            id = value
            self.encryptMediaButton.SetValue(value)
        else:
            id =  event.Checked()
        message = "Set encrypt media, value is: "+str(id)
        wxLogDebug(message)
        self.keyText.Enable(id)
        self.keyCtrl.Enable(id)

    def __setEvents(self):
        EVT_CHECKBOX(self, self.ID_BUTTON, self.ClickEncryptionButton)

    def __doLayout(self):
        sizer = wxStaticBoxSizer(wxStaticBox(self, -1, "Encryption"),
                                 wxVERTICAL)
        sizer.Add(self.encryptMediaButton, 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(25, 10)
        sizer2.Add(self.keyText , 0, wxEXPAND|wxALL, 5)
        sizer2.Add(self.keyCtrl, 1, wxEXPAND|wxALL, 5)
        sizer.Add(sizer2, 1, wxEXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

class StaticAddressingPanel(wxPanel):
    def __init__(self, parent, id):
        wxPanel.__init__(self, parent, id)
        self.ipAddressConverter = IpAddressConverter()
        self.staticAddressingButton = wxCheckBox(self, 5,
                                                 " Use Static Addressing")
        self.panel = wxPanel(self, -1)
        self.videoTitleText = wxStaticText(self.panel, -1, "Video (h261)",
                                           size = wxSize(100,20))
        self.audioTitleText = wxStaticText(self.panel, -1, "Audio (16kHz)",
                                           size = wxSize(100,20))
        self.videoAddressText = wxStaticText(self.panel, -1, "Address: ",
                                             size = wxSize(60,20))
        self.audioAddressText = wxStaticText(self.panel, -1, "Address: ",
                                             size = wxSize(60,20))
        self.videoPortText = wxStaticText(self.panel, -1, " Port: ",
                                          size = wxSize(45,20))
        self.audioPortText = wxStaticText(self.panel, -1, " Port: ",
                                          size = wxSize(45,20))
        self.videoTtlText = wxStaticText(self.panel, -1, " TTL:",
                                         size = wxSize(40,20))
        self.audioTtlText = wxStaticText(self.panel, -1, " TTL:",
                                         size = wxSize(40,20))
        self.videoIp1 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.videoIp2 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.videoIp3 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.videoIp4 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.videoPort = wxTextCtrl(self.panel, -1, "", size = wxSize(50,20),
                                    validator = DigitValidator(PORT))
        self.videoTtl = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(TTL))
        self.audioIp1 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.audioIp2 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.audioIp3 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.audioIp4 = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(IP))
        self.audioPort = wxTextCtrl(self.panel, -1, "", size = wxSize(50,20),
                                    validator =DigitValidator(PORT))
        self.audioTtl = wxTextCtrl(self.panel, -1, "", size = wxSize(30,20),
                                   validator = DigitValidator(TTL))

        if self.staticAddressingButton.GetValue():
            self.panel.Enable(true)
        else:
            self.panel.Enable(false)

        self.__doLayout()
        self.__setEvents()

    def __doLayout(self):
        staticAddressingSizer = wxStaticBoxSizer(wxStaticBox(self, -1,
                                             "Static Addressing"), wxVERTICAL)
        staticAddressingSizer.Add(self.staticAddressingButton, 0,
                                  wxEXPAND|wxALL, 5)

        panelSizer = wxBoxSizer(wxVERTICAL)

        videoIpSizer = wxBoxSizer(wxHORIZONTAL)
        videoIpSizer.Add(self.videoIp1, 0 , wxEXPAND)
        videoIpSizer.Add(self.videoIp2, 0 , wxEXPAND)
        videoIpSizer.Add(self.videoIp3, 0 , wxEXPAND)
        videoIpSizer.Add(self.videoIp4, 0 , wxEXPAND)

        audioIpSizer = wxBoxSizer(wxHORIZONTAL)
        audioIpSizer.Add(self.audioIp1, 0 , wxEXPAND)
        audioIpSizer.Add(self.audioIp2, 0 , wxEXPAND)
        audioIpSizer.Add(self.audioIp3, 0 , wxEXPAND)
        audioIpSizer.Add(self.audioIp4, 0 , wxEXPAND)

        videoTitleSizer = wxBoxSizer(wxHORIZONTAL)
        videoTitleSizer.Add(self.videoTitleText, 0, wxALIGN_CENTER)
        videoTitleSizer.Add(wxStaticLine(self.panel, -1), 1, wxALIGN_CENTER)

        panelSizer.Add(videoTitleSizer, 1 ,  wxEXPAND|wxLEFT|wxRIGHT|wxTOP, 10)

        flexSizer = wxFlexGridSizer(7, 7, 0, 0)
        flexSizer.Add(10,10)
        flexSizer.Add(self.videoAddressText, 0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer.Add(videoIpSizer, 0 , wxEXPAND)
        flexSizer.Add(self.videoPortText, 0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer.Add(self.videoPort, 0 , wxEXPAND)
        flexSizer.Add(self.videoTtlText,0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer.Add(self.videoTtl,0 , wxEXPAND)

        panelSizer.Add(flexSizer, 0 , wxEXPAND|wxALL, 5)

        audioTitleSizer = wxBoxSizer(wxHORIZONTAL)
        audioTitleSizer.Add(self.audioTitleText, 0, wxALIGN_CENTER)
        audioTitleSizer.Add(wxStaticLine(self.panel, -1), 1, wxALIGN_CENTER)

        panelSizer.Add(10,10)

        panelSizer.Add(audioTitleSizer, 1 , wxEXPAND|wxLEFT|wxRIGHT, 10)

        flexSizer2 = wxFlexGridSizer(7, 7, 0, 0)
        flexSizer2.Add(10,10)
        flexSizer2.Add(self.audioAddressText, 0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer2.Add(audioIpSizer, 0 , wxEXPAND)
        flexSizer2.Add(self.audioPortText, 0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer2.Add(self.audioPort, 0 , wxEXPAND)
        flexSizer2.Add(self.audioTtlText,0 , wxEXPAND|wxALIGN_CENTER)
        flexSizer2.Add(self.audioTtl,0 , wxEXPAND)

        panelSizer.Add(flexSizer2, 0 , wxEXPAND|wxALL, 5)
        self.panel.SetSizer(panelSizer)
        panelSizer.Fit(self.panel)

        staticAddressingSizer.Add(self.panel, 0 , wxEXPAND)

        self.SetSizer(staticAddressingSizer)
        staticAddressingSizer.Fit(self)
        self.SetAutoLayout(1)

    def __setEvents(self):
        EVT_CHECKBOX(self, 5, self.ClickStaticButton)

    def SetStaticVideo(self, videoIp, videoPort, videoTtl):
        videoList = self.ipAddressConverter.StringToIp(videoIp)
        self.videoPort.SetValue(str(videoPort))
        self.videoIp1.SetValue(str(videoList[0]))
        self.videoIp2.SetValue(str(videoList[1]))
        self.videoIp3.SetValue(str(videoList[2]))
        self.videoIp4.SetValue(str(videoList[3]))
        self.videoTtl.SetValue(str(videoTtl))

    def SetStaticAudio(self, audioIp, audioPort, audioTtl):
        audioList = self.ipAddressConverter.StringToIp(audioIp)
        self.audioPort.SetValue(str(audioPort))
        self.audioIp1.SetValue(str(audioList[0]))
        self.audioIp2.SetValue(str(audioList[1]))
        self.audioIp3.SetValue(str(audioList[2]))
        self.audioIp4.SetValue(str(audioList[3]))
        self.audioTtl.SetValue(str(audioTtl))

    def GetVideoAddress(self):
        return self.ipAddressConverter.IpToString(self.videoIp1.GetValue(), \
                                             self.videoIp2.GetValue(), \
                                             self.videoIp3.GetValue(), \
                                             self.videoIp4.GetValue())
    def GetAudioAddress(self):
        return self.ipAddressConverter.IpToString(self.audioIp1.GetValue(), \
                                             self.audioIp2.GetValue(), \
                                             self.audioIp3.GetValue(), \
                                             self.audioIp4.GetValue())

    def GetVideoPort(self):
        return self.videoPort.GetValue()

    def GetAudioPort(self):
        return self.audioPort.GetValue()

    def GetVideoTtl(self):
        return self.videoTtl.GetValue()

    def GetAudioTtl(self):
        return self.audioTtl.GetValue()

    def ClickStaticButton(self, event):
        if event.Checked():
            self.panel.Enable(true)
        else:
            self.panel.Enable(false)

    def Validate(self):
        if(self.staticAddressingButton.GetValue()):
            return self.panel.Validate()
        else:
            return true

class AddVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, app)
        self.parent = parent
        self.SetLabel('Add Venue')
        self.LoadLocalVenues()
        self.encryptionPanel.ClickEncryptionButton(None,
                                                   self.application.encrypt)
        EVT_BUTTON (self.okButton, wxID_OK, self.OnOK)
        self.ShowModal()

    def OnOK (self, event):
        wxBeginBusyCursor()
        if(VenueParamFrame.Validate(self)):
            if(self.staticAddressingPanel.Validate()):
                self.Ok()
                try:
                    wxLogInfo("Add venue")
                    self.parent.AddVenue(self.venue)
                    # from super class
                    self.SetStaticAddressing() 
                    # from super class
                    self.SetEncryption() 

                except:
                    wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type) ,
                                                           str(sys.exc_value)))
                    wxLog_GetActiveTarget().Flush()

                self.Hide()
        wxEndBusyCursor()


class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, app)
        wxBeginBusyCursor()
        self.parent = parent
        self.SetLabel('Modify Venue')
        self.__loadCurrentVenueInfo(venueList)
        self.LoadLocalVenues()
        wxEndBusyCursor()

        EVT_BUTTON (self.okButton, wxID_OK, self.OnOK)
        self.ShowModal()

    def OnOK (self, event):
        wxBeginBusyCursor()
        if(VenueParamFrame.Validate(self)):
            if(self.staticAddressingPanel.Validate()):
#FIXME - This is obviously an immediately-before-release fix;
#        it needs to be resolved corectly
                venueUri = self.venue.uri
                self.Ok()
                self.venue.uri = venueUri
                try:
                    wxLogInfo("Modify venue")
                    self.parent.ModifyVenue(self.venue)
                    # from super class
                    self.SetStaticAddressing() 
                    # from super class
                    self.SetEncryption()
                except:
                    wxLogError("\ntype: %s \nvalue: %s" % (str(sys.exc_type),
                                                           str(sys.exc_value)))
                    wxLog_GetActiveTarget().Flush()

                self.Hide()

        wxEndBusyCursor()

    def __loadCurrentVenueInfo(self, venueList):
        item = venueList.GetSelection()
        self.venue = venueList.GetClientData(item)

        self.title.AppendText(self.venue.name)
        self.description.AppendText(self.venue.description)

        wxLogDebug("Get venue information")
        self.application.SetCurrentVenue(self.venue)
        venueC = self.application.currentVenueClient

        if(self.venue.encryptMedia):
            wxLogDebug("We have a key %s" % self.venue.encryptionKey)
            self.encryptionPanel.ClickEncryptionButton(None, true)
            self.encryptionPanel.keyCtrl.SetValue(self.venue.encryptionKey)
        else:
            wxLogDebug("Key is None")
            self.encryptionPanel.ClickEncryptionButton(None, false)

        for e in self.venue.connections.values():
            self.exits.Append(e.name, e)
            wxLogDebug("    %s" % e.name)

        if(len(self.venue.streams)==0):
            wxLogDebug("No static streams to load")
            self.staticAddressingPanel.panel.Enable(false)
            self.staticAddressingPanel.staticAddressingButton.SetValue(false)
        elif(len(self.venue.streams)>2):
            wxLogError("Venue returned more than 2 static streams")
            wxLog_GetActiveTarget().Flush()
        else:
            self.staticAddressingPanel.panel.Enable(true)
            self.staticAddressingPanel.staticAddressingButton.SetValue(true)
            for stream in self.venue.streams:
                if(stream.capability.type == Capability.VIDEO):
                    sl = stream.location
                    self.staticAddressingPanel.SetStaticVideo(sl.host, sl.port,
                                                              sl.ttl)
                elif(stream.capability.type == Capability.AUDIO):
                    sl = stream.location
                    self.staticAddressingPanel.SetStaticAudio(sl.host, sl.port,
                                                              sl.ttl)

        wxLog_GetActiveTarget().Flush()


class AdministratorParamFrame(wxDialog):
    def __init__(self, *args):
        wxDialog.__init__(self, *args)
        self.Centre()
        self.SetSize(wxSize(400, 40))
        self.text = wxStaticText(self, -1, "Please, fill in the distinguished name for the administator you want to add.")
        self.informationBox = wxStaticBox(self, -1, "Information")
        self.nameLabel =  wxStaticText(self, -1, "DN Name:")
        self.name =  wxTextCtrl(self, -1, "",  size = wxSize(400, 20))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")
        self.doLayout()

    def doLayout(self):
        topSizer = wxBoxSizer(wxVERTICAL)
        boxSizer = wxStaticBoxSizer(self.informationBox, wxVERTICAL)

        boxSizer.Add(self.text, 0, wxALL, 10)
        paramFrameSizer = wxFlexGridSizer(10, 2, 10, 10)
        paramFrameSizer.Add(self.nameLabel, 0, wxALIGN_RIGHT)
        paramFrameSizer.Add(self.name, 0, wxEXPAND)
        paramFrameSizer.AddGrowableCol(2)
        boxSizer.Add(paramFrameSizer, 1,  wxEXPAND|wxALL, 10)

        buttonSizer =  wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(20, 20, 1)
        buttonSizer.Add(self.okButton, 0)
        buttonSizer.Add(10, 10)
        buttonSizer.Add(self.cancelButton, 0)
        buttonSizer.Add(20, 20, 1)

        topSizer.Add(boxSizer, 1, wxALL | wxEXPAND, 10)
        topSizer.Add(buttonSizer, 0, wxEXPAND | wxBOTTOM, 5)

        self.SetSizer(topSizer)
        topSizer.Fit(self)
        self.SetAutoLayout(1)

class AddAdministratorFrame(AdministratorParamFrame):
    def __init__(self, parent, id, title):
        AdministratorParamFrame.__init__(self, parent, id, title)
        self.parent = parent
        if (self.ShowModal() == wxID_OK ):
            self.parent.InsertAdministrator(self.name.GetValue())

        self.Destroy();

class ModifyAdministratorFrame(AdministratorParamFrame):
    def __init__(self, parent, id, title, oldName):
        AdministratorParamFrame.__init__(self, parent, id, title)
        self.text.SetLabel("Please, fill in a new distinguished name for the administator")
        self.parent = parent
        self.name.Clear()
        self.name.AppendText(oldName)
        if (self.ShowModal() == wxID_OK ):
            self.parent.ModifyAdministrator(oldName, self.name.GetValue())
        self.Destroy();

        '''class RemoteServerUrlDialog(wxDialog):
        def __init__(self, parent, id, title):
            wxDialog.__init__(self, parent, id, title)
            self.Centre()
            self.okButton = wxButton(self, wxID_OK, "Ok")
            self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
            info = "Please, enter remote server URL address"
            self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
            self.addressText = wxStaticText(self, -1, "Address: ", style=wxALIGN_LEFT)
            self.address = wxTextCtrl(self, -1, "", size = wxSize(300,20))
            self.__doLayout()

            def __doLayout(self):
                sizer = wxBoxSizer(wxVERTICAL)
                sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
                sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)

                sizer2 = wxBoxSizer(wxHORIZONTAL)
                sizer2.Add(self.addressText, 0)
                sizer2.Add(self.address, 1, wxEXPAND)

                sizer1.Add(sizer2, 0, wxEXPAND | wxALL, 20)

                sizer3 =  wxBoxSizer(wxHORIZONTAL)
                sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
                sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

                sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
                sizer.Add(sizer3, 0, wxALIGN_CENTER)
                self.SetSizer(sizer)
                sizer.Fit(self)
                self.SetAutoLayout(1)
'''

class DigitValidator(wxPyValidator):
    def __init__(self, flag):
        wxPyValidator.__init__(self)
        self.flag = flag
        EVT_CHAR(self, self.OnChar)

    def Clone(self):
        return DigitValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        index = 0
        for x in val:
            index = index+1
            if x not in string.digits:
                wxLogMessage("Add venue")("Please, use digits for the mask!")
                wxLog_GetActiveTarget().Flush()
                return false
        if (self.flag == IP or self.flag == IP_1) and index == 0:
            wxLogMessage("Please, fill in all IP Address fields!")
            wxLog_GetActiveTarget().Flush()
            return false

        elif (self.flag == PORT) and index == 0:
            wxLogMessage("Please, fill in port for static addressing!")
            wxLog_GetActiveTarget().Flush()
            return false

        elif (self.flag == TTL) and index == 0:
            wxLogMessage("Please, fill in time to live (ttl) for static addressing!")
            wxLog_GetActiveTarget().Flush()
            return false

        elif self.flag == PORT:
            return true

        elif self.flag == TTL and (int(val)<0 or int(val)>127):
            wxLogMessage("Time to live should be a value between 0 - 127")
            wxLog_GetActiveTarget().Flush()
            return false

        elif self.flag == IP and (int(val)<0 or int(val)>255):
            wxLogMessage("Allowed values for IP Address are between 224.0.0.0 - 239.225.225.225")
            wxLog_GetActiveTarget().Flush()
            return false

        elif self.flag == IP_1 and (int(val)<224 or int(val)>239):
            wxLogMessage("Allowed values for IP Address are between 224.0.0.0 - 239.225.225.225")
            wxLog_GetActiveTarget().Flush()
            return false

        elif index == 0 and self.flag == MASK:
            wxLogMessage("Please, fill in mask!")
            wxLog_GetActiveTarget().Flush()
            return false

        elif self.flag == MASK and (int(val)>24 or int(val)<0):
            wxLogMessage("Allowed values for mask are between 0 - 24")
            wxLog_GetActiveTarget().Flush()
            return false

        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

    def OnChar(self, event):
        key = event.KeyCode()
        if key < WXK_SPACE or key == WXK_DELETE or key > 255:
            event.Skip()
            return

        if chr(key) in string.digits:
            event.Skip()
            return

        if not wxValidator_IsSilent():
            wxBell()

        # Returning without calling event.Skip eats the event before it
        # gets to the text control
        return

class TextValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)

    def Clone(self):
        return TextValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()

        if len(val) < 1:
            wxLogMessage("Please, fill in your name and description")
            wxLog_GetActiveTarget().Flush()
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

class IpAddressConverter:
    def __init__(self):
        self.ipString = ""
        self.ipIntList = []

    def StringToIp(self, ipString):
        ipStringList = string.split(ipString, '.')
        self.ipIntList = map(string.atoi, ipStringList)
        return self.ipIntList

    def IpToString(self, ip1, ip2, ip3, ip4):
        self.ipString = str(ip1)+'.'+str(ip2)+'.'+str(ip3)+'.'+str(ip4)
        return self.ipString

if __name__ == "__main__":
    wxInitAllImageHandlers()
    app = VenueManagementClient()
    app.MainLoop()
