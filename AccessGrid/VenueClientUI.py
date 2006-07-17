#-----------------------------------------------------------------------------
# Name:        VenueClientUI.py
# Purpose:     
#
# Author:      Susanne Lefvert, Thomas D. Uram
#
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClientUI.py,v 1.195 2006-07-17 14:55:08 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""
__revision__ = "$Id: VenueClientUI.py,v 1.195 2006-07-17 14:55:08 turam Exp $"
__docformat__ = "restructuredtext en"

import copy
import os
import os.path
import time
from wx import VERSION as WXVERSION
from wxPython.wx import *
import string
import webbrowser
import traceback
import re
import sys
from twisted.internet import reactor
import threading

from time import localtime , strftime
from AccessGrid import Log
log = Log.GetLogger(Log.VenueClientUI)
Log.SetDefaultLevel(Log.VenueClientUI, Log.WARN)

from AccessGrid import icons
from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows, IsOSX, Config, IsLinux, IsFreeBSD
from AccessGrid.UIUtilities import AboutDialog, MessageDialog
from AccessGrid.UIUtilities import ErrorDialog, BugReportCommentDialog
from AccessGrid.ClientProfile import *
from AccessGrid.Preferences import Preferences
from AccessGrid.PreferencesUI import PreferencesDialog
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import STATUS_ENABLED, STATUS_DISABLED
from AccessGrid.Descriptions import ApplicationDescription, VenueDescription
from AccessGrid.Security.wxgui.AuthorizationUI import AuthorizationUIDialog
from AccessGrid.Utilities import SubmitBug, BuildServiceUrl
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.AppMonitor import AppMonitor
from AccessGrid.Venue import ServiceAlreadyPresent
from AccessGrid.VenueClient import NetworkLocationNotFound, NotAuthorizedError, NoServices
from AccessGrid.VenueClient import DisconnectError
from AccessGrid.VenueClientController import NoAvailableBridges, NoEnabledBridges
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.UIUtilities import AddURLBaseDialog, EditURLBaseDialog
from AccessGrid.Beacon.rtpBeaconUI import BeaconFrame
from AccessGrid.RssReader import RssReader,strtimeToSecs  
from AccessGrid.interfaces.Venue_client import VenueIW   
from AccessGrid import ServiceDiscovery   
from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW

try:
    import win32api
except:
    pass

    
"""

These GUI components live in this file:

Main window components
----------------------

class VenueClientUI(VenueClientObserver):
class VenueClientFrame(wxFrame):
class VenueAddressBar(wxSashLayoutWindow):
class VenueListPanel(wxSashLayoutWindow):
class ContentListPanel(wxPanel):
class TextPanelSash(wxSashLayoutWindow):
class TextClientPanel(wxSashLayoutWindow):
class JabberClientPanel(wxPanel):
class StatusBar(wxStatusBar):



Dialogs
-------

class UrlDialog(wxDialog):
class ProfileDialog(wxDialog):
class TextValidator(wxPyValidator):
class ServicePropertiesDialog(wxDialog):
class ApplicationPropertiesDialog(wxDialog):
class ExitPropertiesDialog(wxDialog):
class DataPropertiesDialog(wxDialog):
class DataDropTarget(wxFileDropTarget):
class SelectAppDialog(wxDialog):

"""



class VenueClientUI(VenueClientObserver, wxFrame):
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
    ID_WINDOW_TOP = wxNewId()
    ID_WINDOW_LEFT  = wxNewId()
    ID_WINDOW_BOTTOM = wxNewId()
    ID_WINDOW_BOTTOM2 = wxNewId()
    ID_VENUE_DATA = wxNewId()
    ID_VENUE_DATA_ADD = wxNewId()
    ID_VENUE_ADMINISTRATE_VENUE_ROLES = wxNewId()
    ID_VENUE_SERVICE = wxNewId() 
    ID_VENUE_SERVICE_ADD = wxNewId()
    ID_VENUE_APPLICATION = wxNewId() 
    ID_VENUE_APPLICATION_MONITOR = wxNewId()
    ID_VENUE_SAVE_TEXT = wxNewId()
    ID_VENUE_PROPERTIES = wxNewId()
    ID_VENUE_OPEN_CHAT = wxNewId()
    ID_VENUE_CLOSE = wxNewId()
    ID_PROFILE = wxNewId()
    ID_PROFILE_EDIT = wxNewId()
    ID_CERTIFICATE_MANAGE = wxNewId()
    ID_USE_MULTICAST = wxNewId()
    ID_USE_UNICAST = wxNewId()
    ID_BRIDGES = wxNewId()
    ID_MYNODE_MANAGE = wxNewId()
    ID_PREFERENCES = wxNewId()
    ID_MYVENUE_ADD = wxNewId()
    ID_MYVENUE_EDIT = wxNewId()
    ID_MYVENUE_GOTODEFAULT = wxNewId()
    ID_MYVENUE_SETDEFAULT = wxNewId()
    ID_ADD_SCHEDULE = wxNewId()
    ID_TIMED_UPDATE = wxNewId()
    ID_HELP = wxNewId()
    ID_HELP_ABOUT = wxNewId()
    ID_HELP_MANUAL = wxNewId()
    ID_HELP_AGDP = wxNewId()
    ID_HELP_AGORG = wxNewId()
    ID_HELP_FL = wxNewId()
    ID_HELP_FLAG = wxNewId()
    ID_HELP_BUG_REPORT = wxNewId()
    ID_HELP_BUGZILLA = wxNewId()
    
    ID_ENABLE_DISPLAY = wxNewId()
    ID_ENABLE_VIDEO = wxNewId()
    ID_ENABLE_AUDIO = wxNewId()
    ID_ENABLE_MULTICAST = wxNewId()

    ID_PARTICIPANT_PROFILE = wxNewId()
    ID_ME_PROFILE = wxNewId()

    def __init__(self, venueClient, controller, app):
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
        self.onExitCalled = false
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
       
        wxFrame.__init__(self, NULL, -1, "")
        self.__BuildUI(app)
        self.SetSize(wxSize(400, 600))
        
        self.__SetMcastStatus(self.venueClient.GetMulticastStatus())
        
        # Tell the UI about installed applications
        self.__EnableAppMenu( false )
        
        #
        # Check if profile is created then open venue client
        #
        profile = prefs.GetProfile()

        if profile.IsDefault():  # not your profile
            log.debug("the profile is the default profile - open profile dialog")
            self.__OpenProfileDialog()
        else:
            self.__OpenVenueClient()
                        
        self.nodeManagementFrame = None

        # Help Doc locations
        agtkConfig = Config.AGTkConfig.instance()
        self.manual_url = "http://www.mcs.anl.gov/fl/research/accessgrid/documentation/manuals/VenueClient/3_0"
        self.agdp_url = "http://www.accessgrid.org/agdp"
        self.ag_url = "http://www.accessgrid.org/"
        self.flag_url = "http://www.mcs.anl.gov/fl/research/accessgrid"
        self.fl_url = "http://www.mcs.anl.gov/fl/"
        self.bugzilla_url = "http://bugzilla.mcs.anl.gov/accessgrid"

        reactor.interleave(wxCallAfter,installSignalHandlers=0)

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

        MessageDialog(self, msg, title, style = wxOK|wxICON_ERROR)

    def __OpenProfileDialog(self):
        """
        This method opens a profile dialog, in which the user can fill in
        his or her information.
        """
        p = self.venueClient.GetPreferences()
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', 1)
        profileDialog.SetProfile(p.GetProfile())
        
        if (profileDialog.ShowModal() == wxID_OK):
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
        self.Show(true)
        
    def __SetStatusbar(self):
        self.SetStatusBar(self.statusbar)
        self.statusbar.SetToolTipString("Statusbar")   
    
    def __SetMenubar(self, app):
        self.SetMenuBar(self.menubar)

        # ---- menus for main menu bar
        self.venue = wxMenu()
      
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
        
        if sys.platform not in ['darwin']:
            self.venue.AppendSeparator()
            self.venue.Append(self.ID_VENUE_CLOSE,"&Exit", "Exit venue")
        
        self.menubar.Append(self.venue, "&Venue")
              
        self.preferences = wxMenu()

