#!/usr/bin/python2
#-----------------------------------------------------------------------------
# Name:        NodeSetupWizard.py
# Purpose:     Wizard for setup and test a room based node configuration
# Created:     2003/08/12
# RCS_ID:      $Id: NodeSetupWizard.py,v 1.28 2004-04-14 15:30:47 turam Exp $ 
# Copyright:   (c) 2003
# Licence:     See COPYING.txt
#-----------------------------------------------------------------------------

import os
import string
import getopt

# Imports for user interface
from wxPython.wx import *
from wxPython.wizard import *

# Agtk specific imports
from AccessGrid.Toolkit import WXGUIApplication
from AccessGrid import Log

from AccessGrid.Platform import IsWindows

from AccessGrid.AGNodeService import AGNodeService
from AccessGrid.AGParameter import ValueParameter
from AccessGrid.Descriptions import AGServiceManagerDescription

from AccessGrid.Utilities import NODE_SETUP_WIZARD_LOG

from AccessGrid.UIUtilities import MessageDialog, ErrorDialog
from AccessGrid.UIUtilities import ProgressDialog

from AccessGrid.AGService import AGServiceIW
from AccessGrid.AGServiceManager import AGServiceManagerIW

log = Log.GetLogger(Log.NodeSetupWizard)

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
        title.SetFont(wxFont(14, wxNORMAL, wxNORMAL, wxBOLD))
        self.sizer.AddWindow(title, 0, wxALL|wxEXPAND, 5)
        self.sizer.AddWindow(wxStaticLine(self, -1), 0, wxEXPAND|wxALL, 5)
        self.sizer.Add(10, 10)
               
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
    def __init__(self, parent, debugMode, log):
        wxWizard.__init__(self, parent, 10,"Setup Node", wxNullBitmap)
        '''
        This class creates a wizard for node setup
        '''
        self.debugMode = debugMode
        self.log = log

        self.step = 1
        self.SetPageSize(wxSize(510, 310))
        self.nodeClient = NodeClient()
        
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

        # Start the node service which will store the configuration
        try:
            self.nodeClient.StartNodeService()
        except:
            log.exception("NodeSetupWizard.__init__: Can not start node service")
            ErrorDialog(self, "Can not start Node Setup Wizard.",
                        "Error", style = wxICON_ERROR|wxOK, logFile = NODE_SETUP_WIZARD_LOG)

        else:
            # Run the wizard
            self.RunWizard(self.page1)

            # Wizard finished
            
            # Stop node service
            node = self.nodeClient.GetNodeService()

            if node:
                try:
                    node.Stop()
                except:
                    log.exception("NodeSetupWizard.__init__: Can not stop node service")

    def ChangingPage(self, event):
        '''
        This method is called when a page is changed in the wizard
        '''
        dir = event.GetDirection()
        page = event.GetPage()
        forward = 1
        backward = 0
              
        # Show users configuration in last page
        if isinstance(page.GetNext(), ConfigWindow):
            p = self.page2
            page.GetNext().SetVideoC(p.machineCtrl.GetValue(),
                                     p.portCtrl.GetValue(), p.checkBox.GetValue(),
                                     self.page3.GetCameraPorts())
            p = self.page4
            page.GetNext().SetVideoD(p.machineCtrl.GetValue(),
                                     p.portCtrl.GetValue(), p.checkBox.GetValue())
            p = self.page5
            page.GetNext().SetAudio(p.machineCtrl.GetValue(),
                                    p.portCtrl.GetValue(), p.checkBox.GetValue())

        # Check to see if values are entered correctly
        if dir == forward:
            if not page.Validate():
                # Ignore event
                event.Veto()

                        
