--- sharedapps/SharedBrowser/SharedBrowser.py.orig	Sat Jan 28 09:46:35 2006
+++ sharedapps/SharedBrowser/SharedBrowser.py	Wed Jun  7 10:19:32 2006
@@ -1,11 +1,17 @@
+
 import os
 import sys
 import logging
 import sys
 import getopt
 
+from AccessGrid import Platform
+
 from wxPython.wx import *
-import wx.lib.iewin as  iewin
+if sys.platform == Platform.WIN:
+    import wx.lib.iewin as iewin
+else:
+    from wxPython.mozilla import *
 
 from AccessGrid.SharedAppClient import SharedAppClient
 from AccessGrid.Platform.Config import UserConfig
@@ -19,10 +25,10 @@
 except:
     pass
 from twisted.internet import reactor
-    
+
 class WebBrowser(wxPanel):
     """
-    WebBrowser is a basic ie-based web browser class
+    WebBrowser is a basic web browser class
     """
     def __init__(self, parent, id, log, frame = None):
         wxPanel.__init__(self, parent, id)
@@ -43,18 +49,21 @@
         # Pages whose completion we need to ignore.  This is because
         #  the events don't tell us which events are for the main page.
         self.ignoreComplete = []
-       
+
 
     def add_navigation_callback(self, listener):
+        self.log.debug("add_navigation_callback")
         self.navigation_callbacks.append(listener)
 
     def remove_navigation_callback(self, listener):
+        self.log.debug("remove_navigation_callback")
         self.navigation_callbacks.remove(listener)
 
     def add_button(self, name, func, sizer):
         b = wxButton(self, -1, name)
         EVT_BUTTON(self, b.GetId(), func)
         sizer.Add(b, 0, wxEXPAND)
+        return b
 
     def populate(self):
 
@@ -69,7 +78,8 @@
         self.back_button = self.add_button("Back", self.OnBack, bsizer)
         self.forward_button = self.add_button("Forward", self.OnForward,
                                               bsizer)
-        self.home_button = self.add_button("Home", self.OnHome, bsizer)
+        if sys.platform == Platform.WIN:
+            self.home_button = self.add_button("Home", self.OnHome, bsizer)
         self.stop_button = self.add_button("Stop", self.OnStop, bsizer)
         self.refresh_button = self.add_button("Refresh", self.OnRefresh,
                                               bsizer)
@@ -90,15 +100,26 @@
         # Now we can set up the browser widget
         #
 
