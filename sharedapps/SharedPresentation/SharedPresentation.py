#-----------------------------------------------------------------------------
# Name:        SharedPresentation.py
# Purpose:     This is the Shared Presentation Software. It is currently very
#              basic, but provides the basis for doing much more advanced
#              functionality.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: SharedPresentation.py,v 1.3 2003-07-16 16:47:37 turam Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
# TO DO
# - test behavior with bad credentials
# - handle transitions between slides
#-----------------------------------------------------------------------------
# Normal import stuff
import os
import sys
import getopt
import logging
from threading import Thread
from Queue import Queue
import cmd, string

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
    print "    -a|--applicationURL : <url to application in venue>"
    print "    -i|--information : <print information about this application>"
    print "    -l|--logging : <log name: defaults to SharedPresentation>"




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

        self.lastSlide = 0

        self.pptAlreadyOpen = 0
    
    def Start(self, file=None):
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

        # Call our own openfile method to start stuff going
        if file != None:
            self.OpenFile(file)

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

        # Open a new presentation and keep a reference to it in self.p
        self.presentation = self.ppt.Presentations.Open(file)
        self.lastSlide = self.presentation.Slides.Count

        # Start viewing the slides in a window
        self.presentation.SlideShowSettings.ShowType = win32com.client.constants.ppShowTypeWindow
        self.win = self.presentation.SlideShowSettings.Run()
        
    def NextSlide(self):
        """
        This method moves to the next slide.
        """
        # Move to the next slide
        self.win.View.Next()

    def PreviousSlide(self):
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
        This method returns the index of the last slides (indexed from 1)
        """
        return self.lastSlide

    def GetSlideNum(self):
        """
        This method returns the index of the current slide
        """
        return self.win.View.CurrentShowPosition


class SharedPresentationFrame(wxFrame):

    ID_CLEAR = wxNewId()
    ID_EXIT = wxNewId()

    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title,
                         wxDefaultPosition, wxSize(450, 300))


        self.loadCallback = None
        self.clearSlidesCallback = None
        self.prevCallback = None
        self.nextCallback = None
        self.gotoCallback = None
        self.masterCallback = None
        self.exitCallback = None

        #
        # Create UI controls
        #
        
        # - Create menu bar
        menubar = wxMenuBar()
        fileMenu = wxMenu()
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

        EVT_MENU(self, self.ID_CLEAR, self.ClearSlidesCB)
        EVT_MENU(self, self.ID_EXIT, self.ExitCB)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Callback stubs for the UI
    #

    def PrevSlideCB(self,event):
        """
        Callback for "previous" button
        """

        if self.prevCallback:
            self.prevCallback()

    def NextSlideCB(self,event):
        """
        Callback for "next" button
        """
        if self.nextCallback:
            self.nextCallback()

    def GotoSlideNumCB(self,event):
        """
        Callback for "enter" presses in the slide number text field
        """
        if self.masterCheckBox.IsChecked():
            if self.gotoCallback:
                slideNum = int(self.slideNumText.GetValue())
                self.gotoCallback(slideNum)

    def MasterCB(self,event):
        """
        Callback for "master" checkbox
        """
        if self.masterCallback:
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
            if self.loadCallback:
                self.loadCallback(slidesUrl)

    def ClearSlidesCB(self,event):
        """
        Callback for "clear slides" menu item
        """
        if self.clearSlidesCallback:
            self.clearSlidesCallback()

    def ExitCB(self,event):
        """
        Callback for "exit" menu item
        """
        if self.exitCallback:
            self.exitCallback()


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Client methods
    #

    def SetCallbacks(self, loadCallback, 
                           closeCallback,
                           prevCallback, 
                           nextCallback, 
                           gotoCallback,
                           masterCallback,
                           exitCallback):
        """
        This method is used to set callbacks for the UI
        """
        
        self.loadCallback = loadCallback
        self.closeCallback = closeCallback
        self.prevCallback = prevCallback
        self.nextCallback = nextCallback
        self.gotoCallback = gotoCallback
        self.masterCallback = masterCallback
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
                           closeCallback,
                           prevCallback, 
                           nextCallback, 
                           gotoCallback,
                           masterCallback,
                           exitCallback):
        """
        Pass-through to frame's SetCallbacks method
        """

        self.frame.SetCallbacks(loadCallback, 
                                closeCallback,
                                prevCallback, 
                                nextCallback, 
                                gotoCallback,
                                masterCallback,
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




# Depending on the platform decide which viewer to use
if sys.platform == Platform.WIN:
    # If we're on Windows we try to use the python/COM interface to PowerPoint
    defaultViewer = PowerPointViewer
else:
    # On Linux the best choice is probably Open/Star Office
    defaultViewer = None

class SharedPresEvent:
    NEXT = "next"
    PREV = "prev"
    MASTER = "master"
    GOTO = "goto"
    CLOSE = "close"
    QUIT = "quit"
    LOAD = "load"

class SharedPresKey:
    SLIDEURL = "slideurl"
    SLIDENUM = "slidenum"
    MASTER = "master"

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
        self.eventQueue = Queue(5)
        self.log = log
        self.lastSlide = 0
        self.running = 0
        self.masterId = None
        
        # Set up method dictionary for the queue processor to call
        # callbacks based on the event type
        #
        # This is an ugly hack, so we can lookup methods by event name
        self.methodDict = dict()
        self.methodDict[SharedPresEvent.NEXT] = self.NextSlide
        self.methodDict[SharedPresEvent.PREV] = self.PreviousSlide
        self.methodDict[SharedPresEvent.GOTO] = self.GoToSlide
        self.methodDict[SharedPresEvent.LOAD] = self.LoadPresentation
        self.methodDict[SharedPresEvent.QUIT] = self.Quit
        self.methodDict[SharedPresEvent.MASTER] = self.SetMaster
        self.methodDict[SharedPresEvent.CLOSE] = self.ClosePresentation

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
        # We pass the controller callbacks that send the events to the Data
        # Channel. 
        self.log.debug("Creating controller.")
        self.controller = UIController(0)
        self.controller.SetCallbacks( self.SendLoad,
                                      self.SendClearSlides,
                                      self.SendPrev,
                                      self.SendNext,
                                      self.SendGoto,
                                      self.SendMaster,
                                      self.QuitCB)
        

        # Retrieve the current presentation
        self.presentation = self.appProxy.GetData(self.privateId,
                                                  SharedPresKey.SLIDEURL)

        # Set the slide URL in the UI
        if len(self.presentation) != 0:
            self.log.debug("Got presentation: %s", self.presentation)
            self.controller.SetSlides(self.presentation)


        # Retrieve the current slide
        self.currentSlide = self.appProxy.GetData(self.privateId,
                                                  SharedPresKey.SLIDENUM)

        # Set the slide number in the UI
        if self.currentSlide == '':
            self.currentSlide = 1
        else:
            self.log.debug("Got slide num: %d", self.currentSlide)
            self.controller.SetSlideNum('%s' % self.currentSlide)

        # Set the master in the UI
        self.controller.SetMaster(false)

        # Start the queue thread
        Thread(target=self.ProcessEventQueue).start()

        # Start the controller 
        # (this is the main thread, so we'll block here until
        # the controller is closed)
        self.controller.Start()

        # Put a quit event, so the viewer gets shut down correctly
        self.eventQueue.put([SharedPresEvent.QUIT, None])

        # When the quit event gets processed, the running flag gets cleared
        self.log.debug("Shutting down...")
        import time
        while self.running:
            print ".",
            time.sleep(1)


    def ProcessEventQueue(self):
        # The queue processing thread is the only one allowed to access
        # the viewer; that keeps the requirements on the viewer minimal.
        # This method loops, processing events that it gets from the 
        # eventQueue.
        # Events are put in this eventQueue by the Recv* methods.

        import pythoncom
        pythoncom.CoInitialize()

        self.viewer = defaultViewer()
        self.viewer.Start()

        # Load presentation locally, if we got one from the venue app object
        if len(self.presentation) != 0:
            try:
                self.LoadPresentation((self.publicId, self.presentation))

                # Go to current slide, if we got one from the venue app object
                if self.currentSlide != '':
                    self.GoToSlide((0,self.currentSlide))
            except:
                self.log.exception("EXCEPTION LOADING SLIDES/VIEWING FIRST SLIDE")


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
    #

    def SendNext(self):
        """
        This method sends a next slide event over the data channel.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendNext called")

        if self.masterId == self.publicId:

            # Increment the current slide
            if self.currentSlide < self.viewer.GetLastSlide():
                self.currentSlide += 1
                self.SendGoto(self.currentSlide)

    def SendPrev(self):
        """
        This method sends a previous slide event over the data channel.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendPrev called")

        if self.masterId == self.publicId:
            # Decrement the current slide
            if self.currentSlide > 1:
                self.currentSlide -= 1
                self.SendGoto(self.currentSlide)


    def SendGoto(self, number):
        """
        This method sends a goto slide event over the data channel.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendGoto called; slidenum=(%d)", number)

        if self.masterId == self.publicId:
            if number > 0 and number <= self.viewer.GetLastSlide():
                self.currentSlide = number

                # Store the current slide number in the venue
                self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, 
                                      self.currentSlide)

                # We send the event, which is wrapped in an Event instance
                self.eventClient.Send(Event(SharedPresEvent.GOTO, self.channelId,
                                            (self.publicId, self.currentSlide)
                                            ))

    def SendLoad(self, path):
        """
        This method sends a load presentation event over the data channel.
        The event is only sent if the local user is the "master"
        """
        self.log.debug("Method SendLoad called; path=(%s)", path)

        if self.masterId == self.publicId:
            # Let's set the presentation in the venue
            self.appProxy.SetData(self.privateId, SharedPresKey.SLIDEURL, path)
            self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, 1)
            
            # We send the event, which is wrapped in an Event instance
            self.eventClient.Send(Event(SharedPresEvent.LOAD, self.channelId,
                                        (self.publicId, path)
                                        ))

    def SendMaster(self, flag):
        """
        This method sends a quit event over the data channel.
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
                                            (self.publicId, "")
                                            ))
            else:
                self.log.debug(" User is not master; skipping")


    def SendClearSlides(self):
        """
        This method will clear the slides from the venue app object;
        and close the local presentation
        """
        self.log.debug("Method SendClearSlides called")

        # Clear the slides url stored in the venue
        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDEURL, "")
        self.appProxy.SetData(self.privateId, SharedPresKey.SLIDENUM, "")
        self.eventQueue.put([SharedPresEvent.CLOSE, None])

    def QuitCB(self):
        """
        This method puts a "quit" event in the queue, to get the
        viewer to shutdown
        """
        self.log.debug("Method QuitCB called")

        self.eventQueue.put([SharedPresEvent.QUIT, None])


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #
    # Methods registered as callbacks with EventClient
    #

    def RecvNext(self, event):
        """
        This callback puts the "next" event from the network on
        the event queue.
        """
        self.log.debug("Method RecvNext called")

        if self.masterId == event.data[0]:

            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.NEXT, event.data])
            except Full:
                self.log.debug("Dropping event, event Queue full!")

    def RecvPrev(self, event):
        """
        This callback puts the "previous" event from the network on
        the event queue.
        """
        self.log.debug("Method RecvPrev called")

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

        if self.masterId == event.data[0]:
            # We put the passed in event on the event queue
            try:
                self.eventQueue.put([SharedPresEvent.GOTO, event.data])
            except Full:
                self.log.debug("Dropping event, event Queue full!")
        
    def RecvLoad(self, event):
        """
        This callback puts the "load" presentation event from
        the network on the event queue.
        """
        self.log.debug("Method RecvLoad called")

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
    # Methods called by the queue processor
    #   

    def NextSlide(self, data):
        """
        This is the _real_ next slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method NextSlide called")

        # Call the viewers NextSlide method
        if self.viewer != None:
            self.viewer.NextSlide()
            self.currentSlide = self.viewer.GetSlideNum()
            self.controller.SetSlideNum(self.currentSlide)
        else:
            self.log.debug("No presentation loaded!")
        
    def PreviousSlide(self, data):
        """
        This is the _real_ previous slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("Method PreviousSlide called")

        # Call the viewers PreviousSlide method
        if self.viewer != None:
            self.viewer.PreviousSlide()
        else:
            self.log.debug("No presentation loaded!")
        
    def GoToSlide(self, data):
        """
        This is the _real_ goto slide method that tells the viewer to move
        to the next slide.
        """
        (id, number) = data
        self.log.debug("Method GoToSlide called; id,slidenum=(%s %d)", id, number)

        # Call the viewers GotoSlide method
        if self.viewer != None:
            self.viewer.GoToSlide(number)
            self.currentSlide = number
        else:
            self.log.debug("No presentation loaded!")

        self.controller.SetSlideNum(number)
                   
    def LoadPresentation(self, data):
        """
        This is the _real_ load presentation method that tells the viewer
        to move to the next slide.
        """
        self.log.debug("Method LoadPresentation called; url=(%s)", data[1])

        presentationUrl = data[1]

        # Call the viewers LoadPresentation method
        self.viewer.LoadPresentation(presentationUrl)

        self.controller.SetSlides(presentationUrl)
        self.controller.SetSlideNum(1)


    def SetMaster(self, data):
        """
        This method sets the master of the presentation
        """
        self.log.debug("Method SetMaster called")

        # Store the master's public id locally
        self.masterId = data[1]

        # Update the controller accordingly
        if self.masterId == self.publicId:
            self.controller.SetMaster(true)
        else:
            self.controller.SetMaster(false)

    def ClosePresentation(self,data):
        """
        This method closes the presentation in the viewer
        """
        self.log.debug("Method ClosePresentation called")

        self.viewer.EndShow()

    def Quit(self, data):
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



if __name__ == "__main__":
    # Initialization of variables
    venueURL = None
    appURL = None
    logName = "SharedPresentation"

    # Here we parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "v:a:l:ih",
                                   ["venueURL=", "applicationURL=",
                                    "information=", "logging=", "help"])
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
        elif o in ("-h", "--help"):
            Usage()
            sys.exit(0)

    # Initialize logging
    log = InitLogging(logName)

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

    # This is needed because COM shutdown isn't clean yet.
    # This should be something like:
    #sys.exit(0)
    os._exit(0)

