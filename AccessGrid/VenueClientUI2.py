#-----------------------------------------------------------------------------
# Name:        VenueClientUI.py
# Purpose:     
#
# Author:      Susanne Lefvert, Thomas D. Uram
#
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClientUI2.py,v 1.4 2004-07-19 14:55:11 binns Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: VenueClientUI2.py,v 1.4 2004-07-19 14:55:11 binns Exp $"
__docformat__ = "restructuredtext en"

import copy
import os
import os.path
import time
import getopt
from wxPython.wx import *
import string
import webbrowser
import traceback
import re
import sys

from time import localtime , strftime
from AccessGrid import Log
log = Log.GetLogger(Log.VenueClientUI)
Log.SetDefaultLevel(Log.VenueClientUI, Log.WARN)

from AccessGrid import icons
from AccessGrid import Toolkit
from AccessGrid.Platform import IsWindows, IsOSX, Config
from AccessGrid.UIUtilities import AboutDialog, MessageDialog
from AccessGrid.UIUtilities import ErrorDialog, BugReportCommentDialog
from AccessGrid.ClientProfile import *
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.Security.wxgui.AuthorizationUI import AuthorizationUIDialog
from AccessGrid.Utilities import SubmitBug
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.AppMonitor import AppMonitor
from AccessGrid.Venue import ServiceAlreadyPresent
from AccessGrid.VenueClient import NetworkLocationNotFound, NotAuthorizedError
from AccessGrid.VenueClient import DisconnectError
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.UIUtilities import AddURLBaseDialog, EditURLBaseDialog

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
class VenueList(wxScrolledWindow):
class ContentListPanel(wxPanel):                   
class TextClientPanel(wxPanel):
class StatusBar(wxStatusBar):
class ExitPanel(wxPanel):


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
    ID_MYNODE_MANAGE = wxNewId()
    ID_ENABLE_VIDEO = wxNewId()
    ID_ENABLE_AUDIO = wxNewId()
    ID_MYNODE_URL = wxNewId()
    ID_MYVENUE_ADD = wxNewId()
    ID_MYVENUE_EDIT = wxNewId()
    ID_MYVENUE_GOTODEFAULT = wxNewId()
    ID_MYVENUE_SETDEFAULT = wxNewId()
    ID_HELP = wxNewId()
    ID_HELP_ABOUT = wxNewId()
    ID_HELP_MANUAL = wxNewId()
    ID_HELP_AGDP = wxNewId()
    ID_HELP_AGORG = wxNewId()
    ID_HELP_FL = wxNewId()
    ID_HELP_FLAG = wxNewId()
    ID_HELP_BUG_REPORT = wxNewId()
    ID_HELP_BUGZILLA = wxNewId()
    
    ID_PARTICIPANT_PROFILE = wxNewId()
    ID_PARTICIPANT_FOLLOW = wxNewId()
    ID_PARTICIPANT_LEAD = wxNewId()
    ID_ME_PROFILE = wxNewId()
    ID_ME_DATA = wxNewId()
    ID_ME_UNFOLLOW = wxNewId()

    def __init__(self, venueClient, controller, app):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        self.venueClient = venueClient
        self.controller = controller

        self.debugMode = 0
           
        self.browser = None
        
        self.textClientPanel = None
        self.myVenuesDict = {}
        self.myVenuesMenuIds = {}
        self.onExitCalled = false
        # State kept so UI can add venue administration options.
        
        wxFrame.__init__(self, NULL, -1, "")
        self.__BuildUI(app)
        self.SetSize(wxSize(400, 500))
        
        # Tell the UI about installed applications
        self.__EnableAppMenu( false )
        
        #
        # Check if profile is created then open venue client
        #
        profile = self.venueClient.GetProfile()
        if profile.IsDefault():  # not your profile
            log.debug("the profile is the default profile - open profile dialog")
            self.__OpenProfileDialog()
        else:
            self.__OpenVenueClient()
            
        self.nodeManagementFrame = None

        # Help Doc locations
        agtkConfig = Config.AGTkConfig.instance()
        self.manual_url = os.path.join(agtkConfig.GetDocDir(),
                                       "VenueClientManual",
                                       "VenueClientManualHTML.htm")
        self.agdp_url = "http://www.accessgrid.org/agdp"
        self.ag_url = "http://www.accessgrid.org/"
        self.flag_url = "http://www.mcs.anl.gov/fl/research/accessgrid"
        self.fl_url = "http://www.mcs.anl.gov/fl/"
        self.bugzilla_url = "http://bugzilla.mcs.anl.gov/AccessGrid"

        # Make sure data can be dragged from tree to the desktop.
        #self.SetDropTarget(DesktopDropTarget(self))

       
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

    def __OpenProfileDialog(self):
        """
        This method opens a profile dialog, in which the user can fill in
        his or her information.
        """
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile')
        profileDialog.SetProfile(self.venueClient.GetProfile())

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

        self.venueAddressBar.SetAddress(self.venueClient.GetProfile().homeVenue)
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
        self.venue.Append(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,"Administrate Roles...",
                             "Change venue authorization settings.")
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_PROPERTIES,"Properties...",
                          "View information about the venue.")
        
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE,"&Exit", "Exit venue")
        
        self.menubar.Append(self.venue, "&Venue")
              
        self.preferences = wxMenu()
        self.preferences.Append(self.ID_PROFILE,"&Edit Profile...", 
                                "Change your personal information")
        #
        # Retrieve the cert mgr GUI from the application.
        #

        gui = None
        try:
            mgr = app.GetCertificateManager()
            gui = mgr.GetUserInterface()
        except:
            log.exception("VenueClientFrame.__SetMenubar: Cannot retrieve \
                           certificate mgr user interface, continuing")

        if gui is not None:
            certMenu = gui.GetMenu(self)
            self.preferences.AppendMenu(self.ID_CERTIFICATE_MANAGE,
                                    "&Manage Certificates", certMenu)

        self.preferences.AppendSeparator()

        # Add node-related entries
        self.preferences.AppendRadioItem(self.ID_USE_MULTICAST, "Use Multicast",
                                "Use multicast to connect media")
        self.preferences.AppendRadioItem(self.ID_USE_UNICAST, "Use Unicast",
                                "Use unicast to connect media")
        self.preferences.AppendSeparator()
        self.preferences.AppendCheckItem(self.ID_ENABLE_VIDEO, "Enable Video",
                                "Enable/disable video for your node")
        self.preferences.Check(self.ID_ENABLE_VIDEO,true)
        self.preferences.AppendCheckItem(self.ID_ENABLE_AUDIO, "Enable Audio",
                                "Enable/disable audio for your node")
        self.preferences.Check(self.ID_ENABLE_AUDIO,true)
        self.preferences.Append(self.ID_MYNODE_URL, "&Set Node URL...",
                                "Specify URL address to node service")
        self.preferences.Append(self.ID_MYNODE_MANAGE, "&Manage My Node...",
                                "Configure your node")
        self.menubar.Append(self.preferences, "&Preferences")
        self.myVenues = wxMenu()
        self.myVenues.Append(self.ID_MYVENUE_GOTODEFAULT, "Go to Home Venue",
                             "Go to default venue")
        self.myVenues.Append(self.ID_MYVENUE_SETDEFAULT, "Set as Home Venue",
                             "Set current venue as default")
        self.myVenues.AppendSeparator()
        
        self.myVenues.Append(self.ID_MYVENUE_ADD, "Add &Current Venue...",
                             "Add this venue to your list of venues")
        self.myVenues.Append(self.ID_MYVENUE_EDIT, "Edit My &Venues...",
                             "Edit your venues")
        self.myVenues.AppendSeparator()
        
        self.menubar.Append(self.myVenues, "My Ven&ues")

              
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
        self.meMenu.AppendSeparator()
        self.meMenu.Append(self.ID_ME_DATA,"Add personal data...",\
                                           "Add data you can bring to other venues")
       
            
        self.participantMenu = wxMenu()
        self.participantMenu.Append(self.ID_PARTICIPANT_PROFILE,"View Profile...",\
                                           "View participant's profile information")
        self.participantMenu.AppendSeparator()
        self.participantMenu.Append(self.ID_PARTICIPANT_FOLLOW,"Follow",\
                                           "Follow this person")
        self.participantMenu.Append(self.ID_PARTICIPANT_LEAD,"Lead",\
                                           "Lead this person")

        # ---- Menus for headings
        self.dataHeadingMenu = wxMenu()
        self.dataHeadingMenu.Append(self.ID_VENUE_DATA_ADD,"Add...",
                                   "Add data to the venue")

        self.serviceHeadingMenu = wxMenu()
        self.serviceHeadingMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...",
                                "Add service to the venue")

        # Do not enable menus until connected
        self.__HideMenu()

        # Don't allow a choice of unicast until in a venue (then we might not
        # have it anyhow)
        self.preferences.Enable(self.ID_USE_UNICAST, false)
        
        # until implemented
        self.participantMenu.Enable(self.ID_PARTICIPANT_LEAD, false)


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
        EVT_MENU(self, self.ID_PROFILE, self.EditProfileCB)
        EVT_MENU(self, self.ID_USE_MULTICAST, self.UseMulticastCB)
        EVT_MENU(self, self.ID_USE_UNICAST, self.UseUnicastCB)
        EVT_MENU(self, self.ID_ENABLE_VIDEO, self.EnableVideoCB)
        EVT_MENU(self, self.ID_ENABLE_AUDIO, self.EnableAudioCB)
        EVT_MENU(self, self.ID_MYNODE_URL, self.SetNodeUrlCB)
        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.ManageNodeCB)
        
        # My Venues Menu
        EVT_MENU(self, self.ID_MYVENUE_GOTODEFAULT, self.GoToDefaultVenueCB)
        EVT_MENU(self, self.ID_MYVENUE_SETDEFAULT, self.SetAsDefaultVenueCB)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenuesCB)
        EVT_MENU(self, self.ID_MYVENUE_EDIT, self.EditMyVenuesCB)
        
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
        EVT_MENU(self, self.ID_PARTICIPANT_FOLLOW, self.FollowCB)
        EVT_MENU(self, self.ID_ME_UNFOLLOW, self.UnFollowCB)
        EVT_MENU(self, self.ID_ME_DATA, self.AddPersonalDataCB)
        EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.ViewProfileCB)

        # UI Events
        EVT_CLOSE(self, self.ExitCB)
        
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.__OnSashDrag)
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_BOTTOM,
                               self.ID_WINDOW_BOTTOM2, self.__OnSashDrag)
        EVT_SIZE(self, self.__OnSize)

    def __SetProperties(self):
        self.SetTitle("Venue Client")
        self.SetIcon(icons.getAGIconIcon())
        #self.venueListPanel.GetSize().GetHeight()
        self.venueListPanel.SetSize(wxSize(160, 300))
        self.venueAddressBar.SetSize(wxSize(self.GetSize().GetWidth(),65))
        
    def __FillTempHelp(self, x):
        if x == '\\':
            x = '/'
        return x

    def __LoadMyVenues(self):
    
        # Delete existing menu items
        for ID in self.myVenuesMenuIds.values():
            self.myVenues.Delete(ID)
        
        self.myVenuesMenuIds = {}
        self.myVenuesDict = self.controller.GetMyVenues()
                   
        # Create menu items
        for name in self.myVenuesDict.keys():
            ID = wxNewId()
            self.myVenuesMenuIds[name] = ID
            url = self.myVenuesDict[name]
            text = "Go to: " + url
            self.myVenues.Append(ID, name, text)
            EVT_MENU(self, ID, self.GoToMenuAddressCB)
                        

    def __BuildUI(self, app):
        
        self.Centre()
        self.menubar = wxMenuBar()
        self.statusbar = StatusBar(self)
       
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, 
                                               self.myVenuesDict,
                                               'default venue')
        self.textInputWindow = wxSashWindow(self, self.ID_WINDOW_BOTTOM2,
                                                  wxDefaultPosition,
                                                  wxSize(-1, 35))
        self.textOutputWindow = wxSashWindow(self, self.ID_WINDOW_BOTTOM,
                                                   wxDefaultPosition,
                                                   wxSize(-1, 100))
        self.textOutput = wxTextCtrl(self.textOutputWindow, wxNewId(), "",
                                     style= wxTE_MULTILINE | wxTE_READONLY |
                                     wxTE_RICH|wxTE_AUTO_URL)
        self.textClientPanel = TextClientPanel(self.textInputWindow, -1,
                                               self.textOutput, self)
               
        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT)
        self.contentListPanel = ContentListPanel(self)
        dataDropTarget = DataDropTarget(self)
        self.contentListPanel.SetDropTarget(dataDropTarget)
        
        self.__SetStatusbar()
        self.__SetMenubar(app)
        self.__SetProperties()
        self.__Layout()
        self.__SetEvents()
        self.__LoadMyVenues()

    def __OnSashDrag(self, event):
        if event.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
            return

        eID = event.GetId()
              
        if eID == self.ID_WINDOW_LEFT:
            self.venueListPanel.Show()
            width = event.GetDragRect().width
            if width < 60:
                width = 20
                self.venueListPanel.Hide()
            elif width > (self.GetSize().GetWidth() - 20):
                width = self.GetSize().GetWidth() - 20
            self.venueListPanel.SetSize(wxSize(width, -1))

        elif eID == self.ID_WINDOW_BOTTOM:
            height = event.GetDragRect().height
            self.textOutputWindow.SetSize(wxSize(-1, height))
           
        elif eID == self.ID_WINDOW_BOTTOM2:
            outputMinSize = 40
            inputMinSize = 30
            oldInputHeight = self.textInputWindow.GetSize().height
            newInputHeight = event.GetDragRect().height

            # Don't make text input too small.
            if newInputHeight < inputMinSize:
                newInputHeight = inputMinSize
                            
            diff = newInputHeight - oldInputHeight
            oldOutputHeight = self.textOutputWindow.GetSize().height
            newOutputHeight = oldOutputHeight - diff

            # Don't make input hide output.
            if newOutputHeight < outputMinSize:
                # fix both sizes
                newInputHeight = newInputHeight - \
                                (outputMinSize - newOutputHeight)
                newOutputHeight = outputMinSize
                            
            self.textInputWindow.SetSize(wxSize(-1, newInputHeight))
                        
            # Make output smaller when input is bigger and vice versa.
            self.textOutputWindow.SetSize(wxSize(-1, newOutputHeight))

        self.__Layout()
                
    def __OnSize(self, event = None):
        self.__Layout()
       
    def __CleanUp(self):
        self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

    def __HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)
        self.menubar.Enable(self.ID_VENUE_PROPERTIES, false)
        self.menubar.Enable(self.ID_MYVENUE_ADD, false)
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


    def __UpdateTransports(self):
        """
        This method is called when a venue stream is modified.
        """
        transportList = self.venueClient.GetTransportList()
        if 'unicast' in transportList:
            self.SetUnicastEnabled(1)
        else:
            self.SetUnicastEnabled(0)

        transport = self.venueClient.GetTransport()
        self.SetTransport(transport)
        
    # end Private Methods
    #
    ##########################################################################


    ##########################################################################
    #
    # Pure UI Methods
        
    def __Layout(self):
        subBox=wxBoxSizer(wxHORIZONTAL)
        subBox.Add(self.venueListPanel,0,wxEXPAND)
        subBox.Add(self.contentListPanel,1,wxEXPAND)
        
        textOutputBox=wxBoxSizer(wxHORIZONTAL)
        textOutputBox.Add(self.textOutput,1,wxEXPAND)
        w,h = self.textOutputWindow.GetSizeTuple()
        self.textOutputWindow.SetSizer(textOutputBox)
        self.textOutputWindow.GetSizer().SetDimension(5,5,w-10,h-10)
        
        textInputBox=wxBoxSizer(wxHORIZONTAL)
        textInputBox.Add(self.textClientPanel,1,wxEXPAND)
        w,h = self.textInputWindow.GetSizeTuple()
        self.textInputWindow.SetSizer(textInputBox)
        self.textInputWindow.GetSizer().SetDimension(5,5,w-10,h-10)
        
        mainBox=wxBoxSizer(wxVERTICAL)
        mainBox.Add(self.venueAddressBar,0,wxEXPAND)
        mainBox.Add(subBox,1,wxEXPAND)
        mainBox.Add(self.textOutputWindow,0,wxEXPAND)
        mainBox.Add(self.textInputWindow,0,wxEXPAND)
        
        self.venueListPanel.SetSashVisible(wxSASH_RIGHT, TRUE)
        self.textOutputWindow.SetSashVisible(wxSASH_TOP, TRUE)
        self.textInputWindow.SetSashVisible(wxSASH_TOP, TRUE)
        
        self.SetSizer(mainBox)
        self.Show(1)
        self.Layout()
    
    def UpdateLayout(self):
        self.__Layout()

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
        streams = self.venueClient.GetVenueStreams()
        venuePropertiesDialog = VenuePropertiesDialog(self, -1,
                                                      'Venue Properties')
        venuePropertiesDialog.PopulateList(streams)
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

    #
    # Preferences Menu
    #
    
    def EditProfileCB(self, event = None):
        profile = None
        profileDialog = ProfileDialog(NULL, -1,
                                  'Your profile information')
        profileDialog.SetProfile(self.venueClient.GetProfile())
        if (profileDialog.ShowModal() == wxID_OK):
            profile = profileDialog.GetNewProfile()
            log.debug("VenueClientFrame.EditProfile: change profile: %s" %profile.name)
            try:
                self.controller.EditProfileCB(profile)
            except:
                log.exception("Error editing profile")
                self.Error("Modified profile could not be saved", "Edit Profile Error")
        profileDialog.Destroy()


        
    """
    ManageCertificates menu is provided by CertMgmt module
    """


    def UseMulticastCB(self,event):
        try:
            self.controller.UseMulticastCB()
        except NetworkLocationNotFound:
            self.Error("Multicast streams not found","Use Multicast")
        except:
            self.Error("Error using multicast","Use Multicast")

    def UseUnicastCB(self,event):

        # Get a list of providers
        providerList = self.venueClient.GetNetworkLocationProviders()
        providerNameLocList = map( lambda provider: provider.name + "/" + provider.location,
                                   providerList )

        # Present the list to the user
        dialog = wxSingleChoiceDialog( self, "Select bridge", 
                                             "Bridge Dialog", 
                                             providerNameLocList )

        currentProvider = self.venueClient.GetProvider()
        if currentProvider:
            currentProviderString = currentProvider.name + "/" + currentProvider.location
            try:
                index = providerNameLocList.index(currentProviderString)
                if index >= 0:
                    dialog.SetSelection(index)
            except ValueError:
                pass

        ret = dialog.ShowModal()
        if ret == wxID_OK:
            # Get the selected provider
            index = dialog.GetSelection()
            selectedProvider = providerList[index]
            try:
                self.controller.UseUnicastCB(selectedProvider)
            except NetworkLocationNotFound:
                # Report the error to the user
                text="Stream information for selected bridge not found; reverting to previous selection"
                self.Error(text, "Use Unicast Error")
            except:
                self.Error("Error switching to selected bridge; reverting to previous selection", "Use Unicast Error")
                
        else:
            # Set the menu checkbox appropriately
            transport = self.venueClient.GetTransport()
            self.SetTransport(transport)

    def EnableVideoCB(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_VIDEO)
        try:
            self.controller.EnableVideoCB(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling video", "Error enabling/disabling video")
            pass

    def EnableAudioCB(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_AUDIO)
        try:
            self.controller.EnableAudioCB(enableFlag)
        except:
            #self.gui.Error("Error enabling/disabling audio", "Error enabling/disabling audio")
            pass
    
    def SetNodeUrlCB(self, event = None):
        nodeUrl = None
        setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                     self.venueClient.GetNodeServiceUri(), 
                                     "Please, specify node service URL")

        if setNodeUrlDialog.ShowModal() == wxID_OK:
            nodeUrl = setNodeUrlDialog.address.GetValue()
            try:
                self.controller.SetNodeUrlCB(nodeUrl)
            except:
                self.Error("Error setting node url", "Set Node Url Error")
       
        setNodeUrlDialog.Destroy()
        
    def ManageNodeCB(self, event):
        if self.nodeManagementFrame:
            self.nodeManagementFrame.Raise()
        else:
            self.nodeManagementFrame = NodeManagementClientFrame(self, -1, "Access Grid Node Management")
            log.debug("VenueClientFrame.OpenNodeMgmtApp: open node management")
            try:
                self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeServiceUri() )
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
                        self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeServiceUri() )

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
    
    # 
    # MyVenues Menu
    #
    
    
    def GoToDefaultVenueCB(self,event):
        venueUrl = self.venueClient.GetProfile().homeVenue
        self.SetVenueUrl(venueUrl)
        self.EnterVenueCB(venueUrl)

    def SetAsDefaultVenueCB(self,event):
        try:
            self.controller.SetAsDefaultVenueCB()
        except:
            self.Error("Error setting default venue", "Set Default Venue Error")

    def AddToMyVenuesCB(self, event):
        url = self.venueClient.GetVenue()
        name = self.venueClient.GetVenueName()
        myVenuesDict = self.controller.GetMyVenues()
        
        if not url:
            log.info("Invalid venue url %s", url)
            self.Error("Error adding venue to venue list","Add Venue Error")
            
        if url in myVenuesDict.values():
            #
            # Venue URL already in list
            #
            for n in myVenuesDict.keys():
                if myVenuesDict[n] == url:
                    name = n
            text = "This venue is already added to your venues as "+"'"+name+"'"
            self.Notify(text, "Add venue")
        else:
            #
            # Venue url not in list
            # - Prompt for name and validate
            #
            venueName = None
            dialog = AddURLBaseDialog(self, -1, name)
            if (dialog.ShowModal() == wxID_OK):
                venueName = dialog.GetValue()
            dialog.Destroy()

            if venueName:
                addVenue = 1
                if myVenuesDict.has_key(venueName):
                    #
                    # Venue name already in list
                    #
                    info = "A venue with the same name is already added, do you want to overwrite it?"
                    if self.Prompt(info ,"Duplicated Venue"):
                        # 
                        # User chose to replace the file 
                        #
                        self.RemoveFromMyVenues(venueName)
                        self.controller.AddToMyVenuesCB(venueName,url)
                        addVenue = 1
                    else:
                        # 
                        # User chose to not replace the file
                        #
                        addVenue = 0
                else:
                    #
                    # Venue name not in list
                    #
                    addVenue = 1
                    
                if addVenue:
                    try:
                        self.controller.AddToMyVenuesCB(venueName,url)
                        self.AddToMyVenues(venueName,url)
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
            
            #SubmitBug(comment, email)
            SubmitBug(comment, self.venueClient.GetProfile(), email,
                      Config.UserConfig.instance())
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
            self.SetStatusText("Trying to enter venue at %s" % (venueUrl,))

            self.controller.EnterVenueCB(venueUrl)
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
            profileView = ProfileDialog(self, -1, "Profile")
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

    def FollowCB(self, event):
        personToFollow = self.GetSelectedItem()
        url = personToFollow.venueClientURL
        name = personToFollow.name
        log.debug("VenueClientFrame.Follow: You are trying to follow :%s url:%s " %(name, url))

        if(self.venueClient.leaderProfile == personToFollow):
            text = "You are already following "+name
            title = "Notification"
            self.Notify(text, title)
        
        elif (self.venueClient.pendingLeader == personToFollow):
            text = "You have already sent a request to follow "+name+". Please, wait for answer."
            title = "Notification"
            self.Notify(text,title)
        else:
            try:
                self.controller.FollowCB(personToFollow)
            except:
                text = "You can not follow "+name
                title = "Notification"
                self.Notify(text, title)
                
    def UnFollowCB(self, event):
        try:
            self.controller.UnFollowCB()
            self.meMenu.Remove(self.ID_ME_UNFOLLOW)
        except:
            self.Error("Error occurred trying to stop following","UnFollow Error") 
            

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
        log.debug("VenueClientFrame.SaveData: Save data")
        data = self.GetSelectedItem()
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
        id = self.venueClient.GetProfile().GetName()
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
            self.controller.SendTextCB(text)
        except:
            self.Error("Error sending text","Send Text Error")
        

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

    def GetVideoEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_VIDEO)

    def GetAudioEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_AUDIO)

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

    def Notify(self,text,title):
    
        wxCallAfter(self.__Notify,text,title)

    def Warn(self,text,title):
        wxCallAfter(self.__Warn,text,title)

    def Error(self,text,title):
        log.exception("Error")
        ErrorDialog(None, text, title)


    #
    # Lead/Follow
    #

    def LeadResponse(self, leaderProfile, isAuthorized):
        """
        This method notifies the user if the request to follow somebody is approved
        or denied.

        **Arguments:**
        
        *leaderProfile* The ClientProfile of the user we want to follow
        *isAuthorized* Boolean value set to true if request is approved, else false.
        
        """
        wxCallAfter(self.NotifyLeadDialog, leaderProfile, isAuthorized)

    def NotifyUnLeadDialog(self, clientProfile):
        text = clientProfile.name+" has stopped following you"
        title = "Notification"
        dlg = wxMessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def NotifyUnLead(self, clientProfile):
        """
        This method  notifies the user that somebody wants to stop following him or
        her

        **Arguments:**
        
        *clientProfile* The ClientProfile of the client who stopped following this client
        """
        wxCallAfter(self.NotifyUnLeadDialog, clientProfile)
        

    def NotifyLeadDialog(self, clientProfile, isAuthorized):
        if isAuthorized:
            text = "You are now following "+clientProfile.name
            self.meMenu.Append(self.ID_ME_UNFOLLOW,"Stop following %s" % clientProfile.name,
                               "%s will not lead anymore" % clientProfile.name)
        else:
            text = clientProfile.name+" does not want you as a follower, the request is denied."

        title = "Notification"
        dlg = wxMessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def AuthorizeLead(self, clientProfile):
        """
        This method  notifies the user that somebody wants to follow him or
        her and allows the user to approve the request.

        **Arguments:**
        
        *clientProfile* The ClientProfile of the user who wish to lead this client.
        """
        wxCallAfter(self.AuthorizeLeadDialog, clientProfile)


    def AuthorizeLeadDialog(self, clientProfile):
        idPending = None
        idLeading = None

        if(self.venueClient.pendingLeader!=None):
            idPending = self.venueClient.pendingLeader.publicId
          

        if(self.app.venueClient.leaderProfile!=None):
            idLeading = self.venueClient.leaderProfile.publicId
          
          
        if(clientProfile.publicId != idPending and clientProfile.publicId != idLeading):
            text = "Do you want "+clientProfile.name+" to follow you?"
            title = "Authorize follow"
            dlg = wxMessageDialog(self, text, title, style = wxYES_NO| wxYES_DEFAULT|wxICON_QUESTION)
            if(dlg.ShowModal() == wxID_YES):
                self.venueClient.SendLeadResponse(clientProfile, true)

            else:
                self.venueClient.SendLeadResponse(clientProfile, false)

            dlg.Destroy()

        else:
            self.venueClient.SendLeadResponse(clientProfile, false)


    #
    # Other
    #

    def SetUnicastEnabled(self, flag):
        self.preferences.Enable(self.ID_USE_UNICAST, flag)

    def SetTransport(self, transport):
        if transport == "multicast":
            self.preferences.Check(self.ID_USE_MULTICAST, true)
        elif transport == "unicast":  
            self.preferences.Check(self.ID_USE_UNICAST, true)

    def SetStatusText(self,text):
        self.statusbar.SetStatusText(text,0)

    def GoBackCB(self):
        """
        This method is called when the user wants to go back to last visited venue
        """
        log.debug("Go back")
        self.controller.GoBackCB()
        
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
        return self.venueClient.GetProfile()
        
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
        self.myVenues.Append(ID, name, text)
        self.myVenuesMenuIds[name] = ID
        self.myVenuesDict[name] = url
        EVT_MENU(self, ID, self.GoToMenuAddressCB)
    
    def RemoveFromMyVenues(self,venueName):
        # Remove the venue from my venues menu list
        menuId = self.myVenuesMenuIds[venueName]
        self.myVenues.Remove(menuId)
    
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


    # end General Implementation
    #
    ############################################################################

    ############################################################################
    #
    # Implementation of VenueClientObserver
    # Note:  These methods are called by an event processor in a different thread,
    #        so any wx calls here must be made with wxCallAfter.

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
        wxCallAfter(self.__UpdateTransports)
        
    def RemoveStream(self,streamDesc):
        wxCallAfter(self.__UpdateTransports)
        
    def ModifyStream(self,streamDesc):
        wxCallAfter(self.__UpdateTransports)
        
    def AddText(self,name,text):
        """
        This method is called when text is received from the text service.

        **Arguments:**
        
        *name* The name of the user who sent the message
        *text* The text sent
        """
        
        wxCallAfter(self.textClientPanel.OutputText, name, text)
        
    def EnterVenue(self, URL, warningString="", enterSuccess=1):
        """
        This method calls the venue client method and then
        performs its own operations when the client enters a venue.
      
        **Arguments:**
        
        *URL* A string including the venue address we want to connect to
        *back* Boolean value, true if the back button was pressed, else false.
        
        """
        log.debug("bin.VenueClient::EnterVenue: Enter venue with url: %s", URL)

        if not enterSuccess:
            # Currently receives type of error in warningString.  This will go back
            #   catching an exception with vc redesign.
            if warningString == "NotAuthorized":
                text = "You are not authorized to enter the venue located at %s.\n." % URL
                wxCallAfter(MessageDialog, None, text, "Notification")
            elif warningString.startswith("Authorization failure connecting to server"):
                text = warningString
                wxCallAfter(self.Notify, text, "Authorization failure")
                log.debug(warningString)
            else:
                log.debug("warningString: %s" %warningString)
                text = "Can not connect to venue located at %s.  Please, try again." % URL
                wxCallAfter(self.Notify, text, "Can not enter venue")
            return

        # initialize flag in case of failure
        enterUISuccess = 1

        try:
            
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
            for conn in venueState.connections.values():
                wxCallAfter(self.venueListPanel.AddVenueDoor,
                            conn)
                # log.debug("   %s" %(conn.name))

            #
            # Reflect venue entry in the client
            #
            wxCallAfter(self.textClientPanel.OutputText, None,
                        "-- Entered venue %s" % self.venueClient.GetVenueName())
            wxCallAfter(self.textClientPanel.OutputText, "enter",
                        self.venueClient.GetVenueDescription())

            wxCallAfter(self.SetVenueUrl, URL)
                                              
            # log.debug("Add your personal data descriptions to venue")
            wxCallAfter(self.statusbar.SetStatusText, "Add your personal data to venue")

            # Enable menus
            wxCallAfter(self.__ShowMenu)
            
            #
            # Enable the application menu that is displayed over
            # the Applications items in the list
            # (this is not the app menu above)
            wxCallAfter(self.__EnableAppMenu, true)

            # Enable/disable the unicast menu entry appropriately
            wxCallAfter(self.__UpdateTransports)
            
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

