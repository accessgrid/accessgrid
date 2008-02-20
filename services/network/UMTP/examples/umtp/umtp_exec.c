#ifndef WIN32
#include <sys/time.h>
#include <inttypes.h>
#include <unistd.h>
#endif

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>

#include "config_unix.h"
#include "config_win32.h"
#include "memory.h"
#include "debug.h"
#include "net_udp.h"

#include "ring_buf.h"
#include "umtp.h"
#include "umtp_util.h"

#define TIMEOUTSECS 600 

static void umtp_handler(umtp_packet *packet);

struct umtp *session = NULL;

static void umtp_handler(umtp_packet *packet)
{
	print_umtp_packet(packet);
}

static void signal_handler(int sig) 
{
	umtp_error.command = RECV_SIGTERM;
	umtp_end = 1;
	printf(" [___umtp___] SHUTDOWN UMTP...\n");
}

int
main(int argc, char *argv[])
{
	int *probe_sent = 0, probe_count = 0;
	int ac = 1, port = 0,t_port = 0, t_mode = 0, timeout = 0;
	char *address = NULL, *type, *t_addr = NULL;
	time_t last_time, now;
	
	umtp_flag flag;	
	m_probe_state mprobe_state = MPROBE_START;

	if( argc < 4 ) 
	{
		fprintf(stdout, "Usage: umtp [-s|-m] <hostname> <port> [<mcast group address> <mcast group port>]\n");
		exit(EXIT_SUCCESS);
	}
	type	= argv[ac++];
	address	= argv[ac++];
	port	= atoi(argv[ac++]);

	if( argc > 4 )
	{
		t_mode = 1; // set test mode
		t_addr = argv[ac++];
		t_port = atoi(argv[ac++]);
		if (argc == 7 ) mprobe_state = MPROBE_STOP;
	}

	if( strcmp(type, "-s") == 0 )		
	{
		flag = SLAVE;	// Slave
		timeout = SLAVE_JOIN_TIMEOUT;
	}
	else if( strcmp(type, "-m") == 0)
	{
		flag = MASTER;	// Master		
		timeout = MASTER_JOIN_TIMEOUT;
	}
	else 
	{
		fprintf(stdout, "Wrong Usage!!! Exit program!!!\n");
		exit(EXIT_SUCCESS);
	}
	
	session = umtp_init(address, port, flag, umtp_handler, mprobe_state);
	if( session == NULL ) exit(EXIT_SUCCESS);

	signal(SIGINT,	signal_handler); // register signal handler
	signal(SIGABRT, signal_handler);
	signal(SIGTERM, signal_handler);

	if ( flag == MASTER ) {
	    probe_sent = umtp_send_probe(  session, umtp_host_addr(address), port);		
	    probe_count = 0;
	    time(&last_time);
	    while( 0 && *probe_sent == 1 ) {
			time(&now);
			if( now - last_time > 1 ) {
				probe_count++;				
			}
			
			if( probe_count > 3 ) {
				printf("Connection Error!!! Exit!!!\n");
				exit(EXIT_SUCCESS);
			}
	    }
	
	    if( argc > 4 ) {
	        umtp_join_group(session, t_addr, t_port, 127);	
	        umtp_join_group(session, t_addr, t_port + 1, 127);
	    }
	}

	time(&last_time);
	while(!umtp_end) {
	    time(&now);
	    if(now - last_time > timeout) {
			if( flag == MASTER ) {
				if(t_mode) {
					umtp_join_group(session, t_addr, t_port, 127);	
					umtp_join_group(session, t_addr, t_port + 1, 127);
	            }
			}
			umtp_update(session);
			time(&last_time);
	    }
		else
		{
#ifndef WIN32
			sleep(1);
#else
            Sleep(1000);
#endif
		}
	}
	umtp_done(session);

	return EXIT_SUCCESS;
}

