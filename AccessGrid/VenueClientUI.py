#-----------------------------------------------------------------------------
# Name:        VenueClientUI.py
# Purpose:     
#
# Author:      Susanne Lefvert, Thomas D. Uram
#
# Created:     2004/02/02
# RCS-ID:      $Id: VenueClientUI.py,v 1.1 2004-02-24 17:04:56 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------
"""
"""

__revision__ = "$Id: VenueClientUI.py,v 1.1 2004-02-24 17:04:56 turam Exp $"
__docformat__ = "restructuredtext en"

import os
import os.path
import time
import logging, logging.handlers
import getopt
from wxPython.wx import *
import string
import webbrowser
import traceback
import re

from time import localtime , strftime
log = logging.getLogger("AG.VenueClientUI")
log.setLevel(logging.WARN)

from AccessGrid import icons
from AccessGrid import Toolkit
from AccessGrid.UIUtilities import AboutDialog, MessageDialog
from AccessGrid.UIUtilities import ErrorDialog, BugReportCommentDialog
from AccessGrid.Platform import GetMimeCommands
from AccessGrid.ClientProfile import *
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.Platform import GetTempDir, GetSharedDocDir
from AccessGrid.Platform import isWindows
from AccessGrid.RoleAuthorization import AddPeopleDialog
from AccessGrid.Utilities import SubmitBug
from AccessGrid.hosting.pyGlobus.AGGSISOAP import faultType
from AccessGrid.VenueClientObserver import VenueClientObserver
from AccessGrid.AppMonitor import AppMonitor

try:
    import win32api
except:
    pass

    