class VenueAddressBar(wxSashWindow):
    ID_GO = wxNewId()
    ID_BACK = wxNewId()
    ID_ADDRESS = wxNewId()
    
    def __init__(self, parent, id, venuesList, defaultVenue):
        wxSashWindow.__init__(self, parent, id, wxDefaultPosition, 
                                    wxDefaultSize)
        self.parent = parent
        self.addressPanel = wxPanel(self, -1, style = wxRAISED_BORDER, size = wxSize(-1,35))
        self.titlePanel =  wxPanel(self, -1, size = wxSize(-1, 80),
                                   style = wxRAISED_BORDER)
        self.title = wxStaticText(self.titlePanel, wxNewId(),
                                  'You are not in a venue',
                                  style = wxALIGN_CENTER)
        font = wxFont(16, wxSWISS, wxNORMAL, wxNORMAL, false)
        self.title.SetFont(font)
        self.address = wxComboBox(self.addressPanel, self.ID_ADDRESS,
                                  defaultVenue,
                                  choices = venuesList.keys(),
                                  style = wxCB_DROPDOWN)
        
        self.goButton = wxButton(self.addressPanel, self.ID_GO, "Go",
                             wxDefaultPosition, wxSize(40, 21))
        self.backButton = wxButton(self.addressPanel, self.ID_BACK ,
                               "<<", wxDefaultPosition, wxSize(36, 21))
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
        box.Add(self.backButton, 0, wxEXPAND|wxRIGHT|wxALIGN_CENTER|wxLEFT, 5)
        box.Add(self.address, 1, wxEXPAND|wxRIGHT|wxALIGN_CENTER, 5)
        box.Add(self.goButton, 0, wxEXPAND|wxRIGHT|wxALIGN_CENTER, 5)
        self.addressPanel.SetSizer(box)

        titleBox = wxBoxSizer(wxHORIZONTAL)
        titleBox.Add(self.title, 1, wxEXPAND|wxCENTER)
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

