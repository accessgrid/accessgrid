#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        VenueManagement.py
# Purpose:     This is the user interface for Virtual Venues Server Management
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueManagement.py,v 1.138 2004-07-26 17:35:01 lefvert Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueManagement.py,v 1.138 2004-07-26 17:35:01 lefvert Exp $"

# Standard imports
import sys
import os
if sys.platform=="darwin":
    # On osx pyGlobus/globus need to be loaded before various modules such as socket.
    import pyGlobus.ioc
import string
import time
import re
import getopt
import webbrowser
import cPickle

# UI imports
from wxPython.wx import *
from wxPython.lib.imagebrowser import *

# Access Grid imports
from AccessGrid.Descriptions import StreamDescription, ConnectionDescription
from AccessGrid.Descriptions import VenueDescription, CreateVenueDescription
from AccessGrid.Descriptions import Capability
from AccessGrid.Security.CertificateManager import CertificateManager
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid import icons
from AccessGrid.UIUtilities import AboutDialog, MessageDialog, ErrorDialog
from AccessGrid.Utilities import VENUE_MANAGEMENT_LOG
from AccessGrid.Security.wxgui.AuthorizationUI import AuthorizationUIPanel, AuthorizationUIDialog
from AccessGrid.Security.AuthorizationManager import AuthorizationManagerIW
from AccessGrid import Log
from AccessGrid.hosting import Client
from AccessGrid.VenueServer import VenueServerIW
from AccessGrid.Venue import VenueIW
from AccessGrid import Toolkit
from AccessGrid.Platform.Config import UserConfig, AGTkConfig

from AccessGrid.UIUtilities import AddURLBaseDialog, EditURLBaseDialog

log = Log.GetLogger(Log.VenueManagement)


