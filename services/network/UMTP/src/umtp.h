/*
 * FILE:   umtp.h
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

#ifndef _UMTP_H
#define _UMTP_H

#if defined(__cplusplus)
extern "C" {
#endif

#define UMTP_VERSION "0"
#define UMTP_MAX_PACKET_LEN  RTP_MAX_PACKET_LEN+16
#define UMTP_DEFAULT_PORT 8010
#define DEFAULT_TTL 127

  typedef enum {
    DATA = 1,
    JOIN_GROUP = 2,
    LEAVE_GROUP = 3,
    TEAR_DOWN = 4,
    PROBE = 5,
    PROBE_ACK = 6,
    PROBE_NACK = 7,
    JOIN_RTP_GROUP = 8,
    LEAVE_RTP_GROUP = 9,
  } umtp_command;
  
  typedef struct umtp_header {
#ifdef WORDS_BIGENDIAN
    unsigned short ttl:8;
    unsigned short source:1;
    unsigned short version:3;
    unsigned short command:4;	
#else    
    unsigned short command:4;
    unsigned short version:3;
    unsigned short source:1;    
    unsigned short ttl:8;
#endif	
    unsigned short port;
    uint32_t multicast_address;
    uint16_t destination_cookie;
    uint16_t source_cookie;
  } umtp_header;

  typedef struct umtp_packet {
    unsigned char  *payload;
    umtp_header    *header;
    uint32_t       source;
  } umtp_packet;

  typedef struct m_probe {
#ifdef WORDS_BIGENDIAN
	  unsigned short flag:8;
	  unsigned short type:8;	  
#else
	  unsigned short type:8;
	  unsigned short flag:8;
#endif
	  uint16_t port;
	  uint32_t destination;
	  uint32_t slave_addr;	  
  } m_probe;

  typedef enum {
    MPROBE = 1,
    MPROBE_ACK = 2,
    MLEAVE = 3,
	MSUSPEND = 4,
  } m_probe_type;

  typedef enum {
    MPROBE_START = 1,
    MPROBE_STOP  = 0    
  } m_probe_state;

  typedef enum {
    MASTER = 0,
    SLAVE = 1,
  } umtp_flag;

  typedef enum {
    STOP = 0,
    START = 1,
  } thread_state;

  // slave and master join time should be different
  // If these values are same, master will always removed from the slave
  #define SLAVE_JOIN_TIMEOUT 300
  #define MASTER_JOIN_TIMEOUT 100
  #define MPROBE_TIMEOUT 3
  #define MPROBE_INTERVAL 60

  typedef struct umtp_endpoint {
    struct umtp_endpoint *next;
    uint32_t host;
    uint16_t port;
    uint16_t local_cookie;
    uint16_t remote_cookie;
    time_t last_time;
    socket_udp *ep_sock;
  } umtp_endpoint;

  typedef enum {
    JOIN = 1,
    LEAVE = 2,
    NO_PROBE_ACK = 3,
    FIND_NEIGHBOR = 4,
    SERVER_REACHABLE = 5,
    RECV_SIGTERM = 6,
  } group_management_command;

  typedef struct group_manager {
    uint16_t command;
    uint16_t port;
    uint32_t addr;    
  } group_manager;

  uint16_t notify_error;
  group_manager umtp_error; // variables to notify error

  typedef struct umtp_group {
    struct umtp_group *next;
    uint32_t group;
    uint16_t port;
    uint16_t timeout;
    time_t last_time;
    umtp_flag flag;
    thread_state state;
    uint16_t default_ttl;
    socket_udp *grp_sock;
    pthread_t t_id;
    umtp_endpoint *member_endpoints;
  } umtp_group;

  typedef struct umtp *umtp_t;
  typedef void (*umtp_callback)(umtp_packet *packet);

  typedef struct umtp {
    char *addr;
    uint16_t port;
    socket_udp *s;
    socket_udp *s1;
    socket_udp *m;
    uint16_t local_cookie;
    umtp_endpoint *slave; // designate umtp server
    umtp_endpoint *allowed_endpoints;
    umtp_group *active_groups;
    umtp_callback callback;
    pthread_t u_id;
    pthread_t m_id;
    pthread_t rx_id;
    pthread_t umtp_id;
    umtp_flag flag;
	m_probe_state mstate;
    FILE *log;
  } umtp;

  umtp_t umtp_init(char *addr, uint16_t port, umtp_flag flag, umtp_callback callback, m_probe_state mprobe_state);

  int*	      umtp_send_probe(umtp_t umtp, char *addr, uint16_t port);
  umtp_group* umtp_join_group(umtp_t umtp, char *addr, uint16_t port, uint16_t ttl);
  int         umtp_join_expire( umtp_t umtp, umtp_group *g);
  void        umtp_update(umtp_t umtp);
  void        umtp_done(umtp_t umtp);

  void* umtp_recv(void *arg);
  void* mcast_recv(void *arg);
  void* ucast_recv(void *arg);
  void* mcast_check(void *arg);

  void umtp_error_notify(umtp_t umtp, uint16_t finish);
  void print_umtp_packet(umtp_packet *p);

  int umtp_end;
  pthread_t t_id, t_id_m;

#if defined(__cplusplus)
}
#endif

#endif
		  