class VenueListPanel(wxSashWindow):
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
    
    ID_MINIMIZE = wxNewId()
    ID_MAXIMIZE = wxNewId()
      
    def __init__(self, parent,id):
        wxSashWindow.__init__(self, parent, id)
        self.parent = parent
        #self.panel = wxPanel(self, -1,  style = wxSUNKEN_BORDER)
        self.list = VenueList(self, parent)
        self.minimizeButton = wxButton(self, self.ID_MINIMIZE, "<<", size = wxSize(40,-1),
                                       #wxDefaultPosition, wxSize(25,21),
                                       style = wxBU_EXACTFIT )
        self.maximizeButton = wxButton(self, self.ID_MAXIMIZE, ">>", size = wxSize(40,-1),
                                       #wxDefaultPosition, wxSize(25,21),
                                       style = wxBU_EXACTFIT )
        self.exitsText = wxButton(self, -1, "Exits") 
                                  #wxDefaultPosition,
                                  #wxSize(20,21), wxBU_EXACTFIT)
        
        self.imageList = wxImageList(32,32)
                
        self.__Layout()
        self.__AddEvents()
        self.__SetProperties()

    def __SetProperties(self):
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.minimizeButton.SetToolTipString("Hide Exits")
        self.maximizeButton.SetToolTipString("Show Exits")
        #self.exitsText.SetBackgroundColour("WHITE")
        #self.SetBackgroundColour(self.maximizeButton.GetBackgroundColour())
        self.maximizeButton.Hide()
                
    def __AddEvents(self):
        EVT_BUTTON(self, self.ID_MINIMIZE, self.OnClick) 
        EVT_BUTTON(self, self.ID_MAXIMIZE, self.OnClick) 
        EVT_SIZE(self,self.__OnSize)
    
    def __OnSize(self,evt):
        self.__Layout()

    def FixDoorsLayout(self):
        self.__Layout()
        #wxLayoutAlgorithm().LayoutWindow(self, self.panel)

    def __Layout(self):
        panelSizer = wxBoxSizer(wxHORIZONTAL)
        panelSizer.Add(self.exitsText, 1, wxEXPAND)
        panelSizer.Add(self.minimizeButton, 0, wxEXPAND)

        venueListPanelSizer = wxBoxSizer(wxVERTICAL)
        venueListPanelSizer.Add(panelSizer, 0, wxEXPAND)
        venueListPanelSizer.Add(self.list, 1, wxEXPAND)

        w,h = self.GetSizeTuple()
        self.SetSizer(venueListPanelSizer)
        self.GetSizer().SetDimension(5,5,w-10,h-10)

    def Hide(self):
        currentHeight = self.GetSize().GetHeight()
        self.exitsText.Hide()
        self.minimizeButton.Hide()  
        self.maximizeButton.Show()
        self.list.HideDoors()
        self.SetSize(wxSize(self.maximizeButton.GetSize().GetWidth(), currentHeight))
        self.parent.UpdateLayout()

    def Show(self):
        currentHeight = self.GetSize().GetHeight()
        self.exitsText.Show()
        self.maximizeButton.Hide()
        self.minimizeButton.Show()  
        self.list.ShowDoors()
        self.SetSize(wxSize(180, currentHeight))
        self.parent.UpdateLayout()
        
    def OnClick(self, event):
        if event.GetId() == VenueListPanel.ID_MINIMIZE:
            self.Hide()
                                               
        if event.GetId() == VenueListPanel.ID_MAXIMIZE:
            self.Show()
                                       
    def CleanUp(self):
        self.list.CleanUp()
        
    def AddVenueDoor(self,connectionDescription):
        self.list.AddVenueDoor(connectionDescription)
        
    def RemoveVenueDoor(self,connectionDescription):
        self.list.RemoveVenueDoor(connectionDescription)


