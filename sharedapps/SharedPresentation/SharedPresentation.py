#-----------------------------------------------------------------------------
# Name:        SharedPresentation.py
# Purpose:     This is the Shared Presentation Software. 
#
# Author:      Ivan R. Judson, Tom Uram
#
# Created:     2002/12/12
# RCS-ID:      $Id: SharedPresentation.py,v 1.4 2003-08-20 19:54:20 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
# Normal import stuff
import os
import sys
import getopt
import logging
from threading import Thread
import Queue

from wxPython.wx import *

# Win 32 COM interfaces that we use
try:
    import win32com
    import win32com.client
except:
    print "No Windows COM support!"
    sys.exit(1)

# Imports we need from the Access Grid Module
from AccessGrid.hosting.pyGlobus import Client
from AccessGrid.EventClient import EventClient
from AccessGrid.Events import ConnectEvent, Event
from AccessGrid import Platform
from AccessGrid import DataStore




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
        self.presentation.Close()

        # Exit the powerpoint application, but only if 
        # it was opened by the viewer
        if not self.pptAlreadyOpen:
            self.ppt.Quit()
        
    def LoadPresentation(self, file):
        """
        This method opens a file and starts the viewing of it.
        """

        # Close existing presentation
        if self.presentation:
            self.presentation.Close()

        # Open a new presentation and keep a reference to it in self.presentation
        self.presentation = self.ppt.Presentations.Open(file)
        self.lastSlide = self.presentation.Slides.Count

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
        self.win.View.Exit()

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



# Depending on the platform decide which viewer to use
if sys.platform == Platform.WIN:
    # If we're on Windows we try to use the python/COM interface to PowerPoint
    defaultViewer = PowerPointViewer
