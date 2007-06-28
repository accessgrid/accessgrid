--- services/node/VideoConsumerService/VideoConsumerService.py.orig	2007-05-04 14:33:54.000000000 +1000
+++ services/node/VideoConsumerService/VideoConsumerService.py	2007-05-04 14:34:17.157641000 +1000
@@ -35,7 +35,7 @@
         else:
             vic = "vic"
 
-        self.executable = os.path.join(os.getcwd(),vic)
+        self.executable = os.path.join("/usr/bin/", vic)
         self.sysConf = SystemConfig.instance()
 
         self.profile = None
