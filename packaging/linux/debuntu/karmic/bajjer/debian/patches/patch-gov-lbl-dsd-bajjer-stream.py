--- gov/lbl/dsd/bajjer/stream.py.orig	2007-01-18 07:23:13.000000000 +1000
+++ gov/lbl/dsd/bajjer/stream.py	2007-11-29 21:52:33.576478000 +1000
@@ -120,6 +120,7 @@
         self._conn.close()
         self._open = False
         self._cbthread.unRegister(self._conn) 
+        self._conn = None
     
     def setHandler(self, callback_func, expected, args_list=None):
         """
