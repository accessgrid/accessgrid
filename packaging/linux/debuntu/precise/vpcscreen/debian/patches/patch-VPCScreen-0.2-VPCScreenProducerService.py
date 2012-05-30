--- x/VPCScreenProducerService.py	2011-04-27 19:56:58.000000000 +1000
+++ y/VPCScreenProducerService.py	2011-05-11 09:13:17.753258391 +1000
@@ -57,7 +57,7 @@
         else:
             VPCScreen = "VPCScreenCapture"
 
-        self.executable = os.path.join(os.getcwd(),VPCScreen)
+        self.executable = os.path.join('/usr/bin', VPCScreen)
 
         self.sysConf = SystemConfig.instance()
 
@@ -73,8 +73,8 @@
 	sizes = VPCScreenProducerService.sizes
 	self.size = OptionSetParameter( "size", sizes[0], sizes )
         self.bandwidth = RangeParameter( "bandwidth", 800, 0, 3072 )
-        self.framerate = RangeParameter( "framerate", 10, 1, 10 )
-        self.quality = RangeParameter( "quality", 75, 1, 100 )
+        self.framerate = RangeParameter( "framerate", 16, 1, 24 )
+        self.quality = RangeParameter( "quality", 85, 1, 100 )
         self.minimized = OptionSetParameter("minimized", 'OFF', ['ON', 'OFF'])
 
         self.configuration.append( self.encoding )
