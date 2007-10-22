--- services/node/VideoService/VideoService.build.py.orig	2007-04-29 22:25:07.599629000 +1000
+++ services/node/VideoService/VideoService.build.py	2007-04-29 22:22:16.906962000 +1000
@@ -45,6 +45,7 @@
         needBuild = 1
         break
 
+needBuild = 0
 if needBuild:
     # Build vic
     if executableToBuild == "openmash":
