--- services/node/AudioService/AudioService.py.orig	2006-08-02 08:01:32.000000000 +1000
+++ services/node/AudioService/AudioService.py	2007-04-29 23:29:33.143761000 +1000
@@ -66,7 +66,7 @@
             ratui = "rat-ui"
             ratkill = "rat-kill"
 
-        self.executable = os.path.join(os.getcwd(), rat)
+        self.executable = os.path.join("/usr/bin/", rat)
         self.rat_media = os.path.join(os.getcwd(), ratmedia) 
         self.rat_ui = os.path.join(os.getcwd(), ratui)
         self.rat_kill = os.path.join(os.getcwd(), ratkill)
