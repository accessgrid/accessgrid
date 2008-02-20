/*
* FILE:     umtp.c
* AUTHOR:   Namgon Kim <ngkim@netmedia.gist.ac.kr> and Ivan R. Judson  <judson@mcs.anl.gov>
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
#include "inet_pton.h"
#include "inet_ntop.h"
#include "hmac.h"
#include "qfDES.h"
#include "base64.h"
#include "gettimeofday.h"
#include "vsnprintf.h"
#include "time.h"
#include "rtp.h"
#include "pthread.h"

#include "ring_buf.h"
#include "umtp.h"
#include "umtp_util.h"
#include "umtp_rx_handler.h"

typedef struct thread_param {
    umtp_t umtp;
    umtp_group *g;
    struct timeval *timeout;
} thread_param;

///////////////////////////////
//// variables for probe check

  int probe_sent;
  time_t   last_probe_sent;

//
/////////////////////////////////


void print_umtp_packet(umtp_packet *p)
{
        fprintf(stdout, "UMTP Packet:\n");
        fprintf(stdout, "\tHeader:\n");

        if(p->header->source)
                fprintf(stdout, "\t\tSource: %s\n", umtp_ntoa(p->source));
        fprintf(stdout, "\t\tVersion: %d\n", p->header->version);
        fprintf(stdout, "\t\tCommand: %d\n", p->header->command);
        fprintf(stdout, "\t\tPort: %d\n", p->header->port);
        fprintf(stdout, "\t\tTTL: %d\n", p->header->ttl);
        fprintf(stdout, "\t\tSource Cookie: %x\n", p->header->source_cookie);
        fprintf(stdout, "\t\tDestination Cookie: %x\n",
                p->header->destination_cookie);
        fprintf(stdout, "\t\tMulticast Address: %s\n",
                umtp_ntoa(p->header->multicast_address));
}


umtp_t umtp_init(char *addr, uint16_t port, umtp_flag flag, umtp_callback callback, m_probe_state mprobe_state)
{
    int mc_port;
    struct umtp *session;	
    char name[255], *umtp_addr = NULL, mc_addr[12], s_type[7];
    	
    int state, m_state, umtp_state, rx_state, ttl = DEFAULT_TTL;

#ifdef WIN32
    WORD wVersionRequested;
    WSADATA wsaData;
    int err;

    wVersionRequested = MAKEWORD( 2, 2 );
 
    err = WSAStartup( wVersionRequested, &wsaData );
    if ( err != 0 ) {
	/* Tell the user that we could not find a usable */
	/* WinSock DLL.                                  */
	return NULL;
    }
#endif
	
    if(umtp_addr_valid(addr))	
	umtp_addr = umtp_host_addr(addr);
    else
    {
	printf("Address is not valid!\n");
#ifdef WIN32
	WSACleanup();
#endif
	return NULL;
    }

    if (flag == MASTER) strcpy(s_type, "MASTER");
    else                strcpy(s_type, "SERVER");

    session = (umtp_t)malloc(sizeof(umtp));
    memset(session, 0, sizeof(umtp));			
	
    session->port		= port;	
    session->allowed_endpoints	= NULL;
    session->active_groups	= NULL;
    session->s			= udp_init(umtp_addr, port, port, ttl);
    session->flag		= flag;	
	session->mstate		= mprobe_state;

    // Due to the problem in setting ttl value for socket session->s using udp_init
    if (setsockopt(session->s->fd, IPPROTO_IP, IP_MULTICAST_TTL, (char *) &(session->s->ttl), sizeof(session->s->ttl)) != 0) 
    {	
	fprintf(stdout, "[umtp__init] setsockopt IP_MULTICAST_TTL");
        umtp_end = 1;
    }
	
    // put local ip address into session->addr
    if(( gethostname(name, sizeof(name))) >= 0) {
	session->addr = umtp_host_addr(name);
        if( session->addr == NULL ) 
	    umtp_end = 1;
    }	  
    else {		
	printf("gethostname failed");
	umtp_end = 1;
    }

    //session->log = fopen("umtp.log", "a");
    session->log = stdout;
    if( session->log == NULL )
    	printf("Error: can't open log file.\n");
		
    fprintf(session->log, "\n======    UMTP %s Initialization    ======\n", s_type);
    fprintf(session->log, " *** LOCAL IP ADDR [%s/%d]\n", session->addr, port);	

    ring_buf_init(4*1024);

    //=================================================================================//
    // UMTP Recv Thread
    //=================================================================================//

    umtp_state = pthread_create(&session->umtp_id, NULL, umtp_recv, (void *)session);
    if(umtp_state != 0)
    {
        fprintf(session->log, "Error in creating UMTP recv thread!\n");
        umtp_end = 1;
    }
    fprintf(session->log, " *** THREAD CREATE - UMTP recv\n");

    //=================================================================================//
    // UMTP Rx Handler Thread
    //=================================================================================//

    rx_state = pthread_create(&session->rx_id, NULL, umtp_rx_handler, (void *)session);
    if(rx_state != 0)
    {
        fprintf(session->log, "Error in creating UMTP RX Handler thread!\n");
        umtp_end = 1;
    }
    fprintf(session->log, " *** THREAD CREATE - UMTP RX Handler \n");

    //=================================================================================//
    // MPROBE Thread
    //=================================================================================//
    
    strcpy(mc_addr, "224.2.2.224");

    mc_port = 50000;

	if( mprobe_state == MPROBE_START )
	{
		session->m = udp_init(mc_addr, mc_port, mc_port, ttl);
		m_state = pthread_create(&session->m_id, NULL, mcast_check, (void *)session);
		if(m_state != 0)
		{
		fprintf(session->log, "Error in creating multicast check thread!\n");
		umtp_end = 1;
		}
		fprintf(session->log, " *** THREAD CREATE - MPROBE [%s/%d]\n", mc_addr, mc_port);
	}
	else
	{
		fprintf(session->log, " *** DO NOT CREATE MPROBE THREAD\n");
	}

    //=================================================================================//
    // UGMP Thread 
    //=================================================================================//
   
    session->s1 = udp_init(umtp_addr, port+1, port+1, ttl);
    state       = pthread_create(&session->u_id, NULL, ucast_recv, (void *)session);
    if(state != 0) 
    {
        fprintf(session->log, "Error in creating thread!\n");
        umtp_end = 1;
    }
    fprintf(session->log, " *** THREAD CREATE - UGMP [%s/%d]\n", session->addr, port+1);	
    
    //= end of thread creation ========================================================//
	
    if( session->flag == MASTER ) notify_error = 0; // notification of error to AG Connector	
    else notify_error = 1; // server doesn't need to notify
	
    // set new cookie value
    srand((unsigned)time(NULL)); 
    #ifndef WIN32
        lrand48();
    #endif
    session->local_cookie		= (uint16_t)lrand48();
    fprintf(session->log, " *** LOCAL COOKIE [%d]\n", session->local_cookie);

    // add umtp server as an endpoint
    umtp_add_endpoint(session, umtp_addr, port, (uint16_t)lrand48());
    if(session->s == NULL) 	umtp_end = 1;
    else {
        session->callback = callback;
        return session;
    }
    return session;
}

void* umtp_recv(void * arg)
{
    /////////////////////////////////////////////////
    // variables for receiving datagrams
    
    unsigned int     buflen = 0;    
    uint8_t buffer[UMTP_MAX_PACKET_LEN]; 
    
    //
    /////////////////////////////////////////////////

    ///////////////////////////////////////////////
    // variables for select() call	
        
	uint32_t recv_cnt = 0;
    struct timeval tv;
    fd_set readfds;

    struct   sockaddr_in fromAddr;
    uint32_t fromSize = sizeof(fromAddr);

    //
    ///////////////////////////////////////////////
    
    umtp_t umtp = (umtp_t)arg;

    while(1)
    {
		if( umtp_end == 1 && notify_error == 1  ) {
			fprintf(umtp->log, " [umtp__recv]  UMTP RECV THREAD STOP.\n");
			pthread_exit(arg);
		}

		tv.tv_sec  = 5;    tv.tv_usec = 0;
		FD_ZERO(&readfds); FD_SET(umtp->s->fd, &readfds);

		if( (select(umtp->s->fd + 1, &readfds, NULL, NULL, &tv)) >= 0 ) {
			if( FD_ISSET(umtp->s->fd, &readfds) ) {
				source_info src;

				memset(buffer, 0, UMTP_MAX_PACKET_LEN);
				buflen	= recvfrom(umtp->s->fd, buffer, UMTP_MAX_PACKET_LEN, 0, \
   							(struct sockaddr *)&fromAddr, &fromSize);

				//////////////////////////////////////////////////
				// umtp_packet should be bigger than sizeof(umtp_header)
			
				if(buflen < sizeof(umtp_header) + sizeof(uint32_t)) continue;
				
				//	
				//////////////////////////////////////////////////

				// put data into buffer
				src.src_addr = fromAddr.sin_addr.s_addr;
				src.src_port = ntohs(fromAddr.sin_port);
				put_ring( buffer, buflen, &src ); 
			}
		}
    }
}

umtp_group* umtp_join_group(umtp_t umtp, char *addr, uint16_t port, uint16_t ttl)
{
  /* 
  1) The local node requests the joining of a (group, port) g, with default TTL t
  */
  umtp_group *G = umtp->active_groups;
  umtp_group *g;

  g = umtp_find_group(umtp, addr, port);
  if( g == NULL )
  {	
	int state;		
	thread_param* param;
	struct timeval timeout;

	g = malloc(sizeof(umtp_group));
	param = malloc( sizeof(thread_param) );
	memset(g, 0, sizeof(umtp_group));

	// add g to G(umtp->active_groups)
	if (G != NULL) 
	{
		while( G->next != NULL ) G = G->next;
		G->next = g;   //add g to G
	} 
	else // new G
		umtp->active_groups = g;

	/*  
      add g to G; set F_g to "master"; set T_g to t
      locally join the multicast group g
	*/
	//set group member vars
	g->next		= NULL;
	g->group	= (uint32_t)inet_addr(addr);
	g->port		= port;
	
	g->flag		= umtp->flag;
	if( g->flag == MASTER )
		g->timeout = MASTER_JOIN_TIMEOUT;	
	else
		g->timeout = SLAVE_JOIN_TIMEOUT;

	g->default_ttl		= ttl;
	g->member_endpoints	= NULL;
	g->grp_sock		= udp_init(addr, port, port, ttl);  //locally join group
	
	timeout.tv_sec	= 0;
	timeout.tv_usec = 0;

	param->umtp	= umtp;
	param->g	= g;
	param->timeout	= &timeout;
	
	g->state = START;
	state = pthread_create(&g->t_id, NULL, mcast_recv, (void *)param);
	if(state != 0){
		puts("Error in creating thread!");
		exit(1);
	}	
	printf("\t\t\t\t\tM CREATE THREAD [%s/%d]\n", addr, port);
  }
  time(&(g->last_time)); // update last access time  

  // Only MASTER send JOIN_GROUP request to SLAVE
  
  if( umtp->flag == MASTER && umtp->slave && g->grp_sock) 
  {	
	int bufLen = 0;
        umtp_packet join_pkt;
	umtp_header header;
        unsigned char *packet_ptr;

	join_pkt.payload = NULL;

	make_udp_send_header( &header, JOIN_GROUP, ttl, g->port, g->group,
					      umtp->slave->remote_cookie,
					      umtp->local_cookie);

        join_pkt.header = &header; 
        join_pkt.source = inet_addr(umtp->addr);
	
        packet_ptr = create_udp_payload(&join_pkt, 0, &bufLen);

	umtp->s->addr4.s_addr = umtp->slave->host;
	umtp->s->tx_port      = umtp->slave->port;
	udp_send( umtp->s, packet_ptr, bufLen);

	if(packet_ptr != NULL ) free((void *)packet_ptr);    
  }
  return g;
}

void umtp_error_notify(umtp_t umtp, uint16_t finish)
{
	char * ptr = NULL;
	umtp_endpoint *ep = NULL;

	while( umtp->active_groups == NULL )
#ifdef WIN32
        Sleep(100); // wait for registering group member
#else
        sleep(100);
#endif

	ptr = (char *)&umtp_error;
	if( umtp->active_groups != NULL )
	{
		ep = umtp->allowed_endpoints;
		for( ; ep != NULL ; ep = ep->next )
		{
			if( ep->remote_cookie ) continue; // if slave, skip
			umtp->s1->addr4.s_addr	= ep->host;
			umtp->s1->tx_port		= ep->port;
			udp_send(umtp->s1, ptr, sizeof(group_manager));
		}
	}
	notify_error = finish;
}

int* umtp_send_probe(umtp_t umtp, char *addr, uint16_t port)
{
	int bufLen = 0;
	unsigned char *packet_ptr;
	
	umtp_packet pkt;
	umtp_header header;
	umtp_endpoint *server = NULL;
			
	// 1. no need to create a new tunnel endpoint.
	// just send probe to server
	server = umtp_find_endpoint(umtp, addr, port);
	if(server == NULL)
	    umtp_add_endpoint(umtp, addr, port, (uint16_t)lrand48());
     
     ///////////////////////////////////////////
     // create a PROBE packet

	pkt.payload = NULL;

	make_udp_send_header( &header, PROBE, 0, 0, 0, server->remote_cookie, umtp->local_cookie);	

	pkt.header = &header;
	pkt.source = inet_addr(umtp->addr);	

	packet_ptr = create_udp_payload(&pkt, 0, &bufLen);	

	udp_send(umtp->s, packet_ptr, bufLen);
      
      //
      ///////////////////////////////////////////

      ///////////////////////////////////////////
      // set variables for probe sent
	
	probe_sent = 1;
	time(&last_probe_sent);

      //
      ///////////////////////////////////////////		
      
	if(packet_ptr != NULL ) free(packet_ptr);
	return &probe_sent;	
}

