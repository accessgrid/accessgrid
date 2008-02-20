/*
 * FILE:     sdp.c
 * AUTHOR:   Ivan R. Judson  <judson@mcs.anl.gov>
 *
 * The routines in this file implement parsing and construction of data
 * that's compliant with the Session Description Protocol, as specified 
 * in RFC draft-ietf-mmusic-sdp-new-08.
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
#include "sdp.h"

int
sdp_check_key(char keylist[], char *currentkey, char key)
{
  char *tempkey = keylist;

  while(*tempkey != key) 
    if(*tempkey != keylist[strlen(keylist)])
      tempkey++;
    else
      return 0;

  if(tempkey >= currentkey) {
    currentkey = tempkey;
    return 1;
  } else {
    return 0;
  }
}


sdp_media *
sdp_handle_session_key(sdp *session, char key, char *value)
{
  sdp_media *media = NULL, *curr_media = NULL;
  sdp_repeat *repeat = NULL, *curr_repeat = NULL;
  sdp_timezone *timezone = NULL;
  sdp_network *network = NULL;
  sdp_bandwidth_modifier *bwm;
  sdp_attribute *attr, *curr_attr;
  sdp_encryption *encrypt;
  unsigned int n_char;

  switch (key) {
  case 'v':
    session->protocol_version = atoi(value);
    break;
  case 'o':
    network = xmalloc(sizeof(sdp_network));
    memset (network, 0, sizeof(sdp_network));

    sscanf(value, "%as %as %ld %as %as %as\n", 
	   &(session->username),&(session->session_id), &(session->version), 
	   &(network->network_type), &(network->address_type), 
	   &(network->address));
 
    network->number_of_addresses = 1;
    session->network = network;

    break;
  case 's':
    session->name = xstrdup(value);
    break;
  case 'i':
    session->information = xstrdup(value);
    break;
  case 'u':
    session->uri = xstrdup(value);
    break;
  case 'e':
    session->email = xstrdup(value);
    break;
  case 'p':
    session->phone = xstrdup(value);
    break;
  case 'c':
    network = xmalloc(sizeof(sdp_network));
    memset (network, 0, sizeof(sdp_network));

    sscanf(value, "%as %as %as\n", &(network->network_type),
	   &(network->address_type), &(network->address));

    network->number_of_addresses = 1;

    if(session->network != NULL) 
      session->network = network;
    else
      xfree(network);

    break;
  case 'b':
    bwm = xmalloc(sizeof(sdp_bandwidth_modifier));
    memset (bwm, 0, sizeof(sdp_bandwidth_modifier));

    sscanf(value, "%a[^:]:%a[^\n]", &(bwm->modifier), &(bwm->value));

    if(session->bandwidth_modifier == NULL)
      session->bandwidth_modifier = bwm;
    else 
      xfree(bwm);

    break;
  case 't':
    sscanf(value, "%ld %ld\n", &(session->start_time), &(session->stop_time));

    break;
  case 'r':
    repeat = xmalloc(sizeof(sdp_repeat));
    memset (repeat, 0, sizeof(sdp_repeat));

    sscanf(value, "%as %as %as\n", &(repeat->interval), &(repeat->duration), 
	   &(repeat->offsets));

    if(session->repeats == NULL)
      session->repeats = repeat;
    else {
      curr_repeat = session->repeats;
      while(curr_repeat != NULL) 
	curr_repeat = curr_repeat->next;
      curr_repeat->next = repeat; 
    }
    break;
  case 'z':
    /* This is icky but for now... */
    timezone = xmalloc(sizeof(sdp_timezone));
    memset(timezone, 0, sizeof(sdp_timezone));

    sscanf(value, "%ld %ld", &(timezone->adjustment), &(timezone->offset));

    session->timezones = timezone;
    break;
  case 'k':
    encrypt = xmalloc(sizeof(sdp_encryption));
    memset(encrypt, 0, sizeof(sdp_encryption));

    sscanf(value, "%a[^:]:%a[^\n]", &(encrypt->method), &(encrypt->key));

    if(session->encryption == NULL)
      session->encryption = encrypt;
    else
      xfree(encrypt);

    break;
  case 'a':
    attr = xmalloc(sizeof(sdp_attribute));
    memset(attr, 0, sizeof(sdp_attribute));

    n_char = strcspn(value, ":");

    attr->key = xmalloc(n_char+1);
    memset(attr->key, '\0', n_char+1);
    strncpy(attr->key, value, n_char);

    if(strlen(value) == n_char)
      attr->value = NULL;
    else {
      attr->value = xmalloc(strlen(value) - n_char + 1);
      memset(attr->value, '\0', strlen(value) - n_char + 1); 
      strncpy(attr->value, value+n_char+1, strlen(value) - n_char);
    }

    if(session->attributes == NULL)
      session->attributes = attr;
    else {
      curr_attr = session->attributes;
      while(curr_attr->next != NULL)
	curr_attr = curr_attr->next;
      
      curr_attr->next = attr;
    }
    break;
  case 'm':
    media = xmalloc(sizeof(sdp_media));
    memset(media, 0, sizeof(sdp_media));
    sscanf(value, "%as %d %as %as\n", &(media->name),
	   &(media->port), &(media->transport), 
	   &(media->format_list));
    media->number_of_ports = 1;

    if(session->media == NULL)
      session->media = media;
    else {
      curr_media = session->media;
      while(curr_media->next != NULL)
	curr_media = curr_media->next;

      curr_media->next = media;
    }
    break;
  }

  return media;
}

