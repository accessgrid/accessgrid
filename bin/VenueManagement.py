from wxPython.wx import *
from wxPython.lib.imagebrowser import *

'''VenueManagementClient. 

The VenueManagementClient class creates the main frame of the application as well as
the VenueManagementTabs and statusbar.  

'''
class VenueManagementClient(wxApp):
    def OnInit(self):
        self.frame = wxFrame(NULL, -1, "Venue Management" )
	self.address = VenueServerAddress(self.frame)
	self.tabs = VenueManagementTabs(self.frame, -1)
	self.__doLayout()
	self.frame.Show() 
	statusbar = self.frame.CreateStatusBar(1)
	self.frame.SetSize(wxSize(500, 340))   
	self.SetTopWindow(self.frame)
        return true

    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
	box.Add(self.address, 0, wxEXPAND|wxALL, 8)
	box.Add(self.tabs, 1, wxEXPAND)
	self.frame.SetSizer(box)
	box.Fit(self.frame)
	self.frame.SetAutoLayout(1)  

class VenueServerAddress(wxPanel):
     def __init__(self, parent):
         wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
	 self.addressLabel =  wxStaticText(self, -1,'Venue Server Address:')
	 self.addressText = wxTextCtrl(self, -1)
	 self.line = wxStaticLine(self, -1)
	 self.__doLayout()
  
     def __doLayout(self):
         venueServerAddressBox = wxBoxSizer(wxVERTICAL)  
	
         box = wxBoxSizer(wxHORIZONTAL)
	 box.Add(self.addressLabel, 0, wxEXPAND|wxRIGHT, 5)
	 box.Add(self.addressText, 1, wxEXPAND)
	 venueServerAddressBox.Add(box, 0, wxEXPAND)
	 venueServerAddressBox.Add(self.line, 0, wxEXPAND|wxTOP, 5)
	 self.SetSizer(venueServerAddressBox)
	 venueServerAddressBox.Fit(self)
	 self.SetAutoLayout(1)  

''' VenueManagementTabs

VenueManagementTabs is a notebook that initializes 3 pages, 
containing the VenuesPanel, AdministratorsPanel, and ServicesPanel.

'''
class VenueManagementTabs(wxNotebook):
    def __init__(self, *args):
        wxNotebook.__init__(self, *args)
	self.venuesPanel = VenuesPanel(self) 
	self.administratorsPanel = AdministratorsPanel(self)
	self.servicesPanel = ServicesPanel(self)
	self.AddPage(self.venuesPanel, "Venues")   
	self.AddPage(self.administratorsPanel, "Server Administrators")
	self.AddPage(self.servicesPanel, "Services")

       
# --------------------- TAB 1 -----------------------------------
'''VenuesPanel.

This is the first page in the notebook.  This page has a list of venues
that are present in the server.   When selecting a venue from the list 
its spcific information profile is displayed.  A user can manipulate the 
list by either add, modify, of delete a venue.  The contents of the 
VenuesPanel is split up into two panels;  VenueProfilePanel and VenueListPanel.

'''
class VenuesPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
	self.venueProfilePanel = VenueProfilePanel(self)
	self.venuesListPanel = VenueListPanel(self)
	self.__doLayout()
	
    def __doLayout(self):
        venuesPanelBox = wxBoxSizer(wxHORIZONTAL)
	venuesPanelBox.Add(self.venuesListPanel, 0, wxEXPAND|wxALL, 10)
	venuesPanelBox.Add(self.venueProfilePanel, 2, wxEXPAND|wxALL, 10)
     
        self.SetSizer(venuesPanelBox)
	venuesPanelBox.Fit(self)
	self.SetAutoLayout(1)  