//uint16_t temp_cookie;
void* mcast_recv(void * arg)
{
	/* 
	4) A (non-local) multicast packet arrives for a (group, port) g,
	with source address s
	*/
	int bufLen = 0, length = 0, ttl = DEFAULT_TTL;
	unsigned char *packet_ptr;
	uint8_t buffer[UMTP_MAX_PACKET_LEN];

	umtp_t			umtp;
	umtp_header		header;
	umtp_group		*g;
	umtp_endpoint	*ep;	
	
	struct timeval  tv;
    fd_set          readfds;

	thread_param	*param;

	param	= (thread_param *)arg;
	umtp	= param->umtp;
	g		= param->g;
	
	while(1)
	{		
		uint16_t port = 0, sPort = 0;
		uint32_t fromSize;
		
		struct sockaddr_in fromAddr;
			
		if( g->state == STOP || (umtp_end == 1 && notify_error == 1) )
		{
			fprintf(umtp->log, " [mcast_recv] STOP MULTICAST THREAD for (%s/%d)\n", umtp_ntoa(g->group), g->port);
			if(param != NULL ) free(param);
			pthread_exit(arg);
		}

		tv.tv_sec  = 5;
        tv.tv_usec = 0;

        FD_ZERO(&readfds);
		FD_SET(g->grp_sock->fd, &readfds);

		if( select(g->grp_sock->fd + 1, &readfds, NULL, NULL, &tv) > 0 && FD_ISSET(g->grp_sock->fd, &readfds) )
        {
			fromSize	= sizeof(fromAddr);		
			bufLen		= recvfrom(g->grp_sock->fd, buffer, RTP_MAX_PACKET_LEN, 0, (struct sockaddr *)&fromAddr, &fromSize);
			port		= g->port;
			sPort		= ntohs(fromAddr.sin_port);			
		}
		else
			continue;
		
		// ignore multicast packet from itself
		if( fromAddr.sin_addr.s_addr == inet_addr(umtp->addr) && sPort == (umtp->port) )
			continue;		
		
		if( umtp->flag == MASTER ) // Master (Agent)
		{
			umtp_packet pkt;
 
			ep = umtp->allowed_endpoints;

			pkt.payload = buffer;
			
			make_udp_send_header( &header, DATA, ttl-1, port, g->group, ep->remote_cookie, umtp->local_cookie);

			pkt.header	= &header;
			pkt.source	= inet_addr(umtp->addr);

			packet_ptr  = create_udp_payload(&pkt, bufLen, &length);

			umtp->s->addr4.s_addr = ep->host;
			umtp->s->tx_port	  = ep->port;			
			udp_send(umtp->s, packet_ptr, length);
		}
		else // Slave (Server)
		{
			umtp_packet pkt;
				
			ep = g->member_endpoints;
			while(ep != NULL)
			{
				pkt.payload = buffer;
				
				make_udp_send_header( &header, DATA, ttl-1, port, g->group, ep->remote_cookie, umtp->local_cookie);

				pkt.header	= &header; 
				pkt.source	= inet_addr(umtp->addr);
				
				packet_ptr  = create_udp_payload(&pkt, bufLen, &length);
				
				// set destination
				umtp->s->addr4.s_addr	= ep->host;
				umtp->s->tx_port		= ep->port;
				udp_send(umtp->s, packet_ptr, length);				
				
				ep = ep->next;
			}
		}		
	}
	return NULL;
}