sdp_media *
sdp_handle_media_key(sdp_media *media, char key, char *value)
{
  sdp_media *new_media;
  sdp_network *network;
  sdp_bandwidth_modifier *bwm;
  sdp_attribute *attr, *curr_attr;
  sdp_encryption *encrypt;
  unsigned int n_char;

  switch (key) {
  case 'i':
    media->information = xstrdup(value);
    break;
  case 'c':
    network = xmalloc(sizeof(sdp_network));
    memset (network, 0, sizeof(sdp_network));

    sscanf(value, "%as %as %as\n", &(network->network_type),
	   &(network->address_type), &(network->address));

    network->number_of_addresses = 1;

    if(media->network == NULL)
      media->network = network;
    else
      xfree(network);

    break;
  case 'b':
    bwm = xmalloc(sizeof(sdp_bandwidth_modifier));
    memset (bwm, 0, sizeof(sdp_bandwidth_modifier));

    sscanf(value, "%as:%as\n", &(bwm->modifier), &(bwm->value));

    if(media->bandwidth_modifier == NULL)
      media->bandwidth_modifier = bwm;
    else
      xfree(bwm);

    break;
  case 'k':
    encrypt = xmalloc(sizeof(sdp_encryption));
    memset(encrypt, 0, sizeof(sdp_encryption));

    sscanf(value, "%as:%as\n", &(encrypt->method), &(encrypt->key));

    if(media->encryption == NULL)
      media->encryption = encrypt;
    else 
      xfree(encrypt);

    break;
  case 'a':
    attr = xmalloc(sizeof(sdp_attribute));
    memset(attr, 0, sizeof(sdp_attribute));

    n_char = strcspn(value, ":");

    attr->key = xmalloc(n_char+1);
    memset(attr->key, '\0', n_char+1);
    strncpy(attr->key, value, n_char);

    if(strlen(value) == n_char)
      attr->value = NULL;
    else {
      attr->value = xmalloc(strlen(value) - n_char + 1);
      memset(attr->value, '\0', strlen(value) - n_char + 1); 
      strncpy(attr->value, value+n_char+1, strlen(value) - n_char);
    }

    if(media->attributes == NULL)
      media->attributes = attr;
    else {
      curr_attr = media->attributes;
      while(curr_attr->next != NULL)
	curr_attr = curr_attr->next;
      
      curr_attr->next = attr;
    }
    break;
  case 'm':
    new_media = xmalloc(sizeof(sdp_media));
    memset(new_media, 0, sizeof(sdp_media));
    sscanf(value, "%as %d %as %as\n", &(new_media->name),
	   &(new_media->port), &(new_media->transport), 
	   &(new_media->format_list));
    new_media->number_of_ports = 1;
    
    media->next = new_media;
    media = media->next;
    break;
  }

  return media;
}

