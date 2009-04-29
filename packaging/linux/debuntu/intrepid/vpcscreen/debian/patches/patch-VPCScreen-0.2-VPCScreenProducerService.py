--- VPCScreen-0.2/VPCScreenProducerService.py.orig	2006-10-10 13:53:37.000000000 +1000
+++ VPCScreen-0.2/VPCScreenProducerService.py	2007-08-09 16:59:51.445191032 +1000
@@ -54,7 +54,7 @@
         else:
             VPCScreen = "VPCScreenCapture"
 
-        self.executable = os.path.join(os.getcwd(),VPCScreen)
+        self.executable = os.path.join('/usr/bin',VPCScreen)
 
         self.sysConf = SystemConfig.instance()
 
@@ -66,12 +66,12 @@
         else:
             encs = VPCScreenProducerService.encodings[:3]
             
-        self.encoding = OptionSetParameter( "encoding", encs[0], encs )
+        self.encoding = OptionSetParameter( "encoding", encs[1], encs )
 	sizes = VPCScreenProducerService.sizes
 	self.size = OptionSetParameter( "size", sizes[0], sizes )
         self.bandwidth = RangeParameter( "bandwidth", 800, 0, 3072 )
-        self.framerate = RangeParameter( "framerate", 10, 1, 10 )
-        self.quality = RangeParameter( "quality", 75, 1, 100 )
+        self.framerate = RangeParameter( "framerate", 16, 1, 24 )
+        self.quality = RangeParameter( "quality", 85, 1, 100 )
         self.minimized = OptionSetParameter("minimized", 'OFF', ['ON', 'OFF'])
 
         self.configuration.append( self.encoding )
