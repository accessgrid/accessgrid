--- services/node/VideoProducerService/VideoProducerService.build.py.orig	2006-05-12 10:49:05.000000000 +1000
+++ services/node/VideoProducerService/VideoProducerService.build.py	2007-04-29 22:23:46.303104000 +1000
@@ -45,6 +45,7 @@
         needBuild = 1
         break
 
+needBuild = 0
 if needBuild:
     # Build vic
     if executableToBuild == "openmash":
