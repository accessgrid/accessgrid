from wxPython.wx import *
from wxPython.lib.imagebrowser import *
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription

'''VenueManagementClient. 

The VenueManagementClient class creates the main frame of the application as well as
the VenueManagementTabs and statusbar.  

'''
class VenueManagementClient(wxApp):
    client = None
    
    def OnInit(self):
        print 'oninit'
        self.frame = wxFrame(NULL, -1, "Venue Management" )
	self.address = VenueServerAddress(self.frame, self)
	self.tabs = VenueManagementTabs(self.frame, -1, self)
        self.tabs.Enable(false)
	self.__doLayout()
	self.frame.Show() 
	statusbar = self.frame.CreateStatusBar(1)
	self.frame.SetSize(wxSize(540, 340))   
	self.SetTopWindow(self.frame)
        print 'oninit finished'
        return true
   
    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
	box.Add(self.address, 0, wxEXPAND|wxALL)
	box.Add(self.tabs, 1, wxEXPAND)
	self.frame.SetSizer(box)
	box.Fit(self.frame)
	self.frame.SetAutoLayout(1)  

    def ConnectToServer(self, URL):
        self.client = Client.Handle(URL).get_proxy()

        #try:
        venueList = self.client.GetVenues()
        print 'try connect to server'
        self.tabs.venuesPanel.venuesListPanel.venuesList.Clear()
        if len(venueList) != 0 :
            for venue in venueList:
                print 'appending venue in startup'
                print venue.name
                print venue.description
                print venue.uri
                self.tabs.venuesPanel.venuesListPanel.venuesList.Append(venue.name, venue)
                self.tabs.venuesPanel.venuesListPanel.venuesList.SetSelection(0)
                currentVenue = self.tabs.venuesPanel.venuesListPanel.venuesList.GetClientData(0)
            exitsList = Client.Handle(currentVenue.uri).get_proxy().GetConnections()    
            self.tabs.venuesPanel.venueProfilePanel.ChangeCurrentVenue(currentVenue, exitsList)
                   
        administratorList = self.client.GetAdministrators()
        self.tabs.configurationPanel.administratorsListPanel.administratorsList.Clear()
        if len(administratorList) != 0 :
            for admin in administratorList:
                self.tabs.configurationPanel.administratorsListPanel.administratorsList.Append(admin, admin)
                self.tabs.configurationPanel.administratorsListPanel.administratorsList.SetSelection(0)
                           
        self.tabs.Enable(true)
       # except:
        #    self.__showNoServerDialog( 'The server you are trying to connect to is not running!')  
        
    def AddVenue(self, venue, exitsList):
     #   try:
         uri = self.client.AddVenue(venue)
         Client.Handle(uri).get_proxy().SetConnections(exitsList)
         return uri      
    # except:
     #       self.__showNoServerDialog('You are not connected to a server')
            
    def ModifyVenue(self, venue, exitsList):
        #  try:
        self.client.ModifyVenue(venue.uri, venue)
        Client.Handle(venue.uri).get_proxy().SetConnections(exitsList) 
        #  except:
        #     print 'modify venue didnt work'
        #    self.__showNoServerDialog('You are not connected to a server')
        
    def DeleteVenue(self, venue):
        try:
            self.client.RemoveVenue(venue.uri)

        except:
            self.__showNoServerDialog('The item is not deleted')
            
    def AddAdministrator(self, name):
        self.client.AddAdministrator(name)

    def DeleteAdministrator(self, name):
        self.client.RemoveAdministrator(name)

   # def ModifyAdministrator(self, name, dnName):
   #    self.client.ModifyAdministrator(name)
        
    def __showNoServerDialog(self, text):
        noServerDialog = wxMessageDialog(self.frame, text, \
                                         '', wxOK | wxICON_INFORMATION)
        noServerDialog.ShowModal()
        noServerDialog.Destroy() 

    
        
