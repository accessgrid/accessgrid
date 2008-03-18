#-----------------------------------------------------------------------------
# Name:        VenueClientUI.py
# Purpose:     
#
# Author:      Susanne Lefvert, Thomas D. Uram
#
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClientUI.py,v 1.253 2007-12-20 20:43:18 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClientUI.py,v 1.253 2007-12-20 20:43:18 turam Exp $"
__docformat__ = "restructuredtext en"

import copy
import os
import os.path
from stat import ST_SIZE
import time
from wx import VERSION as WXVERSION
import wx
import string
import webbrowser
import traceback
import re
import sys
import urlparse
from twisted.internet import reactor
import threading
import urlparse

from time import localtime , strftime
from AccessGrid import Log
log = Log.GetLogger(Log.VenueClientUI)
Log.SetDefaultLevel(Log.VenueClientUI, Log.WARN)

from AccessGrid import icons
from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows, IsOSX, Config, IsLinux, IsFreeBSD
from AccessGrid.UIUtilities import AboutDialog, MessageDialog, ItemBrowserDialog
from AccessGrid.UIUtilities import ErrorDialog, BugReportCommentDialog
from AccessGrid.ClientProfile import *
from AccessGrid.Preferences import Preferences
from AccessGrid.PreferencesUI import PreferencesDialog
from AccessGrid.Descriptions import DataDescription, ServiceDescription, BridgeDescription
from AccessGrid.Descriptions import STATUS_ENABLED, STATUS_DISABLED
from AccessGrid.Descriptions import DirectoryDescription, FileDescription
from AccessGrid.Descriptions import ApplicationDescription, VenueDescription
from AccessGrid.Descriptions import NodeConfigDescription, ConnectionDescription
from AccessGrid.Security.wxgui.AuthorizationUI import AuthorizationUIDialog
from AccessGrid.Utilities import SubmitBug, BuildServiceUrl
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.AppMonitor import AppMonitor
from AccessGrid.Venue import ServiceAlreadyPresent
from AccessGrid.VenueClient import NetworkLocationNotFound, NotAuthorizedError, NoServices
from AccessGrid.VenueClient import DisconnectError, UserWarning
from AccessGrid.VenueClientController import NoAvailableBridges, NoEnabledBridges
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame, StoreConfigDialog
from AccessGrid.UIUtilities import AddURLBaseDialog, EditURLBaseDialog
from AccessGrid.Beacon.rtpBeaconUI import BeaconFrame
from AccessGrid.RssReader import RssReader,strtimeToSecs  
from AccessGrid.interfaces.Venue_client import VenueIW   
from AccessGrid import ServiceDiscovery   
from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW
from AccessGrid.Security.wxgui import CertificateManagerWXGUI
from AccessGrid.DataStore import LegacyCallInvalid, LegacyCallOnDir

from AccessGrid.Venue import CertificateRequired
try:
    import win32api
except:
    pass

    
"""

These GUI components live in this file:

Main window components
----------------------

class VenueClientUI(VenueClientObserver):
class VenueClientFrame(wx.Frame):
class VenueAddressBar(wx.SashLayoutWindow):
class VenueListPanel(wx.SashLayoutWindow):
class ContentListPanel(wx.Panel):
class TextPanelSash(wx.SashLayoutWindow):
class TextClientPanel(wx.SashLayoutWindow):
class JabberClientPanel(wx.Panel):
class StatusBar(wx.StatusBar):



Dialogs
-------

class UrlDialog(wx.Dialog):
class ProfileDialog(wx.Dialog):
class TextValidator(wx.PyValidator):
class ServicePropertiesDialog(wx.Dialog):
class ApplicationPropertiesDialog(wx.Dialog):
class ExitPropertiesDialog(wx.Dialog):
class DataPropertiesDialog(wx.Dialog):
class DataDropTarget(wx.FileDropTarget):
class SelectAppDialog(wx.Dialog):

"""



class VenueClientUI(VenueClientObserver, wx.Frame):
    """
    VenueClientUI is a wrapper for the base VenueClient.
    It updates its UI when it enters or exits a venue or
    receives a coherence event.
    """
    
    """
    The VenueClientUI is the main window of the application,
    creating statusbar, dock, venueListPanel, and contentListPanel.
    The contentListPanel represents current venue and has information
    about all participants in the venue, it also shows what data and
    services are available in the venue, as well as nodes connected to
    the venue.  It represents a room with its contents visible for the
    user.  The venueListPanel contains a list of connected
    venues/exits to current venue.  By clicking on a door icon the
    user travels to another venue/room, which contents will be shown
    in the contentListPanel.
    """
    ID_WINDOW_TOP = wx.NewId()
    ID_WINDOW_LEFT  = wx.NewId()
    ID_WINDOW_BOTTOM = wx.NewId()
    ID_WINDOW_BOTTOM2 = wx.NewId()
    ID_VENUE_DATA = wx.NewId()
    ID_VENUE_DATA_ADD = wx.NewId()
    #Added by NA2-HPCE
    #Added new Id for Directory adding event
    ID_VENUE_DIR_ADD = wx.NewId()
    ID_VENUE_DIR_UPLOAD = wx.NewId()
    
    #ZSI:HO
    ID_VENUE_DIR_SIZE = wx.NewId()
    #***************************************
    ID_VENUE_ADMINISTRATE_VENUE_ROLES = wx.NewId()
    ID_VENUE_SERVICE = wx.NewId() 
    ID_VENUE_SERVICE_ADD = wx.NewId()
    ID_VENUE_APPLICATION = wx.NewId() 
    ID_VENUE_APPLICATION_MONITOR = wx.NewId()
    ID_VENUE_SAVE_TEXT = wx.NewId()
    ID_VENUE_PROPERTIES = wx.NewId()
    ID_VENUE_OPEN_CHAT = wx.NewId()
    ID_VENUE_OPEN = wx.NewId()
    ID_VENUE_CLOSE = wx.NewId()
    ID_PROFILE = wx.NewId()
    ID_PROFILE_EDIT = wx.NewId()
    ID_CERTIFICATE_MANAGE = wx.NewId()
    ID_USE_MULTICAST = wx.NewId()
    ID_USE_UNICAST = wx.NewId()
    ID_BRIDGES = wx.NewId()
    ID_PLUGINS = wx.NewId()
    ID_CONFIGS = wx.NewId()
    ID_SAVE_CONFIG = wx.NewId()
    ID_CONFIG_BUTTON = wx.NewId()
    ID_MYNODE_MANAGE = wx.NewId()
    ID_PREFERENCES = wx.NewId()
    ID_MYVENUE_ADD = wx.NewId()
    ID_MYVENUE_EDIT = wx.NewId()
    ID_MYVENUE_GOTODEFAULT = wx.NewId()
    ID_MYVENUE_SETDEFAULT = wx.NewId()
    ID_ADD_SCHEDULE = wx.NewId()
    ID_TIMED_UPDATE = wx.NewId()
    ID_HELP = wx.NewId()
    ID_HELP_ABOUT = wx.NewId()
    ID_HELP_MANUAL = wx.NewId()
    ID_HELP_AGORG = wx.NewId()
    ID_HELP_FL = wx.NewId()
    ID_HELP_FLAG = wx.NewId()
    ID_HELP_BUG_REPORT = wx.NewId()
    ID_HELP_BUGZILLA = wx.NewId()
    
    ID_ENABLE_DISPLAY = wx.NewId()
    ID_ENABLE_VIDEO = wx.NewId()
    ID_ENABLE_AUDIO = wx.NewId()
    ID_ENABLE_MULTICAST = wx.NewId()

    ID_PARTICIPANT_PROFILE = wx.NewId()
    ID_ME_PROFILE = wx.NewId()

    TOOLSIZE = (25,25)

    def __init__(self, venueClient, controller, app, progressCallback=None):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        self.app = app
        self.bridges = None
        self.bridgeKeyMap = {}
        self.venueClient = venueClient
        self.controller = controller
        
        self.debugMode = 0
        self.browser = None
        self.myVenuesPos = 0
        
        self.textClientPanel = None
        self.myVenuesDict = {}
        self.myVenuesMenuIds = {}

        self.myConfigurationsDict = {}
        self.myConfigurationsMenuIds = {}
        
        self.onExitCalled = False
        # State kept so UI can add venue administration options.
        
        prefs = self.venueClient.GetPreferences()
        self.isAudioEnabled = int(prefs.GetPreference(Preferences.ENABLE_AUDIO))
        self.isDisplayEnabled = int(prefs.GetPreference(Preferences.ENABLE_DISPLAY))
        self.isVideoEnabled = int(prefs.GetPreference(Preferences.ENABLE_VIDEO))
        self.controller.EnableAudioCB(self.isAudioEnabled)
        try:
            self.controller.EnableDisplayCB(self.isDisplayEnabled)
        except:
            pass
        try:
            self.controller.EnableVideoCB(self.isVideoEnabled)
        except:
            pass

        self.currentConfig = None
        prefNodeConfigName = prefs.GetPreference(Preferences.NODE_CONFIG)
        for c in self.venueClient.GetNodeConfigurations():
            if c.name == prefNodeConfigName:
                self.currentConfig = c
       
        wx.Frame.__init__(self, None, -1, "")
        self.__BuildUI(app)
        self.SetSize(wx.Size(400, 600))
        
        if progressCallback:
            progressCallback('Analyzing network',100)
                
        
        # Tell the UI about installed applications
        self.__EnableAppMenu( False )
                                
        self.nodeManagementFrame = None

        # Help Doc locations
        agtkConfig = Config.AGTkConfig.instance()
        self.manual_url = "http://www.mcs.anl.gov/fl/research/accessgrid/documentation/manuals/VenueClient/3_0"
        self.agdp_url = "http://www.accessgrid.org/agdp"
        self.ag_url = "http://www.accessgrid.org/"
        self.flag_url = "http://www.mcs.anl.gov/fl/research/accessgrid"
        self.fl_url = "http://www.mcs.anl.gov/fl/"
        self.bugzilla_url = "http://bugzilla.mcs.anl.gov/accessgrid"

        reactor.interleave(wx.CallAfter,installSignalHandlers=0)

        # Make sure data can be dragged from tree to the desktop.
        #self.SetDropTarget(DesktopDropTarget(self))

        # Build RSS reader
        self.updateDuration = 1800
        rssUrlList = self._LoadFeeds()
        try:
            self.reader = RssReader(rssUrlList,self.updateDuration,[self],log=log)
            self.reader.SetUpdateDuration(self.updateDuration)
            
            # update rss feeds in thread
            t = threading.Thread(target=self.reader.Synch,name='RssReader.Synch')
            t.start()
        except:
            log.exception('Error constructing RSS reader')
            
        self.beaconFrame = None
        
        """
        # disabled for 3.1 release - turam
        self.browser = ServiceDiscovery.Browser('_servicemanager._tcp', self.BrowseCallback)
        self.browser.Start()
        """
        self.hosts = {}

        
    ############################################################################
    # Section Index
    # - Private Methods
    # - Pure UI Methods
    #
    # - Menu Callbacks
    # - Core UI Callbacks
    # - Observer Impl
    # - Manipulators
    #########################################################################
    
            
    #########################################################################
    #
    # Private Methods
    
    """
    Tools
        Host1
            Display
            Audio (need to detect audio devices first)
            Camera1
        Host2
            Display
            Audio (need to detect audio devices first)
            Camera1
            Camera2
        Save configuration
    """
    
    """
    # turam 070320 - disable for 3.1 release
    def BrowseCallback(self,op,serviceName,url=None):
        if op == ServiceDiscovery.Browser.ADD:
            wx.CallAfter(self.AddServiceManager,serviceName,url)
        elif op == ServiceDiscovery.Browser.DELETE:
            wx.CallAfter(self.RemoveServiceManager,serviceName)

    def AddServiceManager(self,serviceName,url):
        if serviceName in self.hosts.keys():
            menu = self.hosts[serviceName]
        else:
            menu = wx.Menu()
            serviceManager = AGServiceManagerIW(url)
            resources = serviceManager.GetResources()
            for r in resources:
                # Skip the vfw mapper device to avoid conflicts with
                # the real wdm device
                if r.name.startswith('Microsoft WDM Image Capture'):
                    continue
                item = menu.AppendCheckItem(wx.NewId(),r.name)
                wx.EVT_MENU(self, item.GetId(), lambda evt,
                     smurl=url, resource=r: self.AddThatService(evt, smurl, resource))
                
            menuid = wx.NewId()
            self.preferences.AppendMenu(menuid,serviceName,menu)
            self.hosts[serviceName] = menuid
                
    def RemoveServiceManager(self,serviceName):
        if serviceName in self.hosts.keys():
            self.preferences.Delete(self.hosts[serviceName])
            del self.hosts[serviceName]
            
    def AddThatService(self,event,smurl,resource):
    
        if event.IsChecked():
            p = self.venueClient.GetPreferences()

            # Add the service to the service manager
            serviceDesc = AGServiceManagerIW(smurl).AddServiceByName('VideoProducerService.zip',
                                            resource,None,p.GetProfile())
            self.venueClient.nodeService.SetServiceEnabled(serviceDesc.uri,1)

            # Add the service manager to the service
            serviceManagers = self.venueClient.nodeService.GetServiceManagers()
            found = 0
            for s in serviceManagers:
                if s.uri == smurl:
                    found = 1
                    break
            if not found:
                log.debug("Adding service manager")
                self.venueClient.nodeService.AddServiceManager(smurl)
        else:
            print 'should find service using resource %s and remove it' % (resource.name,)
    """
            
    def __ShowErrorMessage(self, jabber, type):
        if type == 'login':
            title = 'Login Error'
        elif type == 'register':
            title = 'Registration Error'
        else:
            title = 'Error'

        if jabber.errors.has_key(jabber.errorCode):
            msg = jabber.errors[jabber.errorCode]
        else:
            msg = jabber.errorCode + ": "+ jabber.errorMsg

        MessageDialog(self, msg, title, style = wx.OK|wx.ICON_ERROR)

    def __OpenProfileDialog(self):
        """
        This method opens a profile dialog, in which the user can fill in
        his or her information.
        """
        p = self.venueClient.GetPreferences()
        profileDialog = ProfileDialog(None, -1, 'Fill in your profile', 1)
        profileDialog.SetProfile(p.GetProfile())
        
        if (profileDialog.ShowModal() == wx.ID_OK):
            profile = profileDialog.GetNewProfile()
            
            # Change profile based on values filled in to the profile dialog
            self.controller.ChangeProfile(profile)
            profileDialog.Destroy()

            # Start the main wxPython thread
            self.__OpenVenueClient()

        else:
            profileDialog.Destroy()
            os._exit(0)

    def __OpenVenueClient(self):
        """
        This method is called during client startup.  It displays the
        venue client GUI.
        
        **Arguments:**
        
        *profile* The ClientProfile you want to be associated with in the venue.
        """
        
        self.venueAddressBar.SetAddress(self.venueClient.GetPreferences().GetProfile().homeVenue)
        self.Show(True)
        
    def __SetStatusbar(self):
        self.SetStatusBar(self.statusbar)
        self.statusbar.SetToolTipString("Statusbar")   
    
    #Modified by NA2-HPCE
    def __SetMenubar(self, app):

        # ---- menus for main menu bar
        self.venue = wx.Menu()
        self.venue.Append(self.ID_VENUE_OPEN,"&Open...\tCTRL-O", "Open venue")
      
        self.venue.Append(self.ID_VENUE_DATA_ADD,"Add Data...",
                             "Add data to the venue.")
        self.venue.Append(self.ID_VENUE_SERVICE_ADD,"Add Service...",
                                "Add a service to the venue.")

        self.applicationMenu = self.BuildAppMenu("")
        self.venue.AppendMenu(self.ID_VENUE_APPLICATION,"Start &Application Session",
                              self.applicationMenu)
        
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_SAVE_TEXT,"Save Text...",
                          "Save text from chat to file.")
