--- net/crypt.cpp.orig	Wed Aug  8 21:26:27 2007
+++ net/crypt.cpp	Wed Oct 17 13:07:19 2007
@@ -41,11 +41,7 @@
 /*XXX*/
 #define PROTOTYPES 1 
 #include "global.h"
-#ifndef __FreeBSD__
 #include "md5.h"
-#else
-#include <openssl/md5.h> //SV-XXX: FreeBSD
-#endif
 
 Crypt::Crypt() : badpktlen_(0), badpbit_(0)
 {
@@ -75,15 +71,9 @@
 	MD5_CTX context;
 	u_char hash[16];
 
-#ifndef __FreeBSD__
 	MD5Init(&context);
 	MD5Update(&context, (u_char*)key, strlen(key));
 	MD5Final((u_char *)hash, &context);
-#else
-	MD5_Init(&context); //SV-XXX: FreeBSD.
-	MD5_Update(&context, (u_char*)key, strlen(key)); //SV-XXX: FreeBSD. 
-	MD5_Final((u_char *)hash, &context); //SV-XXX: FreeBSD.
-#endif
 
 	return (install_key(hash));
 }