void* mcast_check(void * arg)
{
	umtp_group *gp;
	umtp_endpoint *ep;
	unsigned char *packet_ptr, *sbuf = NULL;
	int bufLen = 0, rcvLen = 0, sLen = 0, pLen = sizeof(m_probe);
	uint8_t buffer[UMTP_MAX_PACKET_LEN];

	int interval = 0;
	time_t now, last_time, starting_time, ending_time;

	///////////////////////////////////////////////
        // variables for select() call	
        
	struct timeval tv;
	fd_set readfds;

	//
	///////////////////////////////////////////////
	
	umtp_header header;
	umtp_t	    umtp = (umtp_t)arg;	

	///////////////////////////////////////////////
	// multicast address information
	
	char	 mc_addr[12];
	uint32_t mc_port = 50000;
	strcpy(mc_addr, "224.2.2.224");

	//
	///////////////////////////////////////////////

	time(&last_time);
	time(&starting_time);
	while(1)
	{
	    uint32_t  g_addr = 0;
	    m_probe pkt, *temp;
		
	    uint16_t  port = 0;
	    uint32_t  fromSize;
	    struct    sockaddr_in fromAddr;
	    in_addr_t s_addr_, my_addr;

	    if( umtp_end == 1 && notify_error == 1  )
	    {
		fprintf(umtp->log, " [mcast_chek]  MULTICAST CHECK THREAD STOP.\n");
		pthread_exit(arg);
	    }

	    tv.tv_sec  = MPROBE_TIMEOUT;
	    tv.tv_usec = 0;

	    FD_ZERO(&readfds);
	    FD_SET(umtp->m->fd, &readfds);
		
	    if( select(umtp->m->fd + 1, &readfds, NULL, NULL, &tv) > 0) 
	    {
			if(FD_ISSET(umtp->m->fd, &readfds)) 
			{
				memset(buffer, 0, UMTP_MAX_PACKET_LEN); // reset buffer

				fromSize	= sizeof(fromAddr);		
				bufLen	= recvfrom(umtp->m->fd, buffer, UMTP_MAX_PACKET_LEN, 0, \
							(struct sockaddr *)&fromAddr, &fromSize);		
				port	= ntohs(fromAddr.sin_port);
			}
	    }
	    else
	    {
			/////////////////////////////////////////////////////
			///   MPROBE every MPROBE_TIMEOUT seconds   /////////
			/////////////////////////////////////////////////////
				
			time(&now);
			if( now - last_time < interval ) continue;

			//////////////////////////////////////////////////////
			// MPROBE Packet
				
			pkt.type        = MPROBE;
			pkt.flag        = umtp->flag;
			pkt.destination = inet_addr(umtp->addr);
			pkt.port        = umtp->s1->rx_port;
				
			if( umtp->flag == MASTER && umtp->slave ) 
				pkt.slave_addr = umtp->slave->host;
			else
				pkt.slave_addr = 0;

			//
			//////////////////////////////////////////////////////

			bufLen     = sizeof(pkt);
			packet_ptr = (unsigned char *)&pkt;

			umtp->m->addr4.s_addr = inet_addr(mc_addr);
			umtp->m->tx_port      = mc_port;
			udp_send(umtp->m, packet_ptr, bufLen);

			if( interval < MPROBE_INTERVAL ) interval++;
			time(&last_time);			
				
			continue;
	    }

	    // ignore multicast packet from itself
	    s_addr_ = fromAddr.sin_addr.s_addr;
	    my_addr = inet_addr(umtp->addr);
	    if( s_addr_ == my_addr )
		continue;
	    else
	    {
	         // group address
			packet_ptr	= buffer;
			sbuf		= buffer;
			temp = (m_probe *)packet_ptr;

			switch (temp->type)
			{				
				case MPROBE:
					if( umtp->flag == SLAVE )
					{
						if( temp->flag == MASTER && (ep = umtp_find_endpoint_(umtp, fromAddr.sin_addr.s_addr)))
						{
							// if the sender is one of its endpoint
							// TEAR_DOWN
							umtp_packet pkt;

							pkt.payload = NULL;

							make_udp_send_header( &header, TEAR_DOWN, 0, 0, 0, 
								ep->remote_cookie, umtp->local_cookie);
								
							pkt.header	= &header;
							pkt.source	= inet_addr(umtp->addr);

							packet_ptr	= create_udp_payload(&pkt, 0, &bufLen);	
									
							// set destination
							umtp->s->addr4.s_addr	= ep->host;
							umtp->s->tx_port		= ep->port;
							udp_send(umtp->s, packet_ptr, bufLen);																					
							
							if(packet_ptr != NULL ) free(packet_ptr);

							fprintf(umtp->log, " [mcast_chek] Send TEAR DOWN to (%s/%d)\n", 
									umtp_ntoa(ep->host), ep->port);

							umtp_remove_member_in_group(umtp, ep);
							umtp_remove_endpoint_(umtp, ep->host, ep->port);

							time(&ending_time);
							//fprintf(stdout, "**************** elapsed time %d ************\n", ending_time-starting_time);
						}
						else if( temp->flag == MASTER )
						{
							// do nothing to server
							// send MPROBE_ACK with multicast group list
							temp->type = MPROBE_ACK;
							temp->flag = umtp->flag;
							temp->destination = fromAddr.sin_addr.s_addr;// put source of MPROBE
								
							bufLen		= pLen;
							packet_ptr	+= pLen;							
							for( gp = umtp->active_groups; gp != NULL; gp = gp->next )
							{								
								memcpy(packet_ptr, &(gp->group), sizeof(uint32_t));
								
								bufLen		+= sizeof(gp->group);
								packet_ptr	+= sizeof(gp->group);
							}
							packet_ptr = buffer;

							umtp->m->addr4.s_addr = inet_addr(mc_addr);
							umtp->m->tx_port	  = mc_port;
							udp_send(umtp->m, packet_ptr, bufLen);
						}
					}
					else if( umtp->flag == MASTER )
					{
						if( temp->flag == SLAVE )
						{
							if( umtp->slave->host == fromAddr.sin_addr.s_addr )
							{
								fprintf(umtp->log, " [mcast_chek] You're multicast-reachable from Server.\n");
								umtp_error.command = SERVER_REACHABLE;
								umtp_end = 1; notify_error = 1;	
								time(&ending_time);
							//fprintf(stdout, "**************** elapsed time %d ************\n", ending_time-starting_time);
							}
							else
							{
								// send MPROBE_ACK with multicast group list
								temp->type = MPROBE_ACK;
								temp->flag = umtp->flag;
								temp->destination = fromAddr.sin_addr.s_addr;// put source of MPROBE
									
								bufLen		= pLen;
								packet_ptr	+= pLen;
								for( gp = umtp->active_groups; gp != NULL; gp = gp->next )
								{
									memcpy(packet_ptr, &(gp->group), sizeof(uint32_t));
									
									bufLen		+= sizeof(uint32_t);
									packet_ptr	+= sizeof(uint32_t);
								}
								packet_ptr = buffer;

								umtp->m->addr4.s_addr = inet_addr(mc_addr);
								umtp->m->tx_port	  = mc_port;
								udp_send(umtp->m, packet_ptr, bufLen);
							}
						}						
						else if( temp->flag == MASTER )
						{
							// send MPROBE_ACK with multicast group list
							if( umtp->slave && (umtp->slave->host == temp->slave_addr) )
							{
								if( inet_addr(umtp->addr) > fromAddr.sin_addr.s_addr )
								{
									// send other Agent suspend message
									temp->type = MSUSPEND;
									temp->flag = umtp->flag;
									temp->destination = fromAddr.sin_addr.s_addr;

									packet_ptr = buffer;

									umtp->m->addr4.s_addr = inet_addr(mc_addr);
									umtp->m->tx_port	  = mc_port;
									udp_send(umtp->m, packet_ptr, bufLen);
								}
								else
								{
									// notify AG Connector other Agent's unicast socket information
									umtp_error.command = FIND_NEIGHBOR;
									umtp_error.addr	   = fromAddr.sin_addr.s_addr;
									umtp_error.port    = temp->port;

									umtp_error_notify(umtp, FALSE);									
								}
							}
							else
							{
								temp->type = MPROBE_ACK;
								temp->flag = umtp->flag;
								// put source of MPROBE
								temp->destination = fromAddr.sin_addr.s_addr;
								
									
								bufLen		= pLen;
								packet_ptr	+= pLen;
								for( gp = umtp->active_groups; gp != NULL; gp = gp->next )
								{
									memcpy(packet_ptr, &(gp->group), sizeof(uint32_t));
									
									bufLen		+= sizeof(uint32_t);
									packet_ptr	+= sizeof(uint32_t);
								}
								packet_ptr = buffer;

								umtp->m->addr4.s_addr = inet_addr(mc_addr);
								umtp->m->tx_port	  = mc_port;
								udp_send(umtp->m, packet_ptr, bufLen);
							}
						}
					}
					continue;
				case MPROBE_ACK:
					if( temp->destination != inet_addr(umtp->addr) )
						continue;
						
					if( umtp->flag == SLAVE )
					{
						if( temp->flag == MASTER )
						{
							if( ( ep = umtp_find_endpoint_(umtp, fromAddr.sin_addr.s_addr)) )
							{
								// if the sender is one of its endpoint
								// TEAR_DOWN
								umtp_packet pkt;

								pkt.payload = NULL;
								
								make_udp_send_header( &header, TEAR_DOWN, 0, 0, 0, 
									ep->remote_cookie, umtp->local_cookie);

								pkt.header	= &header; 
								pkt.source	= inet_addr(umtp->addr);

								packet_ptr	= create_udp_payload(&pkt, 0, &bufLen);	
										
								// set destination
								umtp->s->addr4.s_addr	= ep->host;
								umtp->s->tx_port		= ep->port;
								udp_send(umtp->s, packet_ptr, bufLen);
																						
								if(packet_ptr != NULL ) free(packet_ptr);

								fprintf(umtp->log, " [mcast_chek] Send TEAR DOWN to (%s/%d)\n", 
											umtp_ntoa(ep->host), ep->port);

								umtp_remove_member_in_group(umtp, ep);
								umtp_remove_endpoint_(umtp, ep->host, ep->port);
							}
							else
							{
								temp->type = MLEAVE;
								temp->flag = umtp->flag;
								temp->destination = fromAddr.sin_addr.s_addr;// put source of MPROBE_ACK

								rcvLen		= pLen;
								sLen		= pLen;
								sbuf		+= pLen;
								packet_ptr	+= pLen;
								while( rcvLen <= bufLen )
								{
									g_addr = *packet_ptr;
									if(umtp_find_groupaddr(umtp, g_addr))
									{
										memcpy(sbuf, &g_addr, sizeof(uint32_t));

										sbuf  += sizeof(uint32_t);
										sLen  += sizeof(uint32_t);
									}
									packet_ptr	+= sizeof(uint32_t);
									rcvLen		+= sizeof(uint32_t);
								}
								packet_ptr = buffer;

								umtp->m->addr4.s_addr = inet_addr(mc_addr);
								umtp->m->tx_port	  = mc_port;
								udp_send(umtp->m, sbuf, sLen);
							}
						}												
					}
					else if( umtp->flag == MASTER )
					{
						if( temp->flag == SLAVE )
						{
							if( umtp->slave->host == fromAddr.sin_addr.s_addr )
							{
								fprintf(umtp->log, " [mcast_chek] You're multicast-reachable from Server.\n");
								umtp_error.command = SERVER_REACHABLE;
								umtp_end = 1; notify_error = 1;
								continue;
							}
							else
							{
								// LEAVE Group
								rcvLen		= pLen;
								packet_ptr	+= pLen;
								while( rcvLen <= bufLen )
								{
									g_addr = *packet_ptr;
									while((gp = umtp_find_groupptr(umtp, g_addr)))
									{
										umtp_destroy_group(umtp, gp);																								
									}
									packet_ptr	+= sizeof(uint32_t);
									rcvLen		+= sizeof(uint32_t);
								}
							}
						}
						else if( temp->flag == MASTER )
						{
							// the one whose ip address is bigger wins the race
							if( temp->destination <= fromAddr.sin_addr.s_addr )
							{
								// LEAVE Group
								rcvLen		= pLen;
								packet_ptr	+= pLen;
								while( rcvLen <= bufLen )
								{
									g_addr = *packet_ptr;
									while((gp = umtp_find_groupptr(umtp, g_addr)))
									{
										umtp_destroy_group(umtp, gp);																								
									}
									packet_ptr	+= sizeof(uint32_t);
									rcvLen		+= sizeof(uint32_t);
								}								
							}
							else
							{
								// send MLEAVE to the destination
								temp->type = MLEAVE;
								temp->flag = umtp->flag;
								temp->destination = fromAddr.sin_addr.s_addr;// put source of MPROBE_ACK

								rcvLen		= pLen;
								sLen		= pLen;
								sbuf		+= pLen;
								packet_ptr	+= pLen;
								while( rcvLen <= bufLen )
								{
									g_addr = *packet_ptr;
									if(umtp_find_groupaddr(umtp, g_addr))
									{
										memcpy(sbuf, &g_addr, sizeof(uint32_t));

										sbuf  += sizeof(uint32_t);
										sLen  += sizeof(uint32_t);
									}
									packet_ptr	+= sizeof(uint32_t);
									rcvLen		+= sizeof(uint32_t);
								}
								packet_ptr = buffer;

								umtp->m->addr4.s_addr = inet_addr(mc_addr);
								umtp->m->tx_port	  = mc_port;
								udp_send(umtp->m, sbuf, sLen);
							}
						}
					}					
					continue;
				case MLEAVE:
					if( temp->destination != my_addr )
						continue;
					fprintf(umtp->log, " [mcast_chek] RECV MLEAVE\n");

					if( umtp->flag == MASTER )
					{
						rcvLen		= pLen;
						packet_ptr	+= pLen;
						for( ; rcvLen <= bufLen; rcvLen += sizeof(uint32_t))
						{
							g_addr = *packet_ptr;
							// remove all groups with g_addr
							while((gp = umtp_find_groupptr(umtp, g_addr)))
								umtp_destroy_group(umtp, gp);
							packet_ptr += sizeof(uint32_t);
						}
					}
					continue;
				case MSUSPEND:
					if( umtp->flag == MASTER && temp->flag == MASTER )
					{
						// notify AG Connector other Agent's unicast socket information
						umtp_error.command = FIND_NEIGHBOR;
						umtp_error.addr	   = fromAddr.sin_addr.s_addr;
						umtp_error.port    = temp->port;

						umtp_error_notify(umtp, FALSE);	
					}
				default:
					continue;
			}
		}
	}
	return NULL;
}