class VenueManagementClient(wxApp):
    """
    VenueManagementClient.

    The VenueManagementClient class creates the main frame of the
    application as well as the VenueManagementTabs and statusbar.
    """
    ID_FILE_EXIT = wxNewId()
    ID_SERVER_CHECKPOINT = wxNewId()
    ID_SERVER_SHUTDOWN = wxNewId()
    ID_HELP_ABOUT = wxNewId()
    ID_HELP_MANUAL =  wxNewId()

    ID_MYSERVERS_GOTODEFAULT = wxNewId()
    ID_MYSERVERS_SETDEFAULT = wxNewId()
    ID_MYSERVERS_ADD = wxNewId()
    ID_MYSERVERS_EDIT = wxNewId()
        
    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        self.agtkConf = AGTkConfig.instance()
        self.manual_url = os.path.join(self.agtkConf.GetDocDir(),
                                       "VenueManagementManual",
                                       "VenueManagementManualHTML.htm")
        self.server = None
        self.serverUrl = None
        self.currentVenueClient = None
        self.currentVenue = None
        self.encrypt = false
        self.venueList = []
        self.help_open = 0
          
        self.frame = wxFrame(NULL, -1, "Venue Management" )
        self.address = VenueServerAddress(self.frame, self)
        self.tabs = VenueManagementTabs(self.frame, -1, self)
        self.statusbar = self.frame.CreateStatusBar(1)

        self.menubar = wxMenuBar()
        self.myServersDict = {}
        self.myServersMenuIds = {}
        #self.homeServer = 'https://localhost/VenueServer'
        self.userConf = UserConfig.instance()
        self.myServersFile = os.path.join(self.userConf.GetConfigDir(), "myServers.txt" )
        

        self.__doLayout()
        self.__setMenuBar()
        self.__setProperties()
        self.__setEvents()
        self.__loadMyServers()
        self.EnableMenu(0)

        self.app = Toolkit.WXGUIApplication()
        self.app.Initialize("VenueManagement")

        return true

    def __setEvents(self):
        # File menu
        EVT_MENU(self, self.ID_FILE_EXIT, self.Exit)

        # Server menu
        EVT_MENU(self, self.ID_SERVER_CHECKPOINT, self.Checkpoint)
        EVT_MENU(self, self.ID_SERVER_SHUTDOWN, self.Shutdown)

        # Help menu
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialog)
        EVT_MENU(self, self.ID_HELP_MANUAL,
                 lambda event, url=self.manual_url: self.OpenHelpURL(url))

        # My Servers Menu
        #EVT_MENU(self, self.ID_MYSERVERS_GOTODEFAULT, self.GoToDefaultServerCB)
        #EVT_MENU(self, self.ID_MYSERVERS_SETDEFAULT, self.SetAsDefaultServerCB)
        EVT_MENU(self, self.ID_MYSERVERS_ADD, self.AddToMyServersCB)
        EVT_MENU(self, self.ID_MYSERVERS_EDIT, self.EditMyServersCB)

        EVT_CLOSE(self, self.OnCloseWindow)
        
    def __setMenuBar(self):
        self.frame.SetMenuBar(self.menubar)

        self.fileMenu = wxMenu()
        self.fileMenu.Append(self.ID_FILE_EXIT,"&Exit", "Quit Venue Management")
        self.menubar.Append(self.fileMenu, "&File")

        self.serverMenu = wxMenu()
        self.serverMenu.Append(self.ID_SERVER_CHECKPOINT, "&Checkpoint",
                               "Checkpoint the server")
        
        self.serverMenu.Append(self.ID_SERVER_SHUTDOWN, "&Shutdown",
                               "Shutdown the server")

        self.menubar.Append(self.serverMenu, "&Server")
        self.myServersMenu = wxMenu()
        #self.myServersMenu.Append(self.ID_MYSERVERS_GOTODEFAULT, "Go to Home Server",
        #                          "Go to default venue")
        #self.myServersMenu.Append(self.ID_MYSERVERS_SETDEFAULT, "Set as Home Server",
        #                     "Set current server as default")
        #self.myServersMenu.AppendSeparator()
    
        self.myServersMenu.Append(self.ID_MYSERVERS_ADD, "Add &Current Server...",
                             "Add this server to your list of servers")
        self.myServersMenu.Append(self.ID_MYSERVERS_EDIT, "Edit My &Servers...",
                             "Edit your servers")
        self.myServersMenu.AppendSeparator()

        self.menubar.Append(self.myServersMenu, '&My Servers')
        
        
        self.helpMenu = wxMenu()
        self.helpMenu.Append(self.ID_HELP_MANUAL, "Venue Management &Help",
                             "Venue Management Manual")
        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(self.ID_HELP_ABOUT, "&About\t", "Information about the application")
        
        self.menubar.Append(self.helpMenu, "&Help")

    def SetLogger(self, debugMode):
        userConfig = UserConfig.instance()
        hdlr = Log.FileHandler(os.path.join(userConfig.GetConfigDir(), "VenueManagement.log"))
        hdlr.setFormatter(Log.GetFormatter())
        hdlr.setLevel(Log.DEBUG)
        Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())

        if debugMode:
            hdlr = Log.StreamHandler() 
            hdlr.setFormatter(Log.GetLowDetailFormatter())
            hdlr.setLevel(Log.DEBUG)
            Log.HandleLoggers(hdlr, Log.GetDefaultLoggers())
               
    def __setProperties(self):
        self.frame.SetIcon(icons.getAGIconIcon())
        self.frame.SetSize(wxSize(500, 350))
        self.SetTopWindow(self.frame)
        self.frame.Show()

    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
        box.Add(self.address, 0, wxEXPAND|wxALL)
        box.Add(self.tabs, 1, wxEXPAND)
        self.frame.SetSizer(box)

    def __fixName(self, name):
        list = name.split('/')
        return list[2]

    def __loadMyServers(self):
        
        # Delete existing menu items
        for ID in self.myServersMenuIds.values():
            self.myServersMenu.Delete(ID)
            
        self.myServersMenuIds = {}

        # Get this info from file
        if os.path.exists(self.myServersFile):
            try:
                myServersFileH = open(self.myServersFile, 'r')
            except:
                myServersFileH = None
                log.exception("Failed to load MyServers file")
        
            try:
                self.myServersDict = cPickle.load(myServersFileH)
              
            except:
                self.myServersDict = []
                log.exception("Failed to pickle MyServers file")

            myServersFileH.close()

        else:
            log.debug("There is no my servers file to load.")
                   
        # Create menu items
        for name in self.myServersDict.keys():
            ID = wxNewId()
            self.myServersMenuIds[name] = ID
            url = self.myServersDict[name]
            text = "Go to: " + url
            self.myServersMenu.Append(ID, name, text)
            EVT_MENU(self, ID, self.GoToMenuAddressCB)

    def __saveMyServersToFile(self):
        """
        This method synchs the saved servers list to disk
        """
        if os.path.exists(self.myServersFile):
            myServersFileH = open(self.myServersFile, 'w')
        else:
            myServersFileH = open(self.myServersFile, 'aw')
            
        cPickle.dump(self.myServersDict, myServersFileH)
        myServersFileH.close()

    def EnableMenu(self, flag):
        #self.myServersMenu.Enable(self.ID_MYSERVERS_SETDEFAULT, flag)
        self.myServersMenu.Enable(self.ID_MYSERVERS_ADD, flag)
        self.serverMenu.Enable(self.ID_SERVER_CHECKPOINT , flag)
        self.serverMenu.Enable(self.ID_SERVER_SHUTDOWN, flag)
        
    #def GoToDefaultServerCB(self,event):
    #    '''
    #    Connect to default venue server.
    #    '''
    #    serverUrl = self.homeServer
    #    self.ConnectToServer(serverUrl)

    #def SetAsDefaultServerCB(self,event):
    #    '''
    #    Set default venue server.
    #    '''
    #    self.homeServer = self.serverUrl 
        
    def AddToMyServersCB(self, event):
        #url = self.serverClient.GetServer()
        #name = self.serverClient.GetServerName()

        url =  self.serverUrl
        name = self.serverUrl
        # myServersDict = self.controller.GetMyServers()

        myServersDict = self.myServersDict
              
        if not url:
            log.info("Invalid server url %s", url)
            #MessageDialog(None,"Error adding server to server list", "Add Server Error",
            #              style=wxOK|wxICON_INFORMATION)
            
            
        if url in myServersDict.values():
            #
            # Server URL already in list
            #
            for n in myServersDict.keys():
                if myServersDict[n] == url:
                    name = n
            text = "This server is already added to your servers as "+"'"+name+"'"
            MessageDialog(self.frame,text, "Add Server Error",
                          style=wxOK|wxICON_INFORMATION)
           
        else:
            #
            # Server url not in list
            # - Prompt for name and validate
            #
            serverName = None
            dialog = AddURLBaseDialog(self.frame, -1, self.__fixName(name), type = 'server')
            if (dialog.ShowModal() == wxID_OK):
                serverName = dialog.GetValue()
            dialog.Destroy()

            if serverName:
                addServer = 1
                if myServersDict.has_key(serverName):
                    #
                    # Server name already in list
                    #
                                       
                    info = "A server with the same name is already added, do you want to overwrite it?"

                    dlg = wxMessageDialog(self.frame, info, "Duplicated Server",
                                          style = wxICON_INFORMATION | wxOK | wxCANCEL)
                                        
                    if dlg.ShowModal() == wxID_OK:
                        # 
                        # User chose to replace the file 
                        #
                        self.RemoveFromMyServers(serverName)
                                                
                        addServer = 1
                    else:
                        # 
                        # User chose to not replace the file
                        #
                        addServer = 0
                else:
                    #
                    # Server name not in list
                    #
                    addServer = 1
                    
                if addServer:
                    try:
                        self.AddToMyServers(serverName,url)
                        self.__saveMyServersToFile()
                                               
                    except:
                        log.exception("Error adding server")
                        MessageDialog(self.frame,"Error adding server to server list", "Add Server Error",
                                      style=wxOK|wxICON_WARNING)
        
    def EditMyServersCB(self, event):
        myServersMenu = None
        #serversDict = self.controller.GetMyServers()
        
        editMyServersDialog = EditURLBaseDialog(self.frame, -1, "Edit your servers", 
                                                self.myServersDict, type = 'server')
        if (editMyServersDialog.ShowModal() == wxID_OK):
            self.myServersDict = editMyServersDialog.GetValue()
            
            try:
                self.__saveMyServersToFile()
                self.__loadMyServers()
            
            except:
                log.exception('Error saving changes to my servers","Edit Servers Error')
                MessageDialog(self.frame,"Error saving changes to my servers", "Add Server Error",
                              style=wxOK|wxICON_WARNING)
        

        editMyServersDialog.Destroy()

    def GoToMenuAddressCB(self, event):
        name = self.menubar.GetLabel(event.GetId())
        serverUrl = self.myServersDict[name]
        self.ConnectToServer(serverUrl)
            
    def AddToMyServers(self,name,url):
        ID = wxNewId()
        text = "Go to: " + url
        self.myServersMenu.Append(ID, name, text)
        self.myServersMenuIds[name] = ID
        self.myServersDict[name] = url
        EVT_MENU(self, ID, self.GoToMenuAddressCB)
    
    def RemoveFromMyServers(self,serverName):
        # Remove the server from my servers menu list
        menuId = self.myServersMenuIds[serverName]
        self.myServersMenu.Remove(menuId)
    
        # Remove it from the dictionary
        del self.myServersMenuIds[serverName]
        del self.myServersDict[name]

    def OpenHelpURL(self, url):
        """
        """
        needNewWindow = not self.help_open
        
        if needNewWindow:
            self.help_open = 1
            self.browser = webbrowser.get()
            
        self.browser.open(url, needNewWindow)

    def OpenAboutDialog(self, event):
        aboutDialog = AboutDialog(self.frame)
        aboutDialog.ShowModal()
        aboutDialog.Destroy()
        
    def Exit(self, event):
        self.frame.Close(true)

    def Checkpoint(self, event):
        self.server.Checkpoint()
    
    def Shutdown(self, event):
        self.server.Shutdown(0)
    
    def OnCloseWindow(self, event):
        self.frame.Destroy()
     
    def ConnectToServer(self, URL):
        log.debug("VenueManagementClient.ConnectToServer: Connect to server %s" %URL)
        
        certMgt = Toolkit.Application.instance().GetCertificateManager()
        if not certMgt.HaveValidProxy():
            log.debug("VenueManagementClient.ConnectToServer:: no valid proxy")
            certMgt.CreateProxy()
        try:
            wxBeginBusyCursor()
            log.debug("VenueManagementClient.ConnectToServer: Connect to server")
            self.server = VenueServerIW(URL)
            log.debug("VenueManagementClient.ConnectToServer: Get venues from server")
            self.venueList = {}
            vl = self.server.GetVenues()
            for v in vl:
                self.venueList[v.uri] = v
                
            self.serverUrl = URL

            vp = self.tabs.venuesPanel
            vlp = vp.venuesListPanel
            
            # Clear out old ones
            vlp.venuesList.Clear()
            vp.venueProfilePanel.ClearAllFields()
            
            # Get default venue
            defaultVenueUrl = self.server.GetDefaultVenue()
            
            # Fill in venues
            
            if len(self.venueList) != 0 :
                for venue in self.venueList.values():
                    log.debug("VenueManagementClient.ConnectToServer: Add venue %s" % venue.name)
                    vlp.venuesList.Append(venue.name, venue)
                    
                    # Set default venue
                    if venue.uri == defaultVenueUrl:
                        vlp.SetDefaultVenue(venue, init = true)
                        
                currentVenue = vlp.venuesList.GetClientData(0)
                vp.venueProfilePanel.ChangeCurrentVenue(currentVenue)
                vlp.venuesList.SetSelection(0)
            else:
                log.debug("VenueManagementClient.ConnectToServer: No venues in server")
                vp.venueProfilePanel.ChangeCurrentVenue(None)
            
            # fill in multicast address
            ip = self.server.GetBaseAddress()
            mask = str(self.server.GetAddressMask())
            
            method = self.server.GetAddressAllocationMethod()
            
            dp = self.tabs.configurationPanel.detailPanel
            dp.ipAddress.SetLabel(ip+'/'+mask)

            if method == MulticastAddressAllocator.RANDOM:
                log.debug("VenueManagementClient.ConnectToServer: Set multicast address to: RANDOM")
                dp.ipAddress.Enable(false)
                dp.changeButton.Enable(false)
                dp.randomButton.SetValue(true)
            else:
                log.debug("VenueManagementClient.ConnectToServer: Set multicast address to: INTERVAL, ip: %s, mask: %s" %(ip, mask))
                dp.ipAddress.Enable(true)
                dp.changeButton.Enable(true)
                dp.intervalButton.SetValue(true)

            # fill in address
            if self.address.addressText.FindString(self.serverUrl) == wxNOT_FOUND:
                log.debug("VenueManagementClient.ConnectToServer: Set address: %s" %self.serverUrl)
                self.address.addressText.Append(self.serverUrl)

            self.address.addressText.SetValue(self.serverUrl)

            # fill in encryption
            key = self.server.GetEncryptAllMedia()
            log.debug("VenueManagementClient.ConnectToServer: Set server encryption key: %s" % key)
            dp.encryptionButton.SetValue(key)
            self.encrypt = key

            self.tabs.Enable(true)
            self.EnableMenu(1)
            
            wxEndBusyCursor()
            
        except Exception, e:
            wxEndBusyCursor()
            text = "You were unable to connect to the venue server at:\n%s." % URL
            lStr = "Can not connect."
            if hasattr(e, "string"):
                text += "\n%s" % e.string
                lStr += "(%s)" % e.string

            log.exception("VenueManagementClient.ConnectToServer: %s:", lStr)
            MessageDialog(None, text, "Unable To Connect",
                          style=wxOK|wxICON_INFORMATION)
            
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
            log.debug("VenueManagementClient.SetCurrentVenue: Set current venue to none")
            self.currentVenue = None
            self.currentVenueClient = None

        elif self.currentVenue == None or self.currentVenue.uri != venue.uri:
            log.debug("VenueManagementClient.SetCurrentVenue: Set current venue to: %s, %s" % (str(venue.name),
                                                         str(venue.uri)))
            self.currentVenue = venue
            self.currentVenueClient = VenueIW(venue.uri)

    def SetVenueEncryption(self, venue, value = 0, key = ''):
        self.SetCurrentVenue(venue)
        log.debug("VenueManagementClient.SetVenueEncryption: Set venue encryption: %s using key: %s for venue: %s" 
                     % (str(value), str(key), str(venue.uri)))
        self.currentVenueClient.SetEncryptMedia(int(value), str(key))

    def DeleteVenue(self, venue):
        log.debug("VenueManagementClient.DeleteVenue: Delete venue: %s" %str(venue.uri))
        self.server.RemoveVenue(venue.uri)
        if self.venueList.has_key(venue.uri):
            del self.venueList[venue.uri]

    def AddAdministrator(self, dnName):
        log.debug("VenueManagementClient.AddAdministrator: Add administrator: %s" %dnName)
        self.server.AddAdministrator(dnName)

    def DeleteAdministrator(self, dnName):
        log.debug("VenueManagementClient.DeleteAdministrator: Delete administrator: %s" %dnName)
        self.server.RemoveAdministrator(dnName)

    def ModifyAdministrator(self, oldName, dnName):
        log.debug("VenueManagementClient.Modify administrator: %s with new dnName: %s" %
                   (oldName,dnName))
        if(dnName != oldName):
            self.server.AddAdministrator(dnName)
            self.server.RemoveAdministrator(oldName)

    def SetRandom(self):
        log.debug("VenueManagementClient.SetRandom: Set random address allocation method")
        self.server.SetAddressAllocationMethod(MulticastAddressAllocator.RANDOM)

    def SetInterval(self, address, mask):
        log.debug("VenueManagementClient.SetInterval: Set interval address allocation method with address: %s, mask: %s" %(str(address), mask))
        self.server.SetBaseAddress(address)
        self.server.SetAddressMask(mask)
        self.server.SetAddressAllocationMethod(MulticastAddressAllocator.INTERVAL)

    def SetEncryption(self, value):
        log.debug("VenueManagementClient.SetEncryption: %s" %str(value))
        self.server.SetEncryptAllMedia(int(value))
        self.encrypt = int(value)