class VenueList(wxScrolledWindow):
    '''
    VenueList. 
    
    The venueList is a scrollable window containing all exits to current venue.
    
    '''   
    def __init__(self, parent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1, size=wxSize(175, 300))
        self.doorsAndLabelsList = []
        self.exitsDict = {}
        self.__Layout()
        self.parent = parent
        self.EnableScrolling(true, true)
        self.SetScrollRate(1, 1)
                      
    def __Layout(self):
        self.box = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.box)
        self.SetAutoLayout(1)
        self.Layout()
               
    def AddVenueDoor(self, connectionDescription):
        panel = ExitPanel(self, wxNewId(), connectionDescription)
        self.doorsAndLabelsList.append(panel)
        self.doorsAndLabelsList.sort(lambda x, y: cmp(x.GetName(),
                                                      y.GetName()))
        index = self.doorsAndLabelsList.index(panel)
                      
        self.box.Insert(index, panel, 0, wxEXPAND)

        id = panel.GetButtonId()

        self.exitsDict[id] = connectionDescription
        self.FitInside()
        self.EnableScrolling(true, true)
                            
    def CleanUp(self):
        for item in self.doorsAndLabelsList:
            self.box.Remove(item)
            item.Destroy()

        self.__Layout()
        #self.parent.__Layout()  

        self.exitsDict.clear()
        del self.doorsAndLabelsList[0:]
                                          
    def HideDoors(self):
        for item in self.doorsAndLabelsList:
            item.Hide()
        self.SetScrollRate(0, 0)
            
    def ShowDoors(self):
        for item in self.doorsAndLabelsList:
            item.Show()
        self.SetScrollRate(1, 1)
        
    def GoToNewVenue(self, event, id):
        if(self.exitsDict.has_key(id)):
            description = self.exitsDict[id]
            self.app.EnterVenueCB(description.uri)
        else:
            text = "The exit is no longer valid "
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
                