class WelcomeWindow(TitledPage):
    '''
    First page of wizard contains introduction text.
    '''
    def __init__(self, parent, title):
        TitledPage.__init__(self, parent, title)
        self.info = wxStaticText(self, -1, "This wizard will help you setup and test your Node. The node is your configuration of machines \ncontrolling cameras, speakers, and microphones.")
        self.beforeText = wxStaticText(self, -1,"Before continuing:")
        self.beforeText.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.beforeText2 =  wxStaticText(self, -1,
                                "Make sure you have Service Managers running on each machine in your node.")
        self.contText =  wxStaticText(self, -1, "Click 'Next' to continue.", style = wxCENTER)
       
        self.Layout()
          
    def Layout(self):
        ''' Handles UI layout '''
        self.sizer.Add(self.info, 0, wxALL, 5)
        self.sizer.Add(10,10)
        self.sizer.Add(self.beforeText, 0, wxALL|wxEXPAND, 5)
        self.sizer.Add(self.beforeText2, 0, wxALL, 5)
        self.sizer.Add(10, 100)
        self.sizer.Add(self.contText, 0, wxALIGN_CENTER|wxALL|wxEXPAND, 5)
        

class VideoCaptureWindow(TitledPage):
    '''
    Wizard page that contains fields for setting video capture machine
    '''
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
        self.machineCtrl = wxTextCtrl(self, self.MACHINE_ID)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "12000")
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
        EVT_TEXT(self.portCtrl, self.PORT_ID, self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)
  
    def EnterText(self, event):
        '''
        Is called whever the user enters text in a text control
        '''   
        # Connect status should only reflect current machine
        self.canConnect = None
            
    def Validate(self):
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
            self.nodeClient.CheckServiceManager(self.machineCtrl.GetValue(),
                                                   self.portCtrl.GetValue())
            self.canConnect = true
        except:
            log.exception("VideoCaptureWindow.Validate: Check service manager failed")
            self.canConnect = false
            
        if self.canConnect:
            cards = []
            try:
                cards = self.nodeClient.GetCaptureCards(self.machineCtrl.GetValue(), self.portCtrl.GetValue())
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
        self.sizer.Add(20,20)
        
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        self.sizer.Add(10,10)
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        
        self.sizer.Add(20, 20)

                
