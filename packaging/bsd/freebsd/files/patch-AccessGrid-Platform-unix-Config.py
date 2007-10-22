--- AccessGrid/Platform/unix/Config.py.orig	Fri Oct 19 13:42:12 2007
+++ AccessGrid/Platform/unix/Config.py	Fri Oct 19 13:42:51 2007
@@ -103,7 +103,7 @@
             self.docDir = os.path.join(self.GetInstallDir(), "doc")
         else:
             self.docDir = os.path.join(self.GetInstallDir(), "share", "doc",
-                                       "AccessGrid-" + str(GetVersion()))
+                                       "accessgrid-" + str(GetVersion()))
     #    # Check dir and make it if needed.
     #    if self.initIfNeeded:
     #        if self.docDir is not None and \
