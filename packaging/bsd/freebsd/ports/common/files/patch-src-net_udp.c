--- ../../src/net_udp.c.orig	Thu Dec 11 02:17:46 2003
+++ ../../src/net_udp.c	Sat Jun 17 15:24:57 2006
@@ -44,7 +44,9 @@
 #include "debug.h"
 #include "memory.h"
 #include "inet_pton.h"
+#if 0
 #include "inet_ntop.h"
+#endif
 #include "vsnprintf.h"
 #include "net_udp.h"
 
