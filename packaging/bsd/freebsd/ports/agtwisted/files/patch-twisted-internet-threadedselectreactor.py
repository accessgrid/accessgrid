--- twisted/internet/_threadedselect.py.orig	2005-10-08 11:37:50.000000000 +1000
+++ twisted/internet/_threadedselect.py	2006-08-10 09:36:42.000000000 +1000
@@ -186,7 +186,7 @@
                     else:
                         raise
                 elif se.args[0] == EINTR:
-                    return
+                    continue
                 elif se.args[0] == EBADF:
                     self._preenDescriptorsInThread()
                 else:
