#-----------------------------------------------------------------------------
# Name:        VenueClientUIClasses.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueClientUIClasses.py,v 1.165 2003-05-05 20:17:46 lefvert Exp $
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

log = logging.getLogger("AG.VenueClientUIClasses")

from AccessGrid import icons
from AccessGrid.VenueClient import VenueClient, EnterVenueException
from AccessGrid import Utilities
from AccessGrid.UIUtilities import AboutDialog, MessageDialog, GetMimeCommands
from AccessGrid.ClientProfile import *
from AccessGrid.Descriptions import DataDescription, ServiceDescription
from AccessGrid.Descriptions import ApplicationDescription
from AccessGrid.Utilities import formatExceptionInfo
from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame
from AccessGrid.UIUtilities import MyLog 
from AccessGrid.Platform import GetTempDir, GetInstallDir
from AccessGrid.TextClient import SimpleTextProcessor
from AccessGrid.TextClient import TextClientConnectException
from pyGlobus.io import GSITCPSocket
from AccessGrid.hosting.pyGlobus.Utilities import CreateTCPAttrAlwaysAuth, GetHostname
from AccessGrid.Events import ConnectEvent, TextEvent, DisconnectEvent

try:
    import win32api
except:
    pass
try:
    from AccessGrid import CertificateManager
    CertificateManager.CertificateManagerWXGUI
    HaveCertificateManager = 0