class ExitPanel(wxPanel):

    ID_PROPERTIES = wxNewId()
    
    def __init__(self, parent, id, connectionDescription):
        wxPanel.__init__(self, parent, id, wxDefaultPosition,
                         size = wxSize(175, 300), style = wxRAISED_BORDER)
        self.id = id
        self.parent = parent
        self.connectionDescription = connectionDescription
        self.SetBackgroundColour(wxColour(190,190,190))
        self.bitmap = icons.getDefaultDoorClosedBitmap()
        self.bitmapSelect = icons.getDefaultDoorOpenedBitmap()
        self.button = wxStaticBitmap(self, self.id, self.bitmap,
                                     wxPoint(0, 0), wxDefaultSize,
                                     wxBU_EXACTFIT)
        self.SetToolTipString(connectionDescription.description)
        self.label = wxTextCtrl(self, self.id, "", size= wxSize(0,10),
                                style = wxNO_BORDER|wxTE_MULTILINE|wxTE_RICH)
        self.label.SetValue(connectionDescription.name)
        self.label.SetBackgroundColour(wxColour(190,190,190))
        self.label.SetToolTipString(connectionDescription.description)
        self.button.SetToolTipString(connectionDescription.description)
        self.__Layout()
        
        EVT_LEFT_DOWN(self.button, self.OnClick) 
        EVT_LEFT_DOWN(self.label, self.OnClick)
        EVT_LEFT_DOWN(self, self.OnClick)
        EVT_RIGHT_DOWN(self.button, self.OnRightClick) 
        EVT_RIGHT_DOWN(self.label, self.OnRightClick)
        EVT_RIGHT_DOWN(self, self.OnRightClick)
        
        EVT_ENTER_WINDOW(self, self.OnMouseEnter)
        EVT_LEAVE_WINDOW(self, self.OnMouseLeave)
            
    def OnMouseEnter(self, event):
        '''
        Sets a new door image when mouse enters the panel
        '''
        self.button.SetBitmap(self.bitmapSelect)
        
    def OnMouseLeave(self, event):
        '''
        Sets a new door image when mouse leaves the panel
        '''
        self.button.SetBitmap(self.bitmap)
               
    def OnClick(self, event):
        '''
        Move client to a new venue
        '''
        self.parent.GoToNewVenue(event, self.GetButtonId())

    def OnRightClick(self, event):
        '''
        Opens a menu for this connected venue
        '''
        self.x = event.GetX() + self.button.GetPosition().x
        self.y = event.GetY() + self.button.GetPosition().y
        
        propertiesMenu = wxMenu()
        propertiesMenu.Append(self.ID_PROPERTIES,"Properties...",
                             "View information about the venue")
      
       
        self.PopupMenu(propertiesMenu, wxPoint(self.x, self.y))
        EVT_MENU(self, self.ID_PROPERTIES, self.OpenPropertiesDialog)
                
    def OpenPropertiesDialog(self, event):
        '''
        Opens a profile dialog for this exit
        '''
        doorView = ExitPropertiesDialog(self, -1, "Venue Properties",
                                        self.connectionDescription)
        doorView.ShowModal()
        doorView.Destroy()
            
    def GetName(self):
        return self.label.GetValue().lower()

    def GetButtonId(self):
        return self.id

    def __Layout(self):
        b = wxBoxSizer(wxHORIZONTAL)
        b.Add(self.button, 0, wxALIGN_LEFT|wxTOP|wxBOTTOM|wxRIGHT|wxLEFT, 2)
        b.Add(self.label, 1,  wxALIGN_CENTER|wxTOP|wxBOTTOM|wxRIGHT|wxEXPAND, 2)
        b.Add(wxSize(5,2))
        self.SetSizer(b)
        b.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()



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
        wxInitAllImageHandlers()
        imageList = wxImageList(18,18)

        bm = icons.getBulletBitmap()
        bm.SetWidth(18); bm.SetHeight(18)
        self.bullet = imageList.Add(bm)
        

        bm = icons.getDefaultParticipantBitmap()
        bm.SetWidth(18); bm.SetHeight(18)
        self.participantId = imageList.Add(bm)

        bm = icons.getDefaultDataBitmap()
        bm.SetWidth(18); bm.SetHeight(18)
        self.defaultDataId = imageList.Add(bm)

        bm = icons.getDefaultServiceBitmap()
        bm.SetWidth(18); bm.SetHeight(18)
        self.serviceId = imageList.Add(bm)
        self.applicationId = imageList.Add(bm)

        bm = icons.getDefaultNodeBitmap()
        bm = icons.getBulletBitmap()
        bm.SetWidth(18); bm.SetHeight(18)
        self.nodeId = imageList.Add(bm)

        self.tree.AssignImageList(imageList)

    def __GetPersonalDataFromItem(self, treeId):
        # Get data for this id
        dataList = []
        cookie = 0
        
        if(self.tree.GetChildrenCount(treeId)>0):
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
        imageId = None
                
        if profile.profileType == "user":
            imageId =  self.participantId
        elif profile.profileType == "node":
            imageId = self.nodeId
        else:
            log.exception("ContentListPanel.AddParticipant: The user type is not a user nor a node, something is wrong")

        log.debug("ContentListPanel.AddParticipant:: AddParticipant %s (called from %s)", 
                  profile.name,
                  (traceback.extract_stack())[-2])
        
        participant = self.tree.AppendItem(self.participants, profile.name, 
                                           imageId, imageId)
        self.tree.SetItemData(participant, wxTreeItemData(profile)) 
        self.participantDict[profile.publicId] = participant
        self.tree.SortChildren(self.participants)
        self.tree.Expand(self.participants)

        for data in dataList:
            participantData = self.tree.AppendItem(participant, data.name,
                                                   self.defaultDataId, self.defaultDataId)
            self.personalDataDict[data.id] = participantData 
            self.tree.SetItemData(participantData, wxTreeItemData(data))

        if(self.tree.GetChildrenCount(participant) == 0):
            index = -1

            # To solve wx bug
            if sys.platform == "win32":
                index = -2
                
            # Add this text to force a + in front of empty participant
            tempId = self.tree.AppendItem(participant, "No personal data available", index, index)
            self.temporaryDataDict[profile.publicId] = tempId

        self.tree.SortChildren(participant)
            
    def RemoveParticipant(self, profile):
        log.debug("ContentListPanel.RemoveParticipant: Remove participant")
        if profile!=None :
            if(self.participantDict.has_key(profile.publicId)):
                log.debug("ContentListPanel.RemoveParticipant: Found participant in tree")
                id = self.participantDict[profile.publicId]

                log.debug("ContentListPanel.RemoveParticipant: Remove participants data")
                self.RemoveParticipantData(id)
                
                if id!=None:
                    log.debug("ContentListPanel.RemoveParticipant: Removed participant from tree")
                    self.tree.Delete(id)

                log.debug("ContentListPanel.RemoveParticipant: Delete participant from dictionary")
                del self.participantDict[profile.publicId]
                          
    def RemoveParticipantData(self, treeId):
        #
        # This is weird, does it work?
        #
        dataList = self.__GetPersonalDataFromItem(treeId)
                
        for data in dataList:
            data.name

            dataTreeId = self.personalDataDict[data.id]
            del self.personalDataDict[data.id]
            self.tree.Delete(dataTreeId)
                          
    def ModifyParticipant(self, description):
        log.debug('ContentListPanel.ModifyParticipant: Modify participant')
        personalData = None
        if self.participantDict.has_key(description.publicId):
            id = self.participantDict[description.publicId]
            personalData = self.__GetPersonalDataFromItem(id)
       
        self.RemoveParticipant(description)
        self.AddParticipant(description, personalData)

    def AddData(self, dataDescription):
        log.debug("ContentListPanel.AddData: profile.type = %s" %dataDescription.type)

        #if venue data
        if(dataDescription.type == 'None' or dataDescription.type == None):
            log.debug("ContentListPanel.AddData: This is venue data")
            dataId = self.tree.AppendItem(self.data, dataDescription.name,
                                      self.defaultDataId, self.defaultDataId)
            self.tree.SetItemData(dataId, wxTreeItemData(dataDescription)) 
            self.dataDict[dataDescription.id] = dataId
            self.tree.SortChildren(self.data)
            self.tree.Refresh()
            #self.tree.Expand(self.data)
            
        #if personal data
        else:
            log.debug("ContentListPanel.AddData: This is personal data")
            id = dataDescription.type
                        
            if(self.participantDict.has_key(id)):
                log.debug("ContentListPanel.AddData: Data belongs to a participant")
                participantId = self.participantDict[id]
              
                if participantId:
                    ownerProfile = self.tree.GetItemData(participantId).GetData()
                    
                    #
                    # Test if personal data is already added
                    #
                                        
                    if not self.personalDataDict.has_key(dataDescription.id):
                        # Remove the temporary text "No personal data available"
                        if self.temporaryDataDict.has_key(id):
                            tempText = self.temporaryDataDict[id]
                            if tempText:
                                self.tree.Delete(tempText)
                                del self.temporaryDataDict[id]
                                                                        
                        dataId = self.tree.AppendItem(participantId, dataDescription.name, \
                                                      self.defaultDataId, self.defaultDataId)
                        self.tree.SetItemData(dataId, wxTreeItemData(dataDescription))
                        self.personalDataDict[dataDescription.id] = dataId
                        self.tree.SortChildren(participantId)
                        self.tree.SelectItem(participantId)

                    else:
                        log.info("ContentListPanel.AddData: Personal data dict already has this data.")
                                            
            else:
                log.info("ContentListPanel.AddData: Owner of data does not exist")

       
    def UpdateData(self, dataDescription):
        id = None

        #if venue data
        if(self.dataDict.has_key(dataDescription.id)):
            log.debug("ContentListPanel.UpdateData: DataDict has data")
            id = self.dataDict[dataDescription.id]
            
        #if personal data
        elif (self.personalDataDict.has_key(dataDescription.id)):
            log.debug("ContentListPanel.UpdateData: Personal DataDict has data")
            id = self.personalDataDict[dataDescription.id]
            
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
            
        elif (self.personalDataDict.has_key(dataDescription.id)):
            # personal data
            id = self.personalDataDict[dataDescription.id]
            ownerId = self.tree.GetItemParent(id)
            ownerProfile = self.tree.GetItemData(ownerId).GetData()
            self.parent.statusbar.SetStatusText("%s just removed personal file '%s'"%(ownerProfile.name, 
                                                dataDescription.name))
            log.debug("ContentListPanel.RemoveData: Remove personal data")
            id = self.personalDataDict[dataDescription.id]
            del self.personalDataDict[dataDescription.id]

        else:
            log.info("ContentListPanel.RemoveData: No key matches, can not remove data")
           
        if(id != None):
            self.tree.Delete(id)

        if(ownerId and self.tree.GetChildrenCount(ownerId) == 0):
            index = -1
            
            # To solve wx bug
            if sys.platform == "win32":
                index = -2
                
            # Add this text to force a + in front of empty participant
            tempId = self.tree.AppendItem(ownerId, "No personal data available", index, index)
            self.temporaryDataDict[ownerProfile.publicId] = tempId
                          
    def AddService(self, serviceDescription):
        service = self.tree.AppendItem(self.services, serviceDescription.name,
                                      self.serviceId, self.serviceId)
        self.tree.SetItemData(service, wxTreeItemData(serviceDescription)) 
        self.serviceDict[serviceDescription.id] = service
        self.tree.SortChildren(self.services)
        self.tree.Refresh()
        #self.tree.Expand(self.services)
        
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
        #self.tree.Expand(self.applications)
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
                        self.parent.RemoveAppCB(event)


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
                if item.publicId == self.parent.GetProfile().publicId:
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
                log.debug("ContentListPanel.OnRightClick: Is this me? public is = %s, my id = %s "
                          % (item.publicId, self.parent.GetProfile().publicId))
                if(item.publicId == self.parent.GetProfile().publicId):
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
                if key != 'Open':
                    othercmds = 1
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event, cmd=key, itm=item:
                             self.parent.StartCmd(item,cmd=cmd))
        if othercmds:
            menu.AppendSeparator()

        # - Application Monitor
        id = wxNewId()
        menu.Append(id, "Open Monitor...", 
                    "View data and participants present in this application session.")
        EVT_MENU(self, id, lambda event: self.parent.MonitorAppCB(item))

        # - Application Monitor
        id = wxNewId()
        menu.Append(id, "Manage Roles...", 
                    "Manage application authorization.")
        EVT_MENU(self, id, lambda event: self.parent.ModifyAppRolesCB(item))

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
# Text Client Panel