class VenueServerAddress(wxPanel):
    ID_BUTTON = wxNewId()
    ID_ADDRESS = wxNewId()

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
                        wxDefaultSize, wxNO_BORDER)
        self.application = application
        self.addressLabel =  wxStaticText(self, -1,'Venue Server Address:')
        self.defaultServer = 'https://localhost/VenueServer'
        self.serverList = ['https://localhost/VenueServer']
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
        self.securityPanel = SecurityPanel(self, application)
        self.AddPage(self.venuesPanel, "Venues")
        self.AddPage(self.configurationPanel, "Configuration")
        self.AddPage(self.securityPanel, "Security")
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

            for e in venue.connections:
                self.exits.Append(e.name, e)

            self.exitsLabel.Show()
            self.url.Show()
            self.urlLabel.Show()
            self.description.SetValue(venue.description)
            self.exits.Show()

    def __doLayout(self):
        self.venueProfileBox = wxStaticBox(self, -1, "Profile")
        self.venueProfileBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        venueListProfileSizer = wxStaticBoxSizer(self.venueProfileBox,
                                                 wxVERTICAL)
        venueListProfileSizer.Add(wxSize(5, 5))
        venueListProfileSizer.Add(self.description, 4,
                                  wxEXPAND|wxLEFT|wxRIGHT, 15)
        venueListProfileSizer.Add(wxSize(5, 10))
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
    DEFAULT_STRING = " (default)"

    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition,
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.parent = parent
        self.application = application
        self.venuesListBox = wxStaticBox(self, -1, "Venues",
                                         name = 'venueListBox')
        self.venuesListBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
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
        self.defaultVenue = None
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
                log.debug("VenueListPanel: EvtListBox: Change current venue")
                self.parent.venueProfilePanel.ChangeCurrentVenue(data)

            except:
                log.exception("VenueListPanel: EvtListBox: Can not change current venue")
                
           
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


            # Check to see if we are deleting the default venue
            defaultVenueUrl = ""

            try:
                defaultVenueUrl = self.application.server.GetDefaultVenue()
            except:
                log.exception("VenueListPanel.DeleteVenue: Could not get default venue")
              
            # Default venue
            if defaultVenueUrl == venueToDelete.uri:
                text =  "'"+ venueToDelete.name +"'"+\
                       " is the default venue on this server.  If you delete this venue, \nit is highly recommended that you select another venue as default from the \n'Modify Venue' dialog.  \n\nAre you sure you want to delete this venue?" 
                
            else:
                text =  "Are you sure you want to delete " + venueToDelete.name +"?"
               

            text2 = "Delete venue"
            message = wxMessageDialog(self, text, text2,
                                      style = wxOK|wxCANCEL|wxICON_INFORMATION)

            if(message.ShowModal()==wxID_OK):

                try:
                    self.application.DeleteVenue(venueToDelete)
                    if defaultVenueUrl == venueToDelete.uri:
                        # We just deleted default venue
                        self.defaultVenue = None

                except Exception, e:
                    if "string" in dir(e) and e.string == "NotAuthorized":
                        text = "You and are not authorized to administrate \
                                this server.\n"
                        MessageDialog(None, text, "Authorization Error",
                                      wxOK|wxICON_WARNING)
                        log.info("VenueManagementClient.ConnectToServer: \
                                  Not authorized to administrate the server.")
                    else:
                        log.exception("VenueListPanel.DeleteVenue: Could not \
                                       delete venue %s" %venueToDelete.name)
                        text = "The venue could not be deleted" + venueToDelete.name
                        ErrorDialog(None, text, "Delete Venue Error",
                                    logFile = VENUE_MANAGEMENT_LOG)
                except:
                    log.exception("VenueListPanel.DeleteVenue: Could \
                                   not delete venue %s" %venueToDelete.name)
                    text = "The venue could not be deleted" + venueToDelete.name
                    ErrorDialog(None, text, "Delete Venue Error",
                                logFile = VENUE_MANAGEMENT_LOG)
                 
                else:
                    self.venuesList.Delete(index)

                    if self.venuesList.Number() > 0:
                        self.venuesList.SetSelection(0)
                        venue = self.venuesList.GetClientData(0)

                        try:
                            log.debug("VenueListPanel.DeleteVenue: \
                                       Change current venue")
                            self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

                        except:
                            log.exception("VenueListPanel.DeleteVenue: \
                                           Could not change current venue")
                    else:
                        self.parent.venueProfilePanel.ChangeCurrentVenue()

    def AddVenue(self, venue):
        # Check to see if a venue with the same name is already added.
        # The string can either be venue's name or venue's name and a
        # default indicator.
        if(self.venuesList.FindString(venue.name) == wxNOT_FOUND):
            newUri = self.application.server.AddVenue(venue)
            venue.uri = newUri

            if newUri:
                exits = venue.connections
                self.venuesList.Append(venue.name, venue)
                self.venuesList.Select(self.venuesList.FindString(venue.name))
                self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

        else:
            text = "The venue could not be added, \na venue with the same name is already present"
            text2 = "Add Venue Error"
            log.info("VenueListPanel.AddVenue: Can not add venue because another venue with the same name is already present.")
            message = wxMessageDialog(self, text, text2,
                                      style = wxOK|wxICON_INFORMATION)
            message.ShowModal()
            message.Destroy()

    def SetDefaultVenue(self, venue, init = false):
        '''
        Sets default venue.

        ** Arguments **
         *venue* Venue to set as default
        '''
       
        #
        # Set default venue if it has changed.  If init is set, the method is
        # called during initialization of the application and default venue
        # is already set in the server.
        #
        
        if not init:
            # If the venue list is empty
            if self.defaultVenue and venue.uri != self.defaultVenue.uri:
                # Remove default text from old default venue
                if self.defaultVenue:
                    id = self.venuesList.FindString(self.defaultVenue.name +self.DEFAULT_STRING)
                    self.venuesList.SetString(id, self.defaultVenue.name)

            # Set default venue for this server
            self.application.server.SetDefaultVenue(venue.uri)

        # Set the default venue
        self.defaultVenue = venue
        
        # Reflect the default venue setting in the UI
        id = self.venuesList.FindString(venue.name)
        if id != wxNOT_FOUND:
            self.venuesList.SetString(id, venue.name+self.DEFAULT_STRING)
                       
    def ModifyVenue(self, venue):
        item = self.venuesList.GetSelection()
        index = self.venuesList.FindString(venue.name)
      
        if(index != wxNOT_FOUND and index != item):
            text = "The venue could not be modified, a venue with the same name is already present"
            text2 = "Add venue error"
            message = wxMessageDialog(self, text, text2,
                                      style = wxOK|wxICON_INFORMATION)
            message.ShowModal()
            message.Destroy()
                
        else:
            if venue.uri != None:
                self.application.server.ModifyVenue(venue.uri, venue)
                self.venuesList.SetClientData(item, venue)
                self.venuesList.SetString(item, venue.name)
                self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

                # Set default venue
                             
                if self.defaultVenue == None or venue.uri == self.defaultVenue.uri:
                    self.SetDefaultVenue(venue)
     
    def SetEncryption(self, value, key):
        item = self.venuesList.GetSelection()
        venue =  self.venuesList.GetClientData(item)
        log.debug("VenueListPanel.SetEncryption: Set encryption value:%s key:%s"%(value,key))
        self.application.SetVenueEncryption(venue, value, key)

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
        
        self.detailPanel = DetailPanel(self, application)
        self.__doLayout()

    def __doLayout(self):
        configurationPanelSizer = wxBoxSizer(wxHORIZONTAL)
        configurationPanelSizer.Add(self.detailPanel, 2, wxEXPAND|wxALL, 10)
        
        self.SetSizer(configurationPanelSizer)
        configurationPanelSizer.Fit(self)
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
        self.multicastBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.encryptionBox = wxStaticBox(self, -1, "Encryption",
                                         size = wxSize(500, 50),
                                         name = 'encryptionBox')
        self.encryptionBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        
        self.randomButton = wxRadioButton(self, self.ID_RANDOM,
                                          "Standard Range")
        self.intervalButton = wxRadioButton(self, self.ID_INTERVAL,
                                            "Custom Range: ")
        self.ipAddress = wxStaticText(self, -1, "224.2.128.0/17")
        self.changeButton = wxButton(self, self.ID_CHANGE, "Change")
        self.encryptionButton = wxCheckBox(self, self.ID_ENCRYPT,
                                           " Encrypt media ")
        self.ipString = "224.2.128.0"
        self.maskString = "17"
        self.__doLayout()
        self.__setEvents()
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)

    def __setEvents(self):
        EVT_BUTTON(self, self.ID_CHANGE, self.OpenIntervalDialog)
        EVT_RADIOBUTTON(self, self.ID_RANDOM, self.ClickedOnRandom)
        EVT_RADIOBUTTON(self, self.ID_INTERVAL, self.ClickedOnInterval)
        EVT_CHECKBOX(self, self.ID_ENCRYPT, self.ClickedOnEncrypt)
                       
    def ClickedOnEncrypt(self, event):
        try:
            log.debug("DetailPanel.ClickedOnEncrypt: Set encryption")
            self.application.SetEncryption(event.Checked())
        except Exception, e:
             if e.string == "NotAuthorized":
                 self.encryptionButton.SetValue(not event.Checked())
                 text = "You are not an administrator on this server and are not authorized to change the media encryption flag.\n"
                 MessageDialog(None, text, "Authorization Error", wxOK|wxICON_WARNING)
                 log.info("DetailPanel.ClickedOnEncrypt: Not authorized to change server's media encryption flag.")
             else:
                 self.encryptionButton.SetValue(not event.Checked())
                 log.exception("DetailPanel.ClickedOnEncrypt: Set encryption failed")
                 text = "The encryption option could not be set"
                 ErrorDialog(None, text, "Set Encryption Error", logFile = VENUE_MANAGEMENT_LOG)
        except:
            self.encryptionButton.SetValue(not event.Checked())
            log.exception("DetailPanel.ClickedOnEncrypt: Set encryption failed")
            text = "The encryption option could not be set"
            ErrorDialog(None, text, "Set Encryption Error",
                        logFile = VENUE_MANAGEMENT_LOG)
          
    def ClickedOnRandom(self, event):
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)
        try:
            log.debug("DetailPanel.ClickedOnRandom: Set multicast address to random")
            self.application.SetRandom()
        except Exception, e:
            self.ipAddress.Enable(true)
            self.changeButton.Enable(true)
            self.intervalButton.SetValue(true)
            if "string" in dir(e) and e.string == "NotAuthorized":
                text = "You are not an administrator on this server and are not authorized to set multicast addressing to random.\n"
                MessageDialog(None, text, "Authorization Error", wxOK|wxICON_WARNING)
                log.info("DetailPanel.ClickedOnRandom: Not authorized to set server multicast addressing to random.")
            else:
                log.exception("DetailPanel.ClickedOnEncrypt: Set multicast address to random failed")
                text = "The multicast option could not be set."
                ErrorDialog(None, text, "Set Multicast Error", logFile = VENUE_MANAGEMENT_LOG)

        except:
            self.ipAddress.Enable(true)
            self.changeButton.Enable(true)
            self.intervalButton.SetValue(true)
            log.exception("DetailPanel.ClickedOnEncrypt: Set multicast address to random failed")
            text = "The multicast option could not be set."
            ErrorDialog(None, text, "Set Multicast Error",
                        logFile = VENUE_MANAGEMENT_LOG)
         
    def ClickedOnInterval(self, event):
        self.ipAddress.Enable(true)
        self.changeButton.Enable(true)
        maskInt = int(self.maskString)

        try:
            log.debug("DetailPanel.ClickedOnInterval: Set multicast address to interval")
            self.application.SetInterval(self.ipString, maskInt)

        except Exception, e:
            self.ipAddress.Enable(false)
            self.changeButton.Enable(false)
            self.randomButton.SetValue(true)
            if e.string == "NotAuthorized":
                text = "You are not an administrator on this server and are not authorized to set multicast addressing to interval.\n"
                MessageDialog(None, text, "Authorization Error", wxOK|wxICON_WARNING)
                log.info("DetailPanel.ClickedOnInterval: Not authorized to set server's multicast address to interval.")
            else:
                log.exception("DetailPanel.ClickedOnInterval: Set multicast address to interval failed")
                text = "The multicast option could not be set."
                ErrorDialog(None, text, "Set Multicast Error", logFile = VENUE_MANAGEMENT_LOG)

        except:
            self.ipAddress.Enable(false)
            self.changeButton.Enable(false)
            self.randomButton.SetValue(true)
            log.exception("DetailPanel.ClickedOnInterval: Set multicast address to interval failed")
            text = "The multicast option could not be set."
            ErrorDialog(None, text, "Set Multicast Error",
                        logFile = VENUE_MANAGEMENT_LOG)
        
    def SetAddress(self, ipAddress, mask):
        oldIpAddress = self.ipAddress.GetLabel()

        try:
            log.debug("DetailPanel.SetAddress: Set ip address and mask")
            self.ipAddress.SetLabel(ipAddress+'/'+mask)
            self.ipString = ipAddress
            self.maskString = mask
            maskInt = int(mask)
            self.application.SetInterval(self.ipString, maskInt)

        except Exception, e:
            self.ipAddress.SetLabel(oldIpAddress)
            if e.string == "NotAuthorized":
                text = "You are not an administrator on this server and are not authorized to set the multicast address.\n"
                MessageDialog(None, text, "Authorization Error", wxOK|wxICON_WARNING)
                log.info("DetailPanel.SetAddress: Not authorized to set server's multicast address.")
            else:
                log.exception("DetailPanel.SetAddress: Set ip and mask failed")
                text = "The multicast option could not be set."
                ErrorDialog(None, text, "Set Multicast Error", logFile = VENUE_MANAGEMENT_LOG)

        except:
            self.ipAddress.SetLabel(oldIpAddress)
            log.exception("DetailPanel.SetAddress: Set ip and mask failed")
            text = "The multicast option could not be set."
            ErrorDialog(None, text, "Set Multicast Error",
                        logFile = VENUE_MANAGEMENT_LOG)
         
    def OpenIntervalDialog(self, event):
        MulticastDialog(self, -1, "Multicast Address - Custom Range")

    def __doLayout(self):
        serviceSizer = wxBoxSizer(wxVERTICAL)
        multicastBoxSizer = wxStaticBoxSizer(self.multicastBox, wxVERTICAL)
        

        multicastBoxSizer.Add(self.randomButton, 0, wxALL, 5)
        flexSizer = wxBoxSizer(wxHORIZONTAL)
        flexSizer.Add(self.intervalButton, 0, wxCENTER|wxRIGHT, 5)
        flexSizer.Add(self.ipAddress, 1, wxCENTER)
        flexSizer.Add(self.changeButton, 0, wxCENTER)
        multicastBoxSizer.Add(flexSizer, 0, wxEXPAND | wxALL, 5)
        
        serviceSizer.Add(multicastBoxSizer, 0,  wxBOTTOM|wxEXPAND, 10)
        serviceSizer.Add(wxSize(5,5))

        encryptionBoxSizer = wxStaticBoxSizer(self.encryptionBox, wxVERTICAL)
        encryptionBoxSizer.Add(self.encryptionButton, 5, wxALL, 10)

        serviceSizer.Add(encryptionBoxSizer, 0, wxEXPAND| wxBOTTOM, 10)
        self.SetSizer(serviceSizer)
        serviceSizer.Fit(self)
        self.SetAutoLayout(1)


