#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        VenueManagement.py
# Purpose:     This is the user interface for Virtual Venues Server Management
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueManagement.py,v 1.176 2007-09-18 20:45:25 turam Exp $
# Copyright:   (c) 2002-2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueManagement.py,v 1.176 2007-09-18 20:45:25 turam Exp $"

# Standard imports
import sys
import os

import string
import time
import re
import webbrowser
import cPickle
from optparse import Option

# UI imports
import wx

# Access Grid imports
from AccessGrid.Descriptions import StreamDescription, ConnectionDescription
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.Descriptions import Capability
from AccessGrid.Security.CertificateManager import CertificateManager
from AccessGrid.NetworkLocation import MulticastNetworkLocation
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid import icons
from AccessGrid.UIUtilities import AboutDialog, MessageDialog, ErrorDialog, SetIcon
from AccessGrid.Utilities import VENUE_MANAGEMENT_LOG
from AccessGrid.Security.wxgui.AuthorizationUI import AuthorizationUIPanel, AuthorizationUIDialog
from AccessGrid.interfaces.AuthorizationManager_client import AuthorizationManagerIW
from AccessGrid import Log
from AccessGrid.hosting import Client
from AccessGrid.interfaces.VenueServer_client import VenueServerIW
from AccessGrid.Venue import VenueIW
from AccessGrid import Toolkit
from AccessGrid.Toolkit import MissingDependencyError
from AccessGrid.Platform.Config import UserConfig, AGTkConfig
from AccessGrid.Platform import IsWindows, IsOSX
from AccessGrid.GUID import GUID

from AccessGrid.UIUtilities import AddURLBaseDialog, EditURLBaseDialog

# Force ZSI to use the M2Crypto HTTPSConnection as transport
from ZSI import client
from M2Crypto import httpslib
client.Binding.defaultHttpsTransport = httpslib.HTTPSConnection

log = Log.GetLogger(Log.VenueManagement)

class VenueManagementClient(wx.App):
    """
    VenueManagementClient.

    The VenueManagementClient class creates the main frame of the
    application as well as the VenueManagementTabs and statusbar.
    """
    ID_FILE_EXIT = wx.NewId()
    ID_SERVER_CHECKPOINT = wx.NewId()
    ID_SERVER_SHUTDOWN = wx.NewId()
    ID_HELP_ABOUT = wx.NewId()
    ID_HELP_MANUAL =  wx.NewId()

    ID_MYSERVERS_GOTODEFAULT = wx.NewId()
    ID_MYSERVERS_SETDEFAULT = wx.NewId()
    ID_MYSERVERS_ADD = wx.NewId()
    ID_MYSERVERS_EDIT = wx.NewId()
        
    def OnInit(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        self.agtkConf = AGTkConfig.instance()
      
        self.manual_url = "http://www.mcs.anl.gov/fl/research/accessgrid/documentation/manuals/VenueManagement/3_0"
        self.server = None
        self.serverUrl = None
        self.currentVenueClient = None
        self.currentVenue = None
        self.encrypt = false
        self.venueList = []
        self.help_open = 0
          
        self.frame = wx.Frame(NULL, -1, "Venue Management" )
        self.address = VenueServerAddress(self.frame, self)
        self.tabs = VenueManagementTabs(self.frame, -1, self)
        self.statusbar = self.frame.CreateStatusBar(1)
        
        self.menubar = wx.MenuBar()
        self.myServersDict = {}
        self.myServersMenuIds = {}
        self.userConf = UserConfig.instance()
        self.myServersFile = os.path.join(self.userConf.GetConfigDir(), "myServers.txt" )
        
        self.__doLayout()
        self.__setMenuBar()
        self.__setEvents()
        self.__loadMyServers()
        self.EnableMenu(0)

        self.app = Toolkit.WXGUIApplication()
        
        urlOption = Option("--url", type="string", dest="url",
                           default="", metavar="URL",
                           help="URL of venue to enter on startup.")
        self.app.AddCmdLineOption(urlOption)

        try:
            self.app.Initialize("VenueManagement")
        except MissingDependencyError, e:
            if e.args[0] == 'SSL':
                msg = "The installed version of Python has no SSL support.  Check that you\n"\
                      "have installed Python from python.org, or ensure SSL support by\n"\
                      "some other means."
            else:
                msg = "The following dependency software is required, but not available:\n\t%s\n"\
                        "Please satisfy this dependency and restart the software"
                msg = msg % e.args[0]
            MessageDialog(None,msg, "Initialization Error",
                          style=wx.ICON_ERROR )
            sys.exit(-1)
        except Exception, e:
            print "Toolkit Initialization failed, exiting."
            print " Initialization Error: ", e
            MessageDialog(None,
                          "The following error occurred during initialization:\n\n\t%s %s" % (e.__class__.__name__,e), 
                          "Initialization Error",
                          style=wx.ICON_ERROR )
            sys.exit(-1)
            
            
        self.__setProperties()
        
        self.certmgr = self.app.GetCertificateManager()
        venueServerUrl = self.app.GetOption('url')
        if venueServerUrl:
            self.ConnectToServer(venueServerUrl)
            
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
        EVT_MENU(self, self.ID_MYSERVERS_ADD, self.AddToMyServersCB)
        EVT_MENU(self, self.ID_MYSERVERS_EDIT, self.EditMyServersCB)

        EVT_CLOSE(self, self.OnCloseWindow)
        
    def __setMenuBar(self):
        self.frame.SetMenuBar(self.menubar)

        self.fileMenu = wx.Menu()
        self.fileMenu.Append(self.ID_FILE_EXIT,"&Exit", "Quit Venue Management")
        self.menubar.Append(self.fileMenu, "&File")

        self.serverMenu = wx.Menu()
        self.serverMenu.Append(self.ID_SERVER_CHECKPOINT, "&Checkpoint",
                               "Checkpoint the server")
        
        self.serverMenu.Append(self.ID_SERVER_SHUTDOWN, "&Shutdown",
                               "Shutdown the server")

        self.menubar.Append(self.serverMenu, "&Server")
        self.myServersMenu = wx.Menu()
        self.myServersMenu.Append(self.ID_MYSERVERS_ADD, "Add Server...",
                             "Add this server to your list of servers")
        self.myServersMenu.Append(self.ID_MYSERVERS_EDIT, "Edit My &Servers...",
                             "Edit your servers")
        self.myServersMenu.AppendSeparator()

        self.menubar.Append(self.myServersMenu, '&My Servers')
        
        
        self.helpMenu = wx.Menu()
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
        SetIcon(self.frame)
        self.frame.SetSize(wx.Size(600, 350))
        self.SetTopWindow(self.frame)
        self.frame.Show()

    def __doLayout(self):
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.address, 0, wx.EXPAND|wx.ALL)
        box.Add(self.tabs, 1, wx.EXPAND)
        self.frame.SetSizer(box)
        self.frame.Layout()

    def __fixName(self, name):
        if len(name)>0:
            parts = name.split('/')
            return parts[2]
        else:
            return name

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
            ID = wx.NewId()
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
        #self.myServersMenu.Enable(self.ID_MYSERVERS_ADD, flag)
        self.serverMenu.Enable(self.ID_SERVER_CHECKPOINT , flag)
        self.serverMenu.Enable(self.ID_SERVER_SHUTDOWN, flag)
                
    def AddToMyServersCB(self, event):
        url =  self.serverUrl
        myServersDict = self.myServersDict
              
        if not url:
            url = ""
        
        #
        # Server url not in list
        # - Prompt for name and validate
        #
        serverName = None
        dialog = AddURLBaseDialog(self.frame, -1, self.__fixName(url), url, type = 'server')
        if (dialog.ShowModal() == wx.ID_OK):
            serverName = dialog.GetName()
            serverUrl = dialog.GetUrl()
        dialog.Destroy()
        
        if serverName:
            addServer = 1
            if myServersDict.has_key(serverName):
                #
                # Server name already in list
                #
                
                info = "A server with the same name is already added, do you want to overwrite it?"
                
                dlg = wx.MessageDialog(self.frame, info, "Duplicated Server",
                                      style = wx.ICON_INFORMATION | wx.OK | wx.CANCEL)
                
                if dlg.ShowModal() == wx.ID_OK:
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
                                  
            if addServer:
                try:
                    self.AddToMyServers(serverName, serverUrl)
                    self.__saveMyServersToFile()
                    
                except:
                    log.exception("Error adding server")
                    MessageDialog(self.frame,
                                  "Error adding server to server list",
                                  "Add Server Error",
                                  style=wx.OK|wx.ICON_WARNING)
        
    def EditMyServersCB(self, event):
        
        editMyServersDialog = EditURLBaseDialog(self.frame, -1, "Edit your servers", 
                                                self.myServersDict, type = 'server')
        if (editMyServersDialog.ShowModal() == wx.ID_OK):
            self.myServersDict = editMyServersDialog.GetValue()
            
            try:
                self.__saveMyServersToFile()
                self.__loadMyServers()
            
            except:
                log.exception(
                    "Error saving changes to my servers","Edit Servers Error")
                MessageDialog(self.frame, "Error saving changes to my servers",
                              "Add Server Error", style=wx.OK|wx.ICON_WARNING)

        editMyServersDialog.Destroy()

    def GoToMenuAddressCB(self, event):
        name = self.menubar.GetLabel(event.GetId())
        serverUrl = self.myServersDict[name]
        self.ConnectToServer(serverUrl)
            
    def AddToMyServers(self,name,url):
        ID = wx.NewId()
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
        del self.myServersDict[serverName]

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
        self.server.Checkpoint(0)
    
    def Shutdown(self, event):
        self.server.Shutdown(0)
    
    def OnCloseWindow(self, event):
        self.frame.Destroy()
     
    def ConnectToServer(self, URL):
        import types
        if type(URL) == types.UnicodeType:
            URL = URL.encode('ascii','ignore')

        log.debug("VenueManagementClient.ConnectToServer: Connect to server %s" %URL)
        
        #certMgt = Toolkit.Application.instance().GetCertificateManager()
        # if not certMgt.HaveValidProxy():
        #     log.debug("VenueManagementClient.ConnectToServer:: no valid proxy")
        #     certMgt.CreateProxy()
        try:
            wx.BeginBusyCursor()
            log.debug("VenueManagementClient.ConnectToServer: Connect to server")
            
            ctx = self.app.GetContext()
            transdict = {'ssl_context':ctx}
            self.server = VenueServerIW(URL,transdict=transdict)
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

            # add address to address list, if not already there
            if self.address.addressText.FindString(self.serverUrl) == wx.NOT_FOUND:
                log.debug("VenueManagementClient.ConnectToServer: Add address: %s" %self.serverUrl)
                self.address.addressText.Append(self.serverUrl)
                
            # set the address displayed
            self.address.addressText.SetValue(self.serverUrl)

            # fill in encryption
            key = int(self.server.GetEncryptAllMedia())
            log.debug("VenueManagementClient.ConnectToServer: Set server encryption key: %s" % key)
            dp.encryptionButton.SetValue(key)
            self.encrypt = key
           
            self.tabs.Enable(true)
            self.EnableMenu(1)
            
            wx.EndBusyCursor()
            
        except Exception, e:
            wx.EndBusyCursor()
            text = "You were unable to connect to the venue server at:\n%s." % URL
            lStr = "Can not connect."
            if hasattr(e, "string"):
                text += "\n%s" % e.faultstring
                lStr += "(%s)" % e.faultstring

            log.exception("VenueManagementClient.ConnectToServer: %s:", lStr)
            MessageDialog(None, text, "Unable To Connect",
                          style=wx.OK|wx.ICON_INFORMATION)
            
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
            ctx = self.app.GetContext()
            transdict = {'ssl_context':ctx}
            venue.uri = venue.uri.encode('ascii','ignore')
            self.currentVenueClient = VenueIW(venue.uri,transdict=transdict)

    def SetVenueEncryption(self, venue, value = 0, key = ''):
        self.SetCurrentVenue(venue)
        log.debug("VenueManagementClient.SetVenueEncryption: Set venue encryption: %s using key: %s for venue: %s" 
                     % (str(value), str(key), str(venue.uri)))
        self.currentVenueClient.SetEncryptMedia(int(value), str(key))

    def DeleteVenue(self, venue):
        log.debug("VenueManagementClient.DeleteVenue: Delete venue: %s" %str(venue.uri))
        self.server.RemoveVenue(venue.id)
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

