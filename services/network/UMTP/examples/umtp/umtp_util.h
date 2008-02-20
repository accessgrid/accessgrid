/*
 * FILE:    umtp_util.h
 * AUTHOR:  Namgon Kim
 * 
 * Simple utility functions for UMTP
 *
 * Copyright (c) 2006 Networked Media Lab. GIST, Korea
 * All rights reserved.
 *
 * $Id: umtp_util.h,v 1.1.2.1 2006/07/01 05:53:39 ngkim Exp $
 */
#ifndef _UMTP_UTIL_H
#define _UMTP_UTIL_H

#if defined(__cplusplus)
extern "C" {
#endif

  char* umtp_ntoa(uint32_t addr);
  char* umtp_host_addr(char* hname);
  int   umtp_addr_valid(char *dst);

  void make_udp_send_header( umtp_header *hdr, unsigned short cmd, unsigned short ttl, unsigned short port, uint32_t mcast_addr, uint16_t dest_cookie, uint16_t src_cookie);

  umtp_endpoint* umtp_add_endpoint(umtp_t umtp, char *addr, uint16_t port, uint16_t remote_cookie);
  umtp_endpoint* umtp_add_endpoint_(umtp_t umtp, uint32_t addr, uint16_t port, uint16_t remote_cookie);
  
  umtp_endpoint* umtp_add_member(umtp_group *g, umtp_endpoint *ep);

  umtp_endpoint* umtp_find_member(umtp_group *g, umtp_endpoint *ep);

  umtp_endpoint* umtp_find_endpoint(umtp_t umtp, char *addr, uint16_t port);
  umtp_endpoint* umtp_find_endpoint_(umtp_t umtp, uint32_t addr);
  umtp_endpoint* umtp_find_endpoint__(umtp_t umtp, uint32_t addr, uint16_t port);

  uint32_t    umtp_find_groupaddr(umtp_t umtp, uint32_t g_addr);  
  umtp_group* umtp_find_groupptr(umtp_t umtp, uint32_t g_addr);
  umtp_group *umtp_find_group(umtp_t umtp, char *addr, uint16_t port);
  umtp_group* umtp_find_group_(umtp_t umtp, uint32_t addr, uint16_t port);

  void umtp_remove_endpoint(umtp_t umtp, char *addr, uint16_t port);
  void umtp_remove_endpoint_(umtp_t umtp, uint32_t addr, uint16_t port);

  void umtp_remove_group(umtp_t umtp, umtp_group *g);
  void umtp_remove_member(umtp_group *g, umtp_endpoint *ep);
  void umtp_remove_member_in_group(umtp_t umtp, umtp_endpoint *ep);
    
  void umtp_leave_group(umtp_t umtp, umtp_group *g);
  void umtp_destroy_group(umtp_t umtp, umtp_group *g);

  char* create_udp_payload(umtp_packet *pkt, int pLen, int *sbufLen);
  void  do_udp_send(socket_udp *s, char * buffer, int buf_len, uint32_t address, uint16_t port);  
  
  void print_umtp_members(umtp_t umtp);
  void print_umtp_groups(umtp_t umtp);

  void send_packet(umtp_t umtp, uint32_t addr, uint16_t port, char* ptr, int ptr_len);

#if defined(__cplusplus)
}
#endif

#endif /* __UMTP_UTIL_H */
