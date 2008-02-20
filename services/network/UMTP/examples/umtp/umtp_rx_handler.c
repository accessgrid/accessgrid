#include "config_unix.h"
#include "config_win32.h"
#include "net_udp.h"
#include "rtp.h"

#include "ring_buf.h"
#include "umtp.h"
#include "umtp_util.h"
#include "umtp_rx_handler.h"

extern int probe_sent;

// 버퍼의 내용을 이용해 umtp_packet을 만든다
umtp_packet buffer_to_umtp_packet(char* buffer, int packet_len)
{
	int           payload_len;
	unsigned char *packetptr = NULL;

	umtp_packet   umtp_p;
	umtp_header   *umtp_h = NULL;
	
	// umtp payload
	packetptr       = (unsigned char *)buffer;
	umtp_p.payload	= packetptr;
	payload_len	= packet_len - sizeof(umtp_header) - sizeof(uint32_t);

	// umtp header
	packetptr	+= payload_len;
	umtp_h		= (umtp_header *)packetptr;
	umtp_p.header	= umtp_h;

	// umtp source
	if(umtp_h->source) {
		packetptr	+= sizeof(umtp_header);
		umtp_p.source 	= (uint32_t)packetptr;
	}

	return umtp_p;
}

int do_if_sender(umtp_t umtp, umtp_endpoint *sender, char *buffer, uint32_t buf_len, umtp_packet *umtp_p, source_info *src)
{
	int      payload_len;

	uint32_t m_addr;
	uint16_t m_port;
	
	uint32_t send_size;
	uint16_t cmd, ttl;

	unsigned char  *addr;
	umtp_header    *umtp_h;
	umtp_group     *g;

	umtp_h  = umtp_p->header;

	cmd	= umtp_h->command;
	m_addr	= umtp_h->multicast_address;
	m_port	= umtp_h->port;
	ttl	= umtp_h->ttl - 1;

	payload_len = buf_len - sizeof(umtp_header) - sizeof(uint32_t);

	if( sender->local_cookie == umtp_h->destination_cookie ) {
	    if( cmd != DATA )					
		    fprintf(umtp->log, " [umtp__recv] %s, %d\t", umtp_ntoa(src->src_addr), src->src_port);
		
		switch (cmd) { /*  Process the packet, based on the "command" field: */
			case DATA: // send it to multicast address and to other UMTP Agents
				// send to multicast address
				do_udp_send(umtp->s, buffer, payload_len, m_addr, m_port);
				
				if( umtp->flag == SLAVE ) { // send to other UMTP Agents
					umtp_group*    group;
					umtp_endpoint* gep;

					group = umtp_find_group_(umtp, m_addr, m_port);
					
					if( group)  gep   = group->member_endpoints;
					else		break; // if group doesn't exist, stop sending

					for( ; gep != NULL; gep = gep->next) {
						umtp_packet   pkt;
						unsigned char *pkt_ptr;
						umtp_header    header;	

						if( gep->host == src->src_addr && gep->port == src->src_port )
							continue;
						else {
							make_udp_send_header( &header, DATA, ttl -1, m_port, m_addr, gep->remote_cookie, umtp->local_cookie);
								
							pkt.header  = &header;
							pkt.payload = umtp_p->payload;							
							pkt.source  = inet_addr(umtp->addr);

							// do not free pkt_ptr; if payload is not empty
							// receiving buffer is used instead of allocating new memory space
							pkt_ptr = create_udp_payload(&pkt, payload_len, &send_size);
							do_udp_send(umtp->s, pkt_ptr, send_size, gep->host, gep->port);
						}
					}
				}
				break;
			case JOIN_GROUP: //JOIN_GROUP(group, m_port, t)
				fprintf(umtp->log, "- JOIN GROUP [%s/%d]\n", umtp_ntoa(m_addr), m_port);
				addr = umtp_ntoa(umtp_h->multicast_address);
				if(addr != NULL) {
					time(&(sender->last_time));
					g = umtp_join_group(umtp, addr, umtp_h->port, umtp_h->ttl);
					umtp_add_member(g, sender);
				}	
				break;
			case LEAVE_GROUP: //LEAVE_GROUP(group, m_port)
				fprintf(umtp->log, "- LEAVE GROUP [%s/%d]\n", umtp_ntoa(m_addr), m_port); 

				if( (g = umtp_find_group_(umtp, umtp_h->multicast_address, umtp_h->port)) ) {
					if( umtp->flag == SLAVE ) {
						umtp_remove_member(g, sender);
						umtp_leave_group(umtp, g);
					}
				}
				break;
			case TEAR_DOWN: //TEAR_DOWN
				fprintf(umtp->log, "- TEAR DOWN\n");
				if( umtp->flag == SLAVE ) {
					umtp_remove_member_in_group(umtp, sender);
					umtp_remove_endpoint_(umtp, sender->host, sender->port);
				}
				else
					umtp_end = 1;					
				break;
			case PROBE: //PROBE
				/* 
				if the sender is in allowed_endpoints list 
				and it knows the cookie, then no need to send reply
				*/
				fprintf(umtp->log, "- PROBE\n");					
				break;
			case PROBE_ACK: // PROBE_ACK
				fprintf(umtp->log, "- PROBE ACK[%d]\n", umtp_h->source_cookie);					
				sender->remote_cookie = umtp_h->source_cookie;
				umtp->slave = sender;
				probe_sent = 2;
				return PROBE_ACK; // return PROBE_ACK to confirm sending
			case PROBE_NACK: //PROBE_NACK
				fprintf(umtp->log, "- PROBE NACK\n");
				break;
			default:
				fprintf(umtp->log, "- WRONG COMMAND [%d]\n", cmd);
				break;
		}
	}
	else 
	{
		// If dstCookie does *not* equal localCookie_s: 
		umtp_packet   pkt;
		unsigned char *pkt_ptr;
		umtp_header    header;	
			
		// Even if sender is in allowed endpoint list, if the sender recently restart the agent,
		// the sender can not know its local cookie
		// Temporarily print out to screen
		fprintf(umtp->log, " [umtp__recv] %s, %d\t", umtp_ntoa(src->src_addr), src->src_port);
		fprintf(umtp->log, "* COOKIE ERROR (LEN:%d)\n", buf_len);

		// Update cookie information of sender. 
		// Sender can be restarted, and doesn't know its previous cookie.
		// Sender's cookie informaton is a new one. Need to store
		if( cmd == PROBE )
			sender->remote_cookie = umtp_h->source_cookie;

		make_udp_send_header( &header, PROBE_ACK, 0, 0, 0, umtp_h->source_cookie, umtp->local_cookie);

		pkt.payload = NULL;
		pkt.header  = &header;
		pkt.source  = inet_addr(umtp->addr);
				
		pkt_ptr	    = create_udp_payload(&pkt, 0, &send_size);		
		do_udp_send(umtp->s, pkt_ptr, send_size, src->src_addr, src->src_port); // use received size

		if(pkt_ptr != NULL ) free(pkt_ptr);

		return PROBE; // return PROBE to confirm sending
	}
	return 0; 
}

