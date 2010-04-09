--- examples/_common/setuporig.py.orig  2005-11-12 01:47:47.000000000 +1000
+++ examples/_common/setuporig.py       2006-06-28 10:15:50.870512750 +1000
@@ -127,10 +127,7 @@
                              extra_link_args=ldFlagsList,
                              libraries=libList)],
       package_dir = { "common" : "common" }, packages = ["common"],
-      ext_package = "common", scripts=["rtpbeacon.py",
-                                       "Win32BeaconService.py",
-                                       "beacon-install.py",
-                                       "beacon.ini"])
+      ext_package = "common", scripts=["rtpbeacon.py"])
     
 print 'Build finished at: ', strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
 print 'Completed in', time() - begin_time, 'seconds'
