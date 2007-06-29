--- mDNSCore/mDNSEmbeddedAPI.h.orig	2006-08-29 16:24:22.000000000 +1000
+++ mDNSCore/mDNSEmbeddedAPI.h	2007-06-12 16:32:16.723351369 +1000
@@ -1155,18 +1155,9 @@
 //   Macro Name __LP64__ Value 1
 // A quick Google search for "defined(__LP64__)" OR "#ifdef __LP64__" gives 2590 hits and
 // a search for "#if __LP64__" gives only 12, so I think we'll go with the majority and use defined()
-#if defined(_ILP64) || defined(__ILP64__)
-typedef   signed int32 mDNSs32;
-typedef unsigned int32 mDNSu32;
-#elif defined(_LP64) || defined(__LP64__)
-typedef   signed int   mDNSs32;
-typedef unsigned int   mDNSu32;
-#else
-typedef   signed long  mDNSs32;
-typedef unsigned long  mDNSu32;
-//typedef   signed int mDNSs32;
-//typedef unsigned int mDNSu32;
-#endif
+#include <sys/types.h>
+typedef int32_t    mDNSs32;
+typedef u_int32_t  mDNSu32;
 
 // To enforce useful type checking, we make mDNSInterfaceID be a pointer to a dummy struct
 // This way, mDNSInterfaceIDs can be assigned, and compared with each other, but not with other types