int do_if_not_sender(umtp_t umtp, uint32_t buf_len, umtp_packet *umtp_p, source_info *src)
{
	uint32_t m_addr;
	uint16_t m_port, cmd;

	umtp_header    *umtp_h;

	umtp_h  = umtp_p->header;

	cmd	= umtp_h->command;
	m_addr	= umtp_h->multicast_address;
	m_port	= umtp_h->port;

	if( cmd == DATA )
		return FALSE;
	else		
		fprintf(stdout, " [umtp_handl] %s, %d\t", umtp_ntoa(src->src_addr), src->src_port);

	if( cmd == PROBE) 
	{
		fprintf(umtp->log, "O PROBE[%d:%d]\n", umtp->local_cookie, umtp_h->source_cookie);
		if( umtp->flag == SLAVE )
		{
			unsigned char *pkt_ptr;

			umtp_h->command			= PROBE_ACK;				
			umtp_h->destination_cookie	= umtp_h->source_cookie;
			umtp_h->source_cookie		= umtp->local_cookie;

			pkt_ptr = umtp_p->payload;
			do_udp_send(umtp->s, pkt_ptr, buf_len, src->src_addr, src->src_port);

			return PROBE; // return PROBE_ACK to confirm sending
		}
	}
	else if( cmd == JOIN_GROUP )
	{
		// cookie matches
		fprintf(umtp->log, "+ JOIN_GROUP [%s/%d]\n", umtp_ntoa(m_addr), m_port);
		if( umtp->local_cookie == umtp_h->destination_cookie )
		{
			umtp_group *g;
			umtp_endpoint *ep;
			
			char *addr = umtp_ntoa(src->src_addr);
			ep = umtp_add_endpoint(umtp, addr, src->src_port, umtp_h->source_cookie);	

			time(&(ep->last_time));

			g  = umtp_join_group(umtp, umtp_ntoa(m_addr), m_port, umtp_h->ttl);
			umtp_add_member(g, ep);
		}
		return JOIN_GROUP;
	}
	else
	{
		fprintf(umtp->log, "+ WRONG COMMAND [%d, %d, %d, %d, %d]\n", cmd, \
				umtp->local_cookie, umtp_h->source_cookie, umtp_h->destination_cookie, buf_len);
			
		return FALSE;
	}
	return 0;
}

// 버퍼에 저장되어 있는 umtp packet을 꺼내어 해당하는 처리를 한다.
// 쓰레드로 동작
void* umtp_rx_handler(void* arg)
{
	source_info src;
	umtp_packet umtp_p;

	umtp_endpoint *sender    = NULL;
	
	int	packet_len;
	char	buffer[UMTP_MAX_PACKET_LEN];

	umtp_t umtp = (umtp_t)arg;

	while(1) {
		memset(buffer, 0, sizeof(buffer));	// reset buffer

		if( umtp_end == 1) {
			fprintf(umtp->log, " [proc___pkt] STOP PKT BUFFER PROCESSING THREAD\n");
			pthread_exit(arg);
		}		

		packet_len = get_ring(buffer, &src);		
		
		if( src.src_addr == inet_addr(umtp->addr)) { 
			umtp_end = 1; // If it receives packet from itself, shutdown
		}

		umtp_p = buffer_to_umtp_packet(buffer, packet_len);
		sender = umtp_find_endpoint__(umtp, src.src_addr, src.src_port);

		if( sender ) /* If s(sender) is one of the endpoints e in E */
			do_if_sender(umtp, sender, buffer, packet_len, &umtp_p, &src);
		else 
			do_if_not_sender(umtp, packet_len, &umtp_p, &src);
	}
	
	return FALSE;	
}
