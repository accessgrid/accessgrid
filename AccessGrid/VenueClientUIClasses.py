#-----------------------------------------------------------------------------
# Name:        VenueClientUIClasses.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueClientUIClasses.py,v 1.235 2003-08-22 04:24:47 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import os.path
import logging, logging.handlers
import cPickle
import threading
import socket
from wxPython.wx import *
from wxPython.wx import wxFileTypeInfo
import string
import webbrowser
import traceback
import cPickle
import re

log = logging.getLogger("AG.VenueClientUIClasses")

from AccessGrid import icons
from AccessGrid import Toolkit
from AccessGrid.VenueClient import VenueClient, EnterVenueException
from AccessGrid import Utilities
from AccessGrid.UIUtilities import AboutDialog, MessageDialog, ErrorDialog
from AccessGrid.Platform import GetMimeCommands, GetMimeType
from AccessGrid.ClientProfile import *
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.Platform import GetTempDir, GetInstallDir, GetSharedDocDir
from AccessGrid.Platform import isWindows, isLinux, isOSX
from AccessGrid.TextClient import TextClient
from AccessGrid.RoleAuthorization import AddPeopleDialog, RoleClient

try:
    import win32api
except:
    pass

class VenueClientFrame(wxFrame):
    
    '''VenueClientFrame. 

    The VenueClientFrame is the main frame of the application,
    creating statusbar, dock, venueListPanel, and contentListPanel.
    The contentListPanel represents current venue and has information
    about all participants in the venue, it also shows what data and
    services are available in the venue, as well as nodes connected to
    the venue.  It represents a room with its contents visible for the
    user.  The venueListPanel contains a list of connected
    venues/exits to current venue.  By clicking on a door icon the
    user travels to another venue/room, which contents will be shown
    in the contentListPanel.
    '''
    ID_WINDOW_TOP = wxNewId()
    ID_WINDOW_LEFT  = wxNewId()
    ID_WINDOW_BOTTOM = wxNewId()
    ID_VENUE_DATA = wxNewId()
    ID_VENUE_DATA_OPEN = wxNewId() 
    ID_VENUE_DATA_PROPERTIES = wxNewId() 
    ID_VENUE_DATA_ADD = wxNewId()
    ID_VENUE_ADMINISTRATE_VENUE_ROLES = wxNewId()
    ID_VENUE_PERSONAL_DATA_ADD = wxNewId()
    ID_VENUE_DATA_SAVE = wxNewId() 
    ID_VENUE_DATA_DELETE = wxNewId() 
    ID_VENUE_SERVICE = wxNewId() 
    ID_VENUE_SERVICE_ADD = wxNewId()
    ID_VENUE_SERVICE_OPEN = wxNewId()
    ID_VENUE_SERVICE_DELETE = wxNewId()
    ID_VENUE_SERVICE_PROPERTIES = wxNewId() 
    ID_VENUE_APPLICATION = wxNewId() 
    ID_VENUE_APPLICATION_JOIN = wxNewId()
    ID_VENUE_APPLICATION_DELETE = wxNewId()
    ID_VENUE_APPLICATION_PROPERTIES = wxNewId() 
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
    ID_HELP = wxNewId()
    ID_HELP_ABOUT = wxNewId()
    ID_HELP_MANUAL = wxNewId()
    ID_HELP_AGDP = wxNewId()
    ID_HELP_AGORG = wxNewId()
    ID_HELP_FL = wxNewId()
    ID_HELP_FLAG = wxNewId()
    ID_PARTICIPANT_PROFILE = wxNewId()
    ID_PARTICIPANT_FOLLOW = wxNewId()
    ID_PARTICIPANT_LEAD = wxNewId()
    ID_ME_PROFILE = wxNewId()
    ID_ME_DATA = wxNewId()
    ID_ME_UNFOLLOW = wxNewId()
         
    def __init__(self, parent, id, title, app = None):
        wxFrame.__init__(self, parent, id, title)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.Centre()
        self.help_open = 0
        self.textClientPanel = None
        self.textClientStandAlone = None
        self.myVenuesDict = {}
        self.myVenuesMenuIds = []
        self.personToFollow = None
        self.manual_url = os.path.join(GetSharedDocDir(), "VenueClientManual",
                                       "VenueClientManualHTML.htm")
        self.agdp_url = "http://www.accessgrid.org/agdp"
        self.ag_url = "http://www.accessgrid.org/"
        self.flag_url = "http://www.mcs.anl.gov/fl/research/accessgrid"
        self.fl_url = "http://www.mcs.anl.gov/fl/"
        self.app = app
        self.parent = parent
        self.myVenuesFile = os.path.join(self.app.accessGridPath, "myVenues.txt" )
	self.menubar = wxMenuBar()
	self.statusbar = self.CreateStatusBar(1)
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, app, \
                                               self.myVenuesDict, 'default venue')
        self.TextWindow = wxSashLayoutWindow(self, self.ID_WINDOW_BOTTOM, wxDefaultPosition,
                                             wxSize(200, 35))
        self.textClientPanel = TextClientPanel(self.TextWindow, -1, app)
        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT, app)
        self.contentListPanel = ContentListPanel(self, app)
        dataDropTarget = DataDropTarget(self.app)
        self.contentListPanel.tree.SetDropTarget(dataDropTarget)

        self.__setStatusbar()
	self.__setMenubar()
        self.__setProperties()
        self.Layout()
        self.__setEvents()
        self.__loadMyVenues()
            
    def OnSashDrag(self, event):
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
             self.TextWindow.SetDefaultSize(wxSize(1000, height))

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
    
    def OnSize(self, event = None):
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

    def __setStatusbar(self):
        self.statusbar.SetToolTipString("Statusbar")   
    
    def __setMenubar(self):
        self.SetMenuBar(self.menubar)

        # ---- menus for main menu bar
        self.venue = wxMenu()
        self.venue.Append(self.ID_VENUE_DATA_ADD,"Add Data...",
                             "Add data to the venue.")
	self.venue.Append(self.ID_VENUE_SERVICE_ADD,"Add Service...",
                                "Add a service to the venue.")
        self.venue.Append(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES,"Administrate Roles...",
                             "Change venue authorization settings.")
     	self.applicationMenu = wxMenu()
      
        self.venue.AppendMenu(self.ID_VENUE_APPLICATION,"&Applications",
                              self.applicationMenu)
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
            log.exception("VenueClientFrame.__setMenubar: Cannot retrieve certificate mgr user interface, continuing")

        if gui is not None:
            certMenu = gui.GetMenu(self)
            self.preferences.AppendMenu(self.ID_CERTIFICATE_MANAGE,
                                    "&Manage Certificates", certMenu)

        self.preferences.AppendSeparator()

        # Add node-related entries
        self.preferences.AppendRadioItem(self.ID_USE_MULTICAST, "Use multicast",
                                "Use multicast to connect media")
        self.preferences.AppendRadioItem(self.ID_USE_UNICAST, "Use unicast",
                                "Use unicast to connect media")
        self.preferences.AppendSeparator()
        self.preferences.AppendCheckItem(self.ID_ENABLE_VIDEO, "Enable video",
                                "Enable/disable video for your node")
        self.preferences.Check(self.ID_ENABLE_VIDEO,true)
        self.preferences.AppendCheckItem(self.ID_ENABLE_AUDIO, "Enable audio",
                                "Enable/disable audio for your node")
        self.preferences.Check(self.ID_ENABLE_AUDIO,true)
        self.preferences.Append(self.ID_MYNODE_URL, "&Set Node URL...",
                                "Specify URL address to node service")
        self.preferences.Append(self.ID_MYNODE_MANAGE, "&Manage My Node...",
                                "Configure your node")
        self.menubar.Append(self.preferences, "&Preferences")
        self.myVenues = wxMenu()
        self.myVenues.Append(self.ID_MYVENUE_ADD, "Add &Current Venue",
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
        self.help.Append(self.ID_HELP_AGORG, "Access &Grid (ag.org) Web Site",
                         "")
        self.help.Append(self.ID_HELP_FLAG, "Access Grid &Toolkit Web Site",
                         "")
        self.help.Append(self.ID_HELP_FL, "&Futures Laboratory Web Site",
                         "")

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

        self.dataEntryMenu = wxMenu()
        self.dataEntryMenu.Append(self.ID_VENUE_DATA_OPEN,"Open",
                             "Open selected data")
	self.dataEntryMenu.Append(self.ID_VENUE_DATA_SAVE,"Save...",
                             "Save selected data to local disk")
	self.dataEntryMenu.Append(self.ID_VENUE_DATA_DELETE,"Delete", "Remove selected data")
        self.dataEntryMenu.AppendSeparator()
	self.dataEntryMenu.Append(self.ID_VENUE_DATA_PROPERTIES,"Properties...",
                             "View information about the selected data")

        self.personalDataEntryMenu = wxMenu()
        self.personalDataEntryMenu.Append(self.ID_VENUE_PERSONAL_DATA_ADD,"Add personal data...",
                             "Add personal data")
        self.personalDataEntryMenu.AppendSeparator()
        self.personalDataEntryMenu.Append(self.ID_VENUE_DATA_OPEN,"Open",
                             "Open selected data")
	self.personalDataEntryMenu.Append(self.ID_VENUE_DATA_SAVE,"Save...",
                             "Save selected data to local disk")
	self.personalDataEntryMenu.Append(self.ID_VENUE_DATA_DELETE,"Delete", "Remove selected data")
        self.personalDataEntryMenu.AppendSeparator()
	self.personalDataEntryMenu.Append(self.ID_VENUE_DATA_PROPERTIES,"Properties...",
                             "View information about the selected data")

        # ---- Menus for headings
        self.dataHeadingMenu = wxMenu()
        self.dataHeadingMenu.Append(self.ID_VENUE_DATA_ADD,"Add...",
                                   "Add data to the venue")

        self.serviceHeadingMenu = wxMenu()
      	self.serviceHeadingMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...",
                                "Add service to the venue")

        # Do not enable menus until connected
        self.HideMenu()
        
        # until implemented
        self.participantMenu.Enable(self.ID_PARTICIPANT_LEAD, false)

    def HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)

        self.menubar.Enable(self.ID_MYVENUE_ADD, false)
        self.menubar.Enable(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, false)

        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, false)

      	self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, false)
        
    def ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, true)
        self.menubar.Enable(self.ID_MYVENUE_ADD, true)
        # Only show administrate button when you can administrate a venue.
        if self.app.isVenueAdministrator:
            self.menubar.Enable(self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, true)
        
        self.dataHeadingMenu.Enable(self.ID_VENUE_DATA_ADD, true)

      	self.serviceHeadingMenu.Enable(self.ID_VENUE_SERVICE_ADD, true)

    def __setEvents(self):
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.OnSashDrag)
        EVT_SIZE(self, self.OnSize)
                
        EVT_MENU(self, self.ID_VENUE_DATA_OPEN, self.OpenData)
        EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.OpenAddDataDialog)
        EVT_MENU(self, self.ID_VENUE_ADMINISTRATE_VENUE_ROLES, self.OpenModifyVenueRolesDialog)
        EVT_MENU(self, self.ID_VENUE_PERSONAL_DATA_ADD, self.OpenAddPersonalDataDialog)
        EVT_MENU(self, self.ID_VENUE_DATA_SAVE, self.SaveData)
        EVT_MENU(self, self.ID_VENUE_DATA_DELETE, self.RemoveData)
        EVT_MENU(self, self.ID_VENUE_DATA_PROPERTIES, self.OpenDataProfile)
        EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.OpenAddServiceDialog)
        EVT_MENU(self, self.ID_VENUE_SERVICE_OPEN, self.OpenService)
        EVT_MENU(self, self.ID_VENUE_SERVICE_DELETE, self.RemoveService)
        EVT_MENU(self, self.ID_VENUE_SERVICE_PROPERTIES, self.OpenServiceProfile)
        EVT_MENU(self, self.ID_VENUE_CLOSE, self.Exit)
        EVT_MENU(self, self.ID_PROFILE, self.OpenMyProfileDialog)
        EVT_MENU(self, self.ID_USE_MULTICAST, self.UseMulticast)
        EVT_MENU(self, self.ID_USE_UNICAST, self.UseUnicast)
        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.OpenNodeMgmtApp)
        EVT_MENU(self, self.ID_ENABLE_VIDEO, self.EnableVideo)
        EVT_MENU(self, self.ID_ENABLE_AUDIO, self.EnableAudio)
        EVT_MENU(self, self.ID_MYNODE_URL, self.OpenSetNodeUrlDialog)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenues)
        EVT_MENU(self, self.ID_MYVENUE_EDIT, self.EditMyVenues)
        EVT_MENU(self, self.ID_ME_PROFILE, self.OpenMyProfileDialog)
        EVT_MENU(self, self.ID_ME_UNFOLLOW, self.UnFollow)
        EVT_MENU(self, self.ID_ME_DATA, self.OpenAddPersonalDataDialog)
        EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialog)
        EVT_MENU(self, self.ID_HELP_MANUAL,
                 lambda event, url=self.manual_url: self.OpenHelpURL(url))
        EVT_MENU(self, self.ID_HELP_AGDP,
                 lambda event, url=self.agdp_url: self.OpenHelpURL(url))
        EVT_MENU(self, self.ID_HELP_AGORG,
                 lambda event, url=self.ag_url: self.OpenHelpURL(url))
        EVT_MENU(self, self.ID_HELP_FLAG, 
                 lambda event, url=self.flag_url: self.OpenHelpURL(url))
        EVT_MENU(self, self.ID_HELP_FL,
                 lambda event, url=self.fl_url: self.OpenHelpURL(url))
        EVT_MENU(self, self.ID_HELP_MANUAL,
                 lambda event, url=self.manual_url: self.OpenHelpURL(url))

        EVT_MENU(self, self.ID_PARTICIPANT_FOLLOW, self.Follow)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_JOIN, self.OpenApp)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_DELETE, self.RemoveApp)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_PROPERTIES, self.OpenApplicationProfile)

        EVT_CLOSE(self, self.Exit)

    def __setProperties(self):
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.SetTitle("Venue Client")
        self.SetIcon(icons.getAGIconIcon())
        self.statusbar.SetStatusWidths([-1])
        #self.statusbar.SetFont(font)
	#self.menubar.SetFont(font)
        #self.SetFont(font)
	currentHeight = self.venueListPanel.GetSize().GetHeight()
	self.venueListPanel.SetSize(wxSize(180, 300))
        
    def Layout(self):
        self.venueAddressBar.SetDefaultSize(wxSize(1000, 60))
        self.venueAddressBar.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.venueAddressBar.SetAlignment(wxLAYOUT_TOP)

        self.TextWindow.SetDefaultSize(wxSize(1000, 80))
        self.TextWindow.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.TextWindow.SetAlignment(wxLAYOUT_BOTTOM)
        self.TextWindow.SetSashVisible(wxSASH_TOP, TRUE)

        wxLayoutAlgorithm().LayoutWindow(self.TextWindow, self.textClientPanel)

        self.venueListPanel.SetDefaultSize(wxSize(180, 1000))
        self.venueListPanel.SetOrientation(wxLAYOUT_VERTICAL)
        self.venueListPanel.SetSashVisible(wxSASH_RIGHT, TRUE)
        self.venueListPanel.SetAlignment(wxLAYOUT_LEFT)

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

    def OpenHelpURL(self, url):
        """
        """
        needNewWindow = not self.help_open
        
        if needNewWindow:
            self.help_open = 1
            self.browser = webbrowser.get()

        log.debug("VenueClientFrame.OpenHelpURL: Opening: %s", url)
        self.browser.open(url, needNewWindow)

    def UnFollow(self, event):

        log.debug("VenueClientFrame.Unfollow: In UnFollow we are being lead by %s" %self.app.venueClient.leaderProfile.name)
        if self.app.venueClient.leaderProfile != None :
           
            try:
              
                self.app.venueClient.UnFollow(self.app.venueClient.leaderProfile)
                self.meMenu.Remove(self.ID_ME_UNFOLLOW)
            except:
               
                log.exception("VenueClientFrame.Unfollow: Can not stop following %s" %self.app.venueClient.leaderProfile.name)

        else:
            log.debug("VenueClientFrame.Unfollow: You are trying to stop following somebody you are not following")
        
    def Follow(self, event):
        id = self.contentListPanel.tree.GetSelection()
        personToFollow = self.contentListPanel.tree.GetItemData(id).GetData()
        url = personToFollow.venueClientURL
        name = personToFollow.name
        log.debug("VenueClientFrame.Follow: You are trying to follow :%s url:%s " %(name, url))

        if(self.app.venueClient.leaderProfile == personToFollow):
            text = "You are already following "+name
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
            
        elif (self.app.venueClient.pendingLeader == personToFollow):
            text = "You have already sent a request to follow "+name+". Please, wait for answer."
            title = "Notification"
            dlg = wxMessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()  

        else:
            try:
                self.app.venueClient.Follow(personToFollow)
            except:
                log.exception("VenueClientFrame.Follow: Can not follow %s" %personToFollow.name)
                text = "You can not follow "+name
                title = "Notification"
                MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
                
    def __fillTempHelp(self, x):
        if x == '\\':
            x = '/'
        return x

    def FillInAddress(self, event = None, url = None):
        fixedUrlList = []
                   
        if(url == None):
            name = self.menubar.GetLabel(event.GetId())
            fixedUrlList = map(self.__fillTempHelp, self.myVenuesDict[name])

        else:
            fixedUrlList = map(self.__fillTempHelp, url)

        fixedUrl = ""
        for x in fixedUrlList:
            fixedUrl = fixedUrl + x

        # Set url in address bar    
        self.venueAddressBar.SetAddress(fixedUrl)

    def GoToMenuAddress(self, event):
        self.FillInAddress(event)
        self.venueAddressBar.callAddress(event)
                  