except Exception, e:
    HaveCertificateManager = 0

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
    ID_MYNODE_MANAGE = wxNewId()
    ID_MYNODE_URL = wxNewId()
    ID_MYVENUE_ADD = wxNewId()
    ID_MYVENUE_EDIT = wxNewId()
    ID_HELP = wxNewId()
    ID_HELP_ABOUT = wxNewId()
    ID_PARTICIPANT_PROFILE = wxNewId()
    ID_PARTICIPANT_FOLLOW = wxNewId()
    ID_PARTICIPANT_LEAD = wxNewId()
    ID_NODE_PROFILE = wxNewId()
    ID_NODE_FOLLOW = wxNewId()
    ID_NODE_LEAD = wxNewId()
    ID_NODE_MANAGE = wxNewId()
    ID_ME_PROFILE = wxNewId()
    ID_ME_DATA = wxNewId()
    ID_ME_UNFOLLOW = wxNewId()

    textClientPanel = None
    textClientStandAlone = None
    myVenuesDict = {}
    myVenuesMenuIds = []
    personToFollow = None
         
    def __init__(self, parent, id, title, app = None):
        wxFrame.__init__(self, parent, id, title)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        self.Centre()
	self.app = app
        self.parent = parent
        self.myVenuesFile = os.path.join(self.app.accessGridPath, "myVenues.txt" )
	self.menubar = wxMenuBar()
	self.statusbar = self.CreateStatusBar(1)
        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, app, \
                                               self.myVenuesDict, 'default venue')
        self.TextWindow = wxSashLayoutWindow(self, self.ID_WINDOW_BOTTOM, wxDefaultPosition,
                                             wxSize(200, 35))
        self.textClientPanel = TextClientPanel(self.TextWindow, -1)
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

        self.venue = wxMenu()
	self.dataMenu = wxMenu()
        self.dataMenu.Append(self.ID_VENUE_DATA_ADD,"Add data to venue...",
                             "Add data to the venue")
        self.dataMenu.Append(self.ID_VENUE_PERSONAL_DATA_ADD,"Add personal data...",
                             "Add personal data")
        self.dataMenu.AppendSeparator()
        self.dataMenu.Append(self.ID_VENUE_DATA_OPEN,"Open",
                             "Open selected data")
	self.dataMenu.Append(self.ID_VENUE_DATA_SAVE,"Save...",
                             "Save selected data to local disk")
	self.dataMenu.Append(self.ID_VENUE_DATA_DELETE,"Delete", "Remove selected data")
        self.dataMenu.AppendSeparator()
	self.dataMenu.Append(self.ID_VENUE_DATA_PROPERTIES,"Properties...",
                             "View information about the selected data")
        self.venue.AppendMenu(self.ID_VENUE_DATA,"&Data", self.dataMenu)
	self.serviceMenu = wxMenu()
	self.serviceMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...",
                                "Add service to the venue")
        self.serviceMenu.Append(self.ID_VENUE_SERVICE_OPEN,
                                     "Open",  "Launch service client")
        self.serviceMenu.Append(self.ID_VENUE_SERVICE_DELETE,"Delete",
                                "Remove selected service")
        self.serviceMenu.AppendSeparator()
        self.serviceMenu.Append(self.ID_VENUE_SERVICE_PROPERTIES,"Properties...",
                                     "View information about the selected service")
        
        self.venue.AppendMenu(self.ID_VENUE_SERVICE,"&Services",
                              self.serviceMenu)

     	self.applicationMenu = wxMenu()
      
        self.venue.AppendMenu(self.ID_VENUE_APPLICATION,"&Applications",
                              self.applicationMenu)
        
     

        # --- I'll use this later, for now, same menu opens for both heading and item selection.

        # Create menu to pop over an application entry
        self.applicationEntryMenu = wxMenu()
        self.applicationEntryMenu.Append(self.ID_VENUE_APPLICATION_JOIN,"Join",
                                    "Join application")
        self.applicationEntryMenu.Append(self.ID_VENUE_APPLICATION_DELETE, "Delete",
                                    "Delete application")
        self.applicationEntryMenu.AppendSeparator()
        self.applicationEntryMenu.Append(self.ID_VENUE_APPLICATION_PROPERTIES,"Properties...",
                              "View information about the selected application")

        # Create menu to pop over an service entry
        #self.serviceEntryMenu = wxMenu()
	#self.serviceEntryMenu.Append(self.ID_VENUE_SERVICE_OPEN,
        #                            "Open",  "Launch service client")


	self.menubar.Append(self.venue, "&Venue")
        
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE,"&Exit\tCTRL-q", "Exit venue")
	
	self.edit = wxMenu()
	self.edit.Append(self.ID_PROFILE,"&Profile...\tCTRL-p", "Change your personal information")
        self.menubar.Append(self.edit, "&Edit")
        self.myNode = wxMenu()
        self.myNode.Append(self.ID_MYNODE_MANAGE, "&Manage...\tCTRL-m", "Configure your node")
        self.myNode.Append(self.ID_MYNODE_URL, "&Set URL...\tCTRL-u", "Specify URL address to node service")
        self.menubar.Append(self.myNode, "My &Node")
        self.myVenues = wxMenu()
        self.myVenues.Append(self.ID_MYVENUE_ADD, "Add &Current Venue...\tCTRL-t", "Add this venue to your list of venues")
        self.myVenues.Append(self.ID_MYVENUE_EDIT, "Edit My &Venues...\tCTRL-e", "Edit your venues")
        self.myVenues.AppendSeparator()
        self.menubar.Append(self.myVenues, "My Ven&ues")

        if HaveCertificateManager:
            # certMenu = wxMenu()
            # certMenu.Append(self.ID_CERT_TRUSTED, "View &Trusted CA Certificates...")
            # certMenu.Append(self.ID_CERT_IDENTITY, "View &Identity Certificates...")
            certMenu = self.app.certificateManagerGUI.GetMenu(self)
            self.menubar.Append(certMenu, "&Certificates")
              
      	self.help = wxMenu()
        self.help.Append(self.ID_HELP_ABOUT, "&About\tCTRL-a", "Information about the application")
        self.menubar.Append(self.help, "&Help")
        self.HideMenu()

        self.meMenu = wxMenu()
        self.meMenu.Append(self.ID_ME_DATA,"Add personal data...",\
                                           "Add data you can bring to other venues")
        self.meMenu.AppendSeparator()
        self.meMenu.Append(self.ID_ME_PROFILE,"View Profile...",\
                                           "View participant's profile information")
            
        self.participantMenu = wxMenu()
	self.participantMenu.Append(self.ID_PARTICIPANT_PROFILE,"View Profile...",\
                                           "View participant's profile information")
        self.participantMenu.AppendSeparator()
        self.participantMenu.Append(self.ID_PARTICIPANT_FOLLOW,"Follow",\
                                           "Follow this person")
        self.participantMenu.Append(self.ID_PARTICIPANT_LEAD,"Lead",\
                                           "Lead this person")

        self.nodeMenu = wxMenu()
        self.nodeMenu.Append(self.ID_NODE_PROFILE,"View Profile...",\
                             "View node's profile information")
        self.nodeMenu.Append(self.ID_NODE_MANAGE,"Manage...",\
                                           "Manage this node")
        self.nodeMenu.AppendSeparator()

        self.nodeMenu.Append(self.ID_NODE_FOLLOW,"Follow",\
                                           "Follow this node")
        self.nodeMenu.Append(self.ID_NODE_LEAD,"Lead",\
                                           "Lead this node")

        #self.nodeMenu.Enable(self.ID_NODE_LEAD, false)
        #self.nodeMenu.Enable(self.ID_NODE_MANAGE, false)
        #self.participantMenu.Enable(self.ID_PARTICIPANT_LEAD, false)

    def HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_PERSONAL_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_DATA_SAVE, false)
        self.menubar.Enable(self.ID_VENUE_DATA_OPEN, false)
        self.menubar.Enable(self.ID_VENUE_DATA_DELETE, false)
        self.menubar.Enable(self.ID_VENUE_DATA_PROPERTIES, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_DELETE, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_OPEN, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_PROPERTIES, false)
        self.menubar.Enable(self.ID_MYVENUE_ADD, false)

        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_JOIN, false)
        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_DELETE, false)
        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_PROPERTIES, false)
                 
    def ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_PERSONAL_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_DATA_SAVE, true)
        self.menubar.Enable(self.ID_VENUE_DATA_OPEN, true)
        self.menubar.Enable(self.ID_VENUE_DATA_DELETE, true)
        self.menubar.Enable(self.ID_VENUE_DATA_PROPERTIES, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_DELETE, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_OPEN, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_PROPERTIES, true)
        self.menubar.Enable(self.ID_MYVENUE_ADD, true)

        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_JOIN, true)
        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_DELETE, true)
        self.applicationEntryMenu.Enable(self.ID_VENUE_APPLICATION_PROPERTIES, true)
         
    def __setEvents(self):
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.OnSashDrag)
        EVT_SIZE(self, self.OnSize)
                
        EVT_MENU(self, self.ID_VENUE_DATA_OPEN, self.OpenData)
        EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.OpenAddDataDialog)
        EVT_MENU(self, self.ID_VENUE_PERSONAL_DATA_ADD, self.OpenAddPersonalDataDialog)
        EVT_MENU(self, self.ID_VENUE_DATA_SAVE, self.SaveData)
        EVT_MENU(self, self.ID_VENUE_DATA_DELETE, self.RemoveData)
        EVT_MENU(self, self.ID_VENUE_DATA_PROPERTIES, self.OpenDataProfile)
        EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.OpenAddServiceDialog)
        EVT_MENU(self, self.ID_VENUE_SERVICE_OPEN, self.OpenService)
        EVT_MENU(self, self.ID_VENUE_SERVICE_DELETE, self.RemoveService)
        EVT_MENU(self, self.ID_VENUE_SERVICE_PROPERTIES, self.OpenServiceProfile)
        EVT_MENU(self, self.ID_VENUE_CLOSE, self.Exit)
        EVT_MENU(self, self.ID_PROFILE, self.OpenProfileDialog)
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialog)
        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.OpenNodeMgmtApp)
        EVT_MENU(self, self.ID_MYNODE_URL, self.OpenSetNodeUrlDialog)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenues)
        EVT_MENU(self, self.ID_MYVENUE_EDIT, self.EditMyVenues)
        EVT_MENU(self, self.ID_ME_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_ME_UNFOLLOW, self.UnFollow)
        EVT_MENU(self, self.ID_ME_DATA, self.OpenAddPersonalDataDialog)
        EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_NODE_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_PARTICIPANT_FOLLOW, self.Follow)
        EVT_MENU(self, self.ID_NODE_FOLLOW, self.Follow)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_JOIN, self.JoinApp)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_DELETE, self.RemoveApp)
        EVT_MENU(self, self.ID_VENUE_APPLICATION_PROPERTIES, self.OpenApplicationProfile)

        EVT_CLOSE(self, self.Exit)

    def __setProperties(self):
        font = wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana")
        self.SetTitle("You are not in a venue")
        self.SetIcon(icons.getAGIconIcon())
        self.statusbar.SetStatusWidths([-1])
        #self.statusbar.SetFont(font)
	#self.menubar.SetFont(font)
        #self.SetFont(font)
	currentHeight = self.venueListPanel.GetSize().GetHeight()
	self.venueListPanel.SetSize(wxSize(180, 300))
        
    def Layout(self):
        self.venueAddressBar.SetDefaultSize(wxSize(1000, 35))
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
        
    def UnFollow(self, event):
        wxLogDebug("VenueClientUIClasses: In UnFollow we are being lead by %s" %self.app.leaderProfile.name)
        if self.app.leaderProfile != None :
            try:
                self.app.UnFollow(self.app.leaderProfile)
                self.meMenu.Remove(self.ID_ME_UNFOLLOW)
            except:
                wxLogError("VenueClientUIClasses: Can not stop following %s" %self.app.leaderProfile.name)

        else:
            wxLogDebug("You are trying to stop following somebody you are not following")
        
    def Follow(self, event):
        wxLogDebug("VenueClientUIClasses: In Follow")
        id = self.contentListPanel.tree.GetSelection()
        personToFollow = self.contentListPanel.tree.GetItemData(id).GetData()
        url = personToFollow.venueClientURL
        name = personToFollow.name
        wxLogDebug("VenueClientUIClasses: You are trying to follow :%s url:%s " %(name, url))

        if(self.app.leaderProfile == personToFollow):
            text = "You are already following "+name
            title = "Notification"
            MessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
            
        elif (self.app.pendingLeader == personToFollow):
            text = "You have already sent a request to follow "+name+". Please, wait for answer."
            title = "Notification"
            dlg = wxMessageDialog(self, text, title, style = wxOK|wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()  

        else:
            try:
                self.app.Follow(personToFollow)
            except:
                wxLogError("VenueClientUIClasses: Can not follow %s" %personToFollow.name)
                wxLog_GetActiveTarget().Flush()

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
        self.venueAddressBar.SetAddress(fixedUrl)

    def SetTextLocation(self, event = None):
        textLoc = tuple(self.app.venueState.GetTextLocation())
        id = self.app.venueState.uniqueId
        self.textClientPanel.SetLocation(self.app.privateId, textLoc, id)

        # I don't know why this is in a try/except block and the previous
        # line isn't.
        try:
            self.textClientStandAlone.SetLocation(self.app.privateId,
                                                  textLoc, id)
        except:
            pass

    def AuthorizeLeadDialog(self, clientProfile):
        idPending = None
        idLeading = None

        if(self.app.pendingLeader!=None):
            idPending = self.app.pendingLeader.publicId

        if(self.app.leaderProfile!=None):
            idLeading = self.app.leaderProfile.publicId
               
        if(clientProfile.publicId != idPending and clientProfile.publicId != idLeading):
            text = "Do you want "+clientProfile.name+" to follow you?"
            title = "Authorize follow"
            dlg = wxMessageDialog(self, text, title, style = wxYES_NO| wxYES_DEFAULT|wxICON_QUESTION)
            if(dlg.ShowModal() == wxID_YES):
                self.app.SendLeadResponse(clientProfile, true)

            else:
                self.app.SendLeadResponse(clientProfile, false)

            dlg.Destroy()

        else:
            self.app.SendLeadResponse(clientProfile, false)

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

        wxLogDebug("Trying to upload personal data")
        #if self.app.upload_url is None or self.app.upload_url == "":
        
        #MessageDialog(self,
        #              "Cannot add data: Venue does not have an operational\ndata storage server.",
        #              "Cannot upload")
        #return
        
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            wxLogDebug("Got files:%s " %str(files))

            # upload!
            self.app.UploadPersonalFiles(files)
                                     
        dlg.Destroy()

    def OpenDataProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        dataView = DataDialog(self, -1, "Data Properties")
        dataView.SetDescription(data)
        dataView.ShowModal()
        dataView.Destroy()

    def OpenServiceProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        service = self.contentListPanel.tree.GetItemData(id).GetData()
        serviceView = ServiceDialog(self, -1, "Service Properties")
        serviceView.SetDescription(service)
        serviceView.ShowModal()
        serviceView.Destroy()

    def OpenApplicationProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        application = self.contentListPanel.tree.GetItemData(id).GetData()

        # For now, use service dialog since app and service have same properties
        applicationView = ServiceDialog(self, -1, "Application Properties")
        applicationView.SetDescription(application)
        applicationView.ShowModal()
        applicationView.Destroy()

    def OpenParticipantProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        participant =  self.contentListPanel.tree.GetItemData(id).GetData()
        wxLogDebug("Open profile view")
        profileView = ProfileDialog(self, -1, "Profile")
        wxLogDebug("open profile view with this participant: %s" %participant.name)
        profileView.SetDescription(participant)
        wxLogDebug("Show profile view")
        profileView.ShowModal()
        profileView.Destroy()
         
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
                EVT_MENU(self, id, self.FillInAddress)
                
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
        url = self.app.venueUri
                
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
                EVT_MENU(self, id, self.FillInAddress)

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
                                     self.app.nodeServiceUri, "Please, specify node service URL")

        if setNodeUrlDialog.ShowModal() == wxID_OK:
            self.app.SetNodeUrl(setNodeUrlDialog.address.GetValue())
       
        setNodeUrlDialog.Destroy()

    def OpenAddDataDialog(self, event = None):

        #
        # Verify that we have a valid upload URL. If we don't have one,
        # then there isn't a data upload service available.
        #

        wxLogDebug("Trying to upload to '%s'" % (self.app.upload_url))
        if self.app.upload_url is None or self.app.upload_url == "":
        
            MessageDialog(self,
                          "Cannot add data: Venue does not have an operational\ndata storage server.",
                          "Cannot upload")
            return
        
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            wxLogDebug("Got files:%s " %str(files))

            # upload!

            self.app.UploadVenueFiles(files)
                          
        dlg.Destroy()

    def OpenProfileDialog(self, event):
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile information')
        profileDialog.SetProfile(self.app.profile)
                
        if (profileDialog.ShowModal() == wxID_OK):
            profile = profileDialog.GetNewProfile()
            self.app.ChangeProfile(profile)
            wxLogDebug("change profile: %s" %profile.name)

        profileDialog.Destroy()


    def OpenAddServiceDialog(self, event):
        addServiceDialog = ServiceDialog(self, -1,
                                            'Please, fill in service details')
        if (addServiceDialog.ShowModal() == wxID_OK):
           
            self.app.AddService(addServiceDialog.GetNewProfile())

        addServiceDialog.Destroy()

    def OpenNodeMgmtApp(self, event):
        frame = NodeManagementClientFrame(self, -1, "Access Grid Node Management")
        wxLogDebug("open node management")
        frame.AttachToNode( self.app.nodeServiceUri )
        if frame.Connected(): # Right node service uri
            frame.UpdateUI()
            frame.Show(true)

        else: # Not right node service uri
            setNodeUrlDialog = UrlDialog(self, -1, "Set node service URL", \
                                         self.app.nodeServiceUri, "Please, specify node service URL")
            
            if setNodeUrlDialog.ShowModal() == wxID_OK:
                self.app.SetNodeUrl(setNodeUrlDialog.address.GetValue())
                frame.AttachToNode( self.app.nodeServiceUri )
                
                if frame.Connected(): # try again
                    frame.Update()
                    frame.Show(true)

                else: # wrong url
                    MessageDialog(self, \
                                  'Can not open node service management\nbased on the URL you specified', \
                                  'Node Management Error')
                
            setNodeUrlDialog.Destroy()
                 
                          
    def OpenDataProfileDialog(self, event):
        self.contentList.tree.GetSelection()
        profileDialog = ProfileDialog(NULL, -1, 'Profile')
        profileDialog.SetProfile(self.app.profile)
        profileDialog.ShowModal()
        profileDialog.Destroy()
              
    def OpenAboutDialog(self, event):
        aboutDialog = AboutDialog(self, wxSIMPLE_BORDER)
        aboutDialog.Popup()
        
    def SaveData(self, event):
        wxLogDebug("Save data")
        id = self.contentListPanel.tree.GetSelection()
        data =  self.contentListPanel.tree.GetItemData(id).GetData()

        
        if(data != None):
            name = data.name
            dlg = wxFileDialog(self, "Save file as",
                               defaultFile = name,
                               style = wxSAVE | wxOVERWRITE_PROMPT)
            if dlg.ShowModal() == wxID_OK:
                path = dlg.GetPath()
                wxLogDebug("Saving file as %s" %path)

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
        if(data != None):
            name = data.name
            tfilepath = os.path.join(GetTempDir(), name)

            self.app.SaveFile(data, tfilepath)

            if sys.platform == 'win32':
                tfilepath = win32api.GetShortPathName(tfilepath)

            commands = GetMimeCommands(filename = tfilepath,
                                       ext = name.split('.')[-1])
            if commands == None:
                message = ("No registered for the selected data\n(mimetype = %s)" % data.mimeType)
                dlg = MessageDialog(self.frame, message)
                wxLogDebug(message)
            else:
                if commands.has_key('open'):
                    wxLogDebug("executing cmd: %s" % commands['open'])
                    if commands['open'][0:6] == "WX_DDE":
                        pid = wxExecute(commands['open'])
                    else:
                        pid = wxShell(commands['open'])
        else:
            self.__showNoSelectionDialog("Please, select the data you want to open")     
    
    def RemoveData(self, event):
        id = self.contentListPanel.tree.GetSelection()
        data = self.contentListPanel.tree.GetItemData(id).GetData()
        
        if(data != None):
            text ="Are you sure you want to delete "+ data.name
            areYouSureDialog = wxMessageDialog(self, text, \
                                               '', wxOK |  wxCANCEL |wxICON_INFORMATION)
            if(areYouSureDialog.ShowModal() == wxID_OK):
                self.app.RemoveData(data)
                                    
            areYouSureDialog.Destroy()
                
        else:
            self.__showNoSelectionDialog("Please, select the data you want to delete")

    def RemoveService(self, event):
        id = self.contentListPanel.tree.GetSelection()
        service =  self.contentListPanel.tree.GetItemData(id).GetData()
        
        if(service != None):
            text ="Are you sure you want to delete "+ service.name
            areYouSureDialog = wxMessageDialog(self, text, \
                                               '', wxOK |  wxCANCEL |wxICON_INFORMATION)
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
            callback = lambda event,theApp=app: self.StartApp(event,theApp)
            EVT_MENU(self, appId, callback)

    def EnableAppMenu(self, flag):
        for entry in self.applicationMenu.GetMenuItems():
            self.applicationMenu.Enable( entry.GetId(), flag )

    def StartApp(self,event,app):
        self.app.StartApp( app )

    def JoinApp(self,event):
        id = self.contentListPanel.tree.GetSelection()
        app =  self.contentListPanel.tree.GetItemData(id).GetData()
        if(app != None):
            self.app.JoinApp( app )
        else:
            self.__showNoSelectionDialog("Please, select the application you want to join")     
    
    def OpenService(self,event):
        id = self.contentListPanel.tree.GetSelection()
        service =  self.contentListPanel.tree.GetItemData(id).GetData()

        if(service != None):
            self.app.OpenService( service )
        else:
            self.__showNoSelectionDialog("Please, select the service you want to open")       
    
    def RemoveApp(self,event):
        id = self.contentListPanel.tree.GetSelection()
        app =  self.contentListPanel.tree.GetItemData(id).GetData()

        if(app != None):
            text ="Are you sure you want to delete "+ app.name
            areYouSureDialog = wxMessageDialog(self, text, \
                                               '', wxOK |  wxCANCEL |wxICON_INFORMATION)
            if(areYouSureDialog.ShowModal() == wxID_OK):
                self.app.RemoveApp( app )
        else:
            self.__showNoSelectionDialog("Please, select the application you want to delete")       
            
            
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
        self.address = wxComboBox(self.panel, self.ID_ADDRESS, defaultVenue,
                                  choices = venuesList.keys(),
                                  style = wxCB_DROPDOWN)
        
        self.goButton = wxButton(self.panel, self.ID_GO, "Go", wxDefaultPosition, wxSize(20, 21))
        self.backButton = wxButton(self.panel, self.ID_BACK , "<<", wxDefaultPosition, wxSize(20, 21))
        self.Layout()
        self.__addEvents()
        
    def __addEvents(self):
        EVT_BUTTON(self, self.ID_GO, self.callAddress)
        EVT_BUTTON(self, self.ID_BACK, self.GoBack)
        EVT_TEXT_ENTER(self, self.ID_ADDRESS, self.callAddress)
        
    def SetAddress(self, url):
        self.address.SetValue(url)

    def AddChoice(self, url):
        if self.address.FindString(url) == wxNOT_FOUND:
            self.address.Append(url)
        self.SetAddress(url)
            
    def GoBack(self, event):
        wxBeginBusyCursor()
        self.application.GoBack()
        wxEndBusyCursor()
      
    def callAddress(self, event):
        url = self.address.GetValue()
        venueUri = self.__fixSpaces(url)
        self.AddChoice(venueUri)
        wxBeginBusyCursor()
        self.application.GoToNewVenue(venueUri)
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
        self.panel.SetSizer(box)
        box.Fit(self.panel)
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
        #\ |wxSB_HORIZONTAL| wxSB_VERTICAL)
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
            self.app.GoToNewVenue(description.uri)
            wxEndBusyCursor()
        else:
            wxLogMessage("This exit does no longer exist, sorry!")
            wxLog_GetActiveTarget().Flush()
                
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
        print '----------------- remove venue door'

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
    def __init__(self, parent, id, profile):
        wxPanel.__init__(self, parent, id, wxDefaultPosition, \
			 size = wxSize(400,200), style = wxRAISED_BORDER)
        self.id = id
        self.parent = parent
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
        EVT_ENTER_WINDOW(self, self.onMouseEnter)
        EVT_LEAVE_WINDOW(self, self.onMouseLeave)
            
    def onMouseEnter(self, event):
        self.button.SetBitmap(self.bitmapSelect)
        
    def onMouseLeave(self, event):
        self.button.SetBitmap(self.bitmap)
               
    def onClick(self, event):
        self.parent.GoToNewVenue(event)
        
    def GetName(self):
        return self.label.GetLabel()

    def GetButtonId(self):
        return self.id

    def AdjustText(self):
        t = ''
        self.label.SetValue(t)

        line1 = self.label.GetLineText(0)
        text = line1

        if(t != line1):
            line2 = self.label.GetLineText(1)
            text  = text+line2

        self.label.SetValue(text)
                
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
    participantDict = {}
    dataDict = {}
    serviceDict = {}
    nodeDict = {}
    applicationDict = {}
    personalDataDict = {}
    
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, 
			 wxDefaultSize)
     	id = wxNewId()
       
        self.parent = parent
	self.app = app
	self.tree = wxTreeCtrl(self, id, wxDefaultPosition, 
			      wxDefaultSize, style = wxTR_TWIST_BUTTONS | wxTR_HAS_BUTTONS |
                               wxTR_NO_LINES  | wxTR_HIDE_ROOT)
        self.__setImageList()
	self.__setTree()
	self.__setProperties()

        EVT_SIZE(self, self.OnSize)
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown) 
        # EVT_LEFT_DOWN(self.tree, self.OnLeftDown)
	
    def __setImageList(self):
	imageList = wxImageList(32,19)
     	self.participantId = imageList.Add(icons.getDefaultParticipantBitmap())
        #self.participantFollowId = imageList.Add(icons.getParticipantFollowBitmap())
        #self.participantLeadId = imageList.Add(icons.getParticipantLeadBitmap())
        self.defaultDataId = imageList.Add(icons.getDefaultDataBitmap())
	self.serviceId = imageList.Add(icons.getDefaultServiceBitmap())
        self.applicationId = imageList.Add(icons.getDefaultServiceBitmap())
        self.nodeId = imageList.Add(icons.getDefaultNodeBitmap())
        #self.nodeFollowId = imageList.Add(icons.getNodeFollowBitmap())
        #self.nodeLeadId = imageList.Add(icons.getNodeLeadBitmap())
        self.tree.AssignImageList(imageList)

    def AddParticipant(self, profile, dataList = []):
        participant = self.tree.AppendItem(self.participants, profile.name, \
                                           self.participantId, self.participantId)
        self.tree.SetItemData(participant, wxTreeItemData(profile)) 
        self.participantDict[profile.publicId] = participant
        self.tree.SortChildren(self.participants)
        self.tree.Expand(self.participants)

        for data in dataList:
            participantData = self.tree.AppendItem(participant, data.name, \
                                                   self.defaultDataId, self.defaultDataId)
            self.personalDataDict[data.name] = participantData 
            self.tree.SetItemData(participantData, wxTreeItemData(data))

        self.tree.SortChildren(participant)
            
    def RemoveParticipantData(self, dataTreeId):
        del self.personalDataDict[id]
        self.tree.Delete(id)
                          
    def RemoveParticipant(self, description):
        wxLogDebug("Remove participant")
        if description!=None :
            if(self.participantDict.has_key(description.publicId)):
                wxLogDebug("Found participant in tree")
                id = self.participantDict[description.publicId]

                if id!=None:
                    wxLogDebug("Removed participant from tree")
                    self.tree.Delete(id)

                wxLogDebug("Delete participant from dictionary")
                del self.participantDict[description.publicId]
                          
    def ModifyParticipant(self, description):
        wxLogDebug('Modify participant')
        type =  description.profileType
        oldType = None
        id = description.publicId

        if(self.participantDict.has_key(id)):
            oldType = 'user'
            
        elif(self.nodeDict.has_key(id)):
            oldType = 'node'
        
        if(oldType == type):   # just change details
            wxLogDebug('Change details')
            if type == 'user':
                treeId = self.participantDict[description.publicId]
                profile = self.tree.GetItemData(treeId).GetData()
                self.tree.SetItemText(treeId, description.name)
                wxLogDebug('this is the name we are changing to %s'%description.name)
                profile = description
                self.tree.SetItemData(treeId, wxTreeItemData(description))
                self.tree.SortChildren(self.participants)
               
            else:
                treeId = self.nodeDict[description.publicId]
                profile = self.tree.GetItemData(treeId).GetData()
                self.tree.SetItemText(treeId, description.name)
                profile = description
                self.tree.SetItemData(treeId, wxTreeItemData(description))
                self.tree.SortChildren(self.nodes)

        elif(oldType != None): # move to new category type

            if type == 'node':
                wxLogDebug('Change to node')
                if(self.participantDict.has_key(description.publicId)):
                    participantId = self.participantDict[description.publicId]
                    dataList = self.__GetPersonalDataFromItem(participantId)
                    self.RemoveParticipant(description)
                    self.AddNode(description, dataList)
                
            else:
                wxLogDebug('Change to user')
                if (self.nodeDict.has_key(description.publicId)):
                    nodeId = self.nodeDict[description.publicId]
                    dataList = self.__GetPersonalDataFromItem(nodeId)
                    self.RemoveNode(description)
                    self.AddParticipant(description, dataList)

    def __GetPersonalDataFromItem(self, treeId):
        # Get data for this id
        dataList = []
        cookie = 0
        
        if(self.tree.GetChildrenCount(treeId)>0):
            id, cookie = self.tree.GetFirstChild(treeId, cookie)
            wxLogDebug("Got first child")
            d = self.tree.GetPyData(id)
            dataList.append(d)
            wxLogDebug("First child's name = %s " %(d.name))
            wxLogDebug("Nr of children %s"%self.tree.GetChildrenCount(treeId))
            for nr in range(self.tree.GetChildrenCount(treeId)-1):
                id, cookie = self.tree.GetNextChild(treeId, cookie)
                dataList.append(self.tree.GetPyData(id))
                wxLogDebug("Next child's name = %s " %self.tree.GetPyData(id).name)
                
        return dataList
            
    def AddData(self, profile):
        wxLogDebug("profile.type = %s" %profile.type)
                
        #if venue data
        if(profile.type == 'None' or profile.type == None):
            wxLogDebug("This is venue data")
            dataId = self.tree.AppendItem(self.data, profile.name, \
                                        self.defaultDataId, self.defaultDataId)
            self.tree.SetItemData(dataId, wxTreeItemData(profile)) 
            self.dataDict[profile.name] = dataId
            self.tree.SortChildren(self.data)
            self.tree.Expand(self.data)
            
        #if personal data
        else:
            wxLogDebug("This is personal data")
            id = profile.type
            if(self.participantDict.has_key(id)):
                wxLogDebug("Data belongs to a participant")
                participantId = self.participantDict[id]
                dataId = self.tree.AppendItem(participantId, profile.name, \
                                     self.defaultDataId, self.defaultDataId)
                self.tree.SetItemData(dataId, wxTreeItemData(profile))
                self.personalDataDict[profile.name] = dataId
                self.tree.SortChildren(participantId)
                
                # I select the participant to ensure the twist button is
                # visible when first data item is added. I have to do
                # this due to a bug in wxPython.

                id = self.tree.GetSelection()
                #if(self.tree.GetChildrenCount(participantId) == 0):
                if(self.tree.GetSelection() == participantId):
                    self.tree.Unselect()
                #else:
                self.tree.SelectItem(participantId)
                self.tree.SelectItem(id)
                
               
            elif (self.nodeDict.has_key(id)):
                wxLogDebug("Data belongs to a node")
                nodeId = self.nodeDict[id]
                dataId = self.tree.AppendItem(nodeId, profile.name, \
                                              self.defaultDataId, self.defaultDataId)
                self.tree.SetItemData(dataId, wxTreeItemData(profile))
                self.personalDataDict[profile.name] = dataId
                self.tree.SortChildren(nodeId)
                
                # I select the node to ensure the twist button is visible
                # when first data item is added. I have to do this due to
                # a bug in wxPython.
                id = self.tree.GetSelection()
                if(self.tree.GetSelection() == nodeId):
                    self.tree.Unselect()
                
                self.tree.SelectItem(nodeId)
                self.tree.SelectItem(id)
                
            elif (self.nodeDict.has_key(id)):
                wxLogInfo("Owner of data does not exist")
        
       
    def UpdateData(self, profile):
        id = None
        
        #if venue data
        if(self.dataDict.has_key(profile.name)):
            wxLogDebug("VenueManagementUIClasses::DataDict has data")
            id = self.dataDict[profile.name]
            
        #if personal data
        elif (self.personalDataDict.has_key(profile.name)):
            wxLogDebug("VenueManagementUIClasses::Personal DataDict has data")
            id = self.personalDataDict[profile.name]
            
        if(id != None):
            self.tree.SetItemData(id, wxTreeItemData(profile))
        else:
            wxLogDebug("Id is none - that is not good")
                          
    def RemoveData(self, profile):
        #if venue data
        if(self.dataDict.has_key(profile.name)):
            wxLogDebug("Remove venue data")
            id = self.dataDict[profile.name]
            del self.dataDict[profile.name]
            
        #if personal data
        elif (self.personalDataDict.has_key(profile.name)):
            wxLogDebug("Remove personal data")
            id = self.personalDataDict[profile.name]
            del self.personalDataDict[profile.name]
            
        if(id != None):
            wxLogDebug("Delete id")
            self.tree.Delete(id)
                          
    def AddService(self, profile):
        service = self.tree.AppendItem(self.services, profile.name,\
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

    def AddNode(self, profile, dataList = []):
        node = self.tree.AppendItem(self.nodes, profile.name, \
                                       self.nodeId, self.nodeId)
        self.tree.SetItemData(node, wxTreeItemData(profile)) 
        self.nodeDict[profile.publicId] = node
        self.tree.SortChildren(self.nodes)
        self.tree.Expand(self.nodes)
        
        for data in dataList:
            nodeData = self.tree.AppendItem(node, data.name, \
                                            self.defaultDataId, self.defaultDataId)
            self.tree.SetItemData(nodeData, wxTreeItemData(data))
            self.personalDataDict[data.name] = nodeData   # data gets new tree id

        self.tree.SortChildren(node)

    def RemoveNode(self, profile):
        if(profile!=None):
            if(self.nodeDict.has_key(profile.publicId)):
                id = self.nodeDict[profile.publicId]

                if(id != None):
                    self.tree.Delete(id)
                    
                del self.nodeDict[profile.publicId]

    def __setTree(self):
        #temporary fix for wxPython bug

        if sys.platform == "win32":
            index = -2
        elif sys.platform == "linux2":
            index = -1
        
        self.root = self.tree.AddRoot("The Lobby", index, index)
                    
	self.participants = self.tree.AppendItem(self.root, "Participants", index, index)
        self.nodes = self.tree.AppendItem(self.root, "Nodes", index, index)
        self.data = self.tree.AppendItem(self.root, "Data", index, index) 
        self.services = self.tree.AppendItem(self.root, "Services", index, index)
        self.applications = self.tree.AppendItem(self.root, "Applications", index, index)

        self.tree.SetItemBold(self.participants)
        self.tree.SetItemBold(self.nodes)
        self.tree.SetItemBold(self.data)
        self.tree.SetItemBold(self.services)
	self.tree.SetItemBold(self.applications)
      
        colour = wxTheColourDatabase.FindColour("NAVY")
                
        self.tree.SetItemTextColour(self.participants, colour)
        self.tree.SetItemTextColour(self.nodes, colour)
        self.tree.SetItemTextColour(self.data, colour)
        self.tree.SetItemTextColour(self.services, colour)
	self.tree.SetItemTextColour(self.applications, colour)
               
        self.tree.Expand(self.participants)
        self.tree.Expand(self.data)
        self.tree.Expand(self.services)
        self.tree.Expand(self.nodes)
        
    def __setProperties(self):
        pass
      
    def UnSelectList(self):
        self.tree.Unselect()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)
	
    #def OnLeftDown(self, event):
    #    self.x = event.GetX()
    #    self.y = event.GetY()
    #	self.tree.Unselect() 
    #	event.Skip()

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

            # service
            #for object in self.serviceDict:
            #    if serviceItem != None and serviceItem.name == object:
            #        self.app.RemoveService(serviceItem)
            #        break
                
    def OnRightClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        treeId = self.tree.GetSelection()
        item = self.tree.GetItemData(treeId).GetData()
        text = self.tree.GetItemText(treeId)

        if text == 'Data' or isinstance(item,DataDescription):
            self.PopupMenu(self.parent.dataMenu, wxPoint(self.x, self.y))

        elif text == 'Services':
            self.PopupMenu(self.parent.serviceMenu, wxPoint(self.x, self.y))

        elif text == 'Applications':
            self.PopupMenu(self.parent.applicationMenu,
                           wxPoint(self.x, self.y))
        elif text == 'Participants' or text == 'Nodes' or item == None:
            pass

        elif isinstance(item, ServiceDescription):
            self.PopupMenu(self.parent.serviceMenu, wxPoint(self.x,self.y))

        elif isinstance(item,ApplicationDescription):
            self.PopupMenu(self.parent.applicationEntryMenu, wxPoint(self.x, self.y))
            
        elif isinstance(item, DataDescription):
            self.PopupMenu(self.parent.dataMenu, wxPoint(self.x, self.y))

        elif isinstance(item,ClientProfile):
            wxLogDebug("Is this me? public is = %s, my id = %s "%(item.publicId, self.app.profile.publicId))
            if(item.publicId == self.app.profile.publicId):
                wxLogDebug("This is me")
                self.PopupMenu(self.parent.meMenu, wxPoint(self.x, self.y))

            elif(item.profileType == 'node'):
                wxLogDebug("This is a node")
                self.PopupMenu(self.parent.nodeMenu, wxPoint(self.x, self.y))

            elif(item.profileType == 'user'):
                wxLogDebug("This is a user")
                self.PopupMenu(self.parent.participantMenu,
                               wxPoint(self.x, self.y))

            
    def CleanUp(self):
        for index in self.participantDict.values():
            self.tree.Delete(index)

        for index in self.nodeDict.values():
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
        self.nodeDict.clear()
        self.applicationDict.clear()
                            
 