# --------------------- TAB 3 -----------------------------------

class SecurityPanel(wxPanel):
    ID_SECURITY = wxNewId()
     
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, 
                         wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
        self.securityBox = wxStaticBox(self, -1, "Security",
                                       size = wxSize(500, 50),
                                       name = 'securityBox')
        self.securityBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        
        self.securityText = wxStaticText(self, -1, "Manage access to venue server including which users are \nallowed to administrate.")
        self.securityButton = wxButton(self, self.ID_SECURITY, "Manage Security")
        self.__doLayout()
        EVT_BUTTON(self, self.ID_SECURITY, self.OpenSecurityDialog)

    def OpenSecurityDialog(self, event):
        f = AuthorizationUIDialog(self, -1, "Security", log)
        wxBeginBusyCursor()
        f.ConnectToAuthManager(self.application.serverUrl)
        wxEndBusyCursor()
        
        if f.ShowModal() == wxID_OK:
            wxBeginBusyCursor()
            f.Apply()
            wxEndBusyCursor()
        f.Destroy()

    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        securityBoxSizer = wxStaticBoxSizer(self.securityBox, wxHORIZONTAL)
        securityBoxSizer.Add(self.securityText, 1 , wxEXPAND|wxALL|wxCENTER, 5)
        securityBoxSizer.Add(wxSize(1,40))
        securityBoxSizer.Add(self.securityButton, 0, wxALIGN_RIGHT|wxALL|wxCENTER, 5)
        sizer.Add(securityBoxSizer, 0, wxEXPAND| wxALL, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
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
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)

        sizer.Add(theSizer, 0, wxALL, 10)
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class VenueParamFrame(wxDialog):
       
    def __init__(self, parent, id, title, application):
        wxDialog.__init__(self, parent, id, title,
                          style = wxRESIZE_BORDER | wxDEFAULT_DIALOG_STYLE)
        self.Centre()
        self.noteBook = wxNotebook(self, -1)

        self.venue = None
        self.exitsList = []
        self.streams = []
        self.encryptionType = (0, None)
        
        self.SetSize(wxSize(400, 350))
        self.application = application
   
        self.generalPanel = GeneralPanel(self.noteBook, -1, application)
        self.staticAddressingPanel = StaticAddressingPanel(self.noteBook, -1)
        self.encryptionPanel = EncryptionPanel(self.noteBook, -1, application)
        self.authorizationPanel = AuthorizationUIPanel(self.noteBook, -1, log)
        
        self.noteBook.AddPage(self.generalPanel, "General")
        self.noteBook.AddPage(self.encryptionPanel, "Encryption")
        self.noteBook.AddPage(self.staticAddressingPanel, "Addressing")
      
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")
             
	self.__doLayout() 

    def __doLayout(self):
        boxSizer = wxBoxSizer(wxVERTICAL)
        boxSizer.Add(self.noteBook, 1, wxEXPAND)

        buttonSizer =  wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(wxSize(20, 20), 1)
        buttonSizer.Add(self.okButton, 0)
        buttonSizer.Add(wxSize(10, 10))
        buttonSizer.Add(self.cancelButton, 0)
        buttonSizer.Add(wxSize(20, 20), 1)

        boxSizer.Add(buttonSizer, 0, wxEXPAND | wxBOTTOM | wxTOP, 5)

        self.SetSizer(boxSizer)
        boxSizer.Fit(self)
        self.SetAutoLayout(1)
                    
    def SetEncryption(self):
        toggled = self.encryptionPanel.encryptMediaButton.GetValue()
        key = ''
        if toggled:
            key = self.encryptionPanel.keyCtrl.GetValue()

        self.parent.SetEncryption(toggled, key)

    def Ok(self):
        exitsList = []
        streams = []
        encryptTuple = (0, '')
        
        # Get Exits
        for index in range(0, self.generalPanel.exits.GetCount()):
            exit = self.generalPanel.exits.GetClientData(index)
            exitsList.append(exit)

        # Get Static Streams
        sap = self.staticAddressingPanel
        if(sap.staticAddressingButton.GetValue()==1):

            # Get the venue name to use as the stream name
            venueName = self.generalPanel.title.GetValue()

            # Static Video
            svml = MulticastNetworkLocation(sap.GetVideoAddress(),
                                            int(sap.GetVideoPort()),
                                            int(sap.GetVideoTtl()))
            staticVideoCap = Capability(Capability.PRODUCER, Capability.VIDEO)
            streams.append(StreamDescription(venueName,
                                                  svml, staticVideoCap,
                                                  0, None, 1))
            # Static Audio
            saml = MulticastNetworkLocation(sap.GetAudioAddress(),
                                            int(sap.GetAudioPort()),
                                            int(sap.GetAudioTtl()))
            staticAudioCap = Capability(Capability.PRODUCER, Capability.AUDIO)
            streams.append(StreamDescription(venueName,
                                                  saml, staticAudioCap,
                                                  0, None, 1))

        # Get Encryption
        if self.encryptionPanel.encryptMediaButton.GetValue():
            encryptTuple = (1, self.encryptionPanel.keyCtrl.GetValue())

        # Make a venue description
        venue = VenueDescription(self.generalPanel.title.GetValue(),
                                 self.generalPanel.description.GetValue(),
                                 encryptTuple, exitsList, streams)
        self.venue = venue

    def Validate(self):
        return true
    