sdp *sdp_parse(char *sdp_string)
{
  static char sessionkeys[] = "vosiuepcbtrzkam";
  static char mediakeys[]   = "micbka";
  static char *current_key;
  int goodkey = 0;
  sdp_media *media = NULL;
  char *line = NULL, key, *value = NULL;
  static char *pos;
  sdp *session = NULL;
  int n_char;

  if(sdp_string != NULL) {
    current_key = sessionkeys;
    session = xmalloc(sizeof(sdp));
    memset (session, 0, sizeof(sdp));

    session->original = xstrdup(sdp_string);

    pos = sdp_string;

    do {
      n_char = strcspn(pos, "\n");

      line = xmalloc(n_char+1);
      memset(line, '\0', n_char+1);
      strncpy(line, pos, n_char);
      pos += n_char + 1;
      
      if(strchr(line, '=') != NULL) {
	key = line[0];
	value = &(line[2]);

	if(media == NULL) {
	  if((goodkey = sdp_check_key(sessionkeys, current_key, key)) == 1) 
	    media = sdp_handle_session_key(session, key, value);
	  else
	    printf("Bad Session Key!\n");
	} else {
	  if((goodkey = sdp_check_key(mediakeys, current_key, key)) == 1) 
	    media = sdp_handle_media_key(media, key, value);
	  else
	    printf("Bad Media Key!\n");
	}
      }
      xfree(line);
    } while (n_char != 0);
  }
  
  return session;
}

void sdp_print(sdp *session)
{
  if(session != NULL) {
    sdp_media *current_media = session->media;
    sdp_attribute *current_attribute = session->attributes;

    printf("Protocol Version: %d\n", session->protocol_version);
    printf("Username: %s\n", session->username);
    printf("Session ID: %s\n", session->session_id);
    printf("Version: %ld\n", session->version);
    printf("Name: %s\n", session->name);
    printf("Information: %s\n", session->information);
    printf("URI: %s\n", session->uri);
    printf("Email: %s\n", session->email);
    printf("Phone: %s\n", session->phone);
    printf("Start Time: %ld\n", session->start_time);
    printf("Stop Time: %ld\n", session->stop_time);

    if(session->network != NULL) {
      sdp_print_network(session->network);
    }

    if(session->bandwidth_modifier != NULL) {
      printf("Bandwidth Modifier\n");
      printf("\tModifier: %s\n", session->bandwidth_modifier->modifier);
      printf("\tValue: %s\n", session->bandwidth_modifier->value);
    }

    printf("Session Attributes:\n");
    while(current_attribute != NULL) {
      printf("\tAttribute: %s Value: %s\n", 
	     current_attribute->key, current_attribute->value);
      current_attribute = current_attribute->next;
    }

    current_media = session->media;
    while(current_media != NULL) {
      sdp_print_media(current_media);
      current_media = current_media->next;
    }
  }
}

void
sdp_print_network(sdp_network *network)
{
  printf("Network Information:\n");
  printf("\tNetwork Type: %s\n", network->network_type);
  printf("\tAddress Type: %s\n", network->address_type);
  printf("\tAddress: %s\n", network->address);
  printf("\t# of Addresses: %d\n", network->number_of_addresses);
}