#    def CloseTextConnection(self):
#        self.textClientPanel.CloseTextConnection()

#     def SetTextLocation(self, event = None):
#         textLoc = tuple(self.app.venueClient.venueState.GetTextLocation())
#         id = self.app.venueClient.venueState.uniqueId
#         self.textClientPanel.SetLocation(self.app.venueClient.privateId,
#                                          textLoc, id)
      
    def AuthorizeLeadDialog(self, clientProfile):
        idPending = None
        idLeading = None

        if(self.app.venueClient.pendingLeader!=None):
            idPending = self.app.venueClient.pendingLeader.publicId
          

        if(self.app.venueClient.leaderProfile!=None):
            idLeading = self.app.venueClient.leaderProfile.publicId
          
          
        if(clientProfile.publicId != idPending and clientProfile.publicId != idLeading):
            text = "Do you want "+clientProfile.name+" to follow you?"
            title = "Authorize follow"
            dlg = wxMessageDialog(self, text, title, style = wxYES_NO| wxYES_DEFAULT|wxICON_QUESTION)
            if(dlg.ShowModal() == wxID_YES):
                self.app.venueClient.SendLeadResponse(clientProfile, true)

            else:
                self.app.venueClient.SendLeadResponse(clientProfile, false)

            dlg.Destroy()

        else:
            self.app.venueClient.SendLeadResponse(clientProfile, false)

    def NotifyUnLeadDialog(self, clientProfile):
        text = clientProfile.name+" has stopped following you"
        title = "Notification"
        dlg = wxMessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

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

               
    def OpenAddPersonalDataDialog(self, event):
        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #

        log.debug("VenueClientFrame.OpenAddPersonalDataDialog:Trying to upload personal data")
                
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            log.debug("VenueClientFrame.OpenAddPersonalDataDialog:%s " %str(files))

            # upload!
            self.app.UploadPersonalFiles(files)
                                     
        dlg.Destroy()

    

    def OpenDataProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        
        if(data != None and isinstance(data, DataDescription)):
            dataView = DataDialog(self, -1, "Data Properties")
            dataView.SetDescription(data)
            dataView.ShowModal()
            dataView.Destroy()
        else:
            self.__showNoSelectionDialog("Please, select the data yow want to view information about")

    def OpenServiceProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        service = self.contentListPanel.tree.GetItemData(id).GetData()

        if(service != None and isinstance(service, ServiceDescription)):
            serviceView = ServiceDialog(self, -1, "Service Properties")
            serviceView.SetDescription(service)
            serviceView.ShowModal()
            serviceView.Destroy()
        else:
             self.__showNoSelectionDialog("Please, select the service yow want to view information about")

    def OpenApplicationProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        application = self.contentListPanel.tree.GetItemData(id).GetData()

        if(application != None and isinstance(application, ApplicationDescription)):
            # For now, use service dialog since app and service have same properties
            applicationView = ServiceDialog(self, -1, "Application Properties")
            applicationView.SetDescription(application)
            applicationView.ShowModal()
            applicationView.Destroy()
        else:
            self.__showNoSelectionDialog("Please, select the application yow want to view information about") 

    def OpenParticipantProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        participant =  self.contentListPanel.tree.GetItemData(id).GetData()
        
        if(participant != None and isinstance(participant, ClientProfile)):
            profileView = ProfileDialog(self, -1, "Profile")
            log.debug("VenueClientFrame.OpenParticipantProfile: open profile view with this participant: %s" %participant.name)
            profileView.SetDescription(participant)
            profileView.ShowModal()
            profileView.Destroy()
        else:
            self.__showNoSelectionDialog("Please, select the participant yow want to view information about") 
         
    def __loadMyVenues(self, venueURL = None):
        for id in self.myVenuesMenuIds:
            self.myVenues.Delete(id)

        self.myVenuesMenuIds = []
            
        try:
            myVenuesFile = open(self.myVenuesFile, 'r')
        except:
            pass
        
        else:
            self.myVenuesDict = cPickle.load(myVenuesFile)
                        
            for name in self.myVenuesDict.keys():
                id = wxNewId()
                self.myVenuesMenuIds.append(id)
                url = self.myVenuesDict[name]
                text = "Go to: " + url
                self.myVenues.Append(id, name, text)
                EVT_MENU(self, id, self.GoToMenuAddress)
                            
    def EditMyVenues (self, event):
        editMyVenuesDialog = EditMyVenuesDialog(self, -1, "Edit your venues", self.myVenuesDict)
        if (editMyVenuesDialog.ShowModal() == wxID_OK):
            self.myVenuesDict = editMyVenuesDialog.dictCopy
            self.SaveMyVenuesToFile()
            self.__loadMyVenues()

        editMyVenuesDialog.Destroy()

    def SaveMyVenuesToFile(self):
        myVenuesFile = open(self.myVenuesFile, 'w')
        cPickle.dump(self.myVenuesDict, myVenuesFile)
        myVenuesFile.close()

    def AddToMyVenues(self, event):
        id = wxNewId()
        url = self.app.venueClient.venueUri
                      
        if url is not None:
            if(url not in self.myVenuesDict.values()):
                dialog = AddMyVenueDialog(self, -1, "Add current venue",
                                          self.app)
                name = ""
                if (dialog.ShowModal() == wxID_OK):
                    name = dialog.address.GetValue()
                dialog.Destroy()

                text = "Go to: " + url
                self.myVenues.Append(id, name, text)
                self.myVenuesMenuIds.append(id)
                self.myVenuesDict[name] = url
                EVT_MENU(self, id, self.GoToMenuAddress)
            
                self.SaveMyVenuesToFile()
                                               
            else:
                for n in self.myVenuesDict.keys():
                    if self.myVenuesDict[n] == url:
                        name = n
                text = "This venue is already added to your venues as "+"'"+name+"'"
                    
                MessageDialog(self, text, "Add venue")

    def Exit(self, event):
        '''
        Called when the window is closed using the built in close button
        '''
        self.app.OnExit()
                     	      
    def UpdateLayout(self):
        width = self.venueListPanel.GetSize().GetWidth()
        self.venueListPanel.SetDefaultSize(wxSize(width, 1000))
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

                        
    def OpenSetNodeUrlDialog(self, event = None):

        setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                     self.app.venueClient.nodeServiceUri, "Please, specify node service URL")

        if setNodeUrlDialog.ShowModal() == wxID_OK:
            self.app.venueClient.SetNodeUrl(setNodeUrlDialog.address.GetValue())
       
        setNodeUrlDialog.Destroy()

    def OpenAddDataDialog(self, event = None):

        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #

        log.debug("VenueClientFrame.OpenAddDataDialog: Trying to upload to '%s'" % (self.app.venueClient.dataStoreUploadUrl))
        if self.app.venueClient.dataStoreUploadUrl is None or self.app.venueClient.dataStoreUploadUrl == "":
        
            MessageDialog(self,
                          "Cannot add data: Venue does not have an operational\ndata storage server.",
                          "Cannot upload")
            return
        
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            log.debug("VenueClientFrame.OpenAddDataDialog: Got files:%s " %str(files))

            # upload!

            self.app.UploadVenueFiles(files)
                          
        dlg.Destroy()

    def OpenMyProfileDialog(self, event = None):
        profileDialog = ProfileDialog(NULL, -1,
                                  'Please, fill in your profile information')
        profileDialog.SetProfile(self.app.venueClient.profile)
                
        if (profileDialog.ShowModal() == wxID_OK):
            profile = profileDialog.GetNewProfile()
            self.app.ChangeProfile(profile)
            log.debug("VenueClientFrame.OpenMyProfileDialog: change profile: %s" %profile.name)

        profileDialog.Destroy()


    def OpenAddServiceDialog(self, event):
        addServiceDialog = ServiceDialog(self, -1,
                                            'Please, fill in service details')
        if (addServiceDialog.ShowModal() == wxID_OK):
           
            self.app.AddService(addServiceDialog.GetNewProfile())

        addServiceDialog.Destroy()

    def OpenNodeMgmtApp(self, event):
        frame = NodeManagementClientFrame(self, -1, "Access Grid Node Management")
        log.debug("VenueClientFrame.OpenNodeMgmtApp: open node management")
        frame.AttachToNode( self.app.venueClient.nodeServiceUri )
        if frame.Connected(): # Right node service uri
            frame.UpdateUI()
            frame.Show(true)

        else: # Not right node service uri
            setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                         self.app.venueClient.nodeServiceUri, "Please, specify node service URL")
            
            if setNodeUrlDialog.ShowModal() == wxID_OK:
                self.app.venueClient.SetNodeUrl(setNodeUrlDialog.address.GetValue())
                frame.AttachToNode( self.app.venueClient.nodeServiceUri )
                
                if frame.Connected(): # try again
                    frame.Update()
                    frame.Show(true)

                else: # wrong url
                    MessageDialog(self, \
                                  'Can not open node service management\nbased on the URL you specified', \
                                  'Node Management Error')
                
            setNodeUrlDialog.Destroy()


    def EnableVideo(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_VIDEO)
        try:
            self.app.SetVideoEnabled(enableFlag)
        except:
            MessageDialog(self,"Error enabling/disabling video")

    def EnableAudio(self,event):
        enableFlag = self.preferences.IsChecked(self.ID_ENABLE_AUDIO)
        try:
            self.app.SetAudioEnabled(enableFlag)
        except:
            MessageDialog(self,"Error enabling/disabling audio")
                          
    def OpenDataProfileDialog(self, event):
        profileDialog = ProfileDialog(NULL, -1, 'Profile')
        profileDialog.SetProfile(self.app.venueClient.profile)
        profileDialog.ShowModal()
        profileDialog.Destroy()
              
    def OpenAboutDialog(self, event):
        aboutDialog = AboutDialog(None)
        aboutDialog.ShowModal()
        aboutDialog.Destroy()
        
    def SaveData(self, event):
        log.debug("VenueClientFrame.SaveData: Save data")
        id = self.contentListPanel.tree.GetSelection()
        data =  self.contentListPanel.tree.GetItemData(id).GetData()

        
        if(data != None and isinstance(data, DataDescription)):
            name = data.name
            dlg = wxFileDialog(self, "Save file as",
                               defaultFile = name,
                               style = wxSAVE | wxOVERWRITE_PROMPT)
            if dlg.ShowModal() == wxID_OK:
                path = dlg.GetPath()
                log.debug("VenueClientFrame.SaveData: Saving file as %s" %path)

                dlg.Destroy()

                self.app.SaveFile(data, path)
                
            else:
                dlg.Destroy()

        else:
            self.__showNoSelectionDialog("Please, select the data you want to save")

    def OpenData(self, event):
        """
        """
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        if(data != None and isinstance(data, DataDescription)):
            name = data.name
            commands = GetMimeCommands(ext = name.split('.')[-1])
            if commands == None:
                message = ("No client registered for the selected data")
                dlg = MessageDialog(self, message)
                log.debug("VenueClientFrame.OpenData: %s"%message)
            else:
                if commands.has_key('Open'):
                    cmd = commands['Open']
                    self.StartCmd(cmd, data)
        else:
            self.__showNoSelectionDialog("Please, select the data you want to open")     
    
    def RemoveData(self, event):
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        
        ownerId = self.contentListPanel.tree.GetItemParent(id)
        text = self.contentListPanel.tree.GetItemText(ownerId)

        if text != 'Data':
            ownerProfile = self.contentListPanel.tree.GetItemData(ownerId).GetData()
        else:
            # Venue data
            ownerProfile = None
        
        if(data != None and isinstance(data, DataDescription)):
            text ="Are you sure you want to delete "+ data.name
            areYouSureDialog = wxMessageDialog(self, text, 
                                               '', wxOK |
                                               wxCANCEL |wxICON_INFORMATION)
            if(areYouSureDialog.ShowModal() == wxID_OK):
                self.app.RemoveData(data, ownerProfile)
                                    
            areYouSureDialog.Destroy()
                
        else:
            self.__showNoSelectionDialog("Please, select the data you want to delete")

    def RemoveService(self, event):
        id = self.contentListPanel.tree.GetSelection()
        service =  self.contentListPanel.tree.GetItemData(id).GetData()
        
        if(service != None and isinstance(service, ServiceDescription)):
            text ="Are you sure you want to delete "+ service.name
            areYouSureDialog = wxMessageDialog(self, text, \
                                               '', wxOK |  wxCANCEL
                                               |wxICON_INFORMATION)
            if(areYouSureDialog.ShowModal() == wxID_OK):
                self.app.RemoveService(service)
            
        else:
            self.__showNoSelectionDialog("Please, select the service you want to delete")       
            
    def __showNoSelectionDialog(self, text):
        MessageDialog(self, text)

    #
    # Applications Integration code
    #
    def SetInstalledApps(self, applicationList):
        """
        Build the menu of installed applications
        """
        
        # Remove existing menu items
        for item in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Delete(item)

        # Add applications in the appList to the menu
        for app in applicationList:
            menuEntryLabel = "Start " + app.name
            appId = wxNewId()
            self.applicationMenu.Append(appId,menuEntryLabel,menuEntryLabel)
            callback = lambda event,theApp=app: self.StartApp(theApp, event)
            EVT_MENU(self, appId, callback)

    def EnableAppMenu(self, flag):
        for entry in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Enable( entry.GetId(), flag )

    def StartApp(self, app, event=None):
        """
        Start the specified application.  This method creates the application
        in the venue, and then joins it by starting the appropriate client

        **Arguments:**
        
        *app* The ApplicationDescription of the application we want to start
        """
        log.debug("Creating application: %s" % app.name)
        appDesc = self.app.venueClient.client.CreateApplication( app.name,
                                                                 app.description,
                                                                 app.mimeType )
        self.RunApp(appDesc)
        
    def OpenApp(self, event):
        """
        """
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        if data != None and isinstance(data, ApplicationDescription):
            self.RunApp(data)
        else:
            self.__showNoSelectionDialog("Please, select the data you want to open")     
    
    def RunApp(self, appDesc, cmd='Open'):
        appdb = Toolkit.GetApplication().GetAppDatabase()
        
        cmd = appdb.GetCommandLine(appDesc.mimeType, cmd)

        self.contentListPanel.StartCmd(cmd, appDesc)
        
    def OpenService(self,event):
        id = self.contentListPanel.tree.GetSelection()
        service =  self.contentListPanel.tree.GetItemData(id).GetData()

        if(service != None and isinstance(service, ServiceDescription)):
            self.app.OpenService( service )
        else:
            self.__showNoSelectionDialog("Please, select the service you want to open")       
    
    def RemoveApp(self,event):
        id = self.contentListPanel.tree.GetSelection()
        app =  self.contentListPanel.tree.GetItemData(id).GetData()

        if(app != None and isinstance(app, ApplicationDescription)):
            text ="Are you sure you want to delete "+ app.name
            areYouSureDialog = wxMessageDialog(self, text, \
                                               '', wxOK |  wxCANCEL |wxICON_INFORMATION)
            if(areYouSureDialog.ShowModal() == wxID_OK):
                self.app.RemoveApp( app )
        else:
            self.__showNoSelectionDialog("Please, select the application you want to delete")    
            

    #
    # Connectivity menu handling
    #
    def UseMulticast(self,event):
        self.app.SetTransport("multicast")
        self.app.UpdateNodeService()

    def UseUnicast(self,event):

	    # Get a list of providers
        providerList = self.app.venueClient.GetNetworkLocationProviders()
        providerNameLocList = map( lambda provider: provider.name + "/" + provider.location,
                                   providerList )

        # Present the list to the user
        dialog = wxSingleChoiceDialog( self, "Select bridge", 
                                             "Bridge Dialog", 
                                             providerNameLocList )
        ret = dialog.ShowModal()

        if ret == wxID_OK:

            # Get the selected provider
            index = dialog.GetSelection()
            selectedProvider = providerList[index]

            # Set the transport in the venue client and update the node service
            self.app.SetProvider(selectedProvider)
            self.app.SetTransport("unicast")
            self.app.UpdateNodeService()
        else:
            # Set the menu checkbox appropriately
            transport = self.app.GetTransport()
            self.SetTransport(transport)

    def SetUnicastEnabled(self, flag):
        self.preferences.Enable(self.ID_USE_UNICAST, flag)

    def SetTransport(self, transport):
        if transport == "multicast":
            self.preferences.Check(self.ID_USE_MULTICAST, true)
        elif transport == "unicast":  
            self.preferences.Check(self.ID_USE_UNICAST, true)

    def OpenModifyVenueRolesDialog(self,event):
        venueUri = self.app.venueClient.venueUri

        # Open the dialog with selected role in the combo box
        addPeopleDialog = AddPeopleDialog(self, -1, "Modify Roles", venueUri)

        if addPeopleDialog.ShowModal() == wxID_OK:
            # Get new role configuration
            rolesDict = addPeopleDialog.GetInfo()
            # Set new role configuration
            if rolesDict:
                RoleClient(venueUri).SetVenueRoles(rolesDict)

    def CleanUp(self):
        self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

