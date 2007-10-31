--- sharedapps/SharedBrowser/SharedBrowser.py.orig	2007-10-05 23:57:30.000000000 +1000
+++ sharedapps/SharedBrowser/SharedBrowser.py	2007-10-11 12:41:17.848583000 +1000
@@ -21,7 +21,7 @@
 if sys.platform == Platform.WIN:
     import wx.lib.iewin as iewin
 else:
-    from wxPython.mozilla import *
+    from wx.mozilla import *
 
 
 from AccessGrid.SharedAppClient import SharedAppClient
@@ -116,15 +116,15 @@
             # wx.EVT_MSHTML_STATUSTEXTCHANGE(self, -1, self.OnStatusTextChange)
             iewin.EVT_TitleChange(self, -1, self.OnTitleChange)
         else:
-            self.wxbrowser = wxMozillaBrowser(self, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
+            self.wxbrowser = MozillaBrowser(self, -1, style = wx.NO_FULL_REPAINT_ON_RESIZE)
             sizer.Add(self.wxbrowser, 1, wx.EXPAND)
 
             # Hook up the event handlers for the Mozilla window
-            wx.EVT_MOZILLA_BEFORE_LOAD(self, -1, self.OnBeforeLoad)
-            wx.EVT_MOZILLA_URL_CHANGED(self, -1, self.UpdateURL)
-            wx.EVT_MOZILLA_LOAD_COMPLETE(self, -1, self.OnLoadComplete)
-            wx.EVT_MOZILLA_STATUS_CHANGED(self, -1, self.UpdateStatus)
-            wx.EVT_MOZILLA_STATE_CHANGED(self, -1, self.UpdateState)
+            EVT_MOZILLA_BEFORE_LOAD(self, -1, self.OnBeforeLoad)
+            EVT_MOZILLA_URL_CHANGED(self, -1, self.UpdateURL)
+            EVT_MOZILLA_LOAD_COMPLETE(self, -1, self.OnLoadComplete)
+            EVT_MOZILLA_STATUS_CHANGED(self, -1, self.UpdateStatus)
+            EVT_MOZILLA_STATE_CHANGED(self, -1, self.UpdateState)
 
         self.SetSizer(sizer)
         self.SetAutoLayout(1)
@@ -254,11 +254,11 @@
 
     def UpdateState(self, event):
         if self.frame:
-            if (event.GetState() & wxMOZILLA_STATE_START) or (event.GetState() & wxMOZILLA_STATE_TRANSFERRING):
+            if (event.GetState() & MOZILLA_STATE_START) or (event.GetState() & MOZILLA_STATE_TRANSFERRING):
                 self.frame.SetStatusText("Loading " + event.GetURL() + "...")
-            elif event.GetState() & wxMOZILLA_STATE_NEGOTIATING:
+            elif event.GetState() & MOZILLA_STATE_NEGOTIATING:
                 self.frame.SetStatusText("Contacting server...")
-            elif event.GetState() & wxMOZILLA_STATE_REDIRECTING:
+            elif event.GetState() & MOZILLA_STATE_REDIRECTING:
                 self.frame.SetStatusText("Redirecting from " + event.GetURL())
 
 
@@ -291,7 +291,7 @@
             if sys.platform == Platform.WIN:
                 self.wxbrowser.Navigate(url)
             else:
-                wx.CallAfter(self.wxbrowser.LoadUrl, url)
+                wx.CallAfter(self.wxbrowser.LoadURL, url)
 
     def OnLocationSelect(self, event):
         self.LocalEvent()
@@ -299,7 +299,7 @@
         if sys.platform == Platform.WIN:
             self.wxbrowser.Navigate(url)
         else:
-            self.wxbrowser.LoadUrl(url)
+            self.wxbrowser.LoadURL(url)
 
     def OnLocationKey(self, event):
         if event.GetKeyCode() == wx.WXK_RETURN:
@@ -307,7 +307,7 @@
             URL = self.location.GetValue()
             if self.current and self.location.FindString(self.current) == wx.NOT_FOUND:
                 self.location.Append(self.current)
-            self.wxbrowser.LoadUrl(URL)
+            self.wxbrowser.LoadURL(URL)
         else:
             event.Skip()
 
