#-----------------------------------------------------------------------------
# Name:        VenueClientUIClasses.py
# Purpose:     
#
# Author:      Susanne Lefvert
#
# Created:     2003/08/02
# RCS-ID:      $Id: VenueClientUIClasses.py,v 1.28 2003-02-14 21:13:52 olson Exp $
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

from AccessGrid.NodeManagementUIClasses import NodeManagementClientFrame

class VenueClientFrame(wxFrame):
    
    '''VenueClientFrame. 

    The VenueClientFrame is the main frame of the application, creating statusbar, toolbar,
    venueListPanel, and contentListPanel.  The contentListPanel represents current venue and
    has information about all participants in the venue, it also shows what data and services 
    are available in the venue, as well as nodes connected to the venue.  It represents a room
    with its contents visible for the user.  The venueListPanel contains a list of connected 
    venues/exits to current venue.  By clicking on a door icon the user travels to another 
    venue/room, which contents will be shown in the contentListPanel.
    
    '''	
    def __init__(self, parent, id, title, app = None):
        wxFrame.__init__(self, parent, id, title)
	self.app = app
        self.parent = parent
	self.menubar = wxMenuBar()
	self.statusbar = self.CreateStatusBar(1)
	self.toolbar = wxToolBar(self, 600,wxDefaultPosition,wxDefaultSize, wxTB_TEXT| \
		  wxTB_HORIZONTAL| wxTB_FLAT)
	self.venueListPanel = VenueListPanel(self, app) 
	self.contentListPanel = ContentListPanel(self, app)
        self.myVenuesList = []
        self.myVenuesFile = os.path.join(self.app.accessGridPath, "myVenues.txt" )
        self.__setStatusbar()
	self.__setMenubar()
	self.__setToolbar()
	self.__setProperties()
        self.__doLayout()
        self.__setEvents()

    def __setStatusbar(self):
        self.statusbar.SetToolTipString("Statusbar")   
    
    def __setMenubar(self):
        self.SetMenuBar(self.menubar)

       # self.ID_VENUE = NewId() 
        self.ID_VENUE_DATA = NewId() 
        self.ID_VENUE_DATA_ADD = NewId() 
        self.ID_VENUE_DATA_SAVE = NewId() 
        self.ID_VENUE_DATA_DELETE = NewId() 
        self.ID_VENUE_SERVICE = NewId() 
        self.ID_VENUE_SERVICE_ADD = NewId()
        self.ID_VENUE_SERVICE_DELETE = NewId()
        self.ID_VENUE_VIRTUAL = NewId()
        self.ID_VENUE_CLOSE = NewId()
        self.ID_PROFILE = NewId()
        self.ID_PROFILE_EDIT = NewId()
        #self.ID_MYNODE = NewId()
        self.ID_MYNODE_MANAGE = NewId()
        self.ID_MYNODE_URL = NewId()
        self.ID_MYVENUE_ADD = NewId()
        self.ID_HELP = NewId()
        self.ID_HELP_ABOUT = NewId()
      
        self.venue = wxMenu()
	self.dataMenu = wxMenu()
	self.dataMenu.Append(self.ID_VENUE_DATA_ADD,"Add...", "Add data to the venue")
	self.dataMenu.Append(self.ID_VENUE_DATA_SAVE,"Save...", "Save data to local disk")
	self.dataMenu.Append(self.ID_VENUE_DATA_DELETE,"Delete", "Remove data")
        #self.dataMenu.Append(223,"Profile")
	self.venue.AppendMenu(self.ID_VENUE_DATA,"&Data", self.dataMenu)
	self.serviceMenu = wxMenu()
	self.serviceMenu.Append(self.ID_VENUE_SERVICE_ADD,"Add...", "Add service to the venue")
        self.serviceMenu.Append(self.ID_VENUE_SERVICE_DELETE,"Delete", "Delete service")
        #self.serviceMenu.Append(233,"Profile")
	self.venue.AppendMenu(self.ID_VENUE_SERVICE,"&Services",self.serviceMenu)
	self.menubar.Append(self.venue, "&Venue")
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_VIRTUAL,"Open virtual venue...",  "Go to new venue")
        self.venue.AppendSeparator()
        self.venue.Append(self.ID_VENUE_CLOSE, 'Close', "Exit venue")
	
	self.edit = wxMenu()
	self.edit.Append(self.ID_PROFILE, "&Profile...", "Change your personal information")
        self.menubar.Append(self.edit, "&Edit")
        self.myNode = wxMenu()
        self.myNode.Append(self.ID_MYNODE_MANAGE, "&Manage...", "Configure your node")
        self.myNode.Append(self.ID_MYNODE_URL, "&Set URL...", "Specify URL address to node service")
        #self.myNode = wxMenu()
        # self.myNode.Append(500, "Add")
        self.menubar.Append(self.myNode, "My &Node")
        self.myVenues = wxMenu()
        self.myVenues.Append(self.ID_MYVENUE_ADD, "&Add...", "Configure your node")
       
        self.__loadMyVenues()
        self.menubar.Append(self.myVenues, "My &Venues")
        
      
	self.help = wxMenu()
	#self.help.Append(301, "Manual")
	self.help.Append(self.ID_HELP_ABOUT, "About", "Information about the application")
        self.menubar.Append(self.help, "&Help")
     
    def __setEvents(self):
        EVT_MENU(self, self.ID_VENUE_DATA_ADD, self.OpenAddDataDialog)
        EVT_MENU(self, self.ID_VENUE_DATA_SAVE, self.SaveData)
        EVT_MENU(self, self.ID_VENUE_DATA_DELETE, self.RemoveData)
        EVT_MENU(self, self.ID_VENUE_SERVICE_ADD, self.OpenAddServiceDialog)
        #EVT_MENU(self, 223, self.OpenDataProfileDialog)
        #EVT_MENU(self, 233, self.OpenServiceProfileDialog)
        EVT_MENU(self, self.ID_VENUE_SERVICE_DELETE, self.RemoveService)
        EVT_MENU(self, self.ID_PROFILE, self.OpenProfileDialog)
        EVT_MENU(self, self.ID_HELP_ABOUT, self.OpenAboutDialog)
        EVT_MENU(self, self.ID_VENUE_VIRTUAL, self.OpenConnectToVenueDialog)
        EVT_MENU(self, self.ID_MYNODE_MANAGE, self.OpenNodeMgmtApp)
        EVT_MENU(self, self.ID_MYNODE_URL, self.OpenSetNodeUrlDialog)
        EVT_MENU(self, self.ID_MYVENUE_ADD, self.AddToMyVenues)
        EVT_MENU(self, self.ID_VENUE_CLOSE, self.Exit)
        
    def __setToolbar(self):
        """
	self.toolbar.AddSimpleTool(20, icons.getWordBitmap(), \
                                   "ImportantPaper.doc", "ImportantPaper.doc",)
	self.toolbar.AddSimpleTool(21, icons.getPowerPointBitmap(), \
                                   "Presentation.ppt", "Presentation.ppt",)
        """
        pass
       	
    def __setProperties(self):
        self.SetTitle("Access Grid - The Lobby")
        self.SetIcon(icons.getAGIconIcon())
        self.statusbar.SetStatusWidths([-1])
	self.statusbar.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.menubar.SetFont(wxFont(12, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	currentHeight = self.venueListPanel.GetSize().GetHeight()
	self.venueListPanel.SetSize(wxSize(100, 300))
		
    def __doLayout(self):
        self.venueClientSizer = wxBoxSizer(wxVERTICAL)
        self.venueContentSizer = wxBoxSizer(wxHORIZONTAL)
	self.venueContentSizer.Add(self.venueListPanel, 0, wxEXPAND)
	self.venueContentSizer.Add(self.contentListPanel, 2, wxEXPAND)
	self.venueClientSizer.Add(self.venueContentSizer, 2, wxEXPAND)
	self.venueClientSizer.Add(self.toolbar)

	self.SetSizer(self.venueClientSizer)
	self.venueClientSizer.Fit(self)
	self.SetAutoLayout(1)

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
            self.myVenues.Append(id, url)
            EVT_MENU(self, id, self.ConnectToMyVenue)

    def AddToMyVenues(self, event):
        setMyVenueUrlDialog = UrlDialog(self, -1, "Add venue URL to your venues", \
                                        '', "Please, specify the URL of the venue you want to add to\nyour venues")
        if setMyVenueUrlDialog.ShowModal() == wxID_OK:
            id = NewId()
            url = setMyVenueUrlDialog.address.GetValue()
            self.myVenues.Append(id, url)
            self.myVenuesList.append(url)
            EVT_MENU(self, id, self.ConnectToMyVenue)

            myVenuesFile = open(self.myVenuesFile, 'w')
            for venueUrl in self.myVenuesList:
                myVenuesFile.write(venueUrl+'\n')
            myVenuesFile.close()
                                   
        setMyVenueUrlDialog.Destroy()
                       
    def Exit(self, event):
        '''
        Called when the window is closed using the built in close button
        '''
        self.app.OnExit()
                     	      
    def UpdateLayout(self):
        self.__doLayout()

    def OpenSetNodeUrlDialog(self, event = None):

        setNodeUrlDialog = UrlDialog(self, -1, "Please, specify node service URL", self.app.nodeServiceUri)

        if setNodeUrlDialog.ShowModal() == wxID_OK:
            self.app.SetNodeUrl(setNodeUrlDialog.address.GetValue())

        setNodeUrlDialog.Destroy()
                
    def OpenAddDataDialog(self, event = None):
        dlg = wxFileDialog(self, "Choose a file:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            print "Got files: ", files

            # upload!

            self.app.UploadFiles(files)

                
            # data = DataDescription(dlg.GetFilename(), dlg.GetPath(), 'uri', 'icon', 'storagetype')
            # self.app.AddData(data)

        dlg.Destroy()

    def OpenProfileDialog(self, event):
        profileDialog = ProfileDialog(NULL, -1, 'Please, fill in your profile', self.app.profile)
           
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
        if frame.Connected():
            frame.Update()
            frame.Show(true)
                
    def OpenDataProfileDialog(self, event):
        self.contentList.tree.GetSelection()
        profileDialog = ProfileDialog(NULL, -1, 'Profile', self.app.profile)
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
        data =  self.contentListPanel.tree.GetItemData(id).GetData()

        print "Removing data ", data
        
        if(data != None):
            self.app.RemoveData(data)

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
        self.venueListPanel.CleanUp()
        self.contentListPanel.CleanUp()
        

class VenueListPanel(wxPanel):
    '''VenueListPanel. 
    
    The venueListPanel contains a list of connected venues/exits to current venue.  
    By clicking on a door icon the user travels to another venue/room, 
    which contents will be shown in the contentListPanel.  By moving the mouse over
    a door/exit information about that specific venue will be shown as a tooltip.
    The user can close the venueListPanel if exits/doors are irrelevant to the user and
    the application will extend the contentListPanel.  The panels is separated into a 
    panel containing the close/open buttons and a VenueList object containing the exits.
    '''   
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1)
	self.parent = parent
        self.app = app
       
	self.list = VenueList(self, app)
        self.minimizeButton = wxButton(self, 10, "<<", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.minimizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.maximizeButton = wxButton(self, 20, ">>", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.maximizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
        self.minimizeButton.SetToolTipString("Hide Exits")
	self.maximizeButton.SetToolTipString("Show Exits")
	self.maximizeButton.Hide()
        self.exitsText = wxButton(self, -1, "Exits", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
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

	self.SetSizer(venueListPanelSizer)
        venueListPanelSizer.Fit(self)
	self.SetAutoLayout(1)  

    def OnClick(self, event):
	currentHeight = self.GetSize().GetHeight()
	parentSize = self.parent.GetSize()
        if event.GetId() == 10:
		self.minimizeButton.Hide()  
		self.maximizeButton.Show()
		self.list.HideDoors()
		self.SetSize(wxSize(20, currentHeight))
		self.Layout()
                self.parent.UpdateLayout()
		self.parent.SetSize(parentSize)
					
	if event.GetId() == 20:
		self.maximizeButton.Hide()
		self.minimizeButton.Show()  
		self.list.ShowDoors()
		self.SetSize(wxSize(100, currentHeight))
                self.parent.UpdateLayout()
	        self.parent.SetSize(parentSize)

    def CleanUp(self):
        self.list.CleanUp()


class VenueList(wxScrolledWindow):
    '''VenueList. 
    
    The venueList is a scrollable window containing all exits to current venue.
    
    '''   
    def __init__(self, parent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1, style = wxRAISED_BORDER)
        
        #self.list = wxListCtrl(self, -1, style = wxLC_ICON)
        #self.list.Show(true)
        #self.list.SetBackgroundColour(parent.GetBackgroundColour())
        #self.imageList = wxImageList(16, 16)
        #self.doorOpenId = self.imageList.Add(icons.getDoorOpenBitmap())
        #self.doorCloseId = self.imageList.Add(icons.getDoorCloseBitmap())
        #self.list.SetImageList(self.imageList, wxIMAGE_LIST_NORMAL)
        #exit = wxListItem()
        #exit.SetText('test')
        #self.list.InsertItem(exit)
        # self.list.SetStringItem(0,0,'test', door)
        self.doorsAndLabelsList = []
        self.exitsDict = {}
        self.__doLayout()
        self.EnableScrolling(true, false)

    def __doLayout(self):
        self.box = wxBoxSizer(wxVERTICAL)
        # box.Add(self.list, 1, wxEXPAND)

        self.column = wxFlexGridSizer(cols=1, vgap=5, hgap=0)
        self.column.AddGrowableCol(1)
	       
        self.column.Add(40, 5)   
        #self.EnableScrolling(true, false)
        #self.SetScrollRate(0, 20)
        self.box.SetVirtualSizeHints(self)
        #self.SetScrollRate(20, 20)
        
        self.box.Add(self.column, 1, wxEXPAND)
        self.SetSizer(self.box)
        self.box.Fit(self)
        self.SetAutoLayout(1)  

    def GoToNewVenue(self, event):
        id = event.GetId()
        description = self.exitsDict[id]
        self.app.GoToNewVenue(description.uri)
        		            
    def AddVenueDoor(self, profile):
        #id = wxNewId()
        #exit = wxListItem()
        #self.list.InsertImageStringItem(0,"LABEL",self.doorOpenId)

        bitmap = icons.getDoorClosedBitmap()
        bitmapSelect = icons.getDoorOpenBitmap()

        id = NewId()
        panel = wxPanel(self, -1,wxDefaultPosition, wxSize(10,50), name ='panel')
        tc = wxBitmapButton(panel, id, bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
	tc.SetBitmapSelected(bitmapSelect)
	tc.SetBitmapFocus(bitmapSelect)
	tc.SetToolTipString(profile.description)
	label = wxStaticText(panel, -1, profile.name)
        b = wxBoxSizer(wxVERTICAL)
        b.Add(tc, 0, wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
        b.Add(label, 0, wxALIGN_LEFT|wxLEFT|wxRIGHT, 5)
        panel.SetSizer(b)
        b.Fit(panel)
        panel.SetAutoLayout(1)
        
        self.column.Add(panel, -1, wxEXPAND)
        self.doorsAndLabelsList.append(panel)
        
	self.SetSize(wxDefaultSize)
	self.Layout()
	self.box.SetVirtualSizeHints(self)
        self.exitsDict[id] = profile
        EVT_BUTTON(self, id, self.GoToNewVenue)
               
    def RemoveVenueDoor(self):
        print 'remove venue door'

    def CleanUp(self):
        for item in self.doorsAndLabelsList:
            self.column.Remove(item)
            item.Destroy()

        self.exitsDict.clear()
        del self.doorsAndLabelsList[0:]
              
    def HideDoors(self):
        self.EnableScrolling(false, false)
        for item in self.doorsAndLabelsList:
            self.column.Hide(item)

    def ShowDoors(self):
        self.EnableScrolling(true, false)
        for item in self.doorsAndLabelsList:
            self.column.Show(item)
                   

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
        # self.emptyImageId = imageList.Add(icons.getEmptyBitmap())
	self.defaultPersonId = imageList.Add(icons.getDefaultParticipantBitmap())
        self.importantPaperId = imageList.Add(icons.getDefaultDataBitmap())
	self.serviceId = imageList.Add(icons.getDefaultServiceBitmap())
        self.nodeId = imageList.Add(icons.getDefaultNodeBitmap())
	self.tree.AssignImageList(imageList)

    def AddParticipant(self, profile):
        participant = self.tree.AppendItem(self.participants, profile.name, \
                                           self.defaultPersonId, self.defaultPersonId)
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
                            
    def __doLayout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer1.Add(self.text, 0, wxALL, 20)
        sizer1.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
        self.SetSizer(sizer1)
        sizer1.Fit(self)
        self.SetAutoLayout(1)
      
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
            print "Cancellign transfer!"
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

        value = int(100 * int(bytes_sent) / int(bytes_total))
        self.progress.SetValue(value)

#class ConnectToServerDialog(wxDialog):
#   def __init__(self, parent, id, title):
 #       wxDialog.__init__(self, parent, id, title)
 #       self.okButton = wxButton(self, wxID_OK, "Ok")
 #       self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
 #       info = "Please, enter server URL address.\nYou will open default venue on the server."
 #       self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
 #       self.addressText = wxStaticText(self, -1, "Address: ", style=wxALIGN_LEFT)
 #       self.address = wxTextCtrl(self, -1, "", size = wxSize(300,20))
 #       self.__doLayout()

  #  def __doLayout(self):
  #      sizer = wxBoxSizer(wxVERTICAL)
  #      sizer1 = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
  #      sizer1.Add(self.text, 0, wxLEFT|wxRIGHT|wxTOP, 20)

    #    sizer2 = wxBoxSizer(wxHORIZONTAL)
    #    sizer2.Add(self.addressText, 0)
    #    sizer2.Add(self.address, 1, wxEXPAND)

   #     sizer1.Add(sizer2, 0, wxEXPAND | wxALL, 20)

   #     sizer3 =  wxBoxSizer(wxHORIZONTAL)
   #     sizer3.Add(self.okButton, 0, wxALIGN_CENTER | wxALL, 10)
   #     sizer3.Add(self.cancelButton, 0, wxALIGN_CENTER | wxALL, 10)

  #      sizer.Add(sizer1, 0, wxALIGN_CENTER | wxALL, 10)
  #      sizer.Add(sizer3, 0, wxALIGN_CENTER)
  #      self.SetSizer(sizer)
  #      sizer.Fit(self)
  #      self.SetAutoLayout(1)

class MainUrlDialog(wxDialog):
    def __init__(self, parent, id, title, address = "", text = None):
        wxDialog.__init__(self, parent, id, title)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        if text == None:
            info = "Please, enter venue URL address"
        else:
            info = text
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Address: ", style=wxALIGN_LEFT)
        #self.address = wxTextCtrl(self, -1, address, size = wxSize(300,20))
        #self.__doLayout()

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
    def __init__(self, parent, id, title, profile):
        wxDialog.__init__(self, parent, id, title)
        self.profile = profile
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
        self.homeVenue = wxStaticText(self, -1, "Home Venue:")
        self.homeVenueCtrl = wxTextCtrl(self, -1, "")
        self.profileTypeText = wxStaticText(self, -1, "Profile Type:", style=wxALIGN_LEFT)
        self.profileTypeBox = wxComboBox(self, -1, choices =['user', 'node'], style = wxCB_DROPDOWN)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__setProperties()
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

    def __setProperties(self):
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

    def __doLayout(self):
        sizer1 = wxBoxSizer(wxVERTICAL)
        sizer2 = wxStaticBoxSizer(wxStaticBox(self, -1, "Profile"), wxHORIZONTAL)
        gridSizer = wxFlexGridSizer(9, 2, 5, 5)
        gridSizer.Add(self.nameText, 1, wxALIGN_LEFT, 0)
        gridSizer.Add(self.nameCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.emailText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.emailCtrl, 2, wxEXPAND, 0)
        gridSizer.Add(self.phoneNumberText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.phoneNumberCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.locationText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.locationCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.supportText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.supportCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.homeVenue, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.homeVenueCtrl, 0, wxEXPAND, 0)
        gridSizer.Add(self.profileTypeText, 0, wxALIGN_LEFT, 0)
        gridSizer.Add(self.profileTypeBox, 0, wxEXPAND, 0)
        sizer2.Add(gridSizer, 1, wxALL, 10)

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
            return true
        
        def AddParticipant(self, profile):
            self.frame.contentListPanel.AddParticipant(profile)
     
        def RemoveParticipant(self):
            self.frame.contentListPanel.RemoveParticipant()

        def AddData(self, profile):
            self.frame.contentListPanel.AddData(profile)

        def RemovData(self):
            self.frame.contentListPanel.RemoveData()

        def AddService(self, profile):
            self.frame.contentListPanel.AddService(profile)

        def RemoveService(self):
            self.frame.contentListPanel.RemoveService()

        def AddNode(self, profile):
            self.frame.contentListPanel.AddNode(profile)

        def RemoveNode(self):
            self.frame.contentListPanel.RemoveNode()

        def ExpandTree(self):
            self.frame.contentListPanel.ExpandTree()

        def AddExit(self, profile):
            self.frame.venueListPanel.list.AddVenueDoor(profile.name, " ", \
                                                        icons.getDoorClosedBitmap(), \
                                                        icons.getDoorOpenBitmap()) 
            
        def RemoveExit(self):
            print 'remove exit'

    app = TheGrid()
    app.MainLoop()
