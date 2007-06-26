--- wxPython/config.py.orig	2006-04-04 14:00:19.000000000 +1000
+++ wxPython/config.py	2007-02-12 22:26:27.378782719 +1000
@@ -671,6 +671,7 @@
     CONTRIBS_INC = [ CONTRIBS_INC ]
 else:
     CONTRIBS_INC = []
+CONTRIBS_INC.append('/usr/X11/include')
 
 
 #----------------------------------------------------------------------
