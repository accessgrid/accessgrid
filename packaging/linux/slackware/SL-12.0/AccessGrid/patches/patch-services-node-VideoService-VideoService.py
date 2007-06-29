--- services/node/VideoService/VideoService.py.orig	2007-06-19 11:55:28.000000000 +1000
+++ services/node/VideoService/VideoService.py	2007-06-27 14:11:20.138563000 +1000
@@ -91,7 +91,7 @@
         else:
             vic = "vic"
 
-        self.executable = os.path.join(os.getcwd(),vic)
+        self.executable = os.path.join("/usr/bin/", vic)
 
         self.sysConf = SystemConfig.instance()
 