# - Disabled for 3.0: No client-side auth support
#         self.venue.Append(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,"Administrate Roles...",
#                           "Change venue authorization settings.")
#         self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_PROPERTIES,"Properties...",
                          "View information about the venue.")
        
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE,"&Exit", "Exit venue")
        
        self.menubar.Append(self.venue, "&Venue")
              
        self.preferences = wx.Menu()


        # Add node-related entries
        self.preferences.AppendRadioItem(self.ID_USE_MULTICAST, "Use Multicast",
                                         "Use multicast to connect media")
        self.preferences.AppendRadioItem(self.ID_USE_UNICAST, "Use Unicast",
                                         "Use unicast to connect media")
     
        transport = self.venueClient.GetTransport()
        index = True
        if transport == "unicast":
            index = False

        self.preferences.Check(self.ID_USE_MULTICAST, index)
        self.preferences.Check(self.ID_USE_UNICAST, not index)
        self.bridgeSubmenu = wx.Menu()
        
        self.configSubmenu = wx.Menu()

        # Create bridge menu, so individual bridges are selectable from the start
        self.__CreateBridgeMenu()
                       
        self.preferences.AppendMenu(self.ID_BRIDGES, "Bridges", self.bridgeSubmenu)
        self.preferences.AppendSeparator()
        
        # Configurations Submenu
        self.preferences.AppendMenu(self.ID_CONFIGS, "Configurations", self.configSubmenu)
        self.preferences.Append(self.ID_SAVE_CONFIG, "Save Configuration...", 
                                "Save current configuration")
        self.preferences.AppendSeparator()
        
	# Append plugin menu, only if plugins exist
        self.pluginMenu = self.BuildPluginMenu()
        if self.pluginMenu:
            self.preferences.AppendMenu(wx.NewId(), "&Plugins", self.pluginMenu)
            self.preferences.AppendSeparator()


        # - enable display/video/audio
        self.preferences.AppendCheckItem(self.ID_ENABLE_AUDIO, "Enable Audio",
                                         "Enable/disable audio for your node")
        audioFlag = self.venueClient.GetPreferences().GetPreference(Preferences.ENABLE_AUDIO)
        self.preferences.Check(self.ID_ENABLE_AUDIO, int(audioFlag))
        
        self.preferences.AppendCheckItem(self.ID_ENABLE_DISPLAY, "Enable Video Display",
                                         "Enable/disable video display for your node")
        displayFlag = self.venueClient.GetPreferences().GetPreference(Preferences.ENABLE_DISPLAY)
        self.preferences.Check(self.ID_ENABLE_DISPLAY, int(displayFlag))
        
        
        self.preferences.AppendCheckItem(self.ID_ENABLE_VIDEO, "Enable Video Capture",
                                         "Enable/disable video for your node")
        videoFlag = self.venueClient.GetPreferences().GetPreference(Preferences.ENABLE_VIDEO)
        self.preferences.Check(self.ID_ENABLE_VIDEO, int(videoFlag))
        
        self.preferences.Append(self.ID_MYNODE_MANAGE, "&Configure node services...",
                                "Configure node services for audio, video, ...")
        self.preferences.AppendSeparator()
        
        #
        # Retrieve the cert mgr GUI from the application.
        #
        self.cmui = None
        try:
            mgr = app.GetCertificateManager()
        except Exception,e:
            log.exception("VenueClientFrame.__SetMenubar: Cannot retrieve \
                           certificate mgr user interface, continuing")

        self.cmui = CertificateManagerWXGUI.CertificateManagerWXGUI(mgr)
        self.cmui.SetCertificateManager(mgr)
        certMenu = self.cmui.GetMenu(self)
        for item in certMenu.GetMenuItems():
            self.preferences.AppendItem(item)
        
        self.preferences.Append(self.ID_PREFERENCES, "&Preferences...")
        if IsOSX():
            self.preferences.Append(wx.ID_PREFERENCES, "&Preferences...")
        self.menubar.Append(self.preferences, "&Tools")
        
        self.navigation = wx.Menu()
        self.navigation.Append(self.ID_MYVENUE_GOTODEFAULT, "Go to Home Venue",
                             "Go to default venue")
        self.navigation.Append(self.ID_MYVENUE_SETDEFAULT, "Set as Home Venue",
                             "Set current venue as default")
        
        self.navigation.AppendSeparator()
        self.navigation.Append(self.ID_MYVENUE_ADD, "Add Venue...",
                             "Add this venue to your list of venues")
        self.navigation.Append(self.ID_MYVENUE_EDIT, "Manage My &Venues...",
                             "Edit your venues")
        self.navigation.AppendSeparator()
        self.myVenuesPos = self.navigation.GetMenuItemCount()-1
        
        self.navigation.Append(self.ID_ADD_SCHEDULE, "Add Schedule...",
                             "Subscribe to a published meeting schedule")
        self.navigation.AppendCheckItem(self.ID_TIMED_UPDATE, "Timed Update",
                             "Update subscribed schedules periodically")
        self.navigation.Check(self.ID_TIMED_UPDATE,1) # timed update on by default

        self.menubar.Append(self.navigation, "&Navigation")

        self.help = wx.Menu()
        self.help.Append(self.ID_HELP_MANUAL, "Venue Client &Manual",
                         "Venue Client Manual")
        self.help.AppendSeparator()
        self.help.Append(self.ID_HELP_AGORG, "Access &Grid (accessgrid.org) Web Site",
                         "")
        self.help.Append(self.ID_HELP_FLAG, "Access Grid &Toolkit Web Site",
                         "")
        self.help.Append(self.ID_HELP_FL, "&Futures Laboratory Web Site",
                         "")

        self.help.AppendSeparator()
        self.help.Append(self.ID_HELP_BUG_REPORT, 
                         "&Submit Error Report or Feature Request",
                         "Send report to bugzilla")

        self.help.Append(self.ID_HELP_BUGZILLA, 
                         "&Bugzilla Web Site",
                         "See current error reports and feature request")

        self.help.AppendSeparator()
         
        self.help.Append(self.ID_HELP_ABOUT, "&About",
                         "Information about the application")
        self.menubar.Append(self.help, "&Help")
       
        # ---- Menus for items
        self.meMenu = wx.Menu()
       
        self.meMenu.Append(self.ID_ME_PROFILE,"View Profile...",\
                                           "View participant's profile information")
       
            
        self.participantMenu = wx.Menu()
        self.participantMenu.Append(self.ID_PARTICIPANT_PROFILE,"View Profile...",\
                                           "View participant's profile information")
        # ---- Menus for headings
        self.dataHeadingMenu = wx.Menu()
        self.dataHeadingMenu.Append(self.ID_VENUE_DATA_ADD,"Add...",
                                   "Add data to the venue")

                           



        #Added by NA2-HPCE
        self.dataHeadingMenu.Append(self.ID_VENUE_DIR_ADD,"Add directory...",
                                    "Add directory into file storage")
        self.dataHeadingMenu.Append(self.ID_VENUE_DIR_UPLOAD,"Upload a directory...",
                                    "Upload a complete directory into file storage")

        #ZSI:HO
        #self.dataHeadingMenu.Append(self.ID_VENUE_DIR_SIZE,"Get data storage size",
        #                            "retrieves the data storage size")  
        #self.dataHeadingMenu.Enable(self.ID_VENUE_DIR_SIZE, True) #Not yet implemented, therefore greyed out
        
        
        self.dataHeadingMenu.Enable(self.ID_VENUE_DIR_UPLOAD, False) #Not yet implemented, therefore greyed out
        self.serviceHeadingMenu = wx.Menu()
        self.serviceHeadingMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...",
                                "Add service to the venue")
        # Do not enable menus until connected
        self.__HideMenu()
        self.SetMenuBar(self.menubar)

    def __CreateBridgeMenu(self):
        
        self.bridges = self.venueClient.GetBridges()
        self.currentBridge = self.venueClient.GetCurrentBridge()
        items = self.bridgeSubmenu.GetMenuItems()
       
        for i in items:
            self.bridgeSubmenu.DeleteItem(i)

        bList = self.bridges.values()
        
        if not bList:
            id = wx.NewId()
            self.bridgeSubmenu.Append(id,'No bridges available')
            self.bridgeSubmenu.Enable(id, False)
            return

        # sort the bridge list
        orderBridgesByPing = self.venueClient.preferences.GetPreference(Preferences.ORDER_BRIDGES_BY_PING)
        bList.sort(lambda x,y: BridgeDescription.sort(x, y, orderBridgesByPing))

        for b in bList:
            # do not display disabled bridges in the menu
            if b.status == STATUS_DISABLED:
                continue
            id = wx.NewId()
            self.bridgeSubmenu.AppendCheckItem(id, b.name)
            self.bridgeKeyMap[b.GetKey()] = id

            if (self.currentBridge and b.GetKey() == self.currentBridge.GetKey()
                and self.venueClient.GetTransport()=="unicast"):
                self.bridgeSubmenu.Check(id, 1)
                
            wx.EVT_MENU(self, id, lambda evt,
                     menuid=id, bridgeDesc=b: self.CheckBridgeCB(evt, menuid, bridgeDesc))

        if len(self.bridges.values())<1:
            self.Warn("No unicast bridge is currently available.", "Use Unicast")
           
                
    def CheckBridgeCB(self, event, menuid, bridgeDescription):
      

        # Uncheck all items except the checked one
        items = self.bridgeSubmenu.GetMenuItems()

        # If selecting the already selected bridge, ignore
        for i in items:
            if i.GetId() == menuid and i.GetKind() == wx.ITEM_CHECK and not self.menubar.IsChecked(menuid):
                self.bridgeSubmenu.Check(menuid, 1)
                return

        # Use current bridge
        try:
            # - use that bridge
            self.controller.UseBridgeCB(bridgeDescription)

            # - uncheck multicast item
            self.preferences.Check( self.ID_USE_UNICAST, 1)

            # - check the selected bridge item
            for i in items:
                if i.GetId() != menuid:
                    if i.GetKind() == wx.ITEM_CHECK:
                        self.bridgeSubmenu.Check(i.GetId(), 0)
        
        except:
            log.exception("Connection to bridge %s failed"%(bridgeDescription.name))
            self.bridgeSubmenu.Check(menuid, 0)
            self.Notify("Connection to bridge %s failed. \nPlease use a different bridge."%(bridgeDescription.name),
                        "Bridge Connection")
                        
    def __SetEvents(self):
    
        # Venue Menu
        wx.EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.AddDataCB)
        #Added by NA2-HPCE
        wx.EVT_MENU(self, self.ID_VENUE_DIR_ADD, self.AddDirCB)
        wx.EVT_MENU(self, self.ID_VENUE_DIR_UPLOAD, self.UploadDirCB)
        
        #ZSI:HO
        #wx.EVT_MENU(self, self.ID_VENUE_DIR_SIZE, self.GetSizeCB)
        #*********************************************************
        wx.EVT_MENU(self, self.ID_VENUE_OPEN, self.OpenVenueCB)
        wx.EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.AddServiceCB)
        wx.EVT_MENU(self, self.ID_VENUE_SAVE_TEXT, self.SaveTextCB)
        wx.EVT_MENU(self, self.ID_VENUE_PROPERTIES, self.OpenVenuePropertiesCB)
        wx.EVT_MENU(self, self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,
                 self.ModifyVenueRolesCB)
        wx.EVT_MENU(self, self.ID_VENUE_CLOSE, self.ExitCB)
        if IsOSX():
            wx.EVT_MENU(self, wx.ID_EXIT, self.ExitCB)
        
        # Preferences Menu
        wx.EVT_MENU(self, self.ID_USE_MULTICAST, self.UseMulticastCB)
        wx.EVT_MENU(self, self.ID_USE_UNICAST, self.UseUnicastCB)
        wx.EVT_MENU(self, self.ID_ENABLE_DISPLAY, self.EnableDisplayCB)
        wx.EVT_MENU(self, self.ID_ENABLE_VIDEO, self.EnableVideoCB)
        wx.EVT_MENU(self, self.ID_ENABLE_AUDIO, self.EnableAudioCB)

        wx.EVT_MENU(self, self.ID_SAVE_CONFIG, self.SaveConfigurationCB)
        
        wx.EVT_MENU(self, self.ID_MYNODE_MANAGE, self.ManageNodeCB)
        wx.EVT_MENU(self, self.ID_PREFERENCES, self.PreferencesCB)
        if IsOSX():
            wx.EVT_MENU(self, wx.ID_PREFERENCES, self.PreferencesCB)
        
        # Navigation Menu
        wx.EVT_MENU(self, self.ID_MYVENUE_GOTODEFAULT, self.GoToDefaultVenueCB)
        wx.EVT_MENU(self, self.ID_MYVENUE_SETDEFAULT, self.SetAsDefaultVenueCB)
        wx.EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenuesCB)
        wx.EVT_MENU(self, self.ID_MYVENUE_EDIT, self.EditMyVenuesCB)
        wx.EVT_MENU(self, self.ID_ADD_SCHEDULE, self.AddScheduleCB)
        wx.EVT_MENU(self, self.ID_TIMED_UPDATE, self.TimedUpdateCB)
        
        # Help Menu
        wx.EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialogCB)
        wx.EVT_MENU(self, self.ID_HELP_MANUAL,self.OpenManualCB)
        wx.EVT_MENU(self, self.ID_HELP_AGORG,self.OpenAGOrgCB)
        wx.EVT_MENU(self, self.ID_HELP_FLAG, self.OpenFLAGCB)
        wx.EVT_MENU(self, self.ID_HELP_FL,self.OpenFLCB)
        wx.EVT_MENU(self, self.ID_HELP_BUG_REPORT, self.SubmitBugCB)
        wx.EVT_MENU(self, self.ID_HELP_BUGZILLA,self.OpenBugzillaCB)

        # Popup Menu Events
        wx.EVT_MENU(self, self.ID_ME_PROFILE, self.EditProfileCB)
        wx.EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.ViewProfileCB)

        # UI Events
        wx.EVT_CLOSE(self, self.ExitCB)
        
        wx.EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.__OnSashDrag)
        wx.EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.__OnSashDrag)
        wx.EVT_SIZE(self, self.__OnSize)
        
        wx.EVT_BUTTON(self,self.networkButton.GetId(),self.OnMulticast)
        wx.EVT_BUTTON(self,self.venueBackButton.GetId(),self.GoBackCB)
        wx.EVT_BUTTON(self,self.venueHomeButton.GetId(),self.GoToDefaultVenueCB)
        wx.EVT_BUTTON(self,self.audioButton.GetId(),self.EnableAudioCB)
        wx.EVT_BUTTON(self,self.displayButton.GetId(),self.EnableDisplayCB)
        wx.EVT_BUTTON(self,self.videoButton.GetId(),self.EnableVideoCB)
        wx.EVT_BUTTON(self,self.configNodeButton.GetId(),self.ManageNodeCB)
        
        buttons = [ self.networkButton, self.audioButton, self.videoButton, 
                    self.displayButton, self.configNodeButton ]
        for button in buttons:
            wx.EVT_ENTER_WINDOW(button,self.OnButtonFocusChange)
            wx.EVT_LEAVE_WINDOW(button,self.OnButtonFocusChange)

    def OnButtonFocusChange(self,event):
        # make sure button gets highlighted when it has focus
        event.Skip()
        
        # clear status text when leaving button
        if isinstance(event,wx.MouseEvent) and event.Leaving():
            self.SetStatusText('')
            return
        
        # set status text otherwise
        statusText = None
        button = event.GetEventObject()
        if button == self.networkButton:
            statusText = "View multicast connectivity"
        elif button == self.audioButton:
            statusText = "Enable/disable audio"
        elif button == self.videoButton:
            statusText = "Enable/disable video"
        elif button == self.displayButton:
            statusText = "Enable/disable display"
        elif button == self.configNodeButton:
            statusText = "Configure node services"
        if statusText:
            if IsWindows():
                self.SetStatusTextDelayed(statusText,0.1)
            else:
                self.SetStatusText(statusText)

    def OnMulticast(self, event):

        pref = self.venueClient.GetPreferences()
        if not self.venueClient.IsInVenue():
             self.Notify("You must be connected to a venue to see\nmulticast connectivity to other participants.", "Show Multicast Connectivity")
        elif not int(pref.GetPreference(Preferences.BEACON)):
            self.Notify("You have beacon set to disabled.\nYou can enable it in the network panel in your preferences.", "Show Multicast Connectivity")
        else:
            if self.beaconFrame:
                self.beaconFrame.Raise()
            else:
                beacon = self.venueClient.GetBeacon()
                # If beacon is not running, can't show beacon view; inform user
                if not beacon:
                    messageDialog = wx.MessageDialog(self, "Beacon statistics not available",
                                                    "Alert",
                                                    style = wx.OK|wx.ICON_INFORMATION)
                    messageDialog.ShowModal()
                    messageDialog.Destroy()

                    self.OnExit()
                    return
                
                parent_pos = self.GetPosition()
                parent_siz = self.GetSize()
                pos = ( parent_pos[0] + parent_siz[0] / 2, parent_pos[1] + parent_siz[1] / 2)
                self.beaconFrame = BeaconFrame(self, log, beacon, pos=pos)
                self.beaconFrame.Show(True)
        
    def __SetProperties(self):
        self.SetTitle("Venue Client")
        #self.venueListPanel.SetSize(wx.Size(160, 300))
        #self.venueAddressBar.SetSize(wx.Size(self.GetSize().GetWidth(),65))
        
    def __FillTempHelp(self, x):
        if x == '\\':
            x = '/'
        return x

    def __LoadMyVenues(self):
    
        # Delete existing menu items
        for ID in self.myVenuesMenuIds.values():
            self.navigation.Delete(ID)
        
        self.myVenuesMenuIds = {}
        self.myVenuesDict = self.controller.GetMyVenues()
                   
        # Create menu items
        for name in self.myVenuesDict.keys():
            ID = wx.NewId()
            self.myVenuesMenuIds[name] = ID
            url = self.myVenuesDict[name]
            text = "Go to: " + url
            self.navigation.Insert(self.myVenuesPos,ID, name, text)
            wx.EVT_MENU(self, ID, self.GoToMenuAddressCB)
                        
    
    # Code for displaying the list of configurations in the Configurations menu
    
    def __LoadMyConfigurations(self):

        # Remove all the config menu items
        items = self.configSubmenu.GetMenuItems()
        map(lambda item: self.configSubmenu.Delete(item.GetId()), items)

        # Work around wx assertion (bug) that occurs when rebuilding
        # menus that contain only radio items (would be better to work
        # around it only when it occurs, but GTK prints to the console
        # when the problem occurs)
        try:
            itemId = wx.NewId()
            self.configSubmenu.Append(itemId,"")
            self.configSubmenu.Delete(itemId)
        except:
            pass

        # Build up the list of menu items 
        configs = self.venueClient.GetNodeConfigurations()
        for configuration in configs:
            ID = wx.NewId()
            configName = configuration.name
            self.configSubmenu.AppendRadioItem(ID, configName)
            self.myConfigurationsMenuIds[ID] = configName
            self.myConfigurationsDict[configName] = configuration
            wx.EVT_MENU(self, ID, self.LoadNodeConfig)

            if (None != configuration) and (None != self.currentConfig):
                if configuration.name == self.currentConfig.name:
                    self.configSubmenu.Check(ID,1)
        
    def __BuildUI(self, app):
        self.Centre()
        self.menubar = wx.MenuBar()
        self.statusbar = StatusBar(self)
        
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, 
                                               self.myVenuesDict,
                                               'default venue')
        self.venueAddressBar.SetDefaultSize((1000, 35))
        self.venueAddressBar.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.venueAddressBar.SetAlignment(wx.LAYOUT_TOP)
        self.venueAddressBar.SetSashVisible(wx.SASH_BOTTOM, True)

        self.textClientPanel = TextPanelSash(self, self.ID_WINDOW_BOTTOM)
        self.textClientPanel.SetDefaultSize((1000, 200))
        self.textClientPanel.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.textClientPanel.SetAlignment(wx.LAYOUT_BOTTOM)
        self.textClientPanel.SetSashVisible(wx.SASH_TOP, True)

        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT,
                                             self)
        self.venueListPanel.SetDefaultSize((170, 1000))
        self.venueListPanel.SetOrientation(wx.LAYOUT_VERTICAL)
        self.venueListPanel.SetAlignment(wx.LAYOUT_LEFT)
        self.venueListPanel.SetSashVisible(wx.SASH_RIGHT, True)

        self.contentListPanel = ContentListPanel(self)
        dataDropTarget = DataDropTarget(self)
        self.contentListPanel.SetDropTarget(dataDropTarget)

        # create toolbar
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolPacking(3)
        
        bitmap = icons.getNoMulticastBitmap()
        self.networkButton = wx.BitmapButton(self.toolbar,-1,bitmap,size=VenueClientUI.TOOLSIZE)
        self.networkButton.SetToolTip(wx.ToolTip('View multicast connectivity'))
        self.toolbar.AddControl(self.networkButton)
        self.toolbar.AddSeparator()
        
        # - create the venueback toolbar button
        self.venueBackButton = wx.BitmapButton(self.toolbar,-1,icons.getPreviousBitmap(),size=VenueClientUI.TOOLSIZE)
        self.venueBackButton.SetToolTip(wx.ToolTip('Previous Venue'))
        self.toolbar.AddControl(self.venueBackButton)
        
        # - create the venuehome toolbar button
        self.venueHomeButton = wx.BitmapButton(self.toolbar,-1,icons.getHomeBitmap(),size=VenueClientUI.TOOLSIZE)
        self.venueHomeButton.SetToolTip(wx.ToolTip('Home Venue'))
        self.toolbar.AddControl(self.venueHomeButton)

        self.toolbar.AddSeparator()
        
        # - create the audio toolbar button  
        if self.isAudioEnabled:
            bitmap = icons.getAudioBitmap()
        else:
            bitmap = icons.getAudioDisabledBitmap()
        self.audioButton = wx.BitmapButton(self.toolbar,-1,bitmap,size=VenueClientUI.TOOLSIZE)
        self.audioButton.SetToolTip(wx.ToolTip('Enable/disable audio'))
        self.toolbar.AddControl(self.audioButton)

        # - create the display toolbar button         
        if self.isDisplayEnabled:
            bitmap = icons.getDisplayBitmap()
        else:
            bitmap = icons.getDisplayDisabledBitmap()
        self.displayButton = wx.BitmapButton(self.toolbar,-1,bitmap,size=VenueClientUI.TOOLSIZE)
        self.displayButton.SetToolTip(wx.ToolTip('Enable/disable display'))
        self.toolbar.AddControl(self.displayButton)

        # - create the video toolbar button         
        if self.isVideoEnabled:
            bitmap = icons.getCameraBitmap()
        else:
            bitmap = icons.getCameraDisabledBitmap()
        self.videoButton = wx.BitmapButton(self.toolbar,-1,bitmap,size=VenueClientUI.TOOLSIZE)
        self.videoButton.SetToolTip(wx.ToolTip('Enable/disable video'))
        self.toolbar.AddControl(self.videoButton)

        bitmap = icons.getConfigureBitmap()
        self.configNodeButton = wx.BitmapButton(self.toolbar,-1,bitmap,size=VenueClientUI.TOOLSIZE)
        self.configNodeButton.SetToolTip(wx.ToolTip('Configure node services'))
        self.toolbar.AddControl(self.configNodeButton)

        self.toolbar.Realize()
        
        self.__SetStatusbar()
        self.__SetMenubar(app)
        self.__SetProperties()
        self.__SetEvents()
        self.__LoadMyVenues()
        self.__LoadMyConfigurations()

    def __OnSashDrag(self, event):
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            return

        eID = event.GetId()
              
        if eID == self.ID_WINDOW_LEFT:
            self.venueListPanel.Show()
            width = event.GetDragRect().width
            minWidth = 10
            if width < 60:
                width = minWidth
                self.venueListPanel.Hide()
            elif width > (self.GetSize().GetWidth() - minWidth):
                width = self.GetSize().GetWidth() - minWidth
           
            self.venueListPanel.SetDefaultSize(wx.Size(width, 1000))

        elif eID == self.ID_WINDOW_TOP:
            height = event.GetDragRect().height
            self.venueAddressBar.SetDefaultSize(wx.Size(1000, height))
        
        elif eID == self.ID_WINDOW_BOTTOM:
            height = event.GetDragRect().height

            # Avoid covering text area
            if height < 50:
                height = 50
            self.textClientPanel.SetDefaultSize(wx.Size(1000, height))

        wx.LayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
        self.contentListPanel.Refresh()
                         
    def __OnSize(self, event = None):
        wx.LayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
        
    def __CleanUp(self):
        #self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

    def __HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, False)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, False)
        self.menubar.Enable(self.ID_VENUE_PROPERTIES, False)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, False)
        self.menubar.Enable(self.ID_VENUE_APPLICATION, False)
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, False)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, False)
                
    def __ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, True)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, True)
        self.menubar.Enable(self.ID_VENUE_PROPERTIES, True)
        self.menubar.Enable(self.ID_MYVENUE_ADD, True)
        self.menubar.Enable(self.ID_MYVENUE_GOTODEFAULT, True)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, True)
        self.menubar.Enable(self.ID_VENUE_APPLICATION, True)
                
        # Only show administrate button when you can administrate a venue.
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, True)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, True)

    def __EnableAppMenu(self, flag):
        for entry in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Enable( entry.GetId(), flag )

    def __Notify(self,text,title):
        dlg = wx.MessageDialog(self, text, title, 
                              style = wx.ICON_INFORMATION | wx.OK)
        ret = dlg.ShowModal()
    
    def __Warn(self,text,title):
        dlg = wx.MessageDialog(self, text, title, style = wx.ICON_WARNING | wx.OK)
        ret = dlg.ShowModal()

    def __OpenApplication(self, appCmdDesc):
        '''
        This method is called when someone wants to invite you to join a shared
        application session.
        '''
        log.debug('In VenueClientUI.__OpenApplication')
        
        if self.venueClient.GetPreferences().GetProfile().GetPublicId() == appCmdDesc.profile.GetPublicId():
            # I wanted to open the application client so don't pop up a message dialog.
            log.debug('Received my own invitation to join application, joining...')
            ret = wx.ID_OK
        else:
            log.debug('Received invitation to join application, prompting...')
            # Ask everyone else if they want to open the application client.
            text = '%s would like to invite you to a shared application session (%s). Do you wish to join?'%(appCmdDesc.profile.name, appCmdDesc.appDesc.name)
            dlg = wx.MessageDialog(self, text, 'Join Shared Application Session', style = wx.OK|wx.CANCEL)
            ret = dlg.ShowModal()

        # Open the client
        if ret == wx.ID_OK:
            log.debug('Joining shared application')
            self.controller.StartCmd(appCmdDesc.appDesc, appCmdDesc.verb, appCmdDesc.command)
                    
        
    # end Private Methods
    #
    ##########################################################################


    ##########################################################################
    #
    # Pure UI Methods
            
    def UpdateLayout(self, panel, size):
        panel.SetDefaultSize(size)
        wx.LayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

    # end Pure UI Methods
    #
    ############################################################################

    ############################################################################
    #
    # Menu Callbacks

    #
    # Venue Menu
    #
    
    #ZSI:HO
    def GetSizeCB(self, event=None):
        size = self.__venueProxy.GetDataSize() 
        message = "Size of data store in KB: " + str(size)
        log.debug(message)
        wx.MessageBox(message, "Size of data store", wx.OK);
    

    #Added by NA2-HPCE
    def AddDirCB(self, event = None, dirList =[]):
        
        #Retrieve selected data description element
        dirDesc = self.contentListPanel.selectedTreeItem
        dirDescName = self.contentListPanel.selectedTreeItemText
        
        noServerDir = True
        
        #self.__venueProxy.HDDump()

        name = None
        desc = None
        dirList =[]
        
        dlgDirName = wx.TextEntryDialog(self, "Enter the name of the directory to create","Create Directory", "", wx.OK | wx.CANCEL)
        retVal = dlgDirName.ShowModal()
        if retVal == wx.ID_OK:
            name = dlgDirName.GetValue()
            desc = name + " is a directory"
            
            dirList.append(name)            
            
                    
                
            #retrieve data descriptions datacontainer
            if (dirDesc == None):
                #We are at the top level nothing above, so we add
                #the directory to the initial dataDescCont of the
                #DataStore
                try:
                    self.__venueProxy.AddDir(name, desc, 1, 0) 
                    noServerDir = False
                except:
                    noServerDir =True
    
            else:
                if dirDesc.IsOfType(DataDescription.TYPE_DIR):
                    #Add DirectoryDescription to container of selected Description
                    #Set Properties of Description
                    #Add dialog here
                    try:
                        log.debug("AddDir in %s",dirDesc.GetName())
                        self.__venueProxy.AddDir(name, desc, dirDesc.GetLevel()+1, dirDesc.GetId()) 
                        noServerDir = False
                    except:
                        noServerDir = True
                    
                else:
                    #This case should never happen
                    log.error("Selected a directory, but appears as a file internally!")
                
            if noServerDir:
                self.Notify("Creation of directories is not supported on server-side", "No directory service available!")
        else:
            #Name entry has been canceled
            pass
        
        return
    
    """
    Added by NA2-HPCE
    """
    def RecursiveDataAdd(self, parent, localPath, level):

        # This method uploads the specified file/directory to the specified parent
        
        filesToAdd = []
        destinationDirectory = None
        # ** Prepare list of files to upload
        
        # if localPath is a file
        if os.path.isfile(localPath):
            # upload to given parent directory
            filesToAdd.append(localPath)

            
        # if localPath is a directory
        elif os.path.isdir(localPath):
            # create the directory on the server
            dirname = os.path.split(localPath)[1]
            if parent == None:
                locDirectoryDescription=self.__venueProxy.AddDir(dirname, "",1,0)
                time.sleep(2)
            else:
                locDirectoryDescription=self.__venueProxy.AddDir(dirname,"",parent.GetLevel()+1,parent.GetId())
                time.sleep(2)  
                
            # upload files in this directory
            fileList = os.listdir(localPath)      
            for f in fileList:    
                path = os.path.join(localPath,f)
                self.RecursiveDataAdd(locDirectoryDescription, path, level + 1)                       

        
        # upload files, if any
        if filesToAdd:
            if parent == None:
                # add to root
                serverPath = ""
            else:
                #add to given directory in data store
                serverPath = parent.GetURI()
    
            self.AddDataCB(None, filesToAdd, serverPath)            

    
    #Added by NA2-HPCE    
    def DecideDragDropType(self, x, y, fileList):
        item  = None
        treeId, flag = self.contentListPanel.tree.HitTest(wx.Point(x, y))
                      
        if(treeId.IsOk()):
            item = self.contentListPanel.tree.GetItemData(treeId).GetData()

        
        # if the drop point was a directory, upload to that directory
        isDirectoryTarget = (item and item.GetObjectType() == DataDescription.TYPE_DIR)

        for entry in fileList:
            if isDirectoryTarget:
                self.RecursiveDataAdd(item,entry,item.GetLevel())
            else:
                self.RecursiveDataAdd(None,entry,1)    

    """
    Added by NA2-HPCE    
    Yet unused code
    Needs to be redone for AG3
    """
    def UploadDirCB(self, event = None, dirList =[]):
        #contains nothing so far and does nothing so far

        #Retrieve selected data description element
        dirDesc = self.contentListPanel.selectedTreeItem
        dirDescName = self.contentListPanel.selectedTreeItemText
        
        
        noServerDir = True

        name = None
        desc = None
        
        dlgLoadDir = wx.DirDialog(self,"Choose a directory to upload!")
        if (dlgLoadDir.ShowModal() == wx.ID_OK):
            strDirToUpload = dlgLoadDir.GetPath()
        else:
            return
        
        if not dirDesc == None:
            self.RecursiveDataAdd(dirDesc,strDirToUpload,dirDesc.GetLevel()+1)
        else:
            self.RecursiveDataAdd(dirDesc,strDirToUpload,1)
    
    

    def OpenVenueCB(self,event):
        venueCache = self.venueClient.venueCache
        venueList = []
        for v in venueCache.GetVenues():
            venueList += v.venueList
        
        # - main frame
        dialog = ItemBrowserDialog(self,-1,'Open Venue',venueList,size=(400,500))
        dialog.CenterOnParent()
        ret = dialog.ShowModal()
        if ret == wx.ID_OK:
            ret = dialog.GetValue()
            if ret:
                self.SetVenueUrl(ret.uri)
                self.EnterVenueCB(ret.uri)

        
        
    def AddDataCB(self, event = None, fileList = [], serverPath=None):
    
        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #
        log.debug("In VenueClientController.AddDataCB")
        
        dirDesc = self.contentListPanel.selectedTreeItem
        dirDescName = self.contentListPanel.selectedTreeItemText

        uploadUrl = self.venueClient.GetDataStoreUploadUrl()
        log.debug("VenueClientUI.AddDataCB: Trying to upload to '%s'" % (uploadUrl))
        if uploadUrl is None or uploadUrl == "":
        
            self.Notify("Cannot add data: Venue does not have an operational\ndata storage server.",
                        "Cannot upload")
            return
        
        #
        # Prompt for files to upload if not given
        #
        
        if not fileList:
            dlg = wx.FileDialog(self, "Choose file(s):",
                               style = wx.OPEN | wx.MULTIPLE)
            if dlg.ShowModal() == wx.ID_OK:
                fileList = dlg.GetPaths()

                for f in fileList:
                    try:
                        unicode(f)
                    except:
                        fileList = []
                        MessageDialog(self, \
                                      'File %s includes foreign characters. \nPlease rename before uploading.'%f,
                                      'Upload File')

            dlg.Destroy()

        uploadRoot = self.venueClient.GetDataStoreUploadUrl()

        #
        # Check if data exists, and prompt to replace
        #
        if fileList:
            # Check file size
            # Hard coded for now - later query server
            MAX_UPLOAD_SIZE = 2147400000
            for filepath in fileList:
                size = os.stat(filepath)[ST_SIZE]
                if size > MAX_UPLOAD_SIZE:
                    MessageDialog(self, \
                        'File %s is too big to upload\n (%d > %d)'% \
                        (os.path.split(filepath)[-1],size,MAX_UPLOAD_SIZE), \
                        'File size warning!')
                    fileList.remove(filepath)
            filesToAdd = []
            dataDescriptions = self.venueClient.GetVenueData()
            for filepath in fileList:
                pathParts = os.path.split(filepath)
                name = pathParts[-1]

                fileExists = 0
                if serverPath:
                    pathToMatch = os.path.join(uploadRoot,serverPath,name)
                else:
                    pathToMatch = os.path.join(uploadRoot,name)
                matchingFiles = filter( lambda x: x.GetURI() == pathToMatch, dataDescriptions)
                if matchingFiles:
                    data = matchingFiles[0]
                    title = "Duplicated File"
                    info = "A file named %s already exists, do you want to overwrite?" % name
                    if self.Prompt(info,title):
                        try:
                            
                            self.controller.RemoveDataCB(data)
                            filesToAdd.append(filepath)
                        except:
                            log.exception("Error overwriting file %s", data)
                            self.Error("Can't overwrite file","Replace Data Error")
                    break

                        
                else:
                    # File does not exist; add the file
                    filesToAdd.append(filepath)

            #
            # Upload the files, the server directory which is the last parameter is for now
            # empty until the mechanisms are available to determine the server directory
            # where the file should be added.
            #
            if serverPath == None:
                if dirDesc == None:
                    serverPath=""
                else:
                    serverPath = dirDesc.GetURI()
                
            log.debug("AddDataCB: URI of parent is %s", serverPath)
            
            try:
                if len(filesToAdd) != 0:
                    self.controller.AddDataCB(filesToAdd, serverPath) #empty server directory
            except:
                log.exception("Error adding data")
                self.Error("The data could not be added", "Add Data Error")
                
    
  

    def AddServiceCB(self, event):
        addServiceDialog = ServicePropertiesDialog(self, -1,
                                         'Add Service')
        if (addServiceDialog.ShowModal() == wx.ID_OK):

            try:
                serviceDescription = addServiceDialog.GetDescription()
                log.debug("Adding service: %s to venue" %serviceDescription.name)
                self.controller.AddServiceCB(serviceDescription)
            except ServiceAlreadyPresent:
                self.Error("A service by that name already exists", "Add Service Error")
            except:
                log.exception("Error adding service")
                self.Error("The service could not be added", "Add Service Error")

        addServiceDialog.Destroy()


    def SaveTextCB(self, event):
        """
        Saves text from text chat to file.
        """
        wildcard = "Text Files |*.txt|" \
                   "All Files |*.*"
        filePath = self.SelectFile("Choose a file:", wildcard = wildcard)
        text = self.GetText()
        if filePath:
            try:
                self.controller.SaveTextCB(filePath,text)
            except:
                log.exception("VenueClientFrame.SaveText: Can not save text.")
                self.Error("Text could not be saved.", "Save Text")


    def OpenVenuePropertiesCB(self, event):
        """
        Displays venue properties dialog.
        """
        venuePropertiesDialog = VenuePropertiesDialog(self, -1,
                                                      'Venue Properties', self.venueClient)
        #venuePropertiesDialog.PopulateList(streams)
        venuePropertiesDialog.ShowModal()
       
    def ModifyAppRolesCB(self, event):
        appUrl = event.uri
                
        # Open the dialog
        f = AuthorizationUIDialog(None, -1, "Manage Roles", log)
        f.ConnectToAuthManager(appUrl)
        if f.ShowModal() == wx.ID_OK:
            f.panel.Apply()
        f.Destroy()

        
    def ModifyVenueRolesCB(self,event):
        venueUri = self.venueClient.GetVenue()

        # Check if I am a venue administrator before
        # opening the dialog
        adminFlag = self.venueClient.IsVenueAdministrator()

        if not adminFlag:
            self.Notify("Only venue administrators are allowed to modify roles. ", "Modify Roles")
            return
        
        # Open the dialog
        f = AuthorizationUIDialog(None, -1, "Manage Roles", log)
        f.ConnectToAuthManager(venueUri)
        if f.ShowModal() == wx.ID_OK:
            f.panel.Apply()
        f.Destroy()
       
    def ExitCB(self, event):
        """
        Called when the window is closed using the built in close button
        """
        self.OnExit()
        try:
            self.controller.ExitCB()
        except:
            log.exception("Error on exit")
            
        self.Destroy()

    #
    # Preferences Menu
    #
    
    def EditProfileCB(self, event = None):
    
        profile = None
        p = self.venueClient.GetPreferences()
        
        profileDialog = ProfileDialog(None, -1,
                                  'Your profile information', 1)
        profileDialog.SetProfile(self.venueClient.GetPreferences().GetProfile())
        if (profileDialog.ShowModal() == wx.ID_OK):
            profile = profileDialog.GetNewProfile()
            log.debug("VenueClientFrame.EditProfile: change profile: %s" %profile.name)
            try:
                self.controller.EditProfileCB(profile)
            except:
                log.exception("Error editing profile")
                self.Error("Modified profile could not be saved", "Edit Profile Error")
        profileDialog.Destroy()
        
    def SetTransport(self, transport):

        if transport == "multicast":
            self.preferences.Check(self.ID_USE_MULTICAST, True)
            #self.menubar.Enable(self.ID_BRIDGES, False)
        elif transport == "unicast":  
            self.preferences.Check(self.ID_USE_UNICAST, True)
            #self.menubar.Enable(self.ID_BRIDGES, True)

    def UseMulticastCB(self, event=None):
        try:
            self.controller.UseMulticastCB()
            #self.menubar.Enable(self.ID_BRIDGES, False)

            # Disable all bridge items
            for child in self.bridgeSubmenu.GetMenuItems():
                if child.GetKind() == wx.ITEM_CHECK:
                    self.bridgeSubmenu.Check(child.GetId(), False)

            self.preferences.Check(self.ID_USE_MULTICAST, True)
            self.preferences.Check(self.ID_USE_UNICAST, False)
                    
        except NetworkLocationNotFound:
            self.Error("Multicast streams not found","Use Multicast")
        except:
            self.Error("Error using multicast","Use Multicast")


    def UseUnicastCB(self,event=None):
        self.preferences.Check(self.ID_USE_MULTICAST, False)
        self.preferences.Check(self.ID_USE_UNICAST, True)

        # Switch to unicast
        try:
            self.controller.UseUnicastCB()

        except NoAvailableBridges:
            self.Warn("No bridges are currently available")
            self.preferences.Check( self.ID_USE_MULTICAST, True)
            return
        except NoEnabledBridges:
            self.Warn("Bridges are available, but they are disabled in preferences.\nEnable bridges in preferences and try again.")
            self.preferences.Check( self.ID_USE_MULTICAST, True)
            return
        except Exception,e:
            log.exception("Error trying to use unicast")
            self.preferences.Check( self.ID_USE_MULTICAST, True)
            self.venueClient.SetCurrentBridge(None)
            self.Warn("Failed to connect to any available bridge.",
                      "Use Unicast")
            return

        self.__CreateBridgeMenu()
        
        
    def EnableDisplayCB(self,event):
        # ensure that toggle and menu item are in sync
        self.isDisplayEnabled = not self.isDisplayEnabled
        enabledFlag = self.isDisplayEnabled
        self.preferences.Check(self.ID_ENABLE_DISPLAY,enabledFlag)
        if enabledFlag:
            self.displayButton.SetBitmapLabel(icons.getDisplayBitmap())
        else:
            self.displayButton.SetBitmapLabel(icons.getDisplayDisabledBitmap())
                
        try:
            self.controller.EnableDisplayCB(enabledFlag)
        except NoServices:
            pass#print 'no display service found, would you like to add one?'
        except:
            self.Error("Error enabling/disabling video display", "Error enabling/disabling video display")
            
    def EnableVideoCB(self,event):
        # ensure that toggle and menu item are in sync
        self.isVideoEnabled = not self.isVideoEnabled
        enabledFlag = self.isVideoEnabled
        self.preferences.Check(self.ID_ENABLE_VIDEO,enabledFlag)
        if enabledFlag:
            self.videoButton.SetBitmapLabel(icons.getCameraBitmap())
        else:
            self.videoButton.SetBitmapLabel(icons.getCameraDisabledBitmap())
                
        try:
            self.controller.EnableVideoCB(enabledFlag)
        except NoServices:
            if enabledFlag:
                d = AddVideoServiceDialog(self,-1,'Add Video Service')
                ret = d.ShowModal()
                if ret == wx.ID_OK:
                    smUrl,resource = d.GetValue()
                    p = self.venueClient.GetPreferences()
                    
                    # Add the service to the service manager
                    serviceDesc = AGServiceManagerIW(smUrl).AddServiceByName('VideoProducerService.zip',
                                                    resource,None,p.GetProfile())
                    self.venueClient.nodeService.SetServiceEnabled(serviceDesc.uri,1)
                                                    
                    # Add the service manager to the service
                    serviceManagers = self.venueClient.nodeService.GetServiceManagers()
                    found = 0
                    for s in serviceManagers:
                        if s.uri == smUrl:
                            found = 1
                            break
                    if not found:
                        log.debug("Adding service manager")
                        self.venueClient.nodeService.AddServiceManager(smUrl)
                    
        except:
            self.Error("Error enabling/disabling video capture", "Error enabling/disabling video capture")
            

    def EnableAudioCB(self,event):
    
        # ensure that toggle and menu item are in sync
        self.isAudioEnabled = not self.isAudioEnabled
        enabledFlag = self.isAudioEnabled
        self.preferences.Check(self.ID_ENABLE_AUDIO,enabledFlag)
        if enabledFlag:
            self.audioButton.SetBitmapLabel(icons.getAudioBitmap())
        else:
            self.audioButton.SetBitmapLabel(icons.getAudioDisabledBitmap())
                        
        try:
            self.controller.EnableAudioCB(enabledFlag)
        except NoServices:
            pass#print 'no audio service found, would you like to add one?'
        except:
            self.Error("Error enabling/disabling audio", "Error enabling/disabling audio")

    def SaveConfigurationCB(self, event):
        nodeService = self.venueClient.GetNodeService()
        if not nodeService:
            self.Notify("Required internal services are unreachable.")
            return
            
        configs = nodeService.GetConfigurations()
        d = StoreConfigDialog(self,-1,'Store configuration',configs)
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
                    nodeService.StoreConfiguration( config )
                except:
                    log.exception("Error storing node configuration %s" % (configName,))
                    self.Error("Error storing node configuration %s" % (configName,))

                try:
                    # Set the default configuration
                    if isDefault:
                        prefs = self.app.GetPreferences()
                        prefs.SetPreference(Preferences.NODE_CONFIG,configName)
                        prefs.SetPreference(Preferences.NODE_CONFIG_TYPE,config.type)
                        prefs.StorePreferences()

                    self.__LoadMyConfigurations()
                except:
                    log.exception("Error finalizing node save")
                    
                wx.EndBusyCursor()

        d.Destroy()



    def ManageNodeCB(self, event):
        
        if self.nodeManagementFrame:
            self.nodeManagementFrame.Raise()
        else:
            self.nodeManagementFrame = NodeManagementClientFrame(self, -1, 
                                        "Access Grid Node Management",
                                        callback=self.OnNodeActivity)
            
            log.debug("VenueClientFrame.ManageNodeCB: open node management")
            log.debug('nodeservice url: %s', self.venueClient.GetNodeServiceUri() )

            try:
                
                self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeService() )
            except:
                log.exception("VenueClientUI.ManageNodeCB: Can not attach to node %s"%self.venueClient.GetNodeServiceUri())
                              
            if self.nodeManagementFrame.Connected(): # Right node service uri
                self.nodeManagementFrame.UpdateUI()
                self.nodeManagementFrame.Show(True)

            else: # Not right node service uri
                setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                             self.venueClient.GetNodeServiceUri(), 
                                             "Enter the hostname of the machine where the Node Service is running, \nor optionally the entire Node Service URL")

                if setNodeUrlDialog.ShowModal() == wx.ID_OK:

                    url = setNodeUrlDialog.GetValue()

                    url = BuildServiceUrl(url,'http',11000,'NodeService')

                    self.venueClient.SetNodeUrl(url)

                    try:
                        self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeService() )

                    except:
                        log.exception("VenueClientUI.ManageNodeCB: Can not attach to node")
                                            
                    if self.nodeManagementFrame.Connected(): # try again
                        self.nodeManagementFrame.Update()
                        self.nodeManagementFrame.Show(True)

                    else: # wrong url
                        MessageDialog(self, \
                             'Can not open node management\nat %s'%self.venueClient.GetNodeServiceUri(),
                             'Node Management Error')

                setNodeUrlDialog.Destroy()
                self.nodeManagementFrame = None
    
    def PreferencesCB(self, event = None):
        profile = None
        p = self.venueClient.GetPreferences()
        preferencesDialog = PreferencesDialog(None, -1,
                                              'Preferences', p)
        if (preferencesDialog.ShowModal() == wx.ID_OK):
            p = preferencesDialog.GetPreferences()
                       
            try:
                self.controller.ChangePreferences(p)

                # Check for disabled bridge preferences
                bDict = p.GetBridges()
                self.venueClient.SetBridges(bDict)
                self.__CreateBridgeMenu()
            except:
                log.exception("Error editing preferences")
                self.Error("Preferences could not be saved", "Edit Preferences Error")
        preferencesDialog.Destroy()

    # 
    # Navigation Menu
    #
    
    
    def GoToDefaultVenueCB(self,event):
        venueUrl = self.venueClient.GetPreferences().GetProfile().homeVenue
        self.SetVenueUrl(venueUrl)
        self.EnterVenueCB(venueUrl)

    def SetAsDefaultVenueCB(self,event):
        try:
            self.controller.SetAsDefaultVenueCB()
        except:
            self.Error("Error setting default venue", "Set Default Venue Error")

    def AddToMyVenuesCB(self, event=None, url=None, name=None):
       
        if url==None and name==None:
            # use current venue
            if self.venueClient.IsInVenue():
                url = self.venueClient.GetVenue()
                name = self.venueClient.GetVenueName()

                if not url:
                    url = ""
                    name = ""
        
        # Venue url not in list
        # - Prompt for name and validate
        venueName = None
        dialog = AddURLBaseDialog(self, -1, name, url)
        if (dialog.ShowModal() == wx.ID_OK):
            venueName = dialog.GetName()
            venueUrl = dialog.GetUrl()
        dialog.Destroy()

        myVenuesDict = self.controller.GetMyVenues()
        if venueName:
            addVenue = 1
            if myVenuesDict.has_key(venueName):
                # Venue name already in list
                info = "A venue with the same name is already added, do you want to overwrite it?"
                if self.Prompt(info ,"Duplicated Venue"):
                    # User chose to replace the file 
                    self.RemoveFromMyVenues(venueName)
                    self.controller.AddToMyVenuesCB(venueName,url)
                    addVenue = 1
                else:
                    # User chose to not replace the file
                    addVenue = 0
                                   
            if addVenue:
                try:
                    self.controller.AddToMyVenuesCB(venueName,venueUrl)
                    self.AddToMyVenues(venueName,venueUrl)
                except:
                    log.exception("Error adding venue")
                    self.Error("Error adding venue to venue list", "Add Venue Error")
        
    def EditMyVenuesCB(self, event):
        myVenues = None
        venuesDict = self.controller.GetMyVenues()

        editMyVenuesDialog = EditURLBaseDialog(self, -1, "Edit your venues", 
                                                venuesDict)
        
        if (editMyVenuesDialog.ShowModal() == wx.ID_OK):
            myVenues = editMyVenuesDialog.GetValue()
            try:
                self.controller.EditMyVenuesCB(myVenues)
                self.__LoadMyVenues()
            except:
                log.exception("Error saving changes to my venues")
                self.Error("Error saving changes to my venues","Edit Venues Error")

        editMyVenuesDialog.Destroy()

    def GoToMenuAddressCB(self, event):
        name = self.menubar.GetLabel(event.GetId())
        venueUrl = self.myVenuesDict[name]
        self.SetVenueUrl(venueUrl)
        self.EnterVenueCB(venueUrl)

        
    # Code for loading the configurations from the Configurations menu

    def LoadNodeConfig(self, event):

        wx.BeginBusyCursor()

        ID = event.GetId()      
        configName = self.myConfigurationsMenuIds[ID]
    
        configs = self.venueClient.GetNodeConfigurations()
        for c in configs:
            if configName == c.name:
                configuration = c
        try:
            self.venueClient.LoadNodeConfiguration(configuration)
            self.currentConfig = configuration
            
        except:
            log.exception("NodeManagementClientFrame.LoadConfiguration: Error loading configuration")

        try:
            self.OnNodeActivity('load_config')
        except:
            log.exception("Exception updating node")
    
        wx.EndBusyCursor()

    # 
    # Support for scheduler integration
    #
    def AddScheduleCB(self,event):
        defaultRssUrl = 'http://www.mcs.anl.gov/fl/research/accessgrid/anl.rss'
        rssUrl = wx.GetTextFromUser('Specify RSS URL of schedule to add',
                                   'Add Schedule',
                                   defaultRssUrl,
                                   parent=self)
        
        if rssUrl:
            try:
                # Add feed to reader
                self.reader.AddFeed(rssUrl)
            except KeyError:
                msg = ( "An error occurred while reading the schedule feed.\n"+
                        "Please verify the schedule address and try again.\n" +
                        "If problems persist, contact the schedule provider." )
                self.Warn(msg, "Add Schedule Error")
                return

            # Persist feed
            self._SaveFeeds()
          
        
    def TimedUpdateCB(self,event):
        if event.IsChecked():
            self.reader.SetUpdateDuration(self.updateDuration)
        else:
            self.reader.SetUpdateDuration(0)
    
    def UpdateRss(self,url,doc,docDate):
        try:
            menutitle,menu = self._CreateMenu(doc)
            menuid = wx.NewId()
            self.navigation.AppendMenu(menuid,menutitle,menu)
            
            menu.AppendSeparator()
            
            # Append remove item
            removeitemid = wx.NewId()
            menu.Append(removeitemid,'Remove Schedule')
            wx.EVT_MENU(self,removeitemid,lambda evt,menuid=menuid,url=url: self.RemoveScheduleCB(evt,menuid,url))
        except:
            log.exception("Exception updating schedule")

    def _GetFeedConfigFile(self):
        ucd = self.app.GetUserConfig().GetConfigDir()
        feedFile = os.path.join(ucd,'schedule.cfg')
        return feedFile
        
    def _LoadFeeds(self):
        rssUrls = []
        feedFile = self._GetFeedConfigFile()
        if os.path.exists(feedFile):
            f = open(feedFile,'r')
            rssUrls = f.readlines()
            f.close()
            
            # strip first and last characters
            # (should be '[' and ']')
            rssUrls = map(lambda x: x[1:-2], rssUrls)
        return rssUrls

    def _SaveFeeds(self):
        rssUrls = self.reader.GetFeeds()

        feedFile = self._GetFeedConfigFile()
        f = open(feedFile,'w')
        for url in rssUrls:
            f.write('[%s]\n'%url)
        f.close()

    def RemoveScheduleCB(self,event,menuid,url):
        self.navigation.Remove(menuid)
        self.reader.RemoveFeed(url)
        
        self._SaveFeeds()

    def _CreateMenu(self,d):
        """
        This method has to get dirty with the rss doc, 
        ripping bits out and reformatting where necessary
        """
        
        months = { 1:'January',2:'February',3:'March',4:'April',
                   5:'May',6:'June',7:'July',8:'August',9:'September',
                   10:'October',11:'November',12:'December' }
                   
        menu = wx.Menu('')

        menutitle = d['feed']['title']
        
        lastdate = [0,0,0]
        for e in d.entries:

            # get all the data for the item as a Python dictionary
            title = e.title
            itemTime = e['modified']
            timestart = itemTime.split(' ')[3]

            # - compute local time string
            localtime = strtimeToSecs(itemTime)
            ltime = time.localtime(localtime)
            
            # - add entry for date, if needed
            if lastdate != ltime[0:3]:
                menu.Append(wx.NewId(),'%02s %s %d'% 
                                       (ltime[2],
                                       months[ltime[1]],
                                       ltime[0]))
                lastdate = ltime[0:3]
            
            # - compute event start time
            hour = ltime[3]
            min = ltime[4]
            ampm="am"
            if hour > 12:
                hour -= 12
                ampm = 'pm'
            if hour < 10:
                hour = ' ' + str(hour)
            timestart = '%s:%02d%s' % (hour,min,ampm)

            # build title
            title = '%s: %s' % (timestart,title)
            itemid = wx.NewId()

            # add submenu for event
            submenu = wx.Menu('')

            # - view event details
            vieweventid = wx.NewId()
            submenu.Append(vieweventid,'View event details')

            # - go to venue
            if e.has_key('enclosures'):
                venueurl = e.enclosures[0]['url']
                gotovenueid = wx.NewId()
                submenu.Append(gotovenueid,'Go to Venue')
                wx.EVT_MENU(self,gotovenueid,lambda evt,url=venueurl: self.GoToVenueCB(evt,url))

            menu.AppendMenu(itemid,title,submenu)

            viewdetailurl = e.link
            if e.has_key('enclosures'):
                venueurl = e.enclosures[0]['url']
            wx.EVT_MENU(self,vieweventid,lambda evt,url=viewdetailurl: self.ViewEventCB(evt,url))
        return menutitle,menu

    def GoToVenueCB(self,event,url):
        if url:
            self.SetVenueUrl(url)
            self.EnterVenueCB(url)
            
    
    def ViewEventCB(self,event,url):
        if url:
            browser = webbrowser.get()
            needNewWindow = 1
            browser.open(url, needNewWindow)
            


    #
    # Help Menu
    #
    
    def OpenAboutDialogCB(self, event):
        aboutDialog = AboutDialog(None)
        aboutDialog.ShowModal()
        aboutDialog.Destroy()
        
    def OpenManualCB(self,event):
        self.OpenURL(self.manual_url)
        
    def OpenAGDPCB(self,event):
        self.OpenURL(self.agdp_url)
    
    def OpenAGOrgCB(self,event):
        self.OpenURL(self.ag_url)
        
    def OpenFLAGCB(self,event):
        self.OpenURL(self.flag_url)
        
    def OpenFLCB(self,event):
        self.OpenURL(self.fl_url)
        
    def SubmitBugCB(self,event):
        bugReportCommentDialog = BugReportCommentDialog(self)
        
        if(bugReportCommentDialog.ShowModal() == wx.ID_OK):
            # Submit the error report to Bugzilla
            comment = bugReportCommentDialog.GetComment()
            email = bugReportCommentDialog.GetEmail()
            
            SubmitBug(comment, self.venueClient.GetPreferences().GetProfile(), email)
            bugFeedbackDialog = wx.MessageDialog(self, 
                                  "Your error report has been sent, thank you.",
                                  "Error Reported", 
                                  style = wx.OK|wx.ICON_INFORMATION)
            bugFeedbackDialog.ShowModal()
            bugFeedbackDialog.Destroy()       
            
        bugReportCommentDialog.Destroy()
        
    def OpenBugzillaCB(self,event):
        self.OpenURL(self.bugzilla_url)
        

    # Menu Callbacks
    #
    ############################################################################

    ############################################################################
    #
    # Core UI Callbacks
    
    
    def EnterVenueCB(self, venueUrl):
        try:
            wx.BeginBusyCursor()
            
            if isinstance(venueUrl,unicode):
                venueUrl = venueUrl.encode('ascii','ignore')
            
            # manipulate the venue url some
            defaultproto = 'https'
            defaultport = 8000
            
            # - define a mess of regular expressions for matching venue urls
            hostre = re.compile('^[\w.-]*$')
            hostportre = re.compile('^[\w.-]*:[\d]*$')
            hostpathre = re.compile('^[\w.-]*/[\w]*')
            protohostre = re.compile('^[\w]*://[\w.-]*$')
            protohostportre = re.compile('^[\w]*://[\w.-]*:[\d]*$')
            protohostportpathre = re.compile('^[\w]*://[\w.-]*:[\d]*/[\w]*')
            protohostpathre = re.compile('^[\w]*://[\w.-^/]*/[\w]*')
            
            # - check for host only
            if hostre.match(venueUrl):
                host = venueUrl
                venueUrl = '%s://%s:%d/Venues/default' % (defaultproto,host,defaultport)
            # - check for host:port
            elif hostportre.match(venueUrl):
                hostport = venueUrl
                venueUrl = '%s://%s/Venues/default' % (defaultproto,hostport)
            elif hostpathre.match(venueUrl):
                parts = venueUrl.split('/')
                host = parts[0]
                path = '/'.join(parts[1:])
                venueUrl = '%s://%s:%d/%s' % (defaultproto,host,defaultport,path)
            elif protohostre.match(venueUrl):
                protohost = venueUrl
                venueUrl = '%s:%d/Venues/default' % (protohost,defaultport)
            elif protohostportre.match(venueUrl):
                protohostport = venueUrl
                venueUrl = '%s/Venues/default' % (protohostport)
            elif protohostportpathre.match(venueUrl):
                pass
            elif protohostpathre.match(venueUrl):
                parts = urlparse.urlparse(venueUrl)
                proto = parts[0]
                host = parts[1]
                path = parts[2]
                venueUrl = '%s://%s:%d%s' % (proto,host,defaultport,path)

            # - update the venue url
            self.venueAddressBar.SetAddress(venueUrl)
            
            self.SetStatusText("Entering venue at %s" % (venueUrl,))
            
            log.info('Entering venue at %s', venueUrl)

            self.controller.EnterVenueCB(venueUrl)
            
            self.SetStatusText("Entered venue at %s" % (venueUrl,))

            self.statusbar.SetStatusText("",1)
            wx.EndBusyCursor()
        except CertificateRequired:
            wx.EndBusyCursor()
            log.info('Certificate required to enter venue')
            try:
                self.usingCert = 1
                self.controller.EnterVenueCB(venueUrl,withcert=1)
                self.statusbar.SetStatusText("SECURE",1)
            except:
                log.exception("Something went wrong trying to enter with a certificate")
                self.Notify('A certificate is required to enter this Venue, but you do not have one.  Press OK to launch the certificate manager so that you can import or request a certificate, or Cancel to not.')
        except:
            wx.EndBusyCursor()
            log.exception("VenueClientUI.EnterVenueCB: Failed to connect to %s"%venueUrl)
            self.Notify("Can not connect to venue at %s"%venueUrl, "Notification")

    #
    # Participant Actions
    #
       
    def ViewProfileCB(self, event=None):
        participant = self.GetSelectedItem()
        if(participant != None and isinstance(participant, ClientProfile)):
            profileView = ProfileDialog(self, -1, "Profile", 0)
            log.debug("VenueClientFrame.OpenParticipantProfile: open profile view with this participant: %s" 
                        %participant.name)
            profileView.SetDescription(participant)
            profileView.ShowModal()
            profileView.Destroy()
        else:
            self.Notify("Select the participant you want to view information about", "View Profile") 

    def AddPersonalDataCB(self, event=None):
        dlg = wx.FileDialog(self, "Choose file(s):", style = wx.OPEN | wx.MULTIPLE)

        if dlg.ShowModal() == wx.ID_OK:
            fileList = dlg.GetPaths()
            log.debug("VenueClientFrame.OpenAddPersonalDataDialog:%s " %str(fileList))

            try:
                self.controller.AddPersonalDataCB(fileList)
            except:
                self.Error("Error uploading personal data files", "Add Personal Data Error")

            

    #
    # Data Actions
    #

    """
    AddData is up above in menu callbacks
    """

    def OpenDataCB(self, event):
        data = self.GetSelectedItem()
        if data:
            self.controller.OpenDataCB(data)
        else:
            self.Notify("Select the data you want to open", "Open Data")
              
    def SaveDataCB(self, event):
        data = self.GetSelectedItem()
        log.debug("VenueClientFrame.SaveData: Save data: %s", data)
        if(data != None and isinstance(data, DataDescription)):
            name = data.name
            path = self.SelectFile("Specify name for file", name)
            if path:
                self.controller.SaveDataCB(data,path)
        else:
            self.Notify("Select the data you want to save", "Save Data")

    def RemoveDataCB(self, event):
        itemList = self.GetSelectedItems()
        parentItem = self.contentListPanel.GetItemData(self.contentListPanel.curItemId)
        if itemList:
            for item in itemList:
                if(item != None and isinstance(item, DataDescription)):
                    text ="Are you sure you want to delete "+ item.name + "?"
                    if self.Prompt(text, "Confirmation"):
                        try:
                            self.controller.RemoveDataCB(item)
                        except NotAuthorizedError:
                            log.info("RemoveDataCB: Not authorized to remove data")
                            self.Notify("You are not authorized to remove the file", 
                                        "Remove Personal Files")        
                        except LegacyCallInvalid:
                            log.info("RemoveDataCB: Invalid legacy call on non-root data")
                            self.Notify("You tried to remove data, that is not accesible for AG3.0.2 users in the data stroe structure ", 
                                        "Remove Files")        
                        except LegacyCallOnDir:
                            log.info("RemoveDataCB: No delete of directories for AG3.0.2 clients")
                            self.Notify("You are not to delete directories with an AG3.0.2 client ", 
                                        "Remove Files")        
                        except:
                            log.exception("RemoveDataCB: Error occurred when trying to remove data")
                            self.Error("The file could not be removed", "Remove Files Error")
        else:
            self.Notify("Select the data you want to delete", "No file selected")
            
    #Added by NA2-HPCE
    def RemoveDirCB(self, event):
        #Implement removal of directories here
        
        treeparent = self.contentListPanel.parent_item
        itemList = self.GetSelectedItems()
        
        if itemList:
            for item in itemList:
                if(item != None and item.IsOfType(DataDescription.TYPE_DIR)):
                    text ="Are you sure you want to delete "+ item.name + "?"
                    if self.Prompt(text, "Confirmation"):
                        #check for files in directory
                        
                        
                        #when all files are deleted, delete directory
                        try:
                            if (not self.__venueProxy == None):             
                                self.__venueProxy.RemoveDir(item)
                                
                        except NotAuthorizedError:
                            log.info("RemoveDirCB: Not authorized to remove data")
                            self.Notify("You are not authorized to remove the file", 
                                        "Remove Personal Files")        
                        #except:
                            #log.exception("RemoveDirCB: Error occured when trying to remove data")
                            #self.Error("The file could not be removed", "Remove Files Error")
                            
        else:
            self.Notify("Select the data or directory you want to delete", "No file selected")
        
    def UpdateDataCB(self,dataDesc):
        try:
            self.controller.UpdateDataCB(dataDesc)
        except:
            log.exception("UpdateDataCB: Error occured when trying to update data")
            self.Error("The file could not be updated", "Update Files Error")

    #
    # Service Actions
    #
    
    """
    AddService is up above in menu callbacks
    """
    
    def OpenServiceCB(self,event):
        service = self.GetSelectedItem()
        if service:
            self.controller.OpenServiceCB(service)
        else:
            self.Notify("Select the service you want to open","Open Service")       
    
    def RemoveServiceCB(self, event):
        serviceList = self.GetSelectedItems()
        if serviceList:
            for service in serviceList:
                if service and isinstance(service,ServiceDescription):
                    text ="Are you sure you want to delete "+ service.name + "?"
                    if self.Prompt(text, "Confirmation"):
                        try:
                            self.controller.RemoveServiceCB(service)
                        except:
                            self.Error("The service could not be removed", "Remove Service Error")
        else:
           self.Notify("Select the service you want to delete", "Delete Service")       

    def UpdateServiceCB(self,serviceDesc):
        try:
            self.controller.UpdateServiceCB(serviceDesc)
        except:
            self.Error("Error updating service", "Update Service Error")
        
            
    #
    # Application Actions
    #
    
    def RemoveApplicationCB(self,event):
        appList = self.GetSelectedItems()
        if appList:
            try:
                self.controller.RemoveApplicationCB(appList)
            except:
                self.Error("Error removing application","Remove Application Error")
                
        else:
            self.Notify( "Select the application you want to delete", "Delete Application")

    def StartApplicationCB(self, app):
        timestamp = time.strftime("%Y-%m-%d %I:%M:%S %p")
        id = self.venueClient.GetPreferences().GetProfile().GetName()
        name = "%s" % (timestamp)
        app.description = "Started by %s at %s" % (id, timestamp)
        
        try:
            self.controller.StartApplicationCB(name,app)
        except:
            self.Error("Error adding application","Add Application Error")
                
    def MonitorAppCB(self, application):
        """
        Open monitor for the application.
        """
        # Create new application monitor
        try:
            AppMonitor(self, str(application.uri))
        except:
            self.Error("Error opening application monitor","Monitor App Error")
    
        
    def UpdateApplicationCB(self,appDesc):
        try:
            self.controller.UpdateApplicationCB(appDesc)
        except:
            self.Error("Error updating application","Application Update Error")
        

    #
    # Plugins
    #

    def StartPluginCB(self, plugin):
        try:
            self.controller.StartPluginCB(plugin)
        except Exception, e:
            self.Error("Error starting plugin: %s" % e, "Start Plugin Error")
            
    #
    # Text
    #
    
    def SendTextCB(self,text):
        try:
            if self.venueClient.IsInVenue():
                self.controller.SendTextCB(text)
            else:
                self.Notify("Connect to a venue before sending text messages.", "Send Text Error")
        except:
            self.Error("Error sending text","Send Text Error")


    #
    # Node Management hook
    #
    def OnNodeActivity(self,action,data=None):
        if action == 'load_config':
            log.info('OnNodeActivity: got action: %s', action)
            try:
                self.controller.EnableVideoCB(self.isVideoEnabled)
            except NoServices:
                pass
            try:
                self.controller.EnableAudioCB(self.isAudioEnabled)
            except NoServices:
                pass
            try:
                self.controller.EnableDisplayCB(self.isDisplayEnabled)
            except NoServices:
                pass
            self.venueClient.UpdateNodeService()
        elif action == 'add_service':
            log.info('OnNodeActivity: got action: %s', action)
            serviceDesc = data
            capType = serviceDesc.capabilities[0].type
            capRole = serviceDesc.capabilities[0].role
            enabled = -1
            if capType == 'video' and capRole == 'producer':
                enabled = self.isVideoEnabled
            elif capType == 'audio':
                enabled = self.isAudioEnabled
            elif capType == 'video' and capRole == 'consumer':
                enabled = self.isDisplayEnabled
            # only set enabled state for well-known services

            #If NodeManagament has been started from within VenueClient and is already connected to a Venue
            #then NegotiateCapabilities to make the newly added service known to the server side
            #UpdateNodeService takes care to update the local NodeService with the new
            #stream information
            if not self.venueClient.GetConnectionId() == None:
               vp = self.venueClient.GetVenueProxy()
               self.venueClient.streamDescList = vp.NegotiateCapabilities(self.venueClient.GetConnectionId(), serviceDesc.capabilities)
               self.venueClient.UpdateNodeService()
                              
            
            if enabled >= 0:
                self.venueClient.nodeService.SetServiceEnabled(serviceDesc.uri,enabled)
        elif action == 'store_config':
            self.__LoadMyConfigurations()
        else:
            log.info('OnNodeActivity: got unexpected action: %s', action)


    # end Core UI Callbacks
    #
    ############################################################################


    ############################################################################
    #
    # Accessors

    def GetSelectedItem(self):
        return self.contentListPanel.GetLastClickedTreeItem()

    def GetSelectedItems(self):
        idList = self.contentListPanel.GetSelections()
        itemList = map( lambda id: self.contentListPanel.GetItemData(id).GetData(), 
                        idList )
        return itemList

    def GetAudioEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_AUDIO)

    def GetDisplayEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_AUDIO)

    def GetVideoEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_VIDEO)

    def GetText(self):
        return self.textClientPanel.GetText()
    
    # end Accessors
    #
    ############################################################################

    ############################################################################
    #
    # General Implementation
    
    #Added by NA2-HPCE
    def SetVenueProxy(self, proxy):
        self.__venueProxy = proxy
        self.contentListPanel.SetVenueProxy(proxy)

    #
    # Upload Files Methods
    #
        
    def OpenUploadFilesDialog(self):
        # Method name should change...
        #
        # Prepare statusbar for progress.
        #
        self.statusbar.Reset()
        self.statusbar.SetMessage("Uploading files")
                
    def UpdateUploadFilesDialog(self, filename, sent, total, file_done, xfer_done):
        # Method name should change...
        #
        text = "Uploading file %s"%filename

        wx.CallAfter(self.statusbar.SetMax, total)
        wx.CallAfter(self.statusbar.SetProgress,
                    text,sent, file_done, xfer_done)

        
    def UploadFilesDialogCancelled(self):
        # Method name should change...
        #
        return self.statusbar.IsCancelled()      
        
    #
    # Save Files Methods
    #
    
    def OpenSaveFileDialog(self, filename, size):
        #
        # Create the dialog for the download.
        #
        
        self.statusbar.Reset()
        self.statusbar.SetMax(size)
        self.statusbar.SetMessage("Saving file to %s ...     "% (filename))
        
        
    def UpdateSaveFileDialog(self, filename, sent, xfer_done):
        text = "Saving file to %s ...     "% (filename)
        file_done = 'not used'
        
        wx.CallAfter(self.statusbar.SetProgress,
                    text,sent, file_done, xfer_done)
        
    def SaveFileDialogCancelled(self):
        return self.statusbar.IsCancelled()      

        
    #
    # File Selection Dialog
    #

    def SelectFile(self,text,defaultFile = "", wildcard = None):
        filePath = None
        if not wildcard:
            wildcard = '*.' + defaultFile.split('.')[-1]
        dlg = wx.FileDialog(self, text, 
                           defaultFile = defaultFile,
                           wildcard = wildcard,
                           style = wx.SAVE)
        
        # Open file dialog
        if dlg.ShowModal() == wx.ID_OK:
            filePath = dlg.GetPath()
            fileName = (os.path.split(filePath))[1]

            # Check if file already exists
            if os.access(filePath, os.R_OK):
                messageDlg = wx.MessageDialog(self, 
                                    "The file %s already exists. Do you want to replace it?"%fileName, 
                                    "Save Text" , 
                                    style = wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT)
                # Do we want to overwrite?
                if messageDlg.ShowModal() == wx.ID_NO:
                    log.debug("VenueClientFrame.SaveText: Do not replace existing text file.")
                    # Do not save text; return
                    filePath = None
                messageDlg.Destroy()
                    
        return filePath

    def SelectFiles(self, text):
        fileList = None
        dlg = wx.FileDialog(self, text,
                           #defaultFile = name,
                           style = wx.OPEN | wx.OVERWRITE_PROMPT | wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            fileList = dlg.GetPaths()
            
        dlg.Destroy()

        return fileList
    
    #
    # Prompts, warnings, etc.
    #

    def Prompt(self,text,title):
    
        
        dlg = wx.MessageDialog(self, text, title,
                              style = wx.ICON_INFORMATION | wx.OK | wx.CANCEL)
        ret = dlg.ShowModal()
        if ret == wx.ID_OK:
            return 1
        return 0

    def Notify(self,text,title="Notification"):
    
        wx.CallAfter(self.__Notify,text,title)

    def Warn(self,text,title="Warning"):
        wx.CallAfter(self.__Warn,text,title)

    def Error(self,text,title="Error"):
        log.exception("Error")
        ErrorDialog(None, text, title)

    #
    # Other
    #

    def SetStatusText(self,text):
        self.statusbar.SetStatusText(text,0)

    def SetStatusTextDelayed(self,text,delay):
        """
        SetStatusTextDelayed performs the same function as SetStatusText, with a
        couple variations:
        - sleeps for the specified time first
        - calls SetStatusText using wx.CallAfter, since the call will be made from a
          thread other than the primary.
        """
        time.sleep(delay)
        wx.CallAfter(self.statusbar.SetStatusText,text,0)

    def GoBackCB(self):
        """
        This method is called when the user wants to go back to last visited venue
        """
        log.debug("Go back")
        self.controller.GoBackCB()

    def StartAllCmd(self, objDesc, verb=None, cmd=None):
        self.controller.StartAllCmd(objDesc, verb, cmd)
        
    def StartCmd(self, objDesc, verb=None,cmd=None):
        self.controller.StartCmd(objDesc,verb,cmd)
            
    def AddVenueToHistory(self,venueUrl):
        self.venueAddressBar.AddChoice(venueUrl)

    def OpenURL(self, url):
        """
        """
        log.debug("VenueClientFrame.OpenURL: Opening: %s", url)
        
        needNewWindow = 0
        if not self.browser:
            self.browser = webbrowser.get()
            needNewWindow = 1
        self.browser.open(url, needNewWindow)
        
    def GetCommands(self, objDesc):
        return self.controller.GetCommands(objDesc)
        
    def GetProfile(self):
        return self.venueClient.GetPreferences().GetProfile()
        
    def GetVenue(self):
        return self.venueClient.GetVenue()

    def HandleServerConnectionFailure(self):
        if self.venueClient and self.venueClient.IsInVenue():
            log.debug("bin::VenueClient::HandleServerConnectionFailure: call exit venue")
            self.__CleanUp()
            self.venueAddressBar.SetTitle("You are not in a venue",
                                                'Click "Go" to connect to the venue, which address is displayed in the address bar') 
            self.venueClient.ExitVenue()
            MessageDialog(None, "Your connection to the venue is interrupted and you will be removed from the venue.  \nTry to connect again.", 
                          "Lost Connection")

    def AddToMyVenues(self,name,url):
        ID = wx.NewId()
        text = "Go to: " + url
        self.navigation.Insert(self.myVenuesPos,ID, name, text)
        self.myVenuesMenuIds[name] = ID
        self.myVenuesDict[name] = url
        wx.EVT_MENU(self, ID, self.GoToMenuAddressCB)
    
    def RemoveFromMyVenues(self,venueName):
        # Remove the venue from my venues menu list
        menuId = self.myVenuesMenuIds[venueName]
        self.navigation.Remove(menuId)
    
        # Remove it from the dictionary
        del self.myVenuesMenuIds[venueName]

    def OnExit(self):
        """
        This method performs all processing which needs to be
        done as the application is about to exit.
        """
       
        # Ensure things are not shut down twice.
        if not self.onExitCalled:
            self.onExitCalled = True
            log.info("--------- END VenueClient")
            
            # Call close on all open child windows so they can do necessary cleanup.
            # If close is called instead of destroy, an wx.EVT_CLOSE event is distributed
            # for child windows and cleanup code can be put in the callback for that event.
            children = self.GetChildren()
            for c in children:
                try:
                    c.Close(1)
                except:
                    pass

        else:
            log.info("note that bin.VenueClient.OnExit() was called twice.")
       
    def SetVenueUrl(self, url = None):
        fixedUrlList = []
                   
        if(url == None):
            name = self.menubar.GetLabel(event.GetId())
            fixedUrlList = map(self.__FillTempHelp, self.myVenuesDict[name])

        else:
            fixedUrlList = map(self.__FillTempHelp, url)

        fixedUrl = ""
        for x in fixedUrlList:
            fixedUrl = fixedUrl + x

        # Set url in address bar    
        self.venueAddressBar.SetAddress(fixedUrl)
        
        # Add url to address history
        self.venueAddressBar.AddChoice(fixedUrl)


    def BuildAppMenu(self, prefix):
        """
        Build the menu of installed applications
        """
        menu = wx.Menu()
        
        appDescList = self.controller.GetInstalledApps()
        	
        # Add applications in the appList to the menu
        for app in appDescList:
            if app != None and app.name != None and int(app.startable) == 1:
                menuEntryLabel = prefix + app.name
                appId = wx.NewId()
                menu.Append(appId,menuEntryLabel,menuEntryLabel)
                callback = lambda event,theApp=app: self.StartApplicationCB(theApp)
                wx.EVT_MENU(self, appId, callback)

        if menu.GetMenuItemCount() == 0:
            log.info('building no applications menu')
            itemid = wx.NewId()
            menu.Append(itemid,"No applications available")
            menu.Enable(itemid,False)

        return menu

    def BuildPluginMenu(self, prefix = ""):
        
        menu = wx.Menu()
        menuItemCount = 0

        pluginList = self.controller.GetInstalledPlugins()
        if not pluginList:
            return None

        for pluginName in pluginList:

            log.debug("Setting up plugin: %s." % pluginName)

            plugin = self.controller.GetInstalledPlugin(pluginName)
            if not plugin:
                log.debug("Missing plugin %s." % pluginName)
                continue

            menuItem = plugin.CreateMenu(self)
            if menuItem:
                if isinstance(menuItem, wx.MenuItem):
                    menu.AppendItem(menuItem)
                    menuItemCount = menuItemCount + 1
                else:
                    log.exception("Menu item for plugin %s must be a wx.MenuItem." % pluginName)

            plugin.CreateToolbar(self, self.toolbar, VenueClientUI.TOOLSIZE)
            
        if menuItemCount > 0:
            return menu
        else:
            log.debug("BuildPluginMenu: no plugins with menu items -> menu hidden")
            return None

    def GetPersonalData(self,clientProfile):
        return self.venueClient.GetPersonalData(clientProfile)

    def UpdateNavigation(self):
        self.venueListPanel.list.UpdateView()
        

    # end General Implementation
    #
    ############################################################################

    ############################################################################
    #
    # Implementation of VenueClientObserver
    # Note:  These methods are called by an event processor in a different thread,
    #        so any wx calls here must be made with wx.CallAfter.

    def SetMcastStatus(self,status):
        wx.CallAfter(self.__SetMcastStatus,status)
        
    def __SetMcastStatus(self,bool):
        if bool:
            bitmap = icons.getMulticastBitmap()
            shortHelp = 'Multicast available'
        else:
            bitmap = icons.getNoMulticastBitmap()
            shortHelp = 'Multicast not available'
        self.networkButton.SetBitmapLabel(bitmap)
        self.networkButton.SetToolTip(wx.ToolTip(shortHelp))
        self.toolbar.Realize()
        
    def UpdateMcastStatus(self):
        self.SetMcastStatus(self.venueClient.GetMulticastStatus())
        
    def AddUser(self, profile):
        """
        This method is called every time a venue participant enters
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *profile* The ClientProfile of the participant who entered the venue
        """

        wx.CallAfter(self.statusbar.SetStatusText, "%s entered the venue" %profile.name)
        wx.CallAfter(self.contentListPanel.AddParticipant, profile)
        self.venueClient.UpdateProfileCache(profile)
        log.debug("  add user: %s" %(profile.name))

    def RemoveUser(self, profile):
        """
        This method is called every time a venue participant exits
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *profile* The ClientProfile of the participant who exited the venue
        """

        wx.CallAfter(self.statusbar.SetStatusText, "%s left the venue" %profile.name)
        wx.CallAfter(self.contentListPanel.RemoveParticipant, profile)
        log.debug("  remove user: %s" %(profile.name))

    def ModifyUser(self, profile):
        """
        This method is called every time a venue participant changes
        its profile.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *profile* The modified ClientProfile of the participant that changed 
                  profile information
        """

        log.debug("EVENT - Modify participant: %s" %(profile.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "%s changed profile information" %profile.name)
        wx.CallAfter(self.contentListPanel.ModifyParticipant, profile)

    def AddData(self, dataDescription):
        """
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        
        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got 
                          added to the venue
        """

        if dataDescription.type == "None" or dataDescription.type == None:
            wx.CallAfter(self.statusbar.SetStatusText, "file '%s' has been added to venue" 
                        %dataDescription.name)
            
            # Just change venuestate for venue data.
        else:
            # Personal data is handled in VenueClientUIClasses to find out 
            # who the data belongs to
            pass

        log.debug("EVENT - Add data: %s" %(dataDescription.name))
        wx.CallAfter(self.contentListPanel.AddData, dataDescription)
        
    #Added by NA2-HPCE
    def AddDir(self, dataDescription):
        """
        This method is called every time new directories are added to the venue.
        Appropriate gui updates are made in client.
        
        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got 
                          added to the venue
        """

        if dataDescription.GetObjectType() == DataDescription.TYPE_DIR:
            wx.CallAfter(self.statusbar.SetStatusText, "Directory '%s' has been added to venue" 
                        %dataDescription.name)
            
            # Just change venuestate for venue data.
        else:
            # Personal data is handled in VenueClientUIClasses to find out 
            # who the data belongs to
            pass

        log.debug("EVENT - Add dir: %s" %(dataDescription.name))
        wx.CallAfter(self.contentListPanel.AddDir, dataDescription)

    def UpdateData(self, dataDescription):
        """
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got updated 
                          in the venue
        """
        
        #Retrieveing dataDescription with newer WSDL description so all
        #required data is contained
        #dataDescription = self.__venueProxy.GetDescById(dataDescription.GetId())
        
        log.debug("EVENT - Update data: %s" %(dataDescription.name))
        wx.CallAfter(self.contentListPanel.UpdateData, dataDescription)

    def RemoveData(self, dataDescription):
        """
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that was removed 
                          from the venue
        """

        # Handle venue data (personal data is in VenueClientUIClasses)
        if dataDescription.type == "None" or dataDescription.type == None:
            wx.CallAfter(self.statusbar.SetStatusText, 
                        "file '%s' has been removed from venue"
                        %dataDescription.name)
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass
        
        #Retrieveing dataDescription with newer WSDL description so all
        #required data is contained
        #try:
        #    dataDescription = self.__venueProxy.GetDescById(dataDescription.GetId())
        #except:
        #    pass
               
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "File '%s' has been removed from the venue" 
                    %dataDescription.name)
        log.debug("EVENT - Remove data: %s" %(dataDescription.name))
        wx.CallAfter(self.contentListPanel.RemoveData, dataDescription)
        
    def RemoveDir(self, dataId):
        """
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that was removed 
                          from the venue
        """
       
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "Directory has been removed from the venue")
        log.debug("EVENT - Remove dir: %s" %(dataId))
        wx.CallAfter(self.contentListPanel.RemoveDir, dataId)


    def AddService(self, serviceDescription):
        """
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that was added to the venue
        """

        log.debug("EVENT - Add service: %s" %(serviceDescription.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "Service '%s' was added to the venue" 
                    %serviceDescription.name)
        wx.CallAfter(self.contentListPanel.AddService, serviceDescription)

    def RemoveService(self, serviceDescription):
        """
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that was removed from the venue
        """

        log.debug("EVENT - Remove service: %s" %(serviceDescription.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "Service '%s' has been removed from the venue" 
                    %serviceDescription.name)
        wx.CallAfter(self.contentListPanel.RemoveService, serviceDescription)

    def UpdateService(self, serviceDescription):
        """
        This method is called when a service is updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that got updated.
        """
        log.debug("EVENT - Update service: %s" %(serviceDescription.name))
        wx.CallAfter(self.SetStatusText, 
                    "Service '%s' was updated." %serviceDescription.name)
        wx.CallAfter(self.contentListPanel.UpdateService, serviceDescription)
    
    def AddApplication(self, appDescription):
        """
        This method is called every time a new application is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that was added to the venue
        """

        log.debug("EVENT - Add application: %s, Mime Type: %s"
                  % (appDescription.name, appDescription.mimeType))
        wx.CallAfter(self.statusbar.SetStatusText,
                    "Application '%s' has been added to the venue" %appDescription.name)
        wx.CallAfter(self.contentListPanel.AddApplication, appDescription)

    def RemoveApplication(self, appDescription):
        """
        This method is called every time an application is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that was removed from the venue
        """

        log.debug("EVENT - Remove application: %s" %(appDescription.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "Application '%s' has been removed from the venue" 
                    %appDescription.name)
        wx.CallAfter(self.contentListPanel.RemoveApplication, appDescription)

    def UpdateApplication(self, appDescription):
        """
        This method is called when an application is updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that should be updated.
        """
        wx.CallAfter(self.SetStatusText,
                    "Application '%s' was updated." %appDescription.name)
        log.debug("EVENT - Update application: %s, Mime Type: %s"
                  % (appDescription.name, appDescription.mimeType))
        wx.CallAfter(self.contentListPanel.UpdateApplication, appDescription)


    def AddConnection(self, connDescription):
        """
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Add connection: %s" %(connDescription.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "A new exit, '%s', has been added to the venue" 
                    %connDescription.name)  
        wx.CallAfter(self.venueListPanel.AddVenueDoor, connDescription)

    def RemoveConnection(self, connDescription):
        """
        This method is called every time an exit is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Remove connection: %s" %(connDescription.name))
        wx.CallAfter(self.statusbar.SetStatusText, 
                    "The exit to '%s' has been removed from the venue" 
                    %connDescription.name)  
        wx.CallAfter(self.venueListPanel.RemoveVenueDoor, connDescription)


    def SetConnections(self, connDescriptionList):
        """
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescriptionList* A list of ConnectionDescriptions representing all the exits in the venue.
        """
        log.debug("EVENT - Set connections")
        wx.CallAfter(self.venueListPanel.CleanUp)

        for connection in connDescriptionList:
            log.debug("EVENT - Add connection: %s" %(connection.name))
            wx.CallAfter(self.venueListPanel.AddVenueDoor, connection)

    def AddStream(self,streamDesc):
        pass
                       
    def RemoveStream(self,streamDesc):
        pass

    def ModifyStream(self,streamDesc):
        pass
                   
    def AddText(self,name,text):
        """
        This method is called when text is received from the text service.

        **Arguments:**
        
        *name* The name of the user who sent the message
        *text* The text sent
        """
        
        wx.CallAfter(self.textClientPanel.OutputText, name, text)

    def OpenApplication(self, appCmdDesc):
        '''
        This method is called when someone wants to invite you to a
        shared application session.
        '''
        wx.CallAfter(self.__OpenApplication, appCmdDesc)
        
    def EnvSort(self, item1, item2):
        if int(item1.GetLevel()) == -2:
            return 1
        if int(item2.GetLevel()) == -2:
            return -1
        if item1.GetLevel() < item2.GetLevel():
            log.debug("Item1 Is higher hierarchy")
            return -1
        elif item1.GetLevel() == item2.GetLevel():
            log.debug("Item1 Is same hierarchy")
            return 0
        else:
            log.debug("Item1 Is lower hierarchy")
            return 1

    def EnterVenue(self, URL, warningString="", enterSuccess=1):
        """
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
      
        **Arguments:**
        
        *URL* A string including the venue address we want to connect to
        *back* Boolean value, True if the back button was pressed, else False.
        
        """
        log.debug("bin.VenueClient::EnterVenue: Enter venue with url: %s", URL)
    
        # Show warnings, do not enter venue
        if not enterSuccess:
            # Currently receives type of error in warningString.
            # This will go back catching an exception with vc redesign.
            # For now, show all warnings to user
            
            if warningString == "NotAuthorized":
                text = "You are not authorized to enter the venue located at %s.\n." % URL
                wx.CallAfter(MessageDialog, None, text, "Notification")
            elif warningString.startswith("Authorization failure connecting to server"):
                text = warningString
                wx.CallAfter(self.Notify, text, "Authorization failure")
                log.debug(warningString)
            else:
                log.debug("warningString: %s" %warningString)
                text = "Error entering venue" 
                if warningString:
                    if warningString == 'No address associated with nodename':
                        warningString = 'Error locating Venue host; check the hostname'
                    elif warningString == 'Connection refused':
                        warningString = 'Error locating Venue host; check the port'   
                    text += '\n%s' % (warningString,)
                wx.CallAfter(self.Notify, text, "Can not enter venue")
                wx.CallAfter(self.statusbar.SetStatusText, "" )

            return
               
        # initialize flag in case of failure
        enterUISuccess = 1

        try:

            #
            # Reflect venue entry in the client
            #
            wx.CallAfter(self.textClientPanel.OutputText, "enter",
                        "-- Entered venue %s" % self.venueClient.GetVenueName())
            wx.CallAfter(self.textClientPanel.OutputText, "enter",
                        self.venueClient.GetVenueDescription())
            
            wx.CallAfter(self.statusbar.SetStatusText, "Entered venue %s successfully" 
                        %self.venueClient.GetVenueName())

            # clean up ui from current venue before entering a new venue
            if self.venueClient.GetVenue() != None:
                # log.debug("clean up frame")
                wx.CallAfter(self.__CleanUp)

            # Get current state of the venue
            venueState = self.venueClient.GetVenueState()
            
            # Update the UI
            wx.CallAfter(self.venueAddressBar.SetTitle,
                            venueState.name, venueState.description) 

            # Load clients
            # log.debug("Add participants")
            wx.CallAfter(self.statusbar.SetStatusText,
                            "Load participants")
            for client in venueState.clients.values():
                wx.CallAfter(self.contentListPanel.AddParticipant,
                            client)
                # log.debug("   %s" %(client.name))

            # Load data
            log.debug("Load Venue data store data")
            wx.CallAfter(self.statusbar.SetStatusText, "Load data")
            log.debug("Amount of entries: %s", len(venueState.data.values()))
            datalist = venueState.data.values()
            sortFunc = self.EnvSort
            datalist.sort(sortFunc)
            for data in datalist:
                if data.GetObjectType() == DataDescription.TYPE_DIR:
                    wx.CallAfter(self.contentListPanel.AddDir, data)
                else:
                    wx.CallAfter(self.contentListPanel.AddData, data)
                # log.debug("   %s" %(data.name))

            # Load services
            # log.debug("Add service")
            wx.CallAfter(self.statusbar.SetStatusText,
                        "Load services")
            for service in venueState.services.values():
                wx.CallAfter(self.contentListPanel.AddService,
                            service)
                # log.debug("   %s" %(service.name))

            # Load applications
            # log.debug("Add application")
            wx.CallAfter(self.statusbar.SetStatusText,
                        "Load applications")
            for app in venueState.applications.values():
                wx.CallAfter(self.contentListPanel.AddApplication,
                            app)
                # log.debug("   %s" %(app.name))

            #  Load exits
            # log.debug("Add exits")
            wx.CallAfter(self.statusbar.SetStatusText, "Load exits")
            wx.CallAfter(self.venueListPanel.AddConnections)
                # log.debug("   %s" %(conn.name))

            # Update scroll position to the top after adding everything
            wx.CallAfter(self.contentListPanel.tree.SetScrollPos, wx.VERTICAL, 0, True)

            wx.CallAfter(self.SetVenueUrl, URL)
                                              
            # Enable menus
            wx.CallAfter(self.__ShowMenu)
            
            #
            # Enable the application menu that is displayed over
            # the Applications items in the list
            # (this is not the app menu above)
            wx.CallAfter(self.__EnableAppMenu, True)

            # Update the UI
            wx.CallAfter(self.AddVenueToHistory, URL)
            
            log.debug("Entered venue")
            
            #
            # Display all non fatal warnings to the user
            #
            if warningString != '': 
                message = "Following non fatal problems have occured when you entered the venue:\n" + warningString
                wx.CallAfter(self.Notify, message, "Notification")
                
                wx.CallAfter(self.statusbar.SetStatusText, 
                            "Entered %s successfully" %self.venueClient.GetVenueName())
       
        except Exception, e:
            log.exception("bin.VenueClient::EnterVenue failed")
            enterUISuccess = 0

        #if not enterUISuccess:
        #    text = "You have not entered the venue located at %s.\nAn error occured.  Please try again."%URL
        #    wx.CallAfter(self.Error, text, "Enter Venue Error")
            

    def ExitVenue(self):
        wx.CallAfter(self.__CleanUp)
        wx.CallAfter(self.venueAddressBar.SetTitle,
                    "You are not in a venue",
                    'Click "Go" to connect to the venue, which address is displayed in the address bar')

        # Don't clear text panel when exiting venue
        #wx.CallAfter(self.textClientPanel.Clear)

        # Disable menus
        wx.CallAfter(self.__HideMenu)
        
        # Stop shared applications
        self.controller.StopApplications()


    def HandleError(self,err):
        if isinstance(err,DisconnectError):
            wx.CallAfter(MessageDialog, None, 
                        "Your connection to the venue is interrupted and you will be removed from the venue.  \nTry to connect again.", 
                        "Lost Connection")
        elif isinstance(err,UserWarning):
            wx.CallAfter(MessageDialog,None,str(err), "Warning")
        else:
            log.info("Unhandled observer exception in VenueClientUI")
            
    def UpdateMulticastStatus(self,status):
        wx.CallAfter(self.__SetMcastStatus,status)


    # end Implementation of VenueClientObserver
    #
    ############################################################################



################################################################################
#
# VenueClient UI components
#
################################################################################


################################################################################
#
# Venue Address Bar
class VenueAddressBar(wx.SashLayoutWindow):
    ID_GO = wx.NewId()
    ID_BACK = wx.NewId()
    ID_ADDRESS = wx.NewId()
    
    def __init__(self, parent, id, venuesList, defaultVenue):
        wx.SashLayoutWindow.__init__(self, parent, id,
                                    wx.DefaultPosition, 
                                    wx.DefaultSize)
        self.parent = parent
        self.addressPanel = wx.Panel(self, -1, style = wx.RAISED_BORDER)
        self.titlePanel =  wx.Panel(self, -1, style = wx.RAISED_BORDER)
        self.title = wx.StaticText(self.titlePanel, wx.NewId(),
                                  'You are not in a venue',
                                  style = wx.ALIGN_CENTER)
        font = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL, False)
        self.title.SetFont(font)
        self.address = wx.ComboBox(self.addressPanel, self.ID_ADDRESS,
                                  defaultVenue,
                                  choices = venuesList.keys(),
                                  style = wx.CB_DROPDOWN)
        if IsLinux() or IsFreeBSD():
            self.goButton = wx.Button(self.addressPanel, self.ID_GO, "Go",
                                     wx.DefaultPosition, wx.Size(38, 27))
        else:
            self.goButton = wx.Button(self.addressPanel, self.ID_GO, "Go",
                                     wx.DefaultPosition, wx.Size(40, 21))
        self.goButton.SetToolTip(wx.ToolTip("Enter venue"))
        if IsLinux() or IsFreeBSD():
            self.backButton = wx.BitmapButton(self.addressPanel, self.ID_BACK ,
                                             icons.getPreviousBitmap(),
                                             wx.DefaultPosition, wx.Size(38, 27))
        else:
            self.backButton = wx.BitmapButton(self.addressPanel, self.ID_BACK ,
                                             icons.getPreviousBitmap(),
                                             wx.DefaultPosition, wx.Size(40, 21))
        self.backButton.SetToolTip(wx.ToolTip("Go to previous venue"))
        self.backButton.Hide() #newui
        self.titlePanel.Hide()

        self.__Layout()
        self.__AddEvents()
        
        

    def __AddEvents(self):
        wx.EVT_BUTTON(self, self.ID_GO, self.CallAddress)
        wx.EVT_BUTTON(self, self.ID_BACK, self.GoBack)
        wx.EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.CallAddress)
        wx.EVT_SIZE(self,self.__OnSize)
        
                     
    def __OnSize(self,event):
        self.__Layout()
        
    def __FixSpaces(self, url):
        index = 0
        for c in url:
            if c != ' ':
                break
            index = index + 1

        return url[index:]
                                      
    def SetAddress(self, url):
        self.address.SetValue(url)

    def SetTitle(self, name, description):
        name = name.replace("&", "&&")
        self.title.SetLabel(name)
        self.titlePanel.SetToolTipString(description)
        self.parent.SetTitle(name + ' - Venue Client')
        self.__Layout()

    def AddChoice(self, url):
        if self.address.FindString(url) == wx.NOT_FOUND:
            self.address.Append(url)
        self.SetAddress(url)
            
    def __Layout(self):
        venueServerAddressBox = wx.BoxSizer(wx.VERTICAL)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        #box.Add(self.backButton, 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER, 5)  # newui
        box.Add(self.address, 1, wx.RIGHT, 5)
        #box.Add(self.address2, 1, wx.RIGHT|wx.EXPAND, 5)
        box.Add(self.goButton, 0, wx.RIGHT|wx.ALIGN_CENTER, 5)
        self.addressPanel.SetSizer(box)

        venueServerAddressBox.Add(self.addressPanel, 0, wx.EXPAND)        
        w,h = self.GetSizeTuple()
        self.SetSizer(venueServerAddressBox)
        self.GetSizer().SetDimension(5,5,w-10,h-10)

        self.Layout()
        
        
    def GoBack(self, event):
        self.parent.GoBackCB()

    def CallAddress(self, event = None):
        url = self.address.GetValue()
        venueUri = self.__FixSpaces(url)

        
        self.parent.EnterVenueCB(venueUri)

        
    
################################################################################
#
# Venue List Panel

class VenueListPanel(wx.SashLayoutWindow):
    '''VenueListPanel. 
    
    The venueListPanel contains a list of connected venues/exits to
    current venue.  By clicking on a door icon the user travels to
    another venue/room, which contents will be shown in the
    contentListPanel.  By moving the mouse over a door/exit
    information about that specific venue will be shown as a tooltip.
    The user can close the venueListPanel if exits/doors are
    irrelevant to the user and the application will extend the
    contentListPanel.  The panels is separated into a panel containing
    the close/open buttons and a VenueList object containing the
    exits.
    '''
    
    def __init__(self, parent, id, app):
        wx.SashLayoutWindow.__init__(self, parent, id)
        self.parent = parent
        self.app = app
        self.choices = {'Exits':Preferences.EXITS,
                   'All Venues':Preferences.ALL_VENUES,
                   'My Venues':Preferences.MY_VENUES}
        self.viewSelector = wx.ComboBox(self,-1,choices=self.choices.keys(),
                                       style=wx.CB_READONLY)
        defaultChoice = self.choices.keys()[0]
        dm = self.app.venueClient.GetPreferences().GetPreference(Preferences.DISPLAY_MODE)
        for k,v in self.choices.items():
            if dm == v:
                defaultChoice = k
        self.viewSelector.SetValue(defaultChoice)
        self.list = NavigationPanel(self, app)
                
        self.__Layout()
        self.__AddEvents()
        self.__SetProperties()

    def __SetProperties(self):
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, 0, "verdana")
                
    def __AddEvents(self):
        wx.EVT_SIZE(self,self.__OnSize)
        wx.EVT_COMBOBOX(self,self.viewSelector.GetId(),self.__OnViewSelect)
    
    def __OnSize(self,evt):
        self.__Layout()
        
    def __OnViewSelect(self,event):
        displayMode = self.GetDisplayMode()
        self.list.UpdateView(displayMode)
        
    def GetDisplayMode(self):
        selected = self.viewSelector.GetValue()
        displayMode = self.choices[selected]
        return displayMode

    def FixDoorsLayout(self):
        self.__Layout()
    
    def __Layout(self):
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        panelSizer.Add(self.viewSelector, 1, wx.EXPAND)

        venueListPanelSizer = wx.BoxSizer(wx.VERTICAL)
        venueListPanelSizer.Add(panelSizer, 0, wx.EXPAND)
        venueListPanelSizer.Add(self.list, 1, wx.EXPAND)

        self.SetSizer(venueListPanelSizer)
        w,h = self.GetSizeTuple()
        self.GetSizer().SetDimension(5,5,w-10,h-7)

    def Hide(self):
        currentHeight = self.GetSize().GetHeight()
        self.viewSelector.Hide()
        s = wx.Size(180, 1000)
        self.parent.UpdateLayout(self, s)
       
    def Show(self):
        currentHeight = self.GetSize().GetHeight()
        self.viewSelector.Show()
        s = wx.Size(180, 1000)
        self.parent.UpdateLayout(self, s)
  
    def CleanUp(self):
        self.list.CleanUp()
        
    def AddVenueDoor(self,connectionDescription):
        self.list.AddVenueDoor(connectionDescription)

    def AddConnections(self, connections=[]):
        try:
            displayMode = self.GetDisplayMode()
            log.info('AddConnections:  displayMode = %s', displayMode)
            
            if displayMode == Preferences.EXITS or displayMode == Preferences.ALL_VENUES:
                self.list.UpdateView(venues=connections)
        except:
            log.exception('Error updating connections list')
        
    def RemoveVenueDoor(self,connectionDescription):
        self.list.RemoveVenueDoor(connectionDescription)