class VenueServerAddress(wx.Panel):
    ID_BUTTON = wx.NewId()
    ID_ADDRESS = wx.NewId()

    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, \
                        wx.DefaultSize, wx.NO_BORDER)
        self.application = application
        self.addressLabel =  wx.StaticText(self, -1,'Venue Server Address:')
        self.defaultServer = 'https://localhost:8000/VenueServer'
        self.serverList = ['https://localhost:8000/VenueServer']
        self.addressText = wx.ComboBox(self, self.ID_ADDRESS,
                                      self.defaultServer,
                                      choices = self.serverList,
                                      style = wx.CB_DROPDOWN)

        self.goButton = wx.Button(self, self.ID_BUTTON, "Go",
                                 wx.DefaultPosition)
        self.line = wx.StaticLine(self, -1)
        self.__doLayout()
        self.__addEvents()

    def __addEvents(self):
        EVT_BUTTON(self, self.ID_BUTTON, self.CallAddress)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.CallAddress)

    def CallAddress(self, event):
        venueServerUrl = self.addressText.GetValue()

        defaultproto = 'https'
        defaultport = 8000

        # - define a mess of regular expressions for matching venue urls
        hostre = re.compile('^[\w.-]*$')
        hostportre = re.compile('^[\w.-]*:[\d]*$')
        protohostre = re.compile('^[\w]*://[\w.-]*$')
        protohostportre = re.compile('^[\w]*://[\w.-]*:[\d]*$')

        # - check for host only
        if hostre.match(venueServerUrl):
            host = venueServerUrl
            venueServerUrl = '%s://%s:%d/VenueServer' % (defaultproto,host,defaultport)
        # - check for host:port
        elif hostportre.match(venueServerUrl):
            hostport = venueServerUrl
            venueServerUrl = '%s://%s/VenueServer' % (defaultproto,hostport)
        elif protohostre.match(venueServerUrl):
            protohost = venueServerUrl
            venueServerUrl = '%s:%d/VenueServer' % (protohost,defaultport)
        elif protohostportre.match(venueServerUrl):
            protohostport = venueServerUrl
            venueServerUrl = '%s/VenueServer' % (protohostport)

        wx.BeginBusyCursor()
        self.application.ConnectToServer(venueServerUrl)
        wx.EndBusyCursor()
        
        #self.addressText.SetValue(venueServerUrl)


    def __doLayout(self):
        venueServerAddressBox = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.addressLabel, 0, wx.CENTER|wx.EXPAND|wx.RIGHT|wx.LEFT|wx.TOP, 5)
        box.Add(self.addressText, 1, wx.CENTER|wx.EXPAND|wx.RIGHT|wx.TOP, 5)
        box.Add(self.goButton, 0, wx.CENTER|wx.EXPAND|wx.RIGHT|wx.TOP, 5)
        venueServerAddressBox.Add(box, 1, wx.EXPAND)
        venueServerAddressBox.Add(self.line, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(venueServerAddressBox)
        venueServerAddressBox.Fit(self)
        self.SetAutoLayout(1)
        self.Layout()


class VenueManagementTabs(wx.Notebook):
    """
    VenueManagementTabs

    VenueManagementTabs is a notebook that initializes 3 pages,
    containing the VenuesPanel, ConfigurationPanel, and ServicesPanel.
    """

    def __init__(self, parent, id, application):
        wx.Notebook.__init__(self, parent, id)
        self.parent = parent
        self.venuesPanel = VenuesPanel(self, application)
        self.configurationPanel = ConfigurationPanel(self, application)
        self.securityPanel = SecurityPanel(self, application)
        self.AddPage(self.venuesPanel, "Venues")
        self.AddPage(self.configurationPanel, "Configuration")
        self.AddPage(self.securityPanel, "Security")
        self.Enable(false)
        

# --------------------- TAB 1 -----------------------------------

class VenuesPanel(wx.Panel):
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
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition,
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D)
        self.parent = parent
        self.venueProfilePanel = VenueProfilePanel(self, application)
        self.dividingLine = wx.StaticLine(self,-1,style=wx.LI_VERTICAL)
        self.venuesListPanel = VenueListPanel(self, application)
        self.__doLayout()
        EVT_SIZE(self,self.__onSize)
        
    def __onSize(self,evt):
        self.__doLayout()

    def __doLayout(self):
        venuesPanelBox = wx.BoxSizer(wx.HORIZONTAL)
        venuesPanelBox.Add(self.venuesListPanel, 2, wx.EXPAND|wx.ALL, 10)
        venuesPanelBox.Add(self.dividingLine, 0, wx.EXPAND)
        venuesPanelBox.Add(self.venueProfilePanel, 3, wx.EXPAND|wx.ALL, 10)

        self.SetSizer(venuesPanelBox)
        self.SetAutoLayout(1)
        self.Layout()