class VenueServerAddress(wxPanel):
     def __init__(self, parent, application):     
         wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER)
         self.application = application
	 self.addressLabel =  wxStaticText(self, -1,'Venue Server Address:')
         self.defaultServer = 'https://localhost:8000/VenueServer'
         self.serverList = ['https://localhost:8000/VenueServer']
	 #self.addressText = wxTextCtrl(self, 42, self.defaultServer,style=wxPROCESS_ENTER)
         self.addressText = wxComboBox(self, 42, self.defaultServer,\
                        choices = self.serverList, style = wxCB_DROPDOWN|wxTE_PROCESS_ENTER)

         self.goButton = wxButton(self, 43, "Go", wxDefaultPosition, wxSize(20, 10))
	 self.line = wxStaticLine(self, -1)
	 self.__doLayout()
         self.__addEvents()
        
     def __addEvents(self):
          EVT_TEXT_ENTER(self, 42, self.evtText)
          EVT_TEXT_ENTER(self, 43, self.evtText)
          EVT_BUTTON(self, 43, self.evtText)  

     def evtText(self, event):
         self.application.ConnectToServer(self.addressText.GetValue())
         
     def __doLayout(self):
         venueServerAddressBox = wxBoxSizer(wxVERTICAL)  
	
         box = wxBoxSizer(wxHORIZONTAL)
	 box.Add(self.addressLabel, 0, wxEXPAND|wxRIGHT|wxLEFT|wxTOP, 5)
	 box.Add(self.addressText, 1, wxEXPAND|wxRIGHT|wxTOP, 5)
         box.Add(self.goButton, 0, wxEXPAND|wxRIGHT|wxTOP, 5)
	 venueServerAddressBox.Add(box, 0, wxEXPAND)
	 venueServerAddressBox.Add(self.line, 0, wxEXPAND|wxALL, 5)
         self.SetSizer(venueServerAddressBox)
	 venueServerAddressBox.Fit(self)
	 self.SetAutoLayout(1)  

