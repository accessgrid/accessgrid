/* 
 * rtpdemo: A simple rtp application that sends and receives data.
 *
 * (c) 2000-2001 University College London.
 * (c) 2004 University of Chicago/Argonne National Laboratory
 */

#ifndef WIN32
#include <sys/time.h>
#include <inttypes.h>
#include <unistd.h>
#endif

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "config_unix.h"
#include "config_win32.h"
#include "debug.h"
#include "memory.h"
#include "net_udp.h"
#include "rtp.h"

#include "rtpforward.h"

/*
 * List of allowed participants that will be forwarded and 
 * a list of available participants to display.
 */
struct participant ssrclist[100];
unsigned long allowed_ssrc = 0;
int len_ssrclist = 0;

/* ------------------------------------------------------------------------ */
/* Access Methods */

//struct participant*
int GetParticipants(struct participant* participantList){
  int i = 0;
  for(i; i < len_ssrclist; i ++){
    struct participant p;
    p.name = ssrclist[i].name;
    p.ssrc = ssrclist[i].ssrc;
    // printf("one item %s   ", ssrclist[i].name);
    //printf("one item %ul\n", ssrclist[i].ssrc);
    participantList[i] = p;
    
  }
  
  //printf("this is what we return %d\n ", len_ssrclist);
  return len_ssrclist;
}

void
SetAllowedParticipant(unsigned long allowedParticipant){
  allowed_ssrc = allowedParticipant;
}

/* ------------------------------------------------------------------------- */


typedef struct session_data {
  struct rtp *session;
  uint32_t selected; 
} session_data;

static void rtp_event_handler2(struct rtp *session, rtp_event *e) 
{
}

static void rtp_event_handler(struct rtp *session, rtp_event *e) 
{
  rtp_packet	*p;
  rtcp_sdes_item	*r;
  struct session_data *data = (struct session_data *)rtp_get_userdata(session);
  uint32_t src_ssrc = rtp_my_ssrc(data->session);
  static int ts = 0;

  switch(e->type) 
    {
    case RX_RTP: 	
      p = (rtp_packet*)e->data;
      //if (data->selected == 0) {
      //data->selected = p->ssrc;
      //rtp_add_csrc(data->session, p->ssrc);
      //}
      
      int i = 0;
      int j = 0;
      
      // Check if participant is added to list.
      for(i; i<len_ssrclist; i++){
	if(ssrclist[i].ssrc == (unsigned long)p->ssrc){
	  j = 1;
	}
      }
      
      // If not; add participant to list.
      if(j == 0){
	ssrclist[len_ssrclist].name = "(*** no name set, click 'Refresh' ***)";
	ssrclist[len_ssrclist].ssrc = (unsigned long) p->ssrc;
     	len_ssrclist ++;
      }
      
      // Check if we are allowed to forward participant.
      if (p->ssrc == (uint32_t)allowed_ssrc) {
	rtp_send_data(data->session, p->ts, p->pt, p->m, p->cc, p->csrc, 
		      p->data, p->data_len, p->extn, p->extn_len, 
		      p->extn_type);
      }

      xfree(p);
      rtp_send_ctrl(data->session, ++ts, NULL);
      rtp_update(data->session);
      break;
    case SOURCE_CREATED: break;
    case SOURCE_DELETED: break;
    case RX_SDES:
      r = (rtcp_sdes_item*)e->data;
      // Check if participant is added to list.
      i = 0;
      j = 0;
      // Check if this is name info.
      for(i; i<len_ssrclist; i++){
	if((ssrclist[i].ssrc == (unsigned long)e->ssrc) && (r->type == 2)){
	  char* cname =  rtp_get_sdes(session, e->ssrc, 2);
	  ssrclist[i].name = (char*) malloc(strlen(cname)+1);
	  strcpy(ssrclist[i].name, cname);
	}
      }
      break;
      
    case RX_BYE:
    case RX_SR:
    case RX_RR:
    case RX_RR_EMPTY:
    case RX_RTCP_START:
    case RX_RTCP_FINISH:
    case RR_TIMEOUT:
    case RX_APP:
      break;
    }
  fflush(stdout);
}

// This is how I want the start method but have to figure out
// how to send more than one param to pthread create.
//void start(char* fromAddr, int fport, char* toAddr, int tport)

void* start(void* address)
//int main(int argc, const char *argv[]) 
{
  struct rtp	       *from_session = NULL;
  struct timeval	timeout;
  uint32_t              rtp_ts = 0;
  struct session_data   data;
  char *from_addr, *to_addr;
  int   from_port, to_port;

  struct address* addr;
  addr = (struct address*) address;

 

  data.selected = 0;
  
  printf("from address %s, from port %d, to address %s, to port %d \n", addr->fromAddr, addr->fport, addr->toAddr, addr->tport);
  
  from_addr = addr->fromAddr ; from_port = addr->fport;
  to_addr = addr->toAddr; to_port = addr->tport;
  
  // from_addr = fromAdd; from_port = fport;
  //to_addr = toAddr; to_port = tport;

  data.session = rtp_init(to_addr,	/* Host/Group IP address */ 
			  to_port,/* receive port */
			  to_port,/* transmit port */
			  127,		/* time-to-live */
			  64000,	/* B/W estimate */
			  rtp_event_handler2, 	/* RTP event callback */
			  NULL);	/* App. specific data */

  from_session = rtp_init(from_addr,	/* Host/Group IP address */ 
			  from_port,/* receive port */
			  from_port,/* transmit port */
			  127,		/* time-to-live */
			  64000,	/* B/W estimate */
			  rtp_event_handler,	/* RTP event callback */
			  (uint8_t *)&data);    /* App. specific data */

  if (from_session && data.session) {
    /* Run main loop */
    uint32_t my_ssrc = rtp_my_ssrc(data.session);
    /*
    const char 	*username  = "Malcovich Malcovitch";
    const char	*telephone = "1-800-RTP-DEMO";
    const char	*toolname  = "RTPdemo";
    const char  *email     = "nobody@mcs.anl.gov";
    const char  *cname     = "Ain't telling ya!";

    rtp_set_sdes(data.session, my_ssrc, RTCP_SDES_NAME,
		 username, strlen(username));
    rtp_set_sdes(data.session, my_ssrc, RTCP_SDES_PHONE,
		 telephone, strlen(telephone));
    rtp_set_sdes(data.session, my_ssrc, RTCP_SDES_TOOL,
		 toolname, strlen(toolname));
    rtp_set_sdes(data.session, my_ssrc, RTCP_SDES_EMAIL,
		 email, strlen(email));
    rtp_set_sdes(data.session, my_ssrc, RTCP_SDES_CNAME,
		 cname, strlen(cname));
    */

    while(send) {
      /* Send control packets */
      rtp_send_ctrl(from_session, rtp_ts, NULL);
      
      /* Receive control and data packets */
      timeout.tv_sec  = 0;
      timeout.tv_usec = 0;
      rtp_recv(from_session, &timeout, rtp_ts);
      
      /* State maintenance */
      rtp_update(from_session);

      xmemchk();
    }
    
    /* Say bye-bye */
    rtp_send_bye(from_session);
    rtp_send_bye(data.session);
    rtp_done(from_session);
    rtp_done(from_session);
  } else {
    printf("Could not initialize session for %s port %d\n",
	   from_addr, from_port);
  }
}