'''VenuesProfilePanel.

Contains specific information about one venue, such as title, icon, url, and 
exits to other venues.

'''
class VenueProfilePanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D, name = "venueProfilePanel")  
	self.venueProfileBox = wxStaticBox(self, -1, "Library")
	self.description = wxStaticText(self, -1,'This is the Library')
	self.line = wxStaticLine(self, -1)
	self.urlLabel = wxStaticText(self, -1, 'URL:', size = wxSize(35, 20),\
				     name = "urlLabel", style = wxALIGN_RIGHT)
	self.url =  wxStaticText(self, -1, 'http://www.theurl.com', name = "url")
	self.iconLabel = wxStaticText(self, -1, 'Icon:', size = wxSize(40, 20),\
				      name = "icon", style = wxALIGN_RIGHT)
	wxInitAllImageHandlers()
	bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	self.icon = wxStaticBitmap(self, -1, bitmap, \
				   size = wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
	self.exitsLabel = wxStaticText(self, -1, 'Exits:', size = wxSize(40, 20), \
				       name = "exitsLabel", style = wxALIGN_RIGHT)
	self.exits = wxListBox(self, 10, size = wxSize(250, 100), style = wxTE_READONLY)
	self.__setProperties()
	self.__doLayout()

    def __setProperties(self):
        self.description.SetLabel('\nThis is the library and you can find all kinds of\ninteresting books!\n')
	self.exits.Append('Chemistry')
	self.exits.Append('Physics')

    def ChangeCurrentVenue(data):
        self.description.SetLabel(data.GetDescription())
	self.url.SetLabel(data.GetUrl())
	self.icon.SetBitmap(self.bitmap)

    def __doLayout(self):
        venueListProfileSizer = wxStaticBoxSizer(self.venueProfileBox, wxVERTICAL)
	venueListProfileSizer.Add(self.description, 0, wxEXPAND|wxALL, 5)
	venueListProfileSizer.Add(self.line, 1, wxEXPAND)
	self.SetSizer(venueListProfileSizer)
	venueListProfileSizer.Fit(self)

	paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
	paramGridSizer.Add(self.urlLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.url, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.iconLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.icon, 0, wxALIGN_LEFT, 0)
	paramGridSizer.Add(self.exitsLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.exits, 0, wxEXPAND|wxRIGHT|wxBOTTOM, 5)
	paramGridSizer.AddGrowableCol(1) 
	paramGridSizer.AddGrowableRow(2) 
	venueListProfileSizer.Add(paramGridSizer, 10, wxEXPAND)

	self.SetAutoLayout(1)  


'''VenueListPanel.

Contains the list of venues that are present on the server and buttons
to execute modifications of the list (add, delete, and modify venue).

'''
class VenueListPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)  
	self.venuesListBox = wxStaticBox(self, -1, "Venues", name = 'venueListBox')
	self.venuesList = wxListBox(self, -1, name = 'venueList')
	self.addButton = wxButton(self, 10, 'Add', \
				  size = wxSize(42,20), name = 'addButton')
	self.modifyButton = wxButton(self, 20, 'Modify',\
				     size = wxSize(42, 20), name = 'modifyButton')
	self.deleteButton = wxButton(self, 30, 'Delete',\
				     size = wxSize(42, 20), name = 'deleteButton')
	self.__doLayout()
	self.__addEvents()
   	
    def __addEvents(self):
        EVT_BUTTON(self, 10, self.OpenAddVenueDialog)  
	EVT_BUTTON(self, 20, self.OpenModifyVenueDialog)  
	EVT_BUTTON(self, 30, self.DeleteVenue)  

    def OpenAddVenueDialog(self, event):
        addVenueDialog = AddVenueFrame(self, -1, "Please, enter right parameters")

    def OpenModifyVenueDialog(self, event):
	if(self.venuesList.GetSelection() != -1):    
		modifyVenueDialog = ModifyVenueFrame(self, -1, "Please, enter right parameters")
		item = self.venuesList.GetSelection()
		data = self.venuesList.GetClientData(item)
		modifyVenueDialog.InsertData(data)
	
    def DeleteVenue(self, event):
        if (self.venuesList.GetSelection() != -1): 
		self.venuesList.Delete(self.venuesList.GetSelection())
		if self.venuesList.Number > 1 :
			self.venuesList.SetSelection(0)
  
    def InsertVenue(self, data):
	self.venuesList.Append(data.GetTitle(), data) 
	self.venuesList.Select(self.venuesList.Number()-1)
		
    def ModifyCurrentVenue(self, data):
	item = self.venuesList.GetSelection()
	self.venuesList.SetClientData(item, data)
	self.venuesList.SetString(item, data.GetTitle())
       
    def __doLayout(self):
        venueListPanelSizer = wxStaticBoxSizer(self.venuesListBox, wxVERTICAL)
	venueListPanelSizer.Add(self.venuesList, 8, wxEXPAND|wxALL, 5)
	buttonSizer = wxBoxSizer(wxHORIZONTAL)
	buttonSizer.Add(self.addButton, 1,  wxLEFT| wxBOTTOM | wxALIGN_CENTER, 5)
	buttonSizer.Add(self.modifyButton, 1, wxLEFT | wxBOTTOM |wxALIGN_CENTER, 5)
	buttonSizer.Add(self.deleteButton, 1, wxLEFT | wxBOTTOM |wxRIGHT | wxALIGN_CENTER, 5)
	venueListPanelSizer.Add(buttonSizer, 0, wxEXPAND)
	
	self.SetSizer(venueListPanelSizer)
	venueListPanelSizer.Fit(self)
		
	self.SetAutoLayout(1)  
	