''' VenueManagementTabs

VenueManagementTabs is a notebook that initializes 3 pages, 
containing the VenuesPanel, ConfigurationPanel, and ServicesPanel.

'''
class VenueManagementTabs(wxNotebook):
    def __init__(self, parent, id, application):
        wxNotebook.__init__(self, parent, id)
        self.parent = parent
	self.venuesPanel = VenuesPanel(self, application) 
	self.configurationPanel = ConfigurationPanel(self, application)
	self.servicesPanel = ServicesPanel(self, application)
	self.AddPage(self.venuesPanel, "Venues")   
	self.AddPage(self.configurationPanel, "Configuration")
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
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.parent = parent
	self.venueProfilePanel = VenueProfilePanel(self)
	self.venuesListPanel = VenueListPanel(self, application)
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
	self.venueProfileBox = wxStaticBox(self, -1, "")
	self.description = wxStaticText(self, -1,'', \
                                        size = wxSize(10, 30) ,\
                                      style = wxTE_MULTILINE | wxTE_READONLY)
	self.line = wxStaticLine(self, -1)
	self.iconLabel = wxStaticText(self, -1, 'Icon:', size = wxSize(40, 20),\
				      name = "icon", style = wxALIGN_RIGHT)
	wxInitAllImageHandlers()
	bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	self.icon = wxStaticBitmap(self, -1, bitmap, \
				   size = wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
	self.exitsLabel = wxStaticText(self, -1, 'Exits:', size = wxSize(50, 20), \
				       name = "exitsLabel", style = wxALIGN_RIGHT)
	self.exits = wxListBox(self, 10, size = wxSize(250, 100), style = wxTE_READONLY)
	self.__doLayout()

    def EvtListBox(self, event):
        list = event.GetEventObject()
        data = list.GetClientData(list.GetSelection())
        if data is not None:
            exits = Client.Handle(data.uri).get_proxy().GetConnections() 
            venueProfilePanel.ChangeCurrentVenue(data, exits)
       
    def ChangeCurrentVenue(self, data, exitsList):
        print 'in change current venue before we set the exits'
        if data == None:
            self.venueProfileBox.SetLabel("")
            self.description.SetLabel("No venues in server")
            
        else:
            self.venueProfileBox.SetLabel(data.name)
            self.description.SetLabel(data.description)
           # self.icon.SetBitmap(wxBitmap(data.icon))
            print 'in change current venue before we set the exits'
            self.exits.Clear()
            index = 0
            while index < len(exitsList):
                print exitsList[index].name
                self.exits.Append(exitsList[index].name, exitsList[index])
                index = index + 1

    def __doLayout(self):
        venueListProfileSizer = wxStaticBoxSizer(self.venueProfileBox, wxVERTICAL)
	venueListProfileSizer.Add(self.description, 0, wxEXPAND|wxALL, 5)
	venueListProfileSizer.Add(self.line, 0, wxEXPAND)

	paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
	paramGridSizer.Add(self.iconLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.icon, 0, wxALIGN_LEFT, 0)
	paramGridSizer.Add(self.exitsLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.exits, 1, wxEXPAND|wxRIGHT|wxBOTTOM, 15)
	paramGridSizer.AddGrowableCol(1) 
	paramGridSizer.AddGrowableRow(1) 
	venueListProfileSizer.Add(paramGridSizer, 10, wxEXPAND|wxTOP, 10)

	self.SetSizer(venueListProfileSizer)
	venueListProfileSizer.Fit(self)
	self.SetAutoLayout(1)  

'''VenueListPanel.

Contains the list of venues that are present on the server and buttons
to execute modifications of the list (add, delete, and modify venue).

'''
class VenueListPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.parent = parent
        self.application = application
	self.venuesListBox = wxStaticBox(self, -1, "Venues", name = 'venueListBox')
	self.venuesList = wxListBox(self, 50, name = 'venueList')
	self.addButton = wxButton(self, 10, 'Add', \
				  size = wxSize(50,20), name = 'addButton')
	self.modifyButton = wxButton(self, 20, 'Modify',\
				     size = wxSize(50, 20), name = 'modifyButton')
	self.deleteButton = wxButton(self, 30, 'Delete',\
				     size = wxSize(50, 20), name = 'deleteButton')
	self.__doLayout()
	self.__addEvents()

    def __addEvents(self):
        EVT_BUTTON(self, 10, self.OpenAddVenueDialog)  
	EVT_BUTTON(self, 20, self.OpenModifyVenueDialog)  
	EVT_BUTTON(self, 30, self.DeleteVenue)
        EVT_LISTBOX(self, 50, self.EvtListBox)

    def EvtListBox(self, event):
        list = event.GetEventObject()
        data = list.GetClientData(list.GetSelection())
        if data is not None:
            exits = Client.Handle(data.uri).get_proxy().GetConnections() 
            self.parent.venueProfilePanel.ChangeCurrentVenue(data, exits)

    def OpenAddVenueDialog(self, event):
        addVenueDialog = AddVenueFrame(self, -1, "", venueList = self.venuesList)
        addVenueDialog.InsertData(self.venuesList)

    def OpenModifyVenueDialog(self, event):
	if(self.venuesList.GetSelection() != -1):    
		modifyVenueDialog = ModifyVenueFrame(self, -1, "", venueList = self.venuesList)
	#	modifyVenueDialog.InsertData(self.venuesList)
	
    def DeleteVenue(self, event):
        if (self.venuesList.GetSelection() != -1):
                index = self.venuesList.GetSelection()
                venueToDelete = self.venuesList.GetClientData(index)
                self.application.DeleteVenue(venueToDelete)
		self.venuesList.Delete(index)
                              
		if self.venuesList.Number() > 1 :
			self.venuesList.SetSelection(0)
                        venue = self.venuesList.GetClientData(0) 
                        exits = Client.Handle(venue.uri).get_proxy().GetConnections() 
                        self.parent.venueProfilePanel.ChangeCurrentVenue(venue, exits)
  
    def InsertVenue(self, data, exitsList):
        newUri = self.application.AddVenue(data, exitsList)
        if newUri :
            data.uri = newUri
            self.venuesList.Append(data.name, data)
            self.venuesList.Select(self.venuesList.Number()-1)
            self.parent.venueProfilePanel.ChangeCurrentVenue(data, exitsList)
            
        		
    def ModifyCurrentVenue(self, data, exitsList):
        item = self.venuesList.GetSelection()
        clientData =  self.venuesList.GetClientData(item)
        clientData.name = data.name
        clientData.description = data.description
     #   self.icon.SetBitmap(data.icon)
        print "in modify venue client data!"
        print clientData.uri
        self.application.ModifyVenue(clientData, exitsList)
        self.venuesList.SetString(item, data.name)
        self.parent.venueProfilePanel.ChangeCurrentVenue(clientData, exitsList)
               
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
'''ConfigurationPanel.

This is the second page in the notebook.  This page has a list of administrators
that are authorized to modify the list of venues on the server and also entitled to add and remove
other administrators.   When selecting a name from the list, the spcific information profile of
the administrator is shown.  The contents of the AdministratorsPanel is split up into two panels;  
AdministratorsProfilePanel and AdministratorsListPanel.

'''
class ConfigurationPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
	self.administratorsListPanel = AdministratorsListPanel(self, application)
        self.detailPanel = DetailPanel(self, application)
	#self.administratorsProfilePanel = AdministratorsProfilePanel(self)
    	self.__doLayout()
	
    def __doLayout(self):
        configurationPanelSizer = wxBoxSizer(wxHORIZONTAL)
	configurationPanelSizer.Add(self.administratorsListPanel, 0, wxEXPAND|wxALL, 10)
        configurationPanelSizer.Add(self.detailPanel, 2, wxEXPAND|wxALL, 10)
	#administratorsPanelSizer.Add(self.administratorsProfilePanel, 2, wxEXPAND|wxALL, 10)
	     
        self.SetSizer(configurationPanelSizer)
	configurationPanelSizer.Fit(self)
	self.SetAutoLayout(1)  


'''AdministratorssProfilePanel.

Contains specific information about one administrators, such as name, icon, and direct name.
'''
#class AdministratorsProfilePanel(wxPanel):
#   def __init__(self, parent):
#        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
#                         wxDefaultSize, wxNO_BORDER|wxSW_3D, name = "venueProfilePanel")  
#        self.administratorsProfileBox = wxStaticBox(self, -1, "Susanne Lefvert")
#        self.description = wxStaticText(self, -1,"ops" ,size = wxSize(200, 30))
#        self.line = wxStaticLine(self, -1)
#        self.dnLabel = wxStaticText(self, -1, "DN:", size = wxSize(35, 20),\
#                                    name = "dnLabel", style = wxALIGN_RIGHT)
#        self.dn =  wxStaticText(self, -1, "http://www.thedn.com", size = wxSize(200, 20), name = "dn")
#        self.iconLabel = wxStaticText(self, -1, "Icon:", size = wxSize(40, 20),\
#                                      name = "icon", style = wxALIGN_RIGHT)
#        wxInitAllImageHandlers()
#        bitmap =  wxBitmap("IMAGES/icon.gif", wxBITMAP_TYPE_GIF)
#        self.icon = wxStaticBitmap(self, -1, bitmap, \
#                                   size =wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
#        self.__setProperties()
#        self.__doLayout()
#        
#    def __setProperties(self):
#        self.description.SetLabel("Employed at Argonne National \nLaboratory!\n")
#        
#    def __doLayout(self):
#        administratorsProfileSizer = wxStaticBoxSizer(self.administratorsProfileBox, wxVERTICAL)
#        administratorsProfileSizer.Add(self.description, 0, wxEXPAND|wxALL, 5)
#        administratorsProfileSizer.Add(self.line, 0, wxEXPAND)
#            
#        self.SetSizer(administratorsProfileSizer)
#        administratorsProfileSizer.Fit(self)
#        
#        paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
#        paramGridSizer.Add(self.dnLabel, 0, wxEXPAND, 0)
#        paramGridSizer.Add(self.dn, 0, wxEXPAND, 0)
#        paramGridSizer.Add(self.iconLabel, 0, wxEXPAND, 0)
#        paramGridSizer.Add(self.icon, 0, wxLEFT, 0)
#        paramGridSizer.AddGrowableCol(1) 
#        paramGridSizer.AddGrowableRow(2) 
#        administratorsProfileSizer.Add(paramGridSizer, 10, wxEXPAND|wxTOP, 10)
#        self.SetAutoLayout(1)
            
            
'''AdministratorsListPanel.

Contains the list of administratos that are authorized to manipulate venues and administrators.  This panel also
has buttons to execute modifications of the list (add, delete, and modify an administrator).

'''
class AdministratorsListPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
	self.administratorsListBox = wxStaticBox(self, -1, "Administrators", name = 'venueListBox')
	self.administratorsList = wxListBox(self, -1, name = 'venueList')
	self.addButton = wxButton(self, 60, 'Add', \
				  size = wxSize(50, 20), name = 'addButton')
	self.deleteButton = wxButton(self, 61, 'Delete',\
				     size = wxSize(50, 20), name = 'deleteButton')
	self.modifyButton = wxButton(self, 62, 'Modify',\
				     size = wxSize(50, 20), name = 'modifyButton')
        self.__addEvents()
	self.__doLayout()

    def __addEvents(self):
        EVT_BUTTON(self, 60, self.OpenAddAdministratorDialog)
        EVT_BUTTON(self, 61, self.DeleteAdministrator)
     #   EVT_BUTTON(self, 62, self.OpenModifyAdministratorDialog)

    def DeleteAdministrator(self, event):
        index = self.administratorsList.GetSelection()
        if (index != -1):
            adminToDelete = self.administratorsList.GetClientData(index)
            print "trying to remove"+adminToDelete
            self.application.DeleteAdministrator(adminToDelete)
            self.administratorsList.Delete(index)
            if self.administratorsList.Number > 1 :
                self.administratorsList.SetSelection(0)
        
    def OpenAddAdministratorDialog(self, title): 
        addAdministratorDialog = AddAdministratorFrame(self, -1, "")

    def InsertAdministrator(self, data):
        self.application.AddAdministrator(data)
        self.administratorsList.Append(data, data)
        self.administratorsList.Select(self.administratorsList.Number()-1)
          
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


class DetailPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
	self.multicastBox = wxStaticBox(self, -1, "Multicast Address",size = wxSize(50, 50), name = 'multicastBox')
	self.storageBox = wxStaticBox(self, -1, "Storage Location", size = wxSize(500, 50), name = 'storageBox')
	self.randomButton = wxRadioButton(self, 302, "Random Address")
	self.intervalButton = wxRadioButton(self, 303, "Interval Address:")
        self.ipAddress = wxStaticText(self, -1, "", size = wxSize(500,20))
        self.changeButton = wxButton(self, 300, "Change")
   	self.storageLocation = wxStaticText(self, -1, "/home/lefvert/cool_files/")
	self.browseButton = wxButton(self, 301, "Change")
        self.__doLayout()
        self.__setEvents()
        self.ipAddress.Enable(false)
        self.changeButton .Enable(false)

    def __setEvents(self):
        EVT_BUTTON(self, 300, self.OpenIntervalDialog)
        EVT_BUTTON(self, 301, self.OpenBrowseDialog)
        EVT_RADIOBUTTON(self, 302, self.ClickedOnRandom)
        EVT_RADIOBUTTON(self, 303, self.ClickedOnInterval)

    def ClickedOnRandom(self, event):
        self.ipAddress.Enable(false)
        self.changeButton .Enable(false)
        
    def ClickedOnInterval(self, event):
        self.ipAddress.Enable(true)
        self.changeButton .Enable(true)

    def OpenBrowseDialog(self, event):
        dlg = wxDirDialog(self, "Choose a directory:")
        if dlg.ShowModal() == wxID_OK:
            self.storageLocation.SetLabel(dlg.GetPath())
            dlg.Destroy()
        
    def OpenIntervalDialog(self, event):
        MulticastDialog(self, -1, "Enter Multicast Address")
    
    def SetAddress(self, ip, mask):
        text = " "+ip+" / "+mask
        self.ipAddress.SetLabel(text)

    def __doLayout(self):
        serviceSizer = wxBoxSizer(wxVERTICAL)
        multicastBoxSizer = wxStaticBoxSizer(self.multicastBox, wxVERTICAL)

	multicastBoxSizer.Add(self.randomButton, 0, wxALL, 5)
        flexSizer = wxFlexGridSizer(0, 2, 1, 1)
        flexSizer.Add(self.intervalButton, 0, wxALL|wxEXPAND, 5)
        flexSizer.Add(self.ipAddress, 0, wxALIGN_BOTTOM|wxEXPAND)
        multicastBoxSizer.Add(flexSizer)
        multicastBoxSizer.Add(self.changeButton, 0, wxBOTTOM|wxALIGN_CENTER, 5) 

	serviceSizer.Add(multicastBoxSizer, 0,  wxBOTTOM|wxEXPAND, 10)
        serviceSizer.Add(5,5)
        
	storageBoxSizer = wxStaticBoxSizer(self.storageBox, wxVERTICAL)
        storageBoxSizer.Add(5,5)
	storageBoxSizer.Add(self.storageLocation, 5, wxALL, 10)
	storageBoxSizer.Add(self.browseButton, 0, wxCENTER|wxBOTTOM, 5)
     
   	serviceSizer.Add(storageBoxSizer, 0, wxEXPAND)

	self.SetSizer(serviceSizer)
	serviceSizer.Fit(self)
	self.SetAutoLayout(1)  


# --------------------- TAB 3 -----------------------------------

'''ServicesPanel.

This is the third page in the notebook.  The page lets the user specify different options
for services for the venue server.  Currently, a user can choose random or interval multicast 
address and the storage location for the server.  

'''
class ServicesPanel(wxPanel):
    def __init__(self, parent, application):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D)
        self.application = application
	self.__doLayout()

    def __doLayout(self):
        self.SetAutoLayout(1)  