else:
    # On Linux the best choice is probably Open/Star Office
    defaultViewer = None



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# GUI code
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class SharedPresentationFrame(wxFrame):

    ID_SYNC = wxNewId()
    ID_CLEAR = wxNewId()
    ID_EXIT = wxNewId()

    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, wxSize(450, 300))


        # Initialize callbacks
        noOp = lambda x=0:0
        self.loadCallback = noOp
        self.clearSlidesCallback = noOp
        self.prevCallback = noOp
        self.nextCallback = noOp
        self.gotoCallback = noOp
        self.masterCallback = noOp
        self.closeCallback = noOp
        self.syncCallback = noOp
        self.exitCallback = noOp

        #
        # Create UI controls
        #
        
        # - Create menu bar
        menubar = wxMenuBar()
        fileMenu = wxMenu()
        fileMenu.Append(self.ID_SYNC,"&Sync", "Sync to app state")
        fileMenu.Append(self.ID_CLEAR,"&Clear slides", "Clear the slides from venue")
        fileMenu.AppendSeparator()
        fileMenu.Append(self.ID_EXIT,"&Exit", "Exit")
     	menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        # - Create main sizer
        sizer = wxBoxSizer(wxVERTICAL)
        self.SetSizer(sizer)

        # - Create checkbox for master
        self.masterCheckBox = wxCheckBox(self,-1,"Take control as presentation master")
        sizer.Add( self.masterCheckBox, 0, wxEXPAND)

        # - Create sizer for remaining ctrls
        staticBoxSizer = wxStaticBoxSizer(wxStaticBox(self, -1, ""), wxVERTICAL)
        gridSizer = wxFlexGridSizer(3, 2, 5, 5)
        gridSizer.AddGrowableCol(1)
        staticBoxSizer.Add(gridSizer, 1, wxEXPAND)
        sizer.Add(staticBoxSizer, 1, wxEXPAND)

        # - Create textctrl for slide url
        staticText = wxStaticText(self, -1, "Slides")
        self.slidesText = wxTextCtrl(self,-1)
        gridSizer.Add( staticText, 0, wxALIGN_LEFT)
        gridSizer.Add( self.slidesText, 1, wxEXPAND)

        # - Create textctrl for slide num
        staticText = wxStaticText(self, -1, "Slide number")
        self.slideNumText = wxTextCtrl(self,-1)
        gridSizer.Add( staticText, wxALIGN_LEFT)
        gridSizer.Add( self.slideNumText )

        # - Create buttons for control 
        rowSizer = wxBoxSizer(wxHORIZONTAL)
        self.prevButton = wxButton(self,-1,"<Prev")
        self.nextButton = wxButton(self,-1,"Next>")
        rowSizer.Add( self.prevButton )
        rowSizer.Add( self.nextButton )
        gridSizer.Add( wxStaticText(self,-1,"") )
        gridSizer.Add( rowSizer, 0, wxALIGN_RIGHT )
        
        # Set up event callbacks
        EVT_TEXT_ENTER(self, self.slidesText.GetId(), self.OpenCB)
        EVT_CHECKBOX(self, self.masterCheckBox.GetId(), self.MasterCB)
        EVT_BUTTON(self, self.prevButton.GetId(), self.PrevSlideCB)
        EVT_TEXT_ENTER(self, self.slideNumText.GetId(), self.GotoSlideNumCB)
        EVT_BUTTON(self, self.nextButton.GetId(), self.NextSlideCB)

        EVT_MENU(self, self.ID_SYNC, self.SyncCB)
        EVT_MENU(self, self.ID_CLEAR, self.ClearSlidesCB)
        EVT_MENU(self, self.ID_EXIT, self.ExitCB)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Callback stubs for the UI
    #

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
            slidesUrl = self.slidesText.GetValue()

            # Call the load callback
            self.loadCallback(slidesUrl)

    def SyncCB(self,event):
        """
        Callback for "sync" menu item
        """
        self.syncCallback()

    def ClearSlidesCB(self,event):
        """
        Callback for "clear slides" menu item
        """
        self.clearSlidesCallback()

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
                           exitCallback):
        """
        This method is used to set callbacks for the UI
        """
        
        self.loadCallback = loadCallback
        self.prevCallback = prevCallback
        self.nextCallback = nextCallback
        self.gotoCallback = gotoCallback
        self.masterCallback = masterCallback
        self.closeCallback = closeCallback
        self.syncCallback = syncCallback
        self.exitCallback = exitCallback

    def SetSlideNum(self, slideNum):
        """
        This method is used to set the slide number
        """
        self.slideNumText.SetValue('%s' % slideNum)

    def SetSlides(self, slides):
        """
        This method is used to set the slide URL
        """
        self.slidesText.SetValue(slides)

    def SetMaster(self, flag):
        """
        This method is used to set the "master" checkbox
        """
        self.masterCheckBox.SetValue(flag)

        self.slidesText.SetEditable(flag)
        self.slideNumText.SetEditable(flag)
        self.prevButton.Enable(flag)
        self.nextButton.Enable(flag)