class NavigationPanel(wx.Panel):
    ID_EXITS = wx.NewId()
    ID_MY_VENUES = wx.NewId()
    ID_ALL = wx.NewId()
    
    def __init__(self, parent, app):
        wx.Panel.__init__(self, parent, -1, size=wx.Size(175, 300))
        self.tree = wx.TreeCtrl(self, wx.NewId(), wx.DefaultPosition, 
                               wx.DefaultSize, style = wx.TR_HAS_BUTTONS |
                               wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT |
                               wx.TR_SINGLE )
        self.app = app
        self.parent = parent

        
        wx.EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        wx.EVT_LEFT_DOWN(self.tree, self.OnLeftDown)
        wx.EVT_RIGHT_DOWN(self.tree, self.OnRightDown)
        wx.EVT_MENU(self, self.ID_EXITS, self.OnExitsMenu)
        wx.EVT_MENU(self, self.ID_MY_VENUES, self.OnMyVenuesMenu)
        wx.EVT_MENU(self, self.ID_ALL, self.OnAllMenu)
        wx.EVT_SIZE(self, self.__OnSize)
        
        self.root = self.tree.AddRoot("ROOT")
        self.UpdateView()
        self.__Layout()
        
        self.menu = wx.Menu()
        self.addToMyVenuesId = wx.NewId()
        self.menu.Append(self.addToMyVenuesId,'Add to My Venues')
        wx.EVT_MENU(self.menu,self.addToMyVenuesId,self.__OnAddToMyVenues)

    def __OnSize(self, event):
        self.__Layout()
        
    def OnExitsMenu(self, event):
        self.UpdateView(Preferences.EXITS)
        
    def OnMyVenuesMenu(self, event):
        self.UpdateView(Preferences.MY_VENUES)
        
    def OnAllMenu(self, event):
        self.UpdateView(Preferences.ALL_VENUES)
        
    def __OnAddToMyVenues(self,event):
        itemId = self.tree.GetSelection()
        venue = self.tree.GetPyData(itemId)
        self.app.AddToMyVenuesCB(url=venue.uri,name=venue.name)
        
  
    def OnDoubleClick(self, event):
        '''
        Called when user double clicks the tree.
        '''
        self.x = event.GetX()
        self.y = event.GetY()
        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))

        # Check to see if the click was made on the tree item text.
        if not treeId.IsOk() or not flag & wx.TREE_HITTEST_ONITEMLABEL:
            return

        wx.BeginBusyCursor()
        venue = self.tree.GetPyData(treeId)
        self.app.EnterVenueCB(venue.uri)
        wx.EndBusyCursor()

    def OnRightDown(self, event):
        """
        Called when user right clicks the tree to retrieve information on the next venue
        """
        self.x = event.GetX()
        self.y = event.GetY()

        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))

        # Check to see if the click hit the twist button
        
        #if not treeId.IsOk() or not(flag & wx.TREE_HITTEST_ONITEMBUTTON):
        #    print "Exit handler!"
        #    return

        wx.BeginBusyCursor()
        venue = self.tree.GetPyData(treeId)
        wx.EndBusyCursor()
        
        localVenueProxy = VenueIW(venue.uri)
        venueState = localVenueProxy.GetState()
        
        message = "Name: " + venueState.description.name
        message = "Description: " + venueState.description
        #for stream in venueDesc.streams
        #    message = Stream: stream.name + stream.capability.type
    
        
        headline = "Information for venue: " + self.tree.GetPyData(treeId).name

        wx.MessageBox(message, headline,wx.OK)

        
        
        
                
    def OnLeftDown(self, event):
        '''
        Called when user clicks the tree
        '''
        
        self.x = event.GetX()
        self.y = event.GetY()
        exits = None

        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))

        # Check to see if the click hit the twist button
        
        if not treeId.IsOk():
            return
            
        if not(flag & wx.TREE_HITTEST_ONITEMBUTTON):
            self.tree.SelectItem(treeId)
            return

        child, cookie = self.tree.GetFirstChild(treeId)
       
        if self.tree.GetItemText(child) == "temp node":
            # Remove temporary node
            self.tree.DeleteChildren(treeId)

        venue = self.tree.GetPyData(treeId)

        exits = None
        if venue:
            exits = VenueIW(str(venue.uri)).GetConnections()
        else:
            # If we did not get click on a venue, ignore
            return
            
        if not exits:
            exits = []

        self.tree.DeleteChildren(treeId)

        for exit in exits:
            newItem = self.tree.AppendItem(treeId,exit.name)

            # Add temporary node to always show + and - buttons.
            tempItem = self.tree.AppendItem(newItem, "temp node")
            self.tree.SetItemBold(newItem)
            self.tree.SetItemData(newItem, wx.TreeItemData(exit)) 
                       
        event.Skip()
                               
    def OnRightDown(self, event):
        '''
        Called when user clicks the tree
        '''
        
        self.x = event.GetX()
        self.y = event.GetY()
        exits = None

        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))

        # Check to see if the click hit the twist button
        
        if not treeId.IsOk():
            return
            
        if not(flag & wx.TREE_HITTEST_ONITEMBUTTON):
            self.tree.SelectItem(treeId)
        
        self.tree.PopupMenu(self.menu)


    def AddVenueDoor(self, venue):
        '''
        Add a new entry in the list of venues.
        '''
        newItem = self.tree.AppendItem(self.tree.GetRootItem(), venue.name)
        
        # Add temporary node to always show + and - buttons.
        tempItem = self.tree.AppendItem(newItem, "temp node")
        self.tree.SetItemBold(newItem)
        self.tree.SetItemData(newItem, wx.TreeItemData(venue)) 
      
 
    def UpdateView(self, displayMode = None, venues=None):
        '''
        Add entries to the list of venues depending on preferences. 
        '''
        self.CleanUp()
        
        dm = displayMode
        
        if not dm:
            dm = self.parent.GetDisplayMode()
        
        # Show my venues
        if dm == Preferences.MY_VENUES:
            myVenues = self.app.controller.GetMyVenues()
            venues = []
            for venue in myVenues.keys():
                cd = VenueDescription(name = venue, uri = myVenues[venue])
                venues.append(cd)

            self.parent.viewSelector.SetValue("My Venues")

        # Show all venues on this server
        elif dm == Preferences.ALL_VENUES:
            venues = self.app.controller.GetVenuesFromServer(self.app.venueClient.GetVenueServer())
            self.parent.viewSelector.SetValue("All Venues")

        # Show connections to this venue
        elif dm == Preferences.EXITS:
            if not venues:
                # if exits not passed in, retrieve them from the venue
                venues = self.app.controller.GetVenueConnections(self.app.venueClient.GetVenue())
            self.parent.viewSelector.SetValue("Exits")

        if venues:
            for venue in venues:
                self.AddVenueDoor(venue)
            self.tree.SortChildren(self.tree.GetRootItem())

    def CleanUp(self):
        '''
        Remove all tree entries
        '''
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("ROOT")
        self.__Layout()
        
    def __Layout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)

        w,h = self.GetSizeTuple()
        self.GetSizer().SetDimension(0,0,w,h)
        