class VenueProfilePanel(wx.Panel):
    """
    VenueProfilePanel.

    Contains specific information about one venue, such as title,
    icon, url, and exits to other venues.
    """

    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition,
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D,
                         name = "venueProfilePanel")
        self.application = application
        self.description = wx.TextCtrl(self, -1,'',
                                      style = wx.SIMPLE_BORDER
                                      | wx.NO_3D | wx.TE_MULTILINE
                                      | wx.TE_RICH2 | wx.TE_READONLY)
        self.line1 = wx.StaticLine(self, -1)
        self.urlLabel = wx.StaticText(self, -1, 'URL:  ',
                                     name = "urlLabel", style = wx.ALIGN_LEFT|wx.CENTER)
        self.url = wx.TextCtrl(self, -1, '', name = 'url', style = wx.ALIGN_LEFT
                              | wx.TE_READONLY)
        self.venueTitle = wx.StaticText(self, -1, 'Profile', style = wx.ALIGN_LEFT)
        if IsOSX():
            self.venueTitle.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.venueTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))

        self.description.SetValue("Not connected to server")
        self.description.SetBackgroundColour(self.GetBackgroundColour())
        self.url.SetBackgroundColour(self.GetBackgroundColour())
        self.description.Enable(true)
        self.__doLayout()
        EVT_SIZE(self, self.__onSize)

    def __onSize(self,evt):
        self.__doLayout()

    def ClearAllFields(self):
        self.venueTitle.SetLabel('Profile')
        self.description.SetValue('')
        self.url.SetValue('')
       
    def __hideFields(self):
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
            self.venueTitle.SetLabel(venue.name)
            self.url.SetValue(venue.uri)

            self.url.Show()
            self.urlLabel.Show()
            self.description.SetValue(venue.description)

    def __doLayout(self):
        urlBox=wx.BoxSizer(wx.HORIZONTAL)
        urlBox.Add(self.urlLabel,0,wx.EXPAND|wx.ALIGN_LEFT|wx.CENTER)
        urlBox.Add(self.url,1,wx.EXPAND)
               
        mainBox=wx.BoxSizer(wx.VERTICAL)
        mainBox.Add(self.venueTitle,0,wx.EXPAND|wx.ALL,5)
        mainBox.Add(self.line1,0,wx.EXPAND)
        mainBox.Add(self.description,1,wx.EXPAND|wx.ALL,5)
        mainBox.Add(urlBox,0,wx.EXPAND|wx.ALL,5)

        self.SetSizer(mainBox)
        self.Show(1)
        self.Layout()

class VenueListPanel(wx.Panel):
    '''VenueListPanel.

    Contains the list of venues that are present on the server and buttons
    to execute modifications of the list (add, delete, and modify venue).
    '''
    ID_LIST = wx.NewId()
    ID_ADD = wx.NewId()
    ID_MODIFY = wx.NewId()
    ID_DELETE = wx.NewId()
    DEFAULT_STRING = " (default)"

    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition,
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D)
        self.parent = parent
        self.application = application
        self.listBoxTitle = wx.StaticText(self, -1, 'Venues', style = wx.ALIGN_LEFT)
        if IsOSX():
            self.listBoxTitle.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.listBoxTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))

        self.venuesList = wx.ListBox(self, self.ID_LIST, name = 'venueList',
                                    style = wx.LB_SORT)
        self.addButton = wx.Button(self, self.ID_ADD, 'Add',
                                  name = 'addButton')
        self.modifyButton = wx.Button(self, self.ID_MODIFY, 'Modify',
                                     name = 'modifyButton')
        self.deleteButton = wx.Button(self, self.ID_DELETE, 'Delete',
                                     name = 'deleteButton')
        self.line = wx.StaticLine(self,-1)
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
        EVT_SIZE(self, self.__onSize)

    def OnKey(self, event):
        key = event.GetKeyCode()
        if key == WXK_DELETE:
            self.DeleteVenue()

    def OnDoubleClick(self, event):
        ModifyVenueFrame(self, -1, "", self.venuesList, self.application)

    def EvtListBox(self, event):
        listCtrl = event.GetEventObject()
        data = listCtrl.GetClientData(listCtrl.GetSelection())
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
            message = wx.MessageDialog(self, text, text2,
                                      style = wx.OK|wx.CANCEL|wx.ICON_INFORMATION)

            if(message.ShowModal()==wx.ID_OK):

                try:
                    self.application.DeleteVenue(venueToDelete)
                    if defaultVenueUrl == venueToDelete.uri:
                        # We just deleted default venue
                        self.defaultVenue = None

                except Exception, e:
                    #if "faultstring" in dir(e) and e.faultstring == "NotAuthorized":
                    #    text = "You and are not authorized to administrate \
                    #            this server.\n"
                    #    MessageDialog(None, text, "Authorization Error",
                    #                  wx.OK|wx.ICON_WARNING)
                    #    log.info("VenueManagementClient.ConnectToServer: \
                    #              Not authorized to administrate the server.")
                    #else:
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

                    if self.venuesList.GetCount() > 0:
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
        if(self.venuesList.FindString(venue.name) == wx.NOT_FOUND):
            newUri = self.application.server.AddVenue(venue)
            venue.uri = newUri

            if newUri:
                self.venuesList.Append(venue.name, venue)
                self.venuesList.Select(self.venuesList.FindString(venue.name))
                self.parent.venueProfilePanel.ChangeCurrentVenue(venue)

        else:
            text = "The venue could not be added, \na venue with the same name is already present"
            text2 = "Add Venue Error"
            log.info("VenueListPanel.AddVenue: Can not add venue because another venue with the same name is already present.")
            message = wx.MessageDialog(self, text, text2,
                                      style = wx.OK|wx.ICON_INFORMATION)
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
                    theId = self.venuesList.FindString(self.defaultVenue.name +self.DEFAULT_STRING)
                    self.venuesList.SetString(theId, self.defaultVenue.name)

            # Set default venue for this server
            self.application.server.SetDefaultVenue(venue.id)

        # Set the default venue
        self.defaultVenue = venue
        
        # Reflect the default venue setting in the UI
        theId = self.venuesList.FindString(venue.name)
        if theId != wx.NOT_FOUND:
            self.venuesList.SetString(theId, venue.name+self.DEFAULT_STRING)
                       
    def ModifyVenue(self, venue):
        item = self.venuesList.GetSelection()
        index = self.venuesList.FindString(venue.name)
      
        if(index != wx.NOT_FOUND and index != item):
            text = "The venue could not be modified, a venue with the same name is already present"
            text2 = "Add venue error"
            message = wx.MessageDialog(self, text, text2,
                                      style = wx.OK|wx.ICON_INFORMATION)
            message.ShowModal()
            message.Destroy()
                
        else:
            if venue.uri != None:
                self.application.server.ModifyVenue(str(venue.id), venue)
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

    def __onSize(self,evt):
        self.__doLayout()

    def __doLayout(self):
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.addButton, 1,  wx.EXPAND| wx.LEFT| wx.BOTTOM | wx.ALIGN_CENTER,
                        5)
        buttonSizer.Add(self.modifyButton, 1, wx.EXPAND| wx.LEFT | wx.BOTTOM
                        | wx.ALIGN_CENTER, 5)
        buttonSizer.Add(self.deleteButton, 1, wx.EXPAND| wx.LEFT | wx.BOTTOM | wx.RIGHT
                        | wx.ALIGN_CENTER, 5)

        venueListPanelSizer=wx.BoxSizer(wx.VERTICAL)
        venueListPanelSizer.Add(self.listBoxTitle,0,wx.EXPAND|wx.ALL,5)
        venueListPanelSizer.Add(self.line,0,wx.EXPAND)
        venueListPanelSizer.Add(self.venuesList,1,wx.EXPAND|wx.ALL,5)
        venueListPanelSizer.Add(buttonSizer,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,5)

        self.SetSizer(venueListPanelSizer)

        self.SetAutoLayout(1)
        self.Layout()


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

class ConfigurationPanel(wx.Panel):
    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, 
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D)
        self.application = application
        
        self.detailPanel = DetailPanel(self, application)
        self.__doLayout()
        EVT_SIZE(self,self.__onSize)
    
    def __onSize(self,evt):
        self.__doLayout()

    def __doLayout(self):
        configurationPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        configurationPanelSizer.Add(self.detailPanel, 1, wx.EXPAND|wx.ALL, 10)
        
        self.SetSizer(configurationPanelSizer)
        self.SetAutoLayout(1)
        self.Layout()

