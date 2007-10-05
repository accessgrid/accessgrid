--- AccessGrid/hosting/ZSI/Server.py.orig	2007-04-27 01:35:09.000000000 +1000
+++ AccessGrid/hosting/ZSI/Server.py	2007-06-27 14:15:54.276398000 +1000
@@ -21,7 +21,7 @@
 
 from AccessGrid import Log
 log = Log.GetLogger(Log.Hosting)
-import select
+import select, socket
 
 def GetSOAPContext():
     return None
@@ -67,6 +67,10 @@
                 r,w,e = select.select([self._server.socket], [], [], pause)
                 if r:
                     self._server.handle_request()
+            except socket.error, ex:
+                if ex[0] == 4: # interrupted system call
+                    continue
+                log.exception("Exception in SOAP server main loop")
             except:
                 log.exception("Exception in SOAP server main loop")
                 
