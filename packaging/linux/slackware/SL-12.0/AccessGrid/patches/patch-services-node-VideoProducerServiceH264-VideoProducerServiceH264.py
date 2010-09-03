--- services/node/VideoProducerServiceH264/VideoProducerServiceH264.py.orig	2008-03-18 14:40:54.000000000 +1000
+++ services/node/VideoProducerServiceH264/VideoProducerServiceH264.py	2008-03-18 14:55:10.735560000 +1000
@@ -60,7 +60,7 @@
 class VideoProducerServiceH264( AGService ):
 
     encodings = [ "mpeg4","h264","h261as" ]
-    standards = [ "NTSC", "PAL" ]
+    standards = [ "NTSC", "PAL", "auto" ]
     inputsizes = [ "Small", "Normal", "Large" ]
 
     def __init__( self ):
@@ -106,7 +106,7 @@
         if IsWindows(): 
             standard = "PAL"
         else:
-            standard = "NTSC"
+            standard = "auto"
         self.standard = OptionSetParameter( "Standard", standard, VideoProducerServiceH264.standards )
         self.bandwidth = RangeParameter( "Bandwidth", 2000, 0, 3072 )
         self.framerate = RangeParameter( "Frame Rate", 24, 1, 30 )
