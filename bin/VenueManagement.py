#-----------------------------------------------------------------------------
# Name:        VenueManagement.py
# Purpose:     This is the user interface for Virtual Venues Server Management
#
# Author:      Susanne Lefvert
#
# Created:     2003/06/02
# RCS-ID:      $Id: VenueManagement.py,v 1.19 2003-02-06 19:39:34 lefvert Exp $
# Copyright:   (c) 2002
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
from wxPython.wx import *
from wxPython.lib.imagebrowser import *

from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Descriptions import VenueDescription
from AccessGrid.MulticastAddressAllocator import MulticastAddressAllocator
from AccessGrid.Utilities import formatExceptionInfo 
from AccessGrid.UIUtilities import *

from pyGlobus.io import GSITCPSocketException

class VenueManagementClient(wxApp):
    '''VenueManagementClient. 
    
    The VenueManagementClient class creates the main frame of the application as well as
    the VenueManagementTabs and statusbar.  
    
    '''
    
    client = None
    
    def OnInit(self):
        self.frame = wxFrame(NULL, -1, "Venue Management" )
	self.address = VenueServerAddress(self.frame, self)
	self.tabs = VenueManagementTabs(self.frame, -1, self)
        self.tabs.Enable(false)
	self.__doLayout()
	self.frame.Show() 
	statusbar = self.frame.CreateStatusBar(1)
	self.frame.SetSize(wxSize(540, 340))   
	self.SetTopWindow(self.frame)
        self.url = None
        return true
   
    def __doLayout(self):
        box = wxBoxSizer(wxVERTICAL)
	box.Add(self.address, 0, wxEXPAND|wxALL)
	box.Add(self.tabs, 1, wxEXPAND)
	self.frame.SetSizer(box)
	box.Fit(self.frame)
	self.frame.SetAutoLayout(1)  

    def ConnectToServer(self, URL):
        try:
            self.client = Client.Handle(URL).get_proxy()
            venueList = self.client.GetVenues()

        except GSITCPSocketException:
            ErrorDialog(self.frame, sys.exc_info()[1][0])

        except:
            print "Can't connect to server!", formatExceptionInfo()
            ErrorDialog(self.frame, 'The server you are trying to connect to is not running!')
                 
        else:
            self.url = URL
            # fill in venues
            self.tabs.venuesPanel.venuesListPanel.venuesList.Clear()
            self.tabs.venuesPanel.venueProfilePanel.ClearAllFields()
            if len(venueList) != 0 :
                for venue in venueList:
                    self.tabs.venuesPanel.venuesListPanel.venuesList.Append(venue.name, venue)
                currentVenue = self.tabs.venuesPanel.venuesListPanel.venuesList.GetClientData(0)
                exitsList = Client.Handle(currentVenue.uri).get_proxy().GetConnections()
                               
                self.tabs.venuesPanel.venueProfilePanel.ChangeCurrentVenue(currentVenue, exitsList)
                self.tabs.venuesPanel.venuesListPanel.venuesList.SetSelection(0)
                
            else:
                self.tabs.venuesPanel.venueProfilePanel.ChangeCurrentVenue(None)
                           

            # fill in administrators
            administratorList = self.client.GetAdministrators()
            self.tabs.configurationPanel.administratorsListPanel.administratorsList.Clear()
            if len(administratorList) != 0 :
                for admin in administratorList:
                    self.tabs.configurationPanel.administratorsListPanel.administratorsList.Append(admin, admin)
                    self.tabs.configurationPanel.administratorsListPanel.administratorsList.SetSelection(0)

            # fill in multicast address
            ip = self.client.GetBaseAddress()
            mask = str(self.client.GetAddressMask())
            self.tabs.configurationPanel.detailPanel.ipAddress.SetLabel(ip+'/'+mask)
            method = self.client.GetAddressAllocationMethod()
            
            if method == MulticastAddressAllocator.RANDOM:
                self.tabs.configurationPanel.detailPanel.ipAddress.Enable(false)
                self.tabs.configurationPanel.detailPanel.changeButton.Enable(false)
                self.tabs.configurationPanel.detailPanel.randomButton.SetValue(true)
            else:
                self.tabs.configurationPanel.detailPanel.ipAddress.Enable(true)
                self.tabs.configurationPanel.detailPanel.changeButton.Enable(true)
                self.tabs.configurationPanel.detailPanel.intervalButton.SetValue(true)


            # fill in storage location
            self.tabs.configurationPanel.detailPanel.storageLocation.SetLabel(self.client.GetStorageLocation())
            
            self.tabs.Enable(true)

              
    def AddVenue(self, venue, exitsList):
        uri = self.client.AddVenue(venue)
        Client.Handle(uri).get_proxy().SetConnections(exitsList)
        return uri      
                
    def ModifyVenue(self, venue, exitsList):
        self.client.ModifyVenue(venue.uri, venue)
        Client.Handle(venue.uri).get_proxy().SetConnections(exitsList) 
                
    def DeleteVenue(self, venue):
        print 'trying to delete venue'
        self.client.RemoveVenue(venue.uri)
            
    def AddAdministrator(self, dnName):
        self.client.AddAdministrator(dnName)

    def DeleteAdministrator(self, dnName):
        self.client.RemoveAdministrator(dnName)

    def ModifyAdministrator(self, oldName, dnName):
        self.client.RemoveAdministrator(oldName)
        self.client.AddAdministrator(dnName)
        
    def SetRandom(self):
        self.client.SetAddressAllocationMethod(MulticastAddressAllocator.RANDOM)
        
    def SetInterval(self, address, mask):
        self.client.SetBaseAddress(address)
        self.client.SetAddressMask(mask)
        self.client.SetAddressAllocationMethod(MulticastAddressAllocator.INTERVAL)

    def SetStorageLocation(self, location):
        self.client.SetStorageLocation(location)
                      
