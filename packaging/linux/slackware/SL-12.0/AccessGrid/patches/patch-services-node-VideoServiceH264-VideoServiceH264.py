--- services/node/VideoServiceH264/VideoServiceH264.py.orig	2008-03-18 14:57:08.000000000 +1000
+++ services/node/VideoServiceH264/VideoServiceH264.py	2008-03-18 14:57:31.279761000 +1000
@@ -69,7 +69,7 @@
 class VideoServiceH264( AGService ):
 
     encodings = [ "mpeg4","h264","h261as" ]
-    standards = [ "NTSC", "PAL" ]
+    standards = [ "NTSC", "PAL", "auto" ]
     inputsizes = [ "Small", "Normal", "Large" ]
     onOffOptions = [ "On", "Off" ]
     tileOptions = [ '1', '2', '3', '4', '5', '6', '7', '8', '9', '10' ]
@@ -129,7 +129,7 @@
         if IsWindows(): 
             standard = "PAL"
         else:
-            standard = "NTSC"
+            standard = "auto"
         self.standard = OptionSetParameter( "Standard", standard, VideoServiceH264.standards )
         self.tiles = OptionSetParameter( "Thumbnail Columns", "4", VideoServiceH264.tileOptions )
         self.bandwidth = RangeParameter( "Bandwidth", 2048, 0, 4096 )