class DetailPanel(wx.Panel):
    ID_CHANGE = wx.NewId()
    ID_BROWSE = wx.NewId()
    ID_RANDOM = wx.NewId()
    ID_INTERVAL = wx.NewId()
    ID_ENCRYPT = wx.NewId()
    ID_NEW = wx.NewId()
   
    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, \
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D)
        self.application = application
        self.multicastTitle=wx.StaticText(self, -1, "Multicast Address")
        if IsOSX():
            self.multicastTitle.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.multicastTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))

        self.line1=wx.StaticLine(self,-1)
        self.line2=wx.StaticLine(self,-1)
        self.line3=wx.StaticLine(self,-1)

        self.encryptionTitle=wx.StaticText(self, -1, "Encryption")
        if IsOSX():
            self.encryptionTitle.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.encryptionTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))

        self.randomButton = wx.CheckBox(self, self.ID_RANDOM,
                                          "Standard Range")
        self.intervalButton = wx.CheckBox(self, self.ID_INTERVAL,
                                         "Custom Range: ")
        self.ipAddress = wx.StaticText(self, -1, "224.2.128.0/17")
        self.changeButton = wx.Button(self, self.ID_CHANGE, "Change")
        self.encryptionButton = wx.CheckBox(self, self.ID_ENCRYPT,
                                           " Encrypt media ")
        self.ipString = "224.2.128.0"
        self.maskString = "17"
        self.__doLayout()
        self.__setEvents()
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)

    def __setEvents(self):
        EVT_BUTTON(self, self.ID_CHANGE, self.OpenIntervalDialog)
        EVT_CHECKBOX(self.randomButton, self.ID_RANDOM, self.ClickedOnRandom)
        EVT_CHECKBOX(self.intervalButton, self.ID_INTERVAL, self.ClickedOnInterval)
        EVT_CHECKBOX(self, self.ID_ENCRYPT, self.ClickedOnEncrypt)
        EVT_SIZE(self,self.__onSize)
    
    def __onSize(self,evt):
        self.__doLayout()

    def ClickedOnEncrypt(self, event):
        try:
            log.debug("DetailPanel.ClickedOnEncrypt: Set encryption")
            self.application.SetEncryption(event.Checked())
        except Exception, e:
             #if e.faultstring == "NotAuthorized":
             #    self.encryptionButton.SetValue(not event.Checked())
             #    text = "You are not an administrator on this server and are not authorized to change the media encryption flag.\n"
             #    MessageDialog(None, text, "Authorization Error", wx.OK|wx.ICON_WARNING)
             #    log.info("DetailPanel.ClickedOnEncrypt: Not authorized to change server's media encryption flag.")
             #else:
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
            self.intervalButton.SetValue(false)
        except Exception, e:
            self.ipAddress.Enable(true)
            self.changeButton.Enable(true)
            self.intervalButton.SetValue(true)
            if "faultstring" in dir(e) and e.faultstring == "NotAuthorized":
                text = "You are not an administrator on this server and are not authorized to set multicast addressing to random.\n"
                MessageDialog(None, text, "Authorization Error", wx.OK|wx.ICON_WARNING)
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
            self.randomButton.SetValue(false)
        except Exception, e:
            log.exception('DetailPanel.ClickedOnInterval: failed')
            self.ipAddress.Enable(false)
            self.changeButton.Enable(false)
            self.randomButton.SetValue(true)
            #if e.faultstring == "NotAuthorized":
            #    text = "You are not an administrator on this server and are not authorized to set multicast addressing to interval.\n"
            #    MessageDialog(None, text, "Authorization Error", wx.OK|wx.ICON_WARNING)
            #    log.info("DetailPanel.ClickedOnInterval: Not authorized to set server's multicast address to interval.")
            #else:
            log.exception("DetailPanel.ClickedOnInterval: Set multicast address to interval failed")
            text = "The multicast option could not be set."
            ErrorDialog(None, text, "Set Multicast Error", logFile = VENUE_MANAGEMENT_LOG)

        except:
            log.exception('DetailPanel.ClickedOnInterval: failed')
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
            #if e.faultstring == "NotAuthorized":
            #    text = "You are not an administrator on this server and are not authorized to set the multicast address.\n"
            #    MessageDialog(None, text, "Authorization Error", wx.OK|wx.ICON_WARNING)
            #    log.info("DetailPanel.SetAddress: Not authorized to set server's multicast address.")
            #else:
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
        serviceSizer = wx.BoxSizer(wx.VERTICAL)

        serviceSizer.Add(self.multicastTitle,0,wx.EXPAND|wx.ALL,5)
        serviceSizer.Add(self.line1,0,wx.EXPAND)
        serviceSizer.Add(self.randomButton,0,wx.EXPAND|wx.ALL,5)

        flexSizer = wx.BoxSizer(wx.HORIZONTAL)
        flexSizer.Add(self.intervalButton, 0, wx.CENTER|wx.RIGHT, 5)
        flexSizer.Add(self.ipAddress, 1, wx.CENTER|wx.RIGHT,5)
        flexSizer.Add(self.changeButton, 0, wx.CENTER)
        serviceSizer.Add(flexSizer,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,5)

        serviceSizer.Add(self.line2,0,wx.EXPAND|wx.BOTTOM,10)

        serviceSizer.Add(self.encryptionTitle,0,wx.EXPAND|wx.ALL,5)
        serviceSizer.Add(self.line3,0,wx.EXPAND)
        serviceSizer.Add(self.encryptionButton, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(serviceSizer)
        serviceSizer.Fit(self)

        self.Layout()


# --------------------- TAB 3 -----------------------------------

class SecurityPanel(wx.Panel):
    ID_SECURITY = wx.NewId()
     
    def __init__(self, parent, application):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, 
                         wx.DefaultSize, wx.NO_BORDER|wx.SW_3D)
        self.application = application
        self.securityTitle = wx.StaticText(self, -1, "Security")
        self.line1 = wx.StaticLine(self, -1)
        if IsOSX():
            self.securityTitle.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.securityTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        
        self.securityText = wx.StaticText(self, -1, "Manage access to venue server including which users are allowed to administrate.")
        self.securityButton = wx.Button(self, self.ID_SECURITY, "Manage Security")
        self.__doLayout()
        EVT_BUTTON(self, self.ID_SECURITY, self.OpenSecurityDialog)

    def OpenSecurityDialog(self, event):
        f = AuthorizationUIDialog(self, -1, "Security", log)
        wx.BeginBusyCursor()
        
        ctx = self.application.app.GetContext()
        transdict = {'ssl_context':ctx}
        authManagerUrl = self.application.serverUrl.encode('ascii','ignore') + '/Authorization'
        authManagerIW = AuthorizationManagerIW(authManagerUrl,transdict=transdict)
        f.ConnectToAuthManager(authManagerIW)
        wx.EndBusyCursor()
        
        if f.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()
            f.Apply()
            wx.EndBusyCursor()
        f.Destroy()

    def __doLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.securityTitle,0,wx.EXPAND|wx.TOP|wx.LEFT, 15)
        sizer.Add(self.line1,0,wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.securityText, 1, wx.EXPAND|wx.ALL|wx.CENTER,5)
        sizer2.Add(self.securityButton, 0, wx.ALL, 5)

        sizer.Add(sizer2, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 15)
              
        self.SetSizer(sizer)
        sizer.Fit(self)
        sizer.Layout()
        
#--------------------- DIALOGS -----------------------------------
IP = 1
IP_1 = 2
MASK = 4
TTL = 5
PORT = 6

class MulticastDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        self.SetSize(wx.Size(400, 350))
        self.parent = parent
        self.ipAddressLabel = wx.StaticText(self, -1, "IP Address: ")
        self.ipAddress1 = wx.TextCtrl(self, -1, "", size = (30,-1),
                                     validator = DigitValidator(IP_1))
        self.ipAddress2 = wx.TextCtrl(self, -1, "", size = (30,-1),
                                     validator = DigitValidator(IP))
        self.ipAddress3 = wx.TextCtrl(self, -1, "", size = (30,-1),
                                     validator = DigitValidator(IP))
        self.ipAddress4 = wx.TextCtrl(self, -1, "", size = (30,-1),
                                     validator = DigitValidator(IP))
        self.maskLabel = wx.StaticText(self, -1, "Mask: ")
        self.mask = wx.TextCtrl(self, -1, "", size = (30,-1),
                               validator = DigitValidator(MASK))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.__doLayout()
        if (self.ShowModal() == wx.ID_OK ):
            address = self.ipAddress1.GetValue() + "." +\
                      self.ipAddress2.GetValue() + "." +\
                      self.ipAddress3.GetValue() + "." +\
                      self.ipAddress4.GetValue()
            self.parent.SetAddress(address, self.mask.GetValue())
        self.Destroy();

    def __doLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        theSizer = wx.FlexGridSizer(0, 5, 10, 10)
        theSizer.Add(self.ipAddressLabel, 0, wx.ALIGN_RIGHT)
        theSizer.Add(self.ipAddress1)
        theSizer.Add(self.ipAddress2)
        theSizer.Add(self.ipAddress3)
        theSizer.Add(self.ipAddress4)
        theSizer.Add(self.maskLabel, 0, wx.ALIGN_RIGHT)
        theSizer.Add(self.mask)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)

        sizer.Add(theSizer, 0, wx.ALL, 10)
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        self.Layout()

