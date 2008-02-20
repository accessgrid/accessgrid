/*
 * FILE:   sap.h
 * AUTHOR: Ivan R. Judson <judson@mcs.anl.gov> 
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
 */

#ifndef _SAP_H
#define _SAP_H

struct sap;

#if defined(__cplusplus)
extern "C" {
#endif

#define SAP_MAX_PACKET_LEN 1024

typedef struct {
#ifdef WORDS_BIGENDIAN
  unsigned short version:3;
  unsigned short address_type:1;
  unsigned short reserved:1;
  unsigned short message_type:1;
  unsigned short encrypted_payload:1;
  unsigned short compressed_payload:1;
#else
  unsigned short compressed_payload:1;
  unsigned short encrypted_payload:1;
  unsigned short message_type:1;
  unsigned short reserved:1;
  unsigned short address_type:1;
  unsigned short version:3;
#endif
  uint8_t                authentication_length;
  uint16_t               message_identifier_hash;
} sap_header;

typedef struct {
  sap_header    *header;
  unsigned char *originating_source;
  unsigned char *authentication_data;
  unsigned char *payload_type;
  unsigned char *payload;
} sap_packet;

typedef void (*sap_callback)(sap_packet *packet);

struct sap *sap_init(const char *addr, uint16_t port, int ttl, 
		     sap_callback callback);

int         sap_recv(struct sap *s, struct timeval *timeout);

void        sap_done(struct sap *s);

void        print_sap_packet(sap_packet *p);
 
#if defined(__cplusplus)
}
#endif

#endif
		  
