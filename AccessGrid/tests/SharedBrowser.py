import os
import sys
import logging

from wxPython.wx import *
from wxPython.iewin import *

from AccessGrid.hosting.pyGlobus import Client

from AccessGrid import Events
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid import EventClient


log = logging.getLogger("SharedBrowser")
def init_logging(appName):
    logger = logging.getLogger("AG")
    logger.setLevel(logging.DEBUG)
    hdlr = logging.StreamHandler()
    fmt = logging.Formatter("%(name)-17s %(asctime)s %(levelname)-5s %(message)s")
    hdlr.setFormatter(fmt)
    logger.addHandler(hdlr)

    appLogger = logging.getLogger(appName)
    appLogger.setLevel(logging.DEBUG)
    appLogger.addHandler(hdlr)


class WebBrowser(wxPanel):
    """
    WebBrowser is a basic ie-based web browser class
    """
    def __init__(self, parent, id, frame = None):

        wxPanel.__init__(self, parent, id)

        self.current = None
        self.populate()

        self.navigation_callbacks = []

        self.frame = frame
        if frame is not None:
            self.title_base = frame.GetTitle()

        self.just_received_navigate = 0

    def add_navigation_callback(self, listener):
        self.navigation_callbacks.append(listener)

    def remove_navigation_callback(self, listener):
        self.navigation_callbacks.remove(listener)

    def add_button(self, name, func, sizer):
        b = wxButton(self, -1, name)
        EVT_BUTTON(self, b.GetId(), func)
        sizer.Add(b, 0, wxEXPAND)

    def populate(self):

        sizer = wxBoxSizer(wxVERTICAL)

        #
        # Create the button bar
        #

        bsizer = wxBoxSizer(wxHORIZONTAL)

        self.back_button = self.add_button("Back", self.OnBack, bsizer)
        self.forward_button = self.add_button("Forward", self.OnForward,
                                              bsizer)
        self.home_button = self.add_button("Home", self.OnHome, bsizer)
        self.stop_button = self.add_button("Stop", self.OnStop, bsizer)
        self.refresh_button = self.add_button("Refresh", self.OnRefresh,
                                              bsizer)

        t = wxStaticText(self, -1, "Location: ")
        bsizer.Add(t, 0, wxEXPAND)

        self.location = wxComboBox(self, wxNewId(), "",
                                   style=wxCB_DROPDOWN|wxPROCESS_ENTER)
        EVT_COMBOBOX(self, self.location.GetId(), self.OnLocationSelect)
        EVT_KEY_UP(self.location, self.OnLocationKey)
        EVT_CHAR(self.location, self.IgnoreReturn)
        bsizer.Add(self.location, 1, wxEXPAND)

        sizer.Add(bsizer, 0, wxEXPAND)

        #
        # Now we can set up the browser widget
        #

        self.ie = wxIEHtmlWin(self, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
        sizer.Add(self.ie, 1, wxEXPAND)

        # Hook up the event handlers for the IE window
        EVT_MSHTML_BEFORENAVIGATE2(self, -1, self.OnBeforeNavigate2)
        EVT_MSHTML_NEWWINDOW2(self, -1, self.OnNewWindow2)
        EVT_MSHTML_DOCUMENTCOMPLETE(self, -1, self.OnDocumentComplete)
        # EVT_MSHTML_STATUSTEXTCHANGE(self, -1, self.OnStatusTextChange)
        EVT_MSHTML_TITLECHANGE(self, -1, self.OnTitleChange)


        self.SetSizer(sizer)
        self.SetAutoLayout(1)
        self.Layout()

    def OnBeforeNavigate2(self, event):
        url = event.GetText1()

        if self.just_received_navigate:
            self.just_received_navigate = 0
        else:
            print "Before navigate ", url
            map(lambda a: a(url), self.navigation_callbacks)

    def OnNewWindow2(self, event):
        print "On new window: ", event.GetText1()
        event.Veto() # don't allow it

    def OnDocumentComplete(self, event):
        print "OnDocumentComplete: ", event.GetText1()
        self.current = event.GetText1()
        self.location.SetValue(self.current)

    def OnTitleChange(self, event):
        print "titlechange: ", event.GetText1()
        if self.frame:
            self.frame.SetTitle(self.title_base + ' -- ' + event.GetText1())

    def OnStatusTextChange(self, event):
        #print "status: ", event.GetText1()
        if self.frame:
            self.frame.SetStatusText(event.GetText1())

    def OnBack(self, event):
        self.ie.GoBack()

    def OnForward(self, event):
        self.ie.GoForward()

    def OnStop(self, event):
        self.ie.Stop()

    def OnHome(self, event):
        self.ie.GoHome()

    def OnRefresh(self, event):
        self.ie.Refresh(wxIEHTML_REFRESH_COMPLETELY)

    def navigate(self, url):
        print "NAVIGATE to ", url
        self.just_received_navigate = 1
        self.ie.Navigate(url)

    def OnLocationSelect(self, event):
        url = self.location.GetStringSelection()
        self.ie.Navigate(url)

    def OnLocationKey(self, event):
        if event.KeyCode() == WXK_RETURN:
            URL = self.location.GetValue()
            self.location.Append(URL)
            self.ie.Navigate(URL)
        else:
            event.Skip()

    def IgnoreReturn(self, event):
        if event.GetKeyCode() != WXK_RETURN:
            event.Skip()


class SharedBrowser( wxApp ):
    """
    SharedBrowser combines a SharedApplication and a WebBrowser
    to provide shared web browsing to venue users
    """
    def OnInit(self):
        return 1

    def OnExit(self):
        self.eventClient.Stop()
        os._exit(1)

    def __init__( self, venueUrl, profile ):

        wxApp.__init__(self, False)
        
        self.venueUrl = venueUrl
        self.profile = profile

        self.venueProxy = Client.Handle(venueUrl).GetProxy()

        # Join the application
        self.privateId = self.venueProxy.Join(profile)

        #
        # Retrieve the channel id
        #
        (self.channelId, eventServiceLocation ) = self.venueProxy.GetDataChannel(self.privateId)

        # 
        # Subscribe to the event channel
        #
        self.eventClient = EventClient.EventClient(eventServiceLocation, self.channelId)
        self.eventClient.start()
        self.eventClient.Send(Events.ConnectEvent(self.channelId))

        #
        # Register browse event callback
        #
        # The callback function is invoked with one argument, the data from the call.
        self.eventClient.RegisterCallback("browse", self.BrowseCallback )

        #
        # Create Browser Window
        #
        self.frame = wxFrame(None, -1, "Browser")
        self.browser = WebBrowser(self.frame, -1, self.frame)

        # Add callback for local browsing
        self.browser.add_navigation_callback( self.IBrowsedCallback )

        # Browse to the current url, if exists
        currentUrl = self.venueProxy.GetData(self.privateId, "url")
        if len(currentUrl) > 0:
            self.browser.navigate(currentUrl)

        self.frame.Show(1)
        self.SetTopWindow(self.frame)

    def IBrowsedCallback(self,data):
        #
        # Send out the event, including our public ID in the message.
        #
        self.eventClient.Send(Events.Event("browse", self.channelId, ( self.profile.publicId, data ) ))

        # Store the URL in the app object in the venue
        self.venueProxy.SetData(self.privateId, "url", data)

    def BrowseCallback(self, data):
        """
        Callback invoked when incoming browse events arrive.  Events
        can include this component's browse events, so these need to be
        filtered out.
        """

        # Determine if the sender of the event is this component or not.
        (senderId, url) = data
        if senderId == self.profile.publicId:
            print "Ignoring %s from myself" % (url)
        else:
            print "Browse to ", url
            self.browser.navigate(url)

        
if __name__ == "__main__":
    init_logging("watcher")

    if len(sys.argv) < 3:
        print "Usage: %s <appObjectUrl> <profileFile>" % sys.argv[0]
        sys.exit(1)

    venueUrl = sys.argv[1]
    profileFile = sys.argv[2]

    profile = ClientProfile(profileFile)
    sb = SharedBrowser( venueUrl, profile )
    sb.MainLoop()
