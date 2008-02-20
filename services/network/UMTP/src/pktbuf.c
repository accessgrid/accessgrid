/*
 * FILE:      pktbuf.c
 * AUTHOR(S): Orion Hodson 
 *
 * Copyright (c) 1999-2000 University College London
 * All rights reserved.
 */
 
#ifndef HIDE_SOURCE_STRINGS
static const char cvsid[] = 
	"$Id: pktbuf.c,v 1.1.1.1 2006/06/30 04:39:43 ngkim Exp $";
#endif /* HIDE_SOURCE_STRINGS */

#include "config_unix.h"
#include "config_win32.h"
#include "debug.h"
#include "memory.h"
#include "rtp.h"
#include "pktbuf.h"

struct s_pktbuf {
        rtp_packet **buf;    /* Pointer to rtp packets                      */
        uint16_t     insert; /* Next insertion point (FIFO circular buffer) */
        uint16_t     buflen; /* Max number of packets                       */
        uint16_t     used;   /* Actual number of packets buffered           */
};

int
pktbuf_create(struct s_pktbuf **ppb, uint16_t size)
{
        struct s_pktbuf *pb;
        uint32_t          i;
        
        pb = (struct s_pktbuf*)xmalloc(sizeof(struct s_pktbuf));
        if (pb == NULL) {
                return FALSE;
        }
        
        pb->buf = (rtp_packet**)xmalloc(sizeof(rtp_packet*) * size);
        if (pb->buf == NULL) {
                xfree(pb);
                return FALSE;
        }

        for(i = 0; i < size; i++) {
                pb->buf[i] = NULL;
        }

        pb->buflen = size;
        pb->used   = 0;
        pb->insert = 0;

        *ppb = pb;
        return TRUE;
}

void
pktbuf_destroy(struct s_pktbuf **ppb)
{
        struct s_pktbuf *pb;
        uint32_t i;

        pb = *ppb;
        for(i = 0; i < pb->buflen; i++) {
                if (pb->buf[i]) {
                        xfree(pb->buf[i]);
                }
        }
        xfree(pb->buf);
        xfree(pb);
        *ppb = NULL;
}

int 
pktbuf_enqueue(struct s_pktbuf *pb, rtp_packet *p)
{
        assert(p != NULL);

        if (pb->buf[pb->insert] != NULL) {
                /* A packet already sits in this space */
                xfree(pb->buf[pb->insert]);
                debug_msg("Buffer overflow.  Process was blocked or network burst.\n");
        } else {
                pb->used++;
                assert(pb->used <= pb->buflen);
        }

        pb->buf[pb->insert] = p;

        pb->insert++;
        if (pb->insert == pb->buflen) {
                pb->insert = 0;
        }

        return TRUE;
}

int 
pktbuf_dequeue(struct s_pktbuf *pb, rtp_packet **pp)
{
        uint32_t idx = (pb->insert + pb->buflen - pb->used) % pb->buflen;

        *pp = pb->buf[idx];
        if (*pp) {
                pb->buf[idx] = NULL;
                pb->used--;
                return TRUE;
        }
        return FALSE;
}

static int 
timestamp_greater(uint32_t t1, uint32_t t2)
{
        uint32_t delta = t1 - t2;
        
        if (delta < 0x7fffffff && delta != 0) {
                return TRUE;
        }
        return FALSE;
}

int
pktbuf_peak_last(pktbuf_t   *pb,
                 rtp_packet **pp)
{
        uint32_t     idx, max_idx;

        max_idx = idx = (pb->insert + pb->buflen - pb->used) % pb->buflen;
        if (pb->buf[idx] == NULL) {
                assert(pb->used == 0);
                *pp = NULL;
                return FALSE;
        }

        idx = (idx + 1) % pb->buflen;
        while (pb->buf[idx] != NULL) {
                if (timestamp_greater(pb->buf[idx]->ts, 
                                      pb->buf[max_idx]->ts)) {
                        max_idx = idx;
                }
                idx = (idx + 1) % pb->buflen;
        }
        
        *pp = pb->buf[max_idx];
        return TRUE;
}

uint16_t 
pktbuf_get_count(pktbuf_t *pb)
{
        return pb->used;
}

