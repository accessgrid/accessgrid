#-----------------------------------------------------------------------------
# Name:        SharedPresentation.py
# Purpose:     This is the Shared Presentation Software. 
#
# Author:      Ivan R. Judson, Tom Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: SharedPresentation.py,v 1.21 2004-01-28 22:41:08 lefvert Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------

# Normal import stuff
import os
import sys
import getopt
from threading import Thread
import Queue
import shutil

from wxPython.wx import *

from AccessGrid import Platform
if sys.platform == Platform.WIN:
    # Win 32 COM interfaces that we use
    try:
        import win32com
        import win32com.client
    except:
        print "No Windows COM support!"
        sys.exit(1)
else:
    # An OpenOffice/StarOffice Viewer
    # We will add options to make the viewer selectable if we have
    #   a choice of more than one viewer.
    from ImpressViewer import ImpressViewer

# Imports we need from the Access Grid Module
from AccessGrid import Platform
from AccessGrid import DataStore
from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.DataStoreClient import GetVenueDataStore
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.Platform import GetUserConfigDir
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.UIUtilities import MessageDialog

class ViewerSoftwareNotInstalled(Exception):
    pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Viewer code
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PowerPointViewer:
    """
    The PowerPoint Viewer is meant to be a single instance of a Presentation
    viewer. On platforms other than windows or mac, where MS Office isn't
    available there might be a different viewer for the data.

    The specifics for the PowerPoint Viewer are related to using the
    win32com interface for controlling PowerPoint from within
    python. What we do is set self.ppt to a python COM interface of an
    instance of the powerpoint application. From there it's using
    internal COM interfaces to do various operations on the PowerPoint
    Application to make it do what we want.

    Here's a description of what we're keeping track of and why:

    self.ppt -- win32com Interface to an instance of the PowerPoint Application
    self.presentation -- The current presentation.
    self.win -- The window showing a slideshow of the current presentation.
    """

    def __init__(self):
        """
        We aren't doing anything in here because we really don't need
        anything yet. Once things get started up externally, this gets fired
        up through the other methods.
        """
        
        self.ppt = None
        self.presentation = None
        self.win = None

        self.pptAlreadyOpen = 0
        # The filename of the currently open file.
        self.openFile = ""

        from win32com.client import gencache
        import pythoncom
        pythoncom.CoInitialize()
        try:
            gencache.EnsureModule('{91493440-5A91-11CF-8700-00AA0060263B}', 0, 2, 6)
        except:
            raise ViewerSoftwareNotInstalled()

    
    def Start(self):
        """
        This method actually fires up PowerPoint and if specified opens a
        file and starts viewing it.
        """
        # Instantiate the powerpoint application via COM
        self.ppt = win32com.client.Dispatch("PowerPoint.Application")

        if self.ppt.Presentations.Count > 0:
            self.pptAlreadyOpen = 1

        # Make it active (visible)
        self.ppt.Activate()

    def Stop(self):
        """
        This method shuts the powerpoint application down.
        """
        # Turn the slide show off
        self.EndShow()
       

    def Quit(self):
        """
        This method quits the powerpoint application.
        """
        # Close the presentation
        try:
            if self.presentation:
                self.presentation.Close()
        except:
            print 'can not close presentation....continue anyway'
                
        # Exit the powerpoint application, but only if 
        # it was opened by the viewer
        if not self.pptAlreadyOpen:
            self.ppt.Quit()
        
    def LoadPresentation(self, file):
        """
        This method opens a file and starts the viewing of it.
        """

        # Close existing presentation
        try:
            if self.presentation:
                self.presentation.Close()
        except:
            print 'can not close previous presentation...continue anyway'
        # Open a new presentation and keep a reference to it in self.presentation
        
        self.presentation = self.ppt.Presentations.Open(file)
        self.lastSlide = self.presentation.Slides.Count
        self.openFile = file
        
        # Start viewing the slides in a window
        self.presentation.SlideShowSettings.ShowType = win32com.client.constants.ppShowTypeWindow
        self.win = self.presentation.SlideShowSettings.Run()
       
    def Next(self):
        """
        This method moves to the next slide.
        """
        # Move to the next slide
        self.win.View.Next()

    def Previous(self):
        """
        This method moves to the previous slide.
        """
        # Move to the previous slide
        self.win.View.Previous()

    def GoToSlide(self, slide):
        """
        This method moves to the specified slide.
        """
        # Move to the specified Slide
        self.win.View.GotoSlide(int(slide))

    def EndShow(self):
        """
        This method quits the viewing of the current set of slides.
        """
        # Quit the presentation
      
        if self.win:
            self.win.View.Exit()
            self.win = None

    def GetLastSlide(self):
        """
        This method returns the index of the last slide (indexed from 1)
        """
        return self.lastSlide

    def GetSlideNum(self):
        """
        This method returns the index of the current slide
        """
        return self.win.View.CurrentShowPosition

    def GetStepNum(self):
        """
        This method returns the step of the current slide
        """
        return self.win.View.Slide.PrintSteps



# Depending on the platform decide which viewer to use
if sys.platform == Platform.WIN:
    # If we're on Windows we try to use the python/COM interface to PowerPoint
    defaultViewer = PowerPointViewer
elif sys.platform == Platform.LINUX:
    # On Linux the best choice is probably Open/Star Office
    defaultViewer = ImpressViewer