# --------------------- TAB 2 -----------------------------------
'''AdministratorsPanel.

This is the second page in the notebook.  This page has a list of administrators
that are authorized to modify the list of venues on the server and also entitled to add and remove
other administrators.   When selecting a name from the list, the spcific information profile of
the administrator is shown.  The contents of the AdministratorsPanel is split up into two panels;  
AdministratorsProfilePanel and AdministratorsListPanel.

'''
class AdministratorsPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
	self.administratorsListPanel = AdministratorsListPanel(self)
	self.administratorsProfilePanel = AdministratorsProfilePanel(self)
    	self.__doLayout()
	
    def __doLayout(self):
        administratorsPanelSizer = wxBoxSizer(wxHORIZONTAL)
	administratorsPanelSizer.Add(self.administratorsListPanel, 0, wxEXPAND|wxALL, 10)
	administratorsPanelSizer.Add(self.administratorsProfilePanel, 2, wxEXPAND|wxALL, 10)
	     
        self.SetSizer(administratorsPanelSizer)
	administratorsPanelSizer.Fit(self)
	self.SetAutoLayout(1)  


'''AdministratorssProfilePanel.

Contains specific information about one administrators, such as name, icon, and direct name.

'''
class AdministratorsProfilePanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D, name = "venueProfilePanel")  
	self.administratorsProfileBox = wxStaticBox(self, -1, "Susanne Lefvert")
	self.description = wxStaticText(self, -1,'ops' ,size = wxSize(200,50))
	self.line = wxStaticLine(self, -1)
	self.dnLabel = wxStaticText(self, -1, 'DN:', size = wxSize(35, 20),\
				     name = "dnLabel", style = wxALIGN_RIGHT)
	self.dn =  wxStaticText(self, -1, 'http://www.thedn.com', size = wxSize(200, 20), name = "dn")
	self.iconLabel = wxStaticText(self, -1, 'Icon:', size = wxSize(40, 20),\
				      name = "icon", style = wxALIGN_RIGHT)
	wxInitAllImageHandlers()
	bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	self.icon = wxStaticBitmap(self, -1, bitmap, \
				   size =wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
	self.__setProperties()
	self.__doLayout()

    def __setProperties(self):
        self.description.SetLabel('\nSusanne Lefvert works in the MCS division at \nArgonne National Laboratories!\n')
			
    def __doLayout(self):
        administratorsProfileSizer = wxStaticBoxSizer(self.administratorsProfileBox, wxVERTICAL)
	administratorsProfileSizer.Add(self.description, 0, wxEXPAND|wxALL, 5)
	administratorsProfileSizer.Add(self.line, 1, wxEXPAND)

	self.SetSizer(administratorsProfileSizer)
        administratorsProfileSizer.Fit(self)

	paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
	paramGridSizer.Add(self.dnLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.dn, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.iconLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.icon, 0, wxLEFT, 0)
	administratorsProfileSizer.Add(paramGridSizer, 10, wxEXPAND)
	self.SetAutoLayout(1)      
	
 
'''AdministratorsListPanel.

Contains the list of administratos that are authorized to manipulate venues and administrators.  This panel also
has buttons to execute modifications of the list (add, delete, and modify an administrator).

'''
class AdministratorsListPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)  
	self.administratorsListBox = wxStaticBox(self, -1, "Administrators", name = 'venueListBox')
	self.administratorsList = wxListBox(self, -1, name = 'venueList')
	self.addButton = wxButton(self, -1, 'Add', \
				  size = wxSize(42, 20), name = 'addButton')
	self.deleteButton = wxButton(self, -1, 'Delete',\
				     size = wxSize(42, 20), name = 'deleteButton')
	self.modifyButton = wxButton(self, -1, 'Modify',\
				     size = wxSize(42, 20), name = 'modifyButton')
	self.__doLayout()

      
    def AddVenue(self, title): 
        self.administratorsList.Append(title)

    def __doLayout(self):
        administratorsListSizer = wxStaticBoxSizer(self.administratorsListBox, wxVERTICAL)
	administratorsListSizer.Add(self.administratorsList, 8, wxEXPAND|wxALL, 5)
	buttonSizer = wxBoxSizer(wxHORIZONTAL)
	administratorsListSizer.Add(buttonSizer, 0)
	buttonSizer.Add(self.addButton, 1,  wxLEFT| wxBOTTOM | wxALIGN_CENTER, 5)
	buttonSizer.Add(self.modifyButton, 1, wxLEFT | wxBOTTOM |wxALIGN_CENTER, 5)
	buttonSizer.Add(self.deleteButton, 1, wxLEFT | wxBOTTOM |wxRIGHT | wxALIGN_CENTER, 5)
		
	self.SetSizer(administratorsListSizer)
	administratorsListSizer.Fit(self)
	self.SetAutoLayout(1)  
	