"""

These GUI components live in this file:

Main window components
----------------------

class VenueClientUI(VenueClientEventSubscriber):
class VenueClientFrame(wxFrame):
class VenueAddressBar(wxSashLayoutWindow):
class VenueListPanel(wxSashLayoutWindow):
class VenueList(wxScrolledWindow):
class ContentListPanel(wxPanel):                   
class TextClientPanel(wxPanel):
class ExitPanel(wxPanel):


Dialogs
-------

class SaveFileDialog(wxDialog):
class UploadFilesDialog(wxDialog):
class EditMyVenuesDialog(wxDialog):
class MyVenuesEditValidator(wxPyValidator):
class RenameDialog(wxDialog):
class AddMyVenueDialog(wxDialog):
class UrlDialog(wxDialog):
class ProfileDialog(wxDialog):
class TextValidator(wxPyValidator):
class ServicePropertiesDialog(wxDialog):
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



    def __init__(self, venueClient, controller):

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
        self.isVenueAdministrator = false

        wxFrame.__init__(self, NULL, -1, "")
        self.__BuildUI(NULL,-1,"")
        self.SetSize(wxSize(500, 400))
        
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
            self.__OpenVenueClient(profile)
            
        self.nodeManagementFrame = None

        # Help Doc locations
        self.manual_url = os.path.join(GetSharedDocDir(), "VenueClientManual",
                                       "VenueClientManualHTML.htm")
        self.agdp_url = "http://www.accessgrid.org/agdp"
        self.ag_url = "http://www.accessgrid.org/"
        self.flag_url = "http://www.mcs.anl.gov/fl/research/accessgrid"
        self.fl_url = "http://www.mcs.anl.gov/fl/"
        self.bugzilla_url = "http://bugzilla.mcs.anl.gov/AccessGrid"


       
    ###########################################################################################
    # Section Index
    # - Private Methods
    # - Pure UI Methods
    #
    # - Menu Callbacks
    # - Core UI Callbacks
    # - Observer Impl
    # - Manipulators
    ###########################################################################################
    
            
    ###########################################################################################
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
            self.__OpenVenueClient(profile)

        else:
            profileDialog.Destroy()
            os._exit(0)

    def __OpenVenueClient(self, profile):
        """
        This method is called during client startup.  It displays the
        venue client GUI.
        
        **Arguments:**
        
        *profile* The ClientProfile you want to be associated with in the venue.
        """

        self.venueAddressBar.SetAddress(self.venueClient.GetProfile().homeVenue)
        self.Show(true)
        
    def __SetStatusbar(self):
        self.statusbar.SetToolTipString("Statusbar")   
    
    def __SetMenubar(self):
        self.SetMenuBar(self.menubar)

        # ---- menus for main menu bar
        self.venue = wxMenu()
        self.venue.Append(self.ID_VENUE_DATA_ADD,"Add Data...",
                             "Add data to the venue.")
        self.venue.Append(self.ID_VENUE_SERVICE_ADD,"Add Service...",
                                "Add a service to the venue.")

        self.applicationMenu = self.BuildAppMenu(None, "")
        self.venue.AppendMenu(self.ID_VENUE_APPLICATION,"Start &Application Session",
                              self.applicationMenu)

        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_SAVE_TEXT,"Save Text...",
                             "Save text from chat to file.")
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,"Administrate Roles...",
                             "Change venue authorization settings.")
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE,"&Exit", "Exit venue")
        
        self.menubar.Append(self.venue, "&Venue")
              
        self.preferences = wxMenu()
        self.preferences.Append(self.ID_PROFILE,"&Edit Profile...", "Change your personal information")
        #
        # Retrieve the cert mgr GUI from the application.
        #

        gui = None
        try:
            mgr = Toolkit.GetApplication().GetCertificateManager()
            gui = mgr.GetUserInterface()

        except:
            log.exception("VenueClientFrame.__SetMenubar: Cannot retrieve certificate mgr user interface, continuing")

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
        self.help.Append(self.ID_HELP_BUG_REPORT, "&Submit Error Report or Feature Request","Send report to bugzilla")

        self.help.Append(self.ID_HELP_BUGZILLA, "&Bugzilla Web Site","See current error reports and feature request")

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
        EVT_MENU(self, self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, self.ModifyVenueRolesCB)
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
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.SetTitle("Venue Client")
        self.SetIcon(icons.getAGIconIcon())
        self.statusbar.SetStatusWidths([-1])
        currentHeight = self.venueListPanel.GetSize().GetHeight()
        self.venueListPanel.SetSize(wxSize(180, 300))
        
    def __FillTempHelp(self, x):
        if x == '\\':
            x = '/'
        return x

    def __LoadMyVenues(self, venueURL = None):
    
        # Delete existing menu items
        for id in self.myVenuesMenuIds.values():
            self.myVenues.Delete(id)
        
        self.myVenuesMenuIds = {}
        self.myVenuesDict = self.controller.GetMyVenues()
                   
        # Create menu items
        for name in self.myVenuesDict.keys():
            id = wxNewId()
            self.myVenuesMenuIds[name] = id
            url = self.myVenuesDict[name]
            text = "Go to: " + url
            self.myVenues.Append(id, name, text)
            EVT_MENU(self, id, self.GoToMenuAddressCB)
                        

    def __BuildUI(self,parent,id,title):
        
        self.Centre()
        self.menubar = wxMenuBar()
        self.statusbar = self.CreateStatusBar(1)
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, \
                                               self.myVenuesDict, 'default venue')
        self.textInputWindow = wxSashLayoutWindow(self, self.ID_WINDOW_BOTTOM2, wxDefaultPosition,
                                                  wxSize(200, 35))
        self.textOutputWindow = wxSashLayoutWindow(self, self.ID_WINDOW_BOTTOM, wxDefaultPosition,
                                                   wxSize(200, 35))
        self.textOutput = wxTextCtrl(self.textOutputWindow, wxNewId(), "",
                                style= wxTE_MULTILINE|wxTE_READONLY|wxTE_RICH|wxTE_AUTO_URL)
        self.textClientPanel = TextClientPanel(self.textInputWindow, -1, self.textOutput, self)
               
        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT)
        self.contentListPanel = ContentListPanel(self)
        dataDropTarget = DataDropTarget(self)
        self.contentListPanel.SetDropTarget(dataDropTarget)
        
        self.__SetStatusbar()
        self.__SetMenubar()
        self.__SetProperties()
        self.Layout()
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
            self.venueListPanel.SetDefaultSize(wxSize(width, 1000))

        elif eID == self.ID_WINDOW_BOTTOM:
            height = event.GetDragRect().height
            self.textOutputWindow.SetDefaultSize(wxSize(1000, height))
           
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
                newInputHeight = newInputHeight - (outputMinSize - newOutputHeight)
                newOutputHeight = outputMinSize
                            
            self.textInputWindow.SetDefaultSize(wxSize(1000, newInputHeight))
                        
            # Make output smaller when input is bigger and vice versa.
            self.textOutputWindow.SetDefaultSize(wxSize(1000, newOutputHeight))

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
                
    def __OnSize(self, event = None):
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
       
    def __CleanUp(self):
        self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

    def __HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)
        self.menubar.Enable(self.ID_MYVENUE_ADD, false)
        #self.menubar.Enable(self.ID_MYVENUE_GOTODEFAULT, false)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, false)
        self.menubar.Enable(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, false)
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, false)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, false)
        
    def __ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, true)
        self.menubar.Enable(self.ID_MYVENUE_ADD, true)
        self.menubar.Enable(self.ID_MYVENUE_GOTODEFAULT, true)
        self.menubar.Enable(self.ID_MYVENUE_SETDEFAULT, true)
        
        # Only show administrate button when you can administrate a venue.
        if self.isVenueAdministrator:
            self.menubar.Enable(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, true)
        
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, true)
        self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, true)

    def __EnableAppMenu(self, flag):
        for entry in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Enable( entry.GetId(), flag )

    def __Notify(self,text,title):
        dlg = wxMessageDialog(self, text, title, style = wxICON_INFORMATION | wxOK)
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
    ###########################################################################################


    ###########################################################################################
    #
    # Pure UI Methods
        
    def Layout(self):
        self.venueAddressBar.SetDefaultSize(wxSize(1000, 60))
        self.venueAddressBar.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.venueAddressBar.SetAlignment(wxLAYOUT_TOP)

        self.textOutputWindow.SetDefaultSize(wxSize(1000, 100))
        self.textOutputWindow.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.textOutputWindow.SetAlignment(wxLAYOUT_BOTTOM)
        self.textOutputWindow.SetSashVisible(wxSASH_TOP, TRUE)

        wxLayoutAlgorithm().LayoutWindow(self.textOutputWindow, self.textClientPanel)
         
        self.textInputWindow.SetDefaultSize(wxSize(1000, 45))
        self.textInputWindow.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.textInputWindow.SetAlignment(wxLAYOUT_BOTTOM)
        self.textInputWindow.SetSashVisible(wxSASH_TOP, TRUE)
        
        wxLayoutAlgorithm().LayoutWindow(self, self.textInputWindow)
       
        self.venueListPanel.SetDefaultSize(wxSize(180, 1000))
        self.venueListPanel.SetOrientation(wxLAYOUT_VERTICAL)
        self.venueListPanel.SetSashVisible(wxSASH_RIGHT, TRUE)
        self.venueListPanel.SetAlignment(wxLAYOUT_LEFT)

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)


    def UpdateLayout(self):
        width = self.venueListPanel.GetSize().GetWidth()
        self.venueListPanel.SetDefaultSize(wxSize(width, 1000))
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)


    # end Pure UI Methods
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Menu Callbacks

    #
    # Venue Menu
    #

    def AddDataCB(self, event = None, fileList = None):
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

        # Prompt for files to upload
        fileList = self.SelectFiles("Choose file(s):")
        if fileList:
            self.controller.AddDataCB(fileList)

    def AddServiceCB(self, event):
        serviceDescription = self.OpenAddServiceDialog()
        if serviceDescription:
            self.controller.AddServiceCB(serviceDescription)

    def SaveTextCB(self, event):
        """
        Saves text from text chat to file.
        """
        wildcard = "Text Files |*.txt|" \
                   "All Files |*.*"
        filePath = self.SelectFile("Choose a file:", wildcard = wildcard)
        text = self.GetText()
        if filePath:
            self.controller.SaveTextCB(filePath,text)
        
    def ModifyVenueRolesCB(self,event):
        rolesDict = self.ModifyVenueRoles()
        if rolesDict:
            self.controller.ModifyVenueRolesCB(rolesDict)

    def ExitCB(self, event):
        """
        Called when the window is closed using the built in close button
        """
        self.OnExit()
        self.controller.ExitCB()

    #
    # Preferences Menu
    #
    
    def EditProfileCB(self, event = None):
        profile = self.OpenEditProfileDialog()
        if profile:
            self.controller.EditProfileCB(profile)
      
        
    """
    ManageCertificates menu is provided by CertMgmt module
    """


    def UseMulticastCB(self,event):
        self.controller.UseMulticastCB()

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
            self.controller.UseUnicastCB(selectedProvider)

        else:
            # Set the menu checkbox appropriately
            transport = self.venueClient.GetTransport()
            self.SetTransport(transport)

    def EnableVideoCB(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_VIDEO)
        self.controller.EnableVideoCB(enableFlag)

    def EnableAudioCB(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_AUDIO)
        self.controller.EnableAudioCB(enableFlag)
    
    def SetNodeUrlCB(self, event = None):
        nodeUrl = None
        setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                     self.venueClient.GetNodeServiceUri(), "Please, specify node service URL")

        if setNodeUrlDialog.ShowModal() == wxID_OK:
            nodeUrl = setNodeUrlDialog.address.GetValue()
            self.controller.SetNodeUrlCB(nodeUrl)
       
        setNodeUrlDialog.Destroy()
        
    def ManageNodeCB(self, event):
        self.OpenNodeManagement()
    
    # 
    # MyVenues Menu
    #
    
    
    def GoToDefaultVenueCB(self,event):
        self.SetVenueUrl(venueUrl)
        self.controller.GoToDefaultVenueCB()

    def SetAsDefaultVenueCB(self,event):
        self.controller.SetAsDefaultVenueCB()

    def AddToMyVenuesCB(self, event):
        url = self.venueClient.GetVenue()
        name = self.venueClient.GetVenueName()
        myVenuesDict = self.controller.GetMyVenues()
        if url is not None:
            if(url not in myVenuesDict.values()):
                venueName = self.OpenAddMyVenueDialog(name)
                if venueName:
                    if myVenuesDict.has_key(venueName):
                        info = "A venue with the same name is already added, do you want to overwrite it?"
                        if self.Prompt(info ,"Duplicated Venue"):
                            self.RemoveFromMyVenues(venueName)
                            self.controller.AddToMyVenuesCB(venueName,url)
                        else:
                            # Do not add this venue
                            return
                    else:
                        self.controller.AddToMyVenuesCB(venueName,url)
            else:
                for n in myVenuesDict.keys():
                    if myVenuesDict[n] == url:
                        name = n
                text = "This venue is already added to your venues as "+"'"+name+"'"
                self.Notify(text, "Add venue")

    def EditMyVenuesCB(self, event):
        myVenues = None
        venuesDict = self.controller.GetMyVenues()
        editMyVenuesDialog = EditMyVenuesDialog(self, -1, "Edit your venues", venuesDict)
        if (editMyVenuesDialog.ShowModal() == wxID_OK):
            myVenues = editMyVenuesDialog.GetValue()
            self.controller.EditMyVenuesCB(myVenues)
            self.__LoadMyVenues()

        editMyVenuesDialog.Destroy()

    def GoToMenuAddressCB(self, event):
        name = self.menubar.GetLabel(event.GetId())
        venueUrl = self.myVenuesDict[name]
        self.SetVenueUrl(venueUrl)
        self.controller.GoToMenuAddressCB(venueUrl)

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
            
            SubmitBug(comment, email)
            bugFeedbackDialog = wxMessageDialog(self, "Your error report has been sent, thank you.",
                                                "Error Reported", style = wxOK|wxICON_INFORMATION)
            bugFeedbackDialog.ShowModal()
            bugFeedbackDialog.Destroy()       
            
        bugReportCommentDialog.Destroy()
        
    def OpenBugzillaCB(self,event):
        self.OpenURL(self.bugzilla_url)
        

    # Menu Callbacks
    #
    ###########################################################################################

    ###########################################################################################
    #
    # Core UI Callbacks
    
    
    def EnterVenueCB(self, venueUrl, backFlag):
        try:
            self.SetBusy()
            self.SetStatusText("Trying to enter venue at %s" % (venueUrl,))

            self.controller.EnterVenueCB(venueUrl,backFlag)
        finally:
            self.EndBusy()

    #
    # Participant Actions
    #
       
    def ViewProfileCB(self, event=None):
        participant = self.GetSelectedItem()
                   
        if(participant != None and isinstance(participant, ClientProfile)):
            self.OpenViewProfileDialog(participant)
        else:
            self.Notify("Please, select the participant you want to view information about") 

    def AddPersonalDataCB(self, event=None):
        fileList = self.OpenUploadFilesDialog()
        self.controller.AddPersonalDataCB(fileList)

    def FollowCB(self, event):
        personToFollow = self.GetSelectedItem()
        self.controller.FollowCB(personToFollow)
                
    def UnFollowCB(self, event):
        self.controller.UnFollowCB()

    #
    # Data Actions
    #

    """
    AddData is up above in menu callbacks
    """

    def OpenDataCB(self, event):
        data = self.GetSelectedItem()
        self.controller.OpenDataCB(data)
              
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
        self.controller.RemoveDataCB(itemList)


    #
    # Service Actions
    #
    
    """
    AddService is up above in menu callbacks
    """
    
    def OpenServiceCB(self,event):
        service = self.GetSelectedItem()
        self.controller.OpenServiceCB(service)
    
    def RemoveServiceCB(self, event):
        itemList = self.GetSelectedItems()
        self.controller.RemoveServiceCB(itemList)
        
            
    #
    # Application Actions
    #
    
    def OpenApplicationCB(self, event):
        app = self.GetSelectedItem()
        self.controller.OpenApplicationCB(app)
    
    def RemoveApplicationCB(self,event):
        appList = self.GetSelectedItems()
        self.controller.RemoveApplicationCB(appList)

    def StartApplicationCB(self, app, event=None):
        name, appDescription = self.OpenAddAppDialog(app)
        app.description = appDescription
        self.controller.StartApplicationCB(name,app)
              
    def RunApplicationCB(self, appDesc, cmd='Open'):
        self.controller.RunApplicationCB()

    def MonitorAppCB(self, application):
        """
        Open monitor for the application.
        """
        self.OpenAppMonitor(application)
        
        
    #
    # Other
    #
    
    def SendTextCB(self,text):
        self.controller.SendTextCB(text)
        

    #
    # Calls to Venue Client
    
    def GetProfile(self):
        return self.venueClient.GetProfile()
        
    def GetVenue(self):
        return self.venueClient.GetVenue()
        

    # end Core UI Callbacks
    #
    ###########################################################################################


    ###########################################################################################
    #
    # Accessors

    def GetSelectedItem(self):
        return self.contentListPanel.GetLastClickedTreeItem()

    def GetSelectedItems(self):
        idList = self.contentListPanel.GetSelections()
        itemList = map( lambda id: self.contentListPanel.GetItemData(id).GetData(), idList )
        return itemList

    def GetVideoEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_VIDEO)

    def GetAudioEnabled(self):
        return self.preferences.IsChecked(self.ID_ENABLE_AUDIO)

    def GetText(self):
        return self.textClientPanel.GetText()
    
    # end Accessors
    #
    ###########################################################################################

    ###########################################################################################
    #
    # General Implementation
    

    #
    # Upload Files Methods
    #
        
    def OpenUploadFilesDialog(self):
        #
        # Create the dialog for the upload.
        #
        self.uploadFilesDialog = UploadFilesDialog(self, -1, "Uploading files")
        self.uploadFilesDialog.Show(1)
                
    def UpdateUploadFilesDialog(self, filename, sent, total, file_done, xfer_done):
        wxCallAfter(self.uploadFilesDialog.SetProgress,filename,sent,total,file_done,xfer_done)
        
    def UploadFilesDialogCancelled(self):
        return self.uploadFilesDialog.IsCancelled()      
        
    #
    # Save Files Methods
    #
    
    def OpenSaveFileDialog(self, filename, size):
        #
        # Create the dialog for the download.
        #
        self.saveFileDialog = SaveFileDialog(self, -1, "Saving file",
                                             "Saving file to %s ...     "
                                             % (filename),
                                             "Saving file to %s ... done"
                                             % (filename),
                                             size)
        self.saveFileDialog.Show(1)
        
    def UpdateSaveFileDialog(self, sent, xfer_done):
        wxCallAfter(self.saveFileDialog.SetProgress,sent,xfer_done)
        
    def SaveFileDialogCancelled(self):
        return self.saveFileDialog.IsCancelled()      
        

        
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
                messageDlg = wxMessageDialog(self, "The file %s already exists. Do you want to replace it?"%fileName, "Save Text" , style = wxICON_INFORMATION | wxYES_NO | wxNO_DEFAULT)
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
    
        dlg = wxMessageDialog(self, text, title, style = wxICON_INFORMATION | wxOK | wxCANCEL)
        ret = dlg.ShowModal()
        if ret == wxID_OK:
            return 1
        return 0

    def Notify(self,text,title):
    
        wxCallAfter(self.__Notify,text,title)

    def Warn(self,text,title):
        wxCallAfter(self.__Warn,text,title)

    def Error(self,text,title):
        ErrorDialog(None, text, title, style = wxOK  | wxICON_ERROR)


    #
    # Dialogs
    #

    def OpenAddServiceDialog(self):
    
        serviceDescription = None
    
        addServiceDialog = ServicePropertiesDialog(self, -1,
                                         'Please, fill in service details')
        if (addServiceDialog.ShowModal() == wxID_OK):

            try:
                serviceDescription = addServiceDialog.GetValue()
                log.debug("Adding service: %s to venue" %serviceDescription.name)
            except:
                log.exception("bin.VenueClient::AddService: Error occured when trying to add service")
                ErrorDialog(None, "The service could not be added", "Add Service Error", style = wxOK | wxICON_ERROR)

        addServiceDialog.Destroy()
        return serviceDescription

    def OpenAddAppDialog(self,app):
        retVal = None
        dlg = AddAppDialog(self, -1, "Start Application Session", app)
        if dlg.ShowModal() == wxID_OK:
            name = dlg.GetName()
            appDescription = dlg.GetDescription()
            retVal = ( name, appDescription )
        dlg.Destroy()
        
        return retVal
        
    def OpenNodeManagement(self):
        if self.nodeManagementFrame:
            self.nodeManagementFrame.Raise()
        else:
            self.nodeManagementFrame = NodeManagementClientFrame(self, -1, "Access Grid Node Management")
            log.debug("VenueClientFrame.OpenNodeMgmtApp: open node management")
            self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeServiceUri() )
            if self.nodeManagementFrame.Connected(): # Right node service uri
                self.nodeManagementFrame.UpdateUI()
                self.nodeManagementFrame.Show(true)

            else: # Not right node service uri
                setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                             self.venueClient.GetNodeServiceUri(), "Please, specify node service URL")

                if setNodeUrlDialog.ShowModal() == wxID_OK:
                    self.venueClient.SetNodeUrl(setNodeUrlDialog.GetValue())
                    self.nodeManagementFrame.AttachToNode( self.venueClient.GetNodeServiceUri() )

                    if self.nodeManagementFrame.Connected(): # try again
                        self.nodeManagementFrame.Update()
                        self.nodeManagementFrame.Show(true)

                    else: # wrong url
                        MessageDialog(self, \
                                      'Can not open node service management\nbased on the URL you specified', \
                                      'Node Management Error')

                setNodeUrlDialog.Destroy()
                self.nodeManagementFrame = None


    def OpenAddMyVenueDialog(self, name):
        newName = None
        dialog = AddMyVenueDialog(self, -1, name)
        if (dialog.ShowModal() == wxID_OK):
            newName = dialog.GetValue()
            
        dialog.Destroy()
            
        return newName


        
    def OpenEditProfileDialog(self):
        profile = None
        profileDialog = ProfileDialog(NULL, -1,
                                  'Please, fill in your profile information')
        profileDialog.SetProfile(self.venueClient.GetProfile())
        if (profileDialog.ShowModal() == wxID_OK):
            profile = profileDialog.GetNewProfile()
            log.debug("VenueClientFrame.EditProfile: change profile: %s" %profile.name)
        profileDialog.Destroy()
        return profile
        
    def OpenViewProfileDialog(self, participant):
        profileView = ProfileDialog(self, -1, "Profile")
        log.debug("VenueClientFrame.OpenParticipantProfile: open profile view with this participant: %s" %participant.name)
        profileView.SetDescription(participant)
        profileView.ShowModal()
        profileView.Destroy()

    def ModifyVenueRoles(self):
        venueUri = self.venueClient.GetVenue()
        
        rolesDict = None

        # Open the dialog with selected role in the combo box
        addPeopleDialog = AddPeopleDialog(self, -1, "Modify Roles", venueUri)
        if addPeopleDialog.ShowModal() == wxID_OK:
            # Get new role configuration
            rolesDict = addPeopleDialog.GetInfo()

        return rolesDict
        
    def OpenAppMonitor(self, application):
        '''
        Open monitor for the application.
        '''
        # Get application proxy from service in venue.
        appUrl = application.uri
       
        # Create new application monitor
        self.monitor = AppMonitor(self, appUrl)
    


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

    def SetBusy(self):
        wxBeginBusyCursor()
        
    def EndBusy(self):
        wxEndBusyCursor()
        
    def SetStatusText(self,text):
        self.statusbar.SetStatusText(text)

    def GoBackCB(self):
        """
        This method is called when the user wants to go back to last visited venue
        """
        log.debug("Go back")
        print "callinbg controller back"
        self.controller.GoBackCB()
        
    def StartCmd(self, command, item=None, namedVars=None, verb=None):
        self.controller.StartCmd(command,item,namedVars,verb)
            
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
        
    def GetMimeCommandNames(self, mimeType):
        return self.controller.GetMimeCommandNames(mimeType)
        

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


    def HandleServerConnectionFailure(self):
        if self.venueClient and self.venueClient.IsInVenue():
            log.debug("bin::VenueClient::HandleServerConnectionFailure: call exit venue")
            self.__CleanUp()
            self.venueAddressBar.SetTitle("You are not in a venue",
                                                'Click "Go" to connect to the venue, which address is displayed in the address bar') 
            self.venueClient.ExitVenue()
            MessageDialog(None, "Your connection to the venue is interrupted and you will be removed from the venue.  \nPlease, try to connect again.", "Lost Connection")

    def AddToMyVenues(self,name,url):
        id = wxNewId()
        text = "Go to: " + url
        self.myVenues.Append(id, name, text)
        self.myVenuesMenuIds[name] = id
        self.myVenuesDict[name] = url
        EVT_MENU(self, id, self.GoToMenuAddress)
    
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
            
            self.controller.ExitCB()

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


    def BuildAppMenu(self, event, prefix):
        """
        Build the menu of installed applications
        """
        menu = wxMenu()
        
        appDescList = self.venueClient.GetInstalledApps()
                
        # Add applications in the appList to the menu
        for app in appDescList:
            if app != None and app.name != None:
                menuEntryLabel = prefix + app.name
                appId = wxNewId()
                menu.Append(appId,menuEntryLabel,menuEntryLabel)
                callback = lambda event,theApp=app: self.StartApplicationCB(theApp)
                EVT_MENU(self, appId, callback)

        return menu

           

    # end General Implementation
    #
    ###########################################################################################

    ###########################################################################################
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
        
        *profile* The modified ClientProfile of the participant that changed profile information
        """

        log.debug("EVENT - Modify participant: %s" %(profile.name))
        wxCallAfter(self.statusbar.SetStatusText, "%s changed profile information" %profile.name)
        wxCallAfter(self.contentListPanel.ModifyParticipant, profile)

    def AddData(self, dataDescription):
        """
        This method is called every time new data is added to the venue.
        Appropriate gui updates are made in client.
        
        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got added to the venue
        """

        if dataDescription.type == "None" or dataDescription.type == None:
            wxCallAfter(self.statusbar.SetStatusText, "file '%s' has been added to venue" %dataDescription.name)
            
            # Just change venuestate for venue data.
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass

        log.debug("EVENT - Add data: %s" %(dataDescription.name))
        wxCallAfter(self.contentListPanel.AddData, dataDescription)

    def UpdateData(self, dataDescription):
        """
        This method is called when a data item has been updated in the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that got updated in the venue
        """
        
        log.debug("EVENT - Update data: %s" %(dataDescription.name))
        wxCallAfter(self.contentListPanel.UpdateData, dataDescription)

    def RemoveData(self, dataDescription):
        """
        This method is called every time data is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *dataDescription* The DataDescription representing data that was removed from the venue
        """

        # Handle venue data (personal data is in VenueClientUIClasses)
        if dataDescription.type == "None" or dataDescription.type == None:
            wxCallAfter(self.statusbar.SetStatusText, "file '%s' has been removed from venue" %dataDescription.name)
        else:
            # Personal data is handled in VenueClientUIClasses to find out who the data belongs to
            pass
        
        wxCallAfter(self.statusbar.SetStatusText, "File '%s' has been removed from the venue" %dataDescription.name)
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
        wxCallAfter(self.statusbar.SetStatusText, "Service '%s' just got added to the venue" %serviceDescription.name)
        wxCallAfter(self.contentListPanel.AddService, serviceDescription)

    def RemoveService(self, serviceDescription):
        """
        This method is called every time service is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *serviceDescription* The ServiceDescription representing the service that was removed from the venue
        """

        log.debug("EVENT - Remove service: %s" %(serviceDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, "Service '%s' has been removed from the venue" %serviceDescription.name)
        wxCallAfter(self.contentListPanel.RemoveService, serviceDescription)

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
        wxCallAfter(self.statusbar.SetStatusText, "Application '%s' has been removed from the venue" %appDescription.name)
        wxCallAfter(self.contentListPanel.RemoveApplication, appDescription)

    def AddConnection(self, connDescription):
        """
        This method is called every time a new exit is added to the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Add connection: %s" %(connDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, "A new exit, '%s', has been added to the venue" %connDescription.name)  
        wxCallAfter(self.venueListPanel.AddVenueDoor, connDescription)

    def RemoveConnection(self, connDescription):
        """
        This method is called every time an exit is removed from the venue.
        Appropriate gui updates are made in client.

        **Arguments:**
        
        *connDescription* The ConnectionDescription representing the exit that was added to the venue
        """

        log.debug("EVENT - Remove connection: %s" %(connDescription.name))
        wxCallAfter(self.statusbar.SetStatusText, "The exit to '%s' has been removed from the venue" %connDescription.name)  
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
        self.__UpdateTransports()
        
    def RemoveStream(self,streamDesc):
        self.__UpdateTransports()
        
    def ModifyStream(self,streamDesc):
        self.__UpdateTransports()
        
    def AddText(self,name,text):
        """
        This method is called when text is received from the text service.

        **Arguments:**
        
        *name* The name of the user who sent the message
        *text* The text sent
        """
        
        self.textClientPanel.OutputText(name, text)

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
                MessageDialog(None, text, "Notification")
            elif warningString.startswith("Authorization failure connecting to server"):
                text = warningString
                MessageDialog(None, text, "Authorization failure")
                log.debug(warningString)
            else:
                log.debug("warningString: %s" %warningString)
                text = "Can not connect to venue located at %s.  Please, try again." % URL
                MessageDialog(None, text, "Can not enter venue")
            return

        # initialize flag in case of failure
        enterUISuccess = 1

        try:
            
            wxCallAfter(self.statusbar.SetStatusText, "Entered venue %s successfully" %self.venueClient.GetVenueName())

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
            for exit in venueState.connections.values():
                wxCallAfter(self.venueListPanel.AddVenueDoor,
                            exit)
                # log.debug("   %s" %(exit.name))

            #
            # Reflect venue entry in the client
            #
            wxCallAfter(self.textClientPanel.OutputText, None,
                        "-- Entered venue %s" % self.venueClient.GetVenueName())
            wxCallAfter(self.SetVenueUrl, URL)
            
            # Venue data storage location
            # self.upload_url = self.venueClient.GetDataStoreUploadUrl()
            #log.debug("Get upload url %s" %self.dataStoreUploadUrl)

            # Get the user's administrative status
            self.isVenueAdministrator = self.venueClient.IsVenueAdministrator()
            
            # log.debug("Add your personal data descriptions to venue")
            wxCallAfter(self.statusbar.SetStatusText, "Add your personal data to venue")
            warningString = warningString 

            # Enable menus
            wxCallAfter(self.__ShowMenu)
            
            #
            # Enable the application menu that is displayed over
            # the Applications items in the list
            # (this is not the app menu above)
            wxCallAfter(self.__EnableAppMenu, true)

            # Enable/disable the unicast menu entry appropriately
            self.__UpdateTransports()
            
            # Update the UI
            wxCallAfter(self.AddVenueToHistory, URL)
            
            log.debug("Entered venue")
            
            #
            # Display all non fatal warnings to the user
            #
            if warningString != '': 
                message = "Following non fatal problems have occured when you entered the venue:\n" + warningString
                MessageDialog(None, message, "Notification")
                
                wxCallAfter(self.statusbar.SetStatusText, "Entered %s successfully" %self.venueClient.GetVenueName())
       
        except Exception, e:
            log.exception("bin.VenueClient::EnterVenue failed")
            enterUISuccess = 0

        if not enterUISuccess:
            text = "You have not entered the venue located at %s.\nAn error occured.  Please, try again."%URL
            ErrorDialog(None, text, "Enter Venue Error",
                          style = wxOK  | wxICON_ERROR)

    def ExitVenue(self):
        wxCallAfter(self.venueListPanel.CleanUp)

        # Disable menus
        wxCallAfter(self.__HideMenu)


    # end Implementation of VenueClientObserver
    #
    ###########################################################################################



###########################################################################################
#
# VenueClient UI components
#
###########################################################################################


###########################################################################################
#
# Venue Address Bar

class VenueAddressBar(wxSashLayoutWindow):
    ID_GO = wxNewId()
    ID_BACK = wxNewId()
    ID_ADDRESS = wxNewId()
    
    def __init__(self, parent, id, venuesList, defaultVenue):
        wxSashLayoutWindow.__init__(self, parent, id, wxDefaultPosition, \
                                    wxDefaultSize)
        self.parent = parent
        self.panel = wxPanel(self, -1)
        self.addressPanel = wxPanel(self.panel, -1, style = wxRAISED_BORDER)
        self.titlePanel =  wxPanel(self.panel, -1, size = wxSize(1000, 40), style = wxRAISED_BORDER)
        self.title = wxStaticText(self.titlePanel, wxNewId(), 'You are not in a venue', style = wxALIGN_CENTER)
        font = wxFont(16, wxSWISS, wxNORMAL, wxNORMAL, false)
        self.title.SetFont(font)
        self.address = wxComboBox(self.addressPanel, self.ID_ADDRESS, defaultVenue,
                                  choices = venuesList.keys(),
                                  style = wxCB_DROPDOWN)
        
        self.goButton = wxButton(self.addressPanel, self.ID_GO, "Go", wxDefaultPosition, wxSize(20, 21))
        self.backButton = wxButton(self.addressPanel, self.ID_BACK , "<<", wxDefaultPosition, wxSize(20, 21))
        self.Layout()
        self.__AddEvents()
        
    def __AddEvents(self):
        EVT_BUTTON(self, self.ID_GO, self.CallAddress)
        EVT_BUTTON(self, self.ID_BACK, self.GoBack)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.CallAddress)
        
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
        self.Layout()

    def AddChoice(self, url):
        if self.address.FindString(url) == wxNOT_FOUND:
            self.address.Append(url)
        self.SetAddress(url)
            
    def Layout(self):
        venueServerAddressBox = wxBoxSizer(wxVERTICAL)
        
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(2,5)
        box.Add(self.backButton, 0, wxRIGHT|wxALIGN_CENTER|wxLEFT, 5)
        box.Add(self.address, 1, wxRIGHT|wxALIGN_CENTER, 5)
        box.Add(self.goButton, 0, wxRIGHT|wxALIGN_CENTER, 5)
        self.addressPanel.SetSizer(box)
        box.Fit(self.addressPanel)

        titleBox = wxBoxSizer(wxHORIZONTAL)
        titleBox.Add(self.title, 1, wxEXPAND|wxCENTER)
        titleBox.Add(2,5)
        self.titlePanel.SetSizer(titleBox)
        titleBox.Fit(self.titlePanel)

        venueServerAddressBox.Add(self.addressPanel, -1, wxEXPAND)
        venueServerAddressBox.Add(self.titlePanel, -1, wxEXPAND)
        self.panel.SetSizer(venueServerAddressBox)
        venueServerAddressBox.Fit(self.panel)
        
        wxLayoutAlgorithm().LayoutWindow(self, self.panel)
        
        
    def GoBack(self, event):
        self.parent.GoBackCB()
      
    def CallAddress(self, event = None):
        url = self.address.GetValue()
        venueUri = self.__FixSpaces(url)
        self.parent.EnterVenueCB(venueUri, 0)

        
        
###########################################################################################
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
    
    ID_MINIMIZE = wxNewId()
    ID_MAXIMIZE = wxNewId()
      
    def __init__(self, parent,id):
        wxSashLayoutWindow.__init__(self, parent, id)
        self.parent = parent
        self.panel = wxPanel(self, -1,  style = wxSUNKEN_BORDER)
        self.list = VenueList(self.panel, parent)
        self.minimizeButton = wxButton(self.panel, self.ID_MINIMIZE, "<<", \
                                       wxDefaultPosition, wxSize(17,21), wxBU_EXACTFIT )
        self.maximizeButton = wxButton(self.panel, self.ID_MAXIMIZE, ">>", \
                                       wxDefaultPosition, wxSize(17,21), wxBU_EXACTFIT )
        self.exitsText = wxButton(self.panel, -1, "Exits", \
                                  wxDefaultPosition, wxSize(20,21), wxBU_EXACTFIT)
        
        self.imageList = wxImageList(32,32)
                
        self.Layout()
        self.__AddEvents()
        self.__SetProperties()

    def __SetProperties(self):
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.minimizeButton.SetToolTipString("Hide Exits")
        self.maximizeButton.SetToolTipString("Show Exits")
        #self.minimizeButton.SetFont(font)
        #self.maximizeButton.SetFont(font)
        self.exitsText.SetBackgroundColour("WHITE")
        self.SetBackgroundColour(self.maximizeButton.GetBackgroundColour())
        self.maximizeButton.Hide()
                
    def __AddEvents(self):
        EVT_BUTTON(self, self.ID_MINIMIZE, self.OnClick) 
        EVT_BUTTON(self, self.ID_MAXIMIZE, self.OnClick) 

    def FixDoorsLayout(self):
        wxLayoutAlgorithm().LayoutWindow(self, self.panel)

    def Layout(self):
        panelSizer = wxBoxSizer(wxHORIZONTAL)
        panelSizer.Add(self.exitsText, wxEXPAND, 0)
        panelSizer.Add(self.minimizeButton, 0)
               
        venueListPanelSizer = wxBoxSizer(wxVERTICAL)
        venueListPanelSizer.Add(panelSizer, 0, wxEXPAND)
        venueListPanelSizer.Add(self.list, 2, wxEXPAND)

        self.panel.SetSizer(venueListPanelSizer)
        venueListPanelSizer.Fit(self.panel)
        self.panel.SetAutoLayout(1)

        wxLayoutAlgorithm().LayoutWindow(self, self.panel)

    def Hide(self):
        currentHeight = self.GetSize().GetHeight()
        self.minimizeButton.Hide()  
        self.maximizeButton.Show()
        self.list.HideDoors()
        self.SetSize(wxSize(25, currentHeight))
        self.parent.UpdateLayout()

    def Show(self):
        currentHeight = self.GetSize().GetHeight()
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
    '''VenueList. 
    
    The venueList is a scrollable window containing all exits to current venue.
    
    '''   
    def __init__(self, parent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1)
        self.doorsAndLabelsList = []
        self.exitsDict = {}
        self.__DoLayout()
        self.parent = parent
        self.EnableScrolling(true, true)
        self.SetScrollRate(1, 1)
                      
    def __DoLayout(self):

        self.box = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.box)
        self.SetAutoLayout(1)
               
    def AddVenueDoor(self, connectionDescription):
        panel = ExitPanel(self, wxNewId(), connectionDescription)
        self.doorsAndLabelsList.append(panel)
        self.doorsAndLabelsList.sort(lambda x, y: cmp(x.GetName(), y.GetName()))
        index = self.doorsAndLabelsList.index(panel)
                      
        self.box.Insert(index, panel, 0, wxEXPAND)

        id = panel.GetButtonId()

        self.exitsDict[id] = connectionDescription
        self.FitInside()
        self.EnableScrolling(true, true)
                            
    def CleanUp(self):
        for item in self.GetChildren():
            self.box.Remove(item)
            item.Destroy()

        self.Layout()
        self.parent.Layout()  

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
        
    def GoToNewVenue(self, event):
        id = event.GetId()

        if(self.exitsDict.has_key(id)):
            description = self.exitsDict[id]
            self.app.EnterVenueCB(description.uri,0)
        else:
            text = "The exit is no longer valid "+name
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
                

class ExitPanel(wxPanel):

    ID_PROPERTIES = wxNewId()
    
    def __init__(self, parent, id, connectionDescription):
        wxPanel.__init__(self, parent, id, wxDefaultPosition, \
                         size = wxSize(400,200), style = wxRAISED_BORDER)
        self.id = id
        self.parent = parent
        self.connectionDescription = connectionDescription
        self.SetBackgroundColour(wxColour(190,190,190))
        self.bitmap = icons.getDefaultDoorClosedBitmap()
        self.bitmapSelect = icons.getDefaultDoorOpenedBitmap()
        self.button = wxStaticBitmap(self, self.id, self.bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
        self.SetToolTipString(connectionDescription.description)
        self.label = wxTextCtrl(self, self.id, "", size= wxSize(0,10),
                                style = wxNO_BORDER|wxTE_MULTILINE|wxTE_RICH)
        self.label.SetValue(connectionDescription.name)
        self.label.SetBackgroundColour(wxColour(190,190,190))
        self.label.SetToolTipString(connectionDescription.description)
        self.button.SetToolTipString(connectionDescription.description)
        self.Layout()
        
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
        self.parent.GoToNewVenue(event)

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
        doorView = ExitPropertiesDialog(self, -1, "Venue Properties", self.connectionDescription)
        doorView.ShowModal()
        doorView.Destroy()
            
    def GetName(self):
        return self.label.GetValue().lower()

    def GetButtonId(self):
        return self.id

    def Layout(self):
        b = wxBoxSizer(wxHORIZONTAL)
        b.Add(self.button, 0, wxALIGN_LEFT|wxTOP|wxBOTTOM|wxRIGHT|wxLEFT, 2)
        b.Add(self.label, 1,  wxALIGN_CENTER|wxTOP|wxBOTTOM|wxRIGHT|wxEXPAND, 2)
        b.Add(5,2)
        self.SetSizer(b)
        b.Fit(self)
        self.SetAutoLayout(1)



###########################################################################################
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
                         wxDefaultSize, style = wxSUNKEN_BORDER)
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
                               wxTR_LINES_AT_ROOT | wxTR_HIDE_ROOT | wxTR_MULTIPLE)
        
        self.__SetImageList()
        self.__SetTree()
               
        EVT_SIZE(self, self.OnSize)
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown)
        EVT_TREE_ITEM_EXPANDING(self.tree, id, self.OnExpand) 
        EVT_TREE_SEL_CHANGED(self.tree, id, self.OnSelect)
       
    def __SetImageList(self):
        imageList = wxImageList(18,18)

        self.bullet = imageList.Add(icons.getBulletBitmap())
        self.participantId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.defaultDataId = imageList.Add(icons.getDefaultDataBitmap())
        self.serviceId = imageList.Add(icons.getDefaultServiceBitmap())
        self.applicationId = imageList.Add(icons.getDefaultServiceBitmap())
        self.nodeId = imageList.Add(icons.getDefaultNodeBitmap())

        self.tree.AssignImageList(imageList)

    def __GetPersonalDataFromItem(self, treeId):
        # Get data for this id
        dataList = []
        cookie = 0
        
        if(self.tree.GetChildrenCount(treeId)>0):
            id, cookie = self.tree.GetFirstChild(treeId, cookie)
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
               
        self.participants = self.tree.AppendItem(self.root, self.PARTICIPANTS_HEADING, index, index)
        self.data = self.tree.AppendItem(self.root, self.DATA_HEADING, index, index) 
        self.services = self.tree.AppendItem(self.root, self.SERVICES_HEADING, index, index)
        self.applications = self.tree.AppendItem(self.root, self.APPLICATIONS_HEADING, index, index)
       
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

        log.debug("ContentListPanel.AddParticipant:: AddParticipant %s (called from %s)", profile.name,
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
            self.parent.statusbar.SetStatusText("%s just removed personal file '%s'"%(ownerProfile.name, dataDescription.name))
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
        self.serviceDict[serviceDescription.name] = service
        self.tree.SortChildren(self.services)
        self.tree.Refresh()
        #self.tree.Expand(self.services)
        
    def RemoveService(self, serviceDescription):
        if(self.serviceDict.has_key(serviceDescription.name)):
            id = self.serviceDict[serviceDescription.name]
            del self.serviceDict[serviceDescription.name]
            if(id != None):
                self.tree.Delete(id)

    def AddApplication(self, appDesc):
        application = self.tree.AppendItem(self.applications, appDesc.name,
                                           self.applicationId,
                                           self.applicationId)
        self.tree.SetItemData(application, wxTreeItemData(appDesc))
        self.applicationDict[appDesc.uri] = application
        self.tree.SortChildren(self.applications)
        #self.tree.Expand(self.applications)
        self.tree.Refresh()
      
    def RemoveApplication(self, appDesc):
        if(self.applicationDict.has_key(appDesc.uri)):
            id = self.applicationDict[appDesc.uri]
            del self.applicationDict[appDesc.uri]
            if(id != None):
                self.tree.Delete(id)

    def UnSelectList(self):
        self.tree.Unselect()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)
        
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
        #if isWindows():
        #    item = event.GetItem()
        #    
        #    # Root item
        #    if self.tree.GetItemText(item) == "":
        #        self.tree.SelectItem(self.participants)
                        
    def OnExpand(self, event):
        treeId = event.GetItem()
        item = self.tree.GetItemData(treeId).GetData()

        if item:
            try:
                dataDescriptionList = self.parent.GetPersonalData(item)
                          
                if dataDescriptionList:
                    for data in dataDescriptionList:
                        self.AddDataCB(data)
            except:
                log.exception("ContentListPanel.OnExpand: Could not get personal data.")
                MessageDialog(None, "%s's data could not be retrieved."%item.name)
                
    def OnDoubleClick(self, event):
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
                openCmd = None
                if isinstance(item, DataDescription):
                    list = item.name.split('.')
                    if len(list) == 2:
                        (name, ext) = list
                    commands = GetMimeCommands(ext = ext)
                    if commands.has_key('Open'):
                        openCmd = commands['Open']
                elif isinstance(item, ServiceDescription):
                    list = item.name.split('.')
                    if len(list) == 2:
                        (name, ext) = list
                    commands = GetMimeCommands(mimeType = item.mimeType,
                                               ext = ext)
                    if commands.has_key('Open'):
                        openCmd = commands['Open']
                else:
                    appdb = Toolkit.GetApplication().GetAppDatabase()
                    openCmd = appdb.GetCommandLine(item.mimeType, 'Open')

                if openCmd == None and \
                       not isinstance(item, ApplicationDescription):
                    self.FindUnregistered(item)
                else:
                    self.parent.StartCmd(openCmd, item, verb='Open')
                    
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
                self.PopupMenu(self.parent.BuildAppMenu(None, "Add "),
                               wxPoint(self.x, self.y))
            elif text == self.PARTICIPANTS_HEADING or item == None:
                # We don't have anything to do with this heading
                pass
            
            elif isinstance(item, ServiceDescription):
                menu = self.BuildServiceMenu(event, item)
                self.PopupMenu(menu, wxPoint(self.x,self.y))

            elif isinstance(item, ApplicationDescription):
                menu = self.BuildAppMenu(event, item)
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
        # This is to flag between using the system OpenShared command
        # and the AG defined one (in case of collision we use the system)
        # useLocal = 0
        
        # Path where temporary file will exist if opened/used.
        a_file = os.path.join(GetTempDir(), item.name)
        ext = item.name.split('.')[-1]

        log.debug("looking for mime commands for extension: %s", ext)
        
        commands = GetMimeCommands(ext = ext)

        log.debug("Commands: %d %s", len(commands), str(commands))
        menu = wxMenu()

        # We always have open
        id = wxNewId()
        menu.Append(id, "Open", "Open this data.")

        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: self.parent.StartCmd(cmd, item=itm, verb='Open'))
        else:
            EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))

        # We always have save for data
        id = wxNewId()
        menu.Append(id, "Save", "Save this item locally.")
        EVT_MENU(self, id, lambda event: self.parent.SaveDataCB(event))
        
        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this data from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveDataCB(event))

        # Do the rest
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             cmd=commands[key], itm=item: self.parent.StartCmd(cmd, item=itm, verb=key))

        menu.AppendSeparator()

        # We always have properties
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
        a_file = os.path.join(GetTempDir(), item.name)
        ext = item.name.split('.')[-1]
        
        commands = GetMimeCommands(mimeType = item.mimeType, ext = ext)

        menu = wxMenu()

        id = wxNewId()
        menu.Append(id, "Open", "Open this data.")

        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: self.parent.StartCmd(cmd, item=itm, verb='Open'))
        else:
            EVT_MENU(self, id, lambda event,
                     itm=item: self.FindUnregistered(itm))

        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this data from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveServiceCB(event))
            
        # Do the rest
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             cmd=commands[key], itm=item: self.parent.StartCmd(cmd, item=itm, verb=key))

        menu.AppendSeparator()

        # We always have properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this data.")
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
                
                # then register the app
                
                # Then execute it
                if isWindows():
                    cmd = program + " %1"
                else:
                    cmd = program + " %s"
                    
                self.parent.StartCmd(cmd, item, verb='Open')
                
    def BuildAppMenu(self, event, item):
        """
        Programmatically build a menu based on the mime based verb
        list passed in.
        """

        commands = self.parent.GetMimeCommandNames(item.mimeType)

        log.info("Got commands: (%s) %s" % (item.mimeType, str(commands)))
        
        menu = wxMenu()
        id = wxNewId()
        menu.Append(id, "Open", "Open application and join the session.")
        # We always have open
            
        if commands != None and 'Open' in commands:
            EVT_MENU(self, id, lambda event, cmd='Open':
                     self.parent.StartCmd(self.parent.controller.GetMimeCommandLine(item.mimeType,'Open'),
                                   item=item, verb='Open'))
      
        else:
            text = "You have nothing configured to open this application."
            title = "Notification"
            EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wxOK|wxICON_INFORMATION))

        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this service.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveApplicationCB(event))

        menu.AppendSeparator()
            
        # Do the rest
        othercmds = 0
        
        if commands != None:
            for key in commands:
                if key != 'Open':
                    othercmds = 1
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event, cmd=key, itm=item:
                             self.parent.StartCmd(appdb.GetCommandLine(item.mimeType,
                                                                cmd),
                                           item=itm, verb=cmd))
        if othercmds:
            menu.AppendSeparator()

        # Add Application Monitor
        id = wxNewId()
        menu.Append(id, "Open Monitor...", "View data and participants present in this application session.")
        EVT_MENU(self, id, lambda event: self.parent.MonitorAppCB(item))

        # Add properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this service.")
        EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def LookAtProperties(self, desc):
        """
        """
              
        if isinstance(desc, DataDescription):
            dataView = DataPropertiesDialog(self, -1, "Data Properties")
            dataView.SetDescription(desc)
            dataView.ShowModal()
            dataView.Destroy()
        elif isinstance(desc, ServiceDescription):
            serviceView = ServicePropertiesDialog(self, -1, "Service Properties")
            serviceView.SetDescription(desc)
            serviceView.ShowModal()
            serviceView.Destroy()
        elif isinstance(desc, ApplicationDescription):
            serviceView = ServicePropertiesDialog(self, -1, "Application Properties")
            serviceView.SetDescription(desc)
            serviceView.ShowModal()
            serviceView.Destroy()
                
    def CleanUp(self):
    
        # Clean up all the entries under the headings
        for heading in (self.participants,self.data,self.services,self.applications):
            cookie = 1
            itemId,cookie = self.tree.GetFirstChild(heading,cookie)
            itemsToDelete = []
            while 1:
                try:
                    self.tree.GetItemData(itemId)
                    itemsToDelete.append(itemId)
                    # get the next item
                    itemId,cookie = self.tree.GetNextChild(heading,cookie)
                except:
                    break
                    
            for item in itemsToDelete:
                self.tree.Delete(item)

        self.participantDict.clear()
        self.dataDict.clear()
        self.serviceDict.clear()
        self.applicationDict.clear()
        self.personalDataDict.clear()

    def SetDropTarget(self,dropTarget):
        self.tree.SetDropTarget(dropTarget)
 
###########################################################################################
#
# Text Client Panel

class TextClientPanel(wxPanel):
    
    ID_BUTTON = wxNewId()

    def __init__(self, parent, id, textOutputCtrl, app):
        wxPanel.__init__(self, parent, id)

        self.parent = parent
        self.textOutput = textOutputCtrl
        self.app = app
        
        self.label = wxStaticText(self, -1, "Your message:")
        self.display = wxButton(self, self.ID_BUTTON, "Display", style = wxBU_EXACTFIT)
        self.textInputId = wxNewId()
        self.textInput = wxTextCtrl(self, self.textInputId, "", size = wxSize(1000, 40),
                                    style= wxTE_MULTILINE)
        self.textInput.SetToolTipString("Write your message here")
        self.__SetProperties()
        self.__DoLayout()

        EVT_TEXT_URL(self, self.textOutput.GetId(), self.OnUrl)
        EVT_CHAR(self.textOutput, self.ChangeTextWindow)
        EVT_CHAR(self.textInput, self.TestEnter) 
        EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
      
        self.Show(true)

    def __SetProperties(self):
        '''
        Sets UI properties.
        '''
        self.SetSize((375, 225))
        
    def __DoLayout(self):
        '''
        Handles UI layout.
        '''
        TextSizer = wxBoxSizer(wxVERTICAL)
        #TextSizer.Add(self.textOutput, 2,
        #              wxEXPAND|wxALIGN_CENTER_HORIZONTAL, 0)
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.label, 0, wxALIGN_CENTER |wxLEFT|wxRIGHT, 5)
        box.Add(self.textInput, 1, wxALIGN_CENTER | wxEXPAND )
        box.Add(self.display, 0, wxALIGN_CENTER |wxLEFT|wxRIGHT, 5)
        
        TextSizer.Add(box, 1, wxEXPAND|wxALIGN_CENTER| wxTOP|wxBOTTOM, 2)
        self.SetAutoLayout(1)
        self.SetSizer(TextSizer)
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

        # Someone is writing a message
        else:
            # Set names bold
            f = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD)
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLACK, font = f))
            self.textOutput.AppendText(name)

            # Set text normal
            f = wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxNORMAL)
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLACK, font = f))
            self.textOutput.AppendText(message+'\n')
            self.textOutput.SetDefaultStyle(wxTextAttr(wxBLACK, font = f))

        if isWindows():
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
               
          
 
###########################################################################################
#
# Dialogs

class SaveFileDialog(wxDialog):
    def __init__(self, parent, id, title, message, doneMessage, fileSize):
        wxDialog.__init__(self, parent, id, title,
                          size = wxSize(300, 200))

        self.doneMessage = doneMessage

        try:
            self.fileSize = int(fileSize)
        except TypeError:
            log.debug("SaveFileDialog.__init__:Received invalid file size: '%s'" % (fileSize))
            fileSize = 1
            
        log.debug("SaveFileDialog.__init__: created, size=%d " %fileSize)
        
        self.button = wxButton(self, wxNewId(), "Cancel")
        self.text = wxStaticText(self, -1, message)

        self.cancelFlag = 0

        self.progress = wxGauge(self, wxNewId(), 100,
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)

        EVT_BUTTON(self, self.button.GetId(), self.OnButton)

        self.transferDone = 0
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.Layout()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 1, wxEXPAND)
        sizer.Add(self.progress, 0, wxEXPAND)
        sizer.Add(self.button, 0, wxCENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    def OnButton(self, event):
        """
        Button press handler.

        If we're still transferring, this is a cancel. Return wxID_CANCEL and
        do an endModal.

        If we're done transferring, this is an OK , so return wxID_OK.
        """
        
        if self.transferDone:
            self.Close()
            pass
        else:
            log.debug("UploadFilesDialog.OnButton: Cancelling transfer!")
            self.Close()
            self.cancelFlag = 1


    def SetMessage(self, value):
        self.text.SetLabel(value)

    def IsCancelled(self):
        return self.cancelFlag

    def SetProgress(self, value, doneFlag):
        #
        # for some reason, the range acts goofy with the actual file
        # sizes. Rescale to 0-100.
        #

        if self.fileSize == 0:
            value = 100
        else:
            value = int(100 * int(value) / self.fileSize)
        self.progress.SetValue(value)
        if doneFlag:
            self.transferDone = 1
            self.button.SetLabel("OK")
            self.SetMessage(self.doneMessage)
        
        return self.cancelFlag

 
###########################################################################################

class UploadFilesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title,
                          size = wxSize(350, 130))

        self.Centre()
        self.button = wxButton(self, wxNewId(), "Cancel")
        self.text = wxStaticText(self, -1, "", size = wxSize(300, 20))

        self.cancelFlag = 0

        self.progress = wxGauge(self, wxNewId(), 100,  size = wxSize(300, 20),
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)

        EVT_BUTTON(self, self.button.GetId(), self.OnButton)

        self.transferDone = 0
        self.currentFile = None
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.Layout()
       
    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(5,5)
        sizer.Add(self.text, 0, wxEXPAND|wxALL, 5)
        sizer.Add(self.progress, 0, wxEXPAND|wxALL, 5)
        sizer.Add(self.button, 0, wxCENTER|wxALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
      
    def OnButton(self, event):
        """
        Button press handler.

        If we're still transferring, this is a cancel. Return wxID_CANCEL and
        do an endModal.

        If we're done transferring, this is an OK , so return wxID_OK.
        """
        
        if self.transferDone:
            self.Close()
            pass
        else:
            log.debug("UploadFilesDialog.OnButton: Cancelling transfer!")
            self.Close()
            self.cancelFlag = 1

    def SetMessage(self, value):
        self.text.SetLabel(value)

    def IsCancelled(self):
        return self.cancelFlag

    def SetProgress(self, filename, bytes_sent, bytes_total, file_done, transfer_done):
        #
        # for some reason, the range acts goofy with the actual file
        # sizes. Rescale to 0-100.
        #

        if transfer_done:
            self.transferDone = transfer_done
            self.progress.SetValue(100)
            self.button.SetLabel("OK")
            self.SetMessage("Transfer complete")
            return 

        if self.currentFile != filename:
            self.SetMessage("Uploading %s" % (filename))
            self.currentFile = filename

        if bytes_total == 0:
            value = 100
        else:
            value = int(100 * int(bytes_sent) / int(bytes_total))
        self.progress.SetValue(value)

 
###########################################################################################
#
# Edit Venues Dialog

class EditMyVenuesDialog(wxDialog):
    ID_DELETE = wxNewId() 
    ID_RENAME = wxNewId()
    listWidth = 500
    listHeight = 200
    currentItem = 0
    ID_LIST = wxNewId()
      
    def __init__(self, parent, id, title, myVenuesDict):
        wxDialog.__init__(self, parent, id, title)
        self.parent = parent 
        self.dictCopy = myVenuesDict.copy()
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        info = "Please, right click on the venue you want to edit and choose from the \noptions available in the menu."
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.myVenuesList= wxListCtrl(self, self.ID_LIST, 
                                       size = wxSize(self.listWidth, self.listHeight), 
                                       style=wxLC_REPORT)
        self.myVenuesList.InsertColumn(0, "Name")
        self.myVenuesList.SetColumnWidth(0, self.listWidth * 1.0/3.0)
        self.myVenuesList.InsertColumn(1, "Url ")
        self.myVenuesList.SetColumnWidth(1, self.listWidth * 2.0/3.0)
        
        self.menu = wxMenu()
        self.menu.Append(self.ID_RENAME,"Rename", "Rename selected venue")
        self.menu.Append(self.ID_DELETE,"Delete", "Delete selected venue")
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.Layout()
        self.__PopulateList()
        self.__SetEvents()
        
    def __SetEvents(self):
        EVT_RIGHT_DOWN(self.myVenuesList, self.OnRightDown)
        EVT_LIST_ITEM_SELECTED(self.myVenuesList, self.ID_LIST, self.OnItemSelected)
        EVT_MENU(self.menu, self.ID_RENAME, self.OnRename)
        EVT_MENU(self.menu, self.ID_DELETE, self.OnDelete)
               
    def __PopulateList(self):
        i = 0
        self.myVenuesList.DeleteAllItems()
        for name in self.dictCopy.keys():
            self.myVenuesList.InsertStringItem(i, name)
            self.myVenuesList.SetStringItem(i, 1, self.dictCopy[name])
            i = i + 1
        
    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 10)
        sizer1.Add(self.myVenuesList, 1, wxALL, 10)

        sizer3 =  wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer3, 0, wxALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    def OnDelete(self, event):
        print "Deleting ",self.currentItem
        if(self.dictCopy.has_key(self.currentItem)):
            del self.dictCopy[self.currentItem]
            self.__PopulateList()
            print " dict copy = ", self.dictCopy
        else:
            text = "Please, select the venue you want to delete"
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)

    def OnRename(self, event):
        if(self.dictCopy.has_key(self.currentItem)):
            renameDialog = RenameDialog(self, -1, "Rename venue")
        else:
            text = "Please, select the venue you want to rename"
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)

    def DoesVenueExist(self, name):
        return self.dictCopy.has_key(name)
                        
    def Rename(self, name):
        if(self.dictCopy.has_key(self.currentItem)):
            self.dictCopy[name] = self.dictCopy[self.currentItem]
            del self.dictCopy[self.currentItem]

            self.myVenuesList.SetItemText(self.currentIndex, name)
        else:
            log.info("EditMyVenuesDialog:Rename: The venue is not present in the dictionary")
               
    def OnItemSelected(self, event):
        self.currentIndex = event.m_itemIndex
        self.currentItem = self.myVenuesList.GetItemText(event.m_itemIndex)
        print "Selected ", self.currentItem
              
    def OnRightDown(self, event):
        self.x = event.GetX() + self.myVenuesList.GetPosition().x
        self.y = event.GetY() + self.myVenuesList.GetPosition().y
        self.PopupMenu(self.menu, wxPoint(self.x, self.y))
        event.Skip()
        
    def GetValue(self):
        print "dict copy = ", self.dictCopy
        return self.dictCopy



class RenameDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.text = wxStaticText(self, -1, "Please, fill in the new name of your venue", style=wxALIGN_LEFT)
        self.nameText = wxStaticText(self, -1, "New Name: ", style=wxALIGN_LEFT)
        self.name = wxTextCtrl(self, -1, "", size = wxSize(300,20), validator = MyVenuesEditValidator())
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
        self.parent = parent
        
        if(self.ShowModal() == wxID_OK):
            parent.Rename(self.name.GetValue())
        self.Destroy()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)

        sizer2 = wxBoxSizer(wxHORIZONTAL)
        sizer2.Add(self.nameText, 0)
        sizer2.Add(self.name, 1, wxEXPAND)

        sizer1.Add(sizer2, 0, wxEXPAND | wxALL, 20)

        sizer3 =  wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(sizer3, 0, wxALIGN_CENTER)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)
        
    def DoesVenueExist(self, name):
        return self.parent.DoesVenueExist(name)
        
    def GetValue(self):
        return self.address.GetValue()
        
        
class MyVenuesEditValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)
            
    def Clone(self):
        return MyVenuesEditValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        venueExists = win.DoesVenueExist(val)

        if venueExists:
            info = "A venue with the same name is already added, please select a different name." 
            dlg = wxMessageDialog(None, info, "Duplicated Venue", style = wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return false

        return true
    
    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.
                
###########################################################################################

class AddMyVenueDialog(wxDialog):
    def __init__(self, parent, id, venueName):
        wxDialog.__init__(self, parent, id, "Add current venue")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        info = "Current venue will be added to your list of venues."
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Name: ", style=wxALIGN_LEFT)
        self.address = wxTextCtrl(self, -1, venueName, size = wxSize(300,20))
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.Layout()
        
    def Layout(self):
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
        
    def GetValue(self):
        return self.address.GetValue()


 
###########################################################################################

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
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.address = wxTextCtrl(self, -1, address, size = wxSize(300,20))
        self.Layout()
        
    def Layout(self):
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
        
    def GetValue(self):
        return self.address.GetValue()

    
 
###########################################################################################

class ProfileDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,20),
                                   validator = TextValidator())
        self.emailText = wxStaticText(self, -1, "Email:", style=wxALIGN_LEFT)
        self.emailCtrl = wxTextCtrl(self, -1, "")
        self.phoneNumberText = wxStaticText(self, -1, "Phone Number:",
                                            style=wxALIGN_LEFT)
        self.phoneNumberCtrl = wxTextCtrl(self, -1, "")
        self.locationText = wxStaticText(self, -1, "Location:")
        self.locationCtrl = wxTextCtrl(self, -1, "")
        self.supportText = wxStaticText(self, -1, "Support Information:",
                                        style=wxALIGN_LEFT)
        self.supportCtrl = wxTextCtrl(self, -1, "")
        self.homeVenue= wxStaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wxTextCtrl(self, -1, "")
        self.profileTypeText = wxStaticText(self, -1, "Profile Type:",
                                            style=wxALIGN_LEFT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.profile = None
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.__DoLayout()
        
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.emailCtrl.SetEditable(false)
            self.phoneNumberCtrl.SetEditable(false)
            self.locationCtrl.SetEditable(false)
            self.supportCtrl.SetEditable(false)
            self.homeVenueCtrl.SetEditable(false)
            self.profileTypeBox.SetEditable(false)
            self.dnTextCtrl.SetEditable(false)
        else:
            self.nameCtrl.SetEditable(true)
            self.emailCtrl.SetEditable(true)
            self.phoneNumberCtrl.SetEditable(true)
            self.locationCtrl.SetEditable(true)
            self.supportCtrl.SetEditable(true)
            self.homeVenueCtrl.SetEditable(true)
            self.profileTypeBox.SetEditable(true)
        log.debug("VenueClientUI.py: Set editable in successfully dialog")
           
    def __DoLayout(self):
        self.sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Profile"), wxHORIZONTAL)
        self.gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        self.gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        self.gridSizer.Add(self.emailText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.emailCtrl, 2, wxEXPAND, 0)
        self.gridSizer.Add(self.phoneNumberText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.phoneNumberCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.locationText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.locationCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.supportText, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.supportCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.homeVenue, 0, wxALIGN_LEFT, 0)
        self.gridSizer.Add(self.homeVenueCtrl, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.profileTypeText, 0, wxALIGN_LEFT, 0)
        #self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        sizer2.Add(self.gridSizer, 1, wxALL, 10)

        self.sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        self.sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)
        self.SetAutoLayout(1)

    def GetNewProfile(self):
        if(self.profile != None):
            self.profile.SetName(self.nameCtrl.GetValue())
            self.profile.SetEmail(self.emailCtrl.GetValue())
            self.profile.SetPhoneNumber(self.phoneNumberCtrl.GetValue())
            self.profile.SetTechSupportInfo(self.supportCtrl.GetValue())
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
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], style = wxCB_DROPDOWN|wxCB_READONLY)
        self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        self.Layout()
        self.nameCtrl.SetValue(self.profile.GetName())
        self.emailCtrl.SetValue(self.profile.GetEmail())
        self.phoneNumberCtrl.SetValue(self.profile.GetPhoneNumber())
        self.locationCtrl.SetValue(self.profile.GetLocation())
        self.supportCtrl.SetValue(self.profile.GetTechSupportInfo())
        self.homeVenueCtrl.SetValue(self.profile.GetHomeVenue())
        if(self.profile.GetProfileType() == 'user'):
            self.profileTypeBox.SetSelection(0)
        else:
            self.profileTypeBox.SetSelection(1)
        self.__SetEditable(true)
        log.debug("ProfileDialog.SetProfile: Set profile information successfully in dialog")

    def SetDescription(self, item):
        log.debug("ProfileDialog.SetDescription: Set description in dialog name:%s, email:%s, phone:%s, location:%s support:%s, home:%s, dn:%s"
                   %(item.name, item.email,item.phoneNumber,item.location,item.techSupportInfo, item.homeVenue, item.distinguishedName))
        self.profileTypeBox = wxTextCtrl(self, -1, item.profileType)
        #self.profileTypeBox.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        self.dnText = wxStaticText(self, -1, "Distinguished name: ")
        self.dnTextCtrl = wxTextCtrl(self, -1, "")
        self.gridSizer.Add(self.dnText, 0, wxEXPAND, 0)
        self.gridSizer.Add(self.dnTextCtrl, 0, wxEXPAND, 0)
        self.sizer1.Fit(self)
        self.Layout()
        
        self.nameCtrl.SetValue(item.name)
        self.emailCtrl.SetValue(item.email)
        self.phoneNumberCtrl.SetValue(item.phoneNumber)
        self.locationCtrl.SetValue(item.location)
        self.supportCtrl.SetValue(item.techSupportInfo)
        self.homeVenueCtrl.SetValue(item.homeVenue)
        self.dnTextCtrl.SetValue(item.distinguishedName)

        if(item.GetProfileType() == 'user'):
            self.profileTypeBox.SetValue('user')
        else:
            self.profileTypeBox.SetValue('node')
            
        self.__SetEditable(false)
        self.cancelButton.Destroy()

class TextValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)
            
    def Clone(self):
        return TextValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        profile = win.GetNewProfile()

        #for view
        if profile == None:
            if val ==  '<Insert Name Here>':
                MessageDialog(NULL, "Please, fill in the name field")
                return false

        #for real profile dialog
        elif len(val) < 1 or profile.IsDefault() or profile.name == '<Insert Name Here>':
            MessageDialog(NULL, "Please, fill in the name field")
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

 
###########################################################################################

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
        self.descriptionCtrl = wxTextCtrl(self, -1, "", style = wxTE_MULTILINE, 
                                          size = wxSize(200, 50), validator = AddAppDialogValidator())

        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")

        self.Layout()

    def Layout(self):
        sizer = wxBoxSizer(wxVERTICAL)

        sizer.Add(self.info, 0, wxEXPAND|wxALL, 10)
        sizer.Add(5,5)
        
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
        
 
###########################################################################################

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
        self.descriptionText = wxStaticText(self, -1, "Description:", style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.descriptionCtrl = wxTextCtrl(self, -1, profile.GetDescription(), size = (500,20))
        self.urlText = wxStaticText(self, -1, "URL:", style=wxALIGN_LEFT)
        self.urlCtrl = wxTextCtrl(self, -1, profile.GetURI(),  size = (500,20))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.__SetProperties()
        self.Layout()
                              
    def __SetProperties(self):
        self.nameCtrl.SetEditable(false)
        self.descriptionCtrl.SetEditable(false)
        self.urlCtrl.SetEditable(false)
                                               
    def Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Properties"), wxHORIZONTAL)
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

 
###########################################################################################

class DataPropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (500,20))
        self.ownerText = wxStaticText(self, -1, "Owner:", style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.ownerCtrl = wxTextCtrl(self, -1, "")
        self.sizeText = wxStaticText(self, -1, "Size:")
        self.sizeCtrl = wxTextCtrl(self, -1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__SetProperties()
        self.Layout()
        
    def __SetProperties(self):
        self.SetTitle("Please, fill in data information")
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))

    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.ownerCtrl.SetEditable(false)
            self.sizeCtrl.SetEditable(false)
                     
        else:
            self.nameCtrl.SetEditable(true)
            self.ownerCtrl.SetEditable(true)
            self.sizeCtrl.SetEditable(true)
                                       
    def Layout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Profile"), wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.ownerText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.ownerCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.sizeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.sizeCtrl, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)

    def SetDescription(self, dataDescription):
        '''
        This method is called if you only want to view the dialog.
        '''
        self.nameCtrl.SetValue(dataDescription.name)
        self.ownerCtrl.SetValue(str(dataDescription.owner))
        self.sizeCtrl.SetValue(str(dataDescription.size))
        self.SetTitle("Data Properties")
        self.__SetEditable(false)
        self.cancelButton.Destroy()
          

###########################################################################################

class ServicePropertiesDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20))
        self.uriText = wxStaticText(self, -1, "Location URL:", style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.uriCtrl = wxTextCtrl(self, -1, "")
        self.typeText = wxStaticText(self, -1, "Mime Type:")
        self.typeCtrl = wxTextCtrl(self, -1, "")
        self.descriptionText = wxStaticText(self, -1, "Description:", style=wxALIGN_LEFT)
        self.descriptionCtrl = wxTextCtrl(self, -1, "", style = wxTE_MULTILINE, size = wxSize(200, 50))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Layout()
    
    def __SetEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.uriCtrl.SetEditable(false)
            self.typeCtrl.SetEditable(false)
            self.descriptionCtrl.SetEditable(false)
          
        else:
            self.nameCtrl.SetEditable(true)
            self.uriCtrl.SetEditable(true)
            self.typeCtrl.SetEditable(true)
            self.descriptionCtrl.SetEditable(true)
                  
    def Layout(self):
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

    def GetValue(self):
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
        self.nameCtrl.SetValue(serviceDescription.name)
        self.uriCtrl.SetValue(serviceDescription.uri)
        self.typeCtrl.SetValue(serviceDescription.mimeType)
        self.descriptionCtrl.SetValue(serviceDescription.description)
        self.__SetEditable(false)
        self.cancelButton.Destroy()
       
 
 
###########################################################################################

class DataDropTarget(wxFileDropTarget):
    def __init__(self, application):
        wxFileDropTarget.__init__(self)
        self.app = application
        self.do = wxFileDataObject()
        self.SetDataObject(self.do)
    
    def OnDropFiles(self, x, y, files):
        self.app.AddDataCB(fileList = files)


if __name__ == "__main__":
    pp = wxPySimpleApp()
    n = AddAppDialog(None, -1, "Start Application Session", ApplicationDescription("test", "test", "test", "test", "test"))
    if n.ShowModal() == wxID_OK:
        print n.GetName()
    
    
    if n:
        n.Destroy()
