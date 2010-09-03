--- services/node/VideoServiceH264/VideoServiceH264.build.py.orig	2008-06-27 10:23:03.000000000 +1000
+++ services/node/VideoServiceH264/VideoServiceH264.build.py	2008-06-27 10:47:10.028186000 +1000
@@ -45,6 +45,7 @@
         needBuild = 1
         break
 
+needBuild = 0
 if needBuild:
     # Build vic
     if executableToBuild == "openmash":