class VenueServerAddress(wxPanel):
     def __init__(self, parent, application):     
         wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER)
         self.application = application
	 self.addressLabel =  wxStaticText(self, -1,'Venue Server Address:')
         self.defaultServer = 'https://localhost:8000/VenueServer'
         self.serverList = ['https://localhost:8000/VenueServer']
         self.addressText = wxComboBox(self, 42, self.defaultServer,\
                        choices = self.serverList, style = wxCB_DROPDOWN)

         self.goButton = wxButton(self, 43, "Go", wxDefaultPosition, wxSize(20, 10))
	 self.line = wxStaticLine(self, -1)
	 self.__doLayout()
         self.__addEvents()
        
     def __addEvents(self):
         EVT_COMBOBOX(self, 42, self.callAddress)
         EVT_BUTTON(self, 43, self.callAddress)

     def callAddress(self, event):
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


class VenueManagementTabs(wxNotebook):
    ''' VenueManagementTabs
    
    VenueManagementTabs is a notebook that initializes 3 pages, 
    containing the VenuesPanel, ConfigurationPanel, and ServicesPanel.
    '''

    def __init__(self, parent, id, application):
        wxNotebook.__init__(self, parent, id)
        self.parent = parent
	self.venuesPanel = VenuesPanel(self, application) 
	self.configurationPanel = ConfigurationPanel(self, application)
	self.servicesPanel = ServicesPanel(self, application)
	self.AddPage(self.venuesPanel, "Venues")   
	self.AddPage(self.configurationPanel, "Configuration")
	#self.AddPage(self.servicesPanel, "Services")

       
# --------------------- TAB 1 -----------------------------------

class VenuesPanel(wxPanel):
    '''VenuesPanel.
    
    This is the first page in the notebook.  This page has a list of venues
    that are present in the server.   When selecting a venue from the list 
    its spcific information profile is displayed.  A user can manipulate the 
    list by either add, modify, of delete a venue.  The contents of the 
    VenuesPanel is split up into two panels;  VenueProfilePanel and VenueListPanel.
    '''

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


