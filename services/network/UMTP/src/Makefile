# Generated automatically from Makefile.in by configure.

# Makefile for the common code library project. 
# This probably requires GNU make.
#

DEFS   = -DHAVE_CONFIG_H
CFLAGS = -g -O2 -W -Wall -Wwrite-strings -Wbad-function-cast -Wmissing-prototypes -Wcast-qual -Wmissing-declarations $(DEFS)
LIBS   = 
CC     = gcc
AR     = ar
RANLIB = ranlib
HOST   = i686-apple-darwin8.9.1
TARGET = libuclmmbase.a

exec_prefix=${prefix}

OBJS = crypt_random.o debug.o md5.o memory.o net_udp.o qfDES.o util.o hmac.o  \
       base64.o ntp.o rtp.o drand48.o mbus_parser.o mbus_config.o mbus_addr.o \
       mbus.o btree.o asarray.o  rijndael-alg-fst.o \
       rijndael-api-fst.o sap.o sdp.o pktbuf.o rtpdump.o umtp.o ring_buf.o

SRCS = $(OBJS:%.o=%.c)

all: version.h $(TARGET) 

$(TARGET): $(OBJS)
	$(AR) r $(TARGET) $(OBJS)
	$(RANLIB) $(TARGET)

version.h: ../VERSION
	sed -e 's/.*/#define CCL_VERSION "v&"/' $? > version.h

.c.o:
	$(CC) $(CFLAGS) $(INC) -c $<

clean:
	-rm -f $(OBJS) version.h $(TARGET) tags 

distclean:	clean
	-rm -f Makefile config.status config.cache uclconf.h

etags:
	etags *.[ch]

ctags:
	ctags *.[ch]

release:
	cvs tag release-`cat ../VERSION | sed "s/\./-/g"`

depend: $(SRCS)
	makedepend $(DEFS) $(INC) $(SRCS)