class VenueAddressBar(wxSashLayoutWindow):
    ID_GO = wxNewId()
    ID_BACK = wxNewId()
    ID_ADDRESS = wxNewId()
    
    def __init__(self, parent, id, application, venuesList, defaultVenue):
        wxSashLayoutWindow.__init__(self, parent, id, wxDefaultPosition, \
                                    wxDefaultSize)
        
        self.application = application
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
        self.__addEvents()
        
    def __addEvents(self):
        EVT_BUTTON(self, self.ID_GO, self.callAddress)
        EVT_BUTTON(self, self.ID_BACK, self.GoBack)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.callAddress)
        
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
            
    def GoBack(self, event):
        wxBeginBusyCursor()
        self.application.GoBack()
        wxEndBusyCursor()
      
    def callAddress(self, event = None):
        url = self.address.GetValue()
        venueUri = self.__fixSpaces(url)
        self.AddChoice(venueUri)
        wxBeginBusyCursor()
        self.application.venueClient.EnterVenue(venueUri, true)
        wxEndBusyCursor()

    def __fixSpaces(self, url):
        index = 0
        for c in url:
            if c != ' ':
                break
            index = index + 1

        return url[index:]
                                      
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
    
    ID_MINIMIZE = 10
    ID_MAXIMIZE = 20
      
    def __init__(self, parent,id,  app):
        wxSashLayoutWindow.__init__(self, parent, id)
	self.parent = parent
        self.app = app
        self.panel = wxPanel(self, -1)
	self.list = VenueList(self.panel, self, app)
        self.minimizeButton = wxButton(self.panel, self.ID_MINIMIZE, "<<", \
                                       wxDefaultPosition, wxSize(17,21), wxBU_EXACTFIT )
	self.maximizeButton = wxButton(self.panel, self.ID_MAXIMIZE, ">>", \
                                       wxDefaultPosition, wxSize(17,21), wxBU_EXACTFIT )
        self.exitsText = wxButton(self.panel, -1, "Exits", \
                                  wxDefaultPosition, wxSize(20,21), wxBU_EXACTFIT)
        
        self.imageList = wxImageList(32,32)
                
	self.Layout()
       	self.__addEvents()
        self.__setProperties()

    def __setProperties(self):
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.minimizeButton.SetToolTipString("Hide Exits")
	self.maximizeButton.SetToolTipString("Show Exits")
        #self.minimizeButton.SetFont(font)
        #self.maximizeButton.SetFont(font)
        self.exitsText.SetBackgroundColour("WHITE")
	self.SetBackgroundColour(self.maximizeButton.GetBackgroundColour())
        self.maximizeButton.Hide()
		
    def __addEvents(self):
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
        self.SetSize(wxSize(20, currentHeight))
        self.parent.UpdateLayout()

    def Show(self):
        currentHeight = self.GetSize().GetHeight()
        self.maximizeButton.Hide()
        self.minimizeButton.Show()  
        self.list.ShowDoors()
        self.SetSize(wxSize(180, currentHeight))
        self.parent.UpdateLayout()
        
    def OnClick(self, event):
        if event.GetId() == 10:
            self.Hide()
                                               
	if event.GetId() == 20:
            self.Show()
                                       
    def CleanUp(self):
        self.list.CleanUp()