class VenueParamFrame(wx.Dialog):
       
    def __init__(self, parent, id, title, application):
        wx.Dialog.__init__(self, parent, id, title,
                          style = wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        self.parent = parent
        self.Centre()
        self.noteBook = wx.Notebook(self, -1)

        self.venue = None
        self.exitsList = []
        self.streams = []
        self.encryptionType = (0, None)
        
        self.SetSize(wx.Size(400, 350))
        self.application = application
   
        self.generalPanel = GeneralPanel(self.noteBook, -1, application)
        self.encryptionPanel = EncryptionPanel(self.noteBook, -1, application)
        self.staticAddressingPanel = StaticAddressingPanel(self.noteBook, -1,
                                                           application)
        self.authorizationPanel = AuthorizationUIPanel(self.noteBook, -1, log,requireCertOption=1)
        
        self.noteBook.AddPage(self.generalPanel, "General")
        self.noteBook.AddPage(self.encryptionPanel, "Encryption")
        self.noteBook.AddPage(self.staticAddressingPanel, "Addressing")
      
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton =  wx.Button(self, wx.ID_CANCEL, "Cancel")
             
        self.__doLayout() 

    def __doLayout(self):
        boxSizer = wx.BoxSizer(wx.VERTICAL)
        boxSizer.Add(self.noteBook, 1, wx.EXPAND)

        buttonSizer =  wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0,wx.EXPAND|wx.RIGHT,10)
        buttonSizer.Add(self.cancelButton, 0,wx.EXPAND)

        boxSizer.Add(buttonSizer, 0, wx.CENTER | wx.BOTTOM | wx.TOP , 5)

        self.SetSizer(boxSizer)
        boxSizer.Fit(self)
        self.SetAutoLayout(1)
        self.Layout()
                    
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
            theExit = self.generalPanel.exits.GetClientData(index)
            exitsList.append(theExit)

        # Get Static Streams
        sap = self.staticAddressingPanel
        if(sap.staticAddressingButton.GetValue()==1):

            # Get the venue name to use as the stream name
            venueName = self.generalPanel.title.GetValue()

            # Static Video
            svml = MulticastNetworkLocation(sap.GetVideoAddress(),
                                            int(sap.GetVideoPort()),
                                            int(sap.GetVideoTtl()))
            strid = GUID()
            staticVideoCap =  [ Capability( Capability.CONSUMER,
                                          Capability.VIDEO,
                                          "H261",
                                          90000, strid)]
            streams.append(StreamDescription(venueName,
                                                  svml, staticVideoCap,
                                                  0, None, 1))
            # Static Audio
            saml = MulticastNetworkLocation(sap.GetAudioAddress(),
                                            int(sap.GetAudioPort()),
                                            int(sap.GetAudioTtl()))
            strid = GUID()
            staticAudioCap =  [ Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L16",16000,strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L16",8000,strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L8",16000, strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "L8",8000, strid),
                               Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                           "PCMU", 16000, strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "PCMU",8000, strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "GSM",16000, strid),
                              Capability( Capability.CONSUMER,
                                          Capability.AUDIO,
                                          "GSM",8000, strid)]
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
        return (self.generalPanel.Validate() and
                self.staticAddressingPanel.Validate())
                     
class AddVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, application)
        self.SetSize(wx.Size(600, 470))
        self.SetLabel('Add Venue')
        self.application.SetCurrentVenue(None)
        self.generalPanel.LoadLocalVenues()
        self.encryptionPanel.genKeyButton.Hide()
        self.encryptionPanel.ClickEncryptionButton(None,
                                                   self.application.encrypt)
        
        self.noteBook.AddPage(self.authorizationPanel, "Security")
        self.authorizationPanel.Disable()
        
        EVT_BUTTON (self.okButton, wx.ID_OK, self.OnOK)
        self.ShowModal()

    def OnOK (self, event):
        wx.BeginBusyCursor()

        if (VenueParamFrame.Validate(self)): #and 
            #self.staticAddressingPanel.Validate() and 
            #self.generalPanel.Validate()):)
            self.Ok()
            try:
                log.debug("AddVenueFrame.OnOk: Add venue.")
                self.parent.AddVenue(self.venue)
            except Exception, e:
                #if e.faultstring == "NotAuthorized":
                #    text = "You are not a server administrator and are not authorized to add venues to this server.\n"
                #    MessageDialog(None, text, "Authorization Error", wx.OK|wx.ICON_WARNING)
                #    log.info("AddVenueFrame.OnOK: Not authorized to add venue to server.")
                #else:
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
        wx.EndBusyCursor()


class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, application)
        wx.BeginBusyCursor()
        self.SetSize(wx.Size(600, 470))
        self.SetLabel('Modify Venue')
        
        self.__loadCurrentVenueInfo(venueList)
        self.generalPanel.LoadLocalVenues()

        # Connect to authorization manager.
        self.noteBook.AddPage(self.authorizationPanel, "Security")
        
        ctx = self.application.app.GetContext()
        transdict = {'ssl_context':ctx}
        authManagerUrl = self.venue.uri.encode('ascii','ignore') + '/Authorization'
        authManagerIW = AuthorizationManagerIW(authManagerUrl,transdict=transdict)
        self.authorizationPanel.ConnectToAuthManager(authManagerIW)
        #self.authorizationPanel.Hide()
        
        wx.EndBusyCursor()

        EVT_BUTTON (self.okButton, wx.ID_OK, self.OnOK)
        self.ShowModal()

    def OnOK (self, event):
        wx.BeginBusyCursor()
        if(VenueParamFrame.Validate(self)):
            #if(self.staticAddressingPanel.Validate()):
            if 1:
#FIXME - This is obviously an immediately-before-release fix;
#        it needs to be resolved corectly
                venueUri = self.venue.uri
                id = self.venue.id
                self.Ok()
                self.venue.uri = venueUri
                self.venue.id = id
                print 'venue = ', self.venue, self.venue.streams
                try:
                    log.debug("ModifyVenueFrame.OnOk: Modify venue")
                    self.parent.ModifyVenue(self.venue)
                    self.authorizationPanel.Apply()
                    
                except Exception, e:
                    log.exception("ModifyVenueFrame.OnOk: Modify venue failed")
                    text = "Could not modify venue %s" %self.venue.name
                    if hasattr(e, "string"):
                        text = text + "\n%s" % e.faultstring
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

        wx.EndBusyCursor()

    def __loadCurrentVenueInfo(self, venueList):
        item = venueList.GetSelection()
        self.venue = venueList.GetClientData(item)

        # Get the real venue description
        ctx = self.application.app.GetContext()
        transdict = {'ssl_context':ctx}
        venueProxy = VenueIW(self.venue.uri,transdict=transdict)
        self.venue = venueProxy.AsVenueDescription()
        
        self.generalPanel.title.AppendText(self.venue.name)
        self.generalPanel.description.AppendText(self.venue.description)

        log.debug("ModifyVenueFrame.__loadCurrentVenueInfo: Get venue information")
        self.application.SetCurrentVenue(self.venue)

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
            self.staticAddressingPanel.genAddrButton.Enable(true)
            for stream in self.venue.streams:
                if(stream.capability[0].type == Capability.VIDEO):
                    sl = stream.location
                    self.staticAddressingPanel.SetStaticVideo(sl.host, sl.port,
                                                              sl.ttl)
                elif(stream.capability[0].type == Capability.AUDIO):
                    sl = stream.location
                    self.staticAddressingPanel.SetStaticAudio(sl.host, sl.port,
                                                              sl.ttl)