class UIController(wxApp):

    def __init__(self,arg):
        wxApp.__init__(self,arg)

    def OnInit(self):
        self.frame = SharedPresentationFrame(NULL, -1, "Shared Presentation controller")
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
                           exitCallback):
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
                                exitCallback)

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
    
    def __init__(self, url, log=None):
        """
        This is the contructor for the Shared Presentation.
        """
        # Initialize state in the shared presentation
        self.url = url
        self.eventQueue = Queue.Queue(5)
        self.log = log
        self.running = 0
        self.masterId = None
        self.numSteps = 0

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

        # Get a handle to the application object in the venue
        self.log.debug("Getting application proxy (%s).", url)
        self.appProxy = Client.Handle(self.url).GetProxy()

        # Join the application object, get a private ID in response
        self.log.debug("Joining application.")
        (self.publicId, self.privateId) = self.appProxy.Join()

        # Get the information about our Data Channel
        self.log.debug("Retrieving data channel information.")
        (self.channelId, esl) = self.appProxy.GetDataChannel(self.privateId)

        # Connect to the Data Channel, using the EventClient class
        # The EventClient class is a general Event Channel Client, but since
        # we use the Event Channel for a Data Channel we can use the
        # Event Client Class as a Data Client. For more information on the
        # Event Channel look in AccessGrid\EventService.py
        # and AccessGrid\EventClient.py
        self.log.debug("Connecting to data channel.")
        self.eventClient = EventClient(self.privateId, esl, self.channelId)
        self.eventClient.start()
        self.eventClient.Send(ConnectEvent(self.channelId, self.privateId))

        # Register callbacks with the Data Channel to handle incoming
        # events.
        self.log.debug("Registering for events.")
        self.eventClient.RegisterCallback(SharedPresEvent.NEXT, self.RecvNext)
        self.eventClient.RegisterCallback(SharedPresEvent.PREV, self.RecvPrev)
        self.eventClient.RegisterCallback(SharedPresEvent.GOTO, self.RecvGoto)
        self.eventClient.RegisterCallback(SharedPresEvent.LOAD, self.RecvLoad)
        self.eventClient.RegisterCallback(SharedPresEvent.MASTER, self.RecvMaster)

        # Create the controller
        self.log.debug("Creating controller.")
        self.controller = UIController(0)
        self.controller.SetCallbacks( self.SendLoad,
                                      self.SendPrev,
                                      self.SendNext,
                                      self.SendGoto,
                                      self.SendMaster,
                                      self.ClearSlides,
                                      self.Sync,
                                      self.QuitCB )
        

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

        import pythoncom
        pythoncom.CoInitialize()

        self.viewer = defaultViewer()
        self.viewer.Start()

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

        if self.masterId == self.publicId:
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_NEXT,None])


    def SendPrev(self):
        """
        This method handles PREV button presses in the UI.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendPrev called")

        if self.masterId == self.publicId:
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_PREV,None])


    def SendGoto(self, slideNum):
        """
        This method handles GOTO events from the UI.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendGoto called; slidenum=(%d)", slideNum)

        if self.masterId == self.publicId:
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_GOTO,slideNum])

    def SendLoad(self, path):
        """
        This method handles LOAD events from the UI.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendLoad called; path=(%s)", path)

        if self.masterId == self.publicId:
            # Put the event on the queue
            self.eventQueue.put([SharedPresEvent.LOCAL_LOAD,path])

    def SendMaster(self, flag):
        """
        This method handles clicks on the MASTER checkbox
        """
        self.log.debug("Method SendMaster called; flag=(%d)", flag)

        if flag:

            # Local user wants to become master
            # Set the master in the venue
            self.appProxy.SetData(self.privateId, SharedPresKey.MASTER, self.publicId)
            
            # We send the event, which is wrapped in an Event instance
            self.eventClient.Send(Event(SharedPresEvent.MASTER, self.channelId,
                                        (self.publicId, self.publicId)
                                            ))
        else:

            # Local user has chosen to stop being master
            if self.masterId == self.publicId:

                self.log.debug(" Set master to empty")

                # Let's set the master in the venue
                self.appProxy.SetData(self.privateId, SharedPresKey.MASTER, "")
                
                # We send the event, which is wrapped in an Event instance
                self.eventClient.Send(Event(SharedPresEvent.MASTER, self.channelId,
                                            (self.publicId, "")))
            else:
                self.log.debug(" User is not master; skipping")


    def ClearSlides(self):
        """
        This method will clear the slides from the venue app object;
        and close the local presentation
        """
        self.log.debug("Method ClearSlides called")

        # Clear the slides url stored in the venue
        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDEURL, "")
        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, "")
        self.appProxy.SetData(self.privateId, SharedPresKey.STEPNUM, "")
        self.eventQueue.put([SharedPresEvent.LOCAL_CLOSE, None])

    def Sync(self):
        """
        This method will sync the viewer with the state in the app object
        """
        self.log.debug("Method Sync called")

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

        if self.masterId == self.publicId:
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

        if self.masterId == self.publicId:
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

        if self.masterId == self.publicId:
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

        if self.masterId == self.publicId:
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
            self.log.debug("No presentation loaded!")
        
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
            self.log.debug("No presentation loaded!")

        self.controller.SetSlideNum(slideNum)
                   
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
            tmpFile = "tmp"
            DataStore.GSIHTTPDownloadFile(slidesUrl, tmpFile, None, None )
            self.viewer.LoadPresentation(tmpFile)
        else:
            self.viewer.LoadPresentation(slidesUrl)

        self.controller.SetSlides(slidesUrl)
        self.controller.SetSlideNum(1)
        self.slideNum = 1
        self.stepNum = 0

    def SetMaster(self, data):
        """
        This method sets the master of the presentation.
        """
        self.log.debug("Method SetMaster called")

        # Store the master's public id locally
        self.masterId = data[1]

        # Update the controller accordingly
        if self.masterId == self.publicId:
            self.controller.SetMaster(true)
        else:
            self.controller.SetMaster(false)

    def ClosePresentation(self,data=None):
        """
        This method closes the presentation in the viewer
        """
        self.log.debug("Method ClosePresentation called")

        self.viewer.EndShow()

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

        if self.viewer != None:

            # Careful not to slip off the end of the presentation, cause that mean an exception
            if self.slideNum == self.viewer.GetLastSlide() and self.stepNum >= self.viewer.win.View.Slide.PrintSteps-1:
                return

            if self.slideNum <= self.viewer.GetLastSlide():
                
                # Call the viewers Next method
                self.viewer.Next()

                # Get the slide number from the viewer
                slideNum = self.viewer.GetSlideNum()
                if slideNum != self.slideNum:

                    # Set the slide number in the controller
                    self.controller.SetSlideNum(slideNum)

                    # Store the slide number in the app object
                    self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, slideNum)
                    self.slideNum = slideNum
                    self.stepNum = 0
                else:
                    # The presentation advanced, but the slide number didn't change,
                    # so it musta been an on-slide transition or some such
                    self.stepNum += 1

                # Store the step number in the app object
                self.appProxy.SetData(self.privateId, SharedPresKey.STEPNUM, self.stepNum)

                # Send the next event to other app users
                self.eventClient.Send(Event(SharedPresEvent.NEXT, self.channelId,
                                            (self.publicId, None)))
        else:
            self.log.debug("No presentation loaded!")
        
    def LocalPrev(self, data):
        """
        This is the _real_ previous slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalPrev called")

        if self.viewer != None:
            if self.slideNum > 0:

                # Call the viewers Previous method
                self.viewer.Previous()

                # Get the slide number from the viewer
                slideNum = self.viewer.GetSlideNum()
                if slideNum != self.slideNum:
                    # Set the slide number in the controller
                    self.controller.SetSlideNum(slideNum)

                    self.slideNum = slideNum
                    self.stepNum = self.viewer.win.View.Slide.PrintSteps - 1

                    # Store the slide number in the app object
                    self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, slideNum)

                else:
                    # The presentation retreated, but the slide number didn't change,
                    # so it musta been an on-slide transition or some such
                    if self.stepNum > 0: 
                        self.stepNum -= 1

                # Store the step number in the app object
                self.appProxy.SetData(self.privateId, SharedPresKey.STEPNUM, self.stepNum)

                # We send the event, which is wrapped in an Event instance
                self.eventClient.Send(Event(SharedPresEvent.PREV, self.channelId,
                                            (self.publicId, None)))

                self.log.debug("slide %d step %d", self.slideNum, self.stepNum)

        else:
            self.log.debug("No presentation loaded!")

        
    def LocalGoto(self, slideNum):
        """
        This is the _real_ goto slide method that tells the viewer to goto
        the specified slide.
        """
        self.log.debug("Method LocalGoto called; slidenum=(%d)", slideNum)

        # Call the viewers GotoSlide method
        if self.viewer != None:
            if slideNum > 0 and slideNum <= self.viewer.GetLastSlide():
                self.viewer.GoToSlide(slideNum)
                self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, slideNum)
                self.slideNum = slideNum
                self.stepNum = 0
                self.appProxy.SetData(self.privateId, SharedPresKey.STEPNUM, self.stepNum)

                # We send the event, which is wrapped in an Event instance
                self.eventClient.Send(Event(SharedPresEvent.GOTO, self.channelId,
                                            (self.publicId, self.slideNum)
                                            ))


        else:
            self.log.debug("No presentation loaded!")

        self.controller.SetSlideNum(slideNum)

    def LocalLoad(self, slidesUrl):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalLoad called; slidesUrl=(%s)", slidesUrl)

        # If the slides URL begins with https, retrieve the slides
        # from the venue data store
        if slidesUrl.startswith("https"):
            tmpFile = Platform.GetTempDir() + "presentation.ppt"
            DataStore.GSIHTTPDownloadFile(slidesUrl, tmpFile, None, None )
            self.viewer.LoadPresentation(tmpFile)
        else:
            self.viewer.LoadPresentation(slidesUrl)

        self.slideNum = 1
        self.stepNum = 0
        self.controller.SetSlides(slidesUrl)
        self.controller.SetSlideNum(self.slideNum)

        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDEURL, slidesUrl)
        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, self.slideNum)
        self.appProxy.SetData(self.privateId, SharedPresKey.STEPNUM, self.stepNum)
        
        # We send the event, which is wrapped in an Event instance
        self.eventClient.Send(Event(SharedPresEvent.LOAD, self.channelId,
                                    (self.publicId, slidesUrl)
                                    ))

        self.SendMaster(true)


    def LocalLoadVenue(self, data=None):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method LocalLoadVenue called")

        # Retrieve the current presentation
        self.presentation = self.appProxy.GetData(self.privateId,
                                                  SharedPresKey.SLIDEURL)

        # Set the slide URL in the UI
        if len(self.presentation) != 0:
            self.log.debug("Got presentation: %s", self.presentation)
            self.controller.SetSlides(self.presentation)

        # Retrieve the current slide
        self.slideNum = self.appProxy.GetData(self.privateId,
                                                  SharedPresKey.SLIDENUM)

        # Retrieve the current step number
        self.stepNum = self.appProxy.GetData(self.privateId,
                                             SharedPresKey.STEPNUM)

        # Retrieve the master
        self.masterId = self.appProxy.GetData(self.privateId,
                                             SharedPresKey.MASTER)

        # If the slides URL begins with https, retrieve the slides
        # from the venue data store
        if self.presentation.startswith("https"):
            tmpFile = Platform.GetTempDir() + "presentation.ppt"
            DataStore.GSIHTTPDownloadFile(self.presentation, tmpFile, None, None )
            self.viewer.LoadPresentation(tmpFile)
        else:
            self.viewer.LoadPresentation(self.presentation)

        # Go to the current slide
        self.GoToSlide(self.slideNum)

        # Go to the current step
        for i in range(self.stepNum):
            self.Next()
        
        # Set the slide number in the UI
        if self.slideNum == '':
            self.slideNum = 1
        else:
            self.log.debug("Got slide num: %d", self.slideNum)
            self.controller.SetSlideNum('%s' % self.slideNum)

        # Set the master in the UI
        self.controller.SetMaster(false)



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
def InitLogging(appName, debug=0):
    """
    This method sets up logging so you can see what's happening.
    If you want to see more logging information use the appName 'AG',
    then you'll see logging information from the Access Grid Module.
    """
    logFormat = "%(name)-17s %(asctime)s %(levelname)-5s %(message)s"


    # Set up a venue client log, too, since it's used by the event client
    log = logging.getLogger("AG.VenueClient")
    log.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler()
    hdlr.setFormatter(logging.Formatter(logFormat))
    log.addHandler(hdlr)

    log = logging.getLogger(appName)
    log.setLevel(logging.DEBUG)


    # Log to file
    logFile = appName + ".log"
    fileHandler = logging.FileHandler(logFile)
    fileHandler.setFormatter(logging.Formatter(logFormat))
    log.addHandler(fileHandler)

    # If debugging, log to command window too
    if debug:
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(logging.Formatter(logFormat))
        log.addHandler(hdlr)
    return log

def Usage():
    """
    Standard usage information for users.
    """
    print "%s:" % sys.argv[0]
    print "    -h|--help : print usage"
    print "    -d|--debug : print debugging output"
    print "    -a|--applicationURL : <url to application in venue>"
    print "    -i|--information : <print information about this application>"
    print "    -l|--logging : <log name: defaults to SharedPresentation>"



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
        opts, args = getopt.getopt(sys.argv[1:], "dv:a:l:ih",
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

    # Initialize logging
    log = InitLogging(logName, debug)

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
    presentation = SharedPresentation(appURL, log)

    if venueDataUrl:
        print "loading venueDataUrl: ", venueDataUrl
        presentation.OpenVenueData(venueDataUrl)
    else:
        print "loading data from venue"
        presentation.LoadFromVenue()

    presentation.Start()

    # This is needed because COM shutdown isn't clean yet.
    # This should be something like:
    #sys.exit(0)
    os._exit(0)

