#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        NodeSetupWizard.py
# Purpose:     Wizard for setup and test a room based node configuration
# Created:     2003/08/12
# RCS_ID:      $Id: NodeSetupWizard.py,v 1.55 2006-09-21 12:05:36 braitmai Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import string
import sys
import urlparse

# Imports for user interface
from wxPython.wx import *
from wxPython.wizard import *

# Agtk specific imports
from AccessGrid.Toolkit import WXGUIApplication, CmdlineApplication
from AccessGrid import Log
from AccessGrid.Toolkit import Service, MissingDependencyError
from AccessGrid.Platform.Config import SystemConfig
from AccessGrid import icons
from AccessGrid.Preferences import Preferences

from AccessGrid.Platform import IsWindows

from AccessGrid.AGNodeService import AGNodeService, WriteNodeConfig
from AccessGrid.interfaces.AGNodeService_interface import AGNodeService as AGNodeServiceI
from AccessGrid.interfaces.AGNodeService_client import AGNodeServiceIW
from AccessGrid.hosting import SecureServer, InsecureServer
from AccessGrid.AGParameter import ValueParameter
from AccessGrid.Descriptions import AGServiceManagerDescription

from AccessGrid.Utilities import NODE_SETUP_WIZARD_LOG

from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.UIUtilities import ProgressDialog

from AccessGrid.interfaces.AGService_client import AGServiceIW

from AccessGrid.AGServiceManager import AGServiceManager
from AccessGrid.interfaces.AGServiceManager_interface import AGServiceManager as AGServiceManagerI
from AccessGrid.interfaces.AGServiceManager_client import AGServiceManagerIW

from AccessGrid.ServiceDiscovery import Browser, Publisher
from AccessGrid.Version import GetVersion, GetStatus

browser = None
services = None

log = Log.GetLogger(Log.NodeSetupWizard)

def HostnameFromServiceName(serviceName):
    hostname = serviceName
    parts = serviceName.split('(')
    hostname = parts[0]
    hostname = hostname.strip()
    return hostname
    

class ServiceUnavailableException(Exception):
    pass
     