#--------------------- DIALOGS -----------------------------------
IP = 1
MASK = 2

class MulticastDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.SetSize(wxSize(400, 350))
        self.parent = parent
        self.ipAddressLabel = wxStaticText(self, -1, "IP Address: ")
        self.ipAddress1 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.ipAddress2 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.ipAddress3 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.ipAddress4 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.maskLabel = wxStaticText(self, -1, "Mask: ")
        self.mask = wxTextCtrl(self, -1, "24", size = (30,20), validator = DigitValidator(MASK))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__doLayout()
        if (self.ShowModal() == wxID_OK ):
            print '---------------before get value'
            address = self.ipAddress1.GetValue() + "." +\
                      self.ipAddress1.GetValue() + "." +\
                      self.ipAddress3.GetValue() + "." +\
                      self.ipAddress3.GetValue()
            print 'after getValue'
            self.parent.SetAddress(address, self.mask.GetValue())
        print 'before destroy'    
        self.Destroy();
        print 'after destroy'

  
    def __doLayout(self):
        sizer = wxBoxSizer(wxVERTICAL)
        theSizer = wxFlexGridSizer(0, 5, 10, 10)
        theSizer.Add(self.ipAddressLabel, 0, wxALIGN_RIGHT)
        theSizer.Add(self.ipAddress1)
        theSizer.Add(self.ipAddress2)
        theSizer.Add(self.ipAddress3)
        theSizer.Add(self.ipAddress4)
        theSizer.Add(self.maskLabel, 0, wxALIGN_RIGHT)
        theSizer.Add(self.mask)

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.okButton, 0, wxRIGHT, 5)
        buttonSizer.Add(self.cancelButton, 0, wxLEFT, 5)
        
        sizer.Add(theSizer, 0, wxALL, 20)
        sizer.Add(buttonSizer, 0, wxALIGN_CENTER|wxBOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetAutoLayout(1)  

class VenueParamFrame(wxDialog):
    def __init__(self, *args):
        wxDialog.__init__(self, *args)
	self.SetSize(wxSize(400, 350))

  
	self.informationBox = wxStaticBox(self, -1, "Information")
	self.exitsBox = wxStaticBox(self, -1, "Exits")
        self.titleLabel =  wxStaticText(self, -1, "Title:")
	self.title =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20))
	self.descriptionLabel = wxStaticText(self, -1, "Description:")
	self.description =  wxTextCtrl(self, -1, "",\
				       size = wxSize(200, 100), style = wxTE_MULTILINE|wxHSCROLL)
	self.iconLabel = wxStaticText(self, -1, "Icon:")
	
	self.bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	self.icon = wxStaticBitmap(self, -1, self.bitmap, \
				   size = wxSize(self.bitmap.GetWidth(), self.bitmap.GetHeight()))
	self.browseButton = wxButton(self, 160, "browse")
        self.venuesLabel = wxStaticText(self, -1, "Venues on this server:")
        self.venues = wxListBox(self, -1, size = wxSize(150, 100))
        self.transferVenueLabel = wxStaticText(self, -1, "Add Exit")
        self.transferVenueButton = wxButton(self, 170, ">>", size = wxSize(30, 20))
        self.removeExitButton = wxButton(self, 180, "Remove Exit")
	self.exitsLabel = wxStaticText(self, -1, "Exits for your venue:")
        self.exits = wxListBox(self, -1, size = wxSize(150, 100))
	self.okButton = wxButton(self, wxID_OK, "Ok")
	self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")
	self.doLayout() 
	self.__addEvents()
	self.Show()

    def __addEvents(self):
     	EVT_BUTTON(self, 160, self.BrowseForImage)
        EVT_BUTTON(self, 170, self.TransferVenue)
        EVT_BUTTON(self, 180, self.RemoveExit) 
    
    def BrowseForImage(self, event):
        initial_dir = '/home/lefvert/PROJECTS/P2_AG/VENUE_MANAGEMENT/IMAGES' 
	imageDialog = ImageDialog(self, initial_dir)   
	imageDialog.Show()
	if (imageDialog.ShowModal() == wxID_OK):      
	    file = imageDialog.GetFile() 
	    self.bitmap =  wxBitmap(file, wxBITMAP_TYPE_GIF)
	    self.icon.SetBitmap(self.bitmap)
	    self.Layout()
     
        imageDialog.Destroy()
			
    def doLayout(self):
        boxSizer = wxBoxSizer(wxVERTICAL)
	
	paramFrameSizer = wxFlexGridSizer(10, 2, 10, 10)
	paramFrameSizer.Add(self.titleLabel, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.title, 0, wxEXPAND)
	
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
        exitsSizer = wxFlexGridSizer(10, 3, 5, 5)
	exitsSizer.Add(self.venuesLabel, 0)
        exitsSizer.Add(10,10, wxEXPAND)
        exitsSizer.Add(self.exitsLabel, 0)
      	exitsSizer.Add(self.venues, 0, wxEXPAND)
        transferbuttonSizer = wxBoxSizer(wxVERTICAL)
        transferbuttonSizer.Add(self.transferVenueLabel, 0, wxEXPAND|wxCENTER)
        transferbuttonSizer.Add(self.transferVenueButton, 0, wxEXPAND|wxTOP, 2)
        exitsSizer.Add(transferbuttonSizer, 0, wxALL|wxALIGN_CENTER, 5)
	exitsSizer.Add(self.exits, 0, wxEXPAND)
        exitsSizer.Add(10,10)
        exitsSizer.Add(10,10)
        exitsSizer.Add(self.removeExitButton, 0, wxEXPAND)
        exitsSizer.AddGrowableCol(0)
        exitsSizer.AddGrowableCol(2) 
        
        bottomParamSizer.Add(exitsSizer, 0, wxEXPAND | wxALL, 10)
	
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

  
    def InsertData(self, venues, exits = None):
        print 'insert data in addVenueFrame'
        index = 0
        while index < venues.Number():
            venue = venues.GetClientData(index)
            self.venues.Append(venue.name, venue)
            index = index + 1

        if exits != None:
            index = 0
            while index < len(exits):
                self.exits.Append(exits[index].name, exits[index])
                index = index + 1

    def TransferVenue(self, event):
        index = self.venues.GetSelection()
        if index != -1:
            venue = self.venues.GetClientData(index)
            
            if self.exits.FindString(venue.name) == -1:
                self.exits.Append(venue.name, venue)
            else:
                text = ""+venue.name+" is added already"
                exitExistDialog = wxMessageDialog(self, text, \
                                                  '', wxOK | wxICON_INFORMATION)
                exitExistDialog.ShowModal()
                exitExistDialog.Destroy() 

    def RemoveExit(self, event):
        index = self.exits.GetSelection()
        self.exits.Delete(index)

    def RightValues(self):
        titleTest =  self.__isStringBlank(self.title.GetValue())
   #    urlTest =  self.__isStringBlank(self.url.GetValue())
        descriptionTest =  self.__isStringBlank(self.description.GetValue())
            
        if(titleTest or  \
           (self.bitmap == None) or descriptionTest):
            wrongParamsDialog = wxMessageDialog(self, 'Please, fill in all fields!', \
                                                '', wxOK | wxICON_INFORMATION)
            wrongParamsDialog.ShowModal()
            wrongParamsDialog.Destroy()
            return false
        
        else:
            return true

    def __isStringBlank(self, text):
        empty = true
        index = 0
        while index < len(text):
            if text[index] >= 'A' and text[index] <= 'z' :
                empty = false
                break
            else:
                index = index + 1
        return empty

 
class AddVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList = list):
        VenueParamFrame.__init__(self, parent, id, title)
	self.parent = parent
        self.InsertData(venueList)
        if (self.ShowModal() == wxID_OK ):
            self.Ok()
        self.Destroy()
     
    def Ok(self):
        if self.RightValues():
            index = 0
            exitsList = []
            while index < self.exits.Number():
                exitsList.append(self.exits.GetClientData(index))
                index = index + 1

            print 'it is weird exits doesnt show up...'
            data = VenueDescription(self.title.GetValue(), \
                         self.description.GetValue(), "", None)

            self.parent.InsertVenue(data, exitsList)
          
            
class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList = list):
        VenueParamFrame.__init__(self, parent, id, title)
	self.parent = parent
        self.InsertData(venueList)
        if (self.ShowModal() == wxID_OK ):
            self.Ok()
        self.Destroy()
    
    def Ok(self):
        if self.RightValues():
            index = 0
            exitsList = []
            while index < self.exits.Number():
                exitsList.append(self.exits.GetClientData(index))
                index = index + 1

            print 'it is weird exits doesnt show up...'
            data = VenueDescription(self.title.GetValue(), \
                         self.description.GetValue(), "", None)
            self.parent.ModifyCurrentVenue(data, exitsList)
           
    def InsertData(self, venuesList):
        print 'insert data in modify venue'
        item = venuesList.GetSelection()
        data = venuesList.GetClientData(item)
        print 'datas name '+data.name
        self.title.AppendText(data.name)
        self.description.AppendText(data.description)
        #self.icon.SetBitmap(data.icon)
        exitsList = Client.Handle(data.uri).get_proxy().GetConnections()
        VenueParamFrame.InsertData(self, venuesList, exitsList)
                           