class VenueProfilePanel(wxPanel):
    '''VenueProfilePanel.

    Contains specific information about one venue, such as title, icon, url, and 
    exits to other venues.
    '''

    def __init__(self, parent):
        wxPanel.__init__(self, parent, -1, wxDefaultPosition, \
			 wxDefaultSize, wxNO_BORDER|wxSW_3D, name = "venueProfilePanel")  
	self.venueProfileBox = wxStaticBox(self, -1, "")
        self.description = wxTextCtrl(self, -1,'', style = wxSIMPLE_BORDER | wxNO_3D | wxTE_MULTILINE )
        self.description.SetBackgroundColour(wxColour(0,0,255))
	self.line = wxStaticLine(self, -1)
        #	self.iconLabel = wxStaticText(self, -1, 'Icon:', size = wxSize(40, 20),\
	#			      name = "icon", style = wxALIGN_RIGHT)
	wxInitAllImageHandlers()
	#bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	#self.icon = wxStaticBitmap(self, -1, bitmap, \
        #				   size = wxSize(bitmap.GetWidth(), bitmap.GetHeight()))
        self.urlLabel = wxStaticText(self, -1, 'URL:', size = wxSize(50, 20), \
				       name = "urlLabel", style = wxALIGN_RIGHT)
	self.url = wxTextCtrl(self, -1, '', name = 'url', style = wxALIGN_LEFT | wxTE_READONLY)
	self.exitsLabel = wxStaticText(self, -1, 'Exits:', size = wxSize(50, 20), \
				       name = "exitsLabel", style = wxALIGN_RIGHT)
	self.exits = wxListBox(self, 10, size = wxSize(250, 100), style = wxTE_READONLY)
        self.description.SetValue("Not connected to server")
        self.description.SetBackgroundColour(wxColour(215, 214, 214))
        self.url.SetBackgroundColour(wxColour(215, 214, 214))
        self.__hideFields()
	self.__doLayout()

    def EvtListBox(self, event):
        list = event.GetEventObject()
        data = list.GetClientData(list.GetSelection())
        if data is not None:
            exits = Client.Handle(data.uri).get_proxy().GetConnections()
            venueProfilePanel.ChangeCurrentVenue(data, exits)

    def ClearAllFields(self):
        self.venueProfileBox.SetLabel('')
        self.description.SetLabel('')
        self.exits.Clear()

    def __hideFields(self):
        self.exitsLabel.Hide()
        self.exits.Hide()
        self.urlLabel.Hide()
        self.url.Hide()
        self.venueProfileBox.SetLabel("")
    
    def ChangeCurrentVenue(self, data = None, exitsList = None):
        if data == None:
            self.__hideFields
            self.description.SetValue("No venues in server")
                        
        else:
            self.exitsLabel.Show()
            self.exits.Show()
            self.url.Show()
            self.urlLabel.Show()
            
            self.venueProfileBox.SetLabel(data.name)
            self.url.SetValue(data.uri)
            self.exits.Clear()
            index = 0
            while index < len(exitsList):
                self.exits.Append(exitsList[index].name, exitsList[index])
                index = index + 1
            self.description.SetValue(data.description)

    def __doLayout(self):
        venueListProfileSizer = wxStaticBoxSizer(self.venueProfileBox, wxVERTICAL)
        venueListProfileSizer.Add(5, 20)
	venueListProfileSizer.Add(self.description, 4, wxEXPAND|wxLEFT|wxRIGHT, 15)
        venueListProfileSizer.Add(5, 10)
	venueListProfileSizer.Add(self.line, 0, wxEXPAND)
        

	paramGridSizer = wxFlexGridSizer(4, 2, 10, 10)
        #	paramGridSizer.Add(self.iconLabel, 0, wxEXPAND, 0)
	#paramGridSizer.Add(self.icon, 0, wxALIGN_LEFT, 0)
        paramGridSizer.Add(self.urlLabel, 0, wxEXPAND, 0)
        paramGridSizer.Add(self.url, 1, wxALIGN_LEFT | wxEXPAND|wxRIGHT, 15)
	paramGridSizer.Add(self.exitsLabel, 0, wxEXPAND, 0)
	paramGridSizer.Add(self.exits, 2, wxEXPAND|wxRIGHT|wxBOTTOM, 15)
	paramGridSizer.AddGrowableCol(1) 
	paramGridSizer.AddGrowableRow(1) 
	venueListProfileSizer.Add(paramGridSizer, 10, wxEXPAND|wxTOP, 10)

	self.SetSizer(venueListProfileSizer)
	venueListProfileSizer.Fit(self)
	self.SetAutoLayout(1)  


