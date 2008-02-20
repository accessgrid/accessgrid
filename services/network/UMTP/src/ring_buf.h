/*
 * FILE:    ring_buf.h
 * AUTHOR:  Namgon Kim
 * 
 * Ring Buffer function
 *
 * Copyright (c) 2006 Networked Media Lab. GIST, Korea
 * All rights reserved.
 *
 * $Id: ring_buf.h,v 1.1.2.1 2006/07/01 05:53:39 ngkim Exp $
 */

#include <pthread.h>
#include <string.h>

#ifndef _RING_BUF_H
#define _RING_BUF_H

#if defined(__cplusplus)
extern "C" {
#endif
        
#define MAX_BUF_LEN 1516

typedef struct source_info {
  uint32_t src_addr;
  uint16_t src_port;
} source_info;

typedef struct ring_buffer {
  uint8_t       is_filled;
  uint16_t      data_len; 
  source_info	data_src;
  unsigned char data[MAX_BUF_LEN];
} ring_buffer;

int set_buffer(ring_buffer *buf, uint8_t *data, int data_len, source_info *src);
void ring_buf_init(int buf_size);
void ring_buf_close( void );
int put_ring( uint8_t *ptr, int ptr_len, source_info *src );
int get_ring( uint8_t *ptr, source_info *src );

FILE* fp;
void* do_loop(void *data);
void* do_loop1(void *data);
void* do_loop2(void *data);

#if defined(__cplusplus)
}
#endif

#endif /* _RING_BUF_H */