#        bitmap =  wxBitmap("IMAGES/icon.gif", wxBITMAP_TYPE_GIF)
#	self.icon.SetBitmap(bitmap)
	self.Layout()


class AdministratorParamFrame(wxDialog):
    def __init__(self, *args):
        wxDialog.__init__(self, *args)
	self.SetSize(wxSize(400, 40))
        self.informationBox = wxStaticBox(self, -1, "Information")
        self.nameLabel =  wxStaticText(self, -1, "Name:")
	self.name =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20))
	self.dnLabel = wxStaticText(self, -1, "DN name:")
	self.dn =  wxTextCtrl(self, -1, "", size = wxSize(200, 20))
	self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")
	self.doLayout() 
              			
    def doLayout(self):
        topSizer = wxBoxSizer(wxVERTICAL)
        boxSizer = wxStaticBoxSizer(self.informationBox, wxVERTICAL)

        paramFrameSizer = wxFlexGridSizer(10, 2, 10, 10)
       # paramFrameSizer.Add(self.informationBox, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.nameLabel, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.name, 0, wxEXPAND)
        paramFrameSizer.Add(self.dnLabel, 0, wxALIGN_RIGHT)
	paramFrameSizer.Add(self.dn, 0, wxEXPAND)
        paramFrameSizer.AddGrowableCol(2) 	
        boxSizer.Add(paramFrameSizer, 1,  wxEXPAND|wxALL, 10)
        
        buttonSizer =  wxBoxSizer(wxHORIZONTAL)
	buttonSizer.Add(20, 20, 1)
	buttonSizer.Add(self.okButton, 0)
	buttonSizer.Add(10, 10)
	buttonSizer.Add(self.cancelButton, 0)
	buttonSizer.Add(20, 20, 1)

    	topSizer.Add(boxSizer, 1, wxALL | wxEXPAND, 10)
	topSizer.Add(buttonSizer, 0, wxEXPAND | wxBOTTOM, 5)

	self.SetSizer(topSizer)
	topSizer.Fit(self)
	self.SetAutoLayout(1)  

    