class VideoCaptureWindow2(TitledPage):
    '''
    Wizard page that contains fields for setting video camera ports
    '''
    def __init__(self, parent, nodeClient, title):
        TitledPage.__init__(self, parent, title)
        self.scrolledWindow = wxScrolledWindow(self, -1, size = wxSize(100,100), style = wxSIMPLE_BORDER)
        self.scrolledWindow.SetScrollbars(0,20,15,8)
        self.text = wxStaticText(self, -1, "Choose appropriate camera settings from the drop down boxes below. If the camera settings \nare wrong, your video might show up blue or black and white.")
        self.text2 = wxStaticText(self, -1, "Installed cameras")
        self.text2.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        
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
            self.cameraPorts[cameraText.GetLabel()] = portWidget.GetValue()
                
        return self.cameraPorts
        
    def SetCaptureCards(self, cardList):
        '''
        Adds installed cameras and their port options to the page
        '''
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
            cameraText = wxStaticText(self.scrolledWindow, -1, self.cameras[i].resource)
            ports = []

            # Fill in camera port options in drop down box
            for port in self.cameras[i].portTypes:
                ports.append(port)
            i = i + 1
            cameraOption = wxComboBox(self.scrolledWindow, -1, style = wxLB_SORT, size = wxSize(100, 50), 
                                      choices = ports, value = ports[0])

            # Save widgets so we can delete them later
            self.widgets.append((cameraText, cameraOption))          
            self.gridSizer.Add(cameraText, 0, wxALIGN_CENTER)
            self.gridSizer.Add(cameraOption, 0, wxEXPAND)
                
        self.gridSizer.AddGrowableCol(1)
        self.scrolledWindow.Layout()
        self.Layout()
    
    def __layout(self):
        '''
        Handles UI layout
        '''
        if IsWindows():
            # For some reason the static text doesn't get the right size on windows
            self.text2.SetSize(wxSize(150, 20))

        self.sizer.Add(self.text, 0, wxALL, 5)
        self.sizer.Add(10,10)
        self.sizer.Add(self.text2, 0, wxLEFT, 5)
        self.sizer.Add(self.scrolledWindow, 1, wxEXPAND|wxLEFT|wxRIGHT, 5)
        self.boxSizer = wxBoxSizer(wxVERTICAL)
        self.boxSizer.Add(10,10)
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
        self.machineCtrl = wxTextCtrl(self, self.MACHINE_ID)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "12000")
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
        EVT_TEXT(self.machineCtrl, self.MACHINE_ID, self.EnterText)
        EVT_TEXT(self.portCtrl, self.PORT_ID, self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)

    def EnterText(self, event):
        '''
        This method is called when user enters text in a text control
        '''   
        self.canConnect = None
        
    def Validate(self):
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
            self.nodeClient.CheckServiceManager(self.machineCtrl.GetValue(), self.portCtrl.GetValue())
            self.canConnect = true
            
        except:
            log.info("VideoDisplayWindow.Validate: Service manager is not started")
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
        self.sizer.Add(20,20)
        
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(10,10)
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        self.sizer.Add(20, 20)

        
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
        self.machineCtrl = wxTextCtrl(self, self.MACHINE_ID)
        self.portCtrl = wxTextCtrl(self, self.PORT_ID, "12000")
        self.checkBox = wxCheckBox(self, self.CHECK_ID,
                                   "I do not want to use an audio machine (you will not be able to hear or send audio).")
        self.canConnect = None
        self.__SetEvents()
        self.Layout()

    def __SetEvents(self):
        EVT_TEXT(self.machineCtrl, self.MACHINE_ID, self.EnterText)
        EVT_TEXT(self.portCtrl, self.PORT_ID , self.EnterText)
        EVT_CHECKBOX(self, self.CHECK_ID, self.CheckBoxEvent)

    def EnterText(self, event):
        '''
        This method is called when a user enters text in a text control
        '''   
        self.canConnect = None
        
    def Validate(self):
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
            self.nodeClient.CheckServiceManager(self.machineCtrl.GetValue(), self.portCtrl.GetValue())
            self.canConnect = true
        except:
            log.info("AudioWindow.Validate: Service manager is not started")
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
        self.sizer.Add(20,20)
        
        gridSizer = wxFlexGridSizer(2, 2, 6, 6)
        gridSizer.Add(self.machineText)
        gridSizer.Add(self.machineCtrl, 0, wxEXPAND)
        gridSizer.Add(self.portText)
        gridSizer.Add(self.portCtrl, 0, wxEXPAND)
        gridSizer.AddGrowableCol(1)
        self.sizer.Add(gridSizer, 0, wxALL | wxEXPAND, 5)
        self.sizer.Add(10,10)
        self.sizer.Add(self.checkBox, 0, wxEXPAND)
        self.sizer.Add(20, 20)


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
        self.vCapHeading.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.vDispHeading = wxStaticText(self, -1, "Video Display Machine", style = wxALIGN_LEFT)
        self.vDispHeading.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.audioHeading = wxStaticText(self, -1, "Audio Machine", style = wxALIGN_LEFT)
        self.audioHeading.SetFont(wxFont(wxDEFAULT, wxNORMAL, wxNORMAL, wxBOLD))
        self.vCapMachineText = wxStaticText(self, -1, "")
        self.vDispMachineText = wxStaticText(self, -1, "")
        self.audioMachineText = wxStaticText(self, -1, "")
        self.CHECK_ID = wxNewId()
        self.checkBox = wxCheckBox(self, self.CHECK_ID, 
                            "Always use this node setup for Access Grid meetings (default configuration)")
        self.checkBox.SetValue(true)
        self.configName = wxStaticText(self, -1, "Configuration Name: ")
        self.configNameCtrl = wxTextCtrl(self, -1, "")
        self.Layout()

    def SetAudio(self, host, port, flag):
        '''Enters appropriate text for audio machine'''
        if not flag:
            self.audioMachineText.SetLabel("%s using port %s." %(host, port))
            self.audioUrl = "https://"+ host + ":"+ port + "/ServiceManager"
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
            self.videoCaptUrl = "https://"+ host + ":"+ port + "/ServiceManager"
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
            self.videoDispUrl = "https://"+ host + ":"+ port + "/ServiceManager"
            self.videoDispMachine = host
            self.videoDispPort = port
        else:
            self.vDispMachineText.SetLabel("Do not use a video display machine")
            self.videoDispUrl = None
          
    def Validate(self):
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
                              
        if self.videoCaptUrl:
            text = self.videoCaptMachine+":"+self.videoCaptPort
            try:
                # Add video capture service manager
                self.nodeClient.AddServiceManager(text, self.videoCaptUrl)

            except:
                # We still want to continue even if a service manager is already present
                log.info("ConfigWindow.Validate: Could not add service manager for video capture")
                pass

            try:
                # Add video producer services
                log.debug("ConfigWindow.Validate: Add video producer")
                self.nodeClient.AddService( self.videoCaptUrl, "VideoProducerService", self.cameraPorts)
                
            except ServiceUnavailableException:
                log.exception("ConfigWindow.Validate: Could not add service to video capture machine.")
                errors = errors + "No services supporting video capture are installed.\nThe video capture machine is not added to the configuration.\n\n"
                
            except:
                log.exception("ConfigWindow.Validate: Could not add service to video capture machine.")
                errors = errors + "The video capture machine could not be added to the configuration. An error occured..\n\n"
                
        if self.videoDispUrl:
            text = self.videoDispMachine+":"+self.videoDispPort
            try:
                # Add video display service manager
                self.nodeClient.AddServiceManager(text, self.videoDispUrl)
            except:
                # We still want to continue even if a service manager is already present
                log.info("ConfigWindow.Validate: Could not add service manager for video display")
                pass

            try:
                # Add video display service
                log.debug("ConfigWindow.Validate: Add video display service")
                self.nodeClient.AddService(self.videoDispUrl, "VideoConsumerService")
                
            except ServiceUnavailableException:
                log.exception("ConfigWindow.Validate: Could not add service to video display machine.")
                errors = errors +"No services supporting video display are installed. \nThe video display machine is not added to the configuration.\n\n"
                
            except:
                log.exception("ConfigWindow.Validate: Could not add service to video display machine.")
                errors = errors + "The video display machine could not be added to the configuration. An error occured.\n\n"
                              
        if self.audioUrl:
            text = self.audioMachine+":"+self.audioPort
            try:
                # Add audio service manager
                self.nodeClient.AddServiceManager(text, self.audioUrl)
            except:
                # We still want to continue even if a service manager is already present
                log.exception("ConfigWindow.Validate: Could not add service manager for audio")
                pass

            try:
                # Add audio service
                log.debug("ConfigWindow.Validate: Add audio service")
                self.nodeClient.AddService(self.audioUrl, "AudioService")
                
            except ServiceUnavailableException:
                log.exception("ConfigWindow.Validate: Could not add service to audio machine.")
                errors = errors + "No services supporting audio are installed. \nThe audio machine is not added to the configuration.\n\n"
            except:
                log.exception("ConfigWindow.Validate: Could not add service to audio machine")
                errors = errors + "The audio machine could not be added to the configuration. An error occured.\n\n"
                   
       
        self.name = self.configNameCtrl.GetValue()

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

        # Save configuration
        try:
            self.nodeClient.GetNodeService().StoreConfiguration(self.name)
        except:
            log.exception("ConfigWindow.Validate: Could not store node configuration.")
            errors = errors + "The configuration could not be saved. Error occured.\n\n"
            
            
        # Set configuration as default
        if self.checkBox.GetValue():
             
            try:
                self.nodeClient.GetNodeService().SetDefaultConfiguration(self.name)
            except:
                log.exception("ConfigWindow.Validate: Could not set default configuration.")
                errors = errors + "The configuration could not be set as default. Error occured.\n\n"

    
        if errors != "":
            ErrorDialog(self, errors, "Error", logFile = NODE_SETUP_WIZARD_LOG)
     
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
        self.sizer.Add(20, 20)
        box = wxBoxSizer(wxHORIZONTAL)
       
        box.Add(self.vCapHeading, 0, wxALIGN_CENTER)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)

        self.sizer.Add(5,5)
        self.sizer.Add(self.vCapMachineText, 0, wxLEFT | wxEXPAND, 30)
        self.sizer.Add(10, 10)

        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.vDispHeading, 0, wxALIGN_CENTER)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)
        
        self.sizer.Add(5,5)
        self.sizer.Add(self.vDispMachineText, 0, wxLEFT | wxEXPAND, 30)
        self.sizer.Add(10, 10)
        
        box = wxBoxSizer(wxHORIZONTAL)
       
        box.Add(self.audioHeading)
        box.Add(wxStaticLine(self, -1), 1, wxALIGN_CENTER)
        self.sizer.Add(box, 0, wxEXPAND)

        self.sizer.Add(5,5)
        self.sizer.Add(self.audioMachineText, 0, wxLEFT | wxEXPAND, 30)

        self.sizer.Add(20,20)
        self.sizer.Add(self.checkBox, 0, wxLEFT | wxEXPAND, 5)

        self.sizer.Add(5,5)
        box = wxBoxSizer(wxHORIZONTAL)
        box.Add(self.configName, 0, wxCENTER|wxALL, 5)
        box.Add(self.configNameCtrl, 1, wxALL, 5)
        self.sizer.Add(box, 0, wxEXPAND)


