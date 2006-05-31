--- SWIG/_asn1.i.orig	Fri Jan 13 13:55:57 2006
+++ SWIG/_asn1.i	Wed May 10 12:37:11 2006
@@ -36,8 +36,8 @@
 %name(asn1_utctime_new) extern ASN1_UTCTIME *ASN1_UTCTIME_new( void );
 %name(asn1_utctime_free) extern void ASN1_UTCTIME_free(ASN1_UTCTIME *);
 %name(asn1_utctime_check) extern int ASN1_UTCTIME_check(ASN1_UTCTIME *);
-%name(asn1_utctime_set) extern ASN1_UTCTIME *ASN1_UTCTIME_set(ASN1_UTCTIME *, long);
-%name(asn1_utctime_set_string) extern int ASN1_UTCTIME_set_string(ASN1_UTCTIME *, CONST098 char *);
+/* %name(asn1_utctime_set) extern ASN1_UTCTIME *ASN1_UTCTIME_set(ASN1_UTCTIME *, long); */
+/* %name(asn1_utctime_set_string) extern int ASN1_UTCTIME_set_string(ASN1_UTCTIME *, CONST098 char *); */
 %name(asn1_utctime_print) extern int ASN1_UTCTIME_print(BIO *, ASN1_UTCTIME *);
 
 %name(asn1_integer_new) extern ASN1_INTEGER *ASN1_INTEGER_new( void );