class AddAdministratorFrame(AdministratorParamFrame):
    def __init__(self, parent, id, title):
        AdministratorParamFrame.__init__(self, parent, id, title)
        self.parent = parent
        if (self.ShowModal() == wxID_OK ):
            self.parent.InsertAdministrator(self.name.GetValue())
        
        self.Destroy();


class DigitValidator(wxPyValidator):
    def __init__(self, flag):
        wxPyValidator.__init__(self)
        self.flag = flag
        EVT_CHAR(self, self.OnChar)
     
    def Clone(self):
        return DigitValidator(self.flag)

    def Validate(self, win):
        print 'validate'
        tc = self.GetWindow()
        val = tc.GetValue()
        index = 0
        for x in val:
            index = index+1
            if x not in string.digits:
                print 'false in validate'
                return false
        if index != 3 and self.flag == IP:
            print 'false in validate'
            return false
        print 'true in validate'
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

    def OnChar(self, event):
        print 'on char'
        key = event.KeyCode()
        if key < WXK_SPACE or key == WXK_DELETE or key > 255:
            event.Skip()
            return
       
        if chr(key) in string.digits:
            print "digits"
            event.Skip()
            return

        if not wxValidator_IsSilent():
            print "silent"
            wxBell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return



app = VenueManagementClient(0)
app.MainLoop()  