class TextClientPanel(wxPanel):
    
    ID_BUTTON = wxNewId()

    def __init__(self, parent, id, textOutputCtrl, app):
        wxPanel.__init__(self, parent, id)

        self.parent = parent
        self.textOutput = textOutputCtrl
        self.app = app
        
        self.display = wxButton(self, self.ID_BUTTON, "Display",
                                style = wxBU_EXACTFIT)
        self.textInputId = wxNewId()
        self.textInput = wxTextCtrl(self, self.textInputId, "",
                                    size = wxSize(-1, 25),
                                    style= wxTE_MULTILINE)


        self.__SetProperties()
        self.__Layout()

        EVT_TEXT_URL(self.textOutput, self.textOutput.GetId(), self.OnUrl)
        EVT_CHAR(self.textOutput, self.ChangeTextWindow)
        EVT_CHAR(self.textInput, self.TestEnter) 
        EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
        EVT_SIZE(self, self.__OnSize)
      
        self.Show(true)

    def __OnSize(self,event):
        self.__Layout()

    def __SetProperties(self):
        '''
        Sets UI properties.
        '''
        pass
        
    def __Layout(self):
        '''
        Handles UI layout.
        '''
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.textInput, 1, wxALIGN_CENTER | wxEXPAND | wxLEFT, 2)
        box.Add(self.display, 0, wxALIGN_CENTER |wxALL, 2)
        
        self.SetSizer(box)
                
        self.Layout()

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
            if IsOSX():
                pointSize = 12
                
            f = wxFont(pointSize, wxDEFAULT, wxNORMAL, wxBOLD)
            textAttr = wxTextAttr(wxBLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)
            self.textOutput.AppendText(name)
          
            # Set text normal
            f = wxFont(pointSize, wxDEFAULT, wxNORMAL, wxNORMAL)
            textAttr = wxTextAttr(wxBLACK)
            textAttr.SetFont(f)
            self.textOutput.SetDefaultStyle(textAttr)
            self.textOutput.AppendText('\"' + message+'\"\n')

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
        
    def LocalInput(self, event):
        '''
        User input
        '''
        log.debug("TextClientPanel.LocalInput: User writes: %s"
                  % self.textInput.GetValue())

        try:
            text = self.textInput.GetValue()
            self.app.SendTextCB(text)
            self.textInput.Clear()
            self.textInput.SetFocus()
        except:
            self.textInput.Clear()
            text = "Could not send text message successfully"
            title = "Notification"
            log.exception("TextClientPanel.LocalInput: %s" %text)
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
     
    def OnCloseWindow(self):
        '''
        Perform necessary cleanup before shutting down the window.
        '''
        log.debug("TextClientPanel.LocalInput:: Destroy text client")
        self.textClient.Stop()
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
               
