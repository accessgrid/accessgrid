--- twisted/internet/_threadedselect.py.orig	2008-07-30 06:13:54.000000000 +1000
+++ twisted/internet/_threadedselect.py	2009-05-22 15:53:04.329397563 +1000
@@ -185,7 +185,7 @@
                     else:
                         raise
                 elif se.args[0] == EINTR:
-                    return
+                    continue
                 elif se.args[0] == EBADF:
                     self._preenDescriptorsInThread()
                 else:
