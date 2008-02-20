#include "config_unix.h"
#include "config_win32.h"
#include "debug.h"
#include "memory.h"
#include "net_udp.h"
#include "pthread.h"

#include "umtp.h"
#include "umtp_util.h"

void do_udp_send(socket_udp *s, char * buffer, int buf_len, uint32_t address, uint16_t port)
{
	s->addr4.s_addr = address;
	s->tx_port	= port;

	udp_send(s, buffer, buf_len);
}

void make_udp_send_header( umtp_header *hdr, 
							 unsigned short cmd, unsigned short ttl, 
							 unsigned short port, uint32_t mcast_addr, 
							 uint16_t dest_cookie, uint16_t src_cookie)
{
	memset(hdr, 0, sizeof(umtp_header));

	hdr->command			= cmd;
	hdr->version			= 3;
	hdr->source				= 1;
	hdr->ttl				= ttl;
	hdr->port				= port;
	hdr->multicast_address	= mcast_addr;
	hdr->destination_cookie = dest_cookie;
	hdr->source_cookie		= src_cookie;	
}

uint32_t umtp_find_groupaddr(umtp_t umtp, uint32_t g_addr)
{
	umtp_group *gp;
	for(gp = umtp->active_groups; gp != NULL; gp = gp->next)
	{
		if( gp->group == g_addr)
			return g_addr;
	}
	return 0;
}

umtp_group* umtp_find_groupptr(umtp_t umtp, uint32_t g_addr)
{
	umtp_group *gp;
	for(gp = umtp->active_groups; gp != NULL; gp = gp->next)
	{
		if( gp->group == g_addr) return gp;
	}
	return NULL;
}

umtp_endpoint* 
umtp_add_endpoint(umtp_t umtp, char *addr, uint16_t port, uint16_t remote_cookie)
{
	umtp_endpoint *ep, *cep = umtp->allowed_endpoints;
    
	ep = umtp_find_endpoint(umtp, addr, port);
	if( ep == NULL )
	{
		ep = malloc(sizeof(umtp_endpoint));
		memset(ep, 0, sizeof(umtp_endpoint));

		ep->host			= (uint32_t)inet_addr(addr);
		ep->port			= port;
		ep->local_cookie	= umtp->local_cookie;
		ep->remote_cookie	= remote_cookie;
		ep->ep_sock			= umtp->s;

		if (cep != NULL) 
		{
			while(cep->next != NULL)
				cep = cep->next;
			cep->next = ep;
		} 
		else 
			umtp->allowed_endpoints = ep;
	}
	return ep;
}

umtp_endpoint* 
umtp_add_endpoint_(umtp_t umtp, uint32_t addr, uint16_t port, uint16_t remote_cookie)
{
	umtp_endpoint *ep, *cep = umtp->allowed_endpoints;
    
	ep = umtp_find_endpoint__(umtp, addr, port);
	if( ep == NULL )
	{
		ep = malloc(sizeof(umtp_endpoint));
		memset(ep, 0, sizeof(umtp_endpoint));

		ep->host			= addr;
		ep->port			= port;
		ep->local_cookie	= umtp->local_cookie;
		ep->remote_cookie	= remote_cookie;
		ep->ep_sock			= umtp->s;

		if (cep != NULL) 
		{
			while(cep->next != NULL)
				cep = cep->next;
			cep->next = ep;
		} 
		else 
			umtp->allowed_endpoints = ep;
	}
	return ep;
}

void umtp_remove_endpoint(umtp_t umtp, char *addr, uint16_t port)
{
	umtp_endpoint *prev = NULL, *epsearchlist = NULL;
	umtp_endpoint *ep = umtp_find_endpoint(umtp, (char *)addr, port);	

	epsearchlist = umtp->allowed_endpoints;
	while( epsearchlist != NULL )
	{
		if( epsearchlist->host == ep->host && epsearchlist->port == ep->port )
		{
			if( prev )
				prev->next = epsearchlist->next;
			else
				umtp->allowed_endpoints = epsearchlist->next;
			free(epsearchlist);	
			
			printf(" [remove__ep] REMOVE ENDPOINT (%s/%d)\n", umtp_ntoa(epsearchlist->host), epsearchlist->port);
			break;
		}
		else
		{
			prev		 = epsearchlist;
			epsearchlist = epsearchlist->next;
		}
	}
}

void umtp_remove_endpoint_(umtp_t umtp, uint32_t addr, uint16_t port)
{
	umtp_endpoint *prev = NULL, *epsearchlist = NULL;
	umtp_endpoint *ep = umtp_find_endpoint__(umtp, addr, port);

	epsearchlist = umtp->allowed_endpoints;
	while( epsearchlist != NULL )
	{
		if( epsearchlist->host == ep->host && epsearchlist->port == ep->port )
		{
			if( prev )
				prev->next = epsearchlist->next;
			else
				umtp->allowed_endpoints = epsearchlist->next;
			free(epsearchlist);
			break;
		}
		else
		{
			prev		 = epsearchlist;
			epsearchlist = epsearchlist->next;
		}
	}
}