void* ucast_recv(void * arg)
{
    int bufLen = 0;
    unsigned char *packet_ptr;
    uint8_t buffer[UMTP_MAX_PACKET_LEN];	

    umtp_t umtp = (umtp_t)arg;
    umtp_header header;

    struct timeval  tv;
    fd_set readfds;
	
    while(1)
    {
	unsigned short	port = 0;
	uint32_t	fromSize;
	u_char		ttl = 0;
	struct		sockaddr_in fromAddr;
	group_manager	*gm;

	if( umtp_end == 1 && notify_error == 1 )
	{
	    fprintf(umtp->log, " [ucast_recv]   UNICAST THREAD STOP.\n");
	    pthread_exit(arg);
	}

	tv.tv_sec  = 5;
        tv.tv_usec = 0;

        FD_ZERO(&readfds);
        FD_SET(umtp->s1->fd, &readfds);

	if( select(umtp->s1->fd + 1, &readfds, NULL, NULL, &tv) > 0  \
		&& FD_ISSET(umtp->s1->fd, &readfds) )
	{
	    memset(buffer, 0, UMTP_MAX_PACKET_LEN); // reset buffer

	    fromSize	= sizeof(fromAddr);
	    bufLen	= recvfrom(umtp->s1->fd, buffer, UMTP_MAX_PACKET_LEN, 0, \
									(struct sockaddr *)&fromAddr, &fromSize);
	    port	= ntohs(fromAddr.sin_port);
	}
	else
	    continue;

	// group address
	gm = (group_manager *)buffer;

	if( umtp->flag == MASTER )
	{
	    umtp_group *g;
	    umtp_endpoint *ep = NULL, *rep = NULL;

	    // create a new endpoint - only has address and port info
	    if( ep == NULL )
	    {
		ep = malloc(sizeof(umtp_endpoint));
		memset(ep, 0, sizeof(umtp_endpoint));
		ep->host = fromAddr.sin_addr.s_addr;
		ep->port = ntohs(fromAddr.sin_port);
	    }
			
	    if( gm->command == 0 )
	    {
		//printf(" [ucast_recv] %s, %d\tS JOIN_GROUP\n", umtp_ntoa(gm->addr), gm->port);
		ep = umtp_add_endpoint_(umtp, ep->host, ep->port, 0);
		g  = umtp_join_group(umtp, umtp_ntoa(gm->addr), gm->port, ttl);			
		umtp_add_member(g, ep);
	    }
	    else
	    {
		g = umtp_find_group_(umtp, gm->addr, gm->port);
				
		rep = umtp_find_member(g, ep);				
		umtp_remove_member(g, rep);				

		// remove umtp_group and send LEAVE_GROUP to server
		if( g->member_endpoints == NULL )
		{   
		    umtp_packet pkt;
		    umtp_endpoint *server;
					
		    //printf(" [ucast_recv] %s, %d\tS LEAVE_GROUP\n", umtp_ntoa(gm->addr), gm->port);
		    server		= umtp->allowed_endpoints;

		    pkt.payload = NULL;

		    make_udp_send_header( &header, LEAVE_GROUP, ttl, g->port, g->group, \
		    umtp->slave->remote_cookie, umtp->local_cookie);

		    pkt.header = &header; 
		    pkt.source = inet_addr(umtp->addr);

		    packet_ptr = create_udp_payload(&pkt, 0, &bufLen);	

		    umtp->s->addr4.s_addr = umtp->slave->host;
		    umtp->s->tx_port	  = umtp->slave->port;
		    udp_send(umtp->s, packet_ptr, bufLen);											
					
		    if(packet_ptr != NULL ) free(packet_ptr);
					
		    // Agent removes information about this group
		    umtp_leave_group(umtp, g);
		}				
	    }					
	}
    }
    return NULL;
}

