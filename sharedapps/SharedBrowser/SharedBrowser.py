import os
import sys
import logging
import sys
import getopt

from wxPython.wx import *
from wxPython.iewin import *

from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid import icons
from AccessGrid.Toolkit import WXGUIApplication
    
class WebBrowser(wxPanel):
    """
    WebBrowser is a basic ie-based web browser class
    """
    def __init__(self, parent, id, log, frame = None):
        wxPanel.__init__(self, parent, id)

        self.log = log
        self.current = None
        self.populate()

        self.navigation_callbacks = []

        self.frame = frame
        if frame is not None:
            self.title_base = frame.GetTitle()

        self.just_received_navigate = 0
        # The document url currently being loaded.
        self.docLoading = ""
        # Pages whose completion we need to ignore.  This is because
        #  the events don't tell us which events are for the main page.
        self.ignoreComplete = []

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
            if url != self.docLoading:
                message = "OnBeforeNav Skipping "+url+"already loading"+self.docLoading 
                self.log.debug(message)
                # If we get a navigation event while loading, we will ignore
                #   the completion since it is from a popup or sub-page.
                self.ignoreComplete.append(url)
                # Because of popups and lack of complete information from
                #   events, we won't reset this (and let the user
                #   navigate) until the document is finished loading.
                # self.just_received_navigate = 0
            else:
                pass # Do nothing since we are already loading this url.
        else:
            # Go to a new url and also send it to the other Shared
            #   Browser clients.  The Send is done in IBrowseCallback.
            message = "Before navigate "+url
            self.log.debug(message)
            self.just_received_navigate = 1
            self.docLoading = url
            map(lambda a: a(url), self.navigation_callbacks)

    def OnNewWindow2(self, event):
        message = "On new window: " +event.GetText1()
        self.log.debug(message)
        event.Veto() # don't allow it

    def OnDocumentComplete(self, event):
        message = "OnDocumentComplete: " + event.GetText1()
        self.log.debug(message)
        self.current = event.GetText1()

        # Check if we are finishing the main document or not.
        if event.GetText1() not in self.ignoreComplete:
            
            if event.GetText1() == "about:blank" and self.docLoading != "about:blank":
                # This case happens at startup.
                self.log.debug("Ignoring DocComplete for first about:blank")
            else:
                # Finished loading, allow user to click links again now.
                #  Needed since there is not enough information in the
                #   events to tell if they refer to a popup (and other sub-
                #   pages) or a user clicking on a url.
                self.log.debug("Finished loading.")
                self.just_received_navigate = 0
                self.current = event.GetText1()
                self.location.SetValue(self.current)
                while len(self.ignoreComplete) > 0:
                    self.ignoreComplete.pop()
        else:
            message = "Ignoring DocComplete for ", event.GetText1()
            self.just_received_navigate = 0
            self.log.debug(message)

    def LocalEvent(self):
        # Reset just_received_navigate flag when url is triggered by combobox or buttons.
        # Else, the browser may not be able to receive incoming remote events
        # from other clients.
        self.just_received_navigate = 0

    def OnTitleChange(self, event):
        self.log.debug("titlechange: " + event.GetText1())
        if self.frame:
            self.frame.SetTitle(self.title_base + ' -- ' + event.GetText1())

    def OnStatusTextChange(self, event):
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
        self.LocalEvent()
        self.ie.Refresh(wxIEHTML_REFRESH_COMPLETELY)
       
    def navigate(self, url):
        if self.just_received_navigate:
            self.log.debug("___cancelled NAVIGATE to "+url)
        else:
            self.log.debug("NAVIGATE to "+url)
            self.just_received_navigate = 1
            self.docLoading = url
            self.ie.Navigate(url)
         
    def OnLocationSelect(self, event):
        self.LocalEvent()
        url = self.location.GetStringSelection()
        self.ie.Navigate(url)

    def OnLocationKey(self, event):
        if event.KeyCode() == WXK_RETURN:
            self.LocalEvent()
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
        '''
        Shut down shared browser.
        '''
        self.sharedAppClient.Shutdown()
        os._exit(1)

    def __init__( self, appUrl, name):
        '''
        Creates the shared application client, used for 
        application service interaction, and opens a web browser 
        for UI display. 
        '''
        wxApp.__init__(self, False)
        
        # Create shared application client        
        self.sharedAppClient = SharedAppClient(name)
        self.log = self.sharedAppClient.InitLogging()

        # Get client profile
        try:
            clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(), "profile")
            clientProfile = ClientProfile(clientProfileFile)
        except:
            self.log.info("SharedAppClient.Connect: Could not load client profile, set clientProfile = None")
            clientProfile = None

        # Join the application session.
        self.sharedAppClient.Join(appUrl, clientProfile)

        # Register browse event callback
        self.sharedAppClient.RegisterEventCallback("browse", self.BrowseCallback )

        # Create Browser Window
        self.frame = wxFrame(None, -1, "Browser")
        self.browser = WebBrowser(self.frame, -1, self.log, self.frame)

        # Add callback for local browsing
        self.browser.add_navigation_callback( self.IBrowsedCallback )

        # Browse to the current url, if exists
        currentUrl = self.sharedAppClient.GetData("url")
        
        if currentUrl and len(currentUrl) > 0:
            self.browser.navigate(currentUrl)
            try:
                self.sharedAppClient.SetParticipantStatus(currentUrl)
            except:
                self.log.exception("SharedBrowser:__init__: Failed to set participant status")

        self.frame.SetIcon(icons.getAGIconIcon())
        self.frame.Show(1)
        self.SetTopWindow(self.frame)


    def IBrowsedCallback(self,data):
        '''
        Callback invoked when local browse events occur.
        '''
        # Send out the event, including our public ID in the message.
        publicId = self.sharedAppClient.GetPublicId()
        self.sharedAppClient.SendEvent("browse", ( publicId, data ) )
        # Store the URL in the application service in the venue
        self.sharedAppClient.SetData("url", data)
        
    def BrowseCallback(self, event):
        """
        Callback invoked when incoming browse events arrive.  Events
        can include this component's browse events, so these need to be
        filtered out.
        """

        # Determine if the sender of the event is this component or not.
        (senderId, url) = event.data
        if senderId == self.sharedAppClient.GetPublicId():
            self.log.debug("Ignoring"+url+"from myself ")
        else:
            self.log.debug("Browse to "+ url)
            self.browser.navigate(url)

        try:
            self.sharedAppClient.SetParticipantStatus(url)
        except:
            self.log.exception("SharedBrowser:__init__: Failed to set participant status")
            
            