class VenueListPanel(wxPanel):
    '''VenueListPanel.
    
    Contains the list of venues that are present on the server and buttons
    to execute modifications of the list (add, delete, and modify venue).
    '''

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
        addVenueDialog = AddVenueFrame(self, -1, "", \
                                       self.venuesList, self.application)
        addVenueDialog.InsertLocalData(self.venuesList)

    def OpenModifyVenueDialog(self, event):
	if(self.venuesList.GetSelection() != -1):    
            modifyVenueDialog = ModifyVenueFrame(self, -1, "", \
                                                 self.venuesList, self.application)
            #	modifyVenueDialog.InsertData(self.venuesList)
	
    def DeleteVenue(self, event):
        if (self.venuesList.GetSelection() != -1):
            index = self.venuesList.GetSelection()
            venueToDelete = self.venuesList.GetClientData(index)
                
            try:
                self.application.DeleteVenue(venueToDelete)
                
            except:
                print sys.exc_type
                print sys.exc_value
                # ErrorDialog(self, sys.exc_info()[1][0])
                ErrorDialog(self, 'Delete vanue failed in server!')
                
            else:
                self.venuesList.Delete(index)
                              
                if self.venuesList.Number() > 0:
                    self.venuesList.SetSelection(0)
                    venue = self.venuesList.GetClientData(0) 
                    exits = Client.Handle(venue.uri).get_proxy().GetConnections()
                    self.parent.venueProfilePanel.ChangeCurrentVenue(venue, exits)
                else:
                    self.parent.venueProfilePanel.ChangeCurrentVenue()
  
    def InsertVenue(self, data, exitsList):
        #try:
            newUri = self.application.AddVenue(data, exitsList)

       # except: 
        #    ErrorDialog(self, 'Add vanue failed in server!')

       # else: 
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
        try:
            self.application.ModifyVenue(clientData, exitsList)

        except:
            ErrorDialog(self, 'Modify vanue failed in server!')

        else:
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
        EVT_BUTTON(self, 62, self.OpenModifyAdministratorDialog)

    def DeleteAdministrator(self, event):
        index = self.administratorsList.GetSelection()
        if (index != -1):
            adminToDelete = self.administratorsList.GetClientData(index)
            try:
                self.application.DeleteAdministrator(adminToDelete)

            except:
                ErrorDialog(self, 'Delete administrator failed in server!')

            else:
                self.administratorsList.Delete(index)
                if self.administratorsList.Number > 1 :
                    self.administratorsList.SetSelection(0)
                
    def OpenAddAdministratorDialog(self, title): 
        addAdministratorDialog = AddAdministratorFrame(self, -1, "")

    def OpenModifyAdministratorDialog(self, title):
        index =  self.administratorsList.GetSelection()
        name = self.administratorsList.GetString(index)
        self.administratorsList.Delete(index)
        modifyAdministratorDialog = ModifyAdministratorFrame(self, -1, "", name)
               
    def InsertAdministrator(self, data):
        try:
            self.application.AddAdministrator(data)
        except:
            ErrorDialog(self, 'Add administrator failed in server!')

        else:
            self.administratorsList.Append(data, data)
            self.administratorsList.Select(self.administratorsList.Number()-1)

    def ModifyAdministrator(self, oldName, newName):
        try:
            self.application.ModifyAdministrator(oldName, newName)

        except:
            ErrorDialog(self, 'Modify administrator failed in server!')

        else:
            self.administratorsList.Append(newName, newName)
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
	self.randomButton = wxRadioButton(self, 302, "Standard Range")
	self.intervalButton = wxRadioButton(self, 303, "Custom Range:")
        self.ipAddress = wxStaticText(self, -1, "111.111.111.111/24", style = wxALIGN_LEFT)
        self.changeButton = wxButton(self, 300, "Change")
   	self.storageLocation = wxStaticText(self, -1, "/home/lefvert/cool_files/")
	self.browseButton = wxButton(self, 301, "Change")
        self.ipString = "111.111.111.111"
        self.maskString = "24"
        self.__doLayout()
        self.__setEvents()
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)
    
    def __setEvents(self):
        EVT_BUTTON(self, 300, self.OpenIntervalDialog)
        EVT_BUTTON(self, 301, self.OpenBrowseDialog)
        EVT_RADIOBUTTON(self, 302, self.ClickedOnRandom)
        EVT_RADIOBUTTON(self, 303, self.ClickedOnInterval)

    def ClickedOnRandom(self, event):
        self.ipAddress.Enable(false)
        self.changeButton.Enable(false)
        try:
            self.application.SetRandom()
        except:
            self.ipAddress.Enable(true)
            self.changeButton.Enable(true)
            self.intervalButton.SetValue(true)
            ErrorDialog(self, 'Set random address failed in server!')
        
    def ClickedOnInterval(self, event):
        self.ipAddress.Enable(true)
        self.changeButton .Enable(true)
        maskInt = int(self.maskString)
        
        try:
            self.application.SetInterval(self.ipString, maskInt)
            
        except:
            self.ipAddress.Enable(false)
            self.changeButton.Enable(false)
            self.randomButton.SetValue(true)
            ErrorDialog(self, 'Set interval address failed in server!')
            

    def SetAddress(self, ipAddress, mask):
        oldIpAddress = self.ipAddress.GetLabel()
        
        try:
            self.ipAddress.SetLabel(ipAddress+'/'+mask)
            self.ipString = ipAddress
            self.maskString = mask
            maskInt = int(mask)
            self.application.SetInterval(self.ipString, maskInt)

        except:
            self.ipAddress.SetLabel(oldIpAddress)
            ErrorDialog(self, 'Set interval address failed in server!')
        
    def OpenBrowseDialog(self, event):
        dlg = wxDirDialog(self, "Choose a directory:")
        if dlg.ShowModal() == wxID_OK:
            # try:
            self.application.SetStorageLocation(dlg.GetPath())
            # except:
            #   ErrorDialog(self, 'Set storage location failed in server!')
            
            # else:
            self.storageLocation.SetLabel(dlg.GetPath())
            
            dlg.Destroy()
        
    def OpenIntervalDialog(self, event):
        MulticastDialog(self, -1, "Enter Multicast Address")
    
    def __doLayout(self):
        serviceSizer = wxBoxSizer(wxVERTICAL)
        multicastBoxSizer = wxStaticBoxSizer(self.multicastBox, wxVERTICAL)

	multicastBoxSizer.Add(self.randomButton, 0, wxALL, 5)
        flexSizer = wxFlexGridSizer(0, 3, 1, 1)
        flexSizer.Add(self.intervalButton, 0)
        flexSizer.Add(self.ipAddress, 0, wxCENTER|wxEXPAND|wxALIGN_CENTER|wxTOP, 5)
        multicastBoxSizer.Add(flexSizer, 0, wxEXPAND | wxALL, 5)
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
IP_1 = 2
MASK = 4

class MulticastDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.SetSize(wxSize(400, 350))
        self.parent = parent
        self.ipAddressLabel = wxStaticText(self, -1, "IP Address: ")
        self.ipAddress1 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP_1))
        self.ipAddress2 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.ipAddress3 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.ipAddress4 = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(IP))
        self.maskLabel = wxStaticText(self, -1, "Mask: ")
        self.mask = wxTextCtrl(self, -1, "", size = (30,20), validator = DigitValidator(MASK))
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        self.__doLayout()
        if (self.ShowModal() == wxID_OK ):
            address = self.ipAddress1.GetValue() + "." +\
                      self.ipAddress2.GetValue() + "." +\
                      self.ipAddress3.GetValue() + "." +\
                      self.ipAddress4.GetValue()
            self.parent.SetAddress(address, self.mask.GetValue())
        self.Destroy();
          
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
    def __init__(self, parent, id, title, application):
        wxDialog.__init__(self, parent, id, title)
	self.SetSize(wxSize(400, 350))
        self.application = application
  
	self.informationBox = wxStaticBox(self, -1, "Information")
	self.exitsBox = wxStaticBox(self, -1, "Exits")
        self.titleLabel =  wxStaticText(self, -1, "Title:")
        self.title =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20))
	self.descriptionLabel = wxStaticText(self, -1, "Description:")
	self.description =  wxTextCtrl(self, -1, "",\
				       size = wxSize(200, 100), style = wxTE_MULTILINE|wxHSCROLL)
      	#self.iconLabel = wxStaticText(self, -1, "Icon:")
	
	#self.bitmap =  wxBitmap('IMAGES/icon.gif', wxBITMAP_TYPE_GIF)
	#self.icon = wxStaticBitmap(self, -1, self.bitmap, \
	#			   size = wxSize(self.bitmap.GetWidth(), self.bitmap.GetHeight()))
	#self.browseButton = wxButton(self, 160, "browse")
        self.venuesLabel = wxStaticText(self, -1, "Venues on server:")
        self.venues = wxListBox(self, -1, size = wxSize(200, 100))
        self.transferVenueLabel = wxStaticText(self, -1, "Add Exit")
        self.transferVenueButton = wxButton(self, 170, ">>", size = wxSize(30, 20))
        self.thisServerButton = wxButton(self, 190, "This server")
        self.remoteServerButton = wxButton(self, 200, "Remote server")
        self.removeExitButton = wxButton(self, 180, "     Remove Exit     ")
	self.exitsLabel = wxStaticText(self, -1, "Exits for your venue:")
        self.exits = wxListBox(self, -1, size = wxSize(200, 100))
	self.okButton = wxButton(self, wxID_OK, "Ok")
	self.cancelButton =  wxButton(self, wxID_CANCEL, "Cancel")
	self.doLayout() 
	self.__addEvents()
	self.Show()

    def __addEvents(self):
     	EVT_BUTTON(self, 160, self.BrowseForImage)
        EVT_BUTTON(self, 170, self.TransferVenue)
        EVT_BUTTON(self, 180, self.RemoveExit)
        EVT_BUTTON(self, 190, self.LoadLocalVenues) 
        EVT_BUTTON(self, 200, self.OpenRemoteVenues) 

    def OpenRemoteVenues(self, event):
        # get remote url
        print 'open remote server'
        remoteServerUrlDialog = RemoteServerUrlDialog(self, -1, 'Connect to server')
        if (remoteServerUrlDialog.ShowModal() == wxID_OK):
            URL = remoteServerUrlDialog.address.GetValue()
                     
        remoteServerUrlDialog.Destroy()
        #        URL = 'https://localhost:9000/VenueServer' #get from dialog
        print URL
        self.LoadVenues(URL)

    def LoadLocalVenues(self, event):
        URL = self.application.url
        self.LoadVenues(URL)
         
    def LoadVenues(self, URL):
        print 'load local: ', self.application.url
        # get local url
        # self.InsertData(venueList)
        self.client = Client.Handle(URL).get_proxy()
        venueList = self.client.GetVenues()
        self.venues.Clear()
        for venue in venueList:
            print venue.name
            self.venues.Append(venue.name, venue)
           
        
    def BrowseForImage(self, event):
        initial_dir = '/'
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
	
	#paramFrameSizer.Add(self.iconLabel, 0, wxALIGN_RIGHT)
	box = wxBoxSizer(wxHORIZONTAL)
	box.Add(20, 10, 0, wxEXPAND)
	#box.Add(self.icon, 0, wxEXPAND)
	box.Add(20, 10, 0, wxEXPAND)
	#box.Add(self.browseButton, 0, wxEXPAND)
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

        buttonSizer = wxBoxSizer(wxHORIZONTAL)
        buttonSizer.Add(self.thisServerButton, 1, wxEXPAND | wxRIGHT, 2)
        buttonSizer.Add(self.remoteServerButton, 1, wxEXPAND |wxLEFT, 2)
        exitsSizer.Add(buttonSizer, 1, wxEXPAND)
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

  
    def InsertLocalData(self, venues, exits = None):
        index = 0
        while index < venues.Number():
            if(venues.GetString(index) != self.title.GetValue()):
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
        if(index > -1):
            self.exits.Delete(index)

    def RightValues(self):
        titleTest =  self.__isStringBlank(self.title.GetValue())
   #    urlTest =  self.__isStringBlank(self.url.GetValue())
        descriptionTest =  self.__isStringBlank(self.description.GetValue())
            
        if(titleTest or descriptionTest):
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
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, app)
	self.parent = parent
        self.InsertLocalData(venueList)
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

           
            data = VenueDescription(self.title.GetValue(), \
                         self.description.GetValue(), "", None)

            self.parent.InsertVenue(data, exitsList)

        else:
            if (self.ShowModal() == wxID_OK ):
                self.Ok()
            self.Destroy()
          
            