class NodeClient:
    '''
    The node configuration wizard uses this class for all node interactions to
    separate user interface code from node specific code. This class contains no
    user interface components.
    '''
    def __init__(self):
        self.node = None

    def StartNodeService(self):
        self.node = AGNodeService()
        self.serviceList = self.node.GetAvailableServices()
                       
    def GetNodeService(self):
        return self.node
   
    def AddServiceManager(self, name, url):
        ''' Adds a service manager to the node service'''
        self.node.AddServiceManager(AGServiceManagerDescription(name, url))
   
    def AddService(self, serviceManagerUrl, type, data = None):
        serviceAvailable = None

        # Check if we have a video producer service installed
        for service in self.serviceList:
            if service.name == type:
                serviceAvailable = service

        if serviceAvailable:
            if type == "VideoProducerService":
                # Add video producer service for each capture card
                
                for captureCard in self.cameraList:
                    log.debug("NodeClient.AddService: Video Producer Service %s %s %s" %
                                (serviceAvailable.servicePackageUri, 
                                 serviceManagerUrl, captureCard))
                    serviceDesc = self.node.AddService(serviceAvailable,
                                                       serviceManagerUrl, captureCard, None)

                    # Get service configuration
                    conf = AGServiceIW(serviceDesc.uri).GetConfiguration()
                                                                                
                    # Set camera port type
                    conf.parameters.append(ValueParameter("port", data[captureCard.resource]))
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
        mgrUri = "https://"+ machine + ":"+ port + "/ServiceManager"
              
        # Is the service manager running on the specified machine and port?

        # Remove current services from service manager
        AGServiceManagerIW(mgrUri).RemoveServices()
                      
    def GetCaptureCards(self, machine, port):
        '''
        Returns a list of video capture cards.
        '''
        self.cameraList = []
        resorceList = []
        mgrUri = "https://"+ machine + ":"+ port + "/ServiceManager"
      
        try:
            # Get available services
            resourceList = AGServiceManagerIW(mgrUri).GetResources()
        except:
            log.exception("NodeClient.GetCaptureCards: Could not find resources")
            return []

        for resource in resourceList:
            if resource.role == 'producer' and resource.type == 'video':
                self.cameraList.append(resource)

        return self.cameraList


    def GetConfigurations(self):
        '''
        Returns a list of existing configuration names.
        '''
        return self.node.GetConfigurations()

def main():
    log = None

    # Create the wxpython app
    wxapp = wxPySimpleApp()

    # Create a progress dialog
    startupDialog = ProgressDialog("Starting Node Setup Wizard...",
                                   "Initializing AccessGrid Toolkit", 5)
    startupDialog.Show()

    # Init the toolkit with the standard environment.
    app = WXGUIApplication()

    # Try to initialize
    try:
        args = app.Initialize("VenueNodeSetupWizard")
    except Exception, e:
        print "Toolkit Initialization failed, exiting."
        print " Initialization Error: ", e
        sys.exit(-1)
        
    # Get the log
    log = app.GetLog()
    debug = app.GetDebugLevel()
    
    startupDialog.UpdateOneStep("Initializing the Node Setup Wizard.")

    nodeSetupWizard = NodeSetupWizard(None, debug, log)
    
    # Startup complete; kill progress dialog
    startupDialog.Destroy()

    # Spin
    wxapp.SetTopWindow(nodeSetupWizard)
    wxapp.MainLoop()

    wxapp.Destroy()
    
# The main block
if __name__ == "__main__":
    main()