class GeneralPanel(wxPanel):
    ID_TRANSFER = wxNewId()
    ID_REMOVE_EXIT = wxNewId()
    ID_LOAD = wxNewId()
    ID_DEFAULT = wxNewId()
    ID_EXIT_RENAME = wxNewId()
    
    def __init__(self, parent, id, app):
        wxPanel.__init__(self, parent, id)
        self.application = app
        self.parent = parent
        self.informationBox = wxStaticBox(self, -1, "Information")
        self.informationBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.exitsBox = wxStaticBox(self, -1, "Exits")
        self.exitsBox.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.titleLabel =  wxStaticText(self, -1, "Title:")
        self.title =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20),
        validator = TextValidator())
        self.descriptionLabel = wxStaticText(self, -1, "Description:")
        self.description =  wxTextCtrl(self, -1, "", size = wxSize(200, 50),
                                       style = wxTE_MULTILINE |
                                       wxTE_RICH2, validator = TextValidator())
        self.defaultVenue = wxCheckBox(self, self.ID_DEFAULT, "Set this venue as default.")
        
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

        # Menu for exits:
        self.exitsMenu = wxMenu()
        self.exitsMenu.Append(self.ID_EXIT_RENAME,"Change Title...",
                             "Give this exit a new title.")
        EVT_MENU(self, self.ID_EXIT_RENAME, self.UpdateExit)
        EVT_RIGHT_DOWN(self.exits, self.OnRightClick)
        
        self.__doLayout()
        self.__setEvents()

    def LoadRemoteVenues(self, event = None):
        URL = self.address.GetValue()
        self.__loadVenues(URL)
        if self.address.FindString(URL) == wxNOT_FOUND:
            log.debug("VenueParamFrame.LoadRemoteVenues: Append address to combobox: %s " % URL)
            self.address.Append(URL)

    def LoadLocalVenues(self):
        self.__loadVenues(self.application.serverUrl)

    def __loadVenues(self, URL):
        self.currentVenueUrl = self.address.GetValue() # used in except:
        try:
            wxBeginBusyCursor()
            log.debug("VenueParamFrame.__LoadVenues: Load venues from: %s " % URL)
            server = VenueServerIW(URL)
            
            venueList = []
            vl = server.GetVenues()
            
            # Remove the current venue from the list of potential exits
            if self.application.currentVenue:
                vl = filter(lambda v,url=self.application.currentVenue.uri: v.uri != url, vl)
            
            self.venues.Clear()
            cdl = map(lambda x: ConnectionDescription(x.name,
                                                      x.description,
                                                      x.uri), vl)
            map(lambda x: self.venues.Append(x.name, x), cdl)
            
            self.currentVenueUrl = URL
            self.address.SetValue(URL)
            
            wxEndBusyCursor()
    
        except:
            wxEndBusyCursor()
            self.address.SetValue(self.currentVenueUrl)
            log.exception("VenueParamFrame.__LoadVenues: Could not load exits from server at %s" %URL)
            MessageDialog(None, "Could not load exits from server at " + str(URL), "Load Exits Error", wxOK|wxICON_INFORMATION)
    
    def OnRightClick(self, event):
        index = self.exits.GetSelection()
        if index == -1:
            return
        self.x = event.GetX() + self.exits.GetPosition().x
        self.y = event.GetY() + self.exits.GetPosition().y
        
        self.PopupMenu(self.exitsMenu, wxPoint(self.x, self.y))
       
                
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
              

    def UpdateExit(self, event):
        index = self.exits.GetSelection()
        oldName = self.exits.GetString(index)
        name = None
        
        dlg = RenameExitDialog(self, -1, "Change Venue Title", oldName)
        if (dlg.ShowModal() == wxID_OK ):
            name = dlg.GetName()
        else:
            return
        
        if index != -1:
            self.exits.SetString(index, name)
            connDesc = self.exits.GetClientData(index)
            connDesc.SetName(name)
            
    def RemoveExit(self, event):
        index = self.exits.GetSelection()
        if index != -1:
            self.exits.Delete(index)
    
    def __setEvents(self):
        EVT_BUTTON(self, self.ID_TRANSFER, self.AddExit)
        EVT_BUTTON(self, self.ID_REMOVE_EXIT, self.RemoveExit)
        EVT_BUTTON(self, self.ID_LOAD, self.LoadRemoteVenues)

    def __doLayout(self):
        boxSizer = wxBoxSizer(wxVERTICAL)
        topSizer =  wxBoxSizer(wxHORIZONTAL)

        paramFrameSizer = wxFlexGridSizer(10, 2, 5, 5)
        paramFrameSizer.Add(self.titleLabel, 0, wxALIGN_RIGHT)
        paramFrameSizer.Add(self.title, 0, wxEXPAND)
        paramFrameSizer.AddGrowableCol(1)

        topParamSizer = wxStaticBoxSizer(self.informationBox, wxVERTICAL)
        topParamSizer.Add(paramFrameSizer, 0, wxEXPAND | wxALL, 10)
        topParamSizer.Add(self.descriptionLabel, 0, wxALIGN_LEFT |wxLEFT, 10)
        topParamSizer.Add(self.description, 1,
                          wxEXPAND |wxLEFT | wxRIGHT| wxBOTTOM, 10)
        topParamSizer.Add(self.defaultVenue, 0,
                          wxEXPAND |wxLEFT | wxRIGHT| wxBOTTOM, 10)

        topSizer.Add(topParamSizer, 1, wxRIGHT | wxEXPAND, 5)

        boxSizer.Add(topSizer, 0, wxALL | wxEXPAND, 10)

        bottomParamSizer = wxStaticBoxSizer(self.exitsBox, wxVERTICAL)
        exitsSizer = wxFlexGridSizer(10, 3, 5, 5)
        exitsSizer.Add(self.venuesLabel, 0)
        exitsSizer.Add(wxSize(10,10), wxEXPAND)
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

        exitsSizer.Add(wxSize(10,10))
        exitsSizer.Add(self.removeExitButton, 0, wxEXPAND)
        exitsSizer.AddGrowableCol(0)
        exitsSizer.AddGrowableCol(2)

        bottomParamSizer.Add(exitsSizer, 0, wxEXPAND | wxALL, 10)
        boxSizer.Add(bottomParamSizer, 0,
                     wxEXPAND | wxLEFT | wxBOTTOM | wxRIGHT, 10)

        self.SetSizer(boxSizer)
        boxSizer.Fit(self)
        self.SetAutoLayout(1)

    def Validate(self):
        return 1
    
