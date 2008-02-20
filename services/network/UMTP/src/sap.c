/*
 * FILE:     sap.c
 * AUTHOR:   Ivan R. Judson  <judson@mcs.anl.gov>
 *
 * The routines in this file implement parsing and construction of data
 * that's compliant with the Session Announcement Protocol, as specified 
 * in RFC2974.
 *
 * $Revision: 1.1.1.1 $ 
 * $Date: 2006/06/30 04:39:44 $
 * 
 * Copyright (c) 2002 Argonne National Laboratory/University of Chicago
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, is permitted provided that the following conditions 
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *      This product includes software developed by the Mathematics and 
 *      Computer Science Division of Argonne National Laboratory.
 * 4. Neither the name of the University nor of the Department may be used
 *    to endorse or promote products derived from this software without
 *    specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */

#include "config_unix.h"
#include "config_win32.h"
#include "debug.h"
#include "memory.h"
#include "net_udp.h"
#include "hmac.h"
#include "qfDES.h"
#include "base64.h"
#include "gettimeofday.h"
#include "vsnprintf.h"
#include "sap.h"

/*
 * The "struct sap" defines an SAP session.
 */

#define SAP_DB_SIZE 2048

struct sap {
  socket_udp *s;
  char *addr;
  uint16_t port;
  uint16_t ttl;
  sap_callback callback;
};

struct sap *
sap_init(const char *addr, uint16_t port, int ttl, sap_callback callback)
{
  struct sap *session;

  session = (struct sap *)xmalloc(sizeof(struct sap));
  memset (session, 0, sizeof(struct sap));

  session->addr = xstrdup(addr);
  session->port = port;
  session->ttl = min(ttl, 127);
  session->s = udp_init(addr, port, port, ttl);

  if(session->s == NULL) {
    xfree(session);
    return(NULL);
  }

  session->callback = callback;

  return session;
}

int
sap_recv(struct sap *s, struct timeval *timeout)
{
  sap_packet sap_p;
  sap_header *sap_h;
  static unsigned char *packetptr;

  udp_fd_zero();
  udp_fd_set(s->s);
  if(udp_select(timeout) > 0) {
    if(udp_fd_isset(s->s)) {
      uint8_t buffer[SAP_MAX_PACKET_LEN];
      int     buflen;
      buflen = udp_recv(s->s, buffer, SAP_MAX_PACKET_LEN);
      packetptr = buffer;

      sap_h = (sap_header *)buffer;
      sap_p.header = sap_h;

      packetptr += sizeof(sap_header);
      sap_p.originating_source = packetptr;

      packetptr += (sap_h->address_type) ? 16 : 4;
      sap_p.authentication_data = packetptr;

      packetptr += ntohs(sap_h->authentication_length/4);
      sap_p.payload = strstr(packetptr, "v=0");

      if(packetptr < sap_p.payload)
	{
	  sap_p.payload_type = packetptr;
	} else {
	  sap_p.payload_type = 0;
	}

      s->callback(&sap_p);
    }
    return TRUE;
  }
  return FALSE;
}

void 
sap_done(struct sap *s)
{
  udp_exit(s->s);

  xfree(s->addr);

  xfree(s);
}

void 
print_sap_packet(sap_packet *p)
{
  printf("SAP Header Information:\n");
  printf("  Version:        %d\n", p->header->version);
  printf("  Address Type:   %d\n", p->header->address_type);
  printf("  Reserved Bit:   %d\n", p->header->reserved);
  printf("  Message Type:   %d\n", p->header->message_type);
  printf("  Encrypted Flag: %d\n", p->header->encrypted_payload);
  printf("  Compressed Flag: %d\n", p->header->compressed_payload);
  printf("  Authentication Length: %d\n", 
	 ntohs(p->header->authentication_length));
  printf("  Authentication Data: %d\n", 
	 p->header->authentication_length ? strlen(p->authentication_data) : 0);
  printf("  Message ID Hash: %d\n", 
	 ntohs(p->header->message_identifier_hash));

  if(p->header->address_type) 
    {
      // This is a 128 bit IPv6 address
      printf("  Originating Source: %d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d.%d\n", 
	     p->originating_source[0], p->originating_source[1],
	     p->originating_source[2], p->originating_source[3],
	     p->originating_source[4], p->originating_source[5],
	     p->originating_source[6], p->originating_source[7],
	     p->originating_source[8], p->originating_source[9],
	     p->originating_source[10], p->originating_source[11],
	     p->originating_source[12], p->originating_source[13],
	     p->originating_source[14], p->originating_source[15]);
    } 
  else 
    {
      // This is a 32 bit IPv4 address
      printf("  Originating Source: %d.%d.%d.%d\n", 
	     p->originating_source[0], p->originating_source[1],
	     p->originating_source[2], p->originating_source[3]);
    }

  if(p->payload_type != NULL)
    printf("  Payload Type: %s\n", p->payload_type);

  printf("  Payload: \n- - - - - - - - - -\n%s- - - - - - - - - -\n", 
	 p->payload);
}