# --------------------- TAB 3 -----------------------------------
'''ServicesPanel.

This is the third page in the notebook.  The page lets the user specify different options
for services for the venue server.  Currently, a user can choose random or interval multicast 
address and the storage location for the server.  

'''
class ServicesPanel(wxPanel):
    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)

	self.multicastBox = wxStaticBox(self, -1, "Multicast Address", name = 'multicastBox')
	self.storageBox = wxStaticBox(self, -1, "Storage Location", name = 'storageBox')
	self.randomButton = wxRadioButton(self, 1, "Random Address")
	self.intervalButton = wxRadioButton(self, 2, "Interval Address")
	self.ipAddress11 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress12 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress13 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress14 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.line = wxStaticText(self, -1, '__')
	self.ipAddress21 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress22 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress23 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.ipAddress24 = wxTextCtrl(self, -1, size = wxSize(30, 20))
	self.storageLocation = wxTextCtrl(self, -1, size = wxSize(310, 20))
	self.browseButton = wxButton(self, -1, "Browse")
	self.__doLayout()

    def __doLayout(self):
        serviceSizer = wxBoxSizer(wxVERTICAL)
        multicastBoxSizer = wxStaticBoxSizer(self.multicastBox, wxVERTICAL)
	multicastBoxSizer.Add(self.randomButton, 0, wxALL, 10)

	intervalSizer = wxFlexGridSizer(1, 10, 2, 2)
	intervalSizer.Add(self.intervalButton, 0, wxEXPAND|wxRIGHT, 5) 
	intervalSizer.Add(self.ipAddress11, 0, wxEXPAND|wxALL, 1)
	intervalSizer.Add(self.ipAddress12, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress13, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress14, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.line, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress21, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress22, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress23, 0, wxEXPAND|wxALL, 1) 
	intervalSizer.Add(self.ipAddress24, 0, wxEXPAND|wxALL, 1) 
	multicastBoxSizer.Add(intervalSizer, 1, wxALL|wxEXPAND, 10)
	
	storageBoxSizer = wxStaticBoxSizer(self.storageBox, wxHORIZONTAL)
	
	storageBoxSizer.Add(self.storageLocation, 0, wxTOP|wxLEFT, 20)
	storageBoxSizer.Add(self.browseButton, 0, wxALL, 20)
	serviceSizer.Add(multicastBoxSizer, 0,  wxEXPAND|wxALL, 10)
	serviceSizer.Add(storageBoxSizer, 0, wxEXPAND|wxALL, 10)

	self.SetSizer(serviceSizer)
	serviceSizer.Fit(self)
	self.SetAutoLayout(1)  
	
	