class EncryptionPanel(wxPanel):
    ID_BUTTON = wxNewId()
    ID_GENKEYBUTTON = wxNewId()
    
    def __init__(self, parent, id, application):
        wxPanel.__init__(self, parent, id)
        self.application = application
        self.encryptMediaButton = wxCheckBox(self, self.ID_BUTTON,
                                             " Encrypt media ")
        self.keyText = wxStaticText(self, -1, "Optional key: ",
                                    size = wxSize(100,20))
        self.keyCtrl = wxTextCtrl(self, -1, "", size = wxSize(200,20))
        self.genKeyButton = wxButton(self, self.ID_GENKEYBUTTON,
                                     "Generate New Key", size= wxSize(100, 20))
        self.keyText.Enable(false)
        self.keyCtrl.Enable(false)
        self.genKeyButton.Enable(false)
        self.__doLayout()
        self.__setEvents()

    def ClickEncryptionButton(self, event = None, value = None):
        if event == None:
            id = value
            self.encryptMediaButton.SetValue(value)
        else:
            id =  event.Checked()
        message = "Set encrypt media, value is: "+str(id)
        self.keyText.Enable(id)
        self.keyCtrl.Enable(id)
        self.genKeyButton.Enable(id)

    def ClickGenKeyButton(self, event = None, value = None):
        self.keyCtrl.Clear()
        newKey = self.application.currentVenueClient.RegenerateEncryptionKeys()
        self.keyCtrl.SetValue(newKey)

    def __setEvents(self):
        EVT_CHECKBOX(self, self.ID_BUTTON, self.ClickEncryptionButton)
        EVT_BUTTON(self, self.ID_GENKEYBUTTON, self.ClickGenKeyButton)
        
    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(wxSize(10,10))
        sizer.Add(self.encryptMediaButton, 0, wxEXPAND|wxALL, 5)
        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(wxSize(25, 10))
        sizer2.Add(self.keyText , 0, wxEXPAND|wxALL, 5)
        sizer2.Add(self.keyCtrl, 1, wxEXPAND|wxALL, 5)
        sizer.Add(sizer2, 0, wxEXPAND | wxRIGHT, 10)
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.genKeyButton, 1, wxALL, 5)
        sizer.Add(sizer3, 1, wxRIGHT, 10)

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
        self.videoTitleText.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.audioTitleText = wxStaticText(self.panel, -1, "Audio (16kHz)",
                                           size = wxSize(100,20))
        self.audioTitleText.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.videoAddressText = wxStaticText(self.panel, -1, "Address: ",
                                             size = wxSize(60,20), style = wxALIGN_RIGHT)
        self.audioAddressText = wxStaticText(self.panel, -1, "Address: ",
                                             size = wxSize(60,20), style = wxALIGN_RIGHT)
        self.videoPortText = wxStaticText(self.panel, -1, " Port: ",
                                          size = wxSize(45,20), style = wxALIGN_RIGHT)
        self.audioPortText = wxStaticText(self.panel, -1, " Port: ",
                                          size = wxSize(45,20), style = wxALIGN_RIGHT)
        self.videoTtlText = wxStaticText(self.panel, -1, " TTL:",
                                         size = wxSize(40,20), style = wxALIGN_RIGHT)
        self.audioTtlText = wxStaticText(self.panel, -1, " TTL:",
                                         size = wxSize(40,20), style = wxALIGN_RIGHT)
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
        staticAddressingSizer = wxBoxSizer(wxVERTICAL)
        staticAddressingSizer.Add(wxSize(10,10))
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
        flexSizer.Add(wxSize(10,10))
        flexSizer.Add(self.videoAddressText, 0 , wxEXPAND)
        flexSizer.Add(videoIpSizer, 0 , wxEXPAND)
        flexSizer.Add(self.videoPortText)
        flexSizer.Add(self.videoPort, 0 , wxEXPAND)
        flexSizer.Add(self.videoTtlText,0 , wxEXPAND)
        flexSizer.Add(self.videoTtl,0 , wxEXPAND)

        panelSizer.Add(flexSizer, 0 , wxEXPAND|wxALL, 5)

        audioTitleSizer = wxBoxSizer(wxHORIZONTAL)
        audioTitleSizer.Add(self.audioTitleText, 0, wxALIGN_CENTER)
        audioTitleSizer.Add(wxStaticLine(self.panel, -1), 1, wxALIGN_CENTER)

        panelSizer.Add(wxSize(10,10))

        panelSizer.Add(audioTitleSizer, 1 , wxEXPAND|wxLEFT|wxRIGHT, 10)

        flexSizer2 = wxFlexGridSizer(7, 7, 0, 0)
        flexSizer2.Add(wxSize(10,10))
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
        VenueParamFrame.__init__(self, parent, id, title, application)
        self.parent = parent
        self.authorizationPanel.Hide()
        self.SetSize(wxSize(600, 470))
        self.SetLabel('Add Venue')
        self.application.SetCurrentVenue(None)
        self.generalPanel.LoadLocalVenues()
        self.encryptionPanel.genKeyButton.Hide()
        self.encryptionPanel.ClickEncryptionButton(None,
                                                   self.application.encrypt)
        EVT_BUTTON (self.okButton, wxID_OK, self.OnOK)
        self.ShowModal()

    def OnOK (self, event):
        wxBeginBusyCursor()

        if (VenueParamFrame.Validate(self) and 
            self.staticAddressingPanel.Validate() and 
            self.generalPanel.Validate()):
            self.Ok()
            try:
                log.debug("AddVenueFrame.OnOk: Add venue.")
                self.parent.AddVenue(self.venue)
            except Exception, e:
                if e.string == "NotAuthorized":
                    text = "You are not a server administrator and are not authorized to add venues to this server.\n"
                    MessageDialog(None, text, "Authorization Error", wxOK|wxICON_WARNING)
                    log.info("AddVenueFrame.OnOK: Not authorized to add venue to server.")
                else:
                    log.exception("AddVenueFrame.OnOk: Could not add venue")
                    text = "Could not add venue %s" %self.venue.name
                    ErrorDialog(None, text, "Add Venue Error",
                                logFile = VENUE_MANAGEMENT_LOG)
            except:
                log.exception("AddVenueFrame.OnOk: Could not add venue")
                text = "Could not add venue %s" %self.venue.name
                ErrorDialog(None, text, "Add Venue Error",
                            logFile = VENUE_MANAGEMENT_LOG)
                
            if self.generalPanel.defaultVenue.IsChecked():
                try:
                    # Set this venue as default venue for this server.
                    self.parent.SetDefaultVenue(self.venue)
                except:
                    log.exception("AddVenueFrame.OnOk: SetDefaultVenue failed")
                    
            self.Hide()
        wxEndBusyCursor()


