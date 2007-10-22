--- ZSI/client.py.orig	2007-05-28 11:17:55.000000000 +1000
+++ ZSI/client.py	2007-06-04 15:15:29.867382000 +1000
@@ -10,7 +10,7 @@
 from ZSI.TC import AnyElement, AnyType, String, TypeCode, _get_global_element_declaration,\
     _get_type_definition
 from ZSI.TCcompound import Struct
-import base64, httplib, Cookie, types, time, urlparse
+import base64, httplib, Cookie, socket, types, time, urlparse
 from ZSI.address import Address
 from ZSI.wstools.logging import getLogger as _GetLogger
 _b64_encode = base64.encodestring
@@ -346,7 +346,10 @@
         if self.data: return self.data
         trace = self.trace
         while 1:
-            response = self.h.getresponse()
+            try:
+                response = self.h.getresponse()
+            except:
+                response = self.h.getresponse()
             self.reply_code, self.reply_msg, self.reply_headers, self.data = \
                 response.status, response.reason, response.msg, response.read()
             if trace:
@@ -375,6 +378,7 @@
             # Horrible internals hack to patch things up.
             self.h._HTTPConnection__state = httplib._CS_REQ_SENT
             self.h._HTTPConnection__response = None
+        self.h = None
         return self.data
 
     def IsSOAP(self):