################################################################################
#
# Statusbar


class StatusBar(wxStatusBar):
    def __init__(self, parent):
        wxStatusBar.__init__(self, parent, -1)
        self.hidden = 0
       
        self.sizeChanged = False
        EVT_SIZE(self, self.OnSize)
        EVT_IDLE(self, self.OnIdle)

        self.progress = wxGauge(self, wxNewId(), 100,
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)
        self.progress.SetValue(True)

        self.cancelButton = wxButton(self, wxNewId(), "Cancel")
        EVT_BUTTON(self, self.cancelButton.GetId(), self.OnCancel)

        self.__hideProgressUI()
        self.Reset()

        self.fields = 1
        self.SetFieldsCount(self.fields)

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

    def __hideProgressUI(self):
        self.hidden = 1
        self.progress.Hide()
        self.cancelButton.Hide()
       
    def __showProgressUI(self):
        self.hidden = 0
        self.progress.Show()
        self.cancelButton.Show()

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
            self.fields = 1
            self.SetFieldsCount(self.fields)
            return 
        
        self.SetMessage(text)

        # Scale value to range 1-100
        if self.max == 0:
            value = 100
        else:
            value = int(100 * int(value) / int(self.max))
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
            self.fields = 1
            self.SetFieldsCount(self.fields)
       
                                    
    def OnSize(self, evt):
        '''
        Handles normal size events.
        '''
        self.Reposition() 

        # Set a flag so the idle time handler will also do the repositioning.
        # It is done this way to get around a bug where GetFieldRect is not
        # accurate during the EVT_SIZE resulting from a frame maximize.
        self.sizeChanged = True

    def OnIdle(self, evt):
        '''
        When idle, fix object positions in statusbar.
        '''
        if self.sizeChanged:
            self.Reposition()
    
    def Reposition(self):
        '''
        Make sure objects are positioned correct in the statusbar.
        '''
        if self.fields == 1:
            self.__hideProgressUI()
            return

        # Gauge
        rect = self.GetFieldRect(1)
        self.progress.SetPosition(wxPoint(rect.x+2, rect.y+2))
        self.progress.SetSize(wxSize(rect.width-4, rect.height-4))
        self.sizeChanged = False
        
        # Cancel button
        rect = self.GetFieldRect(2)
        self.cancelButton.SetPosition(wxPoint(rect.x+2, rect.y+2))
        #self.cancelButton.SetSize(wxSize(rect.width-2, rect.height-2))
        self.cancelButton.SetSize(wxSize(50, rect.height-2))
        self.sizeChanged = False
        
        
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
        #self.Layout()
        
    def GetValue(self):
        return self.address.GetValue()

    
 