class VenueList(wxScrolledWindow):
    '''VenueList. 
    
    The venueList is a scrollable window containing all exits to current venue.
    
    '''   
    def __init__(self, parent, grandParent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1)
        self.grandParent = grandParent
        self.doorsAndLabelsList = []
        self.exitsDict = {}
        self.__doLayout()
        self.parent = parent
        self.EnableScrolling(true, true)
        self.SetScrollRate(1, 1)
                      
    def __doLayout(self):

        self.box = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.box)
        self.SetAutoLayout(1)
               
    def GoToNewVenue(self, event):
        id = event.GetId()

        if(self.exitsDict.has_key(id)):
            description = self.exitsDict[id]
            wxBeginBusyCursor()
            self.app.venueClient.EnterVenue(description.uri, false)
            wxEndBusyCursor()
        else:
            text = "The exit is no longer valid "+name
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
                
    def AddVenueDoor(self, profile):
        panel = ExitPanel(self, wxNewId(), profile)
        self.doorsAndLabelsList.append(panel)
        self.doorsAndLabelsList.sort(lambda x, y: cmp(x.GetName(), y.GetName()))
        index = self.doorsAndLabelsList.index(panel)
                      
        self.box.Insert(index, panel, 0, wxEXPAND)

        id = panel.GetButtonId()

        self.exitsDict[id] = profile
        self.FitInside()
        self.EnableScrolling(true, true)
                            
    def RemoveVenueDoor(self):
        pass
    
    def CleanUp(self):
        for item in self.doorsAndLabelsList:
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

         
class ExitPanel(wxPanel):

    ID_PROPERTIES = wxNewId()
    
    def __init__(self, parent, id, profile):
        wxPanel.__init__(self, parent, id, wxDefaultPosition, \
			 size = wxSize(400,200), style = wxRAISED_BORDER)
        self.id = id
        self.parent = parent
        self.profile = profile
        self.SetBackgroundColour(wxColour(190,190,190))
        self.bitmap = icons.getDefaultDoorClosedBitmap()
        self.bitmapSelect = icons.getDefaultDoorOpenedBitmap()
        self.button = wxStaticBitmap(self, self.id, self.bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
        self.SetToolTipString(profile.description)
        self.label = wxTextCtrl(self, self.id, "", size= wxSize(0,10),
                                style = wxNO_BORDER|wxTE_MULTILINE|wxTE_RICH)
        self.label.SetValue(profile.name)
        self.label.SetBackgroundColour(wxColour(190,190,190))
        self.label.SetToolTipString(profile.description)
        self.button.SetToolTipString(profile.description)
        self.Layout()
        
        EVT_LEFT_DOWN(self.button, self.onClick) 
        EVT_LEFT_DOWN(self.label, self.onClick)
        EVT_LEFT_DOWN(self, self.onClick)
        EVT_RIGHT_DOWN(self.button, self.onRightClick) 
        EVT_RIGHT_DOWN(self.label, self.onRightClick)
        EVT_RIGHT_DOWN(self, self.onRightClick)
        
        EVT_ENTER_WINDOW(self, self.onMouseEnter)
        EVT_LEAVE_WINDOW(self, self.onMouseLeave)
            
    def onMouseEnter(self, event):
        '''
        Sets a new door image when mouse enters the panel
        '''
        self.button.SetBitmap(self.bitmapSelect)
        
    def onMouseLeave(self, event):
        '''
        Sets a new door image when mouse leaves the panel
        '''
        self.button.SetBitmap(self.bitmap)
               
    def onClick(self, event):
        '''
        Move client to a new venue
        '''
        self.parent.GoToNewVenue(event)

    def onRightClick(self, event):
        '''
        Opens a menu for this connected venue
        '''
        self.x = event.GetX() + self.GetPosition().x
        self.y = event.GetY() + self.GetPosition().y
        
        propertiesMenu = wxMenu()
     	propertiesMenu.Append(self.ID_PROPERTIES,"Properties...",
                             "View information about the venue")
      
       
        self.PopupMenu(propertiesMenu, wxPoint(self.x, self.y))
        EVT_MENU(self, self.ID_PROPERTIES, self.OpenProfileDialog)
                
    def OpenProfileDialog(self, event):
        '''
        Opens a profile dialog for this exit
        '''
        doorView = ExitProfileDialog(self, -1, "Venue Properties", self.profile)
        doorView.ShowModal()
        doorView.Destroy()
            
    def GetName(self):
        return self.label.GetValue().lower()

    def GetButtonId(self):
        return self.id

    #def AdjustText(self):
    #    t = ''
    #    self.label.SetValue(t)

    #    line1 = self.label.GetLineText(0)
    #    text = line1

    #    if(t != line1):
    #        line2 = self.label.GetLineText(1)
    #        text  = text+line2

    #    self.label.SetValue(text)
                
    def Layout(self):
        b = wxBoxSizer(wxHORIZONTAL)
        b.Add(self.button, 0, wxALIGN_LEFT|wxTOP|wxBOTTOM|wxRIGHT|wxLEFT, 2)
        b.Add(self.label, 1,  wxALIGN_CENTER|wxTOP|wxBOTTOM|wxRIGHT|wxEXPAND, 2)
        b.Add(5,2)
        self.SetSizer(b)
        b.Fit(self)
        self.SetAutoLayout(1)
                       
class ContentListPanel(wxPanel):                   
    '''ContentListPanel.
    
    The contentListPanel represents current venue and has information
    about all participants in the venue, it also shows what data and
    services are available in the venue, as well as nodes connected to
    the venue.  It represents a room, with its contents visible for
    the user.
    
    '''
   
    
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, 
			 wxDefaultSize)
        id = wxNewId()
        self.participantDict = {}
        self.dataDict = {}
        self.serviceDict = {}
        self.applicationDict = {}
        self.personalDataDict = {}
        self.temporaryDataDict = {}
        self.parent = parent
	self.app = app

        if isWindows():
            self.tree = wxTreeCtrl(self, id, wxDefaultPosition, 
                                   wxDefaultSize, style = wxTR_HAS_BUTTONS |
                                   wxTR_NO_LINES)
            
            
        elif isLinux() or isOSX():
            self.tree = wxTreeCtrl(self, id, wxDefaultPosition, 
                                   wxDefaultSize, style = wxTR_HAS_BUTTONS |
                                   wxTR_NO_LINES | wxTR_HIDE_ROOT)

        self.__setImageList()
	self.__setTree()
       	self.__setProperties()

        EVT_SIZE(self, self.OnSize)
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_LEFT_DCLICK(self.tree, self.OnDoubleClick)
        EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown)
        EVT_TREE_ITEM_EXPANDING(self.tree, id, self.OnExpand) 
       
    def __setImageList(self):
        imageList = wxImageList(18,18)

        self.bullet = imageList.Add(icons.getBulletBitmap())
        self.participantId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.defaultDataId = imageList.Add(icons.getDefaultDataBitmap())
	self.serviceId = imageList.Add(icons.getDefaultServiceBitmap())
        self.applicationId = imageList.Add(icons.getDefaultServiceBitmap())
        self.nodeId = imageList.Add(icons.getDefaultNodeBitmap())

        self.tree.AssignImageList(imageList)
                   
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
                          
    def RemoveParticipant(self, description):
        log.debug("ContentListPanel.RemoveParticipant: Remove participant")
        if description!=None :
            if(self.participantDict.has_key(description.publicId)):
                log.debug("ContentListPanel.RemoveParticipant: Found participant in tree")
                id = self.participantDict[description.publicId]

                log.debug("ContentListPanel.RemoveParticipant: Remove participants data")
                self.RemoveParticipantData(id)
                
                if id!=None:
                    log.debug("ContentListPanel.RemoveParticipant: Removed participant from tree")
                    self.tree.Delete(id)

                log.debug("ContentListPanel.RemoveParticipant: Delete participant from dictionary")
                del self.participantDict[description.publicId]
                          
    def ModifyParticipant(self, description):
        log.debug('ContentListPanel.ModifyParticipant: Modify participant')
        if self.participantDict.has_key(description.publicId):
            id = self.participantDict[description.publicId]
            personalData = self.__GetPersonalDataFromItem(id)
       
        self.RemoveParticipant(description)
        self.AddParticipant(description, personalData)

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
            
    def AddData(self, profile):
        log.debug("ContentListPanel.AddData: profile.type = %s" %profile.type)

        #if venue data
        if(profile.type == 'None' or profile.type == None):
            log.debug("ContentListPanel.AddData: This is venue data")
            dataId = self.tree.AppendItem(self.data, profile.name,
                                      self.defaultDataId, self.defaultDataId)
            self.tree.SetItemData(dataId, wxTreeItemData(profile)) 
            self.dataDict[profile.id] = dataId
            self.tree.SortChildren(self.data)
            self.tree.Expand(self.data)
            
        #if personal data
        else:
            log.debug("ContentListPanel.AddData: This is personal data")
            id = profile.type
                        
            if(self.participantDict.has_key(id)):
                log.debug("ContentListPanel.AddData: Data belongs to a participant")
                participantId = self.participantDict[id]
              
                if participantId:
                    ownerProfile = self.tree.GetItemData(participantId).GetData()
                    #
                    # Test if personal data is already added
                    #
                                        
                    if not self.personalDataDict.has_key(profile.id):
                        # Remove the temporary text "No personal data available"
                        if self.temporaryDataDict.has_key(id):
                            tempText = self.temporaryDataDict[id]
                            if tempText:
                                self.tree.Delete(tempText)
                                del self.temporaryDataDict[id]
                                                                        
                        dataId = self.tree.AppendItem(participantId, profile.name, \
                                                      self.defaultDataId, self.defaultDataId)
                        self.tree.SetItemData(dataId, wxTreeItemData(profile))
                        self.personalDataDict[profile.id] = dataId
                        self.tree.SortChildren(participantId)
                      
                        #
                        # I select the participant to ensure the twist button is
                        # visible when first data item is added. I have to do
                        # this due to a bug in wxPython.
                        #              
                        if(self.tree.GetSelection() == participantId):
                            self.tree.Unselect()
                            
                        self.tree.SelectItem(participantId)
                                                    
            else:
                log.info("ContentListPanel.AddData: Owner of data does not exist")

       
    def UpdateData(self, profile):
        id = None

        #if venue data
        if(self.dataDict.has_key(profile.id)):
            log.debug("ContentListPanel.UpdateData: DataDict has data")
            id = self.dataDict[profile.id]
            
        #if personal data
        elif (self.personalDataDict.has_key(profile.id)):
            log.debug("ContentListPanel.UpdateData: Personal DataDict has data")
            id = self.personalDataDict[profile.id]
            
        if(id != None):
            self.tree.SetItemData(id, wxTreeItemData(profile))
        else:
            log.info("ContentListPanel.UpdateData: Id is none - that is not good")
                          
    def RemoveData(self, profile):
        #if venue data
        id = None
        ownerId = None
        
        if(self.dataDict.has_key(profile.id)):
            log.debug("ContentListPanel.RemoveData: Remove venue data")
            id = self.dataDict[profile.id]
            del self.dataDict[profile.id]
            
        #if personal data
               
        elif (self.personalDataDict.has_key(profile.id)):
            id = self.personalDataDict[profile.id]
            ownerId = self.tree.GetItemParent(id)
            ownerProfile = self.tree.GetItemData(ownerId).GetData()
            self.parent.statusbar.SetStatusText("%s just removed personal file '%s'"%(ownerProfile.name, profile.name))
            log.debug("ContentListPanel.RemoveData: Remove personal data")
            id = self.personalDataDict[profile.id]
            del self.personalDataDict[profile.id]

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
                          
    def AddService(self, profile):
        service = self.tree.AppendItem(self.services, profile.name,
                                      self.serviceId, self.serviceId)

 
        self.tree.SetItemData(service, wxTreeItemData(profile)) 
        self.serviceDict[profile.name] = service
        self.tree.SortChildren(self.services)
        self.tree.Expand(self.services)
        
    def RemoveService(self, profile):
        if(self.serviceDict.has_key(profile.name)):
            id = self.serviceDict[profile.name]
            del self.serviceDict[profile.name]
            if(id != None):
                self.tree.Delete(id)

    def AddApplication(self, appDesc):
        application = self.tree.AppendItem(self.applications, appDesc.name,
                                           self.applicationId,
                                           self.applicationId)
        self.tree.SetItemData(application, wxTreeItemData(appDesc))
        self.applicationDict[appDesc.uri] = application
        self.tree.SortChildren(self.applications)
        self.tree.Expand(self.applications)
      
    def RemoveApplication(self, appDesc):
        if(self.applicationDict.has_key(appDesc.uri)):
            id = self.applicationDict[appDesc.uri]
            del self.applicationDict[appDesc.uri]
            if(id != None):
                self.tree.Delete(id)

    def __setTree(self):
       

        index = self.bullet
        index2 = -1

        #
        # Temporary fix for wxPython bug
        # If I don't have a root item on windows, twist buttons
        # will not show up properly, so I have to add an empty root.
        # Default image index, -1, for empty image will, on windows,
        # display the first image in the image list, setting it
        # to -2 instead results in correct behaviour.
        #
        if sys.platform == "win32":
            index2 = -2
        
        self.root = self.tree.AddRoot("", index2, index2)
        
	self.participants = self.tree.AppendItem(self.root, "Participants", index, index)
        self.data = self.tree.AppendItem(self.root, "Data", index, index) 
        self.services = self.tree.AppendItem(self.root, "Services", index, index)
        self.applications = self.tree.AppendItem(self.root, "Applications", index, index)

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
        self.tree.Expand(self.data)
        self.tree.Expand(self.services)
                
        if sys.platform == "win32":
            self.tree.Expand(self.root)
        
    def __setProperties(self):
        pass
      
    def UnSelectList(self):
        self.tree.Unselect()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)
	
    def OnKeyDown(self, event):
        key = event.GetKeyCode()
      
        if key == WXK_DELETE:
            treeId = self.tree.GetSelection()
            item = self.tree.GetItemData(treeId).GetData()

            if item:
                if isinstance(item,DataDescription):
                    # data
                    self.parent.RemoveData(event)
                elif isinstance(item,ServiceDescription):
                    # service
                    self.parent.RemoveService(event)
                elif isinstance(item,ApplicationDescription):
                    # application
                    self.parent.RemoveApp(event)

    def OnExpand(self, event):
        treeId = event.GetItem()
        item = self.tree.GetItemData(treeId).GetData()

        if item:
            try:
                dataDescriptionList = self.app.venueClient.GetPersonalData(item)
                if dataDescriptionList:
                    for data in dataDescriptionList:
                        self.AddData(data)
                       
            except:
                ErrorDialog(None, "%s's data could not be retrieved."%item.name ,
                            style = wxOK  | wxICON_ERROR)
                
    def OnDoubleClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
       
        if(treeId.IsOk() and flag & wxTREE_HITTEST_ONITEMLABEL):
            item = self.tree.GetItemData(treeId).GetData()
            text = self.tree.GetItemText(treeId)
            if item == None:
                pass

            elif isinstance(item,ClientProfile):
                if item.publicId == self.app.venueClient.profile.publicId:
                    self.parent.OpenMyProfileDialog(None)
                else:
                    self.parent.OpenParticipantProfile(None)

            else:
                openCmd = None
                if isinstance(item, DataDescription) or isinstance(item, ServiceDescription):
                    ext = item.name.split('.')[-1]
                    commands = GetMimeCommands(mimeType = item.mimeType,
                                               ext = ext)
                    openCmd = commands['Open']
                else:
                    appdb = Toolkit.GetApplication().GetAppDatabase()
                    openCmd = appdb.GetCommandLine(item.mimeType, 'Open')
                
                self.StartCmd(openCmd, item)
               
    def OnRightClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()

        treeId, flag = self.tree.HitTest(wxPoint(self.x,self.y))
      
        if(treeId.IsOk()):
            self.tree.SelectItem(treeId)
            item = self.tree.GetItemData(treeId).GetData()
            text = self.tree.GetItemText(treeId)
                        
            if text == 'Data':
                self.PopupMenu(self.parent.dataHeadingMenu,
                               wxPoint(self.x, self.y))
            elif text == 'Services':
                self.PopupMenu(self.parent.serviceHeadingMenu,
                               wxPoint(self.x, self.y))
            elif text == 'Applications':
                self.PopupMenu(self.parent.applicationMenu,
                               wxPoint(self.x, self.y))
            elif text == 'Participants' or item == None:
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
                          % (item.publicId, self.app.venueClient.profile.publicId))
                if(item.publicId == self.app.venueClient.profile.publicId):
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
        
        commands = GetMimeCommands(ext = ext)

        menu = wxMenu()

        # We always have open
        id = wxNewId()
        menu.Append(id, "Open", "Open this data.")

        if commands != None and commands.has_key('Open'):
            EVT_MENU(self, id, lambda event,
                     cmd=commands['Open'], itm=item: self.StartCmd(cmd, item=itm))
        else:
            text = "You have nothing configured to open this data."
            title = "Notification"
            EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wxOK|wxICON_INFORMATION))
