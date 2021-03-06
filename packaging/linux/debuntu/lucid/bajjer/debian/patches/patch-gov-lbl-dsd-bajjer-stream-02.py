--- gov/lbl/dsd/bajjer/stream.py.orig	2009-04-24 13:42:13.000000000 +1000
+++ gov/lbl/dsd/bajjer/stream.py	2009-04-29 15:16:56.559321679 +1000
@@ -11,7 +11,7 @@
 ## Imports
 
 # std lib
-import logging, sha 
+import logging
 import logging.config
 
 # local
@@ -21,6 +21,21 @@
 from gov.lbl.dsd.bajjer import stanza
 from gov.lbl.dsd.bajjer import roster
 
+## Hash wrapper
+def NewShaHash(subject):
+    """
+    Compatibility function:
+    sha is deprecated in python2.6 in favout of hashlib.
+    hashlib is not available < python2.5
+    """
+    try:
+        import hashlib
+        return hashlib.sha(subject)
+    except:
+        import sha
+        return sha.new(subject)
+
+
 ## Logging
 
 
@@ -370,15 +385,15 @@
             zero_auth_error = "Empty 'sequence' in zero-k authentication reply"
             raise RuntimeError(zero_auth_error) 
 
-        x = sha.new(auth_info.password).hexdigest()+ reply.query_e.token_
-        x = sha.new(x).hexdigest()
+        x = NewShaHash(auth_info.password).hexdigest()+ reply.query_e.token_
+        x = NewShaHash(x).hexdigest()
         for i in xrange(int(reply.query_e.sequence_)):
-            x = sha.new(x).hexdigest()
+            x = NewShaHash(x).hexdigest()
         rq.query_e.hash_ = x
         self._jid.hash = x
 
     def _digestAuthRequest(self, auth_info, rq, reply): 
-        digest = sha.new(self._getStreamId() + auth_info.password).hexdigest()
+        digest = NewShaHash(self._getStreamId() + auth_info.password).hexdigest()
         rq.query_e.digest_ = digest
         self._jid.hash = digest
 