class TextClientPanel(wxPanel):
    aboutText = """PyText 1.0 -- a simple text client in wxPython and pyGlobus.
    This has been developed as part of the Access Grid project."""
    bufferSize = 128
    venueId = None
    location = None
    Processor = None
    ID_BUTTON = wxNewId()
    
    def __init__(self, *args, **kwds):
        wxPanel.__init__(self, *args, **kwds)
        self.TextOutput = wxTextCtrl(self, wxNewId(), "",
                                     style= wxTE_MULTILINE|wxTE_READONLY)
        self.label = wxStaticText(self, -1, "Your message:")
        self.display = wxButton(self, self.ID_BUTTON, "Display", style = wxBU_EXACTFIT)
        self.textInputId = wxNewId()
        self.TextInput = wxTextCtrl(self, self.textInputId, "",
                                    style= wxTE_PROCESS_ENTER)
        self.TextInput.SetToolTipString("Write your message here")
        self.__set_properties()
        self.__do_layout()
 
        EVT_TEXT_ENTER(self, self.textInputId, self.LocalInput)
        EVT_BUTTON(self, self.ID_BUTTON, self.LocalInput)
        self.Show(true)

    def SetLocation(self, privateId, location, venueId):
        if self.Processor != None:
            self.Processor.Input(DisconnectEvent(self.venueId, privateId))
            self.Processor.Stop()
            self.socket.close()
            
        self.host = location[0]
        self.port = location[1]
        self.venueId = venueId
        self.attr = CreateTCPAttrAlwaysAuth()
        self.socket = GSITCPSocket()
        try:
            self.socket.connect(self.host, self.port, self.attr)
        except:
            wxLogDebug("Couldn't connect to text service! %s:%d", self.host,
                       self.port)
            raise TextClientConnectException

        wxLogDebug("VenueClientUIClasses.py: Set text location")
        wxLogDebug("\n\thost:%s\n\tport:%d\n\tvenueId:%s\n\tattr:%s"
                   % (self.host, self.port, self.venueId, str(self.attr)))
        wxLogDebug("\n\tsocket:%s" % str(self.socket))
        
        self.Processor = SimpleTextProcessor(self.socket, self.venueId,
                                             self.OutputText)
        self.Processor.Input(ConnectEvent(self.venueId, privateId))
        self.TextOutput.Clear()
        self.TextInput.Clear()

    def OutputText(self, text):
        wxCallAfter( self.TextOutput.AppendText, text)

    def __set_properties(self):
        self.SetSize((375, 225))
        
    def __do_layout(self):
        TextSizer = wxBoxSizer(wxVERTICAL)
        TextSizer.Add(self.TextOutput, 2, wxEXPAND|wxALIGN_CENTER_HORIZONTAL, 0)
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
        if(self.venueId != None):
            wxLogDebug("VenueClientUIClasses.py: User writes: %s"
                       % self.TextInput.GetValue())
            textEvent = TextEvent(self.venueId, None, 0,
                                  self.TextInput.GetValue())
            try:
                self.Processor.Input(textEvent)
                self.TextInput.Clear()
            except:
                wxLogError("Could not send message successfully")
                wxLog_GetActiveTarget().Flush()
        else:
            wxLogMessage( "Please, go to a venue before using the chat")
            wxLog_GetActiveTarget().Flush()
           
    def Stop(self):
        wxLogDebug("VenueClientUIClasses.py: Stop processor")
        self.Processor.Stop()
        
    def OnCloseWindow(self):
        wxLogDebug("VenueClientUIClasses.py: Destroy text client")
        self.Destroy()
        
      