class VenueParamFrame(wxFrame):
    def __init__(self, *args):
        wxFrame.__init__(self, *args)
	self.SetSize(wxSize(400, 350))
	exitsList = ['Chemistry', 'Physics']
  
	self.informationBox = wxStaticBox(self, -1, "Information")
	self.exitsBox = wxStaticBox(self, -1, "Exits")
	self.topTExt =  wxStaticText(self, -1, "")
	self.titleLabel =  wxStaticText(self, -1, "Title:")
	self.title =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20))
	self.descriptionLabel = wxStaticText(self, -1, "Description:")
	self.description =  wxTextCtrl(self, -1, "",\
				       size = wxSize(200, 100), style = wxTE_MULTILINE|wxHSCROLL)
	self.urlLabel = wxStaticText(self, -1, "URL:")
	self.url =  wxTextCtrl(self, -1, "", size = wxSize(200, 20))
	self.iconLabel = wxStaticText(self, -1, "Icon:")
	
	self.bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	self.icon = wxStaticBitmap(self, -1, self.bitmap, \
				   size = wxSize(self.bitmap.GetWidth(), self.bitmap.GetHeight()))
	self.browseButton = wxButton(self, 160, "browse")
	self.exitsLabel = wxStaticText(self, -1, "Exits:")
        self.exits = wxCheckListBox(self, -1, size = wxSize(200, 100), choices = exitsList)
	self.okButton = wxButton(self, 140, "Ok")
	self.cancelButton =  wxButton(self, 150, "Cancel")
	self.doLayout() 
	self.__addEvents()
	self.Show()

    def __addEvents(self):
        EVT_BUTTON(self, 150, self.Cancel) 
	EVT_BUTTON(self, 160, self.BrowseForImage) 
    
    def BrowseForImage(self, event):
        initial_dir = '/home/lefvert/PROJECTS/P2_AG/VENUE_MANAGEMENT/IMAGES' 
	imageDialog = ImageDialog(self, initial_dir)   
	imageDialog.Show()
	if (imageDialog.ShowModal() == wxID_OK):      
	    file = imageDialog.GetFile() 
	    self.bitmap =  wxBitmap(file, wxBITMAP_TYPE_GIF)
	    self.icon.SetBitmap(self.bitmap)
	    self.Layout()
        else:
	    imageDialog.Destroy()
			
    def doLayout(self):
        boxSizer = wxBoxSizer(wxVERTICAL)
	
	paramFrameSizer = wxFlexGridSizer(10, 2, 10, 10)
	paramFrameSizer.Add(self.titleLabel, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.title, 0, wxEXPAND)
	
	paramFrameSizer.Add(self.urlLabel, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.url, 0, wxEXPAND)
	paramFrameSizer.Add(self.iconLabel, 0, wxALIGN_RIGHT)
	box = wxBoxSizer(wxHORIZONTAL)
	box.Add(20, 10, 0, wxEXPAND)
	box.Add(self.icon, 0, wxEXPAND)
	box.Add(20, 10, 0, wxEXPAND)
	box.Add(self.browseButton, 0, wxEXPAND)
	paramFrameSizer.Add(box, 0, wxEXPAND)
	
	paramFrameSizer.AddGrowableCol(1) 

	topParamSizer = wxStaticBoxSizer(self.informationBox, wxVERTICAL)
	topParamSizer.Add(paramFrameSizer, 0, wxEXPAND | wxALL, 20)
	topParamSizer.Add(self.descriptionLabel, 0, wxALIGN_LEFT |wxLEFT, 20)
	topParamSizer.Add(self.description, 0, wxEXPAND |wxLEFT | wxRIGHT| wxBOTTOM, 20)
	
	bottomParamSizer = wxStaticBoxSizer(self.exitsBox, wxVERTICAL)
	bottomParamSizer.Add(self.exitsLabel, 0, wxALIGN_LEFT |wxLEFT, 20)
	bottomParamSizer.Add(self.exits, 0, wxEXPAND |wxLEFT | wxRIGHT| wxBOTTOM, 20)
	
	buttonSizer =  wxBoxSizer(wxHORIZONTAL)
	buttonSizer.Add(20, 20, 1)
	buttonSizer.Add(self.okButton, 0)
	buttonSizer.Add(10, 10)
	buttonSizer.Add(self.cancelButton, 0)
	buttonSizer.Add(20, 20, 1)

    	boxSizer.Add(topParamSizer, 0, wxALL | wxEXPAND, 10)
	boxSizer.Add(bottomParamSizer, 0, wxEXPAND | wxALL, 10)
	boxSizer.Add(buttonSizer, 5, wxEXPAND | wxBOTTOM, 5)

	self.SetSizer(boxSizer)
	boxSizer.Fit(self)
	self.SetAutoLayout(1)  

    def Cancel(self,  event):
        self.Destroy()
 
class AddVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title):
        VenueParamFrame.__init__(self, parent, id, title)
	self.parent = parent
	self.__addEvents()
 
    def __addEvents(self):
        EVT_BUTTON(self, 140, self.Ok)   
    
    def Ok(self, event):
        exitsCopy = []
	index = 0
	while index < self.exits.Number():
		exitsCopy.append(self.exits.IsChecked(index))
		index = index + 1
           
        data = VenueData(self.title.GetValue(), self.url.GetValue(), self.bitmap, self.description.GetValue(), exitsCopy)
        self.parent.InsertVenue(data)
	self.Destroy()

class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title):
        VenueParamFrame.__init__(self, parent, id, title)
	self.parent = parent
	self.__addEvents()
 
    def __addEvents(self):
        EVT_BUTTON(self, 140, self.Ok)   
    
    def Ok(self, event):
        exitsCopy = []
	index = 0
	while index < self.exits.Number():
		exitsCopy.append(self.exits.IsChecked(index))
		index = index + 1

	data = VenueData(self.title.GetValue(), self.url.GetValue(), self.bitmap, self.description.GetValue(), exitsCopy)
	self.parent.ModifyCurrentVenue(data)
	self.Destroy()

    def InsertData(self, data):
        self.title.AppendText(data.GetTitle())
	self.url.AppendText(data.GetUrl())
        self.description.AppendText(data.GetDescription())
	self.icon.SetBitmap(data.GetBitmap())
	self.Layout()
	item = 0
	exitList = data.GetExits()
	index = 0
	if len(exitList) != self.exits.Number():
		print 'error in VenueManagement.py::ModifyVenueFrame::InsertData'

    	while index < len(exitList):
		self.exits.Check(index, exitList[index])
		index = index + 1
	
class VenueData:
    def __init__(self, title, url, bitmap, description, exits):
        self.title = title
	self.url = url
	self.bitmap = bitmap
	self.description = description
	self.exits = exits
		
    def GetTitle(self):
        return self.title

    def GetUrl(self):
        return self.url

    def GetBitmap(self):
        return self.bitmap

    def GetDescription(self):
        return self.description

    def GetExits(self):
        return self.exits


app = VenueManagementClient(0)
app.MainLoop()  
