from wxPython.wx import *
from wxPython.lib.buttons import *
from AccessGrid import icons
from AccessGrid.VenueClient import VenueClient
import threading
from AccessGrid import Utilities
import AccessGrid.ClientProfile


'''VenueClientFrame. 

The VenueClientFrame is the main frame of the application, creating statusbar, toolbar,
venueListPanel, and contentListPanel.  The contentListPanel represents current venue and
has information about all participants in the venue, it also shows what data and services 
are available in the venue, as well as nodes connected to the venue.  It represents a room
with its contents visible for the user.  The venueListPanel contains a list of connected 
venues/exits to current venue.  By clicking on a door icon the user travels to another 
venue/room, which contents will be shown in the contentListPanel.

'''	
class VenueClientFrame(wxFrame):
    def __init__(self, parent, id, title, app = None):
        wxFrame.__init__(self, parent, id, title)
	self.app = app
	self.menubar = wxMenuBar()
	self.statusbar = self.CreateStatusBar(1)
	self.toolbar = wxToolBar(self, -1,wxDefaultPosition,wxDefaultSize, wxTB_TEXT| \
		  wxTB_HORIZONTAL| wxTB_FLAT)
	self.venueListPanel = VenueListPanel(self, app) 
	self.contentListPanel = ContentListPanel(self, app)
	
	self. __setStatusbar()
	self.__setMenubar()
	self.__setToolbar()
	self.__setProperties()
        self.__doLayout()
	
    def __setStatusbar(self):
        self.statusbar.SetToolTipString("Statusbar")   

    def __setMenubar(self):
        self.SetMenuBar(self.menubar)

        self.venue = wxMenu()
	self.dataSubmenu = wxMenu()
	self.dataSubmenu.Append(221,"Add")
	self.dataSubmenu.Append(221,"Modify")
	self.dataSubmenu.Append(221,"Delete")
	self.venue.AppendMenu(220,"&Data",self.dataSubmenu)
	self.serviceSubmenu = wxMenu()
	self.serviceSubmenu.Append(221,"Add")
	self.serviceSubmenu.Append(221,"Modify")
	self.serviceSubmenu.Append(221,"Delete")
	self.venue.AppendMenu(220,"&Services",self.serviceSubmenu)
	self.menubar.Append(self.venue, "&Venue")
	
	self.edit = wxMenu()
	self.edit.Append(200, "Profile", "Change your profile")
        self.menubar.Append(self.edit, "&Edit")

	self.help = wxMenu()
	self.help.Append(301, "Manual")
	self.help.Append(302, "About", "Information about developers and application")
        self.menubar.Append(self.help, "&Help")
	
    def __setToolbar(self):
	self.toolbar.AddSimpleTool(20, icons.getWordIconBitmap(), "ImportantPaper.doc", "ImportantPaper.doc",)
	self.toolbar.AddSimpleTool(21, icons.getPptIconBitmap(), "Presentation.ppt", "Presentation.ppt",)
	
    def __setProperties(self):
        self.SetTitle("Access Grid - The Lobby")
	bitmap = icons.getDefaultPersonIconBitmap()
	icon = wxIcon("future icon", -1)
	self.SetIcon(icon)
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
	      
    def UpdateLayout(self):
        self.__doLayout()
     

