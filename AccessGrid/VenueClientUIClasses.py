#-----------------------------------------------------------------------------
# Name:        VenueClientUIClasses.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueClientUIClasses.py,v 1.50 2003-02-27 21:25:41 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import os.path

from wxPython.wx import *
from AccessGrid import icons
from AccessGrid.VenueClient import VenueClient, EnterVenueException
import threading
from AccessGrid import Utilities
from AccessGrid.UIUtilities import AboutDialog, ErrorDialog
import AccessGrid.ClientProfile
from AccessGrid.Descriptions import DataDescription
from AccessGrid.Descriptions import ServiceDescription
from AccessGrid.TextClientUI import TextClientUI
from AccessGrid.Utilities import formatExceptionInfo

from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame

class VenueClientFrame(wxFrame):
    
    '''VenueClientFrame. 

    The VenueClientFrame is the main frame of the application, creating statusbar, dock,
    venueListPanel, and contentListPanel.  The contentListPanel represents current venue and
    has information about all participants in the venue, it also shows what data and services 
    are available in the venue, as well as nodes connected to the venue.  It represents a room
    with its contents visible for the user.  The venueListPanel contains a list of connected 
    venues/exits to current venue.  By clicking on a door icon the user travels to another 
    venue/room, which contents will be shown in the contentListPanel.
    
    '''
    ID_WINDOW_TOP    = 5100
    ID_WINDOW_LEFT1  = 5101
    ID_WINDOW_LEFT2  = 5102
    ID_WINDOW_BOTTOM = 5103
    ID_VENUE_DATA = NewId()
    ID_VENUE_DATA_ADD = NewId() 
    ID_VENUE_DATA_SAVE = NewId() 
    ID_VENUE_DATA_DELETE = NewId() 
    ID_VENUE_SERVICE = NewId() 
    ID_VENUE_SERVICE_ADD = NewId()
    ID_VENUE_SERVICE_DELETE = NewId()
    ID_VENUE_VIRTUAL = NewId()
    ID_VENUE_TEXT = NewId()
    ID_VENUE_CLOSE = NewId()
    ID_PROFILE = NewId()
    ID_PROFILE_EDIT = NewId()
    ID_MYNODE_MANAGE = NewId()
    ID_MYNODE_URL = NewId()
    ID_MYVENUE_ADD = NewId()
    ID_HELP = NewId()
    ID_HELP_ABOUT = NewId()
    ID_PARTICIPANT_PROFILE = NewId()
    ID_PARTICIPANT_FOLLOW = NewId()
    ID_PARTICIPANT_LEAD = NewId()
    ID_NODE_PROFILE = NewId()
    ID_NODE_FOLLOW = NewId()
    ID_NODE_LEAD = NewId()
    ID_NODE_MANAGE = NewId()
    ID_ME_PROFILE = NewId()
      
    def __init__(self, parent, id, title, app = None):
        wxFrame.__init__(self, parent, id, title)
        self.Centre()
	self.app = app
        self.parent = parent
        self.textClient = None
        self.myVenuesList = []
        self.myVenuesFile = os.path.join(self.app.accessGridPath, "myVenues.txt" )
	self.menubar = wxMenuBar()
	self.statusbar = self.CreateStatusBar(1)
	#self.dock = wxToolBar(self, 600, pos = wxDefaultPosition, \
        #                      size = (300, 30), style = wxTB_TEXT| wxTB_HORIZONTAL| wxTB_FLAT)


        self.venueAddressBar = VenueAddressBar(self, self.ID_WINDOW_TOP, app, self.myVenuesList, 'default venue')
        self.venueAddressBar.SetDefaultSize(wxSize(1000, 35))
        self.venueAddressBar.SetOrientation(wxLAYOUT_HORIZONTAL)
        self.venueAddressBar.SetAlignment(wxLAYOUT_TOP)
        
        self.venueListPanel = VenueListPanel(self, self.ID_WINDOW_LEFT1, app)
        self.venueListPanel.SetDefaultSize(wxSize(120, 1000))
        self.venueListPanel.SetOrientation(wxLAYOUT_VERTICAL)
        self.venueListPanel.SetSashVisible(wxSASH_RIGHT, TRUE)
        self.venueListPanel.SetAlignment(wxLAYOUT_LEFT)
        
        self.contentListPanel = ContentListPanel(self, app)
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
        
        #fileDropTarget = FileDropTarget(self.dock)
        #self.dock.SetDropTarget(fileDropTarget)
        self.__setStatusbar()
	self.__setMenubar()
        #self.__setDock()
	self.__setProperties()
        self.__doLayout()
        self.__setEvents()
        
    def OnSashDrag(self, event):
        if event.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
            return

        eID = event.GetId()

        if eID == self.ID_WINDOW_LEFT1:
            self.venueListPanel.Show()
            width = event.GetDragRect().width
            if width < 60:
                width = 22
                self.venueListPanel.Hide()
            elif width > (self.GetSize().GetWidth() - 20):
                width = self.GetSize().GetWidth() - 20
            self.venueListPanel.SetDefaultSize(wxSize(width, 1000))

        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)
    
    def OnSize(self, event = None):
        wxLayoutAlgorithm().LayoutWindow(self, self.contentListPanel)

    def __setStatusbar(self):
        self.statusbar.SetToolTipString("Statusbar")   
    
    def __setMenubar(self):
        self.SetMenuBar(self.menubar)

        self.venue = wxMenu()
	self.dataMenu = wxMenu()
	self.dataMenu.Append(self.ID_VENUE_DATA_ADD,"Add...", "Add data to the venue")
	self.dataMenu.Append(self.ID_VENUE_DATA_SAVE,"Save...", "Save data to local disk")
	self.dataMenu.Append(self.ID_VENUE_DATA_DELETE,"Delete", "Remove data")
        self.venue.AppendMenu(self.ID_VENUE_DATA,"&Data", self.dataMenu)
	self.serviceMenu = wxMenu()
	self.serviceMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...", "Add service to the venue")
        self.serviceMenu.Append(self.ID_VENUE_SERVICE_DELETE,"Delete", "Delete service")
        self.venue.AppendMenu(self.ID_VENUE_SERVICE,"&Services",self.serviceMenu)
        self.venue.Append(self.ID_VENUE_TEXT,"&Open chat...", "Open text client to chat with others")

	self.menubar.Append(self.venue, "&Venue")
        
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE, 'Close', "Exit venue")
	
	self.edit = wxMenu()
	self.edit.Append(self.ID_PROFILE, "&Profile...", "Change your personal information")
        self.menubar.Append(self.edit, "&Edit")
        self.myNode = wxMenu()
        self.myNode.Append(self.ID_MYNODE_MANAGE, "&Manage...", "Configure your node")
        self.myNode.Append(self.ID_MYNODE_URL, "&Set URL...", "Specify URL address to node service")
        self.menubar.Append(self.myNode, "My &Node")
        self.myVenues = wxMenu()
        self.myVenues.Append(self.ID_MYVENUE_ADD, "&Add...", "Configure your node")
       
        self.__loadMyVenues()
        self.menubar.Append(self.myVenues, "My &Venues")
              
      	self.help = wxMenu()
        self.help.Append(self.ID_HELP_ABOUT, "About", "Information about the application")
        self.menubar.Append(self.help, "&Help")
        self.HideMenu()

        self.meMenu = wxMenu()
        self.meMenu.Append(self.ID_ME_PROFILE,"View Profile...",\
                                           "View participant's profile information")

        self.participantMenu = wxMenu()
	self.participantMenu.Append(self.ID_PARTICIPANT_PROFILE,"View Profile...",\
                                           "View participant's profile information")
        self.participantMenu.AppendSeparator()
        self.participantMenu.Append(self.ID_PARTICIPANT_FOLLOW,"Follow",\
                                           "Follow this person", wxITEM_CHECK)
        self.participantMenu.Append(self.ID_PARTICIPANT_LEAD,"Lead",\
                                           "Lead this person", wxITEM_CHECK)

        self.nodeMenu = wxMenu()
        self.nodeMenu.Append(self.ID_NODE_PROFILE,"View Profile...",\
                             "View node's profile information")
        self.nodeMenu.Append(self.ID_NODE_MANAGE,"Manage...",\
                                           "Manage this node")
        self.nodeMenu.AppendSeparator()

        self.nodeMenu.Append(self.ID_NODE_FOLLOW,"Follow",\
                                           "Follow this node", wxITEM_CHECK)
        self.nodeMenu.Append(self.ID_NODE_LEAD,"Lead",\
                                           "Lead this node", wxITEM_CHECK)
        # until implemented
        self.nodeMenu.Enable(self.ID_NODE_LEAD, false)
        self.participantMenu.Enable(self.ID_PARTICIPANT_LEAD, false)
        
      
    def HideMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, false)
        self.menubar.Enable(self.ID_VENUE_DATA_SAVE, false)
        self.menubar.Enable(self.ID_VENUE_DATA_DELETE, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, false)
        self.menubar.Enable(self.ID_VENUE_SERVICE_DELETE, false)
       
    def ShowMenu(self):
        self.menubar.Enable(self.ID_VENUE_DATA_ADD, true)
        self.menubar.Enable(self.ID_VENUE_DATA_SAVE, true)
        self.menubar.Enable(self.ID_VENUE_DATA_DELETE, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_ADD, true)
        self.menubar.Enable(self.ID_VENUE_SERVICE_DELETE, true)
     
    def __setEvents(self):
        EVT_SASH_DRAGGED_RANGE(self, self.ID_WINDOW_TOP,
                               self.ID_WINDOW_BOTTOM, self.OnSashDrag)
        EVT_SIZE(self, self.OnSize)
                
        EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.OpenAddDataDialog)
        EVT_MENU(self, self.ID_VENUE_DATA_SAVE, self.SaveData)
        EVT_MENU(self, self.ID_VENUE_DATA_DELETE, self.RemoveData)
        EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.OpenAddServiceDialog)
        EVT_MENU(self, self.ID_VENUE_SERVICE_DELETE, self.RemoveService)
        EVT_MENU(self, self.ID_VENUE_TEXT, self.OpenChat)
        EVT_MENU(self, self.ID_VENUE_CLOSE, self.Exit)
        EVT_MENU(self, self.ID_PROFILE, self.OpenProfileDialog)
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialog)
        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.OpenNodeMgmtApp)
        EVT_MENU(self, self.ID_MYNODE_URL, self.OpenSetNodeUrlDialog)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenues)
        EVT_MENU(self, self.ID_ME_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_PARTICIPANT_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_NODE_PROFILE, self.OpenParticipantProfile)
        EVT_MENU(self, self.ID_PARTICIPANT_FOLLOW, self.Follow)
        
    def __setDock(self):
        """
	self.dock.AddSimpleTool(20, icons.getWordBitmap(), \
                                   "ImportantPaper.doc", "ImportantPaper.doc",)
	self.dock.AddSimpleTool(21, icons.getPowerPointBitmap(), \
                                   "Presentation.ppt", "Presentation.ppt",)
        """
        pass
       	
    def __setProperties(self):
        self.SetTitle("You are not in a venue")
        self.SetIcon(icons.getAGIconIcon())
        self.statusbar.SetStatusWidths([-1])
	self.statusbar.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.menubar.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	currentHeight = self.venueListPanel.GetSize().GetHeight()
	self.venueListPanel.SetSize(wxSize(100, 300))
		
    def __doLayout(self):
        pass
        #self.venueClientSizer = wxBoxSizer(wxVERTICAL)
        #self.venueClientSizer.Add(self.venueAddressBar, 0, wxEXPAND)
        #self.venueContentSizer = wxBoxSizer(wxHORIZONTAL)
        
	#self.venueContentSizer.Add(self.venueListPanel, 0 , wxEXPAND)

	#self.venueContentSizer.Add(self.contentListPanel, 2, wxEXPAND)
	#self.venueClientSizer.Add(self.venueContentSizer, 1, wxEXPAND)
	#self.venueClientSizer.Add(self.dock)
        
	#self.SetSizer(self.venueClientSizer)
        #self.venueClientSizer.Fit(self)
	#self.SetAutoLayout(1)
        #self.Layout()


    def Follow(self, event):
        print 'follow'
        #treeId = self.contentListPanel.tree.GetSelection()
        #personToFollow = self.contentListPanel.tree.GetItemData(treeId).GetData()
        #print personToFollow.venueClientURL
        #self.Follow(personToFollow.venueClientURL)

    def __fillTempHelp(self, x):
        if x == '\\':
            x = '/'
        return x
        
    def FillInAddress(self, event = None, url = None):
        if(url == None):
            url = self.menubar.GetLabel(event.GetId())
            fixedUrlList = map(self.__fillTempHelp, url)
            fixedUrl = ""
            for x in fixedUrlList:
                fixedUrl = fixedUrl + x

        else:
            fixedUrl = url
        
        self.venueAddressBar.SetAddress(fixedUrl)

    def OpenChat(self, event = None):
        try:
            textLoc = tuple(self.app.venueState.GetTextLocation())
            id = self.app.venueState.uniqueId
            self.textClient = TextClientUI(self, -1, "",
                                           location = textLoc,
                                           venueId = id)
            self.textClient.Show(1)
       
        except:
            ErrorDialog(self, "Trying to open text client!")
            print formatExceptionInfo()
            
    def OpenParticipantProfile(self, event):
        id = self.contentListPanel.tree.GetSelection()
        participant =  self.contentListPanel.tree.GetItemData(id).GetData()
        profileView = ProfileDialog(self, -1, "test")
        profileView.SetDescription(participant)

        profileView.ShowModal()
        profileView.Destroy()
        

    def ConnectToMyVenue(self, event):
        url = self.menubar.GetLabel(event.GetId())
        connectToVenueDialog = UrlDialogCombo(self, -1, 'Connect to server', url, list = self.myVenuesList)
        if (connectToVenueDialog.ShowModal() == wxID_OK):
            venueUri = connectToVenueDialog.address.GetValue()
            self.app.GoToNewVenue(venueUri)
          
        connectToVenueDialog.Destroy()
       
    def __loadMyVenues(self, venueURL = None):
        try:
            myVenuesFile = open(self.myVenuesFile, 'r')
            for line in myVenuesFile.readlines():
                l = line[0:len(line)-1]
                self.myVenuesList.append(l)

        except:
            pass
            
        if len(self.myVenuesList)>0:
            self.myVenues.AppendSeparator()

        for url in self.myVenuesList:
            id = NewId()
            self.myVenues.Append(id, url, url)
            EVT_MENU(self, id, self.FillInAddress)

    def AddToMyVenues(self, event):
        #setMyVenueUrlDialog = UrlDialog(self, -1, "Add venue URL to your venues", \
        #                                '', "Please, specify the URL of the venue you want to add to\nyour venues")
        #if setMyVenueUrlDialog.ShowModal() == wxID_OK:
            id = NewId()
            url = self.app.venueUri#setMyVenueUrlDialog.address.GetValue()

            text = url + " \nis added to your venues"
            dlg = wxMessageDialog(self, text, "Add venue",
                                  wxOK | wxICON_INFORMATION)
            if(dlg.ShowModal() == wxID_OK):
                self.myVenues.Append(id, url)
                self.myVenuesList.append(url)
                EVT_MENU(self, id, self.FillInAddress)

                myVenuesFile = open(self.myVenuesFile, 'w')
                for venueUrl in self.myVenuesList:
                    myVenuesFile.write(venueUrl+'\n')
                myVenuesFile.close()

            dlg.Destroy()
                                               
        #setMyVenueUrlDialog.Destroy()
                       
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

        print "Tyring to upload to '%s'" % (self.app.upload_url)
        if self.app.upload_url is None or self.app.upload_url == "":
        
            dlg = wxMessageDialog(self,
                                 "Cannot add data: Venue does not have an operational\ndata storage server.",
                                  "Cannot upload",
                                  wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            print "Got files: ", files

            # upload!

            self.app.UploadFiles(files)
                          
            # data = DataDescription(dlg.GetFilename())
            # self.app.AddData(data)

        dlg.Destroy()

    def OpenProfileDialog(self, event):
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile')
        profileDialog.SetProfile(self.app.profile)
           
        if (profileDialog.ShowModal() == wxID_OK): 
            self.app.ChangeProfile(profileDialog.GetNewProfile())

        profileDialog.Destroy()

    def OpenAddServiceDialog(self, event):
        addServiceDialog = AddServiceDialog(self, -1, 'Please, fill in service details')
        if (addServiceDialog.ShowModal() == wxID_OK):
            self.app.AddService(addServiceDialog.GetNewProfile())

        addServiceDialog.Destroy()

    def OpenConnectToVenueDialog(self, event = None):
        connectToVenueDialog = UrlDialogCombo(self, -1, 'Connect to server', list = self.myVenuesList)
        if (connectToVenueDialog.ShowModal() == wxID_OK):
            venueUri = connectToVenueDialog.address.GetValue()
            self.app.GoToNewVenue(venueUri)
          
        connectToVenueDialog.Destroy()

    def OpenNodeMgmtApp(self, event):
        frame = NodeManagementClientFrame(self, -1, "Access Grid Node Management")
        frame.AttachToNode( self.app.nodeServiceUri )
        if frame.Connected(): # Right node service uri
            frame.Update()
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
                    msgDialog = wxMessageDialog(self, \
                                                'Can not open node service management\nbased on the URL you specified', \
                                                'Node Management Error', wxOK | wxICON_INFORMATION)
                    msgDialog.ShowModal()
                    msgDialog.Destroy() 

        setNodeUrlDialog.Destroy()
                
                          
    def OpenDataProfileDialog(self, event):
        self.contentList.tree.GetSelection()
        profileDialog = ProfileDialog(NULL, -1, 'Profile')
        profileDialog.SetProfile(self.app.profile)
        profileDialog.ShowModal()
        profileDialog.Destroy()
              
    def OpenServiceProfileDialog(self, event):
        print 'open service profile'

    def OpenParticipantProfileDialog(self, event):
        print 'open participant profile'

    def OpenAboutDialog(self, event):
        aboutDialog = AboutDialog(self, wxSIMPLE_BORDER)
        aboutDialog.Popup()
        
    def SaveData(self, event):
        id = self.contentListPanel.tree.GetSelection()
        data =  self.contentListPanel.tree.GetItemData(id).GetData()

        
        if(data != None):
            name = data.name
            dlg = wxFileDialog(self, "Save file as",
                               defaultFile = name,
                               style = wxSAVE | wxOVERWRITE_PROMPT)
            if dlg.ShowModal() == wxID_OK:
                path = dlg.GetPath()
                print "Saving file as ", path

                dlg.Destroy()

                self.app.SaveFile(data, path)
                
            else:
                dlg.Destroy()
            

        else:
            self.__showNoSelectionDialog("Please, select the data you want to delete")

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
            self.app.RemoveService(service)

        else:
            self.__showNoSelectionDialog("Please, select the service you want to delete")       

    def __showNoSelectionDialog(self, text):
         noSelectionDialog = wxMessageDialog(self, text, \
                                             '', wxOK | wxICON_INFORMATION)
         noSelectionDialog.ShowModal()
         noSelectionDialog.Destroy()

    def CleanUp(self):
        try:
            if(self.textClient != None):
                self.textClient.Close()
        except:
            (name, args, tb) = formatExceptionInfo()
            
        self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()

class VenueAddressBar(wxSashLayoutWindow):
     def __init__(self, parent, id, application, venuesList, defaultVenue):
         wxSashLayoutWindow.__init__(self, parent, id, wxDefaultPosition, \
			 wxDefaultSize, wxRAISED_BORDER|wxSW_3D)

         self.application = application
         self.panel = wxPanel(self, -1)
         self.address = wxComboBox(self.panel, 42, defaultVenue,\
                        choices = venuesList, style = wxCB_DROPDOWN)

         self.goButton = wxButton(self.panel, 43, "Go", wxDefaultPosition, wxSize(20, 21))
         self.__doLayout()
         self.__addEvents()
         

     def __addEvents(self):
         EVT_BUTTON(self, 43, self.callAddress)

     def SetAddress(self, url):
         self.address.SetValue(url)

     def AddChoice(self, url):
         if self.address.FindString(url) == wxNOT_FOUND:
             self.address.Append(url)
      
     def callAddress(self, event):
         venueUri = self.address.GetValue()
         self.AddChoice(venueUri)
         self.application.GoToNewVenue(venueUri)
                         
     def __doLayout(self):
         venueServerAddressBox = wxBoxSizer(wxVERTICAL)  
         box = wxBoxSizer(wxHORIZONTAL)
         box.Add(self.address, 1, wxRIGHT|wxTOP, 5)
         box.Add(self.goButton, 0, wxRIGHT|wxTOP, 5)
         self.panel.SetSizer(box)
         box.Fit(self.panel)
         wxLayoutAlgorithm().LayoutWindow(self, self.panel)
       
class VenueListPanel(wxSashLayoutWindow):
    '''VenueListPanel. 
    
    The venueListPanel contains a list of connected venues/exits to current venue.  
    By clicking on a door icon the user travels to another venue/room, 
    which contents will be shown in the contentListPanel.  By moving the mouse over
    a door/exit information about that specific venue will be shown as a tooltip.
    The user can close the venueListPanel if exits/doors are irrelevant to the user and
    the application will extend the contentListPanel.  The panels is separated into a 
    panel containing the close/open buttons and a VenueList object containing the exits.
    '''   
    def __init__(self, parent,id,  app):
        wxSashLayoutWindow.__init__(self, parent, id)
	self.parent = parent
        self.app = app

        self.panel = wxPanel(self, -1)
	self.list = VenueList(self.panel, app)
       
        self.minimizeButton = wxButton(self.panel, 10, "<<", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.minimizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.maximizeButton = wxButton(self.panel, 20, ">>", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.maximizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
        self.minimizeButton.SetToolTipString("Hide Exits")
	self.maximizeButton.SetToolTipString("Show Exits")
	self.maximizeButton.Hide()
        self.exitsText = wxButton(self.panel, -1, "Exits", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
        self.exitsText.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
        self.exitsText.SetBackgroundColour("WHITE")
	self.SetBackgroundColour(self.maximizeButton.GetBackgroundColour())
	self.imageList = wxImageList(32,32)
        self.SetToolTipString("Connected Venues")
        
	self.__doLayout()
        self.__addEvents()
		
    def __addEvents(self):
        EVT_BUTTON(self, 10, self.OnClick) 
        EVT_BUTTON(self, 20, self.OnClick) 

    def __doLayout(self):
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
        self.SetSize(wxSize(22, currentHeight))
        self.parent.UpdateLayout()

    def Show(self):
        currentHeight = self.GetSize().GetHeight()
        self.maximizeButton.Hide()
        self.minimizeButton.Show()  
        self.list.ShowDoors()
        self.SetSize(wxSize(100, currentHeight))
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
    def __init__(self, parent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1, style = wxRAISED_BORDER )
        #\ |wxSB_HORIZONTAL| wxSB_VERTICAL)
        
        self.doorsAndLabelsList = []
        self.exitsDict = {}
        self.__doLayout()
        self.parent = parent
        self.EnableScrolling(true, true)
        self.SetScrollRate(1, 1)
     
    def __doLayout(self):
       # self.box = wxBoxSizer(wxVERTICAL)
        
       # self.column = wxFlexGridSizer(cols=1, vgap=5, hgap=0)
       # self.column.AddGrowableCol(1)
	       
       # self.column.Add(40, 5)   
       # self.box.SetVirtualSizeHints(self)
       # self.SetScrollRate(1, 1)
        
       # self.box.Add(self.column, 1, wxEXPAND)
       # self.SetSizer(self.box)
       # self.box.Fit(self)
       # self.SetAutoLayout(1)
       self.box = wxBoxSizer(wxVERTICAL)
       self.column = wxFlexGridSizer(cols=1, vgap=1, hgap=0)
       self.column.AddGrowableCol(1)
       self.box.Add(self.column, 1, wxEXPAND|wxTOP |wxBOTTOM, 5)
       
       self.SetSizer(self.box)
       self.box.Fit(self)
       self.SetAutoLayout(1)
             
    def GoToNewVenue(self, event):
        id = event.GetId()
        description = self.exitsDict[id]
        self.app.GoToNewVenue(description.uri)
        		            
    def AddVenueDoor(self, profile):
        #bitmap = icons.getDoorClosedBitmap()
        #bitmapSelect = icons.getDoorOpenBitmap()

        #id = NewId()
        #panel = wxPanel(self, -1,wxDefaultPosition, wxSize(10,50), name ='panel')
        #tc = wxBitmapButton(panel, id, bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
	#tc.SetBitmapSelected(bitmapSelect)
	#tc.SetBitmapFocus(bitmapSelect)
	#tc.SetToolTipString(profile.description)
	#label = wxStaticText(panel, -1, profile.name)
        #b = wxBoxSizer(wxVERTICAL)
        #b.Add(tc, 0, wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
        #b.Add(label, 0, wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
        #panel.SetSizer(b)
        #b.Fit(panel)

        # print "detach all doors"
        # for p in self.doorsAndLabelsList:
        #     self.column.Detach(p)
              
        #self.column.Add(panel, -1, wxEXPAND)

        panel = ExitPanel(self, profile)
        self.doorsAndLabelsList.append(panel)

        self.doorsAndLabelsList.sort(lambda x, y: cmp(x.GetName(), y.GetName()))
        index = self.doorsAndLabelsList.index(panel)
                      
        #self.column.Add(panel, 1, wxEXPAND)
        self.column.Insert(index, panel, 1, wxEXPAND)
               
        #self.box.SetVirtualSizeHints(self)
        
        id = panel.GetButtonId()
        self.exitsDict[id] = profile
        EVT_BUTTON(self, id, self.GoToNewVenue)
        #self.EnableScrolling(true, true)
        
        self.Layout()
        self.parent.Layout()

                            
    def RemoveVenueDoor(self):
        print 'remove venue door'

    def CleanUp(self):
        for item in self.doorsAndLabelsList:
            self.column.Remove(item)
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
    def __init__(self, parent, profile):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 size = wxSize(200,200), style = wxNO_BORDER|wxSW_3D)
        self.id = NewId()
        bitmap = icons.getDoorClosedBitmap()
        bitmapSelect = icons.getDoorOpenBitmap()
        self.button = wxBitmapButton(self, self.id, bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
	self.button.SetBitmapSelected(bitmapSelect)
	self.button.SetBitmapFocus(bitmapSelect)
	self.button.SetToolTipString(profile.description)
	self.label = wxStaticText(self, -1, profile.name)
        self.__layout()

    def GetName(self):
        return self.label.GetLabel()

    def GetButtonId(self):
        return self.id
        
    def __layout(self):
        b = wxBoxSizer(wxVERTICAL)
        b.Add(self.button, 2, wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
        b.Add(self.label, 1,  wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
       
        self.SetSizer(b)
        b.Fit(self)

class ContentListPanel(wxPanel):                   
    '''ContentListPanel.
    
    The contentListPanel represents current venue and has information about all participants 
    in the venue, it also shows what data and services are available in the venue, as well as 
    nodes connected to the venue.  It represents a room, with its contents visible for the user.
    
    '''   
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
     	id = NewId()
        
        self.parent = parent
	self.app = app
	self.tree = wxTreeCtrl(self, id, wxDefaultPosition, \
			       wxDefaultSize,  wxTR_HAS_BUTTONS \
			       | wxTR_NO_LINES  \
                              # | wxTR_TWIST_BUTTONS \
			       | wxTR_HIDE_ROOT)
	
        self.participantDict = {}
        self.dataDict = {}
        self.serviceDict = {}
        self.nodeDict = {}
	self.__setImageList()
	self.__setTree()
	self.__setProperties()
        
        	
	EVT_SIZE(self, self.OnSize)
        EVT_RIGHT_DOWN(self.tree, self.OnRightClick)
        EVT_TREE_KEY_DOWN(self.tree, id, self.OnKeyDown) 
	EVT_LEFT_DOWN(self.tree, self.OnLeftDown)

	
    def __setImageList(self):
	imageList = wxImageList(32,19)
     	self.defaultPersonId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.importantPaperId = imageList.Add(icons.getDefaultDataBitmap())
	self.serviceId = imageList.Add(icons.getDefaultServiceBitmap())
        self.nodeId = imageList.Add(icons.getDefaultNodeBitmap())
	self.tree.AssignImageList(imageList)

    def AddParticipant(self, profile):
        participant = self.tree.AppendItem(self.participants, profile.name, \
                                           self.defaultPersonId, self.defaultPersonId)
        #self.test = self.tree.AppendItem(participants, "data") # , image)
        self.tree.SetItemData(participant, wxTreeItemData(profile)) 
        self.participantDict[profile.publicId] = participant
        self.tree.Expand(self.participants)
           
    def RemoveParticipant(self, description):
        if description!=None :
            id = self.participantDict[description.publicId]
            del self.participantDict[description.publicId]
            self.tree.Delete(id)
        
    def ModifyParticipant(self, description):
        type =  description.profileType
        oldType = None
        id = description.publicId

        if(self.participantDict.has_key(id)):
            oldType = 'user'
            
        elif(self.nodeDict.has_key(id)):
            oldType = 'node'
        
        if(oldType == type):   # just change details
            if type == 'user':
                treeId = self.participantDict[description.publicId]
                profile = self.tree.GetItemData(treeId).GetData()
                self.tree.SetItemText(treeId, description.name)
                profile = description

            else:
                treeId = self.nodeDict[description.publicId]
                profile = self.tree.GetItemData(treeId).GetData()
                self.tree.SetItemText(treeId, description.name)
                profile = description

        elif(oldType != None): # move to new category type
            if type == 'node':
                treeId = self.participantDict[description.publicId]
                self.RemoveParticipant(description)
                self.AddNode(description)
                
            else:
                treeId = self.nodeDict[description.publicId]
                self.RemoveNode(description)
                self.AddParticipant(description)
        
    def AddData(self, profile):
        data = self.tree.AppendItem(self.data, profile.name, \
                             self.importantPaperId, self.importantPaperId)
        self.tree.SetItemData(data, wxTreeItemData(profile)) 
        self.dataDict[profile.name] = data
        self.tree.Expand(self.data)
       
    def UpdateData(self, profile):
        id = self.dataDict[profile.name]
        
        if(id != None):
            self.tree.SetItemData(id, wxTreeItemData(profile))
                          
    def RemoveData(self, profile):
        id = self.dataDict[profile.name]
        
        if(id != None):
            del self.dataDict[profile.name]
            self.tree.Delete(id)
                          
    def AddService(self, profile):
        service = self.tree.AppendItem(self.services, profile.name,\
                                       self.serviceId, self.serviceId)
        self.tree.SetItemData(service, wxTreeItemData(profile)) 
        self.serviceDict[profile.name] = service
        self.tree.Expand(self.services)
      
    def RemoveService(self, profile):
        id = self.serviceDict[profile.name]
        if(id != None):
            del self.serviceDict[profile.name]
            self.tree.Delete(id)

    def AddNode(self, profile):
        node = self.tree.AppendItem(self.nodes, profile.name, \
                                       self.nodeId, self.nodeId)
        self.tree.SetItemData(node, wxTreeItemData(profile)) 
        self.nodeDict[profile.publicId] = node
        self.tree.Expand(self.nodes)

    def RemoveNode(self, profile):
        id = self.nodeDict[profile.publicId]
        self.tree.Delete(id)
        del self.nodeDict[profile.publicId]
        
        
    def __setTree(self):
        self.root = self.tree.AddRoot("The Lobby")
        #image = self.emptyImageId
             
	self.participants = self.tree.AppendItem(self.root, "Participants") # , image)
       
	self.tree.SetItemBold(self.participants)
             
	self.data = self.tree.AppendItem(self.root, "Data") #, image)
	self.tree.SetItemBold(self.data)
             
	self.services = self.tree.AppendItem(self.root, "Services") #, image)
	self.tree.SetItemBold(self.services)
             
	self.nodes = self.tree.AppendItem(self.root, "Nodes") #, image)
	self.tree.SetItemBold(self.nodes)
             
        self.tree.Expand(self.participants)
        self.tree.Expand(self.data)
        self.tree.Expand(self.services)
        self.tree.Expand(self.nodes)
        
    def __setProperties(self):
        self.tree.SetToolTipString("Contents of this venue")

    def UnSelectList(self):
        self.tree.Unselect()

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.tree.SetDimensions(0, 0, w, h)
	
    def OnLeftDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
	self.tree.Unselect() 
	event.Skip()

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
      
        if key == WXK_DELETE:
            treeId = self.tree.GetSelection()
            dataItem = self.tree.GetItemData(treeId).GetData()
            serviceItem = self.tree.GetItemData(treeId).GetData()

            # data
            for object in self.dataDict:
                if dataItem != None and dataItem.name == object:
                    self.app.RemoveData(dataItem)
                    break

            # service
            for object in self.serviceDict:
                if serviceItem != None and serviceItem.name == object:
                    self.app.RemoveService(serviceItem)
                    break
                
    def OnRightClick(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        treeId = self.tree.GetSelection()
        item = self.tree.GetItemData(treeId).GetData()
        text = self.tree.GetItemText(treeId)

        if text == 'Data' or item != None and self.dataDict.has_key(item.name):
            self.PopupMenu(self.parent.dataMenu, wxPoint(self.x, self.y))

        elif text == 'Services' or item != None and self.serviceDict.has_key(item.name):
            self.PopupMenu(self.parent.serviceMenu, wxPoint(self.x, self.y))

        elif text == 'Participants' or text == 'Nodes':
            pass

        elif item != None and self.participantDict.has_key(item.publicId) or \
                 self.nodeDict.has_key(item.publicId):

            if(item.publicId == self.app.profile.publicId):
                self.PopupMenu(self.parent.meMenu, wxPoint(self.x, self.y))

            elif(item.profileType == 'node'):
                self.PopupMenu(self.parent.nodeMenu, wxPoint(self.x, self.y))

            elif(item.profileType == 'user'):
                self.PopupMenu(self.parent.participantMenu, wxPoint(self.x, self.y))

            
    def CleanUp(self):
        for index in self.participantDict.values():
            self.tree.Delete(index)

        for index in self.nodeDict.values():
            self.tree.Delete(index)
        
        for index in self.serviceDict.values():
            self.tree.Delete(index)
        
        for index in self.dataDict.values():
            self.tree.Delete(index)                                   
        
        self.participantDict.clear()
        self.dataDict.clear()
        self.serviceDict.clear()
        self.nodeDict.clear()
                            
  #  def __doLayout(self):
  #      sizer1 = wxBoxSizer(wxVERTICAL)
  #      sizer1.Add(self.text, 0, wxALL, 20)
  #      sizer1.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
  #      self.SetSizer(sizer1)
  #      sizer1.Fit(self)
  #      self.SetAutoLayout(1)
      
class SaveFileDialog(wxDialog):
    def __init__(self, parent, id, title, message, doneMessage, fileSize):
        wxDialog.__init__(self, parent, id, title,
                          size = wxSize(300, 200))

        self.doneMessage = doneMessage

        try:
            self.fileSize = int(fileSize)
        except TypeError:
            print "Received invalid fileSize: '%s'" % (fileSize)
            fileSize = 1
            
        print "created, size=", fileSize
        self.button = wxButton(self, wxNewId(), "Cancel")
        self.text = wxStaticText(self, -1, message)

        self.cancelFlag = 0

        self.progress = wxGauge(self, wxNewId(), 100,
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)

        EVT_BUTTON(self, self.button.GetId(), self.OnButton)

        self.transferDone = 0

        self.__doLayout()

    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 1, wxEXPAND)
        sizer.Add(self.progress, 0, wxEXPAND)
        sizer.Add(self.button, 0, wxCENTER)

        self.SetSizer(sizer)
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
            print "Cancelling transfer!"
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
                          size = wxSize(300, 200))

        self.button = wxButton(self, wxNewId(), "Cancel")
        self.text = wxStaticText(self, -1, "")

        self.cancelFlag = 0

        self.progress = wxGauge(self, wxNewId(), 100,
                                style = wxGA_HORIZONTAL | wxGA_PROGRESSBAR | wxGA_SMOOTH)

        EVT_BUTTON(self, self.button.GetId(), self.OnButton)

        self.transferDone = 0
        self.currentFile = None

        self.__doLayout()

    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer.Add(self.text, 1, wxEXPAND)
        sizer.Add(self.progress, 0, wxEXPAND)
        sizer.Add(self.button, 0, wxCENTER)

        self.SetSizer(sizer)
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
            print "Cancellign transfer!"
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

class MainUrlDialog(wxDialog):
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
       
    def DoLayout(self):
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

class UrlDialogCombo(MainUrlDialog):
    def __init__(self, parent, id, title, address = "", text = None, list = None):
        MainUrlDialog.__init__(self, parent, id, title, address, text)
        self.address = wxComboBox(self, -1, address, size = wxSize(300,20), choices = list)
        self.DoLayout()
     
class UrlDialog(MainUrlDialog):
     def __init__(self, parent, id, title, address = "", text = None):
         MainUrlDialog.__init__(self, parent, id, title, address, text)
         self.address = wxTextCtrl(self, -1, address, size = wxSize(300,20))
         self.DoLayout()

class WelcomeDialog(wxDialog):
    def __init__(self, parent, id, title, name, venueTitle, description):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.okButton = wxButton(self, wxID_OK, "Ok")
        text1 = "Welcome, "+name+", to "+venueTitle
        self.text = wxStaticText(self, -1, text1, style=wxALIGN_LEFT)
        self.description = wxTextCtrl(self, -1, description, \
                                      size = wxSize(300, 100), style = wxTE_MULTILINE )
        self.description.SetBackgroundColour(self.GetBackgroundColour())
        self.__doLayout()
        self.ShowModal()
        self.Destroy()

    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)
        sizer1.Add(self.description, 0, wxEXPAND | wxALL, 20)
        sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
        sizer.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)

    
class ProfileDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20), validator = TextValidator())
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
        self.__doLayout()

    def GetNewProfile(self):
        self.profile.SetName(self.nameCtrl.GetValue())
        self.profile.SetEmail(self.emailCtrl.GetValue())
        self.profile.SetPhoneNumber(self.phoneNumberCtrl.GetValue())
        self.profile.SetTechSupportInfo(self.supportCtrl.GetValue())
        self.profile.SetLocation(self.locationCtrl.GetValue())
        self.profile.SetHomeVenue(self.homeVenueCtrl.GetValue())
        self.profile.SetProfileType(self.profileTypeBox.GetValue())
        return self.profile

    def SetProfile(self, profile):
        self.profile = profile
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], style = wxCB_DROPDOWN)
        self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        self.Layout()
        self.SetTitle("Please, fill in your profile information")
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

    def SetDescription(self, item):
        self.profileTypeBox = wxTextCtrl(self, -1, item.profileType)
        self.gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        self.Layout()
        self.SetTitle("Please, fill in your profile information")
        self.nameCtrl.SetValue(item.name)
        self.emailCtrl.SetValue(item.email)
        self.phoneNumberCtrl.SetValue(item.phoneNumber)
        self.locationCtrl.SetValue(item.location)
        self.supportCtrl.SetValue(item.techSupportInfo)
        self.homeVenueCtrl.SetValue(item.homeVenue)
        self.__setEditable(false)
        # if(item.profileType == 'user'):
        #    self.profileTypeBox.SetSelection(0)
        #else:
        #    self.profileTypeBox.SetSelection(1)

    def __setEditable(self, editable):
        if not editable:
            self.nameCtrl.SetEditable(false)
            self.emailCtrl.SetEditable(false)
            self.phoneNumberCtrl.SetEditable(false)
            self.locationCtrl.SetEditable(false)
            self.supportCtrl.SetEditable(false)
            self.homeVenueCtrl.SetEditable(false)
            self.profileTypeBox.SetEditable(false)
        else:
            self.nameCtrl.SetEditable(true)
            self.emailCtrl.SetEditable(true)
            self.phoneNumberCtrl.SetEditable(true)
            self.locationCtrl.SetEditable(true)
            self.supportCtrl.SetEditable(true)
            self.homeVenueCtrl.SetEditable(true)
            self.profileTypeBox.SetEditable(true)

    def __doLayout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
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

        sizer1.Add(sizer2, 1, wxALL|wxEXPAND, 10)

        sizer3 = wxBoxSizer(wxHORIZONTAL)
        sizer3.Add(self.okButton, 0, wxALL, 10)
        sizer3.Add(self.cancelButton, 0, wxALL, 10)

        sizer1.Add(sizer3, 0, wxALIGN_CENTER)

        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
                
