/*
 * FILE:    umtp_rx_handler.h
 * AUTHOR:  Namgon Kim
 * 
 * Handler for received UMTP packet
 *
 * Copyright (c) 2006 Networked Media Lab. GIST, Korea
 * All rights reserved.
 *
 * $Id: umtp_util.h,v 1.1.2.1 2006/07/01 05:53:39 ngkim Exp $
 */
#ifndef _UMTP_RX_HANDLER_H
#define _UMTP_RX_HANDLER_H

#ifndef _UMTP_H
#include "umtp.h"
#endif

#if defined(__cplusplus)
extern "C" {
#endif

umtp_packet buffer_to_umtp_packet(char* buffer, int packet_len);
int         do_if_sender(umtp_t umtp, umtp_endpoint *sender, char *buffer, uint32_t buf_len, umtp_packet *umtp_p, source_info *src);
int         do_if_not_sender(umtp_t umtp, uint32_t buf_len, umtp_packet *umtp_p, source_info *src);
void*       umtp_rx_handler(void* arg);

#if defined(__cplusplus)
}
#endif

#endif /* _UMTP_RX_HANDLER_H */