else:
    defaultViewer = None



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# GUI code
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SharedPresentationFrame(wxFrame):

    ID_SYNC = wxNewId()
    ID_LOCALUPLOAD = wxNewId()
    ID_CLEAR = wxNewId()
    ID_EXIT = wxNewId()

    def __init__(self, parent, ID, title, log=None):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition)

        self.log = log
        
        # Initialize callbacks
        noOp = lambda x=0:0
        self.loadCallback = noOp
        #self.clearSlidesCallback = noOp
        self.prevCallback = noOp
        self.nextCallback = noOp
        self.gotoCallback = noOp
        self.masterCallback = noOp
        self.closeCallback = noOp
        self.syncCallback = noOp
        self.exitCallback = noOp
        self.localUploadCallback = noOp

        #
        # Create UI controls
        #
                
        # - Create menu bar
        menubar = wxMenuBar()
        fileMenu = wxMenu()
        self.fileMenu = fileMenu
        fileMenu.Append(self.ID_SYNC,"&Sync", "Sync to app state")
        fileMenu.Append(self.ID_LOCALUPLOAD,"&Upload Local File", "Upload local file to venue.")
        fileMenu.Append(self.ID_CLEAR,"&Clear slides", "Clear the slides from venue")
        fileMenu.AppendSeparator()
        fileMenu.Append(self.ID_EXIT,"&Exit", "Exit")
     	menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        # - Create main panel
        self.panel = wxPanel(self, -1, size = wxSize(320, 260))
        
        # - Create main sizer 
        mainSizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(mainSizer)
    
        mainSizer.Add(self.panel, 1, wxEXPAND)
        
        # - Create panel sizer
        sizer = wxBoxSizer(wxVERTICAL)
        self.panel.SetSizer(sizer)

        # - Create information text
        self.info = wxStaticText(self.panel, -1, "If you want to be the leader of this session, select the master check box below. All presentation files located in the data area of this venue are now available here. Choose a file from these available slides or enter the URL address of your presentation. Click the Load button to open the presentation. \n\nNote: Please, only use this controller window to change slides.")

        sizer.Add(self.info, 1, wxEXPAND | wxALL, 5)
        sizer.Add(wxStaticLine(self.panel, -1), 0, wxEXPAND | wxALL, 5)
              
        # - Create checkbox for master
        self.masterCheckBox = wxCheckBox(self.panel,-1,"Take control as presentation master")
        sizer.Add(5, 5)
        sizer.Add( self.masterCheckBox, 0, wxEXPAND | wxALL, 5)

        # - Create sizer for remaining ctrls
        staticBoxSizer = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        gridSizer = wxFlexGridSizer(2, 3, 5, 5)
        gridSizer.AddGrowableCol(1)
        staticBoxSizer.Add(gridSizer, 0, wxEXPAND)
        sizer.Add(staticBoxSizer, 0, wxEXPAND| wxALL, 5)

        # - Create textctrl for slide url
        staticText = wxStaticText(self.panel, -1, "Slides")
        #self.slidesText = wxTextCtrl(self,-1)
        self.slidesCombo = wxComboBox(self.panel ,wxNewId(), style=wxCB_DROPDOWN|wxCB_SORT)
        self.slidesCombo.Append("")
        self.loadButton = wxButton(self.panel ,-1,"Load", wxDefaultPosition, wxSize(40,21) )

        gridSizer.Add( staticText, 0, wxALIGN_LEFT)
        gridSizer.Add( self.slidesCombo, 1, wxEXPAND | wxALIGN_LEFT)
        gridSizer.Add( self.loadButton, 2, wxALIGN_RIGHT)

        # Don't update the filelist until user becomes a master (it won't 
        #   be needed unless user is a master).
        # self.updateVenueFileList()

        # - Create textctrl for slide num
        staticText = wxStaticText(self.panel, -1, "Slide number")
        self.slideNumText = wxTextCtrl(self.panel ,-1, size = wxSize(40, 20))
        self.goButton = wxButton(self.panel ,-1,"Go", wxDefaultPosition, wxSize(40,21))
        gridSizer.Add( staticText, wxALIGN_LEFT)
        gridSizer.Add( self.slideNumText )
        gridSizer.Add( self.goButton, wxALIGN_RIGHT )

        # - Create buttons for control 
        rowSizer = wxBoxSizer(wxHORIZONTAL)
        self.prevButton = wxButton(self.panel ,-1,"<Prev")
        self.nextButton = wxButton(self.panel ,-1,"Next>")
        rowSizer.Add( self.prevButton , 0, wxRIGHT, 5)
        rowSizer.Add( self.nextButton )

        sizer.Add(rowSizer, 0, wxALIGN_CENTER|wxALL, 5)
        sizer.Add(5,5)
        
        self.SetAutoLayout(1)
        self.Layout()

        # Initially, I'm not the master
        self.SetMaster(0)
               
        # Set up event callbacks
        EVT_TEXT_ENTER(self, self.slidesCombo.GetId(), self.OpenCB)
        EVT_CHECKBOX(self, self.masterCheckBox.GetId(), self.MasterCB)
        EVT_SET_FOCUS(self.slidesCombo, self.ComboCB)
        EVT_BUTTON(self, self.prevButton.GetId(), self.PrevSlideCB)
        EVT_TEXT_ENTER(self, self.slideNumText.GetId(), self.GotoSlideNumCB)
        EVT_BUTTON(self, self.nextButton.GetId(), self.NextSlideCB)
        EVT_BUTTON(self, self.loadButton.GetId(), self.OpenCB)
        EVT_BUTTON(self, self.goButton.GetId(), self.GotoSlideNumCB)

        EVT_MENU(self, self.ID_SYNC, self.SyncCB)
        EVT_MENU(self, self.ID_LOCALUPLOAD, self.LocalUploadCB)
        EVT_MENU(self, self.ID_CLEAR, self.ClearSlidesCB)
        EVT_MENU(self, self.ID_EXIT, self.ExitCB)


    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Callback stubs for the UI
    #
    def ComboCB(self, event):
        """
        Callback for clicking on combobox for slides
        """
        # Load list of presentation slides from venue to combobox
        self.updateVenueFileList()

        # Skip event to preserve normal behaviour of the combobox 
        event.Skip()

    def PrevSlideCB(self,event):
        """
        Callback for "previous" button
        """
        self.prevCallback()

    def NextSlideCB(self,event):
        """
        Callback for "next" button
        """
        self.nextCallback()

    def GotoSlideNumCB(self,event):
        """
        Callback for "enter" presses in the slide number text field
        """
        if self.masterCheckBox.IsChecked():
            slideNum = int(self.slideNumText.GetValue())
            self.gotoCallback(slideNum)

    def MasterCB(self,event):
        """
        Callback for "master" checkbox
        """
        flag = self.masterCheckBox.IsChecked()
        self.masterCallback(flag)

    def OpenCB(self,event):
        """
        Callback for "enter" presses in the slide URL text field
        """
                
        if self.masterCheckBox.IsChecked():
            # Get slide url from text field
            slidesUrl = self.slidesCombo.GetValue()
           
            # Call the load callback
            try:
                self.loadCallback(slidesUrl)
            except:
                wxCallAfter(self.ShowMessage,"Can not load presentation %s"%slidesUrl, "Notification")

    def SyncCB(self,event):
        """
        Callback for "sync" menu item
        """
        self.syncCallback()

    def LocalUploadCB(self,event):
        """
        Callback for "LocalUpload" menu item
        """
        dlg = wxFileDialog(self, "Choose a file to upload:", style = wxOPEN | wxMULTIPLE)

        if dlg.ShowModal() == wxID_OK:
            files = dlg.GetPaths()
            self.log.debug("SharedPresentation.LocalUploadCB:%s " %str(files))

            # To display an individual error message, upload each file separately. 
            for file in files:
                try:
                    self.localUploadCallback([file])
                except:
                    self.log.exception("Can not upload file %s to data store"%file)
                    wxCallAfter(self.ShowMessage, "Can not upload presentation %s"%file, "Notification")
                    
            self.updateVenueFileList()

    def ClearSlidesCB(self,event):
        """
        Callback for "clear slides" menu item
        """
        self.closeCallback()

    def ExitCB(self,event):
        """
        Callback for "exit" menu item
        """
        self.exitCallback()


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Client methods
    #

    def SetCallbacks(self, loadCallback, 
                           prevCallback, 
                           nextCallback, 
                           gotoCallback,
                           masterCallback,
                           closeCallback,
                           syncCallback,
                           exitCallback,
                           localUploadCallback,
                           queryVenueFilesCallback):
        """
        This method is used to set callbacks for the UI
        """
        self.loadCallback = loadCallback
        self.prevCallback = prevCallback
        self.nextCallback = nextCallback
        self.gotoCallback = gotoCallback
        self.masterCallback = masterCallback
        self.closeCallback = closeCallback
        #self.clearSlidesCallback = closeCallback
        self.syncCallback = syncCallback
        self.exitCallback = exitCallback
        self.localUploadCallback = localUploadCallback
        self.queryVenueFilesCallback = queryVenueFilesCallback

    def SetSlideNum(self, slideNum):
        """
        This method is used to set the slide number
        """
        self.slideNumText.SetValue('%s' % slideNum)

    def SetSlides(self, slides):
        """
        This method is used to set the slide URL
        """
        self.slidesCombo.SetValue(slides)

    def ShowMessage(self, message, title):
        """
        This method is used to display a message dialog to the user.
        """
        MessageDialog(self, message, title, style = wxOK|wxICON_INFORMATION)
  
    def SetMaster(self, flag):
        """
        This method is used to set the "master" checkbox
        """
        self.masterCheckBox.SetValue(flag)

        self.slideNumText.SetEditable(flag)
        self.prevButton.Enable(flag)
        self.nextButton.Enable(flag)
        self.loadButton.Enable(flag)
        self.goButton.Enable(flag)
        self.slidesCombo.Enable(flag)
        # If we're becoming the master, make sure our list of files is current.
        if flag:
            self.updateVenueFileList()

    def updateVenueFileList(self):
        """
        This method is used to update the list of files from the venue.
        """
        old_value = self.slidesCombo.GetValue()
        # Fill slides combo box with venue's files.
        
        try:
            if sys.platform == Platform.WIN:
                filenames = self.queryVenueFilesCallback("*.ppt")
            else:
                filenames = self.queryVenueFilesCallback(["*.ppt", "*.sxi"])
            self.slidesCombo.Clear()
            for file in filenames:
                self.slidesCombo.Append(file)
        except:
            self.log.exception("Exception getting filenames from venue.")
        # Restore value that was unset when we updated the list.
        self.slidesCombo.SetValue(old_value)


