--- services/node/VideoConsumerService/VideoConsumerService.build.py.orig	2006-05-10 11:35:39.000000000 +1000
+++ services/node/VideoConsumerService/VideoConsumerService.build.py	2007-04-29 22:26:47.025376000 +1000
@@ -44,6 +44,7 @@
         needBuild = 1
         break
 
+needBuild = 0
 if needBuild:
     # Build vic
     if executableToBuild == "openmash":