class ModifyVenueFrame(VenueParamFrame):
    def __init__(self, parent, id, title, venueList, application):
        VenueParamFrame.__init__(self, parent, id, title, app)
	self.parent = parent
        self.InsertLocalData(venueList)
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

          
            data = VenueDescription(self.title.GetValue(), \
                         self.description.GetValue(), "", None)
            self.parent.ModifyCurrentVenue(data, exitsList)

        else:
            if (self.ShowModal() == wxID_OK ):
                self.Ok()
            self.Destroy()
           
    def InsertLocalData(self, venuesList):
        item = venuesList.GetSelection()
        data = venuesList.GetClientData(item)
        self.title.AppendText(data.name)
        self.description.AppendText(data.description)
        #self.icon.SetBitmap(data.icon)
        exitsList = Client.Handle(data.uri).get_proxy().GetConnections()
        VenueParamFrame.InsertLocalData(self, venuesList, exitsList)
                           
        #        bitmap =  wxBitmap("IMAGES/icon.gif", wxBITMAP_TYPE_GIF)
        #	self.icon.SetBitmap(bitmap)
	self.Layout()


class AdministratorParamFrame(wxDialog):
    def __init__(self, *args):
        wxDialog.__init__(self, *args)
	self.SetSize(wxSize(400, 40))
        self.informationBox = wxStaticBox(self, -1, "Information")
        self.nameLabel =  wxStaticText(self, -1, "DN Name:")
	self.name =  wxTextCtrl(self, -1, "",  size = wxSize(200, 20))
	#self.dnLabel = wxStaticText(self, -1, "DN name:")
	#self.dn =  wxTextCtrl(self, -1, "", size = wxSize(200, 20))
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
        #paramFrameSizer.Add(self.dnLabel, 0, wxALIGN_RIGHT)
	#paramFrameSizer.Add(self.dn, 0, wxEXPAND)
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

