#-----------------------------------------------------------------------------
# Name:        SharedPresentation.py
# Purpose:     This is the Shared Presentation Software. It is currently very
#              basic, but provides the basis for doing much more advanced
#              functionality.
#
# Author:      Ivan R. Judson
#
# Created:     2002/12/12
# RCS-ID:      $Id: SharedPresentation.py,v 1.4 2003-04-24 18:36:47 judson Exp $
# Copyright:   (c) 2003
# Licence:     See COPYING.TXT
#-----------------------------------------------------------------------------
# Normal import stuff
import os
import sys
import getopt
import logging
from threading import Thread
from Queue import Queue
import cmd, string

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
def InitLogging(appName):
    """
    This method sets up logging so you can see what's happening.
    If you want to see more logging information use the appName 'AG',
    then you'll see logging information from the Access Grid Module.
    """
    logFormat = "%(name)-17s %(asctime)s %(levelname)-5s %(message)s"
    log = logging.getLogger(appName)
    log.setLevel(logging.DEBUG)
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
        pass
    
    def Start(self, file=None):
        """
        This method actually fires up PowerPoint and if specified opens a
        file and starts viewing it.
        """
        # Instantiate the powerpoint application via COM
        self.ppt = win32com.client.Dispatch("PowerPoint.Application")

        # Make it active (visible)
        self.ppt.Activate()

        # call our own openfile method to start stuff going
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

        # Exit the powerpoint application
        self.ppt.Quit()
        
    def LoadPresentation(self, file):
        """
        This method opens a file and starts the viewing of it.
        """
        # Open a new presentation and keep a reference to it in self.p
        self.presentation = self.ppt.Presentations.Open(file)

        # Start viewing the slides in a window
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

class CmdLineController(cmd.Cmd, Thread):
    """
    This class provides a presentation controller that reads commands
    from the command line.

    This is a subclass of both the python command interpreter and the
    Thread object. Ideally this would be something that intercepts
    events from the actual viewer and sends them on the network, but
    that's not working yet.
    """
    def __init__(self, nextCallback, prevCallback, gotoCallback,
                 loadCallback, quitCallback):
        """
        We only have to pass the init to our super class for Thread
        setup and keep track of our callbacks.
        """
        Thread.__init__(self)
        self.nextCB = nextCallback
        self.prevCB = prevCallback
        self.gotoCB = gotoCallback
        self.loadCB = loadCallback
        self.quitCB = quitCallback
        self.prompt = "Shared Presentation Controller>"
        
    def run(self):
        """
        This kicks the thread off, we spin on a command loop, processing input.
        """
        # This is the cmd processor method that deals with input
        self.cmdloop()
        
    def next(self):
        """
        This method does the real work of calling the callback.
        """
        # Call the next callback
        self.nextCB()
        
    def previous(self):
        """
        This method does the real work of calling the callback.
        """
        # Call the previous callback
        self.prevCB()
        
    def goto(self, number):
        """
        This method does the real work of calling the callback.
        """
        # Call the go to slide callback
        self.gotoCB(number)

    def load(self, path):
        """
        This method does the real work of calling the callback.
        """
        # Call the load presentation callback
        self.loadCB(path)
        
    def quit(self):
        """
        This method does the real work of calling the callback.
        """
        # Call the quit callback
        self.quitCB()

    # These methods are used by the command processor to recognize input
    # see the documentation on the command processor (cmd module) for
    # more information
    def do_next(self, argline):
        self.next()
    def do_n(self, argline):
        self.next()
        
    def do_prev(self, argline):
        self.previous()
    def do_p(self, argline):
        self.previous()

    def do_goto(self, argline):
        if len(argline) == 0:
            return
        else:
            number = int(argline)
            self.goto(number)

    def do_g(self, argline):
        if len(argline) == 0:
            return
        else:
            number = int(argline)
            self.goto(number)

    def do_load(self, argline):
        path = argline
        self.load(path)
    def do_l(self, argline):
        path = argline
        self.load(path)
        
    def do_quit(self, argline):
        self.quit()
    def do_q(self, argline):
        self.quit()

# Depending on the platform decide which viewer to use
if sys.platform == Platform.WIN:
    # If we're on Windows we try to use the python/COM interface to PowerPoint
    defaultViewer = PowerPointViewer