class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, app)
        wxBeginBusyCursor()
        self.parent = parent
        self.SetSize(wxSize(600, 470))
        self.SetLabel('Modify Venue')
        
        self.__loadCurrentVenueInfo(venueList)
        self.generalPanel.LoadLocalVenues()

        # Connect to authorization manager.
        self.noteBook.AddPage(self.authorizationPanel, "Security")

        self.authorizationPanel.ConnectToAuthManager(self.venue.uri)
        
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
                    log.debug("ModifyVenueFrame.OnOk: Modify venue")
                    self.parent.ModifyVenue(self.venue)
                    self.authorizationPanel.Apply()
                    
                except Exception, e:
                    log.exception("ModifyVenueFrame.OnOk: Modify venue failed")
                    text = "Could not modify venue %s" %self.venue.name
                    if hasattr(e, "string"):
                        text = text + "\n%s" % e.string
                    ErrorDialog(None, text, "Modify Venue Error",
                                logFile = VENUE_MANAGEMENT_LOG)

                if self.generalPanel.defaultVenue.IsChecked():
                    try:
                        # Set this venue as default venue for this server.
                        self.parent.SetDefaultVenue(self.venue)
                    except:
                        # Modify venues should work even if SetVenueRoles fail
                        log.exception("ModifyVenueFrame.OnOk: SetDefaultVenue failed")

                # Send security info to authorization manager,
                self.authorizationPanel.Apply(event)
                                       
                self.Hide()

        wxEndBusyCursor()

    def __loadCurrentVenueInfo(self, venueList):
        item = venueList.GetSelection()
        self.venue = venueList.GetClientData(item)

        self.generalPanel.title.AppendText(self.venue.name)
        self.generalPanel.description.AppendText(self.venue.description)

        log.debug("ModifyVenueFrame.__loadCurrentVenueInfo: Get venue information")
        self.application.SetCurrentVenue(self.venue)
        venueC = self.application.currentVenueClient

        try:
            # Set this venue as default venue for this server.
            url = self.application.server.GetDefaultVenue()
            if self.venue.uri == url:
                self.generalPanel.defaultVenue.Enable(0)
            else:
                self.generalPanel.defaultVenue.Enable(1)
          
        except:
            log.exception("ModifyVenueFrame.__loadCurrentVenueInfo: SetDefaultVenue failed")

        if(self.venue.encryptMedia):
            log.debug("ModifyVenueFrame.__loadCurrentVenueInfo: We have a key %s" % self.venue.encryptionKey)
            self.encryptionPanel.ClickEncryptionButton(None, true)
            self.encryptionPanel.keyCtrl.SetValue(self.venue.encryptionKey)
        else:
            log.debug("ModifyVenueFrame.__loadCurrentVenueInfo: Key is None")
            self.encryptionPanel.ClickEncryptionButton(None, false)

        for e in self.venue.connections:
            self.generalPanel.exits.Append(e.name, e)
            
        if(len(self.venue.streams)==0):
            log.debug("ModifyVenueFrame.__loadCurrentVenueInfo: No static streams to load")
            self.staticAddressingPanel.panel.Enable(false)
            self.staticAddressingPanel.staticAddressingButton.SetValue(false)
        elif(len(self.venue.streams)>2):
            log.exception("ModifyVenueFrame.__loadCurrentVenueInfo: Venue returned more than 2 static streams")
          
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