void umtp_update(umtp_t umtp)
{
	/* 
	* This function just iterates through the structures and looks
	* for things to clean up.
	*/

	time_t now;
	umtp_group *temp = NULL, *group;
	umtp_endpoint *temp_e = NULL, *ep;

	group = umtp->active_groups;

	while(group != NULL) 
	{		
		time(&now);
		temp = group->next;
		if ((now - group->last_time) > group->timeout) 
		{			
			if(umtp->flag) // slave - cleanup				
				umtp_destroy_group(umtp, group);
			else  // master - send update
				umtp_join_group(umtp, umtp_ntoa(group->group), group->port, group->default_ttl);			
		}
		group = temp;
	}

	ep = umtp->allowed_endpoints;
	while(umtp->flag && ep != NULL)
	{
		time(&now);
		temp_e = ep->next;
		if((now - ep->last_time) > MASTER_JOIN_TIMEOUT)
		{
			// remove member from groups
			group = umtp->active_groups;
			while( group != NULL )
			{
				umtp_remove_member(group, ep);
				group = group->next;
			}
			// remove endpoint from allowed endpoints
			umtp_remove_endpoint(umtp, umtp_ntoa(ep->host), ep->port);
		}
		ep = temp_e;
	}
	fflush(umtp->log);
}

void umtp_done(umtp_t umtp)
{
	void *thr_retval;

	if( umtp->flag == MASTER && umtp_error.command ) // notify user about error
		umtp_error_notify(umtp, TRUE);

	umtp_end = 1;
	if( umtp->active_groups != NULL )
	{
		umtp_group *g, *temp = NULL;
		
		fprintf(umtp->log, " [umtp__done] REMOVE GROUPS\n");
		g = umtp->active_groups;
		while( g != NULL )
		{
			temp = g->next;
			fprintf(umtp->log, " [umtp__done] REMOVE GROUP (%s/%d)\n", umtp_ntoa(g->group), g->port);
		    umtp_destroy_group(umtp, g);
			g    = temp;	
		}
	}

	if( umtp->allowed_endpoints != NULL )
	{
		int bufLen = 0;
		umtp_packet pkt;
		umtp_header header;
		unsigned char *packet_ptr = NULL;
		struct in_addr saddr;	
			
		// send TEAR_DOWN to every user or server
		umtp_endpoint *temp = NULL, *ep = umtp->allowed_endpoints;

		fprintf(umtp->log, " [umtp__done] REMOVE ENDPOINTS\n");
		while( ep != NULL )
		{
			if( ep->host != inet_addr(umtp->addr) && ep->remote_cookie != 0)
			{
				fprintf(umtp->log, " [umtp__done] TEAR_DOWN to %s\n", umtp_ntoa(ep->host));
				saddr.s_addr = (in_addr_t)ep->host;

				pkt.payload = NULL;

				make_udp_send_header( &header, TEAR_DOWN, 0, 0, 0, 
								ep->remote_cookie,
								umtp->local_cookie);

				pkt.header	= &header; 
				pkt.source	= inet_addr(umtp->addr);

				packet_ptr  = create_udp_payload(&pkt, 0, &bufLen);	

				umtp->s->addr4.s_addr	= ep->host;
				umtp->s->tx_port		= ep->port;
				udp_send(umtp->s, packet_ptr, bufLen);												
				
				if(packet_ptr != NULL ) free(packet_ptr);
			}			
			temp = ep->next;
			umtp_remove_endpoint_(umtp, ep->host, ep->port);			
			ep   = temp;
		}
	}

	fprintf(umtp->log, " [umtp__done] REMOVE SOCKETS...\n");		

	fprintf(umtp->log, " [umtp__done] 1. UNICAST SOCKET\n");
	fprintf(umtp->log, " [umtp__done]    WAIT FOR UNICAST SOCKET CLOSE...\n");
	pthread_join(umtp->u_id, &thr_retval);
	if( umtp->s1 != NULL )	udp_exit(umtp->s1);
	fprintf(umtp->log, " [umtp__done]    DONE.\n");
	
	if(umtp->mstate == MPROBE_START )
	{
		fprintf(umtp->log, " [umtp__done] 2. MULTICAST CHECK SOCKET\n");
		fprintf(umtp->log, " [umtp__done]    WAIT FOR MULTICAST CHECK SOCKET CLOSE...\n");
		pthread_join(umtp->m_id, &thr_retval);		
		if( umtp->m  != NULL )	udp_exit(umtp->m);
		fprintf(umtp->log, " [umtp__done]    DONE.\n");
	}

	fprintf(umtp->log, " [umtp__done] 3. UMTP SOCKET\n");
	fprintf(umtp->log, " [umtp__done]    WAIT FOR UMTPSOCKET SOCKET CLOSE...\n");
	if( umtp->s  != NULL )	udp_exit(umtp->s);
	fprintf(umtp->log, " [umtp__done]    DONE.\n");	

	if(umtp->addr != NULL ) free(umtp->addr);
	if(umtp->log != NULL) fclose(umtp->log);
	if(umtp != NULL ) free(umtp);

	ring_buf_close();

	printf(" [umtp__done] UMTP ENDS.\n");
}