class SaveFileDialog(wxDialog):
    def __init__(self, parent, id, title, message, doneMessage, fileSize):
        wxDialog.__init__(self, parent, id, title,
                          size = wxSize(300, 200))

        self.doneMessage = doneMessage

        try:
            self.fileSize = int(fileSize)
        except TypeError:
            wxLogDebug("Received invalid file size: '%s'" % (fileSize))
            fileSize = 1
            
        wxLogDebug("created, size=%d " %fileSize)
        
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
            wxLogDebug("SaveFileDialog.OnButton: Cancelling transfer!")
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
            wxLogDebug("UploadFiles.OnButton: Cancelling transfer!")
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
            wxLogMessage('Please, select the venue you want to delete')
            wxLog_GetActiveTarget().Flush()

    def OnRename(self, event):
        if(self.dictCopy.has_key(self.currentItem)):
            renameDialog = RenameDialog(self, -1, "Rename venue")
        else:
            wxLogMessage('Please, select the venue you want to rename')
            wxLog_GetActiveTarget().Flush()
            
    def Rename(self, name):
        self.dictCopy[name] = self.dictCopy[self.currentItem]
        del self.dictCopy[self.currentItem]

        self.myVenuesList.SetItemText(self.currentIndex, name)
               
    def OnItemSelected(self, event):
        self.currentIndex = event.m_itemIndex
        self.currentItem = self.myVenuesList.GetItemText(event.m_itemIndex)
              
    def OnRightDown(self, event):
        self.x = event.GetX() + self.myVenuesList.GetPosition().x
        self.y = event.GetY() + self.myVenuesList.GetPosition().y
        self.PopupMenu(self.menu, wxPoint(self.x, self.y))
        event.Skip()

    def OnBeginEdit(self, event):
        print 'begin'

    def OnEndEdit(self, event):
        print 'end'

    def __setEvents(self):
        EVT_RIGHT_DOWN(self.myVenuesList, self.OnRightDown)
        EVT_LIST_ITEM_SELECTED(self.myVenuesList, self.ID_LIST, self.OnItemSelected)
        EVT_MENU(self.menu, self.ID_RENAME, self.OnRename)
        EVT_MENU(self.menu, self.ID_DELETE, self.OnDelete)
        EVT_LIST_BEGIN_LABEL_EDIT(self.myVenuesList,self.ID_LIST, self.OnBeginEdit) 
        EVT_LIST_END_LABEL_EDIT(self.myVenuesList,self.ID_LIST, self.OnEndEdit)
               
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
        name = app.venueState.name
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
        wxLogDebug("VenueClientUIClasses.py: Create profile dialog")
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (400,20), validator = TextValidator())
        self.emailText = wxStaticText(self, -1, "Email:", style=wxALIGN_LEFT)
        self.emailCtrl = wxTextCtrl(self, -1, "")
        self.phoneNumberText = wxStaticText(self, -1, "Phone Number:", style=wxALIGN_LEFT)
        self.phoneNumberCtrl = wxTextCtrl(self, -1, "")
        self.locationText = wxStaticText(self, -1, "Location:")
        self.locationCtrl = wxTextCtrl(self, -1, "")
        self.supportText = wxStaticText(self, -1, "Support Information:", style=wxALIGN_LEFT)
        self.supportCtrl = wxTextCtrl(self, -1, "")
        self.homeVenue= wxStaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wxTextCtrl(self, -1, "")
        self.profileTypeText = wxStaticText(self, -1, "Profile Type:", style=wxALIGN_LEFT)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.profile = None
        #self.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
        self.__doLayout()
        wxLogDebug("VenueClientUIClasses.py: Created profile dialog")

    def GetNewProfile(self):
        wxLogDebug("VenueClientUIClasses.py: Get profile information from dialog")
        if(self.profile != None):
            self.profile.SetName(self.nameCtrl.GetValue())
            self.profile.SetEmail(self.emailCtrl.GetValue())
            self.profile.SetPhoneNumber(self.phoneNumberCtrl.GetValue())
            self.profile.SetTechSupportInfo(self.supportCtrl.GetValue())
            self.profile.SetLocation(self.locationCtrl.GetValue())
            self.profile.SetHomeVenue(self.homeVenueCtrl.GetValue())
            self.profile.SetProfileType(self.profileTypeBox.GetValue())
        wxLogDebug("VenueClientUIClasses.py: Got profile information from dialog")
        return self.profile

    def SetProfile(self, profile):
        wxLogDebug("VenueClientUIClasses.py: Set profile information in dialog")
        self.profile = profile
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], style = wxCB_DROPDOWN)
        #self.profileTypeBox.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "verdana"))
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
        wxLogDebug("VenueClientUIClasses.py: Set profile information successfully in dialog")

    def SetDescription(self, item):
        wxLogDebug("VenueClientUIClasses.py: Set description in dialog name:%s, email:%s, phone:%s, location:%s support:%s, home:%s, dn:%s"
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
        self.__setEditable(false)
        self.cancelButton.Destroy()
        wxLogDebug("VenueClientUIClasses.py: Set description successfully in dialog")

    def __setEditable(self, editable):
        wxLogDebug("VenueClientUIClasses.py: Set editable in dialog")
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
        wxLogDebug("VenueClientUIClasses.py: Set editable in successfully dialog")
           
    def __doLayout(self):
        wxLogDebug("VenueClientUIClasses.py: Do layout")
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
        #gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        sizer2.Add(self.gridSizer, 1, wxALL, 10)

        self.sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        self.sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)
        self.SetAutoLayout(1)
        wxLogDebug("VenueClientUIClasses.py: Did layout")
                
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
        self.ownerCtrl.SetValue(str(dataDescription.owner.dn))
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
        if self.app.upload_url is None or self.app.upload_url == "":
            MessageDialog(NULL,
                          "Cannot add data: Venue does not have an operational\ndata storage server.",
                          "Cannot upload")
            return

        else:
            self.app.UploadVenueFiles(files)
 

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
        log.critical("The GLOBUS_LOCATION environment must be set, check your Globus installation")
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
    log.debug("My hostname is %s", myhost)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((myhost, 0))
        log.debug("VerifyExecutionEnvironment: bind to local hostname of %s succeeds", myhost)
    except socket.error:
        log.critical("VerifyExecutionEnvironment: bind to local hostname of %s fails", myhost)

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
        log.critical("AGServiceManager.py not found")
        dlg = wxMessageDialog(None, "The application was unable to determine the location of\n" +
                              "its AGServiceManager component. If you installed using a Windows\n" +
                              "installer, this is due to a bug in the installer. If you are running\n" +
                              "from a CVS checkout, check the value of the AGTK_INSTALL environment variable.",
                              "Application configuration problem", wxOK)
        dlg.ShowModal()
        dlg.Destroy()
        sys.exit(1)
        
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