void
sdp_print_media(sdp_media *media)
{
  sdp_attribute *curr_attr = media->attributes;

  printf("Media Configuration:\n");
  printf("\tName: %s\n", media->name);
  printf("\tPort: %d Number of Ports: %d\n", media->port,
	 media->number_of_ports);
  if(media->network != NULL) {
    sdp_print_network(media->network);
  }
  printf("\tTransport: %s\n", media->transport);
  printf("\tInformation: %s\n", media->information);

  if(media->attributes != NULL) {
    printf("\tMedia Attributes:\n");
    while(curr_attr != NULL) {
      printf("\t\tAttribute: %s Value: %s\n", curr_attr->key, 
	     curr_attr->value);
      curr_attr = curr_attr->next;
    }
  }
}

char *
sdp_make(sdp *session)
{
  sdp_timezone *tz;
  sdp_attribute *attr;
  sdp_media *media;
  char *sdp_string;

  sdp_string = xmalloc(4096);

  sprintf(sdp_string, "v=%d\n", session->protocol_version);
  sprintf(sdp_string, "%so=%s %s %ld", sdp_string,
	   session->username, session->session_id, session->version);
  if(session->network != NULL) {
    sprintf(sdp_string, "%s %s %s %s\n", sdp_string,
	     session->network->network_type, 
	     session->network->address_type,
	     session->network->address);
  }
  sprintf(sdp_string, "%ss=%s\n", sdp_string, session->name);

  if(session->information != NULL)
    sprintf(sdp_string, "%si=%s\n", sdp_string, session->information);

  if(session->uri != NULL)
    sprintf(sdp_string, "%su=%s\n", sdp_string, session->uri);

  if(session->email != NULL)
    sprintf(sdp_string, "%se=%s\n", sdp_string, session->email);

  if(session->phone != NULL)
    sprintf(sdp_string, "%sp=%s\n", sdp_string, session->phone);

  if(session->network != NULL)
    sprintf(sdp_string, "%sc=%s %s %s\n", sdp_string,
	    session->network->network_type,
	    session->network->address_type,
	    session->network->address);

  if(session->bandwidth_modifier != NULL)
    sprintf(sdp_string, "%sb=%s:%s\n", sdp_string, 
	    session->bandwidth_modifier->modifier, 
	    session->bandwidth_modifier->value);

  sprintf(sdp_string, "%st=%ld %ld\n", sdp_string, 
	  session->start_time, session->stop_time);

  if(session->timezones != NULL) {
    tz = session->timezones;
    sprintf(sdp_string, "%sz=%ld %ld", sdp_string, tz->adjustment, tz->offset);

    while(tz->next != NULL) {
      sprintf(sdp_string, "%s %ld %ld", sdp_string,
	      tz->next->adjustment, tz->next->offset);
      tz = tz->next;
    }
    sprintf(sdp_string, "%s\n", sdp_string);
  }

  if(session->encryption != NULL) {
    if(session->encryption->key == NULL)
      sprintf(sdp_string, "%sk=%s\n", sdp_string, 
	      session->encryption->method);
    else
      sprintf(sdp_string, "%sk=%s:%s\n", sdp_string, 
	      session->encryption->method,
	      session->encryption->key);
  }
  
  attr = session->attributes;
  while(attr != NULL) {
    sprintf(sdp_string, "%sa=%s:%s\n", sdp_string,
	    attr->key, attr->value);
    attr = attr->next;
  }

  media = session->media;
  while(media != NULL) {
    if(media->number_of_ports > 1)
      sprintf(sdp_string, "%sm=%s %d/%d %s %s\n", sdp_string,
	      media->name, media->port, media->number_of_ports,
	      media->transport, media->format_list);
    else
      sprintf(sdp_string, "%sm=%s %d %s %s\n", sdp_string,
	      media->name, media->port, media->transport, 
	      media->format_list);
    if(media->information != NULL)
      sprintf(sdp_string, "%si=%s\n", sdp_string, media->information);
    
    if(media->network != NULL)
      sprintf(sdp_string, "%sc=%s %s %s\n", sdp_string,
	      media->network->network_type,
	      media->network->address_type,
	      media->network->address);

    if(media->bandwidth_modifier != NULL)
      sprintf(sdp_string, "%sb=%s:%s\n", sdp_string, 
	      media->bandwidth_modifier->modifier, 
	      media->bandwidth_modifier->value);

    if(media->encryption != NULL) {
      if(media->encryption->key == NULL)
	sprintf(sdp_string, "%sk=%s\n", sdp_string, 
		media->encryption->method);
      else
	sprintf(sdp_string, "%sk=%s:%s\n", sdp_string, 
		media->encryption->method,
		media->encryption->key);
    }
  
    attr = media->attributes;
    while(attr != NULL) {
      sprintf(sdp_string, "%sa=%s:%s\n", sdp_string,
	      attr->key, attr->value);
      attr = attr->next;
    }
    media = media->next;
  }

  return sdp_string;
}