class RenameExitDialog(wxDialog):
    def __init__(self, parent, id, title, oldName):
        wxDialog.__init__(self, parent, id, title)
        self.text = wxStaticText(self, -1, "Please, enter a new title for the venue.", style=wxALIGN_LEFT)
       
        self.line = wxStaticLine(self, -1)

        self.nameText = wxStaticText(self, -1, "Title:")
        self.nameBox =  wxTextCtrl(self, -1, oldName)
        self.nameBox.SetSize(wxSize(200, 20))

        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
    
    def GetName(self):
        return self.nameBox.GetValue()
        
    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 0, wxALL, 10)
        sizer.Add(wxSize(2,2))

        s2 =  wxBoxSizer(wxHORIZONTAL)
        s2.Add(self.nameText, 0, wxCENTER | wxRIGHT, 5)
        s2.Add(self.nameBox, 0,  wxCENTER | wxLEFT, 5)
        sizer.Add(s2, 0, wxEXPAND| wxALL, 10)
        sizer.Add(self.line, 0, wxALL | wxEXPAND, 10)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wxALL, 5)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER | wxBOTTOM, 5) 
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


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
                MessageDialog(None, "Please, use digits for the mask.", "Notification")
                return false
        if (self.flag == IP or self.flag == IP_1) and index == 0:
            MessageDialog(None,"Please, fill in all IP Address fields.", "Notification")
            return false

        elif (self.flag == PORT) and index == 0:
            MessageDialog(None,"Please, fill in port for static addressing.", "Notification")
            return false

        elif (self.flag == TTL) and index == 0:
            MessageDialog(None, "Please, fill in time to live (TTL) for static addressing.", "Notification")
            return false

        elif self.flag == PORT:
            return true

        elif self.flag == TTL and (int(val)<0 or int(val)>127):
            MessageDialog(None, "Time to live (TTL) should be a value between 0 - 127.", "Notification")
            return false

        elif self.flag == IP and (int(val)<0 or int(val)>255):
            MessageDialog(None, "Allowed values for IP Address are between 224.0.0.0 - 239.255.255.255", "Notification")
            return false

        elif self.flag == IP_1 and (int(val)<224 or int(val)>239):
            MessageDialog(None, "Allowed values for IP Address are between 224.0.0.0 - 239.255.255.255", "Notification")
            return false

        elif index == 0 and self.flag == MASK:
            MessageDialog(None, "Please, fill in mask.", "Notification")
            return false

        elif self.flag == MASK and (int(val)>31 or int(val)<0):
            MessageDialog(None, "Allowed values for mask are between 0 - 31.", "Notification")
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
            tc = self.GetWindow()
            val = tc.GetValue()
           
            if not val:
                event.Skip()
                return

            # Set maximum number of digits to 3 for
            # ip, ttl, and mask values. No limit for port.
            elif  self.flag == PORT or len(val) < 3:
                event.Skip()
                return

            else:
                # Do not ring the bell if user tries to
                # overwrite a selected string.
                if len(tc.GetStringSelection()) != 0:
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
            MessageDialog(None, "Please, fill in your name and description", "Notification")
            return false
        else:
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
    debugMode = Toolkit.Application.instance().GetOption("debug")
    app.SetLogger(debugMode)
    app.MainLoop()

    """class Application:
        def __init__(self):
            self.serverUrl = ''
        
        def OpenHelpURL(self, url):
            print 'open help'
            
        def ConnectToServer(self, URL):
            print 'connect to server'
            
        def GetCName(self, distinguishedName):
            print 'get c name'
    
        def SetCurrentVenue(self, venue = None):
            print 'set current'

        def DeleteVenue(self, venue):
            print 'delete venue'

        def DeleteAdministrator(self, dnName):
            print 'delete admin'

        def ModifyAdministrator(self, oldName, dnName):
            print 'modify admin'
        
        def SetRandom(self):
            print 'set random'

        def SetInterval(self, address, mask):
            print 'set interval'

        def SetEncryption(self, value):
            print 'set encryption'
    """

    #pp = wxPySimpleApp()
    #addVenueDialog = AddVenueFrame(None, -1, "", [], Application())
    #addVenueDialog.Destroy()