#############################################################################
#
# Content List Panel

class ContentListPanel(wx.Panel):                   
    '''ContentListPanel.
    
    The contentListPanel represents current venue and has information
    about all participants in the venue, it also shows what data and
    services are available in the venue, as well as nodes connected to
    the venue.  It represents a room, with its contents visible for
    the user.
    
    '''
    PARTICIPANTS_HEADING = 'Participants'
    DATA_HEADING = 'Data'
    SERVICES_HEADING = 'Services'
    APPLICATIONS_HEADING = 'Application Sessions'
    
    #Modified by NA2-HPCE
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, wx.DefaultPosition, 
                         wx.Size(225, 300), style = wx.SUNKEN_BORDER)
        id = wx.NewId()
        self.participantDict = {}
        self.dataDict = {}
        self.serviceDict = {}
        self.applicationDict = {}
        self.personalDataDict = {}
        self.temporaryDataDict = {}
        self.parent = parent
        #Added by NA2-HPCE
        self.selectedTreeItem = None
        self.selectedTreeItemText = None
        self.selectedTwig = None
        self.parent_item = None
        self.curItemId = None
        self.curTwig=None
        self.recursionCount = 0

        self.tree = wx.TreeCtrl(self, id, wx.DefaultPosition, 
                               wx.DefaultSize, style = wx.TR_HAS_BUTTONS |
                               wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT |
                               wx.TR_MULTIPLE)
        
        self.__SetImageList()
        self.__SetTree()
               
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        wx.EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        wx.EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown)
        wx.EVT_TREE_ITEM_EXPANDING(self.tree, id, self.OnExpand)
        #wx.EVT_TREE_BEGIN_DRAG(self.tree, id, self.OnBeginDrag) 
        wx.EVT_TREE_SEL_CHANGED(self.tree, id, self.OnSelect)
       
    def __SetImageList(self):
        imageSize = 22

        wx.InitAllImageHandlers()
        imageList = wx.ImageList(imageSize,imageSize)

        bm = icons.getBulletBitmap()
        self.bullet = imageList.Add(bm)
                
        bm = icons.getDefaultParticipantBitmap()
        self.participantId = imageList.Add(bm)
               
        bm = icons.getDefaultDataBitmap()
        self.defaultDataId = imageList.Add(bm)
        
        bm = icons.getFolderBitmap()
        self.folderId = imageList.Add(bm)
        
        bm = icons.getDefaultServiceBitmap()
        self.serviceId = imageList.Add(bm)
        self.applicationId = imageList.Add(bm)
        
        bm = icons.getDefaultNodeBitmap()
        self.nodeId = imageList.Add(bm)
                
        self.tree.AssignImageList(imageList)

    def __GetPersonalDataFromItem(self, treeId):
        # Get data for this id
        dataList = []
        cookie = 0
        
        if(self.tree.GetChildrenCount(treeId)>0):
            if WXVERSION[0] <= 2 and WXVERSION[1] <= 4:
                id, cookie = self.tree.GetFirstChild(treeId, cookie)
            else:
                id, cookie = self.tree.GetFirstChild(treeId)
            d = self.tree.GetPyData(id)
            if d:
                dataList.append(d)
                for nr in range(self.tree.GetChildrenCount(treeId)-1):
                    id, cookie = self.tree.GetNextChild(treeId, cookie)
                    dataList.append(self.tree.GetPyData(id))
                    
        return dataList
            
    def __SetTree(self):
        index = self.bullet
              
        self.root = self.tree.AddRoot("")
               
        self.participants = self.tree.AppendItem(self.root,
                                                 self.PARTICIPANTS_HEADING,
                                                 index, index)
        self.data = self.tree.AppendItem(self.root, self.DATA_HEADING, index,
                                         index) 
        self.services = self.tree.AppendItem(self.root, self.SERVICES_HEADING,
                                             index, index)
        self.applications = self.tree.AppendItem(self.root,
                                                 self.APPLICATIONS_HEADING,
                                                 index, index)
       
        self.tree.SetItemBold(self.participants)
        self.tree.SetItemBold(self.data)
        self.tree.SetItemBold(self.services)
        self.tree.SetItemBold(self.applications)
      
        colour = wx.TheColourDatabase.FindColour("NAVY")
        self.tree.SetItemTextColour(self.participants, colour)
        self.tree.SetItemTextColour(self.data, colour)
        self.tree.SetItemTextColour(self.services, colour)
        self.tree.SetItemTextColour(self.applications, colour)
               
        self.tree.Expand(self.participants)
      
    def GetLastClickedTreeItem(self):
        # x and y is set when we right click on a participnat
        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))
        if treeId.IsOk():
            item = self.tree.GetItemData(treeId).GetData()
        else:
            item = None
            
        return item
        
    def GetSelections(self):
        return self.tree.GetSelections()

    def GetItemData(self,itemId):
        return self.tree.GetItemData(itemId)
        
        
    def AddParticipant(self, profile, dataList = []):
          
        # Bail out if this is a Jabber profile already in the list      
        if profile.profileType == 'jabber':
            name = profile.name.strip()
            currentNames = map(lambda p: self.tree.GetItemText(p),self.participantDict.values())
            if name in currentNames:
                return
                
        # If this is an AG user profile, and a same-named Jabber profile
        # already exists in the list, replace it (by removing the Jabber entry
        # and then proceeding with this Add)
        if profile.profileType == 'user':
            name = profile.name.strip()
            foundItems = filter(lambda p: self.tree.GetItemText(p) == name,self.participantDict.values())
            for item in foundItems:
                item_profile = self.tree.GetItemData(item).GetData()
                if item_profile.profileType == 'jabber':
                    self.tree.Delete(item)
        
        # Determine which image to use for participant
        imageId = None
        if profile.profileType == "user" or profile.profileType == 'jabber':
            imageId =  self.participantId
        elif profile.profileType == "node":
            imageId = self.nodeId
        else:
            log.exception("ContentListPanel.AddParticipant: The user type is not a user nor a node, something is wrong")

        # Add the participant to the list
        participant = self.tree.AppendItem(self.participants, profile.name, 
                                           imageId, imageId)
        self.tree.SetItemData(participant, wx.TreeItemData(profile)) 
        if profile.profileType == 'jabber':
            GRAY = wx.Colour(100,100,100)
            self.tree.SetItemTextColour(participant,GRAY)
        self.participantDict[profile.connectionId] = participant
        
        # Always sort and expand the participant list
        self.tree.SortChildren(self.participants)
        self.tree.Expand(self.participants)
            
    def RemoveParticipant(self, profile):
        log.debug("ContentListPanel.RemoveParticipant: Remove participant")
        if profile!=None :
            if(self.participantDict.has_key(profile.connectionId)):
                log.debug("ContentListPanel.RemoveParticipant: Found participant in tree")
                id = self.participantDict[profile.connectionId]

                if id!=None:
                    log.debug("ContentListPanel.RemoveParticipant: Removed participant from tree")
                    self.tree.Delete(id)

                log.debug("ContentListPanel.RemoveParticipant: Delete participant from dictionary")
                del self.participantDict[profile.connectionId]
                          
    def ModifyParticipant(self, profile):
        log.debug('ContentListPanel.ModifyParticipant: Modify participant')
        personalData = []
        if self.participantDict.has_key(profile.connectionId):
            id = self.participantDict[profile.connectionId]
            personalData = self.__GetPersonalDataFromItem(id)
       
        self.RemoveParticipant(profile)
        self.AddParticipant(profile, personalData)

    #Modified by NA2-HPCE
    def AddData(self, dataDescription):
        #if venue data
        #if(dataDescription.type == 'None' or dataDescription.type == None):
            #dataId = self.tree.AppendItem(self.data, dataDescription.name,
                                      #self.defaultDataId, self.defaultDataId)
            #self.tree.SetItemData(dataId, wx.TreeItemData(dataDescription)) 
            #self.dataDict[dataDescription.id] = dataId
            #self.tree.SortChildren(self.data)
            #self.tree.Refresh()
            
            
        log.debug("ContentListPanel.AddData: profile.type = %s" %dataDescription.GetObjectType())
        log.debug("Id of DataDescription: %s", dataDescription.GetId())
        
        #Added by NA2-HPCE
        # Quite a dirty hack
        # Check if it is a Directory and if so
        # call the fitting AddDir() method
        # This is just to make sure Directories are handled properly
        # Normally the AddDir() should be called directly
        # by event flow.
        if dataDescription.IsOfType(DataDescription.TYPE_DIR):
            self.AddDir(dataDescription)
            return
        

        #if venue data
        if(dataDescription.type == 'None' or dataDescription.type == None):
            log.debug("ContentListPanel.AddData: This is venue data")
                
            try:
                locKey = dataDescription.GetParentId()
            except:
                log.error("Your version of AccessGrid is not capable of the hierarchical data structure support!")
                return
            
            # replace http-encoded spaces with spaces;
            # this should be done elsewhere, but is done here for now
            if not dataDescription.uri == None:
                dataDescription.uri = dataDescription.uri.replace('%20',' ')
            
            self.GetValidTreeEntry(locKey)

            self.selectedTwig = self.curTwig
            if self.selectedTwig == None:
                name = ":-(  %s  )-: " %dataDescription.name
                dataId = self.tree.AppendItem(self.data, name,self.defaultDataId, self.defaultDataId)
                self.selectedTwig = self.data
            else:       
                dataId = self.tree.AppendItem(self.selectedTwig, dataDescription.name, self.defaultDataId, self.defaultDataId)
                
            self.tree.SetItemData(dataId, wx.TreeItemData(dataDescription)) 
            self.dataDict[dataDescription.id] = dataId
            self.tree.SortChildren(self.data)
            self.tree.Refresh()
            self.tree.Expand(self.data)
            
    #Added by NA2-HPCE
    def AddDir(self, dataDescription):
        log.debug("ContentListPanel.AddDir: profile.type = %s" %dataDescription.GetObjectType())
        log.debug("Id of DirDecsription %s ", dataDescription.GetId())

        #if venue data
        log.debug("ContentListPanel.AddDir: This is venue data")
        log.debug("Search for parent of directory: %s", dataDescription.GetName())
        self.GetValidTreeEntry(dataDescription.GetParentId())
        self.selectedTwig = self.curTwig
        log.debug("Twig to add %s -dir to is",dataDescription.GetName())
        if self.selectedTwig == None:
            name = ":-(  %s  )-: " %dataDescription.name
            dataId = self.tree.AppendItem(self.data, name,
                                      self.folderId, self.folderId)
            self.selectedTwig = self.data
        else:
            dataId = self.tree.AppendItem(self.selectedTwig, dataDescription.name,
                                          self.folderId, self.folderId)
            
        treeItem = wx.TreeItemData(dataDescription)
        self.tree.SetItemData(dataId, treeItem) 
        self.dataDict[dataDescription.id] = dataId
        self.tree.SortChildren(self.selectedTwig)
        self.tree.Refresh()
        self.tree.Expand(self.data)     
            
       
    def UpdateData(self, dataDescription):
        id = None

        #if venue data
        if(self.dataDict.has_key(dataDescription.id)):
            log.debug("ContentListPanel.UpdateData: DataDict has data")
            id = self.dataDict[dataDescription.id]
            
        if(id != None):
            self.tree.SetItemData(id, wx.TreeItemData(dataDescription))
            self.tree.SetItemText(id, dataDescription.name)
        else:
            log.info("ContentListPanel.UpdateData: Id is none - that is not good")
                          
    def RemoveData(self, dataDescription):
        #if venue data
        id = None
        ownerId = None

        if(self.dataDict.has_key(dataDescription.id)):
            # venue data
            log.debug("ContentListPanel.RemoveData: Remove venue data")
            id = self.dataDict[dataDescription.id]
            del self.dataDict[dataDescription.id]
            

        else:
            log.info("ContentListPanel.RemoveData: No key matches, can not remove data")
           
        if(id != None):
            self.tree.Delete(id)
        
        #Added by NA2-HPCE    
    def RemoveDir(self, data):
        #if venue data
        id = None
        
        if(self.dataDict.has_key(data.id)):
            # venue data
            log.debug("ContentListPanel.RemoveDir: Remove venue directory")
            id = self.dataDict[data.id]
            del self.dataDict[data.id]
            

        else:
            log.info("ContentListPanel.RemoveDir: No key matches, can not remove data")
           
        if(id != None):
            self.tree.Delete(id)

    def AddService(self, serviceDescription):
        service = self.tree.AppendItem(self.services, serviceDescription.name,
                                      self.serviceId, self.serviceId)
        self.tree.SetItemData(service, wx.TreeItemData(serviceDescription)) 
        self.serviceDict[serviceDescription.id] = service
        self.tree.SortChildren(self.services)
        self.tree.Refresh()
        
    def UpdateService(self, serviceDescription):
        if(self.serviceDict.has_key(serviceDescription.id)):
            self.RemoveService(serviceDescription)
            self.AddService(serviceDescription)
                                           
    def RemoveService(self, serviceDescription):
        if(self.serviceDict.has_key(serviceDescription.id)):
            id = self.serviceDict[serviceDescription.id]
            del self.serviceDict[serviceDescription.id]
            if(id != None):
                self.tree.Delete(id)
        else:
            # Legacy code: Accomodate old (2.1.2 and before) servers
            # Tear this code out as soon as possible
            for id,itemId in self.serviceDict.items():
                itemServiceDesc = self.tree.GetItemData(itemId).GetData()
                if itemServiceDesc.name == serviceDescription.name:
                    del self.serviceDict[id]
                    self.tree.Delete(itemId)

    def AddApplication(self, appDesc):
        application = self.tree.AppendItem(self.applications, appDesc.name,
                                           self.applicationId,
                                           self.applicationId)
        self.tree.SetItemData(application, wx.TreeItemData(appDesc))
        self.applicationDict[appDesc.uri] = application
        self.tree.SortChildren(self.applications)
        self.tree.Refresh()
      
    def UpdateApplication(self, appDesc):
        if(self.applicationDict.has_key(appDesc.uri)):
            self.RemoveApplication(appDesc)
            self.AddApplication(appDesc)
                   
    def RemoveApplication(self, appDesc):
        if(self.applicationDict.has_key(appDesc.uri)):
            id = self.applicationDict[appDesc.uri]
            del self.applicationDict[appDesc.uri]
            if(id != None):
                self.tree.Delete(id)

    def UnSelectList(self):
        self.tree.Unselect()

    def __Layout(self):
        mainBox=wx.BoxSizer(wx.HORIZONTAL)
        mainBox.Add(self.tree,1,wx.EXPAND)
        self.SetSizer(mainBox)
        self.Layout()

    def OnSize(self, event):
        self.__Layout()
        #w,h = self.GetClientSizeTuple()
        #self.tree.SetDimensions(0, 0, w, h)
        
    def OnKeyDown(self, event):
        key = event.GetKeyCode()
      
        if key == wx.WXK_DELETE:
            treeIdList = self.tree.GetSelections()

            for treeId in treeIdList:
                item = self.tree.GetItemData(treeId).GetData()
                
                if item:
                    if isinstance(item,DataDescription):
                        # data
                        self.parent.RemoveDataCB(event)
                    elif isinstance(item,ServiceDescription):
                        # service
                        self.parent.RemoveServiceCB(event)
                    elif isinstance(item,ApplicationDescription):
                        # application
                        self.parent.RemoveApplicationCB(event)


    def OnSelect(self, event):
        pass
        #
        # Due to a bug in wxPython, we need a root item to be able to display
        # twist buttons correctly.  If the root item is selected, the ui looks
        # weird so change selection to the participant heading instead.
        #
        #if IsWindows():
        #    item = event.GetItem()
        #    
        #    # Root item
        #    if self.tree.GetItemText(item) == "":
        #        self.tree.SelectItem(self.participants)

    def OnBeginDrag(self, event):
        '''
        Called when a tree item is being dragged.
        '''
        
        item = event.GetItem()
              
        # Check to see if it is a data item we are trying to drag.
        text = self.tree.GetItemText(item)
        dropData = wx.TextDataObject()
        dropData.SetText(text)

        dropSource = wx.DropSource(self)
        dropSource.SetData(dropData)

        dropSource.DoDragDrop(wx.Drag_AllowMove)
    
    #Modified by NA2-HPCE                            
    def OnExpand(self, event):
        treeId = event.GetItem()
        item = self.tree.GetItemData(treeId).GetData()

        if item:
            if not isinstance(item, DataDescription):
                try:
                    dataDescriptionList = self.parent.GetPersonalData(item)
                              
                    if dataDescriptionList:
                        for data in dataDescriptionList:
                            self.AddData(data)
                except:
                    log.exception("ContentListPanel.OnExpand: Could not get personal data.")
                    MessageDialog(None, "%s's data could not be retrieved."%item.name)
            else:
                pass
                
    def OnDoubleClick(self, event):
        mimeConfig = Config.MimeConfig.instance()
        self.x = event.GetX()
        self.y = event.GetY()
        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))
        ext = None
        name = None
        
        if(treeId.IsOk() and flag & wx.TREE_HITTEST_ONITEMLABEL):
            item = self.tree.GetItemData(treeId).GetData()
            text = self.tree.GetItemText(treeId)
            if item == None:
                pass

            elif isinstance(item,ClientProfile):
                if item.connectionId == self.parent.GetProfile().connectionId:
                    self.parent.EditProfileCB()
                else:
                    self.parent.ViewProfileCB()

            else:
                commands = self.parent.GetCommands(item)
                if commands.has_key('Open'):
                    # Open the given item
                    self.parent.StartCmd(item,verb='Open')
                else:
                    # Handle items with no 'Open' action
                    if(isinstance(item,DataDescription) or 
                       isinstance(item,ServiceDescription)):
                        self.FindUnregistered(item)
                    else:
                        # Notify user of no application client
                        self.parent.Notify("You have no client for this Shared Application.", 
                                    "Notification")
    
    #Modified by NA2-HPCE            
    def OnRightClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()

        if self.parent.GetVenue() == None:
            return
        
        treeId, flag = self.tree.HitTest(wx.Point(self.x,self.y))
        item = self.tree.GetItemData(treeId).GetData()
        text = self.tree.GetItemText(treeId)
        self.curItemId = treeId
        self.selectedTwig = treeId
        self.selectedTreeItem = item
        self.selectedTreeItemText = text
      
        if(treeId.IsOk()):

            # do the right thing in case of Shift or Ctrl (or Cmd)
            if not event.ShiftDown() and not event.CmdDown():
                self.tree.UnselectAll()
            if not self.tree.IsSelected(treeId):
                self.tree.SelectItem(treeId)
                
            item = self.tree.GetItemData(treeId).GetData()
            text = self.tree.GetItemText(treeId)
                        
            if text == self.DATA_HEADING:
                self.PopupMenu(self.parent.dataHeadingMenu,
                               wx.Point(self.x, self.y))
            elif text == self.SERVICES_HEADING:
                self.PopupMenu(self.parent.serviceHeadingMenu,
                               wx.Point(self.x, self.y))
            elif text == self.APPLICATIONS_HEADING:
                self.PopupMenu(self.parent.BuildAppMenu("Add "),
                               wx.Point(self.x, self.y))
            elif text == self.PARTICIPANTS_HEADING or item == None:
                # We don't have anything to do with this heading
                pass
            
            #elif isinstance(item, AGNetworkServiceDescription):
            #    menu = self.BuildNetworkServiceMenu(event, item)
            #    self.PopupMenu(menu, wx.Point(self.x, self.y))
            
            elif isinstance(item, ServiceDescription):
                menu = self.BuildServiceMenu(event, item)
                self.PopupMenu(menu, wx.Point(self.x,self.y))

            elif isinstance(item, ApplicationDescription):
                menu = self.BuildAppMenu(item)
                self.PopupMenu(menu, wx.Point(self.x, self.y))

            elif isinstance(item, DataDescription):
                menu = self.BuildDataMenu(event, item)
                self.PopupMenu(menu, wx.Point(self.x,self.y))
                parent = self.tree.GetItemParent(treeId)
                
            elif isinstance(item,ClientProfile):
                log.debug("ContentListPanel.OnRightClick: Is this me? connectionId is = %s, my id = %s "
                          % (item.connectionId, self.parent.GetProfile().connectionId))
                if(item.connectionId == self.parent.GetProfile().connectionId):
                    log.debug("ContentListPanel.OnRightClick: This is me")
                    self.PopupMenu(self.parent.meMenu, wx.Point(self.x, self.y))
         
                else:
                    log.debug("ContentListPanel.OnRightClick: This is a user")
                    self.PopupMenu(self.parent.participantMenu,
                                   wx.Point(self.x, self.y))
                 
    #Added by NA2-HPCE
    def SetVenueProxy(self, proxy):
        self.__venueProxy = proxy    
    
    #Modified by NA2-HPCE
    def BuildDataMenu(self, event, item):
        """
        Programmatically build a menu based on the mime based verb
        list passed in.
        """

        # Path where temporary file will exist if opened/used.
        ext = item.name.split('.')[-1]

        log.debug("looking for mime commands for extension: %s", ext)
        
        # Get commands for this data type
        commands = self.parent.GetCommands(item)

        log.debug("Commands: %d %s", len(commands), str(commands))
        
        #
        # Build the menu
        # 
        menu = wx.Menu()
        
        if item.GetObjectType() == DataDescription.TYPE_DIR:
            # Code for creation of context menu for adding directories and files
             # - Add data
            id = wx.NewId()
            menu.Append(id, "Add data", "Add data to this directory")
            wx.EVT_MENU(self, id, lambda event: self.parent.AddDataCB(event))
            

            # - Add directory
            id = wx.NewId()
            menu.Append(id, "Add new directory", "Add directory to this directory")
            wx.EVT_MENU(self, id, lambda event: self.parent.AddDirCB(event))
            
            # - Add directory
            id = wx.NewId()
            menu.Append(id, "Upload directory", "Upload complete directory to this directory")
            menu.Enable(id, True)
            wx.EVT_MENU(self, id, lambda event: self.parent.UploadDirCB(event))
            
            # - Delete directory
            id = wx.NewId()
            menu.Append(id, "Delete", "Delete this directory with all contents")
            wx.EVT_MENU(self, id, lambda event: self.parent.RemoveDirCB(event))
            
                            
        else:

            # - Open
            id = wx.NewId()
            menu.Append(id, "Open", "Open this data.")
            if commands != None and commands.has_key('Open'):
                wx.EVT_MENU(self, id, lambda event,
                         cmd=commands['Open'], itm=item: 
                         self.parent.StartCmd(itm, verb='Open'))
            else:
                wx.EVT_MENU(self, id, lambda event,
                         itm=item: self.FindUnregistered(itm))
    
            # - Save
            id = wx.NewId()
            menu.Append(id, "Save", "Save this item locally.")
            wx.EVT_MENU(self, id, lambda event: self.parent.SaveDataCB(event))
            
            # - Delete
            id = wx.NewId()
            menu.Append(id, "Delete", "Delete this data from the venue.")
            wx.EVT_MENU(self, id, lambda event: self.parent.RemoveDataCB(event))
    
            # - type-specific commands
            if commands != None:
                for key in commands.keys():
                    if key != 'Open':
                        id = wx.NewId()
                        menu.Append(id, string.capwords(key))
                        wx.EVT_MENU(self, id, lambda event,
                                 verb=key, itm=item: 
                                 self.parent.StartCmd(itm, verb=verb))
    
            menu.AppendSeparator()
    
            # - Properties
            id = wx.NewId()
            menu.Append(id, "Properties", "View the details of this data.")
            wx.EVT_MENU(self, id, lambda event, item=item:
                     self.LookAtProperties(item))

        return menu

    def BuildNetworkServiceMenu(self, event, item):
        """
        Programmatically build a menu based on the mime type of the item
        passed in.
        """
       
        # Path where temporary file will exist if opened/used.
        ext = item.name.split('.')[-1]
        
        # Get commands for the service type

        commands = self.parent.GetCommands(item)

        #
        # Build the menu
        #
        menu = wx.Menu()

        # - Open
        id = wx.NewId()
               
        menu.Append(id, "Open", "Open this service.")
       
        if commands != None and commands.has_key('Open'):
            wx.EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: 
                     self.parent.StartCmd(itm, verb='Open'))
        else:
            wx.EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))
                   
        # - type-specific commands
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wx.NewId()
                    menu.Append(id, string.capwords(key))
                    wx.EVT_MENU(self, id, lambda event,
                             verb=key, itm=item: 
                             self.parent.StartCmd(itm, verb=verb))

        menu.AppendSeparator()

        # - Properties
        id = wx.NewId()
        menu.Append(id, "Properties", "View the details of this service.")
        wx.EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def BuildServiceMenu(self, event, item):
        """
        Programmatically build a menu based on the mime type of the item
        passed in.
        """
       
        # Path where temporary file will exist if opened/used.
        ext = item.name.split('.')[-1]
        
        # Get commands for the service type

        commands = self.parent.GetCommands(item)

        #
        # Build the menu
        #
        menu = wx.Menu()

        # - Open
        id = wx.NewId()
               
        menu.Append(id, "Open", "Open this service.")
       
        if commands != None and commands.has_key('Open'):
            wx.EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: 
                     self.parent.StartCmd(itm, verb='Open'))
        else:
            wx.EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))

        # - Delete
        id = wx.NewId()
        menu.Append(id, "Delete", "Delete this service from the venue.")
        wx.EVT_MENU(self, id, lambda event: self.parent.RemoveServiceCB(event))
            
        # - type-specific commands
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wx.NewId()
                    menu.Append(id, string.capwords(key))
                    wx.EVT_MENU(self, id, lambda event,
                             verb=key, itm=item: 
                             self.parent.StartCmd(itm, verb=verb))

        menu.AppendSeparator()

        # - Properties
        id = wx.NewId()
        menu.Append(id, "Properties", "View the details of this service.")
        wx.EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def FindUnregistered(self, item):
        dlg = wx.MessageDialog(None,
                        "There is nothing registered for this kind of data." \
                        "Would you like to search for a program?",
                        style = wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT)
        val = dlg.ShowModal()
        dlg.Destroy()

        if val == wx.ID_YES:
            # do the find a file thing
            wildcard = "All Files (*.*)|*.*|"\
                       "Executables (*.exe)|*.exe|"\
                       "Compiled Python Scripts (*.pyc)|*.pyc|"\
                       "Python Source Files (*.py)|*.py|"\
                       "Batch Files (*.bat)|*.bat"
            
            dlg = wx.FileDialog(None, "Choose the program", "",
                               "", wildcard, wx.OPEN)
            if dlg.ShowModal() == wx.ID_OK:
                program = dlg.GetPath()
                dlg.Destroy()
                
                # Then execute it
                if IsWindows():
                    cmd = program + " %1"
                else:
                    cmd = program + " %s"
                    
                self.parent.StartCmd(item, cmd=cmd)
                
    def BuildAppMenu(self, item):
        """
        Programmatically build a menu based on the mime based verb
        list passed in.
        """
     
        # Get the commands for this app type
        commands = self.parent.GetCommands(item)
              
        log.info("Got commands: (%s) %s" % (item.mimeType, str(commands)))
        
        #
        # Build the  menu
        #
        menu = wx.Menu()
        
        # - Open
        id = wx.NewId()
        menu.Append(id, "Open", "Open application and join the session.")

       
        if commands != None and 'Open' in commands:
            wx.EVT_MENU(self, id, lambda event, cmd='Open':
                     self.parent.StartCmd(item,verb='Open'))


            # - Open for All Participants
            key = 'Open for All Participants'
            id = wx.NewId()
            menu.Append(id, key, "Open application for all participants in the venue.")
            wx.EVT_MENU(self, id, lambda event, verb=key, itm=item:
                     self.parent.StartAllCmd(item,verb=key))
            
        else:
            text = "You have nothing configured to open this application."
            title = "Notification"
            wx.EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wx.OK|wx.ICON_INFORMATION))
       
        # - Delete
        id = wx.NewId()
        menu.Append(id, "Delete", "Delete this application.")
        wx.EVT_MENU(self, id, lambda event: self.parent.RemoveApplicationCB(event))

        menu.AppendSeparator()
            
        # - type-specific commands
        othercmds = 0
        if commands != None:
            for key in commands:
                if key != 'Open' and key != 'Open for All Participants':
                    othercmds = 1
                    id = wx.NewId()
                    menu.Append(id, string.capwords(key))
                    wx.EVT_MENU(self, id, lambda event, verb=key, itm=item:
                             self.parent.StartCmd(item,verb=verb))
        if othercmds:
            menu.AppendSeparator()

        # - Application Monitor
        id = wx.NewId()
        menu.Append(id, "Open Monitor...", 
                    "View data and participants present in this application session.")
        wx.EVT_MENU(self, id, lambda event: self.parent.MonitorAppCB(item))

        # - Application Monitor
        menu.AppendSeparator()
        
        # Add properties
        id = wx.NewId()
        menu.Append(id, "Properties", "View the details of this application.")
        wx.EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def LookAtProperties(self, desc):
        """
        """
              
        if isinstance(desc, DataDescription):
            dataView = DataPropertiesDialog(self, -1, "Data Properties")
            dataView.SetDescription(desc)
            if dataView.ShowModal() == wx.ID_OK:
                # Get new description
                newDesc = dataView.GetDescription()
                               
                # If name is different, change data in venue
                if newDesc.name != desc.name:
                    try:
                        self.parent.UpdateDataCB(newDesc)
                    except:
                        log.exception("VenueClientUIClasses: Update data failed")
                        MessageDialog(None, "Update data failed.", "Notification", 
                                      style = wx.OK|wx.ICON_INFORMATION) 
            
            dataView.Destroy()

        #elif isinstance(desc, AGNetworkServiceDescription):
        #    serviceView = ServicePropertiesDialog(self, -1, "Service Properties")
        #    serviceView.SetDescription(desc)
        #    serviceView.ShowModal()
        #    serviceView.Destroy()
            
        elif isinstance(desc, ServiceDescription):
            serviceView = ServicePropertiesDialog(self, -1, "Service Properties")
            serviceView.SetDescription(desc)
            if(serviceView.ShowModal() == wx.ID_OK):
                # Get new description
                newDesc = serviceView.GetDescription()
                newDesc.id = desc.id
              
                # If name or description is different, change the service in venue
                if newDesc.name != desc.name or newDesc.description != desc.description:
                    try:
                        self.parent.UpdateServiceCB(newDesc)
                    except:
                        log.exception("VenueClientUI: Update service failed")
                        MessageDialog(None, "Update service failed.", "Notification", 
                                      style = wx.OK|wx.ICON_INFORMATION)
                                           
            serviceView.Destroy()
        elif isinstance(desc, ApplicationDescription):
            serviceView = ApplicationPropertiesDialog(self, -1, "Application Properties")
            serviceView.SetDescription(desc)
            # Get new description
            if(serviceView.ShowModal() == wx.ID_OK):
                newDesc = serviceView.GetDescription()
              
                # If name or description is different, change the application in venue
                if newDesc.name != desc.name or newDesc.description != desc.description:
                    try:
                        self.parent.UpdateApplicationCB(newDesc)
                    except:
                        MessageDialog(None, "Update application failed.", 
                                      "Notification", style = wx.OK|wx.ICON_INFORMATION)
                                            
            serviceView.Destroy()
                
    def CleanUp(self):
    
        self.tree.DeleteAllItems()
        self.__SetTree()

        self.participantDict.clear()
        self.dataDict.clear()
        self.serviceDict.clear()
        self.applicationDict.clear()
        self.personalDataDict.clear()

    def SetDropTarget(self,dropTarget):
        self.tree.SetDropTarget(dropTarget)
        
    #Added by NA2-HPCE
    def GetValidTreeEntry(self, key):
        self.curTwig = None
        try:
            if key == '-1' or int(key) == -1:
                log.debug("Parent TreeItem is Data root!")
                self.curTwig = self.data
                return
        except ValueError:
            pass
        try:
            log.debug("Parent TreeItem is not the root!")
            self.treeroot = self.data
            fn = self.KeyCompare
            if self.traverse(self.treeroot,fn,key) == False:
                log.error("Error during data traversal!")
        except:
            log.exception("GetValidTreeEntry failed!")
            pass
        
        log.debug("Found tree item for insertion is %s", self.treeroot)
        
    #Added by NA2-HPCE  
    def traverse(self, traverseroot, function, key, cookie=0):
        """ recursivly walk tree control """
        # step in subtree if there are items or ...
        self.recursionCount = self.recursionCount + 1
        if self.tree.ItemHasChildren(traverseroot):
            firstchild, cookie = self.tree.GetFirstChild(traverseroot)
            #log.debug("ChildTraverse:Calling KeyCompare with key = %s",key)
            if not function(key, firstchild):
                self.traverse(firstchild, function, key, cookie)
            else:
                log.debug("Exited traverse! Level: %s", self.recursionCount)
                self.recursionCount = self.recursionCount -1
                return True
                

        # ... loop siblings
        # if there are no siblings, child is a invalid tree item
        # we have to catch that case by a exception block
        try:
            child = self.tree.GetNextSibling(traverseroot)
            if child:
                #log.debug("Siblingloop:Calling KeyCompare with key = %s",key)
                if not function(key, child):
                    self.traverse(child, function, key, cookie)
                else:
                    log.debug("Exited traverse! Level: %s", self.recursionCount)
                    self.recursionCount = self.recursionCount -1
                    return True
        except:
            log.debug("Didn't find a matching data description object!")
            return False

        log.debug("Exited traverse! Level: %s", self.recursionCount)
        self.recursionCount = self.recursionCount -1
        
     #Added by NA2-HPCE
    def KeyCompare(self, key, childdata):
        try:
            fc_dataobject = self.tree.GetItemData(childdata).GetData()
            if not fc_dataobject == None:
                #log.debug("Directory or Filename: %s", fc_dataobject.GetName())
                log.debug("Keys to compare: %s = %s", key, fc_dataobject.GetId())
                if key == fc_dataobject.GetId():
                    self.curTwig = childdata
                    return True 
                else:
                    return False
            else:
                return False
        except:
            log.exception("Error in Key comparision method for hierarchical data structure!")