class UIController(wxApp):

    def __init__(self,arg, log=None):
        self.log = log
        wxApp.__init__(self,arg)

    def OnInit(self):
        self.frame = SharedPresentationFrame(NULL, -1, "Shared Presentation Controller", log=self.log)
        self.frame.Fit()
        self.frame.Show(true)
        self.SetTopWindow(self.frame)
        return true

    def Start(self):
        """
        Start the UI controller app loop
        """
        self.MainLoop()

    def SetCallbacks(self, loadCallback, 
                           prevCallback, 
                           nextCallback, 
                           gotoCallback,
                           masterCallback,
                           closeCallback,
                           syncCallback,
                           exitCallback,
                           localUploadCallback,
                           queryVenueFilesCallback):
        """
        Pass-through to frame's SetCallbacks method
        """

        self.frame.SetCallbacks(loadCallback, 
                                prevCallback, 
                                nextCallback, 
                                gotoCallback,
                                masterCallback,
                                closeCallback,
                                syncCallback,
                                exitCallback,
                                localUploadCallback,
                                queryVenueFilesCallback)

    def SetMaster(self,flag):
        """
        Pass-through to frame's SetMaster method
        """
        self.frame.SetMaster(flag)

    def SetSlides(self,slidesUrl):
        """
        Pass-through to frame's SetSlides method
        """
        self.frame.SetSlides(slidesUrl)

    def ShowMessage(self, message, title):
        """
        Pass-through to frame's ShowMessage method
        """
        self.frame.ShowMessage(message, title)
      
    def SetSlideNum(self,slideNum):
        """
        Pass-through to frame's SetSlideNum method
        """
        self.frame.SetSlideNum(slideNum)

    

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Shared presentation constants classes
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SharedPresEvent:
    NEXT = "next"
    PREV = "prev"
    MASTER = "master"
    GOTO = "goto"
    LOAD = "load"

    LOCAL_NEXT = "local next"
    LOCAL_PREV = "local prev"
    LOCAL_GOTO = "local goto"
    LOCAL_LOAD = "local load"
    LOCAL_LOAD_VENUE = "local load venue"
    LOCAL_CLOSE = "local close"
    LOCAL_SYNC = "local sync"
    LOCAL_QUIT = "local quit"