class GeneralPanel(wx.Panel):
    ID_TRANSFER = wx.NewId()
    ID_LOAD = wx.NewId()
    ID_DEFAULT = wx.NewId()
    ID_EXIT_EDIT = wx.NewId()
    ID_EXIT_ADD = wx.NewId()
    ID_EXIT_REMOVE = wx.NewId()
    
    def __init__(self, parent, id, app):
        wx.Panel.__init__(self, parent, id)
        self.application = app
        self.parent = parent
        self.informationTitle = wx.StaticText(self, -1, "Information")
        if IsOSX():
            self.informationTitle.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.informationTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL,
                                                 wx.NORMAL, wx.BOLD))

        self.exitsTitle = wx.StaticText(self, -1, "Exits")
        if IsOSX():
            self.exitsTitle.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.exitsTitle.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL,
                                           wx.NORMAL, wx.BOLD))

        self.line1=wx.StaticLine(self,-1)
        self.line3=wx.StaticLine(self,-1)
        
        self.titleLabel =  wx.StaticText(self, -1, "Title: ")
        self.title =  wx.TextCtrl(self, -1, "",  size = wx.Size(200, -1))
        self.descriptionLabel = wx.StaticText(self, -1, "Description:")
        self.description =  wx.TextCtrl(self, -1, "", size = wx.Size(200, 70),
                                       style = wx.TE_MULTILINE |
                                       wx.TE_RICH2)
        self.defaultVenue = wx.CheckBox(self, self.ID_DEFAULT, "Set this venue as default.")
        
        self.venuesLabel = wx.StaticText(self, -1, "Available Venues:")
        # This is actually available exits
        self.venues = wx.ListBox(self, -1, size = wx.Size(250, 100),
                                style = wx.LB_SORT)
        self.transferVenueLabel = wx.StaticText(self, -1, "Add Exit", style = wx.ALIGN_CENTER)
        self.transferVenueButton = wx.Button(self, self.ID_TRANSFER, ">>")
        self.address = wx.ComboBox(self, -1, self.application.serverUrl,\
                                  choices = [self.application.serverUrl],
                                  style = wx.CB_DROPDOWN)
        self.goButton = wx.Button(self, self.ID_LOAD, "Go")
        self.exitsLabel = wx.StaticText(self, -1, "Exits for your venue:")
        # This is the exits this venue has
        self.exits = wx.ListBox(self, -1, size = wx.Size(250, 100),
                               style = wx.LB_SORT)

        # Menu for exits:
        self.exitsMenu = wx.Menu()
        self.exitsMenu.Append(self.ID_EXIT_ADD,"Add Exit...",
                              "Add an exit.")
        self.exitsMenu.Append(self.ID_EXIT_EDIT,"Edit...",
                              "Edit this exit.")
        self.exitsMenu.Append(self.ID_EXIT_REMOVE,"Remove",
                              "Remove this exit.")
        
        self.SetValidator(GeneralPanelValidator())
        
        EVT_MENU(self, self.ID_EXIT_EDIT, self.UpdateExit)
        EVT_MENU(self, self.ID_EXIT_ADD, self.ManuallyAddExit)
        EVT_MENU(self, self.ID_EXIT_REMOVE, self.RemoveExit)
        EVT_RIGHT_DOWN(self.exits, self.OnRightClick)
        EVT_SIZE(self,self.__onSize)
        
        self.__doLayout()
        self.__setEvents()
        
        self.currentVenueUrl = None

    def __onSize(self,evt):
        self.__doLayout()

    def LoadRemoteVenues(self, event = None):
        URL = self.address.GetValue()
        self.__loadVenues(URL)
        if self.address.FindString(URL) == wx.NOT_FOUND:
            log.debug("VenueParamFrame.LoadRemoteVenues: Append address to combobox: %s " % URL)
            self.address.Append(URL)

    def LoadLocalVenues(self):
        self.__loadVenues(self.application.serverUrl)

    def __loadVenues(self, URL):
        self.currentVenueUrl = self.address.GetValue() # used in except:
        try:
            wx.BeginBusyCursor()
            log.debug("VenueParamFrame.__LoadVenues: Load venues from: %s " % URL)
            ctx = self.application.app.GetContext()
            transdict = {'ssl_context':ctx}
            server = VenueServerIW(URL,transdict=transdict)
            
            vl = server.GetVenues()
            
            # Remove the current venue from the list of potential exits
            if self.application.currentVenue:
                vl = filter(lambda v,url=self.application.currentVenue.uri:
                            v.uri != url, vl)
            
            self.venues.Clear()
            cdl = map(lambda x: ConnectionDescription(x.name,
                                                      x.description,
                                                      x.uri, x.id), vl)
            map(lambda x: self.venues.Append(x.name, x), cdl)
            
            self.currentVenueUrl = URL
            self.address.SetValue(URL)
            
            wx.EndBusyCursor()
    
        except:
            wx.EndBusyCursor()
            self.address.SetValue(self.currentVenueUrl)
            log.exception("VenueParamFrame.__LoadVenues: Could not load exits from server at %s" %URL)
            MessageDialog(None, "Could not load exits from server at " + str(URL), "Load Exits Error", wx.OK|wx.ICON_INFORMATION)
    
    def OnRightClick(self, event):
        self.x = event.GetX() + self.exits.GetPosition().x
        self.y = event.GetY() + self.exits.GetPosition().y
        
        self.PopupMenu(self.exitsMenu, wx.Point(self.x, self.y))
                       
    def AddExit(self, event):
        index = self.venues.GetSelection()
        if index != -1:
            venue = self.venues.GetClientData(index)
            
            existingExit = 0
            numExits = self.exits.GetCount()
            for index in range(numExits):
                theExit = self.exits.GetClientData(index)
              
                if theExit.uri == venue.uri:
                    existingExit = 1
                    break
            if existingExit:
                text = ""+venue.name+" is added already"
                exitExistDialog = wx.MessageDialog(self, text, '',
                                                  wx.OK | wx.ICON_INFORMATION)
                exitExistDialog.ShowModal()
                exitExistDialog.Destroy()
            else:
                self.exits.Append(venue.name, venue)
                                 
    def ManuallyAddExit(self, event):
        index = self.exits.GetSelection()
              
        dlg = RenameExitDialog(self, -1, "ADD EXIT", "Enter Name Here", "Enter URL Here")
        if (dlg.ShowModal() == wx.ID_OK ):
            name = dlg.GetName()
            url = dlg.GetUrl()

            connDesc = ConnectionDescription(name, "", uri = url)
            index = self.exits.Append(name, connDesc)
            self.exits.SetClientData(index, connDesc)
                 
    def UpdateExit(self, event):
        index = self.exits.GetSelection()

        if index != -1:
            oldName = self.exits.GetString(index)
            oldUrl =  self.exits.GetClientData(index).uri

            name = None
            
            dlg = RenameExitDialog(self, -1, "Edit Exit", oldName, oldUrl)
            if (dlg.ShowModal() == wx.ID_OK ):
                name = dlg.GetName()
                url = dlg.GetUrl()
            else:
                return
               
            self.exits.SetString(index, name)
            connDesc = self.exits.GetClientData(index)
            connDesc.SetName(name)
            connDesc.SetURI(url)
            self.exits.SetClientData(index, connDesc)
            
        else:
            dlg = wx.MessageDialog(self, "Select exit to edit", "Edit Exit",
                                  style = wx.ICON_INFORMATION|wx.OK)
            dlg.ShowModal()
            
    def RemoveExit(self, event):
        index = self.exits.GetSelection()
        if index != -1:
            self.exits.Delete(index)
    
    def __setEvents(self):
        EVT_BUTTON(self, self.ID_TRANSFER, self.AddExit)
        EVT_BUTTON(self, self.ID_LOAD, self.LoadRemoteVenues)

    def __doLayout(self):
        titleSizer=wx.BoxSizer(wx.HORIZONTAL)
        titleSizer.Add(self.titleLabel, 0, wx.EXPAND|wx.ALIGN_RIGHT)
        titleSizer.Add(self.title,1,wx.EXPAND)
        
        infoSizer=wx.BoxSizer(wx.VERTICAL)
        infoSizer.Add(self.informationTitle,0,wx.EXPAND|wx.ALL,5)
        infoSizer.Add(self.line1,0,wx.EXPAND)
        infoSizer.Add(titleSizer,0,wx.EXPAND|wx.ALL,5)
        infoSizer.Add(self.descriptionLabel, 0, wx.EXPAND|wx.ALIGN_LEFT|wx.TOP|wx.LEFT|wx.BOTTOM,5)
        infoSizer.Add(self.description, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        infoSizer.Add(self.defaultVenue,0,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.TOP,5)

        urlSizer=wx.BoxSizer(wx.HORIZONTAL)
        urlSizer.Add(self.address,1,wx.EXPAND)
        urlSizer.Add(self.goButton,0,wx.EXPAND|wx.LEFT,5)

        availSizer=wx.BoxSizer(wx.VERTICAL)
        availSizer.Add(self.venuesLabel,0,wx.EXPAND|wx.BOTTOM,5)
        availSizer.Add(self.venues,1,wx.EXPAND|wx.BOTTOM,5)
        availSizer.Add(urlSizer,0,wx.EXPAND)
        
        addSizer=wx.BoxSizer(wx.VERTICAL)
        addSizer.Add(self.transferVenueLabel,0,wx.EXPAND|wx.CENTER)
        addSizer.Add(self.transferVenueButton,0,wx.EXPAND|wx.TOP,5)
        
        exitsSizer=wx.BoxSizer(wx.VERTICAL)
        exitsSizer.Add(self.exitsLabel,0,wx.EXPAND|wx.BOTTOM,5)
        exitsSizer.Add(self.exits,1,wx.EXPAND|wx.BOTTOM,5)
               
        bottomSubSizer=wx.BoxSizer(wx.HORIZONTAL)
        bottomSubSizer.Add(availSizer,1,wx.EXPAND|wx.RIGHT,5)
        bottomSubSizer.Add(addSizer,0,wx.CENTER|wx.RIGHT,5)
        bottomSubSizer.Add(exitsSizer,1,wx.EXPAND,5)

        bottomSizer=wx.BoxSizer(wx.VERTICAL)
        bottomSizer.Add(self.exitsTitle,0,wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT,5)
        bottomSizer.Add(self.line3,0,wx.EXPAND)
        bottomSizer.Add(bottomSubSizer,1,wx.EXPAND|wx.TOP,5)

        mainSizer=wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(infoSizer,1,wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM,5)
        mainSizer.Add(bottomSizer,1,wx.EXPAND|wx.ALL,5)

        self.SetSizer(mainSizer)
        self.Layout()

    def Validate(self):
        return self.GetValidator().Validate(self)

class GeneralPanelValidator(wx.PyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    GeneralPanel.
    '''
    def __init__(self):
        wx.PyValidator.__init__(self)
                   
    def Clone(self):
        '''
        Returns a new GeneralPanelValidator.
        Note: Overrides super class method.
        '''
        return GeneralPanelValidator()

    def Validate(self, win):
        '''
        Checks if win has correct parameters.
        '''
        
        title = win.title.GetValue()
        description = win.description.GetValue()
        
        if len(title) < 1 or len(description) < 1:
            MessageDialog(None, "Please, fill in your name and description in the 'General' tab", "Notification")
            return false
        else:
            return true
        
    def TransferToWindow(self):
        return true # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wx.Dialog from complaining.

class EncryptionPanel(wx.Panel):
    ID_BUTTON = wx.NewId()
    ID_GENKEYBUTTON = wx.NewId()
    
    def __init__(self, parent, id, application):
        wx.Panel.__init__(self, parent, id)
        self.application = application
        self.encryptMediaButton = wx.CheckBox(self, self.ID_BUTTON,
                                             " Encrypt media ")
        self.keyText = wx.StaticText(self, -1, "Optional key: ",
                                    size = wx.Size(100,-1))
        self.keyCtrl = wx.TextCtrl(self, -1, "", size = wx.Size(200,-1))
        self.genKeyButton = wx.Button(self, self.ID_GENKEYBUTTON,
                                     "Generate New Key")# size= wx.Size(100, 20))
        self.keyText.Enable(false)
        self.keyCtrl.Enable(false)
        self.genKeyButton.Enable(false)
        self.__doLayout()
        self.__setEvents()

    def ClickEncryptionButton(self, event = None, value = None):
        theId = None
        if event == None:
            theId = value
            self.encryptMediaButton.SetValue(value)
        else:
            theId = event.Checked()
        self.keyText.Enable(theId)
        self.keyCtrl.Enable(theId)
        self.genKeyButton.Enable(theId)

    def ClickGenKeyButton(self, event = None, value = None):
        self.keyCtrl.Clear()
        newKey = self.application.currentVenueClient.RegenerateEncryptionKeys()
        self.keyCtrl.SetValue(newKey)

    def __setEvents(self):
        EVT_CHECKBOX(self, self.ID_BUTTON, self.ClickEncryptionButton)
        EVT_BUTTON(self, self.ID_GENKEYBUTTON, self.ClickGenKeyButton)
        
    def __doLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.Size(10,10))
        sizer.Add(self.encryptMediaButton, 0, wx.EXPAND|wx.ALL, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(wx.Size(25, 10))
        sizer2.Add(self.keyText , 0, wx.EXPAND|wx.ALL, 5)
        sizer2.Add(self.keyCtrl, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(sizer2, 0, wx.EXPAND | wx.RIGHT, 10)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.genKeyButton, 1, wx.ALL, 5)
        sizer.Add(sizer3, 1, wx.RIGHT, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

class StaticAddressingPanel(wx.Panel):
    ID_GENADDRBUTTON = wx.NewId()

    def __init__(self, parent, id, application):
        wx.Panel.__init__(self, parent, id)
        self.application = application
        self.ipAddressConverter = IpAddressConverter()
        self.staticAddressingButton = wx.CheckBox(self, 5,
                                                 " Use Static Addressing")
        self.panel = wx.Panel(self, -1)
        self.videoTitleText = wx.StaticText(self.panel, -1, "Video (h261)",
                                           size = wx.Size(100,20))
        if IsOSX():
            self.videoTitleText.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.videoTitleText.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        self.audioTitleText = wx.StaticText(self.panel, -1, "Audio (16kHz)",
                                           size = wx.Size(100,20))
        if IsOSX():
            self.audioTitleText.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.BOLD))
        else:
            self.audioTitleText.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        self.videoAddressText = wx.StaticText(self.panel, -1, "Address: ",
                                             size = wx.Size(60,-1), style = wx.ALIGN_RIGHT)
        self.audioAddressText = wx.StaticText(self.panel, -1, "Address: ",
                                             size = wx.Size(60,-1), style = wx.ALIGN_RIGHT)
        self.videoPortText = wx.StaticText(self.panel, -1, " Port: ",
                                          size = wx.Size(45,-1), style = wx.ALIGN_RIGHT)
        self.audioPortText = wx.StaticText(self.panel, -1, " Port: ",
                                          size = wx.Size(45,-1), style = wx.ALIGN_RIGHT)
        self.videoTtlText = wx.StaticText(self.panel, -1, " TTL:",
                                         size = wx.Size(40,-1), style = wx.ALIGN_RIGHT)
        self.audioTtlText = wx.StaticText(self.panel, -1, " TTL:",
                                         size = wx.Size(40,-1), style = wx.ALIGN_RIGHT)
        self.videoIp1 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.videoIp2 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.videoIp3 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.videoIp4 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.videoPort = wx.TextCtrl(self.panel, -1, "", size = wx.Size(50,-1))
        self.videoTtl = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.audioIp1 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.audioIp2 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.audioIp3 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.audioIp4 = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))
        self.audioPort = wx.TextCtrl(self.panel, -1, "", size = wx.Size(50,-1))
        self.audioTtl = wx.TextCtrl(self.panel, -1, "", size = wx.Size(30,-1))

        self.genAddrButton = wx.Button(self, self.ID_GENADDRBUTTON,
                                     "Generate New Addresses")

        if self.staticAddressingButton.GetValue():
            self.panel.Enable(true)
            self.genAddrButton.Enable(true)
        else:
            self.panel.Enable(false)
            self.genAddrButton.Enable(false)

        self.SetValidator(StaticAddressingValidator())

        self.__doLayout()
        self.__setEvents()

    def __doLayout(self):
        staticAddressingSizer = wx.BoxSizer(wx.VERTICAL)
        staticAddressingSizer.Add(wx.Size(10,10))
        staticAddressingSizer.Add(self.staticAddressingButton, 0,
                                  wx.EXPAND|wx.ALL, 5)

        panelSizer = wx.BoxSizer(wx.VERTICAL)

        videoIpSizer = wx.BoxSizer(wx.HORIZONTAL)
        videoIpSizer.Add(self.videoIp1, 1 , wx.EXPAND)
        videoIpSizer.Add(self.videoIp2, 1 , wx.EXPAND)
        videoIpSizer.Add(self.videoIp3, 1 , wx.EXPAND)
        videoIpSizer.Add(self.videoIp4, 1 , wx.EXPAND)

        audioIpSizer = wx.BoxSizer(wx.HORIZONTAL)
        audioIpSizer.Add(self.audioIp1, 1 , wx.EXPAND)
        audioIpSizer.Add(self.audioIp2, 1 , wx.EXPAND)
        audioIpSizer.Add(self.audioIp3, 1 , wx.EXPAND)
        audioIpSizer.Add(self.audioIp4, 1 , wx.EXPAND)

        videoTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        videoTitleSizer.Add(self.videoTitleText, 0, wx.ALIGN_CENTER)
        videoTitleSizer.Add(wx.StaticLine(self.panel, -1), 1, wx.ALIGN_CENTER)

        panelSizer.Add(videoTitleSizer, 1 ,  wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 10)

        vidSizer=wx.BoxSizer(wx.HORIZONTAL)
        vidSizer.Add(self.videoAddressText,0,wx.EXPAND|wx.LEFT,10)
        vidSizer.Add(videoIpSizer,5,wx.EXPAND)
        vidSizer.Add(self.videoPortText,0,wx.EXPAND)
        vidSizer.Add(self.videoPort,2,wx.EXPAND)
        vidSizer.Add(self.videoTtlText,0,wx.EXPAND)
        vidSizer.Add(self.videoTtl,1,wx.EXPAND)

        panelSizer.Add(vidSizer, 0 , wx.EXPAND|wx.ALL, 5)

        audioTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        audioTitleSizer.Add(self.audioTitleText, 0, wx.ALIGN_CENTER)
        audioTitleSizer.Add(wx.StaticLine(self.panel, -1), 1, wx.ALIGN_CENTER)

        panelSizer.Add(wx.Size(10,10))

        panelSizer.Add(audioTitleSizer, 1 , wx.EXPAND|wx.LEFT|wx.RIGHT, 10)

        audSizer=wx.BoxSizer(wx.HORIZONTAL)
        audSizer.Add(self.audioAddressText,0,wx.EXPAND|wx.LEFT,10)
        audSizer.Add(audioIpSizer,5,wx.EXPAND)
        audSizer.Add(self.audioPortText,0,wx.EXPAND)
        audSizer.Add(self.audioPort,2,wx.EXPAND)
        audSizer.Add(self.audioTtlText,0,wx.EXPAND)
        audSizer.Add(self.audioTtl,1,wx.EXPAND)

        panelSizer.Add(audSizer, 0 , wx.EXPAND|wx.ALL, 5)
        self.panel.SetSizer(panelSizer)
        panelSizer.Fit(self.panel)

        staticAddressingSizer.Add(self.panel, 0 , wx.EXPAND)

        staticAddressingSizer.Add(self.genAddrButton, 0, wx.LEFT, 5)
        
        self.SetSizer(staticAddressingSizer)
        staticAddressingSizer.Fit(self)
        self.SetAutoLayout(1)

    def __setEvents(self):
        EVT_CHECKBOX(self, 5, self.ClickStaticButton)
        EVT_BUTTON(self, self.ID_GENADDRBUTTON, self.ClickGenAddrButton)

    def ClickGenAddrButton(self, event = None, value = None):
        vNL = self.application.currentVenueClient.AllocateMulticastLocation()
        self.SetStaticVideo(vNL.GetHost(), vNL.GetPort(), 127)
        aNL = self.application.currentVenueClient.AllocateMulticastLocation()
        self.SetStaticAudio(aNL.GetHost(), aNL.GetPort(), 127)
        
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
            self.genAddrButton.Enable(true)
            self.panel.Enable(true)
        else:
            self.genAddrButton.Enable(false)
            self.panel.Enable(false)

    def Validate(self):
        if(self.staticAddressingButton.GetValue()):
            return self.GetValidator().Validate(self)
        else:
            return true

class StaticAddressingValidator(wx.PyValidator):
    '''
    Validator used to ensure correctness of parameters entered in
    StaticAddressingPanel.
    '''
    def __init__(self):
        wx.PyValidator.__init__(self)
                   
    def Clone(self):
        '''
        Returns a new StaticAddressingValidator.
        Note: Overrides super class method.
        '''
        return StaticAddressingValidator()

    def Validate(self, win):
        '''
        Checks if win has correct parameters.
        '''
              
        return (self.__CheckIP(win.videoIp1, win.videoIp2, win.videoIp3, win.videoIp4) and
                self.__CheckIP(win.audioIp1, win.audioIp2, win.audioIp3, win.audioIp4) and
                self.__CheckPort(win.videoPort) and
                self.__CheckPort(win.audioPort) and
                self.__CheckTTL(win.videoTtl) and
                self.__CheckTTL(win.audioTtl))
      
    def __CheckIP(self, ip1, ip2, ip3, ip4):
        try:
            i1 = int(ip1.GetValue())
            i2 = int(ip2.GetValue())
            i3 = int(ip3.GetValue())
            i4 = int(ip4.GetValue())
        except ValueError:
            MessageDialog(None,"Please, fill in all IP Address fields in 'Addressing' tab.", "Notification")
            return false
        
        if (i1 in range(224, 240) and
            i2 in range(0,256) and
            i3 in range(0,256) and
            i4 in range(0,256)):
            return true
        else:
            MessageDialog(None, "Allowed values for IP Address are between 224.0.0.0 - 239.255.255.255 in 'Addressing' tab", "Notification")
            return false

    def __CheckPort(self, port):
        try:
            int(port.GetValue())
            return true
        except ValueError:
            MessageDialog(None,"%s is not a valid port in 'Addressing' tab."%(port.GetValue()), "Notification")
            return false

    def __CheckTTL(self, ttl):
        try:
            ttl = int(ttl.GetValue())
        except ValueError:
            MessageDialog(None,"%s is not a valid time to live (TTL) value in 'Addressing' tab."%(ttl.GetValue()), "Notification")
            return false

        if not ttl in range(0,128):
            MessageDialog(None, "Time to live (TTL) should be a value between 0 - 127 in 'Addressing' tab.", "Notification")
            return false
        else:
            return true
                            
    def TransferToWindow(self):
        return true # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wx.Dialog from complaining.



class RenameExitDialog(wx.Dialog):
    def __init__(self, parent, id, title, oldName, oldUrl):
        wx.Dialog.__init__(self, parent, id, title)
        #self.text = wx.StaticText(self, -1, "Please, enter a new title for the venue.", style=wx.ALIGN_LEFT)
       
        self.line = wx.StaticLine(self, -1)

        self.nameText = wx.StaticText(self, -1, "Title:")
        self.nameBox =  wx.TextCtrl(self, -1, oldName)
        self.urlText = wx.StaticText(self, -1, "Url:")
        self.urlBox =  wx.TextCtrl(self, -1, oldUrl)
        self.nameBox.SetSize(wx.Size(200, 20))

        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
    
    def GetName(self):
        return self.nameBox.GetValue()

    def GetUrl(self):
        return self.urlBox.GetValue()
        
    def Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        s2 = wx.FlexGridSizer(2, 2, 5, 5) 
        s2.Add(self.nameText, 0, wx.CENTER | wx.RIGHT, 5)
        s2.Add(self.nameBox, 0,  wx.CENTER | wx.LEFT, 5)
        s2.Add(self.urlText, 0, wx.CENTER | wx.RIGHT, 5)
        s2.Add(self.urlBox, 0,  wx.CENTER | wx.LEFT | wx.EXPAND, 5)
        sizer.Add(s2, 0, wx.EXPAND| wx.ALL, 10)
        sizer.Add(self.line, 0, wx.ALL | wx.EXPAND, 10)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wx.ALL, 5)
        buttonSizer.Add(self.cancelButton, 0, wx.ALL, 5)
        sizer.Add(buttonSizer, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5) 
            
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)


class DigitValidator(wx.PyValidator):
    def __init__(self, flag):
        wx.PyValidator.__init__(self)
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
        return true # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wx.Dialog from complaining.

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
            
        if not wx.Validator_IsSilent():
            wx.Bell()

        # Returning without calling event.Skip eats the event before it
        # gets to the text control
        return

'''class TextValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)

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
        return true # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wx.Dialog from complaining.
'''


class IpAddressConverter:
    def __init__(self):
        self.ipString = ""
        self.ipIntList = []

    def StringToIp(self, ipString):
        ipStringList = string.split(ipString, '.')
        self.ipIntList = map(int, ipStringList)
        return self.ipIntList

    def IpToString(self, ip1, ip2, ip3, ip4):
        self.ipString = str(ip1)+'.'+str(ip2)+'.'+str(ip3)+'.'+str(ip4)
        return self.ipString

if __name__ == "__main__":
    wx.InitAllImageHandlers()

    app = VenueManagementClient()
    debugMode = Toolkit.Application.instance().GetOption("debug")
    app.SetLogger(debugMode)
    app.MainLoop()

