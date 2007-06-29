--- services/node/VideoProducerService/VideoProducerService.py.orig	2007-06-16 07:50:44.000000000 +1000
+++ services/node/VideoProducerService/VideoProducerService.py	2007-06-27 14:14:20.500552000 +1000
@@ -72,7 +72,7 @@
         else:
             vic = "vic"
 
-        self.executable = os.path.join(os.getcwd(),vic)
+        self.executable = os.path.join("/usr/bin/", vic)
 
         self.sysConf = SystemConfig.instance()
 