class SharedPresKey:
    SLIDEURL = "slideurl"
    SLIDENUM = "slidenum"
    STEPNUM = "stepnum"
    MASTER = "master"


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Shared Presentation class itself
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SharedPresentation:
    """
    The SharedPresentation is an Access Grid 2 Application. It is
    designed as an example that shows how reasonably complex
    applications can be built and shared through the AG2 toolkit.

    The SharedPresentation contains a Presentation Viewer and a
    Presentation Controller. These are designed to be generic so that
    they can be switched out with other implementations as necessary.
    """
    appName = "Shared Presentation"
    appDescription = "A shared presentation is a set of slides that someone presents to share an idea, plan, or activity with a group."
    appMimetype = "application/x-ag-shared-presentation"
    
    def __init__(self, url, venueUrl=None, log=None, appName = 'SharedPresentation', debug = 0):
        """
        This is the contructor for the Shared Presentation.
        """
        # Create shared application client. 
        self.sharedAppClient = SharedAppClient(appName)
        self.log = self.sharedAppClient.InitLogging(debug, log)
        
        # Initialize state in the shared presentation
        self.url = url
        self.venueUrl = venueUrl
        self.eventQueue = Queue.Queue(5)
        self.running = 0
        self.masterId = None
        self.numSteps = 0
        self.slideNum = 1

        # Set up method dictionary for the queue processor to call
        # callbacks based on the event type
        #
        # This is an ugly hack, so we can lookup methods by event type
        self.methodDict = dict()
        self.methodDict[SharedPresEvent.NEXT] = self.Next
        self.methodDict[SharedPresEvent.PREV] = self.Previous
        self.methodDict[SharedPresEvent.GOTO] = self.GoToSlide
        self.methodDict[SharedPresEvent.LOAD] = self.LoadPresentation
        self.methodDict[SharedPresEvent.MASTER] = self.SetMaster

        self.methodDict[SharedPresEvent.LOCAL_NEXT] = self.LocalNext
        self.methodDict[SharedPresEvent.LOCAL_PREV] = self.LocalPrev
        self.methodDict[SharedPresEvent.LOCAL_GOTO] = self.LocalGoto
        self.methodDict[SharedPresEvent.LOCAL_LOAD] = self.LocalLoad
        self.methodDict[SharedPresEvent.LOCAL_LOAD_VENUE] = self.LocalLoadVenue
        self.methodDict[SharedPresEvent.LOCAL_CLOSE] = self.ClosePresentation
        self.methodDict[SharedPresEvent.LOCAL_SYNC] = self.Sync
        self.methodDict[SharedPresEvent.LOCAL_QUIT] = self.Quit

        # Get client profile
        try:
            clientProfileFile = os.path.join(GetUserConfigDir(), "profile")
            clientProfile = ClientProfile(clientProfileFile)
        except:
            self.log.info("Could not load client profile, set clientProfile = None")
            clientProfile = None

        # Connect to shared application service. 
        self.sharedAppClient.Join(self.url, clientProfile)

        # Register callbacks with the Data Channel to handle incoming
        # events.
        self.log.debug("Registering for events.")
        self.sharedAppClient.RegisterEventCallback(SharedPresEvent.NEXT, self.RecvNext)
        self.sharedAppClient.RegisterEventCallback(SharedPresEvent.PREV, self.RecvPrev)
        self.sharedAppClient.RegisterEventCallback(SharedPresEvent.GOTO, self.RecvGoto)
        self.sharedAppClient.RegisterEventCallback(SharedPresEvent.LOAD, self.RecvLoad)
        self.sharedAppClient.RegisterEventCallback(SharedPresEvent.MASTER, self.RecvMaster)

        # Create the controller
        self.log.debug("Creating controller.")
        self.controller = UIController(0, self.log)
        self.controller.SetCallbacks( self.SendLoad,
                                      self.SendPrev,
                                      self.SendNext,
                                      self.SendGoto,
                                      self.SendMaster,
                                      self.ClearSlides,
                                      self.Sync,
                                      self.QuitCB,
                                      self.LocalUpload,
                                      self.QueryVenueFiles )
        

        # Start the queue thread
        Thread(target=self.ProcessEventQueue).start()

        # Start the controller 
        # (this is the main thread, so we'll block here until
        # the controller is closed)
        #self.controller.Start()

    def Start(self):
        self.controller.Start()
        # Put a quit event, so the viewer gets shut down correctly
        self.eventQueue.put([SharedPresEvent.LOCAL_QUIT, None])

        # When the quit event gets processed, the running flag gets cleared
        self.log.debug("Shutting down...")
        import time
        while self.running:
            print ".",
            time.sleep(1)
       
        # Shutdown sharedAppClient
        self.sharedAppClient.Shutdown()
       
    def OpenVenueData(self,venueDataUrl):
        """
        OpenFile opens the specified file in the viewer.
        Since the caller of this method loads the slide set,
        he is implicitly the master.
        """

        # Load the specified file
        self.eventQueue.put([SharedPresEvent.LOCAL_LOAD,venueDataUrl])


    def LoadFromVenue(self):
        """
        LoadFromVenue loads the presentation from the venue and
        moves to the current slide and step
        """
        self.eventQueue.put([SharedPresEvent.LOCAL_LOAD_VENUE,None])


    def ProcessEventQueue(self):
        # The queue processing thread is the only one allowed to access
        # the viewer; that keeps the requirements on the viewer minimal.
        # This method loops, processing events that it gets from the 
        # eventQueue.

        try:
            self.viewer = defaultViewer()
            self.viewer.Start()
        except ViewerSoftwareNotInstalled:
            print "The necessary viewer software is not installed; exiting"
            self.eventQueue.put([SharedPresEvent.LOCAL_QUIT, None])


        # Loop, processing events from the event queue
        self.running = 1
        while self.running:

            # Pull the next event out of the queue
            (event, data) = self.eventQueue.get(1)
            self.log.debug("Got Event: %s %s", event, str(data))

            # Invoke the matching method, passing the data
            try:
                self.methodDict[event](data)
            except:
                self.log.exception("EXCEPTION PROCESSING EVENT")


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Methods registered as callbacks with the UI
    # These methods typically put an event in the event queue.
    #

    def SendNext(self):
        """
        This method handles NEXT button presses in the UI.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendNext called")

        if self.masterId == self.sharedAppClient.GetPublicId():
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_NEXT,None])


    def SendPrev(self):
        """
        This method handles PREV button presses in the UI.
        The event is only sent if the local user is the 'master'
        """
        self.log.debug("Method SendPrev called")

        if self.masterId == self.sharedAppClient.GetPublicId():
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_PREV,None])


    def SendGoto(self, slideNum):
        """
        This method handles GOTO events from the UI.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendGoto called; slidenum=(%d)", slideNum)

        # Check if slideNum is greater than max slide
                
        if not self.viewer or not self.viewer.win:
            self.controller.ShowMessage("No slides are loaded.", "Notification")
            return
        
        lastPage = self.viewer.GetLastSlide()
        if slideNum > lastPage:
            self.controller.ShowMessage("Slide number is incorrect. Last slide is %s"%lastPage, "Notification")
            return

        if slideNum < 1:
            self.controller.ShowMessage("Slide number should be greater than 0.", "Notification")
            return
                   
        if self.masterId == self.sharedAppClient.GetPublicId():
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_GOTO,slideNum])
       
    def SendLoad(self, path):
        """
        This method handles LOAD events from the UI.
        The event is only sent if the local user is the 'master'
        """
        self.log.debug("Method SendLoad called; path=(%s)", path)

        if self.masterId == self.sharedAppClient.GetPublicId():
            # Put the event on the queue
            if path[:5] != "http:":
                try:
                    # Default to loading from venue now.
                    dsc = GetVenueDataStore(self.venueUrl)
                    fileData = dsc.GetFileData(path)
                    path = fileData['uri']
                except:
                    self.log.exception("Unable to get file from venue.")
                    raise "Unable to get file from venue."

            self.eventQueue.put([SharedPresEvent.LOCAL_LOAD,path])

    def SendMaster(self, flag):
        """
        This method handles clicks on the MASTER checkbox
        """
        self.log.debug("Method SendMaster called; flag=(%d)", flag)
        publicId = self.sharedAppClient.GetPublicId()

        if flag:

            # Local user wants to become master
            # Set the master in the venue
            self.sharedAppClient.SetData(SharedPresKey.MASTER, publicId)
            self.sharedAppClient.SetParticipantStatus("master")
            
            # Send event
            self.sharedAppClient.SendEvent(SharedPresEvent.MASTER, (publicId, publicId))
        else:

            # Local user has chosen to stop being master
            if self.masterId == publicId:

                self.log.debug(" Set master to empty")

                # Let's set the master in the venue
                self.sharedAppClient.SetData(SharedPresKey.MASTER, "")
                self.sharedAppClient.SetParticipantStatus("connected")
                
                # Send event
                self.sharedAppClient.SendEvent(SharedPresEvent.MASTER, (publicId, ""))
            else:
                self.log.debug(" User is not master; skipping")


    def ClearSlides(self):
        """
        This method will clear the slides from the venue app object;
        and close the local presentation
        """
        self.log.debug("Method ClearSlides called")

        # Clear the slides url stored in the venue
        self.sharedAppClient.SetData(SharedPresKey.SLIDEURL, "")
        self.sharedAppClient.SetData(SharedPresKey.SLIDENUM, "")
        self.sharedAppClient.SetData(SharedPresKey.STEPNUM, "")

        self.eventQueue.put([SharedPresEvent.LOCAL_CLOSE, None])

    def Sync(self):
        """
        This method will sync the viewer with the state in the app object
        """
        self.log.debug("Method Sync called")

        # Also, update the list of venue ppt files in the dropdown menu.
        # This method does not exist in this class.
        #self.updateVenueFileList()

        self.eventQueue.put([SharedPresEvent.LOCAL_LOAD_VENUE,None])

    def QuitCB(self):
        """
        This method puts a "quit" event in the queue, to get the
        viewer to shutdown
        """
        self.log.debug("Method QuitCB called")
        self.eventQueue.put([SharedPresEvent.LOCAL_QUIT, None])


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Methods registered as callbacks with EventClient
    # These methods typically put an event in the event queue.
    #

    def RecvNext(self, event):
        """
        This callback puts the "next" event from the network on
        the event queue.
        """
        self.log.debug("Method RecvNext called")

        if self.masterId == self.sharedAppClient.GetPublicId():
            self.log.debug("got my own event; skip")
            return

        if self.masterId == event.data[0]:
            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.NEXT, event.data])
            except Queue.Full:
                self.log.debug("Dropping event, event Queue full!")

    def RecvPrev(self, event):
        """
        This callback puts the "previous" event from the network on
        the event queue.
        """
        self.log.debug("Method RecvPrev called")

        if self.masterId == self.sharedAppClient.GetPublicId():
            self.log.debug( "got my own event; skip")
            return

        if self.masterId == event.data[0]:
            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.PREV, event.data])
            except Full:
                self.log.debug("Dropping event, event Queue full!")
        
    def RecvGoto(self, event):
        """
        This callback puts the "goto" event from the network on
        the event queue.
        """
        self.log.debug("Method RecvGoto called")

        if self.masterId == self.sharedAppClient.GetPublicId():
            self.log.debug( "got my own event; skip")
            return

        if self.masterId == event.data[0]:
            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.GOTO, event.data[1]])
            except Full:
                self.log.debug("Dropping event, event Queue full!")
        
    def RecvLoad(self, event):
        """
        This callback puts the "load" presentation event from
        the network on the event queue.
        """
        self.log.debug("Method RecvLoad called")
      
        if self.masterId == self.sharedAppClient.GetPublicId():
            self.log.debug( "got my own event; skip")
            return

        if self.masterId == event.data[0]:
            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.LOAD, event.data])
            except Full:
                self.log.debug("Dropping event, event Queue full!")

            
    def RecvMaster(self, event):
        """
        This callback puts a "master" event from the network
        on the event queue
        """
        self.log.debug("Method RecvMaster called")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put([SharedPresEvent.MASTER, event.data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")

    

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Methods called by the queue processor for incoming events.
    # These methods can communicate with the viewer, since they
    # are called by the queue processing thread, in which the
    # viewer was created.
    #   

    def Next(self, data=None):
        """
        This is the _real_ next slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method Next called")

        # Call the viewers Next method
        if self.viewer != None:
            self.viewer.Next()
        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded")
        
    def Previous(self, data=None):
        """
        This is the _real_ previous slide method that tells the viewer to move
        to the previous slide.
        """
        self.log.debug("Method Previous called")

        # Call the viewers Previous method
        if self.viewer != None:
            self.viewer.Previous()
        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded!")

    def GoToSlide(self, slideNum):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the specified slide.
        """
        self.log.debug("Method GoToSlide called; slidenum=(%d)", slideNum)

        # Call the viewers GotoSlide method
        if self.viewer != None:
            self.viewer.GoToSlide(slideNum)
        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded!")

        wxCallAfter(self.controller.SetSlideNum, slideNum)
                   
    def LoadPresentation(self, data):
        """
        This is the _real_ load presentation method that tells the viewer
        to load the specified presentation.
        """
        self.log.debug("Method LoadPresentation called; url=(%s)", data[1])

        slidesUrl = data[1]
        # If the slides URL begins with https, retrieve the slides
        # from the venue data store
       
        if slidesUrl.startswith("https"):
            tmpFile = os.path.join(Platform.GetTempDir(), "presentation.ppt")
            # Make sure filename is not currently open
            if tmpFile == self.viewer.openFile:
                tmpFile = os.path.join(Platform.GetTempDir(), "presentation2.ppt")
           
            try:
                DataStore.GSIHTTPDownloadFile(slidesUrl, tmpFile, None, None )
                self.viewer.LoadPresentation(tmpFile)
            except:
                self.log.exception("Can not load presentation %s"%slidesUrl)
                wxCallAfter(self.controller.ShowMessage,
                            "Can not load presentation %s." %slidesUrl, "Notification")
               
        else:
            try:
                self.viewer.LoadPresentation(slidesUrl)
            except:
                self.log.exception("Can not load presentation %s" %slidesUrl)
                wxCallAfter(self.controller.ShowMessage,
                            "Can not load presentation %s." %slidesUrl, "Notification")
              
        if slidesUrl[:6] == "https:":
            # Remove datastore prefix on local url in UI since master checks
            #  if file is in venue and sends full datastore url if it is.
            short_filename = self.stripDatastorePrefix(slidesUrl)
            wxCallAfter(self.controller.SetSlides, short_filename)
            #self.controller.SetSlides(slidesUrl)
        else:
            wxCallAfter(self.controller.SetSlides, slidesUrl)
            
        wxCallAfter(self.controller.SetSlideNum, 1)
        self.slideNum = 1
        self.stepNum = 0
        
    def stripDatastorePrefix(self, url):
        vproxy = Client.Handle(venueURL).GetProxy()
        ds = vproxy.GetDataStoreInformation()
        ds_prefix = str(ds[0])
        url_beginning = url[:len(ds_prefix)]
        # If it starts with the prefix ds[1], return just the ending.
        if ds_prefix == url_beginning and ds_prefix[:6] == "https:":
            # Get url without datastore ds_prefix, +1 is for extra "/" 
            short_url = url[len(ds_prefix)+1:]
            #print "url stripped to:", short_url
            return short_url
        else:
            # Does not start with datastore prefix, leave it alone.
            return url

    def SetMaster(self, data):
        """
        This method sets the master of the presentation.
        """
        self.log.debug("Method SetMaster called")

        # If I was master, change status in application service.
        if self.masterId == self.sharedAppClient.GetPublicId():
            self.sharedAppClient.SetParticipantStatus("connected")

        # Store the master's public id locally
        self.masterId = data[1]

        # Update the controller accordingly
        if self.masterId == self.sharedAppClient.GetPublicId():
            wxCallAfter(self.controller.SetMaster, true)
        else:
            wxCallAfter(self.controller.SetMaster, false)

    def ClosePresentation(self,data=None):
        """
        This method closes the presentation in the viewer
        """

        self.log.debug("Method ClosePresentation called")
        try:
            self.viewer.EndShow()
        except:
            self.log.exception("Can not end show, ignore")
        
    def Quit(self, data=None):
        """
        This is the _real_ Quit method that tells the viewer to quit
        """
        self.log.debug("Method Quit called")
        
        # Stop the viewer
        try:
            self.viewer.Stop()
        except:
            self.log.exception("Exception stopping show")

        # Close the viewer
        try:
            self.viewer.Quit()
        except:
            self.log.exception("Exception quitting viewer")

        # Get rid of the controller
        self.controller = None

        # Turn off the main loop
        self.running = 0


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Methods called by the queue processor for local events.
    # These methods can communicate with the viewer, since they
    # are called by the queue processing thread, in which the
    # viewer was created.
    # 

    def LocalNext(self, data):
        """
        This is the _real_ next slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalNext called")

        if self.viewer != None and self.viewer.win != None:
            # Careful not to slip off the end of the presentation, cause that mean an exception
            if self.slideNum == self.viewer.GetLastSlide() and self.stepNum >= self.viewer.GetStepNum()-1:
                wxCallAfter(self.controller.ShowMessage,
                            "This is the last slide. You can not go to next.", "Notification")
                return

            if self.slideNum <= self.viewer.GetLastSlide():
                
                # Call the viewers Next method
                self.viewer.Next()

                # Get the slide number from the viewer
                slideNum = self.viewer.GetSlideNum()
                if slideNum != self.slideNum:

                    # Set the slide number in the controller
                    wxCallAfter(self.controller.SetSlideNum, slideNum)

                    # Store the slide number in the app object
                    self.sharedAppClient.SetData(SharedPresKey.SLIDENUM, slideNum)
                    self.slideNum = slideNum
                    self.stepNum = 0
                else:
                    # The presentation advanced, but the slide number didn't change,
                    # so it musta been an on-slide transition or some such
                    self.stepNum += 1

                # Store the step number in the app object
                self.sharedAppClient.SetData(SharedPresKey.STEPNUM, self.stepNum)

                # Send the next event to other app users
                publicId = self.sharedAppClient.GetPublicId()
                self.sharedAppClient.SendEvent(SharedPresEvent.NEXT,(publicId, None))
        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded!")
        
    def LocalPrev(self, data):
        """
        This is the _real_ previous slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalPrev called")
       
        if self.viewer != None and self.viewer.win != None:
            if self.slideNum < 2:
                wxCallAfter(self.controller.ShowMessage,
                            "This is the first slide. You can not go to previous.", "Notification")
                
            if self.slideNum > 0:

                # Call the viewers Previous method
                self.viewer.Previous()
                                    
                # Get the slide number from the viewer
                slideNum = self.viewer.GetSlideNum()
                if slideNum != self.slideNum:
                    # Set the slide number in the controller
                    wxCallAfter(self.controller.SetSlideNum, slideNum)

                    self.slideNum = slideNum
                    self.stepNum = self.viewer.GetStepNum() - 1

                    # Store the slide number in the app object
                    self.sharedAppClient.SetData(SharedPresKey.SLIDENUM, slideNum)

                else:
                    # The presentation retreated, but the slide number didn't change,
                    # so it musta been an on-slide transition or some such
                    if self.stepNum > 0: 
                        self.stepNum -= 1

                # Store the step number in the app object
                self.sharedAppClient.SetData(SharedPresKey.STEPNUM, self.stepNum)

                # We send the event, which is wrapped in an Event instance
                publicId = self.sharedAppClient.GetPublicId()
                self.sharedAppClient.SendEvent(SharedPresEvent.PREV, (publicId, None))

                self.log.debug("slide %d step %d", self.slideNum, self.stepNum)

        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded!")

        
    def LocalGoto(self, slideNum):
        """
        This is the _real_ goto slide method that tells the viewer to goto
        the specified slide.
        """
        self.log.debug("Method LocalGoto called; slidenum=(%d)", slideNum)
        # Call the viewers GotoSlide method
        if self.viewer != None and self.viewer.win != None:
            if slideNum > 0 and slideNum <= self.viewer.GetLastSlide():
                self.viewer.GoToSlide(slideNum)
                self.sharedAppClient.SetData(SharedPresKey.SLIDENUM, slideNum)
                self.slideNum = slideNum
                self.stepNum = 0
                self.sharedAppClient.SetData(SharedPresKey.STEPNUM, self.stepNum)

                # Send event
                publicId = self.sharedAppClient.GetPublicId()
                self.sharedAppClient.SendEvent(SharedPresEvent.GOTO, (publicId, self.slideNum))
                
        else:
            wxCallAfter(self.controller.ShowMessage, "No slides are loaded.", "Notification")
            self.log.debug("No presentation loaded!")

        wxCallAfter(self.controller.SetSlideNum, slideNum)

    def LocalLoad(self, slidesUrl):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalLoad called; slidesUrl=(%s)", slidesUrl)

        # If the slides URL begins with https, retrieve the slides
        # from the venue data store
        if slidesUrl.startswith("https"):
            tmpFile = os.path.join(Platform.GetTempDir(), "presentation.ppt")
            # If current filename is in use, use slightly different name.
            if tmpFile == self.viewer.openFile:
                tmpFile = os.path.join(Platform.GetTempDir(), "presentation2.ppt")
           
            try:
                DataStore.GSIHTTPDownloadFile(slidesUrl, tmpFile, None, None )
                self.viewer.LoadPresentation(tmpFile)
            except:
                self.log.exception("#Can not load presentation %s"%slidesUrl)
                wxCallAfter(self.controller.ShowMessage,
                            "Can not load presentation %s." %slidesUrl,
                            "Notification")
               
            # Remove datastore prefix on local url in UI since master checks
            #  if file is in venue and sends full datastore url if it is.
            short_url = self.stripDatastorePrefix(slidesUrl)
            wxCallAfter(self.controller.SetSlides, short_url)
            #self.controller.SetSlides(slidesUrl)
        else:
            try:
                self.viewer.LoadPresentation(slidesUrl)
            except:
                self.log.exception("Can not load presentation %s"%slidesUrl)
                wxCallAfter(self.controller.ShowMessage,
                            "Can not load presentation %s." %slidesUrl,
                            "Notification")
               
                
            wxCallAfter(self.controller.SetSlides, slidesUrl)
                      
        self.slideNum = 1
        self.stepNum = 0
        wxCallAfter(self.controller.SetSlideNum, self.slideNum)

        self.sharedAppClient.SetData(SharedPresKey.SLIDEURL, slidesUrl)
        self.sharedAppClient.SetData(SharedPresKey.SLIDENUM, self.slideNum)
        self.sharedAppClient.SetData(SharedPresKey.STEPNUM, self.stepNum)
        
        # Send event
        publicId = self.sharedAppClient.GetPublicId()
        self.sharedAppClient.SendEvent(SharedPresEvent.LOAD,(publicId, slidesUrl))
                                    
        self.SendMaster(true)


    def LocalLoadVenue(self, data=None):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalLoadVenue called")

        # Retrieve the current presentation
        self.presentation = self.sharedAppClient.GetData(SharedPresKey.SLIDEURL)
        errorFlag = false
        # Check i presentation still exists.

        # Set the slide URL in the UI
        if len(self.presentation) != 0:
            self.log.debug("Got presentation: %s", self.presentation)
            if self.presentation[:6] == "https:":
                # Remove datastore prefix on local url in UI since master checks
                #  if file is in venue and sends full datastore url if it is.
                short_presentation = self.stripDatastorePrefix(self.presentation)
                wxCallAfter( self.controller.SetSlides, short_presentation)
                #self.controller.SetSlides(self.presentation)
            else:
                wxCallAfter( self.controller.SetSlides, self.presentation)
                                
            # Retrieve the current slide
            self.slideNum = self.sharedAppClient.GetData(SharedPresKey.SLIDENUM)
            # If it's a string, convert it to an integer
            if type(self.slideNum) == type(""):
                if len(self.slideNum) < 1:
                    self.slideNum = 1
                else:
                    self.slideNum = int(self.slideNum)

            # Retrieve the current step number
            self.stepNum = self.sharedAppClient.GetData(SharedPresKey.STEPNUM)
            # If it's a string, convert it to an integer
            if type(self.stepNum) == type(""):
                if len(self.stepNum) < 1:
                    self.stepNum = 0
                else:
                    self.stepNum = int(self.stepNum)

            # Retrieve the master
            self.masterId = self.sharedAppClient.GetData(SharedPresKey.MASTER)

            # If the slides URL begins with https, retrieve the slides
            # from the venue data store
            if self.presentation.startswith("https"):
                tmpFile = os.path.join(Platform.GetTempDir(), "presentation.ppt")
                # If tmpFile name is in use, use a different name.
                if tmpFile == self.viewer.openFile:
                    tmpFile = os.path.join(Platform.GetTempDir(), "presentation2.ppt")
                try:
                    DataStore.GSIHTTPDownloadFile(self.presentation, tmpFile, None, None )
                    self.viewer.LoadPresentation(tmpFile)
                except:
                    errorFlag = 1
                    self.log.exception("Can not load file %s 5"%self.presentation)
                                                       
            else:
                try:
                    self.viewer.LoadPresentation(self.presentation)
                except:
                    errorFlag = 1
                    self.log.exception("Can not load file %s 6"%self.presentation)

            if not errorFlag:       
                # Go to the current slide
                self.GoToSlide(self.slideNum)

                # Go to the current step
                for i in range(self.stepNum):
                    self.Next()

            else:
                wxCallAfter(self.controller.ShowMessage,
                            "Can not load presentation %s." %self.presentation, "Notification")
                self.slideNum = ''
                
        # Set the slide number in the UI
        if self.slideNum == '':
            self.slideNum = 1
        else:
            self.log.debug("Got slide num: %d", self.slideNum)
            wxCallAfter(self.controller.SetSlideNum, '%s' % self.slideNum)

        # Set the master in the UI
        wxCallAfter(self.controller.SetMaster, false)

    def LocalUpload(self, filenames):
        dsc = GetVenueDataStore(self.venueUrl)
        for filename in filenames:
            dsc.Upload(filename)
            
    def QueryVenueFiles(self, file_query="*"):
        dsc = GetVenueDataStore(self.venueUrl)
        if type(file_query) == type(""):
            filenames = dsc.QueryMatchingFiles(file_query)
        elif type(file_query) == type([]):
            filenames = dsc.QueryMatchingFilesMultiple(file_query)
        else:
            raise "InvalidQueryType"
        return filenames



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# Utility functions
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#
# This gets logging started given the log name passed in
# For more information about the logging module, check out:
# http://www.red-dove.com/python_logging.html
#

def Usage():
    """
    Standard usage information for users.
    """
    print "%s:" % sys.argv[0]
    print "    -a|--applicationURL : <url to application in venue>"
    print "    -d|--data : <url to data in venue>"
    print "    -h|--help : print usage"
    print "    -i|--information : <print information about this application>"
    print "    -l|--logging : <log name: defaults to SharedPresentation>"
    print "    --debug : print debugging output"



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# MAIN block
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    # Initialization of variables
    venueURL = None
    appURL = None
    venueDataUrl = None
    logName = "SharedPresentation"
    debug = 0

    # Here we parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:v:a:l:ih",
                                   ["venueURL=", "applicationURL=",
                                    "information=", "logging=", 
                                    "data=", "debug", "help"])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-v", "--venueURL"):
            venueURL = a
        elif o in ("-a", "--applicationURL"):
            appURL = a
        elif o in ("-l", "--logging"):
            logName = a
        elif o in ("-i", "--information"):
            print "App Name: %s" % SharedPresentation.appName
            print "App Description: %s" % SharedPresentation.appDescription
            print "App Mimetype: %s" % SharedPresentation.appMimetype
            sys.exit(0)
        elif o in ("-d", "--data"):
            venueDataUrl = a
        elif o in ("--debug",):
            debug = 1
        elif o in ("-h", "--help"):
            Usage()
            sys.exit(0)
    
    # If we're not passed some url that we can use, bail showing usage
    if appURL == None and venueURL == None:
        Usage()
        sys.exit(0)

    # If we got a venueURL and not an applicationURL
    # This is only in the example code. When Applications are integrated
    # with the Venue Client, the application will only be started with
    # some applicatoin URL (it will never know about the Venue URL)
    if appURL == None and venueURL != None:
        venueProxy = Client.Handle(venueURL).get_proxy()
        appURL = venueProxy.CreateApplication(SharedPresentation.appName,
                                              SharedPresentation.appDescription,
                                              SharedPresentation.appMimetype)
        log.debug("Application URL: %s", appURL)

   
    # This is all that really matters!
    presentation = SharedPresentation(appURL, venueURL, logName, "SharedPresentation", debug)

    if venueDataUrl:
        presentation.OpenVenueData(venueDataUrl)
    else:
        presentation.LoadFromVenue()

    presentation.Start()

    # This is needed because COM shutdown isn't clean yet.
    # This should be something like:
    #sys.exit(0)
    os._exit(0)

    # Stress Test
    #import threading
    #import time

    #s = SharedAppClient("test")
    #s.Join(appURL)
    #publicId = s.GetPublicId()

    #def SendEvents():
    #    time.sleep(10)
    #    s.SendEvent(SharedPresEvent.MASTER, (publicId, publicId))
    #    print 'send next event'
    #    s.SendEvent(SharedPresEvent.NEXT,(publicId, None))
    #    s.SendEvent(SharedPresEvent.NEXT,(publicId, None))
    #    s.SendEvent(SharedPresEvent.PREV,(publicId, None))
    #    s.SendEvent(SharedPresEvent.PREV,(publicId, None))
        
    #thread = threading.Thread(target = SendEvents)
    #thread.start()
    
    #presentation.Start()
    #os._exit(0)