#########################################################################
#
# Jabber Client Panel

class TextPanelSash(wx.SashLayoutWindow):
    
    def __init__(self, parent, id):
        wx.SashLayoutWindow.__init__(self, parent, id)
        self.parent = parent
        
        self.textClientPanel = JabberClientPanel(self, -1)#wx.Panel(self, -1)
        wx.EVT_SIZE(self, self.__OnSize)
        self.__Layout()

    #def GetText(self):
    #    return self.textClientPanel.GetText()
       
    def OutputText(self, name, message):
        self.textClientPanel.OutputText(name, message)
        
    def GetText(self):
        return self.textClientPanel.GetText()

    def Clear(self):
        return self.textClientPanel.Clear()

    def __OnSize(self, evt):
        self.__Layout()

    def __Layout(self):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.textClientPanel, 1, wx.EXPAND)
        w,h = self.GetSizeTuple()
        self.SetSizer(box)
        self.GetSizer().SetDimension(5,5,w-10,h-10)

class JabberClientPanel(wx.Panel):
    
    ID_BUTTON = wx.NewId()
    ID_WINDOW_TOP = wx.NewId()
    client =''

    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.sashWindow = wx.SashLayoutWindow(
            self, self.ID_WINDOW_TOP, wx.DefaultPosition, (200, 30), 
            wx.NO_BORDER)
        
        self.sashWindow.SetDefaultSize((1000, 60))
        self.sashWindow.SetOrientation(wx.LAYOUT_HORIZONTAL)
        self.sashWindow.SetAlignment(wx.LAYOUT_TOP)
        self.sashWindow.SetSashVisible(wx.SASH_BOTTOM, True)

        self.outputPanel = wx.Panel(self.sashWindow, -1)
        self.textOutput = wx.TextCtrl(self.outputPanel, wx.NewId(), "",
                                     style= wx.TE_MULTILINE | wx.TE_READONLY |
                                     wx.TE_RICH|wx.TE_AUTO_URL) 
        self.app = parent.parent
        self.panel = wx.Panel(self, -1)
        self.display = wx.Button(self.panel, self.ID_BUTTON, "Display",
                                style = wx.BU_EXACTFIT)
        self.textInput = wx.TextCtrl(self.panel, wx.NewId(), "",
                                    size = wx.Size(-1, 25),
                                    style= wx.TE_MULTILINE)
        self.panelHeight = None


        self.parent = parent
        self.display.SetToolTip(wx.ToolTip("Send text message"))
        
        self.display.Hide() # newui
        
        self.__DoLayout()

        wx.EVT_TEXT_URL(self.textOutput, self.textOutput.GetId(), self.OnUrl)
        wx.EVT_CHAR(self.textOutput, self.ChangeTextWindow)
        wx.EVT_CHAR(self.textInput, self.TestEnter) 
        wx.EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
        wx.EVT_SIZE(self, self.__OnSize)
        wx.EVT_SASH_DRAGGED(self, self.ID_WINDOW_TOP, 
                         self.__OnSashDrag)
        self.Show(True)

        self.app.venueClient.jabber.SetPanel(self)

    def __OnSashDrag(self, event):
        eID = event.GetId()
        
        maxHeight = self.GetSize().height
        
        if eID == self.ID_WINDOW_TOP:
            h =  event.GetDragRect().height
            # Do not cover output
            
            if h < 10:
                h = 10
            
            # Do not minimize input
            if maxHeight - h < 25:
                h = maxHeight - 25
            self.sashWindow.SetDefaultSize(wx.Size(1000, h))
            self.outputPanel.SetSize(wx.Size(1000, h-5))
    
        wx.LayoutAlgorithm().LayoutWindow(self, self.panel)
        self.panel.Refresh()
        self.panelHeight = self.panel.GetSize().height

        #self.__Layout()

    def __OnSize(self, event):
        # Keep input constant
        newHeight = event.GetSize().height
        if not self.panelHeight:
            self.panelHeight = self.panel.GetSize().height

        # Do not keep input constant if it is higher
        # than output.
        if newHeight >= self.panelHeight:
            sashHeight = newHeight - self.panelHeight
        else:
            sashHeight = newHeight
        
        self.sashWindow.SetDefaultSize(wx.Size(1000, sashHeight))
        self.outputPanel.SetSize(wx.Size(1000, sashHeight-5))
        wx.LayoutAlgorithm().LayoutWindow(self, self.panel)
             
    def __DoLayout(self):
        '''
        Handles UI layout.
        '''
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.textInput, 1, wx.ALIGN_CENTER | wx.EXPAND |
                wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box.Add(self.display, 0, wx.ALIGN_CENTER |wx.ALL, 2)

        self.panel.SetSizer(box)
        box.Fit(self.panel)
        self.panel.SetAutoLayout(1)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(self.textOutput, 1, wx.EXPAND)
        self.outputPanel.SetSizer(box2)
        box2.Fit(self.outputPanel)
        self.outputPanel.SetAutoLayout(1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.outputPanel, 1, wx.EXPAND)
        self.sashWindow.SetSizer(sizer)
        
    def __OutputText(self, name, message, messagetime=None):
        '''
        Prints received text in the text chat.
        **Arguments**
        *name* Statement to put in front of message (for example; "You say,").
        *message* The actual message.
        '''
        
        # no-op on null messages
        # investigate why this happens and handle it properly, it's probably state updates or somesuch
        if not message:
            return
        
        # Add time to event message
        if not messagetime:
           messagetime = localtime()
        dateAndTime = strftime("%d %b %H:%M", messagetime )
        
        # Event message
        if name == None:
            message = '%s: %s' % (dateAndTime,message)

            # Events are coloured blue
            self.textOutput.SetDefaultStyle(wx.TextAttr(wx.BLUE))
            self.textOutput.AppendText(message+'\n')
            self.textOutput.SetDefaultStyle(wx.TextAttr(wx.BLACK))

        elif name == "enter":
            # Descriptions are coloured black
            self.textOutput.SetDefaultStyle(wx.TextAttr(wx.BLACK))
            self.textOutput.AppendText(message+'\n')
        # Someone is writing a message
        else:
            # Fix for osx
            pointSize = wx.NORMAL_FONT.GetPointSize()

            # Fix for osx
            if IsOSX():
                pointSize = 12
                           
            f = wx.Font(pointSize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            textAttr = wx.TextAttr(wx.BLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)
            # Detect /me
            if message.startswith("/me ") and len(message.strip()) > 3:
                nameText = name[:-2] # remove trailing ": "
                messageText = " " + message[4:] + "\n"
            else:
                nameText = name
                messageText = message + '\n'
                
            self.textOutput.AppendText(dateAndTime + ': ')

            self.textOutput.AppendText(nameText)
          
            # Set text normal
            f = wx.Font(pointSize, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            textAttr = wx.TextAttr(wx.BLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)
            self.textOutput.AppendText(messageText)

        if IsWindows():
            # Scrolling is not correct on windows when I use
            # wx.TE_RICH flag in text output window.
            self.SetRightScroll()

    def OutputText(self, name, message, messageTime=None):
        '''
        Print received text in text chat.
        
        **Arguments**
        *name* Statement to put in front of message (for example; "You say,").
        *message* The actual message.
        '''
        wx.CallAfter(self.__OutputText, name, message,messageTime)

    def Clear(self):
        self.textOutput.AppendText("CLEAR")
        self.textOutput.Clear()
        
    def LocalInput(self, event):
        '''
        User input
        '''
        try:
            text = self.textInput.GetValue()
            sent = self.app.venueClient.jabber.SendMessage(text)
            self.textInput.Clear()
            self.textInput.SetFocus()
            if not sent:
                text = "You have to be connected to a venue to send a text message"
                title = "Not Connected"
                MessageDialog(self, text, title, style = wx.OK|wx.ICON_INFORMATION)
        except Exception, e:
            self.textInput.Clear()
            log.exception(e)
            text = "Could not send text message successfully"
            title = "Notification"
            log.error(text)
            MessageDialog(self, text, title, style = wx.OK|wx.ICON_INFORMATION)
     
    def OnCloseWindow(self):
        '''
        Perform necessary cleanup before shutting down the window.
        '''
        log.debug("JabberClientPanel.LocalInput:: Destroy chat client")
        AGClient.disconnect()
        self.Destroy()

    def TestEnter(self, event):
        '''
        Check to see what keys are pressed down when enter button is pressed.
        If cltl or shift are held down, ignore the event; the enter will then just
        switch rows in the text input field instead of sending the event.
        '''
        key = event.GetKeyCode()
        shiftKey = event.ShiftDown()
        ctrlKey = event.ControlDown()

        # If enter key is pressed, send message to
        # text output field
        if key == wx.WXK_RETURN:
            # If shift or ctrl key is pressed, ignore
            # the event and switch line in the text input
            # field.
            if shiftKey or ctrlKey:
                event.Skip()
            else:
                self.LocalInput(None)
        else:
            event.Skip()
            return

    def OnUrl(self, event):
        '''
        If a url is pressed in the text chat, this method is called to
        bring up correct web site.
        '''
        # Ignore mouse over events.
        if event.GetMouseEvent().GetButton() == wx.MOUSE_BTN_NONE:
            event.Skip()
            return

        start = event.GetURLStart()
        end = event.GetURLEnd()
        url = self.textOutput.GetRange(start, end)
        
        self.app.OpenURL(url)
      
    def ChangeTextWindow(self, event):
        '''
        If user tries to print in text output field, this method
        changes focus to text input field to make it clear for
        users where to write messages.
        '''
        key = event.GetKeyCode()
        ctrlKey = event.ControlDown()
       
        # If ctrl key is pressed, do not enter text
        # automatically into the text output field.
        if ctrlKey:
            event.Skip()
            return
        
        self.textInput.SetFocus()
        if(44 < key < 255) and not ctrlKey:
            self.textInput.AppendText(chr(key))

    def SetRightScroll(self):
        '''
        Scrolls to right position in text output field 
        '''
        # Added due to wx.Python bug. The wx.TextCtrl doesn't
        # scroll properly when the wx.TE_AUTO_URL flag is set. 
        #pos = self.textOutput.GetInsertionPoint()
        #self.textOutput.ShowPosition(pos - 1)
        self.textOutput.ScrollLines(-1)
                                            
    def ClearTextWidgets(self):
        '''
        Clears text widgets.
        '''
        self.textOutput.Clear()
        self.textInput.Clear()

    def GetText(self):
        return self.textOutput.GetValue()

    def messageCB(self, msg):
        """Called when a message is recieved"""
        if msg.getBody(): ## Dont show blank messages ##
#            print '<--' + str(msg.getFrom()) + '> ' + msg.getBody()
            OutputText("i said:", msg.getBody())


        self.client.send("/presence %s/%s unavailable" % (self.currentRoom, self.user))
        self.currentRoom = venue + "@conference.localhost"
        self.client.send("/presence %s/%s" % (self.currentRoom, self.user))
        
               

               
################################################################################
#
# Statusbar


class StatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.sizeChanged = False
        self.parent = parent
        wx.EVT_SIZE(self, self.OnSize)
        
        self.progress = wx.Gauge(self, wx.NewId(), 100,
                                style = wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.progress.SetValue(True)

        self.cancelButton = wx.Button(self, wx.NewId(), "Cancel")
        wx.EVT_BUTTON(self, self.cancelButton.GetId(), self.OnCancel)

        self.__hideProgressUI()
        self.Reset()

        self.secondFieldWidth = 100
        self.fields = 2
        self.SetFieldsCount(self.fields)
        self.SetStatusWidths([-1,self.secondFieldWidth])
        self.Reposition()

    def __hideProgressUI(self):
        self.hidden = 1
        self.progress.Hide()
        self.cancelButton.Hide()

    def __showProgressUI(self):
        self.hidden = 0
        self.progress.Show()
        self.cancelButton.Show()

    def SetMax(self, value):
        self.max = value
        
    def Reset(self):
        self.__cancelFlag = 0
        self.transferDone = 0
        self.fields = 3
        self.SetFieldsCount(self.fields)
        self.SetStatusWidths([-1,80,60])
        # set the initial position of the progress UI.
        self.Reposition()

    def SetMessage(self, text):
        self.SetStatusText(text,0)
   
    def IsCancelled(self):
        if self.__cancelFlag:
            self.__hideProgressUI()
        return self.__cancelFlag
    
    def SetProgress(self, text, value, NOT_USED, doneFlag):
              
        if self.hidden:
            self.__showProgressUI()
        
        if doneFlag:
            self.transferDone = doneFlag
            self.progress.SetValue(100)
            self.__hideProgressUI()
            self.SetMessage("Transfer complete")
            self.fields = 2
            self.SetFieldsCount(self.fields)
            self.SetStatusWidths([-1,self.secondFieldWidth])
            return 
        
        self.SetMessage(text)

        # Scale value to range 1-100
        if self.max == 0:
            value = 100
        else:
            value = int(100*value)
        self.progress.SetValue(value)

    def OnCancel(self, event):
        '''
        The cancel button was clicked.
       
        If we are still transferring, this is a cancel. 
        If we are done transferring, this is an OK.
        '''
        if not self.transferDone:
            self.__cancelFlag = 1
            self.__hideProgressUI()
            self.SetMessage("")
            self.fields = 2
            self.SetFieldsCount(self.fields)
            self.SetStatusWidths([-1,self.secondFieldWidth])
            self.Refresh()
            
    def OnSize(self, evt):
        '''
        Handles normal size events.
        '''
        self.Reposition() 
    
    def Reposition(self):
        '''
        Make sure objects are positioned correct in the statusbar.
        '''
        
        if self.fields == 2:
            self.__hideProgressUI()
            return

        # Gauge
        rect = self.GetFieldRect(1)
        self.progress.SetPosition(wx.Point(rect.x+2, rect.y+2))
        self.progress.SetSize(wx.Size(rect.width-4, rect.height-4))
               
        # Cancel button
        rect = self.GetFieldRect(2)
        self.cancelButton.SetPosition(wx.Point(rect.x+2, rect.y+2))
        self.cancelButton.SetSize(wx.Size(50, rect.height-2))
        
        
        
################################################################################
#
# Dialogs


class UrlDialog(wx.Dialog):
    def __init__(self, parent, id, title, address = "", text = None):
        wx.Dialog.__init__(self, parent, id, title)
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.Centre()
        if text == None:
            info = "Enter venue URL address"
        else:
            info = text
        self.text = wx.StaticText(self, -1, info, style=wx.ALIGN_LEFT)
        self.addressText = wx.StaticText(self, -1, "Address: ", style=wx.ALIGN_LEFT)
        self.address = wx.TextCtrl(self, -1, address, size = wx.Size(300,-1))
        self.__Layout()
        
    def __Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.text, 0, wx.LEFT|wx.RIGHT|wx.TOP, 20)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.addressText, 0)
        sizer2.Add(self.address, 1, wx.EXPAND)

        sizer1.Add(sizer2, 0, wx.EXPAND | wx.ALL, 20)

        sizer3 =  wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        sizer.Add(sizer1, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        sizer.Add(sizer3, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()
        
    def GetValue(self):
        return self.address.GetValue()

    
 
################################################################################

class ProfileDialog(wx.Dialog):
    def __init__(self, parent, id, title, validate):
        wx.Dialog.__init__(self, parent, id, title,
                          style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.Centre()
        self.nameText = wx.StaticText(self, -1, "Name:", style=wx.ALIGN_LEFT)
        if validate:
            self.nameCtrl = wx.TextCtrl(self, -1, "", size = (400,-1),
                                       validator = TextValidator("Name"))
        else:
            # Don't use a validator
            self.nameCtrl = wx.TextCtrl(self, -1, "", size = (400,-1))
        self.emailText = wx.StaticText(self, -1, "Email:", style=wx.ALIGN_LEFT)
        if validate:
            self.emailCtrl = wx.TextCtrl(self, -1, "",
                                       validator = TextValidator("Email"))
        else:
            # Don't use a validator
            self.emailCtrl = wx.TextCtrl(self, -1, "")
        self.phoneNumberText = wx.StaticText(self, -1, "Phone Number:",
                                            style=wx.ALIGN_LEFT)
        self.phoneNumberCtrl = wx.TextCtrl(self, -1, "")
        self.locationText = wx.StaticText(self, -1, "Location:")
        self.locationCtrl = wx.TextCtrl(self, -1, "")
        self.homeVenue= wx.StaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wx.TextCtrl(self, -1, "")
        self.profileTypeText = wx.StaticText(self, -1, "Profile Type:",
                                            style=wx.ALIGN_LEFT)
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.profile = None
        self.profileTypeBox = None
        
        self.titleText = wx.StaticText(self,-1,"Profile")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        self.__Layout()
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(False)
            self.emailCtrl.SetEditable(False)
            self.phoneNumberCtrl.SetEditable(False)
            self.locationCtrl.SetEditable(False)
            self.homeVenueCtrl.SetEditable(False)
            if isinstance(self.profileTypeBox,wx.TextCtrl):
                self.profileTypeBox.SetEditable(False)
        else:
            self.nameCtrl.SetEditable(True)
            self.emailCtrl.SetEditable(True)
            self.phoneNumberCtrl.SetEditable(True)
            self.locationCtrl.SetEditable(True)
            self.homeVenueCtrl.SetEditable(True)
            if isinstance(self.profileTypeBox,wx.TextCtrl):
                self.profileTypeBox.SetEditable(True)
            
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __Layout(self):
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        #box = wx.StaticBox(self, -1, "Profile")
        #box.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        #sizer2 = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        self.gridSizer = wx.FlexGridSizer(0, 2, 4, 5)
        self.gridSizer.Add(self.nameText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.AddGrowableCol(1)
        
        self.gridSizer.Add(self.phoneNumberText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wx.ALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wx.EXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wx.ALIGN_LEFT, 0)
        if self.profileTypeBox:
            self.gridSizer.Add(self.profileTypeBox, 0, wx.EXPAND)
            
        self.sizer1.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        self.sizer1.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        self.sizer1.Add(self.gridSizer, 1, wx.ALL|wx.EXPAND, 10)
        self.sizer1.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)

        #self.sizer1.Add(sizer2, 1, wx.ALL|wx.EXPAND, 10)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.EAST, 10)
        sizer3.Add(self.cancelButton, 0)

        self.sizer1.Add(sizer3, 0, wx.ALIGN_CENTER|wx.ALL, 10)

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

    def SetProfile(self, profile):
        self.profile = profile
        self.selections = ["user", "node"]
        self.profileTypeBox = wx.ComboBox(self, -1, self.selections[0],
                                         choices = self.selections, 
                                         style = wx.CB_READONLY)
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
        
    def SetDescription(self, item):
        log.debug("ProfileDialog.SetDescription: Set description in dialog name:%s, email:%s, phone:%s, location:%s home:%s, dn:%s"
                   %(item.name, item.email,item.phoneNumber,item.location,
                     item.homeVenue, item.distinguishedName))
        self.profileTypeBox = wx.TextCtrl(self, -1, item.profileType)
        #self.profileTypeBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL, 
        #                            0, "verdana"))
        self.gridSizer.Add(self.profileTypeBox, 0, wx.EXPAND, 0)
        self.__Layout()
        
        self.nameCtrl.SetValue(item.name)
        self.emailCtrl.SetValue(item.email)
        self.phoneNumberCtrl.SetValue(item.phoneNumber)
        self.locationCtrl.SetValue(item.location)
        self.homeVenueCtrl.SetValue(item.homeVenue)
                     
        self.profileTypeBox.SetValue(item.GetProfileType())
            
        self.__SetEditable(False)
        self.cancelButton.Hide()



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

        #for view
        if profile == None:
            if val ==  '<Insert Name Here>':
                MessageDialog(None, "Fill in the %s field" % (self.fieldName,))
                return False
            
            if val ==  '<Insert Email Address Here>':
                MessageDialog(None, "Fill in the %s field" % (self.fieldName,))
                return False
            
        #for real profile dialog
        elif(len(val) < 1 or profile.IsDefault() 
             or profile.name == '<Insert Name Here>'
             or profile.email == '<Insert Email Address Here>'):
             
            if profile.name == '<Insert Name Here>':
                self.fieldName == 'Name'
            elif profile.email ==  '<Insert Email Address Here>':
                self.fieldName = 'Email'
                                                   
            MessageDialog(None, "Fill in the %s field" %(self.fieldName,))
            return False
        return True

    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.


################################################################################



class AddAppDialog(wx.Dialog):
    '''
    Dialog for adding name and description to an application session.
    '''

    def __init__(self, parent, id, title, appDescription):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        self.info = wx.StaticText(self, -1, "Give this %s session a name and a short description, click Ok to start it.  \nOnce the session is started, all participants of the venue will be able to join." %appDescription.name)

        self.nameText = wx.StaticText(self, -1, "Name: ")
        self.nameCtrl = wx.TextCtrl(self, -1, "", validator = AddAppDialogValidator())
        self.descriptionText = wx.StaticText(self, -1, "Description:")
        self.descriptionCtrl = wx.TextCtrl(self, -1, "",
                                          style = wx.TE_MULTILINE, 
                                          size = wx.Size(200, 50),
                                          validator = AddAppDialogValidator())

        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.__Layout()

    def __Layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(self.info, 0, wx.EXPAND|wx.ALL, 10)
        sizer.Add(wx.Size(5,5))
        
        gridSizer = wx.FlexGridSizer(2, 2, 10, 5)
        gridSizer.Add(self.nameText)
        gridSizer.Add(self.nameCtrl, 0, wx.EXPAND)
        gridSizer.Add(self.descriptionText)
        gridSizer.Add(self.descriptionCtrl, 0, wx.EXPAND)
        gridSizer.AddGrowableCol(1)
        
        sizer.Add(gridSizer, 1, wx.EXPAND|wx.ALL, 10)
        sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND|wx.ALL, 10)

        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.Add(self.okButton, 0, wx.BOTTOM, 10)
        bsizer.Add(self.cancelButton, 0, wx.LEFT|wx.BOTTOM, 5)

        sizer.Add(bsizer, 0, wx.CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()
        
    def GetName(self):
        return self.nameCtrl.GetValue()

    def GetDescription(self):
        return self.descriptionCtrl.GetValue()



class AddAppDialogValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)

    def Clone(self):
        return AddAppDialogValidator()

    def Validate(self, win):
        name = win.GetName()
        desc = win.GetDescription()
        
        if name == "":
            info = "Enter a name for this application session." 
            dlg = wx.MessageDialog(None, info, "Enter Name", style = wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        if desc == "":
            info = "Enter a description for this application session." 
            dlg = wx.MessageDialog(None, info, "Enter Description", style = wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        return True
    
    def TransferToWindow(self):
        return True # Prevent wx.Dialog from complaining.

    def TransferFromWindow(self):
        return True # Prevent wx.Dialog from complaining.
        
 
################################################################################

class ExitPropertiesDialog(wx.Dialog):
    '''
    This dialog is opened when a user right clicks an exit
    '''
    def __init__(self, parent, id, title, profile):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        self.title = title
        self.nameText = wx.StaticText(self, -1, "Name:", style=wx.ALIGN_LEFT)
        self.nameCtrl = wx.TextCtrl(self, -1, profile.GetName(), size = (500,-1))
        self.descriptionText = wx.StaticText(self, -1, "Description:", 
                                            style=wx.ALIGN_LEFT | wx.TE_MULTILINE )
        self.descriptionCtrl = wx.TextCtrl(self, -1, profile.GetDescription(), 
                                          size = (500,-1))
        self.urlText = wx.StaticText(self, -1, "URL:", style=wx.ALIGN_LEFT)
        self.urlCtrl = wx.TextCtrl(self, -1, profile.GetURI(),  size = (500,-1))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        
        self.titleText = wx.StaticText(self,-1,"Exit Properties")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        
        self.__SetProperties()
        self.__Layout()
                              
    def __SetProperties(self):
        self.nameCtrl.SetEditable(False)
        self.descriptionCtrl.SetEditable(False)
        self.urlCtrl.SetEditable(False)
                                               
    def __Layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.FlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.urlText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.urlCtrl, 0, wx.EXPAND, 0)
        
        sizer1.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        sizer1.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        sizer1.Add(gridSizer, 1, wx.ALL, 10)
        sizer1.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)

        #sizer1.Add(sizer2, 1, wx.ALL|wx.EXPAND, 10)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
       
        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
         
################################################################################

class DataPropertiesDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wx.StaticText(self, -1, "Name:", style=wx.ALIGN_LEFT)
        self.nameCtrl = wx.TextCtrl(self, -1, "", size = (500,-1))
        self.ownerText = wx.StaticText(self, -1, "Owner:", 
                                      style=wx.ALIGN_LEFT | wx.TE_MULTILINE )
        self.ownerCtrl = wx.TextCtrl(self, -1, "")
        self.sizeText = wx.StaticText(self, -1, "Size:")
        self.sizeCtrl = wx.TextCtrl(self, -1, "")
        self.lastModText = wx.StaticText(self, -1, "Last modified:")
        self.lastModCtrl = wx.TextCtrl(self, -1, "")
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.titleText = wx.StaticText(self,-1,"Data Properties")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        
        self.__SetProperties()
        self.__SetEditable(True)
        self.__Layout()
        
        self.description = None
        
    def __SetProperties(self):
        self.SetTitle("Fill in data information")
        
    def __SetEditable(self, editable):
        if not editable:
            # Name is always editable
            self.nameCtrl.SetEditable(False)
           
        else:
            self.nameCtrl.SetEditable(True)
            self.ownerCtrl.SetEditable(False)
            self.sizeCtrl.SetEditable(False)
            self.lastModCtrl.SetEditable(False)
                                 
                                       
    def __Layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        #box = wx.StaticBox(self, -1, "Properties")
        #box.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        #sizer2 = wx.StaticBoxSizer(box, wx.HORIZONTAL)
        gridSizer = wx.FlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.ownerText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.ownerCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.sizeText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.sizeCtrl, 0, wx.EXPAND, 0)
        gridSizer.Add(self.lastModText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.lastModCtrl, 0, wx.EXPAND, 0)
        
        sizer1.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        sizer1.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        sizer1.Add(gridSizer, 1, wx.ALL, 10)
        sizer1.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALL, 10)

        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()

    def SetDescription(self, dataDescription):
        '''
        This method is called if you only want to view the dialog.
        '''
        self.description = copy.copy(dataDescription)
        self.nameCtrl.SetValue(dataDescription.name)
        self.ownerCtrl.SetValue(str(dataDescription.owner))
        self.sizeCtrl.SetValue(str(dataDescription.size))
        try:
            if not dataDescription.lastModified:
                self.lastModCtrl.SetValue("Not available.")
            else:    
                self.lastModCtrl.SetValue(str(dataDescription.lastModified))
        except:
            self.lastModCtrl.SetValue("Not available.")
            log.info("DataDialog.SetDescription: last modified param does not exist. Probably old data description. Ignore!")
        self.SetTitle("Data Properties")
        self.__SetEditable(True)
        self.cancelButton.Destroy()
        
    def GetDescription(self):
        if self.description:
            self.description.name = self.nameCtrl.GetValue()

        return self.description
          
          

############################################################################

class ServicePropertiesDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wx.StaticText(self, -1, "Name:", style=wx.ALIGN_LEFT)
        self.nameCtrl = wx.TextCtrl(self, -1, "", size = (300,-1))
        self.uriText = wx.StaticText(self, -1, "Location URL:",
                                    style=wx.ALIGN_LEFT | wx.TE_MULTILINE )
        self.uriCtrl = wx.TextCtrl(self, -1, "")
        self.typeText = wx.StaticText(self, -1, "Mime Type:")
        self.typeCtrl = wx.TextCtrl(self, -1, "")
        self.descriptionText = wx.StaticText(self, -1, "Description:",
                                            style=wx.ALIGN_LEFT)
        self.descriptionCtrl = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE,
                                          size = wx.Size(200, 50))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.titleText = wx.StaticText(self,-1,"Service Properties")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        
        self.__Layout()
        
        self.description = None

    
    def __SetEditable(self, editable):
        if not editable:
            self.uriCtrl.SetEditable(False)
            self.typeCtrl.SetEditable(False)
            
            # Always editable
            self.nameCtrl.SetEditable(True)
            self.descriptionCtrl.SetEditable(True)
        else:
            self.nameCtrl.SetEditable(True)
            self.uriCtrl.SetEditable(True)
            self.typeCtrl.SetEditable(True)
            self.descriptionCtrl.SetEditable(True)
                  
    def __Layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.FlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.uriText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.typeText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wx.EXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wx.EXPAND, 0)
        #sizer2.Add(gridSizer, 1, wx.ALL, 10)

        sizer1.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        sizer1.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        sizer1.Add(gridSizer, 1, wx.ALL, 10)
        sizer1.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALL, 10)

        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()

    def GetDescription(self):
        service = ServiceDescription("service", "service", "uri",
                                     "storagetype")
        service.SetName(self.nameCtrl.GetValue())
        service.SetDescription(self.descriptionCtrl.GetValue())
        service.SetURI(self.uriCtrl.GetValue())
        service.SetMimeType(self.typeCtrl.GetValue())
        return service

    def SetDescription(self, serviceDescription):
        '''
        This method is called if you only want to view the dialog.
        '''
        
        self.description = copy.copy(serviceDescription)
        
        self.nameCtrl.SetValue(serviceDescription.name)
        self.uriCtrl.SetValue(serviceDescription.uri)
        self.typeCtrl.SetValue(serviceDescription.mimeType)
        self.descriptionCtrl.SetValue(serviceDescription.description)
        self.__SetEditable(False)
        self.cancelButton.Destroy()