else:
    # On Linux the best choice is probably Open/Star Office
    defaultViewer = None

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

        # This is an ugly hack, so we can lookup methods by event name
        self.methodDict = dict()
        self.methodDict["next"] = self.NextSlide
        self.methodDict["prev"] = self.PreviousSlide
        self.methodDict["goto"] = self.GoToSlide
        self.methodDict["load"] = self.LoadPresentation
        self.methodDict["quit"] = self.Quit

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
        self.eventClient.RegisterCallback("next", self.RecvNext)
        self.eventClient.RegisterCallback("prev", self.RecvPrev)
        self.eventClient.RegisterCallback("goto", self.RecvGoto)
        self.eventClient.RegisterCallback("load", self.RecvLoad)
        self.eventClient.RegisterCallback("quit", self.RecvQuit)

        # Start the viewer
        self.log.debug("Creating viewer.")
        self.viewer = defaultViewer()
        self.viewer.Start()

        # Create the controller
        # We pass the controller callbacks that send the events to the Data
        # Channel. 
        self.log.debug("Creating controller.")
        self.controller = CmdLineController(self.SendNext, self.SendPrev,
                                            self.SendGoto, self.SendLoad,
                                            self.SendQuit)

        self.log.debug("Getting current presentation.")

        # Retrieve the current presentation
        self.presentation = self.appProxy.GetData(self.privateId,
                                                  "presentation")

        self.log.debug("Got presentation: %s", self.presentation)
                       
        # If there is one load it
        if len(self.presentation) != 0:
            self.LoadPresentation((self.publicId, self.presentation))
        
        self.log.debug("Getting current slide.")

        # Retrieve the current slide
        self.currentSlide = self.appProxy.GetData(self.privateId,
                                                  "current slide")

        # If there is one, go to it
        if len(self.currentSlide) != 0:
            self.GoToSlide(self.currentSlide)

        # Retrieve the current master
        self.master = self.appProxy.GetData(self.privateId, "master")
        
        # Start the controller thread
        self.controller.start()

        # The main application thread is the only one allowed to access
        # the viewer, that keeps the requirements on the viewer minimal.
        # The main application thread loops processing events that it
        # gets from the eventQueue.
        # Events are put in this eventQueue by the Recv* methods.
        self.running = 1
        while self.running:
            # Pull the next event out of the queue
            (event, data) = self.eventQueue.get(1)

            self.log.debug("Got Event: %s %s", event, str(data))

            # Invoke the matching method passing the data
            self.methodDict[event](data)

    def SendNext(self):
        """
        This method sends a next slide event over the data channel.
        """
        self.log.debug("SendNext")

        # We send the event, which is wrapped in an Event instance
        # the Event object is documented in AccessGrid\Events.py
        self.eventClient.Send(Event("next", self.channelId,
                                    (self.publicId)
                                    ))
    def SendPrev(self):
        """
        This method sends a previous slide event over the data channel.
        """
        self.log.debug("SendPrev")

        # We send the event, which is wrapped in an Event instance
        self.eventClient.Send(Event("prev", self.channelId,
                                    (self.publicId)
                                    ))

    def SendGoto(self, number):
        """
        This method sends a goto slide event over the data channel.
        """
        self.log.debug("SendGoto")

        # We send the event, which is wrapped in an Event instance
        self.eventClient.Send(Event("goto", self.channelId,
                                    (self.publicId, number)
                                    ))

    def SendLoad(self, path):
        """
        This method sends a load presentation event over the data channel.
        """
        self.log.debug("SendLoad")

        # Let's set the presentation in the venue
        self.appProxy.SetData(self.privateId, "presentation", path)
        
        # We send the event, which is wrapped in an Event instance
        self.eventClient.Send(Event("load", self.channelId,
                                    (self.publicId, path)
                                    ))

    def SendQuit(self):
        """
        This method sends a quit event over the data channel.
        """
        self.log.debug("SendQuit")

        # We send the event, which is wrapped in an Event instance
        self.eventClient.Send(Event("quit", self.channelId,
                                    (self.publicId)
                                    ))

    def RecvNext(self, data):
        """
        This is a callback that puts the next event from the network on
        the event queue.
        """
        self.log.debug("In RecvNext")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put(["next", data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")

    def RecvPrev(self, data):
        """
        This is a callback that puts the previous event from the network on
        the event queue.
        """
        self.log.debug("In RecvPrev")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put(["prev", data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")
        
    def RecvGoto(self, data):
        """
        This is a callback that puts the goto slide event from the network on
        the event queue.
        """
        self.log.debug("In RecvGoto")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put(["goto", data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")
        
    def RecvLoad(self, data):
        """
        This is a callback that puts the load presentation event from
        the network on the event queue.
        """
        self.log.debug("In RecvLoad")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put(["load", data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")
        
    def RecvQuit(self, data):
        """
        This is a callback that puts the quit event from the network on
        the event queue.
        """
        self.log.debug("In RecvQuit")

        # We put the passed in event on the event queue
        try:
            self.eventQueue.put(["quit", data])
        except Full:
            self.log.debug("Dropping event, event Queue full!")
        
    def NextSlide(self, data):
        """
        This is the _real_ next slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("in Next Slide")

        # Call the viewers NextSlide method
        if self.viewer != None:
            self.viewer.NextSlide()
        else:
            self.log.debug("No presentation loaded!")
        
    def PreviousSlide(self, data):
        """
        This is the _real_ previous slide method that tells the viewer to move
        to the next slide.
        """
        self.log.debug("in previous slide")

        # Call the viewers NextSlide method
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
        self.log.debug("in goto slide (%s %d)", id, number)

        # Call the viewers NextSlide method
        if self.viewer != None:
            self.viewer.GoToSlide(number)
        else:
            self.log.debug("No presentation loaded!")
                   
    def LoadPresentation(self, data):
        """
        This is the _real_ load presentation method that tells the viewer
        to move to the next slide.
        """
        self.log.debug("in load presentation (%s)", data[1])

        # Call the viewers LoadPresentation method
        self.viewer.LoadPresentation(data[1])

    def Quit(self, data):
        """
        This is the _real_ Quit method that tells the viewer to move
        to the next slide.
        """
        # Turn off the main loop
        self.running = 0

        # Stop the viewer
        self.viewer.Stop()

        # Close the viewer
        self.viewer.Quit()

        # Get rid of the controller
        self.controller = None

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
    # sys.exit(0)
    os._exit(0)