class TitledPage(wxPyWizardPage):
    '''
    Base class for all wizard pages.  Creates a title.
    '''
    def __init__(self, parent, title):
    
        wxPyWizardPage.__init__(self, parent)
        self.title = title
        self.next = None
        self.prev = None
        self.MakePageTitle()

    def MakePageTitle(self):
        '''
        Create page title
        '''
        self.sizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(self.sizer)
        title = wxStaticText(self, -1, self.title, style = wxALIGN_CENTER)
        title.SetLabel(self.title)
        title.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))
        self.sizer.AddWindow(title, 0, wxALL|wxEXPAND, 5)
        self.sizer.AddWindow(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        self.sizer.Add((10, 10))
               
    def SetNext(self, next):
        '''
        Set following page that will show up when user clicks on next button.
        '''
        self.next = next

    def SetPrev(self, prev):
        '''
        Set previous page that will show up when user clicks on back button.
        '''
        self.prev = prev  

    def GetNext(self):
        '''
        Get the following page.
        '''
        return self.next
    
    def GetPrev(self):
        '''
        Get the previous page.
        '''
        return self.prev


class NodeSetupWizard(wxWizard):
    '''
    The node setup wizard guides users through the steps necessary for
    creating and testing a node configuration. 
    '''
    def __init__(self, parent, debugMode, progress, app = None):
        wxWizard.__init__(self, parent, 10,"Setup Node", wxNullBitmap)
        '''
        This class creates a wizard for node setup
        '''
        self.debugMode = debugMode
        self.progress = progress
        self.step = 1
        self.SetIcon(icons.getAGIconIcon())
        self.SetPageSize(wxSize(510, 350))
        self.nodeClient = NodeClient(app)
        
        # Start the node service which will store the configuration
        try:
            progress.UpdateGauge("Start the node service.",50)
            self.nodeClient.StartNodeService()
        except:
            log.exception("NodeSetupWizard.__init__: Can not start node service")
            dlg = wxMessageDialog(None, "Do you want to clear the node service that is already running? (not recommended if you currently are participating in a meeting).", "Warning", style = wxOK | wxCANCEL | wxICON_INFORMATION)
            if not dlg.ShowModal() == wxID_OK:
                dlg.Destroy()
                return
            else:
                log.info("NodeSetupWizard.__init__: Try connect to already running service")
                try:
                    self.nodeClient.ConnectToNodeService()
                except:
                    log.exception("NodeSetupWizard.__init__:Can not connect to node service")
                    ErrorDialog(self, "Can not start Node Setup Wizard.",
                                "Error", logFile = NODE_SETUP_WIZARD_LOG)
                    return
        
        self.page1 = WelcomeWindow(self, "Welcome to the Node Setup Wizard")
        self.page2 = VideoCaptureWindow(self, self.nodeClient,
                                        "Video Capture Machine")
        self.page3 = VideoCaptureWindow2(self, self.nodeClient,
                                         "Video Capture Machine")
        self.page4 = VideoDisplayWindow(self, self.nodeClient,
                                        "Display Machine")
        self.page5 = AudioWindow(self, self.nodeClient,
                                 "Audio Machine")
        self.page6 = ConfigWindow(self, self.nodeClient, "Your Node Setup")
        self.FitToPage(self.page1)
               
        EVT_WIZARD_PAGE_CHANGING(self, 10, self.ChangingPage) 
        
        # Set the initial order of the pages
        self.page1.SetNext(self.page2)
        self.page2.SetNext(self.page3)
        self.page3.SetNext(self.page4)
        self.page4.SetNext(self.page5)
        self.page5.SetNext(self.page6)
        
        self.page2.SetPrev(self.page1)
        self.page3.SetPrev(self.page2)
        self.page4.SetPrev(self.page3)
        self.page5.SetPrev(self.page4)
        self.page6.SetPrev(self.page5)

        # Run the wizard
        progress.UpdateGauge("Open wizard.",75)
        progress.Destroy()
        
        self.RunWizard(self.page1)
        
        # Wizard finished; stop node service
        try:
            self.nodeClient.Stop()
        except:
            log.exception("NodeSetupWizard.__init__: Can not stop node service")

    def ChangingPage(self, event):
        '''
        This method is called when a page is changed in the wizard
        '''
        direction = event.GetDirection()
        page = event.GetPage()
        forward = 1
        
        print ' 222 = ', self.page2.machineCtrl.GetValue()
        
        # Show users configuration in last page
        if isinstance(page.GetNext(), ConfigWindow):
            p = self.page2
            page.GetNext().SetVideoC(HostnameFromServiceName(p.machineCtrl.GetValue()),
                                     p.portCtrl.GetValue(), p.checkBox.GetValue(),
                                     self.page3.GetCameraPorts())
            p = self.page4
            page.GetNext().SetVideoD(HostnameFromServiceName(p.machineCtrl.GetValue()),
                                     p.portCtrl.GetValue(), p.checkBox.GetValue())
            p = self.page5
            page.GetNext().SetAudio(HostnameFromServiceName(p.machineCtrl.GetValue()),
                                    p.portCtrl.GetValue(), p.checkBox.GetValue())

        # Check to see if values are entered correctly
        if direction == forward:
            if not page.GetValidity():
                # Ignore event
                event.Veto()

                        
class WelcomeWindow(TitledPage):
    '''
    First page of wizard contains introduction text.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.info = wxStaticText(self, -1, "This wizard will help you setup and test your Node. The node is your configuration of machines \ncontrolling the display, cameras, speakers, and microphones.")
        self.beforeText = wxStaticText(self, -1,"Before continuing:")
        self.beforeText.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))
        self.beforeText2 =  wxStaticText(self, -1,
                                "Make sure you have Service Managers running on each machine in your node.")
        self.contText =  wxStaticText(self, -1, "Click 'Next' to continue.", style = wxCENTER)
       
        self.Layout()

    def GetValidity(self):
        return true
          
    def Layout(self):
        ''' Handles UI layout '''
        self.sizer.Add(self.info, 0, wxALL, 5)
        self.sizer.Add((10,10))
        self.sizer.Add(self.beforeText, 0, wxALL|wxEXPAND, 5)
        self.sizer.Add(self.beforeText2, 0, wxALL, 5)
        self.sizer.Add((10, 100))
        self.sizer.Add(self.contText, 0, wxALIGN_CENTER|wxALL|wxEXPAND, 5)
        

class VideoCaptureWindow(TitledPage):
    '''
    Wizard page that contains fields for setting video capture machine
    '''
    #global browser, services
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.parent = parent
        self.nodeClient = nodeClient
        self.text = wxStaticText(self, -1, "Which machine controls your cameras?")
        self.machineText = wxStaticText(self, -1, "Machine Name:")
        self.portText = wxStaticText(self, -1, "Service Manager Port:")
        self.MACHINE_ID = wxNewId()
        self.PORT_ID =  wxNewId()
        self.BUTTON_ID = wxNewId()
        self.services = browser.GetServices()
        hostnames = self.services.keys()
        if nodeClient.app.GetHostname() in hostnames:
            hostnameToSelect = nodeClient.app.GetHostname()
        else:
            hostnameToSelect = hostnames[0]
        self.machineCtrl = wxComboBox(self, self.MACHINE_ID, choices=hostnames)
        self.machineCtrl.SetValue(hostnameToSelect)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "11000")
        self.CHECK_ID = wxNewId()
        self.checkBox = wxCheckBox(self, self.CHECK_ID, "I do not want to use a video capture machine (you will not be able to send video).")
        
        # The result after clicking the test button
        # True - we can connect to current machine
        # False - can not connect to current machine
        # None - didn't try connecting yet
        self.canConnect = None
        self.__SetEvents()
        self.Layout()

    def __SetEvents(self):
        ''' Set the events '''
        EVT_TEXT(self.machineCtrl, self.MACHINE_ID, self.EnterText)
        EVT_COMBOBOX(self.machineCtrl, self.MACHINE_ID, self.OnSelect)
        EVT_TEXT(self.portCtrl, self.PORT_ID, self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)
  
    def OnSelect(self,event):
        selectedHostname = self.machineCtrl.GetValue()
        if selectedHostname in self.services.keys():
            url = self.services[selectedHostname]
            hostport = urlparse.urlparse(url)[1]
            parts = hostport.split(':')
            if len(parts) > 1:
                port = parts[1]
                self.portCtrl.SetValue(port)
        
    def EnterText(self, event):
        '''
        Is called whever the user enters text in a text control
        '''   
        # Connect status should only reflect current machine
        self.canConnect = None
            
    def GetValidity(self):
        '''
        Is called when the next button is clicked. It tests if a service manager is running on
        the specified machine and port. If it can connect available video capture cards are displayed.
        Else, a text displays telling you that the connection failed.
        '''
        # User decides to not have a video capture machine
        if self.checkBox.GetValue():
            return true

        # A uri built with empty host will point at local host, to
        # avoid misunderstandings the user have to give a machine name.
        if self.machineCtrl.GetValue() == "":
            MessageDialog(self, "Could not connect. Is a service manager running\nat given machine and port?",  
                          style = wxICON_ERROR|wxOK)
            return false
        
        wxBeginBusyCursor()

        # Verify access to machine
        try:
            hostname = HostnameFromServiceName(self.machineCtrl.GetValue())
            self.nodeClient.CheckServiceManager(hostname,
                                                self.portCtrl.GetValue())
            self.canConnect = true
        except:
            log.exception("VideoCaptureWindow.Validate: Check service manager failed")
            self.canConnect = false
            
        if self.canConnect:
            cards = []
            try:
                cards = self.nodeClient.GetCaptureCards(hostname, self.portCtrl.GetValue())
            except:
                log.exception("VideoCaptureWindow.Validate: Can not get capture cards from service manager")
                ErrorDialog(self, "Could not find your installed video capture cards.", "Error",
                            logFile = NODE_SETUP_WIZARD_LOG)
                               
            if self.next:
                # Set capture cards
                self.GetNext().SetCaptureCards(cards)

            wxEndBusyCursor()
            return true
        
        else:
            MessageDialog(self, "Could not connect. Is a service manager running\nat given machine and port?",  
                          style = wxICON_ERROR|wxOK)
            wxEndBusyCursor()
            return false
          
    def CheckBoxEvent(self, event):
        '''
        Disables all options if user decides not to use a capture machine
        '''
        if self.checkBox.GetValue():
            # Checked
            self.machineText.Enable(false)
            self.portText.Enable(false)
            self.machineCtrl.Enable(false)
            self.portCtrl.Enable(false)
                
            # Ignore camera information
            self.next = self.parent.page4
            self.parent.page4.prev = self
                                       
        else:
            # Not checked
            self.machineText.Enable(true)
            self.portText.Enable(true)
            self.machineCtrl.Enable(true)
            self.portCtrl.Enable(true)

            # Next page shows cameras
            self.next = self.parent.page3
            self.parent.page4.prev = self.parent.page3
                                       
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add((20,20))
        
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        self.sizer.Add((10,10))
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        
        self.sizer.Add((20, 20))

                
class VideoCaptureWindow2(TitledPage):
    '''
    Wizard page that contains fields for setting video camera ports
    '''
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.scrolledWindow = wxScrolledWindow(self, -1, size = wxSize(100,100), style = wxSIMPLE_BORDER)
        self.scrolledWindow.SetScrollbars(0,20,15,8)
        self.text = wxStaticText(self, -1, "Choose appropriate camera settings from the drop down boxes below. If the camera settings \nare wrong, your video might show up blue or black and white.")
        self.text2 = wxStaticText(self, -1, "Installed capture devices")
        self.text2.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))
        
        self.scrolledWindow.SetBackgroundColour('white')
        self.nodeClient = nodeClient
        self.cameras = []
        self.widgets = []
        self.cameraPorts = dict()
        self.gridSizer = None
        self.lastUrl = None
        self.__layout()

    def GetCameraPorts(self):
        ''' returns a dictionary with capture card as key and selected port option as value.'''
        for widget in self.widgets:
            cameraText, portWidget = widget
            self.cameraPorts[cameraText.GetLabel()] = ''
                
        return self.cameraPorts
        
    def SetCaptureCards(self, cardList):
        '''
        Adds installed cameras and their port options to the page
        '''
        
        self.scrolledWindow.DestroyChildren()
        
        self.cameras = cardList
        nrOfCameras = len(self.cameras)
        
        if self.gridSizer:
            # Remove old camera texts and camera options
            for widget in self.widgets:
                cameraText, portWidget = widget
                cameraText.Destroy()
                portWidget.Destroy()

            del self.widgets[0:]

            # Remove the old sizer
            self.boxSizer.Remove(self.gridSizer)
            
        # Create a new sizer and add it
        self.gridSizer  = wxFlexGridSizer(nrOfCameras, 2, 6, 6)
        self.boxSizer.Add(self.gridSizer, 1, wxALL | wxEXPAND, 5)
       
        # No cameras are installed
        if nrOfCameras == 0:
            text = "No cameras found."
            self.gridSizer.Add(wxStaticText(self.scrolledWindow, -1, text))
            
        i = 0
        # Add camera widgets
        for camera in self.cameras:
            cameraText = wxStaticText(self.scrolledWindow, -1, self.cameras[i].name)
            ports = []

            # Save widgets so we can delete them later
            self.widgets.append((cameraText, ''))          
            self.gridSizer.Add(cameraText, 0, wxALIGN_CENTER)
                
        self.gridSizer.AddGrowableCol(1)
        self.scrolledWindow.Layout()
        self.Layout()

    def GetValidity(self):
        return true
    
    def __layout(self):
        '''
        Handles UI layout
        '''
        if IsWindows():
            # For some reason the static text doesn't get the right size on windows
            self.text2.SetSize(wxSize(150, 20))

        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add((10,10))
        self.sizer.Add(self.text2, 0, wxLEFT, 5)
        self.sizer.Add(self.scrolledWindow, 1, wxEXPAND|wxLEFT|wxRIGHT, 5)
        self.boxSizer = wxBoxSizer(wxVERTICAL)
        self.boxSizer.Add((10,10))
        self.scrolledWindow.SetSizer(self.boxSizer)
        self.scrolledWindow.SetAutoLayout(1)

                       
class VideoDisplayWindow(TitledPage):
    '''
    Wizard page that contains fields for setting video display machine
    '''
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.nodeClient = nodeClient
        self.text = wxStaticText(self, -1, "Which machine displays your video?")
        self.machineText = wxStaticText(self, -1, "Machine Name:")
        self.portText = wxStaticText(self, -1, "Service Manager Port:")
        self.MACHINE_ID = wxNewId()
        self.PORT_ID =  wxNewId()
        self.CHECK_ID = wxNewId()
        self.services = browser.GetServices()
        hostnames = self.services.keys()
        if nodeClient.app.GetHostname() in hostnames:
            hostnameToSelect = nodeClient.app.GetHostname()
        else:
            hostnameToSelect = hostnames[0]
        self.machineCtrl = wxComboBox(self, self.MACHINE_ID, choices=hostnames,
                                    name=hostnameToSelect)
        self.machineCtrl.SetValue(hostnameToSelect)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "11000")
        self.checkBox = wxCheckBox(self, self.CHECK_ID,
                                   "I do not want to use a video display machine (you will not be able to see video).")
        
        # The result after clicking the test button
        # True - we can connect to current machine
        # False - can not connect to current machine
        # None - didn't try connecting yet
        self.canConnect = None
        self.__SetEvents()
        self.Layout()
    
    def __SetEvents(self):
        EVT_COMBOBOX(self.machineCtrl, self.MACHINE_ID, self.OnSelect)
        EVT_TEXT(self.portCtrl, self.PORT_ID, self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)

    def EnterText(self, event):
        '''
        This method is called when user enters text in a text control
        '''   
        self.canConnect = None
        
    def OnSelect(self,event):
        selectedHostname = self.machineCtrl.GetValue()
        if selectedHostname in self.services.keys():
            url = self.services[selectedHostname]
            hostport = urlparse.urlparse(url)[1]
            parts = hostport.split(':')
            if len(parts) > 1:
                port = parts[1]
                self.portCtrl.SetValue(port)
        
    def GetValidity(self):
        '''
        Is called when the next button is clicked. It tests if a service manager is running on
        the specified machine and port. 
        '''
        if self.checkBox.GetValue():
            return true

        # A uri built with empty host will point at local host, to
        # avoid misunderstandings the user have to give a machine name.
        if self.machineCtrl.GetValue() == "":
            MessageDialog(self, "Could not connect. Is a service manager running\nat given machine and port?",  
                          style = wxICON_ERROR|wxOK)
            return false

        # Verify access to machine
        wxBeginBusyCursor()
        try:
            hostname = HostnameFromServiceName(self.machineCtrl.GetValue())
            self.nodeClient.CheckServiceManager(self.machineCtrl.GetValue(), self.portCtrl.GetValue())
            self.canConnect = true
            
        except:
            log.exception("VideoDisplayWindow.Validate: Service manager is not started")
            self.canConnect = false

        wxEndBusyCursor()
        
        if self.canConnect:
            return true
            
        else:
            MessageDialog(self, "Could not connect. Is a service manager running\nat given machine and port?",  
                          style = wxICON_ERROR|wxOK)
            return false
        
    def CheckBoxEvent(self, event):
        '''
        Disable all options if user decides not to use a capture machine
        '''
        if self.checkBox.GetValue():
            # Checked
            self.machineText.Enable(false)
            self.portText.Enable(false)
            self.machineCtrl.Enable(false)
            self.portCtrl.Enable(false)
         
        else:
            # Not checked
            self.machineText.Enable(true)
            self.portText.Enable(true)
            self.machineCtrl.Enable(true)
            self.portCtrl.Enable(true)
                               
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add((20,20))
        
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add((10,10))
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        self.sizer.Add((20, 20))

        
class AudioWindow(TitledPage):
    '''
    Wizard page that contains fields for setting audio machine
    '''
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.nodeClient = nodeClient
        self.text = wxStaticText(self, -1, "Which machine controls your microphones and speakers?")
        self.machineText = wxStaticText(self, -1, "Machine Name:")
        self.portText = wxStaticText(self, -1, "Service Manager Port:")
        self.MACHINE_ID = wxNewId()
        self.PORT_ID =  wxNewId()
        self.CHECK_ID = wxNewId()
        self.services = browser.GetServices()
        hostnames = self.services.keys()
        if nodeClient.app.GetHostname() in hostnames:
            hostnameToSelect = nodeClient.app.GetHostname()
        else:
            hostnameToSelect = hostnames[0]
        self.machineCtrl = wxComboBox(self, self.MACHINE_ID, choices=hostnames,
                                    name=hostnameToSelect)
        self.machineCtrl.SetValue(hostnameToSelect)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "11000")
        self.checkBox = wxCheckBox(self, self.CHECK_ID,
                                   "I do not want to use an audio machine (you will not be able to hear or send audio).")
        self.canConnect = None
        self.__SetEvents()
        self.Layout()

    def __SetEvents(self):
        EVT_TEXT(self.machineCtrl, self.MACHINE_ID, self.EnterText)
        EVT_COMBOBOX(self.machineCtrl, self.MACHINE_ID, self.OnSelect)
        EVT_TEXT(self.portCtrl, self.PORT_ID , self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)

    def EnterText(self, event):
        '''
        This method is called when a user enters text in a text control
        '''   
        self.canConnect = None
        
    def OnSelect(self,event):
        selectedHostname = self.machineCtrl.GetValue()
        if selectedHostname in self.services.keys():
            url = self.services[selectedHostname]
            hostport = urlparse.urlparse(url)[1]
            parts = hostport.split(':')
            if len(parts) > 1:
                port = parts[1]
                self.portCtrl.SetValue(port)
        
    def GetValidity(self):
        '''
        Is called when the next button is clicked. It tests if a service manager is running on
        the specified machine and port. 
        '''
        if self.checkBox.GetValue():
            return true

        # A uri built with empty host will point at local host, to
        # avoid misunderstandings the user have to give a machine name.
        if self.machineCtrl.GetValue() == "":
            MessageDialog(self, "Could not connect. Is a service manager running\nat given machine and port?",  
                          style = wxICON_ERROR|wxOK)
            return false
        
        wxBeginBusyCursor()
        try:
            hostname = HostnameFromServiceName(self.machineCtrl.GetValue())
            port = self.portCtrl.GetValue()
            self.nodeClient.CheckServiceManager(self.machineCtrl.GetValue(), port)
            self.canConnect = true
        except:
            log.exception("AudioWindow.Validate: Service manager is not started")
            self.canConnect = false

        wxEndBusyCursor()
  
        if self.canConnect:
            return true
        else:
            MessageDialog(self, "Could not connect. Is a service manager running\nat %s:%s?" % (hostname,port),  
                          style = wxICON_ERROR|wxOK)
            return false
    
    def CheckBoxEvent(self, event):
        '''
        Disable all options if user decides not to use an audio machine
        '''
        if self.checkBox.GetValue():
            # Checked
            self.machineText.Enable(false)
            self.portText.Enable(false)
            self.machineCtrl.Enable(false)
            self.portCtrl.Enable(false)
            
        else:
            # Not checked
            self.machineText.Enable(true)
            self.portText.Enable(true)
            self.machineCtrl.Enable(true)
            self.portCtrl.Enable(true)
                                        
    def Layout(self):
        '''
        Handles UI layout
        '''
        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add((20,20))
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        self.sizer.Add((10,10))
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        self.sizer.Add((20, 20))


class ConfigWindow(TitledPage):
    '''
    Wizard page giving a summary of node configuration.
    '''
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.nodeClient = nodeClient
        self.audioUrl = None
        self.videoCaptUrl = None
        self.videoDispUrl = None
        self.info = wxStaticText(self, -1, 
                                 "This is your node configuration. Click 'Back' if you want to change something.")
        self.vCapHeading = wxStaticText(self, -1, "Video Capture Machine", style = wxALIGN_LEFT)
        self.vCapHeading.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))
        self.vDispHeading = wxStaticText(self, -1, "Video Display Machine", style = wxALIGN_LEFT)
        self.vDispHeading.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))

        self.audioHeading = wxStaticText(self, -1, "Audio Machine", style = wxALIGN_LEFT)
        self.audioHeading.SetFont(wxFont(wxNORMAL_FONT.GetPointSize(), wxNORMAL, wxNORMAL, wxBOLD))
        self.vCapMachineText = wxStaticText(self, -1, "")
        self.vDispMachineText = wxStaticText(self, -1, "")
        self.audioMachineText = wxStaticText(self, -1, "")
        self.configName = wxStaticText(self, -1, "Configuration Name: ")
        self.configNameCtrl = wxTextCtrl(self, -1, "")
        self.CHECK_ID = wxNewId()
        self.checkBox = wxCheckBox(self, self.CHECK_ID, 
                            "Always use this node setup for Access Grid meetings (default configuration)")
        self.checkBox.SetValue(true)
        self.Layout()

    def SetAudio(self, host, port, flag):
        '''Enters appropriate text for audio machine'''
        if not flag:
            self.audioMachineText.SetLabel("%s using port %s." %(host, port))
            self.audioUrl = "http://"+ host + ":"+ port + "/ServiceManager"
            self.audioMachine = host
            self.audioPort = port
                      
        else:
            self.audioMachineText.SetLabel("Do not use an audio machine")
            self.audioUrl = None
        
    def SetVideoC(self, host, port, flag, cameraPortDict):
        '''Enters appropriate text for video capture machine'''
        if not flag:
            self.cameraPorts = cameraPortDict
            self.vCapMachineText.SetLabel("%s using port %s." %(host, port))
            self.videoCaptUrl = "http://"+ host + ":"+ port + "/ServiceManager"
            self.videoCaptMachine = host
            self.videoCaptPort = port
            
        else:
            self.cameraPorts = None
            self.vCapMachineText.SetLabel("Do not use a video capture machine")
            self.videoCaptUrl = None
            
    def SetVideoD(self,  host, port, flag):
        '''Enters appropriate text for video display machine'''
        if not flag:
            self.vDispMachineText.SetLabel("%s using port %s." %(host, port))
            self.videoDispUrl = "http://"+ host + ":"+ port + "/ServiceManager"
            self.videoDispMachine = host
            self.videoDispPort = port
        else:
            self.vDispMachineText.SetLabel("Do not use a video display machine")
            self.videoDispUrl = None
          
    def GetValidity(self):
        """
        Adds service managers for each machine to the node service. For each
        service manager, appropriate services are added. Then save the configuration
        possibly as default.
        """
        wxBeginBusyCursor()
        errors = ""

        configName = self.configNameCtrl.GetValue()
        
        
        if configName == "":
            MessageDialog(self, "Please enter a name for this configuration.", "Enter Configuration Name")
            wxEndBusyCursor()
            return false

        if string.find(configName, "/") != -1 or string.find(configName, "\\") != -1:
            info = "Configuration name %s is invalid." % configName
            dlg = wxMessageDialog(None, info, "Invalid Configuration Name", style = wxOK | wxICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            wxEndBusyCursor()
            return false
            
            
        configs = []

        # Get known configurations from the Node Service
        try:
            configs = self.nodeClient.GetConfigurations()
        except:
            log.exception("ConfigWindow.Validate: Could not retrieve configurations.")
      
        # Confirm overwrite
        if configName in configs:
            text ="The configuration %s already exists. Do you want to overwrite?" % (configName,)
            dlg = wxMessageDialog(self, text, "Confirm",
                                  style = wxICON_INFORMATION | wxOK | wxCANCEL)
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret != wxID_OK:
                wxEndBusyCursor()
                # User does not want to overwrite.
                return false
                
        # Build up config to send to writer
        config = {}
        if self.videoCaptUrl and self.cameraPorts:
            for capture in self.cameraPorts.keys():
                service = [ 'VideoProducerService.zip', capture, [] ]
                if self.videoCaptUrl in config.keys():
                    config[self.videoCaptUrl].append( service )
                else:
                    config[self.videoCaptUrl] = [ service ]
        if self.videoDispUrl:
            service = [ 'VideoConsumerService.zip', None, [] ]
            if self.videoDispUrl in config.keys():
                config[self.videoDispUrl].append(service)
            else:
                config[self.videoDispUrl] = [ service ]
        if self.audioUrl:
            service = [ 'AudioService.zip', None, [] ]
            if self.audioUrl in config.keys():
                config[self.audioUrl].append(service)
            else:
                config[self.audioUrl] = [ service ]
            
        # Write the node config file
        WriteNodeConfig(configName,config)

        # Set configuration as default
        setAsDefault = self.checkBox.GetValue()
        if setAsDefault:
            prefs = self.nodeClient.app.GetPreferences()
            prefs.SetPreference(Preferences.NODE_CONFIG,configName)
            prefs.SetPreference(Preferences.NODE_CONFIG_TYPE,'user')
            prefs.StorePreferences()
    
        if errors != "":
            ErrorDialog(self, errors, "Error", logFile = NODE_SETUP_WIZARD_LOG)
        else:
            messageText = "New configuration written to " + configName
            if setAsDefault:
                messageText += "\nand set as default node configuration"
            MessageDialog(self, messageText,  
                          style = wxICON_INFORMATION|wxOK)
     
        wxEndBusyCursor()
        return true
                       
    def Layout(self):
        '''
        Handles UI layout
        '''
        if IsWindows():
            # For some reason the static text doesn't get the right size on windows
            self.vCapHeading.SetSize(wxSize(150, 20))
            self.vDispHeading.SetSize(wxSize(150, 20))
            self.audioHeading.SetSize(wxSize(100, 20))
                     
        self.sizer.Add(self.info, 0, wxALL, 5)
        self.sizer.Add((20, 20))
        box = wxBoxSizer(wxHORIZONTAL)
       
        box.Add(self.vCapHeading, 0, wxALIGN_CENTER)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)

        self.sizer.Add((5,5))
        self.sizer.Add(self.vCapMachineText, 0, wxLEFT | wxEXPAND, 30)
        self.sizer.Add((10, 10))

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.vDispHeading, 0, wxALIGN_CENTER)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)
        
        self.sizer.Add((5,5))
        self.sizer.Add(self.vDispMachineText, 0, wxLEFT | wxEXPAND, 30)
        self.sizer.Add((10, 10))
        
        box = wxBoxSizer(wxHORIZONTAL)
       
        box.Add(self.audioHeading)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)

        self.sizer.Add((5,5))
        self.sizer.Add(self.audioMachineText, 0, wxLEFT | wxEXPAND, 30)

        self.sizer.Add((5,5))
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.configName, 0, wxCENTER|wxALL, 5)
        box.Add(self.configNameCtrl, 1, wxALL, 5)
        self.sizer.Add(box, 0, wxEXPAND)

        self.sizer.Add((20,20))
        self.sizer.Add(self.checkBox, 0, wxCENTER, 5)



class NodeClient:
    '''
    The node configuration wizard uses this class for all node interactions to
    separate user interface code from node specific code. This class contains no
    user interface components.
    '''
    def __init__(self, app = None):
        self.node = None
        self.app = app

    def ConnectToNodeService(self):
        '''
        Connects to an already running node service
        '''

        if not self.app:
            self.app = Service().instance()

            #Initialize node service
            try:
                self.app.Initialize("NodeService")
            except Exception, e:
                log.exception("NodeClient: init failed. Exiting.")
                sys.exit(-1)
        
        hostname = SystemConfig.instance().GetHostname()
        port = 11000

        url = "http://%s:%s/NodeService"%(hostname, port)
        self.node = AGNodeServiceIW(url)
        log.info("Connected to node service: %s", url)

        url = "http://%s:%s/ServiceManager"%(hostname, port)
        self.serviceManagerIW = AGServiceManagerIW(url)
        log.info("Connected to service manager: %s", url)
    
    def StartNodeService(self):
        '''
        Starts a node service, assumes no service is already started.
        '''
        if not self.app:
            self.app = Service().instance()

            #Initialize node service
            try:
                self.app.Initialize("NodeService")
            except Exception, e:
                log.exception("NodeClient: init failed. Exiting.")
                sys.exit(-1)
        
        hostname = SystemConfig.instance().GetHostname()
        port = 11000
        self.server = InsecureServer((hostname, port)) #, debug = self.app.GetDebugLevel())

        #
        # Start a node service
        #        
        self.nodeService = AGNodeService(self.app)
        nsi = AGNodeServiceI(self.nodeService)
        nsi.impl = self.nodeService
        nsurl = self.server.RegisterObject(nsi, path="/NodeService")
        self.node = AGNodeServiceIW(nsurl)
        log.info("Started node service: %s", nsurl)
        
        #
        # Start a service manager
        #
        self.serviceManager = AGServiceManager(self.server,self.app)
        smi = AGServiceManagerI(self.serviceManager)
        smi.impl = self.serviceManager
        smurl = self.server.RegisterObject(smi, path="/ServiceManager")
        self.serviceManagerIW = AGServiceManagerIW(smurl)
        log.info("Started service manager: %s", smurl)
        
        try:
            Publisher(hostname,AGServiceManager.ServiceType,
                                            smurl,
                                            port)
        except:
            log.exception('Error advertising service manager')
        try:
            Publisher(hostname,AGNodeService.ServiceType,
                                       nsurl,
                                       port)
        except:
            log.exception('Error advertising node service')

        
        self.server.RunInThread()
        
    def Stop(self):
        # Exit cleanly
        try:
            self.nodeService.Stop()
        except:
            raise Exception, "Can not stop node service"
        try:
            self.server.Stop()
        except:
            raise Exception, 'Can not stop server'
                               
    def GetNodeService(self):
        return self.node
   
    def AddServiceManager(self, name, url):
        ''' Adds a service manager to the node service'''
        self.node.AddServiceManager(url)
   
    def AddService(self, serviceManagerUrl, type, data = None):
        serviceAvailable = None
        
        serviceManager = AGServiceManagerIW(serviceManagerUrl)

        # Check if we have a video producer service installed
        serviceList = serviceManager.GetServicePackageDescriptions()
        for service in serviceList:
            if service.name == type:
                serviceAvailable = service

        if serviceAvailable:
            if type == "VideoProducerService":
                # Add video producer service for each capture card
                
                for captureCard in self.cameraList:
                    log.debug("NodeClient.AddService: Video Producer Service %s %s %s" %
                                (serviceAvailable.servicePackageFile, 
                                 serviceManagerUrl, captureCard))
                    serviceDesc = serviceManager.AddServiceByName(serviceAvailable.name,
                                                                  captureCard)

                    # Get service configuration
                    conf = AGServiceIW(serviceDesc.uri).GetConfiguration()
                                                                                
                    # Set camera port type
                    if data and data.has_key(captureCard.resource):
                        conf.append(ValueParameter("port", data[captureCard.name]))
                        AGServiceIW(serviceDesc.uri).SetConfiguration(conf)

            else: # Video consumer or audio
                log.debug("NodeClient.AddService: Audio or video consumer service")
                self.node.AddService(serviceAvailable,
                                     serviceManagerUrl, None, None)
                
        else:
            # The service does not exist in your
            # node configuration. Check services directory to see
            # if you have it.
            raise ServiceUnavailableException()
                             
    def CheckServiceManager(self, machine, port):
        '''
        Checks to see if a video producer service is running on a service manager located
        at machine using port.
        '''
        mgrUri = "http://"+ machine + ":"+ port + "/ServiceManager"
              
        # Is the service manager running on the specified machine and port?

        # Remove current services from service manager
        AGServiceManagerIW(mgrUri).RemoveServices()
                      
    def GetCaptureCards(self, machine, port):
        '''
        Returns a list of video capture cards.
        '''
        self.cameraList = []
        resourceList = []
        mgrUri = "http://"+ machine + ":"+ port + "/ServiceManager"
      
        try:
            # Get available services
            resourceList = AGServiceManagerIW(mgrUri).GetResources()
        except:
            log.exception("NodeClient.GetCaptureCards: Could not find resources")
            return []

        for resource in resourceList:
            self.cameraList.append(resource)

        return self.cameraList


    def GetConfigurations(self):
        '''
        Returns a list of existing configuration names.
        '''
        return self.node.GetConfigurations()

def main():
    global browser

    browser = Browser(AGServiceManager.ServiceType)
    browser.Start()

    # Create the wxpython app
    wxapp = wxPySimpleApp()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()
    
    # Try to initialize
  
    try:
        app.Initialize("NodeSetupWizard")
    except MissingDependencyError, e:
        if e.args[0] == 'SSL':
            msg = "The installed version of Python has no SSL support.  Check that you\n"\
                  "have installed Python from python.org, or ensure SSL support by\n"\
                  "some other means."
        else:
            msg = "The following dependency software is required, but not available:\n\t%s\n"\
                    "Please satisfy this dependency and restart the software"
            msg = msg % e.args[0]
        MessageDialog(None,msg, "Initialization Error",
                      style=wxICON_ERROR )
        sys.exit(-1)
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        MessageDialog(None,
                      "The following error occurred during initialization:\n\n\t%s %s" % (e.__class__.__name__,e), 
                      "Initialization Error",
                      style=wxICON_ERROR )
        sys.exit(-1)

    

    # Create a progress dialog
    versionText = "Version %s %s" % (str(GetVersion()), str(GetStatus()) )
    startupDialog = ProgressDialog(None,icons.getSplashBitmap(), 100, versionText)
    startupDialog.Show()
        
    debug = app.GetDebugLevel()

    startupDialog.UpdateGauge("Initializing the Node Setup Wizard.",25)
    nodeSetupWizard = NodeSetupWizard(None, debug, startupDialog, app)
    
    browser.Stop()
       
# The main block
if __name__ == "__main__":
    main()
