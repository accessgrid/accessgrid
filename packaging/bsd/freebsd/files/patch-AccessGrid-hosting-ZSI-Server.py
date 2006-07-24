--- AccessGrid/hosting/ZSI/Server.py.socket_error	2005-10-20 05:34:18.000000000 +1000
+++ AccessGrid/hosting/ZSI/Server.py	2006-06-26 18:06:26.000000000 +1000
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
                 
