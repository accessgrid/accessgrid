--- gov/lbl/dsd/bajjer/stanza.py.orig	2006-01-14 08:58:43.000000000 +1000
+++ gov/lbl/dsd/bajjer/stanza.py	2006-02-14 15:26:53.000000000 +1000
@@ -180,7 +180,9 @@
         """
         Debugging hook; get XML contents as a string.
         """
-        return tostring(self.elt)
+        xmlstr = tostring(self.elt).replace(":ns0","")
+        xmlstr = xmlstr.replace("ns0:","")
+        return xmlstr
 
     def getText(self):
         """