# - Disabled for 3.0: No client-side auth support
#         #
#         # Retrieve the cert mgr GUI from the application.
#         #
#         self.cmui = None
#         try:
#             mgr = app.GetCertificateManager()
#         except:
#             log.exception("VenueClientFrame.__SetMenubar: Cannot retrieve \
#                            certificate mgr user interface, continuing")
# 
#         self.cmui = CertificateManagerWXGUI()
#         self.cmui.SetCertificateManager(mgr)
#         certMenu = self.cmui.GetMenu(self)
#         for item in certMenu.GetMenuItems():
#             self.preferences.AppendItem(item)
#         
#         self.preferences.AppendSeparator()

        # Add node-related entries
        self.preferences.AppendRadioItem(self.ID_USE_MULTICAST, "Use Multicast",
                                         "Use multicast to connect media")
        self.preferences.AppendRadioItem(self.ID_USE_UNICAST, "Use Unicast",
                                         "Use unicast to connect media")
     
        transport = self.venueClient.GetTransport()
        index = true
        if transport == "unicast":
            index = false

        self.preferences.Check(self.ID_USE_MULTICAST, index)
        self.preferences.Check(self.ID_USE_UNICAST, not index)
        self.bridgeSubmenu = wxMenu()

        # Create bridge menu, so individual bridges are selectable from the start
        self.__CreateBridgeMenu()
                       
        self.preferences.AppendMenu(self.ID_BRIDGES, "Bridges", self.bridgeSubmenu)
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
        self.preferences.Append(self.ID_PREFERENCES, "&Preferences...")
        self.menubar.Append(self.preferences, "&Tools")
        
        self.navigation = wxMenu()
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

        self.menubar.Append(self.navigation, "Navigation")
        
        self.help = wxMenu()
        self.help.Append(self.ID_HELP_MANUAL, "Venue Client &Manual",
                         "Venue Client Manual")
        self.help.Append(self.ID_HELP_AGDP,
                         "AG &Documentation Project Web Site",
                         "")
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
        self.meMenu = wxMenu()
       
        self.meMenu.Append(self.ID_ME_PROFILE,"View Profile...",\
                                           "View participant's profile information")
       
            
        self.participantMenu = wxMenu()
        self.participantMenu.Append(self.ID_PARTICIPANT_PROFILE,"View Profile...",\
                                           "View participant's profile information")
        # ---- Menus for headings
        self.dataHeadingMenu = wxMenu()
        self.dataHeadingMenu.Append(self.ID_VENUE_DATA_ADD,"Add...",
                                   "Add data to the venue")

        self.serviceHeadingMenu = wxMenu()
        self.serviceHeadingMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...",
                                "Add service to the venue")

        # Do not enable menus until connected
        self.__HideMenu()

    def __CreateBridgeMenu(self):
        
        self.bridges = self.venueClient.GetBridges()
        self.currentBridge = self.venueClient.GetCurrentBridge()
        items = self.bridgeSubmenu.GetMenuItems()
       
        for i in items:
            self.bridgeSubmenu.DeleteItem(i)

        bList = self.bridges.values()
        
        if not bList:
            id = wxNewId()
            self.bridgeSubmenu.Append(id,'No bridges available')
            self.bridgeSubmenu.Enable(id, false)
            return

        # sort the bridge list
        bList.sort(lambda x,y: cmp(x.rank, y.rank))

        for b in bList:
            id = wxNewId()
            self.bridgeSubmenu.AppendCheckItem(id, b.name)
            self.bridgeKeyMap[b.guid] = id

            if b.status == STATUS_ENABLED:
                self.bridgeSubmenu.Enable(id, true)
            else:
                self.bridgeSubmenu.Enable(id, false)

            if (self.currentBridge and b.guid == self.currentBridge.guid
                and self.venueClient.GetTransport()=="unicast"):
                self.bridgeSubmenu.Check(id, 1)
                
            EVT_MENU(self, id, lambda evt,
                     menuid=id, bridgeDesc=b: self.CheckBridgeCB(evt, menuid, bridgeDesc))

        if len(self.bridges.values())<1:
            self.Warn("No unicast bridge is currently available.", "Use Unicast")
           
                
    def CheckBridgeCB(self, event, menuid, bridgeDescription):
      

        # Uncheck all items except the checked one
        items = self.bridgeSubmenu.GetMenuItems()

        # If selecting the already selected bridge, ignore
        for i in items:
            if i.GetId() == menuid and i.GetKind() == wxITEM_CHECK and not self.menubar.IsChecked(menuid):
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
                    if i.GetKind() == wxITEM_CHECK:
                        self.bridgeSubmenu.Check(i.GetId(), 0)
        
        except:
            log.exception("Connection to bridge %s failed"%(bridgeDescription.name))
            self.bridgeSubmenu.Check(menuid, 0)
            self.Notify("Connection to bridge %s failed. \nPlease use a different bridge."%(bridgeDescription.name),
                        "Bridge Connection")
                        
    def __SetEvents(self):
    
        # Venue Menu
        EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.AddDataCB)
        EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.AddServiceCB)
        EVT_MENU(self, self.ID_VENUE_SAVE_TEXT, self.SaveTextCB)
        EVT_MENU(self, self.ID_VENUE_PROPERTIES, self.OpenVenuePropertiesCB)
        EVT_MENU(self, self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,
                 self.ModifyVenueRolesCB)
        EVT_MENU(self, self.ID_VENUE_CLOSE, self.ExitCB)
        
        # Preferences Menu
        EVT_MENU(self, self.ID_USE_MULTICAST, self.UseMulticastCB)
        EVT_MENU(self, self.ID_USE_UNICAST, self.UseUnicastCB)
        EVT_MENU(self, self.ID_ENABLE_DISPLAY, self.EnableDisplayCB)
        EVT_MENU(self, self.ID_ENABLE_VIDEO, self.EnableVideoCB)
        EVT_MENU(self, self.ID_ENABLE_AUDIO, self.EnableAudioCB)

        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.ManageNodeCB)
        EVT_MENU(self, self.ID_PREFERENCES, self.PreferencesCB)
        
        # Navigation Menu
        EVT_MENU(self, self.ID_MYVENUE_GOTODEFAULT, self.GoToDefaultVenueCB)
        EVT_MENU(self, self.ID_MYVENUE_SETDEFAULT, self.SetAsDefaultVenueCB)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenuesCB)
        EVT_MENU(self, self.ID_MYVENUE_EDIT, self.EditMyVenuesCB)
        EVT_MENU(self, self.ID_ADD_SCHEDULE, self.AddScheduleCB)
        EVT_MENU(self, self.ID_TIMED_UPDATE, self.TimedUpdateCB)
        
        # Help Menu
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialogCB)
        EVT_MENU(self, self.ID_HELP_MANUAL,self.OpenManualCB)
        EVT_MENU(self, self.ID_HELP_AGDP,self.OpenAGDPCB)
        EVT_MENU(self, self.ID_HELP_AGORG,self.OpenAGOrgCB)
        EVT_MENU(self, self.ID_HELP_FLAG, self.OpenFLAGCB)
        EVT_MENU(self, self.ID_HELP_FL,self.OpenFLCB)
        EVT_MENU(self, self.ID_HELP_BUG_REPORT, self.SubmitBugCB)
        EVT_MENU(self, self.ID_HELP_BUGZILLA,self.OpenBugzillaCB)

        # Popup Menu Events
        EVT_MENU(self, self.ID_ME_PROFILE, self.EditProfileCB)
        EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.ViewProfileCB)

        # UI Events
        EVT_CLOSE(self, self.ExitCB)
        
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.__OnSashDrag)
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.__OnSashDrag)
        EVT_SIZE(self, self.__OnSize)
        
        EVT_BUTTON(self,self.networkButton.GetId(),self.OnMulticast)
        EVT_BUTTON(self,self.audioButton.GetId(),self.EnableAudioCB)
        EVT_BUTTON(self,self.displayButton.GetId(),self.EnableDisplayCB)
        EVT_BUTTON(self,self.videoButton.GetId(),self.EnableVideoCB)
        EVT_BUTTON(self,self.configNodeButton.GetId(),self.ManageNodeCB)
        
        buttons = [ self.networkButton, self.audioButton, self.videoButton, 
                    self.displayButton, self.configNodeButton ]
        for button in buttons:
            EVT_ENTER_WINDOW(button,self.OnButtonFocusChange)
            EVT_LEAVE_WINDOW(button,self.OnButtonFocusChange)

    def OnButtonFocusChange(self,event):
        # make sure button gets highlighted when it has focus
        event.Skip()
        
        # clear status text when leaving button
        if isinstance(event,wxMouseEvent) and event.Leaving():
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
                    messageDialog = wxMessageDialog(self, "Beacon statistics not available",
                                                    "Alert",
                                                    style = wxOK|wxICON_INFORMATION)
                    messageDialog.ShowModal()
                    messageDialog.Destroy()

                    self.OnExit()
                    return
                
                parent_pos = self.GetPosition()
                parent_siz = self.GetSize()
                pos = ( parent_pos[0] + parent_siz[0] / 2, parent_pos[1] + parent_siz[1] / 2)
                self.beaconFrame = BeaconFrame(self, log, beacon, pos=pos)
                self.beaconFrame.Show(true)
        
    def __SetProperties(self):
        self.SetTitle("Venue Client")
        self.SetIcon(icons.getAGIconIcon())
        #self.venueListPanel.SetSize(wxSize(160, 300))
        #self.venueAddressBar.SetSize(wxSize(self.GetSize().GetWidth(),65))
        
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
            ID = wxNewId()
            self.myVenuesMenuIds[name] = ID
            url = self.myVenuesDict[name]
            text = "Go to: " + url
            self.navigation.Insert(self.myVenuesPos,ID, name, text)
            EVT_MENU(self, ID, self.GoToMenuAddressCB)
                        

    def __BuildUI(self, app):
        
        self.Centre()
        self.menubar = wxMenuBar()
        self.statusbar = StatusBar(self)
        
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, 
                                               self.myVenuesDict,
                                               'default venue')
        self.venueAddressBar.SetDefaultSize((1000, 55))
        self.venueAddressBar.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.venueAddressBar.SetAlignment(wxLAYOUT_TOP)
        self.venueAddressBar.SetSashVisible(wxSASH_BOTTOM, True)

        self.textClientPanel = TextPanelSash(self, self.ID_WINDOW_BOTTOM)
        self.textClientPanel.SetDefaultSize((1000, 200))
        self.textClientPanel.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.textClientPanel.SetAlignment(wxLAYOUT_BOTTOM)
        self.textClientPanel.SetSashVisible(wxSASH_TOP, True)

        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT,
                                             self)
        self.venueListPanel.SetDefaultSize((170, 1000))
        self.venueListPanel.SetOrientation(wxLAYOUT_VERTICAL)
        self.venueListPanel.SetAlignment(wxLAYOUT_LEFT)
        self.venueListPanel.SetSashVisible(wxSASH_RIGHT, True)

        self.contentListPanel = ContentListPanel(self)
        dataDropTarget = DataDropTarget(self)
        self.contentListPanel.SetDropTarget(dataDropTarget)

        # create toolbar
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolPacking(3)
        toolsize = (25,25)
        
        bitmap = icons.getNoMulticastBitmap()
        self.networkButton = wxBitmapButton(self.toolbar,-1,bitmap,size=toolsize)
        self.networkButton.SetToolTip(wxToolTip('View multicast connectivity'))
        self.toolbar.AddControl(self.networkButton)
        self.toolbar.AddSeparator()
        
        
        # - create the audio toolbar button  
        if self.isAudioEnabled:
            bitmap = icons.getAudioBitmap()
        else:
            bitmap = icons.getAudioDisabledBitmap()
        self.audioButton = wxBitmapButton(self.toolbar,-1,bitmap,size=toolsize)
        self.audioButton.SetToolTip(wxToolTip('Enable/disable audio'))
        self.toolbar.AddControl(self.audioButton)

        # - create the display toolbar button         
        if self.isDisplayEnabled:
            bitmap = icons.getDisplayBitmap()
        else:
            bitmap = icons.getDisplayDisabledBitmap()
        self.displayButton = wxBitmapButton(self.toolbar,-1,bitmap,size=toolsize)
        self.displayButton.SetToolTip(wxToolTip('Enable/disable display'))
        self.toolbar.AddControl(self.displayButton)

        # - create the video toolbar button         
        if self.isVideoEnabled:
            bitmap = icons.getCameraBitmap()
        else:
            bitmap = icons.getCameraDisabledBitmap()
        self.videoButton = wxBitmapButton(self.toolbar,-1,bitmap,size=toolsize)
        self.videoButton.SetToolTip(wxToolTip('Enable/disable video'))
        self.toolbar.AddControl(self.videoButton)

        bitmap = icons.getConfigureBitmap()
        self.configNodeButton = wxBitmapButton(self.toolbar,-1,bitmap,size=toolsize)
        self.configNodeButton.SetToolTip(wxToolTip('Configure node services'))
        self.toolbar.AddControl(self.configNodeButton)
        self.toolbar.Realize()
        
        self.__SetStatusbar()
        self.__SetMenubar(app)
        self.__SetProperties()
        self.__SetEvents()
        self.__LoadMyVenues()

    
    def __OnSashDrag(self, event):
        if event.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
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
           
            self.venueListPanel.SetDefaultSize(wxSize(width, 1000))

        elif eID == self.ID_WINDOW_TOP:
            height = event.GetDragRect().height
            self.venueAddressBar.SetDefaultSize(wxSize(1000, height))
        
        elif eID == self.ID_WINDOW_BOTTOM:
            height = event.GetDragRect().height

            # Avoid covering text area
            if height < 50:
                height = 50
            self.textClientPanel.SetDefaultSize(wxSize(1000, height))

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
        self.contentListPanel.Refresh()
                         
    def __OnSize(self, event = None):
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
        
    def __CleanUp(self):
        #self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

    def __HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)
        self.menubar.Enable(self.ID_VENUE_PROPERTIES, false)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, false)
        self.menubar.Enable(self.ID_VENUE_APPLICATION, false)
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, false)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, false)
                
    def __ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, true)
        self.menubar.Enable(self.ID_VENUE_PROPERTIES, true)
        self.menubar.Enable(self.ID_MYVENUE_ADD, true)
        self.menubar.Enable(self.ID_MYVENUE_GOTODEFAULT, true)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, true)
        self.menubar.Enable(self.ID_VENUE_APPLICATION, true)
                
        # Only show administrate button when you can administrate a venue.
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, true)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, true)

    def __EnableAppMenu(self, flag):
        for entry in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Enable( entry.GetId(), flag )

    def __Notify(self,text,title):
        dlg = wxMessageDialog(self, text, title, 
                              style = wxICON_INFORMATION | wxOK)
        ret = dlg.ShowModal()
    
    def __Warn(self,text,title):
        dlg = wxMessageDialog(self, text, title, style = wxICON_WARNING | wxOK)
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
            ret = wxID_OK
        else:
            log.debug('Received invitation to join application, prompting...')
            # Ask everyone else if they want to open the application client.
            text = '%s would like to invite you to a shared application session (%s). Do you wish to join?'%(appCmdDesc.profile.name, appCmdDesc.appDesc.name)
            dlg = wxMessageDialog(self, text, 'Join Shared Application Session', style = wxOK|wxCANCEL)
            ret = dlg.ShowModal()

        # Open the client
        if ret == wxID_OK:
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
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

    # end Pure UI Methods
    #
    ############################################################################

    ############################################################################
    #
    # Menu Callbacks

    #
    # Venue Menu
    #

    def AddDataCB(self, event = None, fileList = []):
    
        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #
        log.debug("In VenueClientController.AddDataCB")

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
            dlg = wxFileDialog(self, "Choose file(s):",
                               style = wxOPEN | wxMULTIPLE)
            if dlg.ShowModal() == wxID_OK:
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


        #
        # Check if data exists, and prompt to replace
        #
        if fileList:
            filesToAdd = []
            dataDescriptions = self.venueClient.GetVenueData()
            for filepath in fileList:
                pathParts = os.path.split(filepath)
                name = pathParts[-1]

                fileExists = 0
                for data in dataDescriptions:
                    if data.name == name:
                        # file exists; prompt for replacement
                        fileExists = 1
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
                        
                if not fileExists:
                    # File does not exist; add the file
                    filesToAdd.append(filepath)

            #
            # Upload the files
            #
            try:
                self.controller.AddDataCB(filesToAdd)
            except:
                log.exception("Error adding data")
                self.Error("The data could not be added", "Add Data Error")

    def AddServiceCB(self, event):
        addServiceDialog = ServicePropertiesDialog(self, -1,
                                         'Please, fill in service details')
        if (addServiceDialog.ShowModal() == wxID_OK):

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
        if f.ShowModal() == wxID_OK:
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
        if f.ShowModal() == wxID_OK:
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
        
        profileDialog = ProfileDialog(NULL, -1,
                                  'Your profile information', 1)
        profileDialog.SetProfile(self.venueClient.GetPreferences().GetProfile())
        if (profileDialog.ShowModal() == wxID_OK):
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
            self.preferences.Check(self.ID_USE_MULTICAST, true)
            #self.menubar.Enable(self.ID_BRIDGES, false)
        elif transport == "unicast":  
            self.preferences.Check(self.ID_USE_UNICAST, true)
            #self.menubar.Enable(self.ID_BRIDGES, true)

    def UseMulticastCB(self, event=None):
        try:
            self.controller.UseMulticastCB()
            #self.menubar.Enable(self.ID_BRIDGES, false)

            # Disable all bridge items
            for child in self.bridgeSubmenu.GetMenuItems():
                if child.GetKind() == wxITEM_CHECK:
                    self.bridgeSubmenu.Check(child.GetId(), false)

            self.preferences.Check(self.ID_USE_MULTICAST, true)
            self.preferences.Check(self.ID_USE_UNICAST, false)
                    
        except NetworkLocationNotFound:
            self.Error("Multicast streams not found","Use Multicast")
        except:
            self.Error("Error using multicast","Use Multicast")


    def UseUnicastCB(self,event=None):
        self.preferences.Check(self.ID_USE_MULTICAST, false)
        self.preferences.Check(self.ID_USE_UNICAST, true)

        # Switch to unicast
        try:
            self.controller.UseUnicastCB()

        except NoAvailableBridges:
            self.Warn("No bridges are currently available")
            self.preferences.Check( self.ID_USE_MULTICAST, true)
            return
        except NoEnabledBridges:
            self.Warn("Bridges are available, but they are disabled in preferences.\nEnable bridges in preferences and try again.")
            self.preferences.Check( self.ID_USE_MULTICAST, true)
            return
        except Exception,e:
            log.exception("Error trying to use unicast")
            self.preferences.Check( self.ID_USE_MULTICAST, true)
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
                if ret == wxID_OK:
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

    def ManageNodeCB(self, event):
        
        if self.nodeManagementFrame:
            self.nodeManagementFrame.Raise()
        else:
            self.nodeManagementFrame = NodeManagementClientFrame(self, -1, 
                                        "Access Grid Node Management",
                                        callback=self.OnNodeActivity)

            log.debug("VenueClientFrame.ManageNodeCB: open node management")
            log.debug('nodeservice url: %s', self.venueClient.GetNodeService() )

            try:
                
                self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeService() )
            except:
                log.exception("VenueClientUI.ManageNodeCB: Can not attach to node %s"%self.venueClient.GetNodeServiceUri())
                              
            if self.nodeManagementFrame.Connected(): # Right node service uri
                self.nodeManagementFrame.UpdateUI()
                self.nodeManagementFrame.Show(true)

            else: # Not right node service uri
                setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                             self.venueClient.GetNodeServiceUri(), 
                                             "Please, specify node service URL")

                if setNodeUrlDialog.ShowModal() == wxID_OK:
                    self.venueClient.SetNodeUrl(setNodeUrlDialog.GetValue())

                    try:
                        self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeService() )

                    except:
                        log.exception("VenueClientUI.ManageNodeCB: Can not attach to node")
                                            
                    if self.nodeManagementFrame.Connected(): # try again
                        self.nodeManagementFrame.Update()
                        self.nodeManagementFrame.Show(true)

                    else: # wrong url
                        MessageDialog(self, \
                             'Can not open node management\nat %s'%self.venueClient.GetNodeServiceUri(),
                             'Node Management Error')

                setNodeUrlDialog.Destroy()
                self.nodeManagementFrame = None
    
    def PreferencesCB(self, event = None):
        profile = None
        p = self.venueClient.GetPreferences()
        preferencesDialog = PreferencesDialog(NULL, -1,
                                              'Preferences', p)
        if (preferencesDialog.ShowModal() == wxID_OK):
            p = preferencesDialog.GetPreferences()
                       
            try:
                self.controller.ChangePreferences(p)

                # Check for disabled bridge preferences
                bDict = p.GetBridges()
                bridges = self.venueClient.GetBridges()
                
                for id in bDict.keys():
                    if self.bridgeKeyMap.has_key(id):
                        index = self.bridgeKeyMap[id]
                        status = true
                        
                        if bDict[id].status == STATUS_DISABLED:
                            status = false
                                                    
                        # Update bridge menu
                        self.bridgeSubmenu.Enable(index, status)
                        
                        # Change status for venue client bridges
                        if bridges.has_key(id):
                            bridges[id].status = bDict[id].status
                       
                self.venueClient.SetBridges(bridges)
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
        if (dialog.ShowModal() == wxID_OK):
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
        
        if (editMyVenuesDialog.ShowModal() == wxID_OK):
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

    # 
    # Support for scheduler integration
    #
    def AddScheduleCB(self,event):
        defaultRssUrl = 'http://www.mcs.anl.gov/fl/research/accessgrid/anl.rss'
        rssUrl = wxGetTextFromUser('Specify RSS URL of schedule to add',
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
        menutitle,menu = self._CreateMenu(doc)
        menuid = wxNewId()
        self.navigation.AppendMenu(menuid,menutitle,menu)
        
        menu.AppendSeparator()
        
        # Append remove item
        removeitemid = wxNewId()
        menu.Append(removeitemid,'Remove Schedule')
        EVT_MENU(self,removeitemid,lambda evt,menuid=menuid,url=url: self.RemoveScheduleCB(evt,menuid,url))

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
                   
        menu = wxMenu('')

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
                menu.Append(wxNewId(),'%02s %s %d'% 
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
            itemid = wxNewId()

            # add submenu for event
            submenu = wxMenu('')

            # - view event details
            vieweventid = wxNewId()
            submenu.Append(vieweventid,'View event details')

            # - go to venue
            if e.has_key('enclosures'):
                venueurl = e.enclosures[0]['url']
                gotovenueid = wxNewId()
                submenu.Append(gotovenueid,'Go to Venue')
                EVT_MENU(self,gotovenueid,lambda evt,url=venueurl: self.GoToVenueCB(evt,url))

            menu.AppendMenu(itemid,title,submenu)

            viewdetailurl = e.link
            if e.has_key('enclosures'):
                venueurl = e.enclosures[0]['url']
            EVT_MENU(self,vieweventid,lambda evt,url=viewdetailurl: self.ViewEventCB(evt,url))
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
        
        if(bugReportCommentDialog.ShowModal() == wxID_OK):
            # Submit the error report to Bugzilla
            comment = bugReportCommentDialog.GetComment()
            email = bugReportCommentDialog.GetEmail()
            
            SubmitBug(comment, self.venueClient.GetPreferences().GetProfile(), email)
            bugFeedbackDialog = wxMessageDialog(self, 
                                  "Your error report has been sent, thank you.",
                                  "Error Reported", 
                                  style = wxOK|wxICON_INFORMATION)
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
            wxBeginBusyCursor()
            
            # manipulate the venue url some
            defaultproto = 'https'
            defaultport = 8000

            # - define a mess of regular expressions for matching venue urls
            hostre = re.compile('^[\w.-]*$')
            hostportre = re.compile('^[\w.-]*:[\d]*$')
            protohostre = re.compile('^[\w]*://[\w.-]*$')
            protohostportre = re.compile('^[\w]*://[\w.-]*:[\d]*$')

            # - check for host only
            if hostre.match(venueUrl):
                host = venueUrl
                venueUrl = '%s://%s:%d/Venues/default' % (defaultproto,host,defaultport)
            # - check for host:port
            elif hostportre.match(venueUrl):
                hostport = venueUrl
                venueUrl = '%s://%s/Venues/default' % (defaultproto,hostport)
            elif protohostre.match(venueUrl):
                protohost = venueUrl
                venueUrl = '%s:%d/Venues/default' % (protohost,defaultport)
            elif protohostportre.match(venueUrl):
                protohostport = venueUrl
                venueUrl = '%s/Venues/default' % (protohostport)

            # - update the venue url
            self.venueAddressBar.SetAddress(venueUrl)
            
            self.SetStatusText("Trying to enter venue at %s" % (venueUrl,))

            # Enter in a thread so UI gets responsive immediately
            self.controller.EnterVenueCB(venueUrl)
            
            # Check if unicast option is set in preferences.
            currentTransport = self.venueClient.GetTransport()
           
            if currentTransport == "unicast":
                self.UseUnicastCB()
                             
            wxEndBusyCursor()
        except:
            wxEndBusyCursor()
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
            self.Notify("Please, select the participant you want to view information about", "View Profile") 

    def AddPersonalDataCB(self, event=None):
        dlg = wxFileDialog(self, "Choose file(s):", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
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
            self.Notify("Please, select the data you want to open", "Open Data")
              
    def SaveDataCB(self, event):
        data = self.GetSelectedItem()
        log.debug("VenueClientFrame.SaveData: Save data: %s", data)
        if(data != None and isinstance(data, DataDescription)):
            name = data.name
            path = self.SelectFile("Specify name for file", name)
            if path:
                self.controller.SaveDataCB(data,path)
        else:
            self.Notify("Please, select the data you want to save", "Save Data")

    def RemoveDataCB(self, event):
        itemList = self.GetSelectedItems()
        if itemList:
            for item in itemList:
                if(item != None and isinstance(item, DataDescription)):
                    text ="Are you sure you want to delete "+ item.name + "?"
                    if self.Prompt(text, "Confirmation"):
                        try:
                            self.controller.RemoveDataCB(item)
                        except NotAuthorizedError:
                            log.info("bin.VenueClient::RemoveData: Not authorized to remove data")
                            self.Notify("You are not authorized to remove the file", 
                                        "Remove Personal Files")        
                        except:
                            log.exception("bin.VenueClient::RemoveData: Error occured when trying to remove data")
                            self.Error("The file could not be removed", "Remove Files Error")
        else:
            self.Notify("Please, select the data you want to delete", "No file selected")
        
    def UpdateDataCB(self,dataDesc):
        try:
            self.controller.UpdateDataCB(dataDesc)
        except:
            log.exception("bin.VenueClient::UpdateData: Error occured when trying to update data")
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
            self.Notify("Please, select the service you want to open","Open Service")       
    
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
           self.Notify("Please, select the service you want to delete", "Delete Service")       

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
            self.Notify( "Please, select the application you want to delete", "Delete Application")

    def StartApplicationCB(self, app):
        timestamp = time.strftime("%I:%M:%S %p %B %d, %Y")
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
            AppMonitor(self, application.uri)
        except:
            self.Error("Error opening application monitor","Monitor App Error")
    
        
    def UpdateApplicationCB(self,appDesc):
        try:
            self.controller.UpdateApplicationCB(appDesc)
        except:
            self.Error("Error updating application","Application Update Error")
        
        
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
            self.controller.EnableVideoCB(self.isVideoEnabled)
            self.controller.EnableAudioCB(self.isAudioEnabled)
            self.controller.EnableDisplayCB(self.isDisplayEnabled)
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
            if enabled >= 0:
                self.venueClient.nodeService.SetServiceEnabled(serviceDesc.uri,enabled)
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

        wxCallAfter(self.statusbar.SetMax, total)
        wxCallAfter(self.statusbar.SetProgress,
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
        
        wxCallAfter(self.statusbar.SetProgress,
                    text,sent, file_done, xfer_done)
        
    def SaveFileDialogCancelled(self):
        return self.statusbar.IsCancelled()      

        
    #
    # File Selection Dialog
    #

    def SelectFile(self,text,defaultFile = "", wildcard = "*.*"):
        filePath = None
        dlg = wxFileDialog(self, text, 
                           defaultFile = defaultFile,
                           wildcard = wildcard,
                           style = wxSAVE)
        
        # Open file dialog
        if dlg.ShowModal() == wxID_OK:
            filePath = dlg.GetPath()
            fileName = (os.path.split(filePath))[1]

            # Check if file already exists
            if os.access(filePath, os.R_OK):
                messageDlg = wxMessageDialog(self, 
                                    "The file %s already exists. Do you want to replace it?"%fileName, 
                                    "Save Text" , 
                                    style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT)
                # Do we want to overwrite?
                if messageDlg.ShowModal() == wxID_NO:
                    log.debug("VenueClientFrame.SaveText: Do not replace existing text file.")
                    # Do not save text; return
                    filePath = None
                messageDlg.Destroy()
                    
        return filePath

    def SelectFiles(self, text):
        fileList = None
        dlg = wxFileDialog(self, text,
                           #defaultFile = name,
                           style = wxOPEN | wxOVERWRITE_PROMPT | wxMULTIPLE)
        if dlg.ShowModal() == wxID_OK:
            fileList = dlg.GetPaths()
            
        dlg.Destroy()

        return fileList
    
    #
    # Prompts, warnings, etc.
    #

    def Prompt(self,text,title):
    
        dlg = wxMessageDialog(self, text, title,
                              style = wxICON_INFORMATION | wxOK | wxCANCEL)
        ret = dlg.ShowModal()
        if ret == wxID_OK:
            return 1
        return 0

    def Notify(self,text,title="Notification"):
    
        wxCallAfter(self.__Notify,text,title)

    def Warn(self,text,title="Warning"):
        wxCallAfter(self.__Warn,text,title)

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
        - calls SetStatusText using wxCallAfter, since the call will be made from a
          thread other than the primary.
        """
        time.sleep(delay)
        wxCallAfter(self.statusbar.SetStatusText,text,0)

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
            MessageDialog(None, "Your connection to the venue is interrupted and you will be removed from the venue.  \nPlease, try to connect again.", 
                          "Lost Connection")

    def AddToMyVenues(self,name,url):
        ID = wxNewId()
        text = "Go to: " + url
        self.navigation.Insert(self.myVenuesPos,ID, name, text)
        self.myVenuesMenuIds[name] = ID
        self.myVenuesDict[name] = url
        EVT_MENU(self, ID, self.GoToMenuAddressCB)
    
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
            self.onExitCalled = true
            log.info("--------- END VenueClient")
            
            # Call close on all open child windows so they can do necessary cleanup.
            # If close is called instead of destroy, an EVT_CLOSE event is distributed
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
        menu = wxMenu()
        
        appDescList = self.controller.GetInstalledApps()

        # Add applications in the appList to the menu
        for app in appDescList:
            if app != None and app.name != None and int(app.startable) == 1:
                menuEntryLabel = prefix + app.name
                appId = wxNewId()
                menu.Append(appId,menuEntryLabel,menuEntryLabel)
                callback = lambda event,theApp=app: self.StartApplicationCB(theApp)
                EVT_MENU(self, appId, callback)

        return menu
        
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
    #        so any wx calls here must be made with wxCallAfter.

    def SetMcastStatus(self,status):
        wxCallAfter(self.__SetMcastStatus,status)
        
    def __SetMcastStatus(self,bool):
        if bool:
            bitmap = icons.getMulticastBitmap()
            shortHelp = 'Multicast available'
        else:
            bitmap = icons.getNoMulticastBitmap()
            shortHelp = 'Multicast not available'
        self.networkButton.SetBitmapLabel(bitmap)
        self.networkButton.SetToolTip(wxToolTip(shortHelp))
        self.toolbar.Realize()
        
    def AddUser(self, profile):
        """
        This method is called every time a venue participant enters
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *profile* The ClientProfile of the participant who entered the venue
        """

        wxCallAfter(self.statusbar.SetStatusText, "%s entered the venue" %profile.name)
        wxCallAfter(self.contentListPanel.AddParticipant, profile)
        self.venueClient.UpdateProfileCache(profile)
        log.debug("  add user: %s" %(profile.name))

    def RemoveUser(self, profile):
        """
        This method is called every time a venue participant exits
        the venue.  Appropriate gui updates are made in client.

        **Arguments:**
        
        *profile* The ClientProfile of the participant who exited the venue
        """

        wxCallAfter(self.statusbar.SetStatusText, "%s left the venue" %profile.name)
        wxCallAfter(self.contentListPanel.RemoveParticipant, profile)
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
        wxCallAfter(self.statusbar.SetStatusText, 
                    "%s changed profile information" %profile.name)
        wxCallAfter(self.contentListPanel.ModifyParticipant, profile)

    def AddData(self, dataDescription):
        """
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        
        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got 
                          added to the venue
        """

        if dataDescription.type == "None" or dataDescription.type == None:
            wxCallAfter(self.statusbar.SetStatusText, "file '%s' has been added to venue" 
                        %dataDescription.name)
            
            # Just change venuestate for venue data.
        else:
            # Personal data is handled in VenueClientUIClasses to find out 
            # who the data belongs to
            pass

        log.debug("EVENT - Add data: %s" %(dataDescription.name))
        wxCallAfter(self.contentListPanel.AddData, dataDescription)

    def UpdateData(self, dataDescription):
        """
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got updated 
                          in the venue
        """
        
        log.debug("EVENT - Update data: %s" %(dataDescription.name))
        wxCallAfter(self.contentListPanel.UpdateData, dataDescription)

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
            wxCallAfter(self.statusbar.SetStatusText, 
                        "file '%s' has been removed from venue"
                        %dataDescription.name)
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass
        
        wxCallAfter(self.statusbar.SetStatusText, 
                    "File '%s' has been removed from the venue" 
                    %dataDescription.name)
        log.debug("EVENT - Remove data: %s" %(dataDescription.name))
        wxCallAfter(self.contentListPanel.RemoveData, dataDescription)

    def AddService(self, serviceDescription):
        """
        This method is called every time new service is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that was added to the venue
        """

        log.debug("EVENT - Add service: %s" %(serviceDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, 
                    "Service '%s' just got added to the venue" 
                    %serviceDescription.name)
        wxCallAfter(self.contentListPanel.AddService, serviceDescription)

    def RemoveService(self, serviceDescription):
        """
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that was removed from the venue
        """

        log.debug("EVENT - Remove service: %s" %(serviceDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, 
                    "Service '%s' has been removed from the venue" 
                    %serviceDescription.name)
        wxCallAfter(self.contentListPanel.RemoveService, serviceDescription)

    def UpdateService(self, serviceDescription):
        """
        This method is called when a service is updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that got updated.
        """
        log.debug("EVENT - Update service: %s" %(serviceDescription.name))
        wxCallAfter(self.SetStatusText, 
                    "Service '%s' just got updated." %serviceDescription.name)
        wxCallAfter(self.contentListPanel.UpdateService, serviceDescription)
    
    def AddApplication(self, appDescription):
        """
        This method is called every time a new application is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that was added to the venue
        """

        log.debug("EVENT - Add application: %s, Mime Type: %s"
                  % (appDescription.name, appDescription.mimeType))
        wxCallAfter(self.statusbar.SetStatusText,
                    "Application '%s' has been added to the venue" %appDescription.name)
        wxCallAfter(self.contentListPanel.AddApplication, appDescription)

    def RemoveApplication(self, appDescription):
        """
        This method is called every time an application is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that was removed from the venue
        """

        log.debug("EVENT - Remove application: %s" %(appDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, 
                    "Application '%s' has been removed from the venue" 
                    %appDescription.name)
        wxCallAfter(self.contentListPanel.RemoveApplication, appDescription)

    def UpdateApplication(self, appDescription):
        """
        This method is called when an application is updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *appDescription* The ApplicationDescription representing the application that should be updated.
        """
        wxCallAfter(self.SetStatusText,
                    "Application '%s' just got updated." %appDescription.name)
        log.debug("EVENT - Update application: %s, Mime Type: %s"
                  % (appDescription.name, appDescription.mimeType))
        wxCallAfter(self.contentListPanel.UpdateApplication, appDescription)


    def AddConnection(self, connDescription):
        """
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Add connection: %s" %(connDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, 
                    "A new exit, '%s', has been added to the venue" 
                    %connDescription.name)  
        wxCallAfter(self.venueListPanel.AddVenueDoor, connDescription)

    def RemoveConnection(self, connDescription):
        """
        This method is called every time an exit is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Remove connection: %s" %(connDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, 
                    "The exit to '%s' has been removed from the venue" 
                    %connDescription.name)  
        wxCallAfter(self.venueListPanel.RemoveVenueDoor, connDescription)


    def SetConnections(self, connDescriptionList):
        """
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescriptionList* A list of ConnectionDescriptions representing all the exits in the venue.
        """
        log.debug("EVENT - Set connections")
        wxCallAfter(self.venueListPanel.CleanUp)

        for connection in connDescriptionList:
            log.debug("EVENT - Add connection: %s" %(connection.name))
            wxCallAfter(self.venueListPanel.AddVenueDoor, connection)

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
        
        wxCallAfter(self.textClientPanel.OutputText, name, text)

    def OpenApplication(self, appCmdDesc):
        '''
        This method is called when someone wants to invite you to a
        shared application session.
        '''
        wxCallAfter(self.__OpenApplication, appCmdDesc)

    def EnterVenue(self, URL, warningString="", enterSuccess=1):
        """
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
      
        **Arguments:**
        
        *URL* A string including the venue address we want to connect to
        *back* Boolean value, true if the back button was pressed, else false.
        
        """
        log.debug("bin.VenueClient::EnterVenue: Enter venue with url: %s", URL)
    
        # Show warnings, do not enter venue
        if not enterSuccess:
            # Currently receives type of error in warningString.
            # This will go back catching an exception with vc redesign.
            # For now, show all warnings to user
            
            if warningString == "NotAuthorized":
                text = "You are not authorized to enter the venue located at %s.\n." % URL
                wxCallAfter(MessageDialog, None, text, "Notification")
            elif warningString.startswith("Authorization failure connecting to server"):
                text = warningString
                wxCallAfter(self.Notify, text, "Authorization failure")
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
                wxCallAfter(self.Notify, text, "Can not enter venue")
                wxCallAfter(self.statusbar.SetStatusText, "" )

            return
               
        # initialize flag in case of failure
        enterUISuccess = 1

        try:

            #
            # Reflect venue entry in the client
            #
            wxCallAfter(self.textClientPanel.OutputText, None,
                        "-- Entered venue %s" % self.venueClient.GetVenueName())
            wxCallAfter(self.textClientPanel.OutputText, "enter",
                        self.venueClient.GetVenueDescription())
            
            wxCallAfter(self.statusbar.SetStatusText, "Entered venue %s successfully" 
                        %self.venueClient.GetVenueName())

            # clean up ui from current venue before entering a new venue
            if self.venueClient.GetVenue() != None:
                # log.debug("clean up frame")
                wxCallAfter(self.__CleanUp)

            # Get current state of the venue
            venueState = self.venueClient.GetVenueState()
            
            # Update the UI
            wxCallAfter(self.venueAddressBar.SetTitle,
                            venueState.name, venueState.description) 

            # Load clients
            # log.debug("Add participants")
            wxCallAfter(self.statusbar.SetStatusText,
                            "Load participants")
            for client in venueState.clients.values():
                wxCallAfter(self.contentListPanel.AddParticipant,
                            client)
                # log.debug("   %s" %(client.name))

            # Load data
            # log.debug("Add data")
            wxCallAfter(self.statusbar.SetStatusText, "Load data")
            for data in venueState.data.values():
                wxCallAfter(self.contentListPanel.AddData, data)
                # log.debug("   %s" %(data.name))

            # Load services
            # log.debug("Add service")
            wxCallAfter(self.statusbar.SetStatusText,
                        "Load services")
            for service in venueState.services.values():
                wxCallAfter(self.contentListPanel.AddService,
                            service)
                # log.debug("   %s" %(service.name))

            # Load applications
            # log.debug("Add application")
            wxCallAfter(self.statusbar.SetStatusText,
                        "Load applications")
            for app in venueState.applications.values():
                wxCallAfter(self.contentListPanel.AddApplication,
                            app)
                # log.debug("   %s" %(app.name))

            #  Load exits
            # log.debug("Add exits")
            wxCallAfter(self.statusbar.SetStatusText, "Load exits")
            wxCallAfter(self.venueListPanel.AddConnections)
                # log.debug("   %s" %(conn.name))

           

            wxCallAfter(self.SetVenueUrl, URL)
                                              
            # Enable menus
            wxCallAfter(self.__ShowMenu)
            
            #
            # Enable the application menu that is displayed over
            # the Applications items in the list
            # (this is not the app menu above)
            wxCallAfter(self.__EnableAppMenu, true)

            # Update the UI
            wxCallAfter(self.AddVenueToHistory, URL)
            
            log.debug("Entered venue")
            
            #
            # Display all non fatal warnings to the user
            #
            if warningString != '': 
                message = "Following non fatal problems have occured when you entered the venue:\n" + warningString
                wxCallAfter(self.Notify, message, "Notification")
                
                wxCallAfter(self.statusbar.SetStatusText, 
                            "Entered %s successfully" %self.venueClient.GetVenueName())
       
        except Exception, e:
            log.exception("bin.VenueClient::EnterVenue failed")
            enterUISuccess = 0

        if not enterUISuccess:
            text = "You have not entered the venue located at %s.\nAn error occured.  Please, try again."%URL
            wxCallAfter(self.Error, text, "Enter Venue Error")
            

    def ExitVenue(self):
        wxCallAfter(self.__CleanUp)
        wxCallAfter(self.venueAddressBar.SetTitle,
                    "You are not in a venue",
                    'Click "Go" to connect to the venue, which address is displayed in the address bar')

        wxCallAfter(self.textClientPanel.Clear)

        # Disable menus
        wxCallAfter(self.__HideMenu)
        
        # Stop shared applications
        self.controller.StopApplications()


    def HandleError(self,err):
        if isinstance(err,DisconnectError):
            wxCallAfter(MessageDialog, None, 
                        "Your connection to the venue is interrupted and you will be removed from the venue.  \nPlease, try to connect again.", 
                        "Lost Connection")
        else:
            log.info("Unhandled observer exception in VenueClientUI")
            
    def UpdateMulticastStatus(self,status):
        wxCallAfter(self.__SetMcastStatus,status)


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

class VenueAddressBar(wxSashLayoutWindow):
    ID_GO = wxNewId()
    ID_BACK = wxNewId()
    ID_ADDRESS = wxNewId()
    
    def __init__(self, parent, id, venuesList, defaultVenue):
        wxSashLayoutWindow.__init__(self, parent, id,
                                    wxDefaultPosition, 
                                    wxDefaultSize)
        self.parent = parent
        self.addressPanel = wxPanel(self, -1, style = wxRAISED_BORDER)
        self.titlePanel =  wxPanel(self, -1, style = wxRAISED_BORDER)
        self.title = wxStaticText(self.titlePanel, wxNewId(),
                                  'You are not in a venue',
                                  style = wxALIGN_CENTER)
        font = wxFont(14, wxSWISS, wxNORMAL, wxNORMAL, false)
        self.title.SetFont(font)
        self.address = wxComboBox(self.addressPanel, self.ID_ADDRESS,
                                  defaultVenue,
                                  choices = venuesList.keys(),
                                  style = wxCB_DROPDOWN)
        self.goButton = wxButton(self.addressPanel, self.ID_GO, "Go",
                             wxDefaultPosition, wxSize(40, 21))
        self.goButton.SetToolTip(wxToolTip("Enter venue"))
        self.backButton = wxBitmapButton(self.addressPanel, self.ID_BACK ,
                                         icons.getPreviousBitmap(),
                                         wxDefaultPosition, wxSize(40, 21))
        self.backButton.SetToolTip(wxToolTip("Go to previous venue"))
        self.__Layout()
        self.__AddEvents()
        
    def __AddEvents(self):
        EVT_BUTTON(self, self.ID_GO, self.CallAddress)
        EVT_BUTTON(self, self.ID_BACK, self.GoBack)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.CallAddress)
        EVT_SIZE(self,self.__OnSize)
        
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
        self.__Layout()

    def AddChoice(self, url):
        if self.address.FindString(url) == wxNOT_FOUND:
            self.address.Append(url)
        self.SetAddress(url)
            
    def __Layout(self):
        venueServerAddressBox = wxBoxSizer(wxVERTICAL)
        
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.backButton, 0, wxRIGHT|wxLEFT|wxALIGN_CENTER, 5)
        box.Add(self.address, 1, wxRIGHT, 5)
        box.Add(self.goButton, 0, wxRIGHT|wxALIGN_CENTER, 5)
        self.addressPanel.SetSizer(box)

        titleBox = wxBoxSizer(wxHORIZONTAL)
        titleBox.Add(self.title, 1, wxCENTER)
        self.titlePanel.SetSizer(titleBox)

        venueServerAddressBox.Add(self.addressPanel, 0, wxEXPAND)
        venueServerAddressBox.Add(self.titlePanel, 1, wxEXPAND)
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

class VenueListPanel(wxSashLayoutWindow):
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
        wxSashLayoutWindow.__init__(self, parent, id)
        self.parent = parent
        self.app = app
        self.choices = {'Exits':Preferences.EXITS,
                   'All Venues':Preferences.ALL_VENUES,
                   'My Venues':Preferences.MY_VENUES}
        self.viewSelector = wxComboBox(self,-1,choices=self.choices.keys(),
                                       style=wxCB_READONLY)
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
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
                
    def __AddEvents(self):
        EVT_SIZE(self,self.__OnSize)
        EVT_COMBOBOX(self,self.viewSelector.GetId(),self.__OnViewSelect)
    
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
        panelSizer = wxBoxSizer(wxHORIZONTAL)
        panelSizer.Add(self.viewSelector, 1, wxEXPAND)

        venueListPanelSizer = wxBoxSizer(wxVERTICAL)
        venueListPanelSizer.Add(panelSizer, 0, wxEXPAND)
        venueListPanelSizer.Add(self.list, 1, wxEXPAND)

        self.SetSizer(venueListPanelSizer)
        w,h = self.GetSizeTuple()
        self.GetSizer().SetDimension(5,5,w-10,h-7)

    def Hide(self):
        currentHeight = self.GetSize().GetHeight()
        self.viewSelector.Hide()
        s = wxSize(180, 1000)
        self.parent.UpdateLayout(self, s)
       
    def Show(self):
        currentHeight = self.GetSize().GetHeight()
        self.viewSelector.Show()
        s = wxSize(180, 1000)
        self.parent.UpdateLayout(self, s)
  
    def CleanUp(self):
        self.list.CleanUp()
        
    def AddVenueDoor(self,connectionDescription):
        self.list.AddVenueDoor(connectionDescription)

    def AddConnections(self):
        displayMode = self.GetDisplayMode()
        if displayMode == Preferences.EXITS or displayMode == Preferences.ALL_VENUES:
            self.list.UpdateView()
        
    def RemoveVenueDoor(self,connectionDescription):
        self.list.RemoveVenueDoor(connectionDescription)

class NavigationPanel(wxPanel):
    ID_EXITS = wxNewId()
    ID_MY_VENUES = wxNewId()
    ID_ALL = wxNewId()
    
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1, size=wxSize(175, 300))
        self.tree = wxTreeCtrl(self, wxNewId(), wxDefaultPosition, 
                               wxDefaultSize, style = wxTR_HAS_BUTTONS |
                               wxTR_LINES_AT_ROOT | wxTR_HIDE_ROOT |
                               wxTR_SINGLE )
        self.app = app
        self.parent = parent

        
        EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        EVT_LEFT_DOWN(self.tree, self.OnLeftDown)
        EVT_RIGHT_DOWN(self.tree, self.OnRightDown)
        EVT_MENU(self, self.ID_EXITS, self.OnExitsMenu)
        EVT_MENU(self, self.ID_MY_VENUES, self.OnMyVenuesMenu)
        EVT_MENU(self, self.ID_ALL, self.OnAllMenu)
        EVT_SIZE(self, self.__OnSize)
        
        self.root = self.tree.AddRoot("ROOT")
        self.UpdateView()
        self.__Layout()
        
        self.menu = wxMenu()
        self.addToMyVenuesId = wxNewId()
        self.menu.Append(self.addToMyVenuesId,'Add to My Venues')
        EVT_MENU(self.menu,self.addToMyVenuesId,self.__OnAddToMyVenues)

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
        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))

        # Check to see if the click was made on the tree item text.
        if not treeId.IsOk() or not flag & wxTREE_HITTEST_ONITEMLABEL:
            return

        wxBeginBusyCursor()
        venue = self.tree.GetPyData(treeId)
        self.app.controller.EnterVenueCB(venue.uri)
        wxEndBusyCursor()
                
    def OnLeftDown(self, event):
        '''
        Called when user clicks the tree
        '''
        
        self.x = event.GetX()
        self.y = event.GetY()
        exits = None

        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))

        # Check to see if the click hit the twist button
        
        if not treeId.IsOk():
            return
            
        if not(flag & wxTREE_HITTEST_ONITEMBUTTON):
            self.tree.SelectItem(treeId)
            return

        child, cookie = self.tree.GetFirstChild(treeId)
       
        if self.tree.GetItemText(child) == "temp node":
            # Remove temporary node
            self.tree.DeleteChildren(treeId)

        venue = self.tree.GetPyData(treeId)

        exits = None
        if venue:
            exits = VenueIW(venue.uri).GetConnections()
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
            self.tree.SetItemData(newItem, wxTreeItemData(exit)) 
                       
        event.Skip()
                               
    def OnRightDown(self, event):
        '''
        Called when user clicks the tree
        '''
        
        self.x = event.GetX()
        self.y = event.GetY()
        exits = None

        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))

        # Check to see if the click hit the twist button
        
        if not treeId.IsOk():
            return
            
        if not(flag & wxTREE_HITTEST_ONITEMBUTTON):
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
        self.tree.SetItemData(newItem, wxTreeItemData(venue)) 
      
 
    def UpdateView(self, displayMode = None):
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
        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(self.tree, 1, wxEXPAND)
        self.SetSizer(sizer)

        w,h = self.GetSizeTuple()
        self.GetSizer().SetDimension(0,0,w,h)
        

#############################################################################
#
# Content List Panel
    
class ContentListPanel(wxPanel):                   
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
    
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, 
                         wxSize(225, 300), style = wxSUNKEN_BORDER)
        id = wxNewId()
        self.participantDict = {}
        self.dataDict = {}
        self.serviceDict = {}
        self.applicationDict = {}
        self.personalDataDict = {}
        self.temporaryDataDict = {}
        self.parent = parent

        self.tree = wxTreeCtrl(self, id, wxDefaultPosition, 
                               wxDefaultSize, style = wxTR_HAS_BUTTONS |
                               wxTR_LINES_AT_ROOT | wxTR_HIDE_ROOT |
                               wxTR_MULTIPLE)
        
        self.__SetImageList()
        self.__SetTree()
               
        EVT_SIZE(self, self.OnSize)
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown)
        EVT_TREE_ITEM_EXPANDING(self.tree, id, self.OnExpand)
        #EVT_TREE_BEGIN_DRAG(self.tree, id, self.OnBeginDrag) 
        EVT_TREE_SEL_CHANGED(self.tree, id, self.OnSelect)
       
    def __SetImageList(self):
        imageSize = 22

        wxInitAllImageHandlers()
        imageList = wxImageList(imageSize,imageSize)

        bm = icons.getBulletBitmap()
        self.bullet = imageList.Add(bm)
                
        bm = icons.getDefaultParticipantBitmap()
        self.participantId = imageList.Add(bm)
               
        bm = icons.getDefaultDataBitmap()
        self.defaultDataId = imageList.Add(bm)
        
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
                log.debug("ContentListPanel.__GetPersonalDataFromItem: First child's name = %s " %(d.name))
                for nr in range(self.tree.GetChildrenCount(treeId)-1):
                    id, cookie = self.tree.GetNextChild(treeId, cookie)
                    dataList.append(self.tree.GetPyData(id))
                    log.debug("ContentListPanel.__GetPersonalDataFromItem: Next child's name = %s " %self.tree.GetPyData(id).name)
                    
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
      
        colour = wxTheColourDatabase.FindColour("NAVY")
        self.tree.SetItemTextColour(self.participants, colour)
        self.tree.SetItemTextColour(self.data, colour)
        self.tree.SetItemTextColour(self.services, colour)
        self.tree.SetItemTextColour(self.applications, colour)
               
        self.tree.Expand(self.participants)
      
    def GetLastClickedTreeItem(self):
        # x and y is set when we right click on a participnat
        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
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

        log.debug("ContentListPanel.AddParticipant:: AddParticipant %s (called from %s)", 
                  profile.name,
                  (traceback.extract_stack())[-2])

        # Add the participant to the list
        participant = self.tree.AppendItem(self.participants, profile.name, 
                                           imageId, imageId)
        self.tree.SetItemData(participant, wxTreeItemData(profile)) 
        if profile.profileType == 'jabber':
            GRAY = wxColour(100,100,100)
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

    def AddData(self, dataDescription):
        #if venue data
        if(dataDescription.type == 'None' or dataDescription.type == None):
        
            # replace http-encoded spaces with spaces;
            # this should be done elsewhere, but is done here for now
            dataDescription.uri = dataDescription.uri.replace('%20',' ')
            
            dataId = self.tree.AppendItem(self.data, dataDescription.name,
                                      self.defaultDataId, self.defaultDataId)
            self.tree.SetItemData(dataId, wxTreeItemData(dataDescription)) 
            self.dataDict[dataDescription.id] = dataId
            self.tree.SortChildren(self.data)
            self.tree.Refresh()
            
       
    def UpdateData(self, dataDescription):
        id = None

        #if venue data
        if(self.dataDict.has_key(dataDescription.id)):
            log.debug("ContentListPanel.UpdateData: DataDict has data")
            id = self.dataDict[dataDescription.id]
            
        if(id != None):
            self.tree.SetItemData(id, wxTreeItemData(dataDescription))
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

    def AddService(self, serviceDescription):
        service = self.tree.AppendItem(self.services, serviceDescription.name,
                                      self.serviceId, self.serviceId)
        self.tree.SetItemData(service, wxTreeItemData(serviceDescription)) 
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
        self.tree.SetItemData(application, wxTreeItemData(appDesc))
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
        mainBox=wxBoxSizer(wxHORIZONTAL)
        mainBox.Add(self.tree,1,wxEXPAND)
        self.SetSizer(mainBox)
        self.Layout()

    def OnSize(self, event):
        self.__Layout()
        #w,h = self.GetClientSizeTuple()
        #self.tree.SetDimensions(0, 0, w, h)
        
    def OnKeyDown(self, event):
        key = event.GetKeyCode()
      
        if key == WXK_DELETE:
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
        dropData = wxTextDataObject()
        dropData.SetText(text)

        dropSource = wxDropSource(self)
        dropSource.SetData(dropData)

        dropSource.DoDragDrop(wxDrag_AllowMove)
                                
    def OnExpand(self, event):
        treeId = event.GetItem()
        item = self.tree.GetItemData(treeId).GetData()

        if item:
            try:
                dataDescriptionList = self.parent.GetPersonalData(item)
                          
                if dataDescriptionList:
                    for data in dataDescriptionList:
                        self.AddData(data)
            except:
                log.exception("ContentListPanel.OnExpand: Could not get personal data.")
                MessageDialog(None, "%s's data could not be retrieved."%item.name)
                
    def OnDoubleClick(self, event):
        mimeConfig = Config.MimeConfig.instance()
        self.x = event.GetX()
        self.y = event.GetY()
        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
        ext = None
        name = None
        
        if(treeId.IsOk() and flag & wxTREE_HITTEST_ONITEMLABEL):
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
                
    def OnRightClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()

        if self.parent.GetVenue() == None:
            return
        
        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
      
        if(treeId.IsOk()):

            if len(self.tree.GetSelections()) <= 1:
                # Keep selection if more than one item is selected to
                # enable multiple deletions.
                self.tree.SelectItem(treeId)
                
            item = self.tree.GetItemData(treeId).GetData()
            text = self.tree.GetItemText(treeId)
                        
            if text == self.DATA_HEADING:
                self.PopupMenu(self.parent.dataHeadingMenu,
                               wxPoint(self.x, self.y))
            elif text == self.SERVICES_HEADING:
                self.PopupMenu(self.parent.serviceHeadingMenu,
                               wxPoint(self.x, self.y))
            elif text == self.APPLICATIONS_HEADING:
                self.PopupMenu(self.parent.BuildAppMenu("Add "),
                               wxPoint(self.x, self.y))
            elif text == self.PARTICIPANTS_HEADING or item == None:
                # We don't have anything to do with this heading
                pass
            
            #elif isinstance(item, AGNetworkServiceDescription):
            #    menu = self.BuildNetworkServiceMenu(event, item)
            #    self.PopupMenu(menu, wxPoint(self.x, self.y))
            
            elif isinstance(item, ServiceDescription):
                menu = self.BuildServiceMenu(event, item)
                self.PopupMenu(menu, wxPoint(self.x,self.y))

            elif isinstance(item, ApplicationDescription):
                menu = self.BuildAppMenu(item)
                self.PopupMenu(menu, wxPoint(self.x, self.y))

            elif isinstance(item, DataDescription):
                menu = self.BuildDataMenu(event, item)
                self.PopupMenu(menu, wxPoint(self.x,self.y))
                parent = self.tree.GetItemParent(treeId)
                
            elif isinstance(item,ClientProfile):
                log.debug("ContentListPanel.OnRightClick: Is this me? connectionId is = %s, my id = %s "
                          % (item.connectionId, self.parent.GetProfile().connectionId))
                if(item.connectionId == self.parent.GetProfile().connectionId):
                    log.debug("ContentListPanel.OnRightClick: This is me")
                    self.PopupMenu(self.parent.meMenu, wxPoint(self.x, self.y))
         
                else:
                    log.debug("ContentListPanel.OnRightClick: This is a user")
                    self.PopupMenu(self.parent.participantMenu,
                                   wxPoint(self.x, self.y))
                                   
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
        menu = wxMenu()

        # - Open
        id = wxNewId()
        menu.Append(id, "Open", "Open this data.")
        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: 
                     self.parent.StartCmd(itm, verb='Open'))
        else:
            EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))

        # - Save
        id = wxNewId()
        menu.Append(id, "Save", "Save this item locally.")
        EVT_MENU(self, id, lambda event: self.parent.SaveDataCB(event))
        
        # - Delete
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this data from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveDataCB(event))

        # - type-specific commands
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             verb=key, itm=item: 
                             self.parent.StartCmd(itm, verb=verb))

        menu.AppendSeparator()

        # - Properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this data.")
        EVT_MENU(self, id, lambda event, item=item:
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
        menu = wxMenu()

        # - Open
        id = wxNewId()
               
        menu.Append(id, "Open", "Open this service.")
       
        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: 
                     self.parent.StartCmd(itm, verb='Open'))
        else:
            EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))
                   
        # - type-specific commands
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             verb=key, itm=item: 
                             self.parent.StartCmd(itm, verb=verb))

        menu.AppendSeparator()

        # - Properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this service.")
        EVT_MENU(self, id, lambda event, item=item:
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
        menu = wxMenu()

        # - Open
        id = wxNewId()
               
        menu.Append(id, "Open", "Open this service.")
       
        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: 
                     self.parent.StartCmd(itm, verb='Open'))
        else:
            EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))

        # - Delete
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this service from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveServiceCB(event))
            
        # - type-specific commands
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             verb=key, itm=item: 
                             self.parent.StartCmd(itm, verb=verb))

        menu.AppendSeparator()

        # - Properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this service.")
        EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def FindUnregistered(self, item):
        dlg = wxMessageDialog(None,
                        "There is nothing registered for this kind of data." \
                        "Would you like to search for a program?",
                        style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT)
        val = dlg.ShowModal()
        dlg.Destroy()

        if val == wxID_YES:
            # do the find a file thing
            wildcard = "All Files (*.*)|*.*|"\
                       "Executables (*.exe)|*.exe|"\
                       "Compiled Python Scripts (*.pyc)|*.pyc|"\
                       "Python Source Files (*.py)|*.py|"\
                       "Batch Files (*.bat)|*.bat"
            
            dlg = wxFileDialog(None, "Choose the program", "",
                               "", wildcard, wxOPEN)
            if dlg.ShowModal() == wxID_OK:
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
        menu = wxMenu()
        
        # - Open
        id = wxNewId()
        menu.Append(id, "Open", "Open application and join the session.")

       
        if commands != None and 'Open' in commands:
            EVT_MENU(self, id, lambda event, cmd='Open':
                     self.parent.StartCmd(item,verb='Open'))


            # - Open for All Participants
            key = 'Open for All Participants'
            id = wxNewId()
            menu.Append(id, key, "Open application for all participants in the venue.")
            EVT_MENU(self, id, lambda event, verb=key, itm=item:
                     self.parent.StartAllCmd(item,verb=key))
            
        else:
            text = "You have nothing configured to open this application."
            title = "Notification"
            EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wxOK|wxICON_INFORMATION))
       
        # - Delete
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this application.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveApplicationCB(event))

        menu.AppendSeparator()
            
        # - type-specific commands
        othercmds = 0
        if commands != None:
            for key in commands:
                if key != 'Open' and key != 'Open for All Participants':
                    othercmds = 1
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event, verb=key, itm=item:
                             self.parent.StartCmd(item,verb=verb))
        if othercmds:
            menu.AppendSeparator()

        # - Application Monitor
        id = wxNewId()
        menu.Append(id, "Open Monitor...", 
                    "View data and participants present in this application session.")
        EVT_MENU(self, id, lambda event: self.parent.MonitorAppCB(item))

        # - Application Monitor
        menu.AppendSeparator()
        
        # Add properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this application.")
        EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def LookAtProperties(self, desc):
        """
        """
              
        if isinstance(desc, DataDescription):
            dataView = DataPropertiesDialog(self, -1, "Data Properties")
            dataView.SetDescription(desc)
            if dataView.ShowModal() == wxID_OK:
                # Get new description
                newDesc = dataView.GetDescription()
                               
                # If name is different, change data in venue
                if newDesc.name != desc.name:
                    try:
                        self.parent.UpdateDataCB(newDesc)
                    except:
                        log.exception("VenueClientUIClasses: Update data failed")
                        MessageDialog(None, "Update data failed.", "Notification", 
                                      style = wxOK|wxICON_INFORMATION) 
            
            dataView.Destroy()

        #elif isinstance(desc, AGNetworkServiceDescription):
        #    serviceView = ServicePropertiesDialog(self, -1, "Service Properties")
        #    serviceView.SetDescription(desc)
        #    serviceView.ShowModal()
        #    serviceView.Destroy()
            
        elif isinstance(desc, ServiceDescription):
            serviceView = ServicePropertiesDialog(self, -1, "Service Properties")
            serviceView.SetDescription(desc)
            if(serviceView.ShowModal() == wxID_OK):
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
                                      style = wxOK|wxICON_INFORMATION)
                                           
            serviceView.Destroy()
        elif isinstance(desc, ApplicationDescription):
            serviceView = ApplicationPropertiesDialog(self, -1, "Application Properties")
            serviceView.SetDescription(desc)
            # Get new description
            if(serviceView.ShowModal() == wxID_OK):
                newDesc = serviceView.GetDescription()
              
                # If name or description is different, change the application in venue
                if newDesc.name != desc.name or newDesc.description != desc.description:
                    try:
                        self.parent.UpdateApplicationCB(newDesc)
                    except:
                        MessageDialog(None, "Update application failed.", 
                                      "Notification", style = wxOK|wxICON_INFORMATION)
                                            
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

#########################################################################
#
# Jabber Client Panel

class TextPanelSash(wxSashLayoutWindow):
    
    def __init__(self, parent, id):
        wxSashLayoutWindow.__init__(self, parent, id)
        self.parent = parent
        self.textClientPanel = JabberClientPanel(self, -1)#wxPanel(self, -1)
        EVT_SIZE(self, self.__OnSize)
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
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.textClientPanel, 1, wxEXPAND)
        w,h = self.GetSizeTuple()
        self.SetSizer(box)
        self.GetSizer().SetDimension(5,5,w-10,h-10)

class JabberClientPanel(wxPanel):
    
    ID_BUTTON = wxNewId()
    ID_WINDOW_TOP = wxNewId()
    client =''

    def __init__(self, parent, id):
        wxPanel.__init__(self, parent, id)
        self.sashWindow = wxSashLayoutWindow(
            self, self.ID_WINDOW_TOP, wxDefaultPosition, (200, 30), 
            wxNO_BORDER)
        
        self.sashWindow.SetDefaultSize((1000, 60))
        self.sashWindow.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.sashWindow.SetAlignment(wxLAYOUT_TOP)
        self.sashWindow.SetSashVisible(wxSASH_BOTTOM, True)

        self.outputPanel = wxPanel(self.sashWindow, -1)
        self.textOutput = wxTextCtrl(self.outputPanel, wxNewId(), "",
                                     style= wxTE_MULTILINE | wxTE_READONLY |
                                     wxTE_RICH|wxTE_AUTO_URL) 
        self.app = parent.parent
        self.panel = wxPanel(self, -1)
        self.display = wxButton(self.panel, self.ID_BUTTON, "Display",
                                style = wxBU_EXACTFIT)
        self.textInput = wxTextCtrl(self.panel, wxNewId(), "",
                                    size = wxSize(-1, 25),
                                    style= wxTE_MULTILINE)
        self.panelHeight = None


        self.parent = parent
        self.display.SetToolTip(wxToolTip("Send text message"))
        
        self.__DoLayout()

        EVT_TEXT_URL(self.textOutput, self.textOutput.GetId(), self.OnUrl)
        EVT_CHAR(self.textOutput, self.ChangeTextWindow)
        EVT_CHAR(self.textInput, self.TestEnter) 
        EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
        EVT_SIZE(self, self.__OnSize)
        EVT_SASH_DRAGGED(self, self.ID_WINDOW_TOP, 
                         self.__OnSashDrag)
        self.Show(true)

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
            self.sashWindow.SetDefaultSize(wxSize(1000, h))
            self.outputPanel.SetSize(wxSize(1000, h-5))
    
        wxLayoutAlgorithm().LayoutWindow(self, self.panel)
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
        
        self.sashWindow.SetDefaultSize(wxSize(1000, sashHeight))
        self.outputPanel.SetSize(wxSize(1000, sashHeight-5))
        wxLayoutAlgorithm().LayoutWindow(self, self.panel)
             
    def __DoLayout(self):
        '''
        Handles UI layout.
        '''
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.textInput, 1, wxALIGN_CENTER | wxEXPAND |
                wxLEFT | wxRIGHT | wxBOTTOM, 5)
        box.Add(self.display, 0, wxALIGN_CENTER |wxALL, 2)

        self.panel.SetSizer(box)
        box.Fit(self.panel)
        self.panel.SetAutoLayout(1)

        box2 = wxBoxSizer(wxHORIZONTAL)
        box2.Add(self.textOutput, 1, wxEXPAND)
        self.outputPanel.SetSizer(box2)
        box2.Fit(self.outputPanel)
        self.outputPanel.SetAutoLayout(1)

        sizer = wxBoxSizer(wxHORIZONTAL)
        sizer.Add(self.outputPanel, 1, wxEXPAND)
        self.sashWindow.SetSizer(sizer)
        
    def __OutputText(self, name, message):
        '''
        Prints received text in the text chat.
        **Arguments**
        *name* Statement to put in front of message (for example; "You say,").
        *message* The actual message.
        '''
               
        # Event message
        if name == None:
            # Add time to event message
            dateAndTime = strftime("%a, %d %b %Y, %H:%M:%S", localtime() )
            message = message + " ("+dateAndTime+")" 

            # Events are coloured blue
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLUE))
            self.textOutput.AppendText(message+'\n')
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLACK))

        elif name == "enter":
            # Descriptions are coloured black
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLACK))
            self.textOutput.AppendText(message+'\n')
        # Someone is writing a message
        else:
            # Set names bold
            pointSize = wxDEFAULT

            # Fix for osx
            pointSize = wxNORMAL_FONT.GetPointSize()

            # Fix for osx
            if IsOSX():
                pointSize = 12
                           
            f = wxFont(pointSize, wxDEFAULT, wxNORMAL, wxBOLD)
            textAttr = wxTextAttr(wxBLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)

            # Detect /me
            if message.startswith("/me ") and len(message.strip()) > 3:
                nameText = name[:-2] # remove trailing ": "
                messageText = " " + message[4:] + "\n"
            else:
                nameText = name
                messageText = message + '\n'

            self.textOutput.AppendText(nameText)
          
            # Set text normal
            f = wxFont(pointSize, wxDEFAULT, wxNORMAL, wxNORMAL)
            textAttr = wxTextAttr(wxBLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)
            self.textOutput.AppendText(messageText)

        if IsWindows():
            # Scrolling is not correct on windows when I use
            # wxTE_RICH flag in text output window.
            self.SetRightScroll()

    def OutputText(self, name, message):
        '''
        Print received text in text chat.
        
        **Arguments**
        *name* Statement to put in front of message (for example; "You say,").
        *message* The actual message.
        '''
        wxCallAfter(self.__OutputText, name, message)

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
                MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
        except Exception, e:
            self.textInput.Clear()
            log.exception(e)
            text = "Could not send text message successfully"
            title = "Notification"
            log.error(text)
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
     
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
        if key == WXK_RETURN:
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
        if event.GetMouseEvent().GetButton() == wxMOUSE_BTN_NONE:
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
        # Added due to wxPython bug. The wxTextCtrl doesn't
        # scroll properly when the wxTE_AUTO_URL flag is set. 
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


class StatusBar(wxStatusBar):
    def __init__(self, parent):
        wxStatusBar.__init__(self, parent, -1)
        self.sizeChanged = False
        self.parent = parent
        EVT_SIZE(self, self.OnSize)
        
        self.progress = wxGauge(self, wxNewId(), 100,
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)
        self.progress.SetValue(True)

        self.cancelButton = wxButton(self, wxNewId(), "Cancel")
        EVT_BUTTON(self, self.cancelButton.GetId(), self.OnCancel)

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
        self.progress.SetPosition(wxPoint(rect.x+2, rect.y+2))
        self.progress.SetSize(wxSize(rect.width-4, rect.height-4))
               
        # Cancel button
        rect = self.GetFieldRect(2)
        self.cancelButton.SetPosition(wxPoint(rect.x+2, rect.y+2))
        self.cancelButton.SetSize(wxSize(50, rect.height-2))
        
        
        
################################################################################
#
# Dialogs


class UrlDialog(wxDialog):
    def __init__(self, parent, id, title, address = "", text = None):
        wxDialog.__init__(self, parent, id, title)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        if text == None:
            info = "Please, enter venue URL address"
        else:
            info = text
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Address: ", style=wxALIGN_LEFT)
        self.address = wxTextCtrl(self, -1, address, size = wxSize(300,-1))
        self.__Layout()
        
    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxBoxSizer(wxVERTICAL)
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
        #self.Layout()
        
    def GetValue(self):
        return self.address.GetValue()

    
 
################################################################################

class ProfileDialog(wxDialog):
    def __init__(self, parent, id, title, validate):
        wxDialog.__init__(self, parent, id, title,
                          style = wxDEFAULT_DIALOG_STYLE | wxRESIZE_BORDER)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        if validate:
            self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,-1),
                                       validator = TextValidator("Name"))
        else:
            # Don't use a validator
            self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,-1))
        self.emailText = wxStaticText(self, -1, "Email:", style=wxALIGN_LEFT)
        if validate:
            self.emailCtrl = wxTextCtrl(self, -1, "",
                                       validator = TextValidator("Email"))
        else:
            # Don't use a validator
            self.emailCtrl = wxTextCtrl(self, -1, "")
        self.phoneNumberText = wxStaticText(self, -1, "Phone Number:",
                                            style=wxALIGN_LEFT)
        self.phoneNumberCtrl = wxTextCtrl(self, -1, "")
        self.locationText = wxStaticText(self, -1, "Location:")
        self.locationCtrl = wxTextCtrl(self, -1, "")
        self.homeVenue= wxStaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wxTextCtrl(self, -1, "")
        self.profileTypeText = wxStaticText(self, -1, "Profile Type:",
                                            style=wxALIGN_LEFT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.profile = None
        self.profileTypeBox = None
        
        self.titleText = wxStaticText(self,-1,"Profile")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        self.__Layout()
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.emailCtrl.SetEditable(false)
            self.phoneNumberCtrl.SetEditable(false)
            self.locationCtrl.SetEditable(false)
            self.homeVenueCtrl.SetEditable(false)
            if isinstance(self.profileTypeBox,wxTextCtrl):
                self.profileTypeBox.SetEditable(false)
        else:
            self.nameCtrl.SetEditable(true)
            self.emailCtrl.SetEditable(true)
            self.phoneNumberCtrl.SetEditable(true)
            self.locationCtrl.SetEditable(true)
            self.homeVenueCtrl.SetEditable(true)
            if isinstance(self.profileTypeBox,wxTextCtrl):
                self.profileTypeBox.SetEditable(true)
            
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __Layout(self):
        self.sizer1 = wxBoxSizer(wxVERTICAL)
        #box = wxStaticBox(self, -1, "Profile")
        #box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        #sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        self.gridSizer = wxFlexGridSizer(0, 2, 4, 5)
        self.gridSizer.Add(self.nameText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 0, wxEXPAND, 0)
        self.gridSizer.AddGrowableCol(1)
        
        self.gridSizer.Add(self.phoneNumberText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wxALIGN_LEFT, 0)
        if self.profileTypeBox:
            self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND)
            
        self.sizer1.Add(self.titleText,0,wxEXPAND|wxALL,10)
        self.sizer1.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        self.sizer1.Add(self.gridSizer, 1, wxALL|wxEXPAND, 10)
        self.sizer1.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)

        #self.sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxEAST, 10)
        sizer3.Add(self.cancelButton, 0)

        self.sizer1.Add(sizer3, 0, wxALIGN_CENTER|wxALL, 10)

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
        self.profileTypeBox = wxComboBox(self, -1, self.selections[0],
                                         choices = self.selections, 
                                         style = wxCB_READONLY)
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

        self.__SetEditable(true)
        log.debug("ProfileDialog.SetProfile: Set profile information successfully in dialog")
        
    def SetDescription(self, item):
        log.debug("ProfileDialog.SetDescription: Set description in dialog name:%s, email:%s, phone:%s, location:%s home:%s, dn:%s"
                   %(item.name, item.email,item.phoneNumber,item.location,
                     item.homeVenue, item.distinguishedName))
        self.profileTypeBox = wxTextCtrl(self, -1, item.profileType)
        #self.profileTypeBox.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 
        #                            0, "verdana"))
        self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        self.__Layout()
        
        self.nameCtrl.SetValue(item.name)
        self.emailCtrl.SetValue(item.email)
        self.phoneNumberCtrl.SetValue(item.phoneNumber)
        self.locationCtrl.SetValue(item.location)
        self.homeVenueCtrl.SetValue(item.homeVenue)
                     
        self.profileTypeBox.SetValue(item.GetProfileType())
            
        self.__SetEditable(false)
        self.cancelButton.Hide()



class TextValidator(wxPyValidator):
    def __init__(self, fieldName):
        wxPyValidator.__init__(self)
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
                MessageDialog(NULL, "Please, fill in the %s field" % (self.fieldName,))
                return false
            
            if val ==  '<Insert Email Address Here>':
                MessageDialog(NULL, "Please, fill in the %s field" % (self.fieldName,))
                return false
            
        #for real profile dialog
        elif(len(val) < 1 or profile.IsDefault() 
             or profile.name == '<Insert Name Here>'
             or profile.email == '<Insert Email Address Here>'):
             
            if profile.name == '<Insert Name Here>':
                self.fieldName == 'Name'
            elif profile.email ==  '<Insert Email Address Here>':
                self.fieldName = 'Email'
                                                   
            MessageDialog(NULL, "Please, fill in the %s field" %(self.fieldName,))
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.


################################################################################



class AddAppDialog(wxDialog):
    '''
    Dialog for adding name and description to an application session.
    '''

    def __init__(self, parent, id, title, appDescription):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.info = wxStaticText(self, -1, "Give this %s session a name and a short description, click Ok to start it.  \nOnce the session is started, all participants of the venue will be able to join." %appDescription.name)

        self.nameText = wxStaticText(self, -1, "Name: ")
        self.nameCtrl = wxTextCtrl(self, -1, "", validator = AddAppDialogValidator())
        self.descriptionText = wxStaticText(self, -1, "Description:")
        self.descriptionCtrl = wxTextCtrl(self, -1, "",
                                          style = wxTE_MULTILINE, 
                                          size = wxSize(200, 50),
                                          validator = AddAppDialogValidator())

        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.__Layout()

    def __Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)

        sizer.Add(self.info, 0, wxEXPAND|wxALL, 10)
        sizer.Add(wxSize(5,5))
        
        gridSizer = wxFlexGridSizer(2, 2, 10, 5)
        gridSizer.Add(self.nameText)
        gridSizer.Add(self.nameCtrl, 0, wxEXPAND)
        gridSizer.Add(self.descriptionText)
        gridSizer.Add(self.descriptionCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        
        sizer.Add(gridSizer, 1, wxEXPAND|wxALL, 10)
        sizer.Add(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 10)

        bsizer = wxBoxSizer(wxHORIZONTAL)
        bsizer.Add(self.okButton, 0, wxBOTTOM, 10)
        bsizer.Add(self.cancelButton, 0, wxLEFT|wxBOTTOM, 5)

        sizer.Add(bsizer, 0, wxCENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()
        
    def GetName(self):
        return self.nameCtrl.GetValue()

    def GetDescription(self):
        return self.descriptionCtrl.GetValue()



class AddAppDialogValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)

    def Clone(self):
        return AddAppDialogValidator()

    def Validate(self, win):
        name = win.GetName()
        desc = win.GetDescription()
        
        if name == "":
            info = "Please, enter a name for this application session." 
            dlg = wxMessageDialog(None, info, "Enter Name", style = wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return false

        if desc == "":
            info = "Please, enter a description for this application session." 
            dlg = wxMessageDialog(None, info, "Enter Description", style = wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return false
        
        return true
    
    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.
        
 
################################################################################

class ExitPropertiesDialog(wxDialog):
    '''
    This dialog is opened when a user right clicks an exit
    '''
    def __init__(self, parent, id, title, profile):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.title = title
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, profile.GetName(), size = (500,-1))
        self.descriptionText = wxStaticText(self, -1, "Description:", 
                                            style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.descriptionCtrl = wxTextCtrl(self, -1, profile.GetDescription(), 
                                          size = (500,-1))
        self.urlText = wxStaticText(self, -1, "URL:", style=wxALIGN_LEFT)
        self.urlCtrl = wxTextCtrl(self, -1, profile.GetURI(),  size = (500,-1))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        
        self.titleText = wxStaticText(self,-1,"Exit Properties")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        
        self.__SetProperties()
        self.__Layout()
                              
    def __SetProperties(self):
        self.nameCtrl.SetEditable(false)
        self.descriptionCtrl.SetEditable(false)
        self.urlCtrl.SetEditable(false)
                                               
    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.urlText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.urlCtrl, 0, wxEXPAND, 0)
        
        sizer1.Add(self.titleText,0,wxEXPAND|wxALL,10)
        sizer1.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        sizer1.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)

        #sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
       
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
         
################################################################################

class DataPropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (500,-1))
        self.ownerText = wxStaticText(self, -1, "Owner:", 
                                      style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.ownerCtrl = wxTextCtrl(self, -1, "")
        self.sizeText = wxStaticText(self, -1, "Size:")
        self.sizeCtrl = wxTextCtrl(self, -1, "")
        self.lastModText = wxStaticText(self, -1, "Last modified:")
        self.lastModCtrl = wxTextCtrl(self, -1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.titleText = wxStaticText(self,-1,"Data Properties")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        
        self.__SetProperties()
        self.__SetEditable(true)
        self.__Layout()
        
        self.description = None
        
    def __SetProperties(self):
        self.SetTitle("Please, fill in data information")
        
    def __SetEditable(self, editable):
        if not editable:
            # Name is always editable
            self.nameCtrl.SetEditable(false)
           
        else:
            self.nameCtrl.SetEditable(true)
            self.ownerCtrl.SetEditable(false)
            self.sizeCtrl.SetEditable(false)
            self.lastModCtrl.SetEditable(false)
                                 
                                       
    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        #box = wxStaticBox(self, -1, "Properties")
        #box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        #sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.ownerText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.ownerCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.sizeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.sizeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.lastModText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.lastModCtrl, 0, wxEXPAND, 0)
        
        sizer1.Add(self.titleText,0,wxEXPAND|wxALL,10)
        sizer1.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        sizer1.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

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
        self.__SetEditable(true)
        self.cancelButton.Destroy()
        
    def GetDescription(self):
        if self.description:
            self.description.name = self.nameCtrl.GetValue()

        return self.description
          
          

############################################################################

class ServicePropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,-1))
        self.uriText = wxStaticText(self, -1, "Location URL:",
                                    style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.uriCtrl = wxTextCtrl(self, -1, "")
        self.typeText = wxStaticText(self, -1, "Mime Type:")
        self.typeCtrl = wxTextCtrl(self, -1, "")
        self.descriptionText = wxStaticText(self, -1, "Description:",
                                            style=wxALIGN_LEFT)
        self.descriptionCtrl = wxTextCtrl(self, -1, "", style = wxTE_MULTILINE,
                                          size = wxSize(200, 50))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.titleText = wxStaticText(self,-1,"Service Properties")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        
        self.__Layout()
        
        self.description = None

    
    def __SetEditable(self, editable):
        if not editable:
            self.uriCtrl.SetEditable(false)
            self.typeCtrl.SetEditable(false)
            
            # Always editable
            self.nameCtrl.SetEditable(true)
            self.descriptionCtrl.SetEditable(true)
        else:
            self.nameCtrl.SetEditable(true)
            self.uriCtrl.SetEditable(true)
            self.typeCtrl.SetEditable(true)
            self.descriptionCtrl.SetEditable(true)
                  
    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.uriText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.typeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wxEXPAND, 0)
        #sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(self.titleText,0,wxEXPAND|wxALL,10)
        sizer1.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        sizer1.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

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
        self.__SetEditable(false)
        self.cancelButton.Destroy()


############################################################################

class ApplicationPropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title,
                          style = wxDEFAULT_DIALOG_STYLE | 
                          wxRESIZE_BORDER)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,-1))
        self.uriText = wxStaticText(self, -1, "Location URL:",
                                    style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.uriCtrl = wxTextCtrl(self, -1, "")
        self.typeText = wxStaticText(self, -1, "Mime Type:")
        self.typeCtrl = wxTextCtrl(self, -1, "")
        self.descriptionText = wxStaticText(self, -1, "Description:",
                                            style=wxALIGN_LEFT)
        self.descriptionCtrl = wxTextCtrl(self, -1, "", style = wxTE_MULTILINE,
                                          size = wxSize(200, 50))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.titleText = wxStaticText(self,-1,"Application Properties")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
        
        self.__Layout()
        
        self.description = None

    
    def __SetEditable(self, editable):
        if not editable:
            self.uriCtrl.SetEditable(false)
            self.typeCtrl.SetEditable(false)
            
            # Always editable
            self.nameCtrl.SetEditable(true)
            self.descriptionCtrl.SetEditable(true)
        else:
            self.nameCtrl.SetEditable(true)
            self.uriCtrl.SetEditable(true)
            self.typeCtrl.SetEditable(true)
            self.descriptionCtrl.SetEditable(true)
                  
    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        #sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Profile"), wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.uriText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.typeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wxEXPAND, 0)
       
        sizer1.Add(self.titleText,0,wxEXPAND|wxALL,10)
        sizer1.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        sizer1.Add(gridSizer, 1, wxALL, 10)
        sizer1.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()

    def GetDescription(self):
        if not self.description:
            self.description = ApplicationDescription(GUID(), "", "", "",
                                             "")
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
        self.__SetEditable(false)
        self.cancelButton.Destroy()
         
################################################################################

class VenuePropertiesDialog(wxDialog):
    def __init__(self, parent, id, title, venueClient):
        wxDialog.__init__(self, parent, id, title)
        self.venueClient = venueClient
        self.streamListLabel = wxStaticText(self,-1,'Streams')
        self.list = wxListCtrl(self, wxNewId(), size = wxSize(500, 150),style=wxLC_REPORT)

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
        
        self.textLocationLabel = wxStaticText(self,-1,'Text Location')
        self.textLocationText = wxTextCtrl(self,-1,
                                        self.venueClient.GetChatLocation())
        self.textLocationText.SetEditable(false)
        
        self.dataLocationLabel = wxStaticText(self,-1,'Data Location')
        self.dataLocationText = wxTextCtrl(self,-1,
                                        self.venueClient.venueState.GetDataLocation())
        self.dataLocationText.SetEditable(false)

        self.okButton = wxButton(self, wxID_OK, "Ok")
        
        self.titleText = wxStaticText(self,-1,"Venue Properties")
        if IsOSX():
            self.titleText.SetFont(wxFont(12,wxNORMAL,wxNORMAL,wxBOLD))
        else:
            self.titleText.SetFont(wxFont(wxDEFAULT,wxNORMAL,wxNORMAL,wxBOLD))
        self.titleLine = wxStaticLine(self,-1)
        self.buttonLine = wxStaticLine(self,-1)
                       
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
        mainSizer = wxBoxSizer(wxVERTICAL)
        #box = wxStaticBox(self, -1, "Multicast Addresses")
        #box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        #sizer = wxStaticBoxSizer(box, wxVERTICAL)
        mainSizer.Add(self.titleText,0,wxEXPAND|wxALL,10)
        mainSizer.Add(self.titleLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        mainSizer.Add(self.streamListLabel,0, wxLEFT|wxTOP, 10)
        mainSizer.Add(self.list, 1, wxEXPAND| wxALL, 10)
        
        # text location 
        horsizer = wxBoxSizer(wxHORIZONTAL)
        horsizer.Add(self.textLocationLabel,0, wxALL, 10)
        horsizer.Add(self.textLocationText,1, wxRIGHT|wxTOP|wxBOTTOM, 10)
        mainSizer.Add(horsizer,0,wxEXPAND)
        
        # data location
        horsizer = wxBoxSizer(wxHORIZONTAL)
        horsizer.Add(self.dataLocationLabel,0, wxALL, 10)
        horsizer.Add(self.dataLocationText,1, wxRIGHT|wxTOP|wxBOTTOM, 10)
        mainSizer.Add(horsizer,0,wxEXPAND)
        
        mainSizer.Add(self.buttonLine,0,wxEXPAND|wxLEFT|wxRIGHT,5)
        
        #mainSizer.Add(sizer, 1, wxEXPAND| wxALL, 10)
        mainSizer.Add(self.okButton, 0, wxCENTER | wxALL, 10)
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
class AddVideoServiceDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        
        self.hostname = Config.SystemConfig.instance().GetHostname()
                
        self.guideText = wxStaticText(self, -1, videoServiceDialogMsg, 
                                      style=wxALIGN_LEFT)
        self.hostText = wxStaticText(self, -1, "Host:", style=wxALIGN_LEFT)
        self.hostCtrl = wxComboBox(self, -1, "",size=(300,-1))
        
        self.exists = threading.Event()
        self.exists.set()
        
        self.deviceText = wxStaticText(self, -1, "Device:", style=wxALIGN_LEFT)
        self.deviceCtrl = wxComboBox(self, -1, "",size=(300,-1))
        
        self.okButton = wxButton(self, wxID_OK, "OK")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.browser = ServiceDiscovery.Browser('_servicemanager._tcp', self.BrowseCallback)
        self.browser.Start()

        EVT_COMBOBOX(self,self.hostCtrl.GetId(),self.OnHostSelect)
        EVT_TEXT_ENTER(self,self.hostCtrl.GetId(),self.OnHostSelect)

        self.__Layout()
        
    def OnHostSelect(self,event=None):
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
            self.deviceCtrl.SetValue(resources[0].name)
    
    def BrowseCallback(self,op,serviceName,url=None):
        if self.exists.isSet() and op == ServiceDiscovery.Browser.ADD:
            wxCallAfter(self.AddItem,serviceName,url)
            
    def AddItem(self,name,url):
        if self.hostCtrl.FindString(url) == wxNOT_FOUND:
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
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer1.Add(self.guideText, 0, wxRIGHT|wxLEFT|wxBOTTOM|wxALIGN_LEFT, 10)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.hostText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.hostCtrl, 1, wxEXPAND, 0)
        gridSizer.Add(self.deviceText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.deviceCtrl, 1, wxEXPAND, 0)
        sizer1.Add(gridSizer, 0, wxALL|wxEXPAND, 5)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

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

class DataDropTarget(wxFileDropTarget):
    def __init__(self, application):
        wxFileDropTarget.__init__(self)
        self.app = application
        self.do = wxFileDataObject()
        self.SetDataObject(self.do)
    
    def OnDropFiles(self, x, y, files):
        self.app.AddDataCB(fileList = files)

class DesktopDropTarget(wxFileDropTarget):
    def __init__(self, application):
        wxFileDropTarget.__init__(self)
        self.app = application
        self.do = wxFileDataObject()
        self.SetDataObject(self.do)

    def OnEnter(self, x, y, d):
        print 'on enter'
        
    def OnLeave(self):
        print 'on leave'

    def OnDropFiles(self, x, y, files):
        print 'on drop files ', files[0]
        #self.app.AddDataToDesktop(fileList = files)


if __name__ == "__main__":
    pp = wxPySimpleApp()
    #n = VenuePropertiesDialog(None, -1, 'Properties')
    #n.ShowModal()
    
    f = wxFrame(None, -1, "Navigation")
    n = NavigationPanel(f, -1)
    f.Show()
    
    pp.MainLoop()
   
    
    #n = AddAppDialog(None, -1, "Start Application Session", 
    #                 ApplicationDescription("test", "test", "test", "test", "test"))
    #if n.ShowModal() == wxID_OK:
    #    print n.GetName()
    
    
    if n:
        n.Destroy()