############################################################################

class ApplicationPropertiesDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title,
                          style = wx.DEFAULT_DIALOG_STYLE | 
                          wx.RESIZE_BORDER)
        self.Centre()
        self.nameText = wx.StaticText(self, -1, "Name:", style=wx.ALIGN_LEFT)
        self.nameCtrl = wx.TextCtrl(self, -1, "", size = (300,-1))
        self.uriText = wx.StaticText(self, -1, "Location URL:",
                                    style=wx.ALIGN_LEFT | wx.TE_MULTILINE )
        self.uriCtrl = wx.TextCtrl(self, -1, "")
        self.typeText = wx.StaticText(self, -1, "Mime Type:")
        self.typeCtrl = wx.TextCtrl(self, -1, "")
        self.descriptionText = wx.StaticText(self, -1, "Description:",
                                            style=wx.ALIGN_LEFT)
        self.descriptionCtrl = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE,
                                          size = wx.Size(200, 50))
        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.titleText = wx.StaticText(self,-1,"Application Properties")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
        
        self.__Layout()
        
        self.description = None

    
    def __SetEditable(self, editable):
        if not editable:
            self.uriCtrl.SetEditable(False)
            self.typeCtrl.SetEditable(False)
            
            # Always editable
            self.nameCtrl.SetEditable(True)
            self.descriptionCtrl.SetEditable(True)
        else:
            self.nameCtrl.SetEditable(True)
            self.uriCtrl.SetEditable(True)
            self.typeCtrl.SetEditable(True)
            self.descriptionCtrl.SetEditable(True)
                  
    def __Layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        #sizer2 = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Profile"), wx.HORIZONTAL)
        gridSizer = wx.FlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.uriText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wx.EXPAND, 0)
        gridSizer.Add(self.typeText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wx.EXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wx.EXPAND, 0)
       
        sizer1.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        sizer1.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        sizer1.Add(gridSizer, 1, wx.ALL, 10)
        sizer1.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALL, 10)

        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()

    def GetDescription(self):
        if not self.description:
            self.description = ApplicationDescription(GUID(), "", "", "","")
        self.description.SetName(self.nameCtrl.GetValue())
        self.description.SetDescription(self.descriptionCtrl.GetValue())
        self.description.SetURI(self.uriCtrl.GetValue())
        self.description.SetMimeType(self.typeCtrl.GetValue())
        return self.description

    def SetDescription(self, appDescription):
        '''
        This method is called if you only want to view the dialog.
        '''
        self.description = copy.copy(appDescription)
        
        self.nameCtrl.SetValue(appDescription.name)
        self.uriCtrl.SetValue(appDescription.uri)
        self.typeCtrl.SetValue(appDescription.mimeType)
        self.descriptionCtrl.SetValue(appDescription.description)
        self.__SetEditable(False)
        self.cancelButton.Destroy()
         