-        self.ie = iewin.IEHtmlWindow(self, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
-        sizer.Add(self.ie, 1, wxEXPAND)
+        if sys.platform == Platform.WIN:
+            self.wxbrowser = iewin.IEHtmlWindow(self, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
+            sizer.Add(self.wxbrowser, 1, wxEXPAND)
+
+            # Hook up the event handlers for the IE window
+            iewin.EVT_BeforeNavigate2(self, -1, self.OnBeforeNavigate2)
+            iewin.EVT_NewWindow2(self, -1, self.OnNewWindow2)
+            iewin.EVT_DocumentComplete(self, -1, self.OnDocumentComplete)
+            # EVT_MSHTML_STATUSTEXTCHANGE(self, -1, self.OnStatusTextChange)
+            iewin.EVT_TitleChange(self, -1, self.OnTitleChange)
+        else:
+            self.wxbrowser = wxMozillaBrowser(self, -1, style = wxNO_FULL_REPAINT_ON_RESIZE)
+            sizer.Add(self.wxbrowser, 1, wxEXPAND)
 
-        # Hook up the event handlers for the IE window
-        iewin.EVT_BeforeNavigate2(self, -1, self.OnBeforeNavigate2)
-        iewin.EVT_NewWindow2(self, -1, self.OnNewWindow2)
-        iewin.EVT_DocumentComplete(self, -1, self.OnDocumentComplete)
-        # EVT_MSHTML_STATUSTEXTCHANGE(self, -1, self.OnStatusTextChange)
-        iewin.EVT_TitleChange(self, -1, self.OnTitleChange)
+            # Hook up the event handlers for the Mozilla window
+            EVT_MOZILLA_BEFORE_LOAD(self, -1, self.OnBeforeLoad)
+            EVT_MOZILLA_URL_CHANGED(self, -1, self.UpdateURL)
+            EVT_MOZILLA_LOAD_COMPLETE(self, -1, self.OnLoadComplete)
+            EVT_MOZILLA_STATUS_CHANGED(self, -1, self.UpdateStatus)
+            EVT_MOZILLA_STATE_CHANGED(self, -1, self.UpdateState)
 
         self.SetSizer(sizer)
         self.SetAutoLayout(1)
@@ -109,7 +130,7 @@
 
         if self.just_received_navigate:
             if url != self.docLoading:
-                message = "OnBeforeNav Skipping "+url+"already loading"+self.docLoading 
+                message = "OnBeforeNav Skipping "+url+"already loading"+self.docLoading
                 self.log.debug(message)
                 # If we get a navigation event while loading, we will ignore
                 #   the completion since it is from a popup or sub-page.
@@ -122,13 +143,32 @@
                 pass # Do nothing since we are already loading this url.
         else:
             # Go to a new url and also send it to the other Shared
-            #   Browser clients.  The Send is done in IBrowseCallback.
+            #   Browser clients.  The Send is done in IBrowsedCallback.
             message = "Before navigate "+url
             self.log.debug(message)
             self.just_received_navigate = 1
             self.docLoading = url
             map(lambda a: a(url), self.navigation_callbacks)
 
+    # Mozilla event handler
+    def OnBeforeLoad(self, event):
+        if not self.just_received_navigate:
+            # Go to a new url and also send it to the other Shared
+            #   Browser clients.  The Send is done in IBrowsedCallback.
+            url = event.GetURL()
+            message = "Before load "+url
+            self.log.debug(message)
+            self.just_received_navigate = 1
+            self.docLoading = url
+            map(lambda a: a(url), self.navigation_callbacks)
+
+    # Mozilla event handler
+    def UpdateURL(self, event):
+        url = event.GetNewURL()
+        self.log.debug("UpdateURL url=" + url)
+        self.back_button.Enable(event.CanGoBack())
+        self.forward_button.Enable(event.CanGoForward())
+
     def OnNewWindow2(self, event):
         message = "On new window: " +event.URL
         self.log.debug(message)
@@ -141,7 +181,7 @@
 
         # Check if we are finishing the main document or not.
         if event.URL not in self.ignoreComplete:
-            
+
             if event.URL == "about:blank" and self.docLoading != "about:blank":
                 # This case happens at startup.
                 self.log.debug("Ignoring DocComplete for first about:blank")
@@ -151,6 +191,8 @@
                 #   events to tell if they refer to a popup (and other sub-
                 #   pages) or a user clicking on a url.
                 self.log.debug("Finished loading.")
+                if self.location.FindString(self.current) == wxNOT_FOUND:
+                    self.location.Append(self.current)
                 self.just_received_navigate = 0
                 self.current = event.URL
                 self.location.SetValue(self.current)
@@ -161,6 +203,31 @@
             self.just_received_navigate = 0
             self.log.debug(message)
 
+    # Mozilla callback
+    def OnLoadComplete(self, event):
+        message = "OnLoadComplete: " + self.wxbrowser.GetURL()
+        self.log.debug(message)
+        self.current = self.wxbrowser.GetURL()
+
+        if self.frame:
+            self.frame.SetStatusText("")
+
+        if self.wxbrowser.GetURL() == "about:blank" and self.docLoading != "about:blank":
+            # This case happens at startup.
+            self.log.debug("Ignoring DocComplete for first about:blank")
+        else:
+            # Finished loading, allow user to click links again now.
+            #  Needed since there is not enough information in the
+            #   events to tell if they refer to a popup (and other sub-
+            #   pages) or a user clicking on a url.
+            self.log.debug("Finished loading.")
+            if self.location.FindString(self.current) == wxNOT_FOUND:
+                self.location.Append(self.current)
+            self.just_received_navigate = 0
+            self.location.SetValue(self.current)
+            if self.frame:
+                self.frame.SetTitle(self.title_base + ' -- ' + self.wxbrowser.GetTitle())
+
     def LocalEvent(self):
         # Reset just_received_navigate flag when url is triggered by combobox or buttons.
         # Else, the browser may not be able to receive incoming remote events
@@ -176,22 +243,39 @@
         if self.frame:
             self.frame.SetStatusText(event.URL)
 
+    def UpdateStatus(self, event):
+        if self.frame:
+            self.frame.SetStatusText(event.GetStatusText())
+
+    def UpdateState(self, event):
+        if self.frame:
+            if (event.GetState() & wxMOZILLA_STATE_START) or (event.GetState() & wxMOZILLA_STATE_TRANSFERRING):
+                self.frame.SetStatusText("Loading " + event.GetURL() + "...")
+            elif event.GetState() & wxMOZILLA_STATE_NEGOTIATING:
+                self.frame.SetStatusText("Contacting server...")
+            elif event.GetState() & wxMOZILLA_STATE_REDIRECTING:
+                self.frame.SetStatusText("Redirecting from " + event.GetURL())
+
+
     def OnBack(self, event):
-        self.ie.GoBack()
+        self.wxbrowser.GoBack()
 
     def OnForward(self, event):
-        self.ie.GoForward()
+        self.wxbrowser.GoForward()
 
     def OnStop(self, event):
-        self.ie.Stop()
+        self.wxbrowser.Stop()
 
     def OnHome(self, event):
-        self.ie.GoHome()
+        self.wxbrowser.GoHome()
 
     def OnRefresh(self, event):
         self.LocalEvent()
-        self.ie.Refresh(wxIEHTML_REFRESH_COMPLETELY)
-       
+        if sys.platform == Platform.WIN:
+            self.wxbrowser.Refresh(wxIEHTML_REFRESH_COMPLETELY)
+        else:
+            self.wxbrowser.Reload()
+
     def navigate(self, url):
         if self.just_received_navigate:
             self.log.debug("___cancelled NAVIGATE to "+url)
@@ -199,19 +283,28 @@
             self.log.debug("NAVIGATE to "+url)
             self.just_received_navigate = 1
             self.docLoading = url
-            self.ie.Navigate(url)
-         
+            if sys.platform == Platform.WIN:
+                self.wxbrowser.Navigate(url)
+            else:
+                wxCallAfter(self.wxbrowser.LoadURL, url)
+
     def OnLocationSelect(self, event):
         self.LocalEvent()
         url = self.location.GetStringSelection()
-        self.ie.Navigate(url)
+        if sys.platform == Platform.WIN:
+            self.wxbrowser.Navigate(url)
+        else:
+            self.wxbrowser.LoadURL(url)
 
     def OnLocationKey(self, event):
         if event.KeyCode() == WXK_RETURN:
             self.LocalEvent()
             URL = self.location.GetValue()
-            self.location.Append(URL)
-            self.ie.Navigate(URL)
+            print "URL %s" % URL
+            print "self.current = %s" % self.current
+            if self.current and self.location.FindString(self.current) == wxNOT_FOUND:
+                self.location.Append(self.current)
+            self.wxbrowser.LoadURL(URL)
         else:
             event.Skip()
 
@@ -237,13 +330,14 @@
 
     def __init__( self, appUrl, name):
         '''
-        Creates the shared application client, used for 
-        application service interaction, and opens a web browser 
-        for UI display. 
+        Creates the shared application client, used for
+        application service interaction, and opens a web browser
+        for UI display.
         '''
         wxApp.__init__(self, False)
+
         reactor.interleave(wxCallAfter)
-        # Create shared application client        
+        # Create shared application client
         self.sharedAppClient = SharedAppClient(name)
         self.log = self.sharedAppClient.InitLogging()
 
@@ -262,7 +356,9 @@
         self.sharedAppClient.RegisterEventCallback("browse", self.BrowseCallback )
 
         # Create Browser Window
-        self.frame = wxFrame(None, -1, "Browser")
+        self.frame = wxFrame(None, -1, "Browser", size=wxSize(800, 600))
+        if sys.platform != Platform.WIN:
+            self.frame.CreateStatusBar()
         self.browser = WebBrowser(self.frame, -1, self.log, self.frame)
 
         # Add callback for local browsing
@@ -270,7 +366,7 @@
 
         # Browse to the current url, if exists
         currentUrl = self.sharedAppClient.GetData("url")
-        
+
         if currentUrl and len(currentUrl) > 0:
             self.browser.navigate(currentUrl)
             try:
@@ -292,7 +388,7 @@
         self.sharedAppClient.SendEvent("browse", data)
         # Store the URL in the application service in the venue
         self.sharedAppClient.SetData("url", data)
-        
+
     def BrowseCallback(self, event):
         """
         Callback invoked when incoming browse events arrive.  Events
@@ -304,7 +400,7 @@
         url = event.data
         senderId = event.GetSenderId()
         if senderId == self.sharedAppClient.GetPublicId():
-            self.log.debug("Ignoring"+url+"from myself ")
+            self.log.debug("Ignoring "+ url +" from myself ")
         else:
             self.log.debug("Browse to "+ url)
             self.browser.navigate(url)
@@ -313,17 +409,17 @@
             self.sharedAppClient.SetParticipantStatus(url)
         except:
             self.log.exception("SharedBrowser:__init__: Failed to set participant status")
-            
-            
+
+
 class ArgumentManager:
     def __init__(self):
         self.arguments = {}
         self.arguments['applicationUrl'] = None
         self.arguments['debug'] = 0
-        
+
     def GetArguments(self):
         return self.arguments
-        
+
     def Usage(self):
         """
         How to use the program.
@@ -332,7 +428,7 @@
         print "    -a|--applicationURL : <url to application in venue>"
         print "    -d|--debug : <enables debug output>"
         print "    -h|--help : <print usage>"
-        
+
     def ProcessArgs(self):
         """
         Handle any arguments we're interested in.
@@ -343,7 +439,7 @@
         except getopt.GetoptError:
             self.Usage()
             sys.exit(2)
-            
+
         for o, a in opts:
             if o in ("-a", "--applicationURL"):
                 self.arguments["applicationUrl"] = a
@@ -352,17 +448,17 @@
             elif o in ("-h", "--help"):
                 self.Usage()
                 sys.exit(0)
-    
-        
+
+
 if __name__ == "__main__":
     app = WXGUIApplication()
     name = "SharedBrowser"
-    
+
     # Parse command line options
     am = ArgumentManager()
     am.ProcessArgs()
     aDict = am.GetArguments()
-    
+
     appUrl = aDict['applicationUrl']
     debugMode = aDict['debug']
 
@@ -372,24 +468,24 @@
         init_args.append("--debug")
 
     app.Initialize(name, args=init_args)
-          
+
     if not appUrl:
         am.Usage()
     else:
         wxInitAllImageHandlers()
         sb = SharedBrowser( appUrl, name)
         sb.MainLoop()
-        
+
     #
     # Stress test. Start a client and send events.
     #
     #import threading
     #import time
-    
+
     #browsers = []
     #threadList = []
     #urls = ["www.oea.se","www.aftonbladet.se", "www.passagen.se"]
-    
+
     #def StartBrowser():
     #    sb = SharedBrowser(appUrl, debugMode, logging)
     #    browsers.append(sb)
@@ -405,16 +501,16 @@
     #            # Store the URL in the application service in the venue
     #            sharedAppClient.SetData("url", url)
     #            time.sleep(0.07)
-            
+
     #s = SharedAppClient("SharedAppClientTest")
     #s.InitLogging()
     #clientProfileFile = os.path.join(GetUserConfigDir(), "profile")
     #clientProfile = ClientProfile(clientProfileFile)
     #s.Join(appUrl, clientProfile)
-    
+
     #thread = threading.Thread(target = SendEvents, args = [s])
     #thread.start()
 
     #StartBrowser()
-    
+
 
