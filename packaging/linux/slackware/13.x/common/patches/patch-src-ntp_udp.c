--- src/net_udp.c.orig  2003-12-11 02:17:46.000000000 +1000
+++ src/net_udp.c       2006-06-28 09:23:00.216359250 +1000
@@ -44,7 +44,9 @@
 #include "debug.h"
 #include "memory.h"
 #include "inet_pton.h"
+#ifdef NEED_INET_NTOP
 #include "inet_ntop.h"
+#endif
 #include "vsnprintf.h"
 #include "net_udp.h"
 

