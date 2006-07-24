--- AccessGrid/hosting/ZSI/Server.py.orig	Thu Oct 20 05:34:18 2005
+++ AccessGrid/hosting/ZSI/Server.py	Mon Jul 24 12:28:13 2006
@@ -21,7 +21,7 @@
 
 from AccessGrid import Log
 log = Log.GetLogger(Log.Hosting)
-import select
+import select, socket
 
 def GetSOAPContext():
     return None
@@ -66,6 +66,10 @@
                 r,w,e = select.select([self._server.socket], [], [], pause)
                 if r:
                     self._server.handle_request()
+            except socket.error, ex:
+                if ex[0] == 4: # interrupted system call
+                    continue
+                log.exception("Exception in SOAP server main loop")
             except:
                 log.exception("Exception in SOAP server main loop")
                 