#            EVT_MENU(self, id, lambda event, item=item:

        # We always have save for data
        id = wxNewId()
        menu.Append(id, "Save", "Save this item locally.")
        EVT_MENU(self, id, lambda event: self.parent.SaveData(event))
        
        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this data from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveData(event))
            
        # Do the rest
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             cmd=commands[key], itm=item: self.StartCmd(cmd, item=itm))
#                elif key == 'OpenShared':
#                    useLocal = 1

#         appdb = Toolkit.GetApplication().GetAppDatabase()
#         mimeType = GetMimeType(ext)
#         mt2 = appdb.GetMimeType(extension = ext)
#         print "MIMETYPE: <%s> <%s>" % (mimeType, mt2)
#         cmdLine = appdb.GetCommandLine(mimeType, 'OpenShared')
#         print "MTL: ", appdb.ListMimeTypes()
#         print "CMDLINE: %s" % cmdLine

#         if not useLocal:
#             id = wxNewId()
#             menu.Append(id, string.capwords('Open Shared'))
#             EVT_MENU(self, id, lambda event,
#                      cmd=cmdLine, itm=item: self.StartCmd(cmd, item=item,
#                                                           name='OpenShared'))

        menu.AppendSeparator()

        # We always have properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this data.")
        EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu

    def BuildServiceMenu(self, event, item):
        """
        Programmatically build a menu based on the mime based verb
        list passed in.
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
                     cmd=commands['Open'], itm=item: self.StartCmd(cmd, item=itm))
        else:
            text = "You have nothing configured to open this data."
            title = "Notification"
            EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wxOK|wxICON_INFORMATION))
#            EVT_MENU(self, id, lambda event, item=item:

        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this data from the venue.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveService(event))
            
        # Do the rest
        if commands != None:
            for key in commands.keys():
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event,
                             cmd=commands[key], itm=item: self.StartCmd(cmd, item=itm))

        menu.AppendSeparator()

        # We always have properties
        id = wxNewId()
        menu.Append(id, "Properties", "View the details of this data.")
        EVT_MENU(self, id, lambda event, item=item:
                 self.LookAtProperties(item))

        return menu
    def BuildAppMenu(self, event, item):
        """
        Programmatically build a menu based on the mime based verb
        list passed in.
        """

        appdb = Toolkit.GetApplication().GetAppDatabase()
        commands = appdb.GetCommandNames(mimeType = item.mimeType)

        log.info("Got commands: (%s) %s" % (item.mimeType, str(commands)))
        
        menu = wxMenu()

        # We always have open
        id = wxNewId()
        menu.Append(id, "Open", "Open this service.")
        if commands != None and 'Open' in commands:
            EVT_MENU(self, id, lambda event, cmd='Open':
                     self.StartCmd(appdb.GetCommandLine(item.mimeType,
                                                        'Open'),
                                   item=item))
        else:
            text = "You have nothing configured to open this service."
            title = "Notification"
            EVT_MENU(self, id, lambda event, text=text, title=title:
                     MessageDialog(self, text, title,
                                   style = wxOK|wxICON_INFORMATION))
#            EVT_MENU(self, id, lambda event, item=item:
#                     self.MakeAssociation(event, item))

        # We always have Remove
        id = wxNewId()
        menu.Append(id, "Delete", "Delete this service.")
        EVT_MENU(self, id, lambda event: self.parent.RemoveApp(event))
            
        # Do the rest
        if commands != None:
            for key in commands:
                if key != 'Open':
                    id = wxNewId()
                    menu.Append(id, string.capwords(key))
                    EVT_MENU(self, id, lambda event, cmd=key:
                             self.StartCmd(cmd))

        menu.AppendSeparator()

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
            dataView = DataDialog(self, -1, "Data Properties")
            dataView.SetDescription(desc)
            dataView.ShowModal()
            dataView.Destroy()
        elif isinstance(desc, ServiceDescription):
            serviceView = ServiceDialog(self, -1, "Service Properties")
            serviceView.SetDescription(desc)
            serviceView.ShowModal()
            serviceView.Destroy()
        elif isinstance(desc, ApplicationDescription):
            serviceView = ServiceDialog(self, -1, "Application Properties")
            serviceView.SetDescription(desc)
            serviceView.ShowModal()
            serviceView.Destroy()
                
    def StartCmd(self, command, item=None, namedVars=None):
        """
        """
        localFilePath = None
        mimeType = None
        if namedVars == None:
            namedVars = dict()

        # If item is passed in, download the filename specified in it.
        if item != None and isinstance(item, DataDescription):
            ext = item.name.split('.')[-1]
            appdb = Toolkit.GetApplication().GetAppDatabase()
            mimeType = appdb.GetMimeType(extension = ext)
            if mimeType == None:
                mimeType == Platform.GetMimeType(extension = ext)
                
            localFilePath = os.path.join(GetTempDir(), item.name)
            self.app.SaveFileNoProgress(item, localFilePath)

            # Fix odd commands
            if command.find("%1") != -1:
                command = command.replace("%1", "%(localFilePath)s")
            elif command.find("%(localFilePath)s") == -1:
                command += " \"%(localFilePath)s\""
        else:
            if command.find("%1") != -1:
                command = command.replace("%1", "%(appUrl)s")
            elif command.find("%(appUrl)s") == -1:
                command += " \"%(appUrl)s\""
            mimeType = item.mimeType
            
        namedVars['appName'] = item.name
        namedVars['appDesc'] = item.description
        namedVars['appMimeType'] = mimeType
        namedVars['venueDataUrl'] = item.uri
        namedVars['localFilePath'] = localFilePath
        namedVars['appUrl'] = item.uri

        # Gross KLUDGE for open shared
#         if name == 'OpenShared':
#             appName = appdb.GetNameForMimeType(mimeType)
#             appDesc = self.app.venueClient.client.CreateApplication(
#                 appName, None, mimeType )
#             namedVars['appUrl'] = appDesc.uri
#         else:
#             namedVars['appUrl'] = item.uri

        # We're doing some icky munging to make our lives easier
        # We're only doing this for a single occurance of a windows
        # environment variable
        prog = re.compile("\%[a-zA-Z0-9\_]*\%")
        result = prog.match(command)

        print "CMD: <%s>" % command

        if result != None:
            subStr = result.group()

            realCommand = command.replace(subStr,
                                          "DORKYREPLACEMENT") % namedVars
            realCommand = realCommand.replace("DORKYREPLACEMENT", subStr)
            if isWindows():
                shell = os.environ['ComSpec']
                realCommand = "%s %s %s" % (shell, "/c", realCommand)
        else:
            realCommand = command % namedVars
            
        self.app.venueClient.processManager.start_process(realCommand, [])
        
    def CleanUp(self):
        for index in self.participantDict.values():
            self.tree.Delete(index)

        for index in self.serviceDict.values():
            self.tree.Delete(index)
        
        for index in self.dataDict.values():
            self.tree.Delete(index)

        for index in self.applicationDict.values():
            self.tree.Delete(index)

        self.participantDict.clear()
        self.dataDict.clear()
        self.serviceDict.clear()
        self.applicationDict.clear()
        self.personalDataDict.clear()
 
class TextClientPanel(wxPanel):
    aboutText = """PyText 1.0 -- a simple text client in wxPython and pyGlobus.
    This has been developed as part of the Access Grid project."""
    bufferSize = 128
    venueId = None
    location = None
    Processor = None
    ID_BUTTON = wxNewId()
    textMessage = ''

    def __init__(self, parent, id, application):
        wxPanel.__init__(self, parent, id)
        self.textOutputId = wxNewId()
        self.app = application
        self.TextOutput = wxTextCtrl(self, self.textOutputId, "",
                                     style= wxTE_MULTILINE|wxTE_READONLY)
        self.label = wxStaticText(self, -1, "Your message:")
        self.display = wxButton(self, self.ID_BUTTON, "Display", style = wxBU_EXACTFIT)
        self.textInputId = wxNewId()
        self.TextInput = wxTextCtrl(self, self.textInputId, "",
                                    style= wxTE_PROCESS_ENTER)
        self.TextInput.SetToolTipString("Write your message here")
        self.__set_properties()
        self.__do_layout()

        EVT_CHAR(self.TextOutput, self.ChangeTextWindow)
        EVT_TEXT_ENTER(self, self.textInputId, self.LocalInput)
        EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
        self.Show(true)

    def ChangeTextWindow(self, event):
        '''Changes focus from text output field to text input field
        to make it clear for users where to write messages.'''
       
        key = event.GetKeyCode()
        self.TextInput.SetFocus()
        
        if(44 < key < 255):
            self.TextInput.AppendText(chr(key)) 
                                    
    def ClearTextWidgets(self):
        """
        """
        self.TextOutput.Clear()
        self.TextInput.Clear()

    def OutputText(self, message):
        wxCallAfter( self.TextOutput.AppendText, message)

    def __set_properties(self):
        self.SetSize((375, 225))
        
    def __do_layout(self):
        TextSizer = wxBoxSizer(wxVERTICAL)
        TextSizer.Add(self.TextOutput, 2,
                      wxEXPAND|wxALIGN_CENTER_HORIZONTAL, 0)
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.label, 0, wxALIGN_CENTER |wxLEFT|wxRIGHT, 5)
        box.Add(self.TextInput, 1, wxALIGN_CENTER )
        box.Add(self.display, 0, wxALIGN_CENTER |wxLEFT|wxRIGHT, 5)
        
        TextSizer.Add(box, 0, wxEXPAND|wxALIGN_CENTER| wxTOP|wxBOTTOM, 2)
        self.SetAutoLayout(1)
        self.SetSizer(TextSizer)
        self.Layout()
        
    def LocalInput(self, event):
        """ User input """
        log.debug("TextClientPanel.LocalInput: User writes: %s"
                  % self.TextInput.GetValue())

        text = self.TextInput.GetValue()
        try:
            self.app.venueClient.textClient.Input(text)
            self.TextInput.Clear()
        except:
            text = "Could not send text message successfully"
            title = "Notification"
            log.exception("TextClientPanel.LocalInput: %s" %text)
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
        
    def OnCloseWindow(self):
        log.debug("TextClientPanel.LocalInput:: Destroy text client")
        self.textClient.Stop()
        self.Destroy()
          
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
            self.EndModal(wxID_OK)
        else:
            log.debug("SaveFileDialog.OnButton: Cancelling transfer!")
            self.EndModal(wxID_CANCEL)
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
            self.EndModal(wxID_OK)
        else:
            log.debug("UploadFilesDialog.OnButton: Cancelling transfer!")
            self.EndModal(wxID_CANCEL)
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

class EditMyVenuesDialog(wxDialog):
    ID_DELETE = wxNewId() 
    ID_RENAME = wxNewId()
    listWidth = 500
    listHeight = 200
    currentItem = 0
    ID_LIST = wxNewId()
      
    def __init__(self, parent, id, title, myVenuesDict):
        wxDialog.__init__(self, parent, id, title)
        self.dict = myVenuesDict
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
        self.__populateList()
        self.__setEvents()
        
    def OnDelete(self, event):
        if(self.dictCopy.has_key(self.currentItem)):
            del self.dictCopy[self.currentItem]
            self.__populateList()
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
              
    def OnRightDown(self, event):
        self.x = event.GetX() + self.myVenuesList.GetPosition().x
        self.y = event.GetY() + self.myVenuesList.GetPosition().y
        self.PopupMenu(self.menu, wxPoint(self.x, self.y))
        event.Skip()

    def __setEvents(self):
        EVT_RIGHT_DOWN(self.myVenuesList, self.OnRightDown)
        EVT_LIST_ITEM_SELECTED(self.myVenuesList, self.ID_LIST, self.OnItemSelected)
        EVT_MENU(self.menu, self.ID_RENAME, self.OnRename)
        EVT_MENU(self.menu, self.ID_DELETE, self.OnDelete)
               
    def __populateList(self):
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


class RenameDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.text = wxStaticText(self, -1, "Please, fill in the new name of your venue", style=wxALIGN_LEFT)
        self.nameText = wxStaticText(self, -1, "New Name: ", style=wxALIGN_LEFT)
        self.name = wxTextCtrl(self, -1, "", size = wxSize(300,20))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        self.Layout()
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
        
        
class AddMyVenueDialog(wxDialog):
    def __init__(self, parent, id, title, app = None):
        wxDialog.__init__(self, parent, id, title)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.Centre()
        info = "Current venue will be added to your list of venues."
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Name: ", style=wxALIGN_LEFT)
        name = app.venueClient.venueState.name
        self.address = wxTextCtrl(self, -1, name, size = wxSize(300,20))
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
        self.__doLayout()
        
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
        self.__setEditable(true)
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
            
        self.__setEditable(false)
        self.cancelButton.Destroy()
       
    def __setEditable(self, editable):
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
        log.debug("VenueClientUIClasses.py: Set editable in successfully dialog")
           
    def __doLayout(self):
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

class ServiceDialog(wxDialog):
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
        self.descriptionCtrl = wxTextCtrl(self, -1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__setProperties()
        self.Layout()
    
    def GetNewProfile(self):
        service = ServiceDescription("service", "service", "uri",
                                     "storagetype")
        service.SetName(self.nameCtrl.GetValue())
        service.SetDescription(self.descriptionCtrl.GetValue())
        service.SetURI(self.uriCtrl.GetValue())
        service.SetMimeType(self.typeCtrl.GetValue())
        return service

    def SetDescription(self, serviceDescription):
        '''
        This method is called if you on want to view the dialog.
        '''
        self.nameCtrl.SetValue(serviceDescription.name)
        self.uriCtrl.SetValue(serviceDescription.uri)
        self.typeCtrl.SetValue(serviceDescription.mimeType)
        self.descriptionCtrl.SetValue(serviceDescription.description)
        self.SetTitle("Service Properties")
        self.__setEditable(false)
        self.cancelButton.Destroy()
          
    def __setProperties(self):
        self.SetTitle("Please, fill in service information")
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))

    def __setEditable(self, editable):
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

class ExitProfileDialog(wxDialog):
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
        self.__setProperties()
        self.Layout()
                              
    def __setProperties(self):
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

class DataDialog(wxDialog):
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
        self.__setProperties()
        self.Layout()
        
    def SetDescription(self, dataDescription):
        '''
        This method is called if you only want to view the dialog.
        '''
        self.nameCtrl.SetValue(dataDescription.name)
        self.ownerCtrl.SetValue(str(dataDescription.owner))
        self.sizeCtrl.SetValue(str(dataDescription.size))
        self.SetTitle("Data Properties")
        self.__setEditable(false)
        self.cancelButton.Destroy()
          
    def __setProperties(self):
        self.SetTitle("Please, fill in data information")
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))

    def __setEditable(self, editable):
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


class DataDropTarget(wxFileDropTarget):
    def __init__(self, application):
        wxFileDropTarget.__init__(self)
        self.app = application
        self.do = wxFileDataObject()
        self.SetDataObject(self.do)
    
    def OnDropFiles(self, x, y, files):
        if self.app.venueClient.dataStoreUploadUrl is None or self.app.venueClient.dataStoreUploadUrl == "":
            MessageDialog(NULL,
                          "Cannot add data: Venue does not have an operational\ndata storage server.",
                          "Cannot upload")
            return

        else:
            self.app.UploadVenueFiles(files)
 
class SelectAppDialog(wxDialog):
    """
    SelectAppDialog provides the option for selecting an executable
    for operations on a particular mimetype, and for storing this 
    association permanently.
    """
    def __init__(self, parent, id, title, mimetype ):

        wxDialog.__init__(self, parent, id, title,
                          style = wxRESIZE_BORDER|wxDEFAULT_DIALOG_STYLE)

        # Set up sizers
        gridSizer = wxFlexGridSizer(5, 1, 5, 5)
        gridSizer.AddGrowableCol(0)
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer1.Add(gridSizer, 1, wxALL|wxEXPAND, 10)
        self.SetSizer( sizer1 )
        self.SetAutoLayout(1)

        # Create config list label and listctrl
        gridSizer.Add( wxStaticText(self,-1,
                                    "No client registered for item:\n\t"
                                    + mimetype), 1 )
        gridSizer.Add( wxStaticText(self,-1,
                                    "Select an application to use with this mimetype"), 1 )

        # Create application text field and button
        fieldButtonSizer = wxBoxSizer(wxHORIZONTAL)
        self.fileText = wxTextCtrl(self,-1,"")
        buttonId = wxNewId()
        button = wxButton(self,buttonId,"Browse...")
        EVT_BUTTON(self, buttonId, self.BrowseCallback)

        fieldButtonSizer.Add( self.fileText, 1 )
        fieldButtonSizer.Add( button )
        gridSizer.Add( fieldButtonSizer, 1, wxEXPAND )

        # Create default checkbox
        self.defaultCheckbox = wxCheckBox(self,-1,
                                          "Always use this application")
        gridSizer.Add( self.defaultCheckbox, 1, wxEXPAND )

    
        # Create ok/cancel buttons
        sizer3 = wxBoxSizer(wxHORIZONTAL)
        okButton = wxButton( self, wxID_OK, "OK" )
        cancelButton = wxButton( self, wxID_CANCEL, "Cancel" )
        sizer3.Add(okButton, 0, wxALL, 10)
        sizer3.Add(cancelButton, 0, wxALL, 10)
        sizer1.Add(sizer3, 0, wxALIGN_RIGHT)

        sizer1.Fit(self)

        self.SetSize( wxSize(350,200) )

    def GetPath(self):
        """
        Return path to selected file
        """
        return self.fileText.GetValue()

    def GetCheckboxValue(self):
        """
        Return state of checkbox
        """
        return self.defaultCheckbox.GetValue()

    def BrowseCallback(self, event):
        """
        Handle file selection
        """

        d = wxFileDialog(self, "Select application")
        ret = d.ShowModal()

        if ret == wxID_OK:
            file = d.GetPath()
            self.fileText.SetValue( file )


'''VenueClient.

The VenueClient class creates the main frame of the application, the
VenueClientFrame.

'''

def VerifyExecutionEnvironment():
    """
    Verify that the current execution environment is sufficient
    for running the VV software.
    """

    #
    # Test for GLOBUS_LOCATION
    #

    if not os.environ.has_key("GLOBUS_LOCATION"):
        log.critical("VerifyExecutionEnvironment: The GLOBUS_LOCATION environment must be set, check your Globus installation")
        dlg = wxMessageDialog(None, "The GLOBUS_LOCATION environment variable is not set.\n" + 
                              "Check your Globus installation.",
                              "Globus configuration problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()
        sys.exit(1)

    #
    # Test for valid local hostname.
    #
        
    myhost = Utilities.GetHostname()
    log.debug("VerifyExecutionEnvironment: My hostname is %s", myhost)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((myhost, 0))
        log.debug("VerifyExecutionEnvironment: bind to local hostname of %s succeeds", myhost)
    except socket.error:
        log.critical("VerifyExecutionEnvironment: bind to local hostname of %s fails", myhost)
        log.critical("VerifyExecutionEnvironment: This may be due to the hostname being set to something different than the name to which the IP address of this computer maps, or to the the hostname not being fully qualified with the full domain.")
        #
        # Test to see if the environment variable GLOBUS_HOSTNAME has a different
        # value than the registry. If that is the case, then teh user
        # has manually done something in a cmd window. This is unlikely in
        # general use, but developers may run into it.
        #

        global_reg = None
        user_reg = None

        from AccessGrid.Platform import WIN
        if sys.platform == WIN:
            from Platform import FindRegistryEnvironmentVariable
            (global_reg, user_reg) = FindRegistryEnvironmentVariable("GLOBUS_HOSTNAME")

        msg = None
        msgbase = "If you started this program from a command window you may\n" + \
                 "have to start a new command window to run with the proper settings.)"
                 
        if os.environ.has_key("GLOBUS_HOSTNAME"):
            if global_reg is None and user_reg is None:
                msg = "(GLOBUS_HOSTNAME is not configured in the registry, but\n" + \
                      "is set in the process environment.\n" + msgbase

        else:
            if global_reg is not None or user_reg is not None:
                msg = "(GLOBUS_HOSTNAME is configured in the registry, but\n" + \
                      "is not set in the process environment.\n" + msgbase

        ShowNetworkInit(msg)
        sys.exit(1)

    #
    # Test for ability to find the service manager and node service programs.
    #

    svcMgr = os.path.join(GetInstallDir(), "AGServiceManager.py")

    if not os.access(svcMgr, os.R_OK):
        log.critical("VerifyExecutionEnvironment: AGServiceManager.py not found")
        dlg = wxMessageDialog(None, "The application was unable to determine the location of\n" +
                              "its AGServiceManager component. If you installed using a Windows\n" +
                              "installer, this is due to a bug in the installer. If you are running\n" +
                              "from a CVS checkout, check the value of the AGTK_INSTALL environment variable.",
                              "Application configuration problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()
        
        sys.exit(1)
    
    

def ShowNetworkInit(msg = None):
    if sys.platform == "win32":
        ShowNetworkInitWin32(msg)
    else:
        ShowNetworkInitNonWin32(msg)

def ShowNetworkInitNonWin32(msg):
        dlg = wxMessageDialog(None,
                              "This computer's network configuration is not correct.\n" +
                              "Correct the problem (by setting the GLOBUS_HOSTNAME environment" +
                              "variable) and restart the app. Appliation will exit.",
                              "Globus network problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()

def ShowNetworkInitWin32(msg):
    if msg is  None:
        msg = ""
    else:
        msg = "\n" + msg
        
    networkInit = os.path.join(os.environ['GLOBUS_LOCATION'], "config", "network_init.py")
    if (os.access(networkInit, os.R_OK)):
        dlg = wxMessageDialog(None,
                              "This computer's network configuration is not correct.\n" \
                              "We will invoke the network configuration tool, and the \n" \
                              "Venues client will then exit. Complete the configuration and\n" \
                              "restart the Venues client." +  msg,
                              "Globus network problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()

        import win32api
        shortpath = win32api.GetShortPathName(networkInit)
        win32api.WinExec("python %s" % (shortpath))
    else:

        dlg = wxMessageDialog(None,
                              "This computer's network configuration is not correct.\n" + 
                              "Correct the problem (by setting the GLOBUS_HOSTNAME environment\n" + 
                              "variable) and restart the app. Appliation will exit." + msg,
                              "Globus network problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == "__main__":
   
    import time
    
    class TheGrid(wxApp):
        def OnInit(self, venueClient = None):
            self.frame = VenueClientFrame(NULL, -1,"The Lobby")
            self.frame.Show(true)
            self.frame.SetSize(wxSize(300, 400))
            self.SetTopWindow(self.frame)
            self.client = venueClient