class TextValidator(wxPyValidator):
    def __init__(self):
        wxPyValidator.__init__(self)
            
    def Clone(self):
        return TextValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
              
        if len(val) < 1:
            wxMessageBox("Please, fill in the name field", "Error")
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

 
class AddServiceDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.Centre()
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20))
        self.descriptionText = wxStaticText(self, -1, "Description:", style=wxALIGN_LEFT)
        self.descriptionCtrl = wxTextCtrl(self, -1, "")
        self.uriText = wxStaticText(self, -1, "Location URL:", style=wxALIGN_LEFT | wxTE_MULTILINE )
        self.uriCtrl = wxTextCtrl(self, -1, "")
        self.typeText = wxStaticText(self, -1, "Mime Type:")
        self.typeCtrl = wxTextCtrl(self, -1, "")
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__setProperties()
        self.__doLayout()

    def GetNewProfile(self):
        service = ServiceDescription('service', 'service', 'uri', 'icon', 'storagetype')
        service.SetName(self.nameCtrl.GetValue())
        service.SetDescription(self.descriptionCtrl.GetValue())
        service.SetURI(self.uriCtrl.GetValue())
        service.SetMimeType(self.typeCtrl.GetValue())
        return service

    def __setProperties(self):
        self.SetTitle("Please, fill in service information")
              
    def __doLayout(self):
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

 
class FileDropTarget(wxFileDropTarget):
    def __init__(self, dock):
        wxFileDropTarget.__init__(self)
        self.dock = dock
        self.do = wxFileDataObject()
        self.SetDataObject(self.do)
        
    def OnDropFiles(self, x, y, filenames):
        print 'on drop files'
        for file in filenames:
            fileNameList = file.split('/')
            fileName = fileNameList[len(fileNameList)-1]
            self.dock.AddSimpleTool(20, icons.getDefaultDataBitmap(), fileName)
        return true

    def OnData(self, x, y, d):
        print 'on data'
        self.GetData()
        files = self.do.GetFilenames()
        for file in files:
            fileNameList = file.split('/')
            fileName = fileNameList[len(fileNameList)-1]
            self.dock.AddSimpleTool(20, icons.getDefaultDataBitmap(), fileName)
        return d
        


'''VenueClient. 

The VenueClient class creates the main frame of the application, the VenueClientFrame. 

'''
if __name__ == "__main__":
   
    import time
    
    class TheGrid(wxApp):
        def OnInit(self, venueClient = None):
            self.frame = VenueClientFrame(NULL, -1,"The Lobby")
            self.frame.Show(true)
            self.frame.SetSize(wxSize(300, 400))
            self.SetTopWindow(self.frame)
            self.client = venueClient
            re
