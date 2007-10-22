--- setuporig.py.orig	Sat Nov 12 01:47:47 2005
+++ setuporig.py	Thu Oct 18 16:20:32 2007
@@ -1,6 +1,7 @@
 """
 Common module
 """ 
+from distutils.command.build import build
 from distutils.core import setup, Extension
 from distutils.spawn import spawn
 from distutils.sysconfig import get_python_inc
@@ -20,6 +21,7 @@
 RUN_EPYDOC    = 0
 RUN_EPYDOCIFY = 1
 SWIG_ARGS = [ "-python", "-outdir", "common", "-c++", "-new_repr", 
+              "-cpperraswarn",
               "-I%s" % get_python_inc(plat_specific=1),
               "-I%s" % os.path.join("..", "..", "src")]
 SRC = os.path.join('..','..')
@@ -96,6 +98,19 @@
 swigList = [ ("common.i", "common_wrap.cpp") ]
 pyModList = [ "common", "scheduler" ]
 
+class my_build(build):
+    def run(self):
+        """Specialized Python source builder."""
+        # Make the higher level stuff first
+        here = os.getcwd()
+        ulpath = os.path.join('..', '..')
+        os.chdir(ulpath)
+        cmd = 'sh dobuild.sh'
+        print "cmd = ", cmd
+        os.system(cmd)
+        os.chdir(here)
+        build.run(self)
+
 # Distutils doesn't currently work with recent 1.3.x
 # versions of swig.
 def run_swig(swigList):
@@ -116,7 +131,8 @@
     check_swig_version()
     run_swig(swigList)
 
-setup(name="common", version="1.2",
+setup(cmdclass={'build': my_build},
+      name="common", version="1.2",
       description="Python UCL Common Library wrapper",
       author="Ivan R. Judson", author_email="judson@mcs.anl.gov",
       url="http://www.mcs.anl.gov/fl/research/common",
@@ -127,10 +143,7 @@
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
