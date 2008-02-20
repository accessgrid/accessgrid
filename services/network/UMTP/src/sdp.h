/*
 * FILE:   sdp.h
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

#ifndef _SDP_H
#define _SDP_H

#if defined(__cplusplus)
extern "C" {
#endif

  typedef struct sdp_network {
    char *network_type;
    char *address_type;
    char *address;
    int number_of_addresses;
  } sdp_network;

  typedef struct sdp_attribute {
    struct sdp_attribute *next;
    char *key;
    char *value;
  } sdp_attribute;

  typedef struct sdp_encryption {
    char *method;
    char *key;
  } sdp_encryption;

  typedef struct sdp_bandwidth_modifier {
    char *modifier;
    char *value;
  } sdp_bandwidth_modifier;

  typedef struct sdp_media {
    struct sdp_media *next;
    char *name;
    int port;
    int number_of_ports;
    sdp_network *network;
    char *transport;
    char *format_list;
    char *information;
    sdp_bandwidth_modifier *bandwidth_modifier;
    sdp_encryption *encryption;
    sdp_attribute *attributes;
  } sdp_media;

  typedef struct sdp_timezone {
    struct sdp_timezone *next;
    long adjustment;
    long offset;
  } sdp_timezone;

  typedef struct sdp_repeat {
    struct sdp_repeat *next;
    char *interval;
    char *duration;
    char *offsets;
  } sdp_repeat;

typedef struct sdp {
  int protocol_version;
  char *username;
  char *session_id;
  long version;
  sdp_network *network;
  char *name;
  char *information;
  char *uri;
  char *email;
  char *phone;
  sdp_bandwidth_modifier *bandwidth_modifier;
  sdp_timezone *timezones;
  sdp_encryption *encryption;
  sdp_attribute *attributes;

  long start_time;
  long stop_time;
  sdp_repeat *repeats;

  sdp_media *media;

  char *original;
} sdp;


int sdp_check_key(char *keylist, char *currentkey, char key);
sdp_media *sdp_handle_session_key(sdp *session, char key, char *value);
sdp_media *sdp_handle_media_key(sdp_media *media, char key, char *value);

sdp *sdp_parse(char *sdp_string);

void sdp_print(sdp *session); 
void sdp_print_media(sdp_media *media);
void sdp_print_network(sdp_network *network);

char *sdp_make(sdp *session);;

void sdp_free(sdp *session);
void sdp_free_media(sdp_media *media);
void sdp_free_attribute(sdp_attribute *attr);
void sdp_free_encryption(sdp_encryption *encr);
void sdp_free_bandwidth_modifier(sdp_bandwidth_modifier *bwm);
void sdp_free_repeat(sdp_repeat *repeat);
void sdp_free_network(sdp_network *network);

#if defined(__cplusplus)
}
#endif

#endif
