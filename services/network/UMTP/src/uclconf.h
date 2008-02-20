/* src/uclconf.h.  Generated automatically by configure.  */
/* src/config.h.in.  Generated automatically from ../configure.in by autoheader.  */

/* Define if type char is unsigned and you are not using gcc.  */
#ifndef __CHAR_UNSIGNED__
/* #undef __CHAR_UNSIGNED__ */
#endif

/* Define to empty if the keyword does not work.  */
/* #undef const */

/* Define if you have <sys/wait.h> that is POSIX.1 compatible.  */
#define HAVE_SYS_WAIT_H 1

/* Define to `unsigned' if <sys/types.h> doesn't define.  */
/* #undef size_t */

/* Define if you have the ANSI C header files.  */
#define STDC_HEADERS 1

/* Define if you can safely include both <sys/time.h> and <time.h>.  */
#define TIME_WITH_SYS_TIME 1

/* Define if your processor stores words with the most significant
   byte first (like Motorola and SPARC, unlike Intel and VAX).  */
/* #undef WORDS_BIGENDIAN */

/*
 * Define this if you have a /dev/urandom which can supply good random numbers.
 */
#define HAVE_DEV_URANDOM 1

/*
 * Define this if you want IPv6 support.
 */
/* #undef HAVE_IPv6 */

/*
 * V6 structures that host may or may not be present.
 */
#define HAVE_ST_ADDRINFO 1
#define HAVE_GETIPNODEBYNAME 1
/* #undef HAVE_SIN6_LEN */

/*
 * Define these if your C library is missing some functions...
 */
/* #undef NEED_VSNPRINTF */
/* #undef NEED_INET_PTON */
/* #undef NEED_INET_NTOP */

/*
 * If you don't have these types in <inttypes.h>, #define these to be
 * the types you do have.
 */
/* #undef int8_t */
/* #undef int16_t */
/* #undef int32_t */
/* #undef int64_t */
/* #undef uint8_t */
/* #undef uint16_t */
/* #undef uint32_t */

/*
 * Debugging:
 * DEBUG: general debugging
 * DEBUG_MEM: debug memory allocation
 */
/* #undef DEBUG */
/* #undef DEBUG_MEM */

/* Define if you have the vsnprintf function.  */
#define HAVE_VSNPRINTF 1

/* Define if you have the <inttypes.h> header file.  */
#define HAVE_INTTYPES_H 1

/* Define if you have the <netinet6/in6.h> header file.  */
/* #undef HAVE_NETINET6_IN6_H */

/* Define if you have the <stdint.h> header file.  */
#define HAVE_STDINT_H 1

/* Define if you have the <stropts.h> header file.  */
/* #define HAVE_STROPTS_H 1 */

/* Define if you have the <sys/filio.h> header file.  */
/* #undef HAVE_SYS_FILIO_H */

/* Define if you have the <sys/time.h> header file.  */
#define HAVE_SYS_TIME_H 1

#ifndef WORDS_BIGENDIAN
#define WORDS_SMALLENDIAN
#endif