################################################################################

class VenuePropertiesDialog(wx.Dialog):
    def __init__(self, parent, id, title, venueClient):
        wx.Dialog.__init__(self, parent, id, title)
        self.venueClient = venueClient
        self.streamListLabel = wx.StaticText(self,-1,'Streams')
        self.list = wx.ListCtrl(self, wx.NewId(), size = wx.Size(500, 150),style=wx.LC_REPORT)

        self.list.InsertColumn(0, "Address")
        self.list.InsertColumn(1, "Port")
        self.list.InsertColumn(2, "TTL")
        self.list.InsertColumn(3, "Purpose")
        self.list.InsertColumn(4, "Type")
        self.list.InsertColumn(5, "Encryption Key")

        self.list.SetColumnWidth(0, 100)
        self.list.SetColumnWidth(1, 50)
        self.list.SetColumnWidth(2, 50)
        self.list.SetColumnWidth(3, 100)
        self.list.SetColumnWidth(4, 80)
        self.list.SetColumnWidth(5, 100)
        
        self.textLocationLabel = wx.StaticText(self,-1,'Text Location')
        self.textLocationText = wx.TextCtrl(self,-1,
                                        self.venueClient.GetChatLocation())
        self.textLocationText.SetEditable(False)
        
        self.dataLocationLabel = wx.StaticText(self,-1,'Data Location')
        self.dataLocationText = wx.TextCtrl(self,-1,
                                        self.venueClient.venueState.GetDataLocation())
        self.dataLocationText.SetEditable(False)

        self.okButton = wx.Button(self, wx.ID_OK, "Ok")
        
        self.titleText = wx.StaticText(self,-1,"Venue Properties")
        if IsOSX():
            self.titleText.SetFont(wx.Font(12,wx.NORMAL,wx.NORMAL,wx.BOLD))
        else:
            self.titleText.SetFont(wx.Font(wx.DEFAULT,wx.NORMAL,wx.NORMAL,wx.BOLD))
        self.titleLine = wx.StaticLine(self,-1)
        self.buttonLine = wx.StaticLine(self,-1)
                       
        self.__Layout()


        # Populate venue properties dialog
        
        # - stream information
        streamList = self.venueClient.GetVenueStreams()

        j = 0
        for stream in streamList:
            location = stream.location
        
            self.list.InsertStringItem(j, 'item')
            self.list.SetStringItem(j, 0, str(location.host))
            self.list.SetStringItem(j, 1, str(location.port))
            if hasattr(stream.location, 'ttl'):
                self.list.SetStringItem(j, 2, str(location.ttl))
            else:
                self.list.SetStringItem(j, 2, str(''))

            self.list.SetStringItem(j, 3, str(stream.capability[0].type +
                                              " (" +location.type+")"))
            if stream.static:
                self.list.SetStringItem(j, 4, 'static')
            else:
                self.list.SetStringItem(j, 4, 'dynamic')
                
            if stream.encryptionFlag:
                self.list.SetStringItem(j, 5, stream.encryptionKey)
            else:
                self.list.SetStringItem(j, 5, '-')
        
            j = j + 1
        
    def __Layout(self):
        '''
        Handle UI layout.
        '''
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        #box = wx.StaticBox(self, -1, "Multicast Addresses")
        #box.SetFont(wx.Font(wx.DEFAULT, wx.NORMAL, wx.NORMAL, wx.BOLD))
        #sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        mainSizer.Add(self.titleText,0,wx.EXPAND|wx.ALL,10)
        mainSizer.Add(self.titleLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        mainSizer.Add(self.streamListLabel,0, wx.LEFT|wx.TOP, 10)
        mainSizer.Add(self.list, 1, wx.EXPAND| wx.ALL, 10)
        
        # text location 
        horsizer = wx.BoxSizer(wx.HORIZONTAL)
        horsizer.Add(self.textLocationLabel,0, wx.ALL, 10)
        horsizer.Add(self.textLocationText,1, wx.RIGHT|wx.TOP|wx.BOTTOM, 10)
        mainSizer.Add(horsizer,0,wx.EXPAND)
        
        # data location
        horsizer = wx.BoxSizer(wx.HORIZONTAL)
        horsizer.Add(self.dataLocationLabel,0, wx.ALL, 10)
        horsizer.Add(self.dataLocationText,1, wx.RIGHT|wx.TOP|wx.BOTTOM, 10)
        mainSizer.Add(horsizer,0,wx.EXPAND)
        
        mainSizer.Add(self.buttonLine,0,wx.EXPAND|wx.LEFT|wx.RIGHT,5)
        
        #mainSizer.Add(sizer, 1, wx.EXPAND| wx.ALL, 10)
        mainSizer.Add(self.okButton, 0, wx.CENTER | wx.ALL, 10)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(1)
        

############################################################################

videoServiceDialogMsg="""
No video services found; if you want to add one,
select a host and, thereafter, a device.  To have
the service load automatically the next time you
start the Venue Client, you must store the node
configuration using Tools->Configure node services."""
class AddVideoServiceDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)
        self.Centre()
        
        self.hostname = Config.SystemConfig.instance().GetHostname()
                
        self.guideText = wx.StaticText(self, -1, videoServiceDialogMsg, 
                                      style=wx.ALIGN_LEFT)
        self.hostText = wx.StaticText(self, -1, "Host:", style=wx.ALIGN_LEFT)
        self.hostCtrl = wx.ComboBox(self, -1, "",size=(300,-1))
        
        self.exists = threading.Event()
        self.exists.set()
        
        self.deviceText = wx.StaticText(self, -1, "Device:", style=wx.ALIGN_LEFT)
        self.deviceCtrl = wx.ComboBox(self, -1, "",size=(300,-1))
        
        self.okButton = wx.Button(self, wx.ID_OK, "OK")
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")

        self.browser = ServiceDiscovery.Browser('_servicemanager._tcp', self.BrowseCallback)
        self.browser.Start()

        wx.EVT_COMBOBOX(self,self.hostCtrl.GetId(),self.OnHostSelect)
        wx.EVT_TEXT_ENTER(self,self.hostCtrl.GetId(),self.OnHostSelect)

        self.__Layout()
        
    def OnHostSelect(self,event=None):
        if event:
            url = event.GetString()
        else:
            url = self.hostCtrl.GetValue()
        newurl = BuildServiceUrl(url,'http',11000,'ServiceManager')
        if url != newurl:
            self.hostCtrl.SetValue(newurl)
            url = newurl

        # clear the device list
        for i in range(self.deviceCtrl.GetCount()):
            self.deviceCtrl.Delete(0)
        
        # populate device list with resources
        resources = AGServiceManagerIW(url).GetResources()
        for r in resources:
            item = self.deviceCtrl.Append(r.name)     
            self.deviceCtrl.SetClientData(item,r)
        if resources:
            self.deviceCtrl.SetSelection(0)
    
    def BrowseCallback(self,op,serviceName,url=None):
        if self.exists.isSet() and op == ServiceDiscovery.Browser.ADD:
            wx.CallAfter(self.AddItem,serviceName,url)
            
    def AddItem(self,name,url):
        if self.hostCtrl.FindString(url) == wx.NOT_FOUND:
            self.hostCtrl.Append(url)
            
            val = self.hostCtrl.GetValue()
            # if the combobox doesn't have a value set, use this one
            if not val:
                self.hostCtrl.SetValue(url)
            # if the found service is local, use it instead of existing one
            elif (val.find(self.hostname) == -1 and url.find(self.hostname) >= 0):
                self.hostCtrl.SetValue(url)
            self.OnHostSelect()
        
    def __Layout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.guideText, 0, wx.RIGHT|wx.LEFT|wx.BOTTOM|wx.ALIGN_LEFT, 10)
        gridSizer = wx.FlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.hostText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.hostCtrl, 1, wx.EXPAND, 0)
        gridSizer.Add(self.deviceText, 0, wx.ALIGN_LEFT, 0)
        gridSizer.Add(self.deviceCtrl, 1, wx.EXPAND, 0)
        sizer1.Add(gridSizer, 0, wx.ALL|wx.EXPAND, 5)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.okButton, 0, wx.ALL, 10)
        sizer3.Add(self.cancelButton, 0, wx.ALL, 10)

        sizer1.Add(sizer3, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        
    def GetValue(self):
        """
        Get selected values from dialog
        
        Returns:  tuple:  (host url, device resource)
        """
        deviceIndex = self.deviceCtrl.GetSelection()
        return (self.hostCtrl.GetValue(),self.deviceCtrl.GetClientData(deviceIndex))

 
################################################################################

class DataDropTarget(wx.FileDropTarget):
    def __init__(self, application):
        wx.FileDropTarget.__init__(self)
        self.app = application
        self.do = wx.FileDataObject()
        self.SetDataObject(self.do)
    
    #Modified by NA2-HPCE
    def OnDropFiles(self, x, y, files):
        #self.app.AddDataCB(fileList = files)
        self.app.DecideDragDropType(x,y,fileList = files)

class DesktopDropTarget(wx.FileDropTarget):
    def __init__(self, application):
        wx.FileDropTarget.__init__(self)
        self.app = application
        self.do = wx.FileDataObject()
        self.SetDataObject(self.do)

    def OnEnter(self, x, y, d):
        print 'on enter'
        
    def OnLeave(self):
        print 'on leave'

    def OnDropFiles(self, x, y, files):
        print 'on drop files ', files[0]
        #self.app.AddDataToDesktop(fileList = files)
        
    #Added by NA2-HPCE
    def EnvSort(item1, item2):
        """
        Sorting method designed for sorting DataDescriptions arriving from 
        VenueServer in order fo their hierarchy level, so that lowest level
        entries are sorted first. This is necessary to first create the directories
        for files of lower hierarchy levels.
        
        """
        if int(item1.GetLevel()) == -2:
            return 1
        if int(item2.GetLevel()) == -2:
            return -1
        if item1.GetLevel() < item2.GetLevel():
            log.debug("Item1 Is higher hierarchy")
            return -1
        elif item1.GetLevel() == item2.GetLevel():
            log.debug("Item1 Is same hierarchy")
            return 0
        else:
            log.debug("Item1 Is lower hierarchy")
            return 1


if __name__ == "__main__":
    pp = wx.PySimpleApp()
    #n = VenuePropertiesDialog(None, -1, 'Properties')
    #n.ShowModal()
    
    f = wx.Frame(None, -1, "Navigation")
    n = NavigationPanel(f, -1)
    f.Show()
    
    pp.MainLoop()
   
    
    #n = AddAppDialog(None, -1, "Start Application Session", 
    #                 ApplicationDescription("test", "test", "test", "test", "test"))
    #if n.ShowModal() == wx.ID_OK:
    #    print n.GetName()
    
    
    if n:
        n.Destroy()
