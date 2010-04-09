--- services/node/AudioService/AudioService.build.py.orig	2006-05-10 11:35:39.000000000 +1000
+++ services/node/AudioService/AudioService.build.py	2007-04-29 22:21:02.490135000 +1000
@@ -43,6 +43,7 @@
         needBuild = 1
         break
 
+needBuild = 0
 # Build rat if necessary
 if needBuild:
     print "source dist = ", SOURCE, DEST