void
sdp_free(sdp *session)
{
  sdp_media *media, *cmedia;
  sdp_attribute *attr, *cattr;
  sdp_repeat *repeat, *crepeat;

  if(session->username != NULL)
    xfree(session->username);

  if(session->session_id != NULL)
    xfree(session->session_id);

  if(session->network != NULL)
    sdp_free_network(session->network);

  if(session->name != NULL)
    xfree(session->name);

  if(session->information != NULL)
    xfree(session->information);

  if(session->uri != NULL)
    xfree(session->uri);

  if(session->email != NULL)
    xfree(session->email);
  
  if(session->phone != NULL) 
    xfree(session->phone);

  if(session->bandwidth_modifier != NULL)
    sdp_free_bandwidth_modifier(session->bandwidth_modifier);

  if(session->timezones != NULL)
    xfree(session->timezones);

  if(session->encryption != NULL)
    sdp_free_encryption(session->encryption);

  repeat = session->repeats;
  while(repeat != NULL) {
    crepeat = repeat;
    repeat = repeat->next;
    sdp_free_repeat(crepeat);
  }

  attr = session->attributes;
  while(attr != NULL) {
    cattr = attr;
    attr = attr->next;
    sdp_free_attribute(cattr);
  }

  media = session->media;
  while(media != NULL) {
    cmedia = media;
    media = media->next;
    sdp_free_media(cmedia);
  }
  
  if(session->original != NULL)
    xfree(session->original);

  xfree(session);
}

void
sdp_free_network(sdp_network *network)
{
  xfree(network->network_type);
  xfree(network->address_type);
  xfree(network->address);
  xfree(network);
}

void
sdp_free_attribute(sdp_attribute *attr)
{
  xfree(attr->key);
  if(attr->value != NULL)
    xfree(attr->value);
  xfree(attr);
}

void
sdp_free_encryption(sdp_encryption *encr)
{
  xfree(encr->method);
  xfree(encr->key);
  xfree(encr);
}

void
sdp_free_bandwidth_modifier(sdp_bandwidth_modifier *bwm)
{
  xfree(bwm->modifier);
  xfree(bwm->value);
  xfree(bwm);
}

void
sdp_free_repeat(sdp_repeat *repeat)
{
  xfree(repeat->interval);
  xfree(repeat->duration);
  xfree(repeat->offsets);
  xfree(repeat);
}

void 
sdp_free_media(sdp_media *media)
{
  sdp_attribute *attr, *cattr;

  xfree(media->name);

  if(media->network != NULL)
    sdp_free_network(media->network);

  xfree(media->transport);
  xfree(media->format_list);

  if(media->information != NULL)
    xfree(media->information);
  
  if(media->bandwidth_modifier != NULL)
    sdp_free_bandwidth_modifier(media->bandwidth_modifier);

  if(media->encryption != NULL)
    sdp_free_encryption(media->encryption);

  attr = media->attributes;
  while(attr != NULL) {
    cattr = attr;
    attr = attr->next;
    sdp_free_attribute(cattr);
  }

  xfree(media);
}