################################################################################

class ProfileDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,-1),
                                   validator = TextValidator("Name"))
        self.emailText = wxStaticText(self, -1, "Email:", style=wxALIGN_LEFT)
        self.emailCtrl = wxTextCtrl(self, -1, "",
                                   validator = TextValidator("Email"))
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
        self.dnText = None
        self.dnTextCtrl = None
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.__Layout()
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.emailCtrl.SetEditable(false)
            self.phoneNumberCtrl.SetEditable(false)
            self.locationCtrl.SetEditable(false)
            self.homeVenueCtrl.SetEditable(false)
            self.profileTypeBox.SetEditable(false)
            self.dnTextCtrl.SetEditable(false)
        else:
            self.nameCtrl.SetEditable(true)
            self.emailCtrl.SetEditable(true)
            self.phoneNumberCtrl.SetEditable(true)
            self.locationCtrl.SetEditable(true)
            self.homeVenueCtrl.SetEditable(true)
            self.profileTypeBox.SetEditable(true)
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __Layout(self):
        self.sizer1 = wxBoxSizer(wxVERTICAL)
        box = wxStaticBox(self, -1, "Profile")
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        self.gridSizer = wxFlexGridSizer(0, 2, 5, 5)
        self.gridSizer.Add(self.nameText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.phoneNumberText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wxALIGN_LEFT, 0)
        if self.profileTypeBox:
            self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        if self.dnText:
            self.gridSizer.Add(self.dnText, 0, wxALIGN_LEFT, 0)
            self.gridSizer.Add(self.dnTextCtrl, 0, wxEXPAND, 0)
        sizer2.Add(self.gridSizer, 1, wxALL|wxEXPAND, 1)

        self.sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxEAST, 10)
        sizer3.Add(self.cancelButton, 0)

        self.sizer1.Add(sizer3, 0, wxALIGN_CENTER|wxSOUTH, 10)

        self.SetSizer(self.sizer1)
        print str(self.GetSize())
        self.sizer1.Fit(self)
        self.SetAutoLayout(1)
        self.Layout()
        print str(self.GetSize())

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
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], 
                                         style = wxCB_DROPDOWN|wxCB_READONLY)
        #self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
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
        self.dnText = wxStaticText(self, -1, "Distinguished name: ")
        self.dnTextCtrl = wxTextCtrl(self, -1, "")
        #self.gridSizer.Add(self.dnText, 0, wxEXPAND, 0)
        #self.gridSizer.Add(self.dnTextCtrl, 0, wxEXPAND, 0)
        #self.sizer1.Fit(self)
        self.__Layout()
        
        self.nameCtrl.SetValue(item.name)
        self.emailCtrl.SetValue(item.email)
        self.phoneNumberCtrl.SetValue(item.phoneNumber)
        self.locationCtrl.SetValue(item.location)
        self.homeVenueCtrl.SetValue(item.homeVenue)
        self.dnTextCtrl.SetValue(item.distinguishedName)

        if(item.GetProfileType() == 'user'):
            self.profileTypeBox.SetValue('user')
        else:
            self.profileTypeBox.SetValue('node')
            
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
        self.nameCtrl = wxTextCtrl(self, -1, profile.GetName(), size = (500,20))
        self.descriptionText = wxStaticText(self, -1, "Description:", 
                                            style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.descriptionCtrl = wxTextCtrl(self, -1, profile.GetDescription(), 
                                          size = (500,20))
        self.urlText = wxStaticText(self, -1, "URL:", style=wxALIGN_LEFT)
        self.urlCtrl = wxTextCtrl(self, -1, profile.GetURI(),  size = (500,20))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.__SetProperties()
        self.__Layout()
                              
    def __SetProperties(self):
        self.nameCtrl.SetEditable(false)
        self.descriptionCtrl.SetEditable(false)
        self.urlCtrl.SetEditable(false)
                                               
    def __Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        box = wxStaticBox(self, -1, "Properties")
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.urlText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.urlCtrl, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
       
        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
        #self.Layout()
 
################################################################################

class DataPropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (500,20))
        self.ownerText = wxStaticText(self, -1, "Owner:", 
                                      style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.ownerCtrl = wxTextCtrl(self, -1, "")
        self.sizeText = wxStaticText(self, -1, "Size:")
        self.sizeCtrl = wxTextCtrl(self, -1, "")
        self.lastModText = wxStaticText(self, -1, "Last modified:")
        self.lastModCtrl = wxTextCtrl(self, -1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__SetProperties()
        self.__SetEditable(true)
        self.__Layout()
        
        self.description = None
        
    def __SetProperties(self):
        self.SetTitle("Please, fill in data information")
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))

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
        box = wxStaticBox(self, -1, "Properties")
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.ownerText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.ownerCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.sizeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.sizeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.lastModText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.lastModCtrl, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

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
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20))
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
        box = wxStaticBox(self, -1, "Properties")
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer2 = wxStaticBoxSizer(box, wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.uriText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.typeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

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
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20))
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
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Profile"), wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.uriText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.uriCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.typeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.typeCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.descriptionText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.descriptionCtrl, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

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
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.list = wxListCtrl(self, wxNewId(), size = wxSize(460, 150),style=wxLC_REPORT)

        self.list.InsertColumn(0, "Address")
        self.list.InsertColumn(1, "Port")
        self.list.InsertColumn(2, "TTL")
        self.list.InsertColumn(3, "Purpose")
        self.list.InsertColumn(4, "Type")

        self.list.SetColumnWidth(0, 100)
        self.list.SetColumnWidth(1, 80)
        self.list.SetColumnWidth(2, 80)
        self.list.SetColumnWidth(3, 100)
        self.list.SetColumnWidth(3, 100)

        self.okButton = wxButton(self, wxID_OK, "Ok")
               
        self.__Layout()

    def PopulateList(self, streamList):
        '''
        Enter correct values into the listctrl.
        '''
       
        if not streamList:
            return

        j = 0
        for stream in streamList:
            self.list.InsertStringItem(j, 'item')
            self.list.SetStringItem(j, 0, str(stream.location.host))
            self.list.SetStringItem(j, 1, str(stream.location.port))
            self.list.SetStringItem(j, 2, str(stream.location.ttl))
            self.list.SetStringItem(j, 3, str(stream.capability.type))
            if stream.static:
                self.list.SetStringItem(j, 4, 'static')
            else:
                self.list.SetStringItem(j, 4, 'dynamic')
                
            j = j + 1
                
    def __Layout(self):
        '''
        Handle UI layout.
        '''
        mainSizer = wxBoxSizer(wxVERTICAL)
        box = wxStaticBox(self, -1, "Multicast Addresses")
        box.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        sizer = wxStaticBoxSizer(box, wxVERTICAL)
        sizer.Add(self.list, 1, wxEXPAND| wxALL, 10)
        
        mainSizer.Add(sizer, 1, wxEXPAND| wxALL, 10)
        mainSizer.Add(self.okButton, 0, wxCENTER | wxALL, 10)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetAutoLayout(1)
        

        

 
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
    n = VenuePropertiesDialog(None, -1, 'Properties')
    n.ShowModal()
    
    #n = AddAppDialog(None, -1, "Start Application Session", 
    #                 ApplicationDescription("test", "test", "test", "test", "test"))
    #if n.ShowModal() == wxID_OK:
    #    print n.GetName()
    
    
    if n:
        n.Destroy()