umtp_endpoint *umtp_find_endpoint(umtp_t umtp, char *addr, uint16_t port)
{
	uint32_t host = (uint32_t)inet_addr(addr);
	umtp_endpoint *epsearchlist = umtp->allowed_endpoints;
	for( ; epsearchlist != NULL; epsearchlist = epsearchlist->next )
		if( epsearchlist->host == host && epsearchlist->port == port )
			return epsearchlist;

	return NULL;
}

umtp_endpoint*	umtp_find_endpoint_(umtp_t umtp, uint32_t addr)
{
	umtp_endpoint *epsearchlist = umtp->allowed_endpoints;
	for( ; epsearchlist != NULL; epsearchlist = epsearchlist->next )
		if( epsearchlist->host == addr ) return epsearchlist;

	return NULL;
}

umtp_endpoint*	umtp_find_endpoint__(umtp_t umtp, uint32_t addr, uint16_t port)
{
	umtp_endpoint *epsearchlist = umtp->allowed_endpoints;
	for( ; epsearchlist != NULL; epsearchlist = epsearchlist->next )
		if( epsearchlist->host == addr && epsearchlist->port == port ) return epsearchlist;

	return NULL;
}

umtp_endpoint* umtp_add_member(umtp_group *g, umtp_endpoint *ep)
{
	umtp_endpoint *member, *e	= NULL;
	
	if((e = umtp_find_member(g, ep)))
	{
		// check if ep is already a member of g
		member = e;		
	}
	else
	{
		// copy contents of ep into member
		member	= malloc(sizeof(umtp_endpoint));
		memset(member, 0, sizeof(umtp_endpoint));

		member->host			= ep->host;
		member->port			= ep->port;
		member->local_cookie	= ep->local_cookie;
		member->remote_cookie	= ep->remote_cookie;
		member->ep_sock			= ep->ep_sock;
		member->next			= NULL;

		if( g->member_endpoints != NULL )
		{
			e = g->member_endpoints;
			while(e->next != NULL) 
			{ 
				e = e->next;
			}
			e->next = member; // to allocate a value to e->next we should compare e->next
		}
		else
			g->member_endpoints = member;			
	}
	time(&(g->last_time));

	return member;
}

void umtp_remove_member(umtp_group *g, umtp_endpoint *ep)
{
	uint32_t addr = 0; uint16_t port = 0;
	umtp_endpoint *e, *prev	= NULL;

	e = g->member_endpoints;
	while( e != NULL )
	{
		if( e->host == ep->host && e->port == ep->port )
			break;
		else
		{
			prev	= e;
			e		= e->next;
		}
	}

	if( e == NULL )
		printf(" [remove_mem] NO MATCHING MEMBER (%s/%d).\n", umtp_ntoa(ep->host), ep->port);
	else
	{
		addr = e->host; port = e->port;

		if( prev )
			prev->next = e->next;
		else
			g->member_endpoints = e->next;
	
		free(e);
		printf(" [remove_mem] REMOVE (%s/%d)", umtp_ntoa(addr), port);
		printf(" in (%s/%d)\n", umtp_ntoa(g->group), g->port);
	}
}

void umtp_remove_member_in_group(umtp_t umtp, umtp_endpoint *ep)
{
	umtp_group *g = umtp->active_groups;

	for( ; g != NULL ; g = g->next )
		umtp_remove_member(g, ep);
}

void umtp_remove_group(umtp_t umtp, umtp_group *g)
{
	// find group in the active groups list 
	// and free memory allocation
	umtp_group *prev = NULL, *temp = NULL, *gpsearchlist = NULL;

	gpsearchlist = umtp->active_groups;
	while( gpsearchlist != NULL )
	{
		temp = gpsearchlist->next;
	    if( gpsearchlist->group == g->group && gpsearchlist->port == g->port )
		{
			if( prev )
				prev->next = temp;
			else
				umtp->active_groups = temp;
			free(g);
			break;
		}
		else
			prev		 = gpsearchlist;
		gpsearchlist = temp;
	}
}

// find a member in a group that matches designated endpoint
umtp_endpoint* umtp_find_member(umtp_group *g, umtp_endpoint *ep)
{
	umtp_endpoint *ge, *e = NULL;
	
	ge = g->member_endpoints;	
	while( ge != NULL)
	{
		if(ge->host == ep->host && ge->port == ep->port)
		{
			e = ge;
			break;
		}
		else
			ge = ge->next;
	}

	return e;
}

umtp_group *umtp_find_group(umtp_t umtp, char *addr, uint16_t port)
{
	uint32_t group = (uint32_t)inet_addr(addr);
	umtp_group *gpsearchlist = umtp->active_groups;
	for( ; gpsearchlist != NULL; gpsearchlist = gpsearchlist->next )
		if( gpsearchlist->group == group && gpsearchlist->port == port )
			return gpsearchlist;

	return NULL;
}

