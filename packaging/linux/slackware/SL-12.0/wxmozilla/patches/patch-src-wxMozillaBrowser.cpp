--- src/wxMozillaBrowser.cpp.orig	2006-12-18 22:20:33.000000000 +1000
+++ src/wxMozillaBrowser.cpp	2007-04-01 20:02:58.896202228 +1000
@@ -300,7 +300,7 @@
         NS_ShutdownXPCOM(nsnull);
         XPCOMGlueShutdown();
 #else
-        #if WXMOZ_FIREFOX_VERSION >= 15 || WXMOZ_SEAMONKEY_VERSION >= 10
+        #if WXMOZ_FIREFOX_VERSION >= 15 || WXMOZ_SEAMONKEY_VERSION >= 10 || WXMOZ_XUL_VERSION >= 18
         NS_ShutdownXPCOM(nsnull);
         #else
 		NS_TermEmbedding();
@@ -357,7 +357,7 @@
         //nsCOMPtr<nsIServiceManager> servMan;
         NS_InitXPCOM2(nsnull, greDir, nsnull); 
 #else
-        #if WXMOZ_FIREFOX_VERSION >= 15 || WXMOZ_SEAMONKEY_VERSION >= 10
+        #if WXMOZ_FIREFOX_VERSION >= 15 || WXMOZ_SEAMONKEY_VERSION >= 10 || WXMOZ_XUL_VERSION >= 18
         rv = NS_InitXPCOM3(nsnull, greDir, nsnull, nsnull, nsnull);
         #else
         rv = NS_InitEmbedding(greDir, nsnull);
