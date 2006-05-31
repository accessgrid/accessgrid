--- setuporig.py.orig	Sat Nov 12 01:47:47 2005
+++ setuporig.py	Tue May 23 12:19:40 2006
@@ -96,6 +96,15 @@
 swigList = [ ("common.i", "common_wrap.cpp") ]
 pyModList = [ "common", "scheduler" ]
 
+# Make the higher level stuff first
+here = os.getcwd()
+ulpath = os.path.join('..', '..')
+os.chdir(ulpath)
+cmd = 'sh dobuild.sh'
+print "cmd = ", cmd
+os.system(cmd)
+os.chdir(here)
+
 # Distutils doesn't currently work with recent 1.3.x
 # versions of swig.
 def run_swig(swigList):
@@ -127,10 +136,7 @@
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