umtp_group* umtp_find_group_(umtp_t umtp, uint32_t addr, uint16_t port)
{
	umtp_group *gpsearchlist = NULL;

	gpsearchlist = umtp->active_groups;
	while( gpsearchlist != NULL )
	{		
		if( gpsearchlist->group == addr && gpsearchlist->port == port )
				return gpsearchlist;
		gpsearchlist = gpsearchlist->next;
	}
	
	return NULL;
}

void umtp_leave_group(umtp_t umtp, umtp_group *g)
{	
	// check member existence
	if( g->member_endpoints == NULL )
	{
		// destroy group if no member exists
		umtp_destroy_group(umtp, g);	
	}
}

void umtp_destroy_group(umtp_t umtp, umtp_group *g)
{	
	void *thr_retval;
	uint32_t group = 0; uint16_t port = 0;
	umtp_endpoint *ep, *temp = NULL;

	// remove member endpoints in this group	
	ep = g->member_endpoints;
	while(ep != NULL)
	{
		temp = ep->next; // ep will destroy, store e->next
		umtp_remove_member(g, ep);
		ep   = temp;
	}

	group    = g->group; port = g->port;
	g->state = STOP;			// stop thread
	pthread_join(g->t_id, &thr_retval);	
	if( g->grp_sock ) udp_exit(g->grp_sock); // locally leave mcast group g
	umtp_remove_group(umtp, g); // remove group from active_groups	
	printf(" [destroy__g] DESTROY GROUP (%s/%d)\n", umtp_ntoa(group), port);
}

char* umtp_ntoa(uint32_t addr)
{
	struct in_addr saddr;
	saddr.s_addr = addr;

	return inet_ntoa(saddr);
}

void send_packet(umtp_t umtp, uint32_t addr, uint16_t port, char* ptr, int ptr_len)
{
	uint32_t temp;

	temp = umtp->s->addr4.s_addr;

	umtp->s->addr4.s_addr = addr;
	umtp->s->tx_port 	  = port;

	udp_send(umtp->s, ptr, ptr_len);

	umtp->s->addr4.s_addr = temp;
}

char *umtp_host_addr(char* hname)
{		
	struct hostent 		*hent;
	struct in_addr  	 iaddr;
	
	hent = gethostbyname(hname);
	if (hent == NULL) {
		fprintf(stderr, "Can't resolve IP address for %s", hname);
		return NULL;
	}

	assert(hent->h_addrtype == AF_INET);
	memcpy(&iaddr.s_addr, hent->h_addr, sizeof(iaddr.s_addr));	

	
	return strdup(inet_ntoa(iaddr));
}

int umtp_addr_valid(char *dst)
{
    struct in_addr addr4;
	struct hostent *h;

	if (inet_pton(AF_INET, dst, &addr4)) {
		return TRUE;
	} 

	h = gethostbyname(dst);
	if (h != NULL) {
		return TRUE;
	}
	fprintf(stderr, "Can't resolve IP address for %s", dst);

    return FALSE;
}

void print_umtp_members(umtp_t umtp)
{
	int i;
	umtp_endpoint* ep = umtp->allowed_endpoints;
	for(i = 1; ep != NULL; ep = ep->next, i++)
	{
		fprintf(umtp->log, "  %d: [%s, %d]\n", i, umtp_ntoa(ep->host), ep->port); 
	}
}

void print_umtp_groups(umtp_t umtp)
{
	int i, j;
	umtp_endpoint *ep = NULL;

	umtp_group* gp = umtp->active_groups;
	for(i = 1; gp != NULL; gp = gp->next, i++)
	{		
		fprintf(umtp->log, "  [#%d] %s/%d\n", i, umtp_ntoa(gp->group), gp->port);

		ep = gp->member_endpoints;
		for(j = 1; ep != NULL; j++)
		{
			fprintf(umtp->log, "\t+ %s/%d\n", umtp_ntoa(ep->host), ep->port); 
			ep = ep->next;
		}
	}
	if( i == 1 )
		fprintf(umtp->log, "\tThere are no groups.\n");
}

char* create_udp_payload(umtp_packet *pkt, int pLen, int * sbufLen)
{
	char * sbuf = NULL;
	int len = 0, payloadLen = 0, headerLen = 0, uintLen = 0;
	
	uintLen		= sizeof(uint32_t);
	headerLen	= sizeof(umtp_header);	

	if(pkt->payload != NULL) 
	{		
		payloadLen	= pLen;		
		len			= payloadLen + headerLen + uintLen;
		
		sbuf = pkt->payload;	

		memcpy(sbuf + payloadLen, (void *)pkt->header, headerLen);
		memcpy(sbuf + payloadLen + headerLen, (void *)&(pkt->source), uintLen);		
	}
	else
	{
		len = headerLen + uintLen;

		sbuf = malloc(len);
		memset(sbuf, 0, len);
		
		memcpy(sbuf, (void *)pkt->header, sizeof(struct umtp_header));
		memcpy(sbuf + headerLen, (void *)&(pkt->source), sizeof(uint32_t));
	}
	*sbufLen = len; // return buffer length
	return sbuf;
}