'''VenueListPanel. 

The venueListPanel contains a list of connected venues/exits to current venue.  
By clicking on a door icon the user travels to another venue/room, 
which contents will be shown in the contentListPanel.  By moving the mouse over
a door/exit information about that specific venue will be shown as a tooltip.
The user can close the venueListPanel if exits/doors are irrelevant to the user and
the application will extend the contentListPanel.  The panels is separated into a 
panel containing the close/open buttons and a VenueList object containing the exits.
'''   
class VenueListPanel(wxPanel):
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1)
	self.parent = parent
        self.app = app
	self.list = VenueList(self, app)
      
   	self.minimizeButton = wxButton(self, 10, "<<", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.minimizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.maximizeButton = wxButton(self, 20, ">>", wxDefaultPosition, wxDefaultSize, wxBU_EXACTFIT )
	self.maximizeButton.SetFont(wxFont(5, wxSWISS, wxNORMAL, wxNORMAL, 0, "adventure"))
	self.minimizeButton.SetToolTipString("Hide Sidebar")
	self.maximizeButton.SetToolTipString("Show Sidebar")
	self.maximizeButton.Hide()
	self.SetBackgroundColour(self.maximizeButton.GetBackgroundColour())
        print 'siiiiiiiiiiiiiiiiiiiiiiiiiiiiiize'
      	print self.GetSize().width
	self.imageList = wxImageList(16,16)
	self.__doLayout()
	self.__addEvents()
	self.__insertItems()
	
    def __insertItems(self):
    	self.SetToolTipString("Connected Venues")
	self.iconId =  self.imageList.Add(icons.getDoorOpenBitmap())
		
    def __addEvents(self):
        EVT_BUTTON(self, 10, self.OnClick) 
        EVT_BUTTON(self, 20, self.OnClick) 

    def __doLayout(self):
        panelSizer = wxBoxSizer(wxHORIZONTAL)
	panelSizer.Add(self.maximizeButton, 0)
	panelSizer.Add(50,10, wxEXPAND)
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
		self.list.Hide()
		self.SetSize(wxSize(20, currentHeight))
		self.Layout()
		self.parent.UpdateLayout()
		self.parent.SetSize(parentSize)
					
	if event.GetId() == 20:
		self.maximizeButton.Hide()
		self.minimizeButton.Show()  
		self.list.Show()
		self.SetSize(wxSize(100, currentHeight))
		self.parent.UpdateLayout()
	        self.parent.SetSize(parentSize)

'''VenueList. 

The venueList is a scrollable window containing all exits to current venue.

'''   
class VenueList(wxScrolledWindow):
    def __init__(self, parent, app):
        self.app = app
        wxScrolledWindow.__init__(self, parent, -1, style = wxRAISED_BORDER)
        self.list = wxListCtrl(self, -1, style = wxLC_ICON)
        self.list.SetBackgroundColour(parent.GetBackgroundColour())
        self.imageList = wxImageList(16, 16)
        door = self.imageList.Add(icons.getDoorOpenBitmap())
        self.list.SetImageList(self.imageList, wxIMAGE_LIST_NORMAL,)
        exit = wxListItem()
        exit.SetText('test')
       # self.list.SetStringItem(0,0,'test', door)
        self.__doLayout()

    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
        box.Add(self.list, 1, wxEXPAND)
        self.SetSizer(box)
        box.Fit(self)
        self.SetAutoLayout(1)  

        
#	self.column = wxFlexGridSizer(cols=1, vgap=1, hgap=0)
#        self.column.AddGrowableCol(1)
	
#	self.box.Add(self.column, 1)
#	self.column.Add(40, 5)   
#	self.SetSizer(self.box)
 #       self.EnableScrolling(true, false)
 #       self.SetScrollRate(0, 20)
 #       self.box.SetVirtualSizeHints(self)
#	self.EnableScrolling(true, true)
  #      self.SetScrollRate(20, 20)
		            
    def AddVenueDoor(self, profile):
        print 'add venue door'
       # bitmap = icons.getDoorCloseBitmap()
        #bitmapSelect = icons.getDoorOpenBitmap()
            
       # tc = wxBitmapButton(self, -1, bitmap, wxPoint(0, 0), wxDefaultSize, wxBU_EXACTFIT)
#	tc.SetBitmapSelected(bitmapSelect)
#	tc.SetBitmapFocus(bitmapSelect)
#	tc.SetToolTipString(profile.description)
#	label = wxStaticText(self, -1, profile.name)
#
	#self.column.Add(tc, 0, wxALIGN_CENTER|wxLEFT|wxRIGHT, 5)
	#self.column.Add(label, 0, wxALIGN_CENTER|wxLEFT|wxRIGHT, 5)
	#self.column.Add(40, 5)   
#	self.SetSize(wxDefaultSize)
#	self.Layout()
	#self.box.SetVirtualSizeHints(self)

    def RemoveVenueDoor(self):
        print 'remove venue door'
	

'''ContentListPanel.
 
The contentListPanel represents current venue and has information about all participants 
in the venue, it also shows what data and services are available in the venue, as well as 
nodes connected to the venue.  It represents a room, with its contents visible for the user.
 
'''   
class ContentListPanel(wxPanel):
    def __init__(self, parent, app):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
     	id = NewId()
	self.app = app
	self.tree = wxTreeCtrl(self, id, wxDefaultPosition, \
			       wxDefaultSize,  wxTR_HAS_BUTTONS \
			       | wxTR_NO_LINES | wxTR_TWIST_BUTTONS \
			       | wxTR_HIDE_ROOT)
	
        self.participantDict = {}
        self.dataDict = {}
        self.serviceDict = {}
        self.nodeDict = {}
	self.__setImageList()
	self.__setTree()
	self.__setProperties()
        	
	EVT_SIZE(self, self.OnSize)
#	EVT_TREE_SEL_CHANGED(self, id, self.OnSelChanged)
	EVT_LEFT_DOWN(self.tree, self.OnLeftDown)
	
    def __setImageList(self):
#	wxInitAllImageHandlers()
	imageList = wxImageList(16,16)  
#	service = wxBitmap('IMAGES/service.bmp', wxBITMAP_TYPE_BMP)
#	smileyOn = wxBitmap('IMAGES/smileyOn.jpg', wxBITMAP_TYPE_JPEG)
#	smileySelect = wxBitmap('IMAGES/smileySelect.jpg', wxBITMAP_TYPE_JPEG)

	newImageList = wxImageList(16,16) 
#	self.arrow = imageList.Add(wxBitmap("IMAGES/rightArrow.gif"))
	self.defaultPersonId = imageList.Add(icons.getDefaultPersonIconBitmap())
	self.pptDocId = imageList.Add(icons.getPptIconBitmap())
	self.importantPaperId = imageList.Add(icons.getWordIconBitmap())
	self.serviceId = imageList.Add(icons.getVoyagerIconBitmap())
	self.iconId = imageList.Add(icons.getDefaultPersonIconBitmap())  
	#self.smileyOnId =  imageList.Add(smileyOn)
	#self.smileySelectId =  imageList.Add(smileySelect)
	self.tree.AssignImageList(imageList)

    def AddParticipant(self, profile):
        print "---------------"
        print "in venue client"
        print profile.name
        participant = self.tree.AppendItem(self.participants, profile.name, \
                             self.iconId, self.iconId)
        self.tree.SetPyData(participant, profile)
        self.participantDict[profile.name] = participant
        self.tree.Expand(self.participants)
    
    def RemoveParticipant(self):
        id = self.participantDict['New Person']
        self.tree.Delete(id)
        
    def AddData(self, profile):
        name = "ImportantPaper.doc"
        data = self.tree.AppendItem(self.data, name, \
                             self.importantPaperId, self.importantPaperId)
        self.tree.SetPyData(data, profile)
        self.dataDict[name] = data
        self.tree.Expand(self.data)
       
    def RemoveData(self):
        id = self.dataDict["ImportantPaper.doc"]
        self.tree.Delete(id)
       
    def AddService(self, profile):
        name = "Voyager"
        service = self.tree.AppendItem(self.services, name,\
                                       self.serviceId, self.serviceId)
        self.tree.SetPyData(service, profile)
        self.serviceDict[name] = service
        self.tree.Expand(self.services)
      
    def RemoveService(self):
        id = self.serviceDict["Voyager"]
        self.tree.Delete(id)

    def AddNode(self, profile):
        name = "Library Node"
        node = self.tree.AppendItem(self.nodes, name)
        self.tree.SetPyData(node, profile)
        self.nodeDict[name] = node
        self.tree.Expand(self.nodes)

    def RemoveNode(self):
        id = self.nodeDict["Library Node"]
        self.tree.Delete(id)

    def __setTree(self):
        self.root = self.tree.AddRoot("The Lobby")
        self.tree.SetPyData(self.root, 1)
        
	self.participants = self.tree.AppendItem(self.root, "Participants")
	self.tree.SetItemBold(self.participants)
        self.tree.SetPyData(self.participants, 1)
        
	self.data = self.tree.AppendItem(self.root, "Data")
	self.tree.SetItemBold(self.data)
        self.tree.SetPyData(self.data, 1)
        
	self.services = self.tree.AppendItem(self.root, "Services")
	self.tree.SetItemBold(self.services)
        self.tree.SetPyData(self.services, 1)
        
	self.nodes = self.tree.AppendItem(self.root, "Nodes")
	self.tree.SetItemBold(self.nodes)
        self.tree.SetPyData(self.nodes, 1)
        
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

    def OnSelChanged(self, event):
        self.item = event.GetEventObject()
     	infoPopup = InfoPopup(self, wxSIMPLE_BORDER)
	object = event.GetEventObject()
	size =  object.GetSize()
	position  = object.ClientToScreen((150, 0 - size.height + self.y - 50))
	infoPopup.Position(position, (0, size.height))
	infoPopup.Popup()


class ErrorDialog:
   def __init__(self, frame, text):
       (name, args, traceback_string_list) = Utilities.formatExceptionInfo()
       for x in traceback_string_list:
           print(x)       
       noServerDialog = wxMessageDialog(frame, text, \
                                        '', wxOK | wxICON_INFORMATION)
       noServerDialog.ShowModal()
       noServerDialog.Destroy()
       
class ProfileDialog(wxDialog):
    def __init__(self, parent, id, title, profile):
        wxDialog.__init__(self, parent, id, title)
        self.profile = profile
        self.nameText = wxStaticText(self, -1, "Name:", style=wxALIGN_LEFT)
        self.nameCtrl = wxTextCtrl(self, -1, "", size = (300,20))
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
        self.__set_properties()
        self.__do_layout()
        #if (self.ShowModal() == wxID_OK):
         #   self.profile.SetName(self.nameCtrl.GetValue())
          #  self.profile.SetEmail(self.emailCtrl.GetValue())
           # self.profile.SetPhoneNumber(self.phoneNumberCtrl.GetValue())
           # self.profile.SetTechSupportInfo(self.supportCtrl.GetValue())
           # self.profile.SetLocation(self.locationCtrl.GetValue())
           # self.profile.SetHomeVenue(self.homeVenueCtrl.GetValue())
           # self.profile.SetProfileType(self.profileTypeBox.GetValue())

        #else:
         #   print 'profile = none'
          #  self.profile = None
        
       # self.Destroy()
               
    def __set_properties(self):
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

    def __do_layout(self):
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
                                                        icons.getDoorCloseBitmap(), \
                                                        icons.getDoorOpenBitmap()) 
            
        def RemoveExit(self):
            print 'remove exit'

    app = TheGrid()
    print 'before main loop'
    app.MainLoop()
