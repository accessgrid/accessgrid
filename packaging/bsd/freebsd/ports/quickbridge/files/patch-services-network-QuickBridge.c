--- services/network/QuickBridge/QuickBridge.c.orig	Tue Aug  8 08:40:54 2006
+++ services/network/QuickBridge/QuickBridge.c	Wed Oct 17 22:17:22 2007
@@ -58,6 +58,10 @@
 #include <string.h>
 #endif
 
+#if defined(__FreeBSD__)
+#include <getopt.h>
+#endif
+
 #define MSGBUFSIZE 8192 
 #ifndef MAXHOSTNAMELEN
 #define MAXHOSTNAMELEN 64
