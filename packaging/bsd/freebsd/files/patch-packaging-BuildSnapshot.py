--- packaging/BuildSnapshot.py.orig	Mon May 29 09:06:12 2006
+++ packaging/BuildSnapshot.py	Wed May 31 12:34:35 2006
@@ -317,27 +317,6 @@
 os.system(cmd)
 
 file_list = os.listdir(SourceDir)
-
-if bdir is not None:
-    pkg_script = "BuildPackage.py"
-    NextDir = os.path.join(StartDir, bdir)
-    if os.path.exists(NextDir):
-        os.chdir(NextDir)
-        cmd = "%s %s --verbose -s %s -b %s -d %s -p %s -m %s -v %s" % (sys.executable,
-                                                                 pkg_script,
-                                                                 SourceDir,
-                                                                 BuildDir,
-                                                                 DestDir,
-                                                                 options.pyver,
-                                                                 metainfo.replace(' ', '_'),
-                                                                 version)
-        if sys.platform == 'linux2' or sys.platform == 'freebsd5' or sys.platform == 'freebsd6':
-            cmd += ' --dist %s' % (options.dist,)
-        print "cmd = ", cmd
-        os.system(cmd)
-    else:
-        print "No directory (%s) found." % NextDir
-
 nfl = os.listdir(SourceDir)
 for f in file_list:
     nfl.remove(f)
@@ -346,4 +325,6 @@
     pkg_file = nfl[0]
 else:
     pkg_file = None
+
+print "END OF BUILDSNAPSHOT"
 