class ModifyAdministratorFrame(AdministratorParamFrame):
    def __init__(self, parent, id, title, oldName):
        AdministratorParamFrame.__init__(self, parent, id, title)
        self.parent = parent
        self.name.Clear()
        self.name.AppendText(oldName)
        if (self.ShowModal() == wxID_OK ):
            self.parent.ModifyAdministrator(oldName, self.name.GetValue())      
        self.Destroy();

class RemoteServerUrlDialog(wxDialog):
    def __init__(self, parent, id, title):
        wxDialog.__init__(self, parent, id, title)
        self.okButton = wxButton(self, wxID_OK, "Ok")
        self.cancelButton = wxButton(self, wxID_CANCEL, "Cancel")
        info = "Please, enter remote server URL address"
        self.text = wxStaticText(self, -1, info, style=wxALIGN_LEFT)
        self.addressText = wxStaticText(self, -1, "Address: ", style=wxALIGN_LEFT)
        self.address = wxTextCtrl(self, -1, "", size = wxSize(300,20))
        self.__doLayout()

    def __doLayout(self):
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
        
class DigitValidator(wxPyValidator):
    def __init__(self, flag):
        wxPyValidator.__init__(self)
        self.flag = flag
        EVT_CHAR(self, self.OnChar)
     
    def Clone(self):
        return DigitValidator(self.flag)

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        index = 0
        for x in val:
            index = index+1
            if x not in string.digits:
                wxMessageBox("Please, use digits for the mask!", "Error")
                return false
        if (self.flag == IP or self.flag == IP_1) and index == 0:
            wxMessageBox("Please, fill in all IP Address fields!", "Error")
            return false
        
        if self.flag == IP and (int(val)<0 or int(val)>255):
            wxMessageBox("Allowed values for IP Address are between 224.0.0.0 - 239.225.225.225", "Error")
            return false
        
        elif self.flag == IP_1 and (int(val)<224 or int(val)>239):
            wxMessageBox("Allowed values for IP Address are between 224.0.0.0 - 239.225.225.225", "Error")
            return false
        
        elif index == 0 and self.flag == MASK:
            wxMessageBox("Please, fill in mask!", "Error")
            return false
        return true

    def TransferToWindow(self):
        return true # Prevent wxDialog from complaining.

    def TransferFromWindow(self):
        return true # Prevent wxDialog from complaining.

    def OnChar(self, event):
        key = event.KeyCode()
        if key < WXK_SPACE or key == WXK_DELETE or key > 255:
            event.Skip()
            return
       
        if chr(key) in string.digits:
            event.Skip()
            return

        if not wxValidator_IsSilent():
            wxBell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return

app = VenueManagementClient(0)
app.MainLoop()  