class ArgumentManager:
    def __init__(self):
        self.arguments = {}
        self.arguments['applicationUrl'] = None
        self.arguments['debug'] = 0
        
    def GetArguments(self):
        return self.arguments
        
    def Usage(self):
        """
        How to use the program.
        """
        print "%s:" % sys.argv[0]
        print "    -a|--applicationURL : <url to application in venue>"
        print "    -d|--debug : <enables debug output>"
        print "    -h|--help : <print usage>"
        
    def ProcessArgs(self):
        """
        Handle any arguments we're interested in.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:], "a:d:h",
                                       ["applicationURL=", "debug", "help"])
        except getopt.GetoptError:
            self.Usage()
            sys.exit(2)
            
        for o, a in opts:
            if o in ("-a", "--applicationURL"):
                self.arguments["applicationUrl"] = a
            elif o in ("-d", "--debug"):
                self.arguments["debug"] = 1
            elif o in ("-h", "--help"):
                self.Usage()
                sys.exit(0)
    
        
if __name__ == "__main__":
    app = WXGUIApplication()
    name = "SharedBrowser"
    
    # Parse command line options
    am = ArgumentManager()
    am.ProcessArgs()
    aDict = am.GetArguments()
    
    appUrl = aDict['applicationUrl']
    debugMode = aDict['debug']

    init_args = []

    if "--debug" in sys.argv or "-d" in sys.argv:
        init_args.append("--debug")

    app.Initialize(name, args=init_args)
          
    if not appUrl:
        am.Usage()
    else:
        wxInitAllImageHandlers()
        sb = SharedBrowser( appUrl, name)
        sb.MainLoop()
        
    #
    # Stress test. Start a client and send events.
    #
    #import threading
    #import time
    
    #browsers = []
    #threadList = []
    #urls = ["www.oea.se","www.aftonbladet.se", "www.passagen.se"]
    
    #def StartBrowser():
    #    sb = SharedBrowser(appUrl, debugMode, logging)
    #    browsers.append(sb)
    #    sb.MainLoop()

    #def SendEvents(sharedAppClient):
    #    time.sleep(3)
    #    while 1:
    #        for url in urls:
    #            publicId = sharedAppClient.GetPublicId()
    #            sharedAppClient.SendEvent("browse", (publicId, url))
    #            sharedAppClient.SetParticipantStatus(url)
    #            # Store the URL in the application service in the venue
    #            sharedAppClient.SetData("url", url)
    #            time.sleep(0.07)
            
    #s = SharedAppClient("SharedAppClientTest")
    #s.InitLogging()
    #clientProfileFile = os.path.join(GetUserConfigDir(), "profile")
    #clientProfile = ClientProfile(clientProfileFile)
    #s.Join(appUrl, clientProfile)
    
    #thread = threading.Thread(target = SendEvents, args = [s])
    #thread.start()

    #StartBrowser()
    

