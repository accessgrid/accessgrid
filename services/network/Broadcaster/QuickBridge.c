/* MBONE UNICAST/MULTICAST Gateway/reflector program. */
/*
 *
 * This code was originally based on the reflector written by Tom Lehman
 * http://www.east.isi.edu/~tlehman/programs/mboneuctomcgw/
 * it has been heavily re-written since then by 
 * Stephen Booth, EPCC, University of Edinburgh. spb@epcc.ed.ac.uk
 *
 * This program is intended to connect unicast mbone clients to
 * multicast groups. You can supply an access control list to limit
 * which clients can connect to the gateway.
 * 
 * Data arriving on the unicast ports are resent to the multicast group and
 * to other unicast clients.
 * Multicast data is reset to all unicast clients
 * As this tool is intended for mbone use it forwards a pair of ports.
 * even port - data
 * odd port  - RTCP
 *
 * The program can also work in a concentrator mode by forcing a unicast 
 * connection to a remote gateway. 
 * 
 * To avoid the danger of generating multicast feedback the
 * program will abort if a multicast packet is received from a registered
 * unicast peer. Use this mode with caution e.g. set a restrictive TTL value.
 * $Id: QuickBridge.c,v 1.31 2004-12-17 21:49:23 leggett Exp $
 * Original: Id: quickbridge.c,v 1.12 2003/05/02 11:34:15 spb Exp $
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <errno.h>
#include <signal.h>

#ifndef _WIN32
#include <netinet/in.h>
#include <sys/time.h>
#include <sys/unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/signal.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/uio.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <sys/resource.h>
#include <unistd.h>
#include <string.h>
#include <stdarg.h>
#include <limits.h>
#include <regex.h>
#else
#include "getopt.h"
#include <memory.h>
#include <winsock.h>
#include <mmsystem.h>
#endif

// detect OSX
#if defined(__APPLE__) && defined(__MACH__)
#include <getopt.h>
#endif

#define MSGBUFSIZE 8192 
#ifndef MAXHOSTNAMELEN
#define MAXHOSTNAMELEN 64
#endif
#define MAXUNICASTMEMBERS 32 
/*#define TIMEOUTSECS 300  */
#define TIMEOUTSECS 60 
#define ACLFILE "bridge.acl"

/* For Web Server */
#define PATH_SIZE 1024

static int handleTransaction(int sock);

static int reqGet(FILE *file, char *url);

static int sendHeader(FILE *fwsock, char *url);
static int sendBody(FILE *fwsock, char *url);

static void debug(int level,char *format, ...);

static void sigChldHndlr(int sigRecv);
static void sigAlrmHndlr(int sigRecv);
static void sigPipeHndlr(int sigRecv);

static int msgsock;

static int debugFlag = 0;
static char *documentRoot = NULL;
static int timeOutVal = 0;

static time_t startTime;
static time_t curTime;

#define MY_SERVER_PORT		8080	/* Set this for a static port number */
/*End Web Server*/

enum{
  data=0,
    rtcp,
    nchan
    };

typedef struct uctable{
  struct in_addr addr;  // address of unicast host
  int    active;        // activity flag;
  int    fixed;         // this is a fixed entry do not delete
}uctable_t;


/*
 * access list type
 */
typedef struct acl{
  u_long mask;
  u_long addr;
  struct acl *next;
}acl_t;

acl_t *list=NULL;

int uctotalbytesrecv[nchan];
int uctotalbytessent[nchan];
int ucrecvfromcalls[nchan];
int ucsendtocalls[nchan];
int mctotalbytesrecv[nchan];
int mctotalbytessent[nchan];
int mcrecvfromcalls[nchan];
int mcsendtocalls[nchan];

int max_unicast_mem = MAXUNICASTMEMBERS;

void zero_stats( )
{
  int i;
  debug( 9, "Entering zero_stats( )\n" );
  for( i = 0; i < nchan; i++ )
    {
      uctotalbytesrecv[i] = 0;
      uctotalbytessent[i] = 0;
      ucrecvfromcalls[i]  = 0;
      ucsendtocalls[i]    = 0;
      mctotalbytesrecv[i] = 0;
      mctotalbytessent[i] = 0;
      mcrecvfromcalls[i]  = 0;
      mcsendtocalls[i]    = 0;
    }
  debug( 9, "Leaving zero_stats( )\n" );
}

void printstats( )
{
  debug( 9, "Entering printstats( )\n" );
  printf( "\n" );


  /*print out debug information*/
  printf( "number of uc data bytes received = %d\n", uctotalbytesrecv[data] );
  printf( "number of uc data recvfromcalls = %d\n", ucrecvfromcalls[data] );
  printf( "number of mc data bytes sent = %d\n", mctotalbytessent[data] );
  printf( "number of mc data sendtocalls = %d\n", mcsendtocalls[data] );
  printf( "--------------------------------\n" );
  printf( "number of uc rtcp bytes received = %d\n", uctotalbytesrecv[rtcp] );
  printf( "number of uc rtcp recvfromcalls = %d\n", ucrecvfromcalls[rtcp] );
  printf( "number of mc rtcp bytes sent = %d\n", mctotalbytessent[rtcp] );
  printf( "number of mc rtcp sendtocalls = %d\n", mcsendtocalls[rtcp] );
  printf( "--------------------------------\n" );
  printf( "number of mc data bytes received = %d\n", mctotalbytesrecv[data] );
  printf( "number of mc data recvfromcalls = %d\n", mcrecvfromcalls[data] );
  printf( "number of uc data bytes sent = %d\n", uctotalbytessent[data] );
  printf( "number of uc data sendtocalls = %d\n", ucsendtocalls[data] );
  printf( "--------------------------------\n" );
  printf( "number of mc rtcp bytes received = %d\n", mctotalbytesrecv[rtcp] );
  printf( "number of mc rtcp recvfromcalls = %d\n", mcrecvfromcalls[rtcp] );
  printf( "number of uc rtcp bytes sent = %d\n", uctotalbytessent[rtcp] );
  printf( "number of uc rtcp sendtocalls = %d\n", ucsendtocalls[rtcp] );

  debug( 9, "Leaving printstats( )\n" );
}

int programshutdown( )
{
  printstats( );
  exit( 0 );
}

long addr_lookup( char *s )
{
  long res;
  struct hostent *host;
  struct in_addr *a;
  
  debug( 9, "Entering addr_lookup( )\n" );
  res = inet_addr( s );
  if ( res != -1 )
    {
      debug( 9, "Leaving addr_lookup( ) with return %l\n", res );
      return res;
    }
  if ( ( host = gethostbyname( s ) ) != NULL )
    {
      a = (struct in_addr *)host->h_addr_list[0];
      res = a->s_addr;
      debug( 9, "Leaving addr_lookup( ) with return %l\n", res );
      return( res );
    }
  debug( 9, "Leaving addr_lookup( ) with return -1\n" );
  return( -1 );
}

typedef struct qb_session
{
  int ucfd[nchan];    //unicast receive sockets
  int mcfd[nchan];    //multicast receive socket
  struct sockaddr_in ucaddr[nchan];
  struct sockaddr_in mcaddr[nchan];
  struct ip_mreq mcreq;
  int group_member;     /* are we a member of the multicast group */
  uctable_t *ucmemarray;
  int numunicastmem;  /* number of current unicast members */
  int use_multicast;
  int forward_unicast;    /* do unicast members get to send data */
  int has_fixed;
  struct qb_session *next; /* for multiple session bridging */
}Session;

int num_unicast( Session *head )
{
  int n = 0;
  Session *s;
  
  debug( 9, "Entering num_unicast( )\n" );
  for ( s = head; s; s = s->next )
    {
      n += s->numunicastmem;
    }
  debug( 9, "Leaving num_unicast( ) with return %d\n", n );
  return( n );
}


int findentrymatch( Session *s, struct in_addr *address )
{
  int stopcond = 0;

  debug( 9, "Entering findentrymatch( )\n" );

  /*figure out if address is in array*/
  for ( stopcond = 0; stopcond < s->numunicastmem; stopcond++ )
    {
      if ( s->ucmemarray[stopcond].addr.s_addr == address->s_addr )
	{
	  debug( 9, "Leaving findentrymatch( ) with return %d\n", stopcond );
	  return( stopcond );
	}
    }//end of for
  debug( 9, "Leaving findentrymatch( ) with return %d\n", s->numunicastmem + 1 );
  return( s->numunicastmem + 1 );
}

void printmembers( Session *s );
void zeroarray( Session *s );

void printmembers( Session *head )
{
  Session *s;
  int stopcond = 0;
  
  debug( 9, "Entering printmembers( )\n" );
  for ( s = head; s; s = s->next )
    {
      printf( "---------------\n" );
      for ( stopcond = 0; stopcond < s->numunicastmem; stopcond++ )
	{
	  printf( "%d: %s", stopcond, inet_ntoa( s->ucmemarray[stopcond].addr ) );
	  printf( "\t%s", s->ucmemarray[stopcond].active ? "active" : "inactive" );
	  printf( "\t%s", s->ucmemarray[stopcond].fixed ? "fixed" : "dynamic" );
	  printf( "\n" );
	}
    }
}

void zeroarray( Session *s )  
{
  debug( 9, "Entering zeroarray( )\n" );
  memset( (char *)s->ucmemarray, 0, max_unicast_mem * sizeof( uctable_t ) );
  debug( 9, "Leaving zeroarray( )\n" );
}

void timeoutchk( Session *head )
{
  int stopcond = 0;
  Session *s;

  debug( 9, "Entering timeoutchk( )\n" );
  //printf("checking for inactive unicast members\n");
  for ( s = head; s; s = s->next )
    {
      for ( stopcond = 0; stopcond < s->numunicastmem; stopcond++ )
	{
	  /*if activityflag=0, delete member*/ 
	  while ( ( s->ucmemarray[stopcond].active == 0 ) && 
		  ( s->ucmemarray[stopcond].fixed == 0 ) && 
		  ( stopcond < s->numunicastmem ) )
	    {
	      printf( "deleting an inactive unicast member=%s\n", inet_ntoa( s->ucmemarray[stopcond].addr ) );
	      /* reduce count and copy down */
	      s->numunicastmem--;
	      s->ucmemarray[stopcond] = s->ucmemarray[s->numunicastmem];
	      /*
	       * The following are necessary for the case where 
	       * stopcond == numunicastmem
	       */
	      memset( (char *)(s->ucmemarray+s->numunicastmem), 0, sizeof( uctable_t ) );
	    }
	  if ( stopcond < s->numunicastmem )
	    { // don't over index array if array full 
	      s->ucmemarray[stopcond].active = 0; // reset flag for next pass
	    }
	}//end of for
    }
  debug( 9, "Leaving timeoutchk( )\n" );
}

int is_multicast( u_long a )
{
  debug( 9, "Entering is_multicast( )\n" );
  u_long mask = inet_addr( "224.0.0.0" );
  debug( 9, "Leaving is_multicast( ) with return: %d\n", ( ( a & mask ) == mask ) );
  return( ( a & mask ) == mask );
}

int is_auth( u_long a )
{
  struct acl *p;

  debug( 9, "Entering is_auth( )\n" );
  if ( ! list )
    {
      debug( 9, "Leaving is_auth( ) with return: 1\n" );
      return 1;
    }
  for ( p = list; p; p = p->next )
    {
      if ( ( a & p->mask ) == p->addr )
	{
	  debug( 9, "Leaving is_auth( ) with return: 1\n" );
	  return 1;
	}
    }
  
  debug( 9, "Leaving is_auth( ) with return: 0\n" );
  return 0;
}

void set_acl( char *file )
{
  FILE *in;
  char line[160], *a = NULL, *m = NULL;
  acl_t *new;
  char *s;
  int skip;

  debug( 9, "Entering set_acl( )\n" );
  in = fopen( file, "r" );
  if ( ! in )
    {
      printf( "No %s file found, no ACL set\n", file );
      debug( 9, "Leaving set_acl( )\n" );
      return;
    }
  printf( "ACL is:\n" );
  while ( fgets( line, 160, in ) )
    {
      a = NULL;
      m = NULL;
      skip = 0;
      for ( s = line; *s; s++ )
	{
	  /* remove comments */
	  if ( *s == '#' )
	    {
	      *s = '\0';
	      break;
	    }
	  if ( *s == ' ' || *s == '\t' )
	    {
	      *s = '\0';
	      skip = 0;
	    }
	  else
	    {
	      if ( ! a )
		{
		  a = s;
		  skip = 1;
		}
	      else
		{
		  if ( ! m && ( skip == 0 ) )
		    {
		      m = s;
		    }
		}
	    }
	}

      if ( a && m )
	{
	  /* found a line with 2 strings */
	  printf( "%s\t%s\n", a, m );
	  new = (acl_t *)malloc( sizeof( acl_t ) );
	  if ( ! new )
	    {
	      perror( "malloc failed\n" );
	      exit( 1 );
	    }
	  new->addr = inet_addr( a );
	  if ( new->addr == -1 )
	    {
	      printf( "bad address in acl file %s\n", a );
	      exit( 1 );
	    }
	  new->mask = inet_addr( m );
	  if ( new->mask == -1 )
	    {
	      printf( "bad mask in acl file %s\n", m );
	      exit( 1 );
	    }
	  /*
	   * There are no deny rules only permit so its fine to 
	   * build list in reverse order
	   */
	  
	  new->next = list;
	  list = new;
	}
    }
  fclose( in );
  
  debug( 9, "Leaving set_acl( )\n" );
}

void print_usage( char *name )
{
  debug( 9, "Entering print_usage( )\n" );
  printf( "usage: %s [-g <multicast-group>|<unicast peer>] [-m mcast port] [-u ucast port] [-t ttl] [-f <sdp file>] -n [ Flags for additional session ]\n", name );
  printf( "Any number of additional bridge sessions can be specified by using\nthe -n flag, unspecified values default to that of the previous session\n" );
  printf( "\n\nAccess list for dynamic unicast session defined in %s file\nas address netmask pairs\n", ACLFILE );
  debug( 9, "Leaving print_usage( )\n" );
}


void join_group( Session *s )
{
  int i;

  debug( 9, "Entering join_group( )\n" );
  if ( s->use_multicast && ! s->group_member )
    {
      printf( "joining multicast group\n" );
      for ( i = 0; i < nchan; i++ )
	{
	  if ( setsockopt( s->mcfd[i], IPPROTO_IP, IP_ADD_MEMBERSHIP, 
			   (char *)&s->mcreq, sizeof( s->mcreq ) ) < 0 )
	    {
	      perror( "can't set socket options to join multicast group!" );
	      exit( 1 );
	    } 
	}
      s->group_member = 1;
    }
  debug( 9, "Leaving join_group( )\n" );
}

void leave_group( Session *s )
{
  int j;

  debug( 9, "Entering leave_group( )\n" );
  if ( s->use_multicast && s->group_member )
    {
      printf( "leaving multicast group\n" );
      for ( j = 0; j < nchan; j++ )
	{
	  if ( setsockopt( s->mcfd[j], IPPROTO_IP, IP_DROP_MEMBERSHIP, 
		       (char *)&s->mcreq, sizeof( s->mcreq ) ) < 0 )
	    {
	      perror( "can't set socket options to leave multicast group!" );
	      exit( 1 );
	    } 
	}
      s->group_member = 0;
    }
  debug( 9, "Leaving leave_group( )\n" );
}

void do_group_membership( Session *head )
{
  int n = 0;
  Session *s;

  debug( 9, "Entering do_group_membership( )\n" );
  for ( s = head; s; s = s->next )
    {
      /* we are relying on the join/leave being a no-op if already in correct state */
      if ( s->numunicastmem > 0 )
	{
	  join_group( s );
	}
      else
	{
	  leave_group( s );
	}
    }
  debug( 9, "Leaving do_group_membership( )\n" );
}

int set_maxfds( Session *head, int maxfds )
{
  Session *s;

  debug( 9, "Entering set_maxfds( )\n" );
  for ( s = head; s; s = s->next )
    {
      if ( s->ucfd[data] > maxfds )
	{
	  maxfds = s->ucfd[data];
	}
      if ( s->ucfd[rtcp] > maxfds)
	{
	  maxfds = s->ucfd[rtcp];
	}
      if ( s->use_multicast )
	{
	  if ( s->mcfd[data] > maxfds )
	    {
	      maxfds = s->mcfd[data];
	    }
	  if ( s->mcfd[rtcp] > maxfds )
	    {
	      maxfds = s->mcfd[rtcp];
	    }
	}
    }
  debug( 9, "Leaving set_maxfds( ) with return: %d\n", maxfds );
  return( maxfds );
}

void session_set( Session *head, fd_set *readfds )
{
  Session *s;

  debug( 9, "Entering session_set( )\n" );
  for ( s = head; s; s = s->next )
    {
      FD_SET( s->ucfd[data], readfds );
      FD_SET( s->ucfd[rtcp], readfds );
      if ( s->use_multicast )
	{
	  FD_SET( s->mcfd[data], readfds );
	  FD_SET( s->mcfd[rtcp], readfds );
	}
    }
  debug( 9, "Leaving session_set( )\n" );
}



void process_session( Session *head, fd_set *readfds, u_long myip )
{
  int i;
  int do_send;
  struct sockaddr_in sourceaddr;
  int sourceaddrlen;
  char recvbuf[MSGBUFSIZE];
  int foundindex;
  int nr;
  int ns;
  int stopcond = 0;
  u_long remoteunicastaddress;

  Session *s;

  debug( 9, "Entering process_session( )\n" );
  for ( s = head; s; s = s->next )
    {
      /*1:receive from unicast, send on multicast and other unicast participants */
      for ( i = 0; i < nchan; i++ )
	{
	  do_send = s->forward_unicast;
	  if ( FD_ISSET( s->ucfd[i], readfds ) )
	    {
	      //printf("\nready to receive data on s->ucfd[%d]!\n",i);
	      sourceaddrlen = sizeof( sourceaddr );
	      memset( (char *)&sourceaddr,0, sourceaddrlen );
	      //debug( 9, "Before recvfrom( )\n" );
	      //nr = recvfrom( s->ucfd[i], recvbuf, MSGBUFSIZE, 0,
	      //(struct sockaddr *)&sourceaddr, &sourceaddrlen );
	      //debug( 2, "\nreading from ucfd[%d], got data from %s:%d\n", i, inet_ntoa( sourceaddr.sin_addr ), ntohs( sourceaddr.sin_port ) );
	      if ( debugFlag > 0 )
		{
		  ucrecvfromcalls[i] = ucrecvfromcalls[i] + 1;
		  uctotalbytesrecv[i] = uctotalbytesrecv[i] + nr;
		}
	      
	      if ( nr < 0 )
		{
		  printf( "ucfd[%d]:recvfrom over unicast error!(1) %s\n", i, strerror( errno ) );
		  do_send = 0;
		}
	      else
		{
		  /*send to all unicast (execpt the one it came from)*/ 
		  /*first figure out if sourceaddress is in ucmemarray*/
		  /*if sourceaddress if local host address, do not update the ucmemarray*/
		  if ( sourceaddr.sin_addr.s_addr != myip )
		    {
		      foundindex = findentrymatch( s, &sourceaddr.sin_addr );
		      //printf("sourceaddr=%d\n",sourceaddr.sin_addr.s_addr);
		      //printf("foundindex=%d\n",foundindex);
		      if ( foundindex < s->numunicastmem )
			{
			  //printf("found address at ucmemarray[%d]\n",foundindex);
			  /*update activity flag*/ 
			  s->ucmemarray[foundindex].active = 1; 
			}
		      else
			{
			  //debug( 2, "did not find address in ucmemarray\n" );
			  /*add entry to array*/
			  if ( ( s->numunicastmem < max_unicast_mem ) && 
			       is_auth( sourceaddr.sin_addr.s_addr ) )
			    {
			      s->ucmemarray[s->numunicastmem].addr.s_addr = sourceaddr.sin_addr.s_addr;
			      s->ucmemarray[s->numunicastmem].active = 1;
			      s->ucmemarray[s->numunicastmem].fixed = 0; 
			      s->numunicastmem++;
			      printf( "\nadding an entry, unicast members are now:\n" );
			      printmembers( s );
			      join_group( s );
			    }
			  else
			    {
			      //debug( 1, "Not auth or too many unicast members, can't add another!\n" );
			      do_send=0;
			    }
			}//end of else 
		    }
		  else
		    {
		      //debug( 2, "Discarding packet from local host\n" );
		    } //end of updating ucmemarray values 
		  
		  /*now step thru array and send to all unicast members, except current source*/
		  do_send = 0;
		  if ( do_send )
		    {
		      for ( stopcond = 0; stopcond < s->numunicastmem; stopcond ++ )
			{
			  remoteunicastaddress = s->ucmemarray[stopcond].addr.s_addr;
			  if ( remoteunicastaddress != sourceaddr.sin_addr.s_addr )
			    {
			      s->ucaddr[i].sin_addr.s_addr = remoteunicastaddress;
			      //debug( 2, "sending to %s\n", inet_ntoa( s->ucmemarray[stopcond].addr ) );
			      ns = sendto( s->ucfd[i], recvbuf, nr, 0, (struct sockaddr *)&s->ucaddr[i],
					   sizeof( s->ucaddr[i] ) );
			    }
			  else
			    {
			      //debug( 4, "not resending to ORIGINATOR! or array entry = 0\n" );
			    }
			}//end of for (stopcond=0;....
		      
		      if ( s->use_multicast && s->forward_unicast )
			{
			  /*sent to the multicast group*/
			  //debug( 2, "sending to %s\n", inet_ntoa( s->mcaddr[i].sin_addr ) );
			  ns = sendto( s->mcfd[i], recvbuf, nr, 0, (struct sockaddr *)&s->mcaddr[i],
				       sizeof( s->mcaddr[i] ) );
			  if ( debugFlag > 0 )
			    {
			      mcsendtocalls[i] = mcsendtocalls[i] + 1;
			      mctotalbytessent[i] = mctotalbytessent[i] + ns;
			    }
			  if ( ns < 0 )
			    {
			      perror( "sendto over multicast address error!(2)\n" );
			    }
			} /* use_multicast */
		    } /* do send */
		} /* recv failed */
	    } /* FD_ISSET */
	} /* nchan loop */

      if ( s->use_multicast )
	{
	  /*3:receive from multicast, send on unicast to all unicast participants */ 
	  for ( i = 0; i < nchan; i++ )
	    {
	      if ( FD_ISSET( s->mcfd[i], readfds ) )
		{
		  debug( 4, "ready to receive data on mcfd[%d]!\n", i );
		  sourceaddrlen = sizeof( sourceaddr );
		  memset( (char *)&sourceaddr, 0, sourceaddrlen );
		  nr = recvfrom( s->mcfd[i], recvbuf, MSGBUFSIZE, 0,
				 (struct sockaddr *)&sourceaddr, &sourceaddrlen );
		  if ( nr < 0 )
		    {
		      printf( "mcfd[%d]:recvfrom over multicast error!(5) %s\n", i, strerror( errno ) );
		    }
		  else
		    {
		      debug( 2, "\nreading from mcfd[%d], got data from=%s\n", i, inet_ntoa( sourceaddr.sin_addr ) );
		      debug( 2, "retransmit to unicast addresses\n" );
		      //printf("chksrc=%d\n", chksrc);
		      
		      if ( debugFlag > 0 )
			{
			  mcrecvfromcalls[i] = mcrecvfromcalls[i] + 1;
			  mctotalbytesrecv[i] = mctotalbytesrecv[i] + nr;
			}
		      
		      /*now step thru array and send to all unicast members*/
		      for ( stopcond = 0; stopcond < s->numunicastmem; stopcond++ )
			{
#ifdef FEEDBACK_CHECK
			  if ( s->ucmemarray[stopcond].addr.s_addr == sourceaddr.sin_addr.s_addr )
			    {
			      printf( "ERROR detected multicast packet from a unicst peer\n" );
			      printf( "possible feedback configuration\n" );
			      exit( 2 );
			    }
#endif
			  remoteunicastaddress = s->ucmemarray[stopcond].addr.s_addr;
			  s->ucaddr[i].sin_addr.s_addr = remoteunicastaddress;
			  debug( 2, "sending to %s\n", inet_ntoa( s->ucmemarray[stopcond].addr ) );
			  ns = sendto( s->ucfd[i], recvbuf, nr, 0, (struct sockaddr *)&s->ucaddr[i],
				       sizeof( s->ucaddr[i] ) );
			  if ( debugFlag > 0 )
			    {
			      ucsendtocalls[i] = ucsendtocalls[i] + 1;
			      uctotalbytessent[i] = uctotalbytessent[i] + 1;
			    }
			}//end of for (stopcond=0;....
		    }// end of if *nr < 0 )
		}
	    }
	}
    }
  debug( 9, "Leaving process_session( )\n" );
}

void insert_fixed( Session *s, u_long addr )
{
  debug( 9, "Entering insert_fixed( )\n" );
  /* now insert into list */
  if ( s->numunicastmem < max_unicast_mem )
    {
      s->ucmemarray[s->numunicastmem].addr.s_addr = addr;
      s->ucmemarray[s->numunicastmem].active = 1;
      s->ucmemarray[s->numunicastmem].fixed = 1;
      printf( "inserting a fixed unicast peer %s\n", inet_ntoa( s->ucmemarray[s->numunicastmem].addr ) );
      s->numunicastmem++;
      s->has_fixed = 1;
    }
  else
    {
      printf( "Too many fixed addresses\n" );
      exit( 1 );
    }
  debug( 9, "Leaving insert_fixed( )\n" );
}

typedef int Ports[nchan];

Session *setup_session( Ports ucport, Ports mcport, u_long multicastaddress, u_char ttl, int forward, Session *list )
{
  Session *s;
  int i;
  u_char do_loopback;

  debug( 9, "Entering setup_session( )\n" );
  /* check values */
  if ( multicastaddress == -1 )
    {
      printf( "Bad multicast address\n" );
      debug( 9, "Leaving setup_session( )\n" );
      return( NULL );
    }

  s = (Session *)malloc( sizeof( Session ) );
  
  if ( s == NULL )
    {
      perror( "Session: malloc failed" );
      exit( 1 );
    }

  s->use_multicast = is_multicast( multicastaddress );

  if( s->use_multicast )
    {
      printf( "using multicast\n" );

      if ( s->use_multicast && mcport[data] == 0 )
	{
	  printf( "Bad multicast port\n" );
	  debug( 9, "Leaving setup_session( )\n" );
	  return( NULL );
	}
    }
  if ( ucport[data] == 0 )
    {
      printf( "Bad unicast port\n" );
      debug( 9, "Leaving setup_session( )\n" );
      return( NULL );
    }
  if ( ttl < 1 )
    {
      printf( "Bad TTL value\n" );
      debug( 9, "Leaving setup_session( )\n" );
      return( NULL );
    }


  s->forward_unicast = forward;
  s->group_member = 0;
  s->ucmemarray = calloc( sizeof( uctable_t ), max_unicast_mem );
  if ( ! s->ucmemarray )
    {
      perror( "unicast table malloc failed" );
      exit( 1 );
    }
  s->numunicastmem = 0;
  /*zero out ucmemarray*/
  zeroarray( s );

  printf( "ucport[data]=%d  ", ucport[data] );
  printf( "ucport[rtcp]=%d\n", ucport[rtcp] );
  if ( s->use_multicast )
    {
      printf( "mcport[data]=%d  ", mcport[data] );
      printf( "mcport[rtcp]=%d\n", mcport[rtcp] );
    }

  //printf("multicastaddress=%d\n",multicastaddress);

  for ( i = 0; i < nchan; i++ )
    {
      /*enter the address/port data into the s->ucaddr[i] structure
       * once the port is set up we will re-use this in the send calls
       */
      memset( (char *)&s->ucaddr[i], 0, sizeof( s->ucaddr[i] ) );
      s->ucaddr[i].sin_family = AF_INET;
      s->ucaddr[i].sin_addr.s_addr = htonl( INADDR_ANY );
      s->ucaddr[i].sin_port = htons( ucport[i] );
      /*get the s->ucfd[data] socket, bind to address*/
      if ( ( s->ucfd[i] = socket( AF_INET, SOCK_DGRAM, 0 ) ) < 0 )
	{
	  perror( "can't open s->ucfd socket!" );
	  exit( 1 );
	}
    if ( bind( s->ucfd[i], (struct sockaddr *)&s->ucaddr[i],
	       sizeof( s->ucaddr[i] ) ) < 0 )
      {
	perror( "can't bind ucaddr to socket!" );
	exit( 1 );
      }
    if ( s->use_multicast )
      {
	printf( "making multicast port[%d]\n", i );
	/*enter the address/port data into the mcaddr[data] structure*/
	memset( (char *)&s->mcaddr[i], 0, sizeof(s->mcaddr[i] ) );
	s->mcaddr[i].sin_family = AF_INET;
	s->mcaddr[i].sin_addr.s_addr = multicastaddress;
	s->mcaddr[i].sin_port = htons( mcport[i] );

	/*get a mcfd[data] socket, bind to address */
	if ( ( s->mcfd[i] = socket( AF_INET, SOCK_DGRAM, 0 ) ) < 0 )
	  {
	    perror( "can't open mcfd socket!" );
	    exit( 1 );
	  }
	if ( bind( s->mcfd[i], (struct sockaddr *)&s->mcaddr[i], sizeof( s->mcaddr[i] ) ) < 0 )
	  {
	    perror( "can't bind mcaddr to socket!" );
	    exit( 1 );
	  }
	/*now set multicast socket TTL option*/
	/*setsocketopt (int filedescriptor, int level, in optname),*/
	/*charpointer optvalue, intpointer optlen)*/
	if ( setsockopt( s->mcfd[i], IPPROTO_IP, IP_MULTICAST_TTL,
			 &ttl, sizeof( ttl ) ) < 0 )
	  {
	    perror( "can't set multicast ttl socket option!" );
	    exit( 1 );
	  }
	do_loopback = 0;
	if ( setsockopt(s->mcfd[i], IPPROTO_IP, IP_MULTICAST_LOOP,
			&do_loopback, sizeof( do_loopback ) ) < 0 )
	  {
	    perror( "can't set multicast ttl socket option!" );
	    exit( 1 );
	  }
      }
  }

  memset( (char *)&s->mcreq, 0, sizeof( s->mcreq ) );
  if ( s->use_multicast )
    {
      /*enter the address/port data into the mcreq structure*/
      s->mcreq.imr_multiaddr.s_addr = multicastaddress;
      s->mcreq.imr_interface.s_addr = htonl( INADDR_ANY );
    }
  else
    {
      /* make this a fixed unicast address instead */
      insert_fixed( s, multicastaddress );
    }

  /* not actually needed if fixed and multicast are mutually exclusive 
   * but put it in for completeness as we needed this in earlier versions
   */
  if ( s->has_fixed )
    {
      join_group( s );
    }

  s->next = list;
  debug( 9, "Leaving setup_session( )\n" );
  return s;
}

int all_fixed( Session *head )
{
  Session *s;
  int result = 1;

  debug( 9, "Entering all_fixed( )\n" );
  for ( s = head; result && s != NULL; s = s->next )
    {
      result = result && s->has_fixed;
    }
  debug( 9, "Leaving all_fixed with return: %d\n", result );
  return( result );
}

#if 1
/* tdu */
void signal_handler( int signum )
{
  exit( 2 );
}
#endif



int main( int argc, char *argv[] )
{
  /*define variables*/
  Session *s = NULL;
  u_char ttl;
  int mcport[nchan];
  int ucport[nchan];
  u_long multicastaddress;
  u_long remoteunicastaddress;

  char myhostname[MAXHOSTNAMELEN];
  char *myhostnameipaddress;
  u_long myip;  
  struct hostent *host;
  int forward = 0;

  int i;
  fd_set readfds, web_masterfds, web_readfds;
  int maxfds, web_maxfds;
  int nfds;
  int n2;
  int timeoutsecs = TIMEOUTSECS;
  char inputbuf[32];
  int timerstatus;
  struct timeval tv;
  time_t last_time, now;
  char *progname;
  char *tmp;
  int c, arg_err = 0;

  int sock;
  int length;
  struct sockaddr_in server, client;
  int chid;
  int stat;

#ifdef _WIN32
  WORD wVersionRequested = MAKEWORD(2,2);
  WSADATA wsaData;
  int err = WSAStartup( wVersionRequested, &wsaData );
  if ( err != 0 )
    {
      exit( 0 );
    }
#endif

  /* 
   * don't want this as a command line flag as we want the array
   * in place before processing flags (the -a flag uses it
   */
  if ( ( tmp = getenv( "MAX_UNICAST_MEM" ) ) != NULL )
    {
      i = atoi( tmp );
      if ( i > 0 )
	{
	  max_unicast_mem = i;
	}
    }
  printf( "max_unicast_mem is %d\n", max_unicast_mem );

  if( max_unicast_mem < 1 )
    {
      printf( "Bad max_unicast_mem value %d\n",max_unicast_mem );
      exit( 1 );
    }
  
  /*figure out the hostname and get a local ip address*/
#ifndef _WIN32
  if ( gethostname( myhostname, MAXHOSTNAMELEN ) < 0 )
    {
      perror( "gethostname error" );
      exit( 1 );
    }
#else
  if ( gethostname( myhostname, MAXHOSTNAMELEN ) == SOCKET_ERROR )
    {
      printf( "Couldn't get hostname: %d\n", WSAGetLastError( ) );
      exit( 1 );
    }
#endif
  printf( "myhostname=%s\n", myhostname );
  if ( ( host = gethostbyname( myhostname ) ) == NULL )
    {
      perror( "gethostbyname failure!" );
      exit( 1 );
    }
  myhostnameipaddress = (char *)inet_ntoa( *((struct in_addr *)host->h_addr_list[0]) );
  myip = inet_addr( myhostnameipaddress );
  printf( "myhostipaddress=%s\n\n", myhostnameipaddress );

  zero_stats( );

  progname = argv[0];
  /* default values */
  ttl = 127;
  mcport[data] = 0;
  ucport[data] = 0;
  mcport[rtcp] = 0;
  ucport[rtcp] = 0;
  multicastaddress = -1;

  startTime = time( NULL );

  while ( ( c = getopt( argc, argv, "f:g:t:u:m:d:nl" ) ) != EOF )
    {
      switch( c )
	{
	case 'g':
	  multicastaddress = addr_lookup( optarg );
	  break;
	case 'm':
	if ( atoi( optarg ) % 2 == 0 )
	  {
	    mcport[data] = atoi( optarg );
	    mcport[rtcp] = atoi( optarg ) + 1;
	  }
	else
	  {
	    mcport[data] = atoi( optarg ) - 1;
	    mcport[rtcp] = atoi( optarg );
	  }
	break;
	case 'u':
	  if ( atoi( optarg ) % 2 == 0 )
	    {
	      ucport[data] = atoi( optarg );
	      ucport[rtcp] = atoi( optarg ) + 1;
	    }
	  else
	    {
	      ucport[data] = atoi( optarg ) - 1;
	      ucport[rtcp] = atoi( optarg );
	    }
	  break;
	case 't':
	  ttl = atoi( optarg );
	  break;
	case 'd':
	  debugFlag = atoi( optarg );
	  break;
	case 'n':
	  s = setup_session( ucport, mcport, multicastaddress, ttl, forward, s );
	  if ( ! s )
	    {
	      perror( "No session" );
	      print_usage( progname );
	      exit( 1 );
	    }
	  break;
	case 'l':
	  forward = ! forward;
	  break;
	case 'f':
	  documentRoot = optarg;
	  break;
	default:
	  printf( "Unknown flag %c\n", c );
	  arg_err = 1;
	  break;
	}
    }

  if ( timeOutVal == 0 )
    timeOutVal = 20;

  if ( documentRoot == NULL )
    {
      perror( "No documentRoot" );
      print_usage( progname );
      exit( 1 );
    }

  s = setup_session( ucport, mcport, multicastaddress, ttl, forward, s );
  if ( ! s )
    {
      print_usage( progname );
      exit( 1 );
    }
  

  /* code for gateway mode */
  set_acl(ACLFILE);

#ifndef WIN32
  signal( SIGALRM,SIG_IGN );
#endif

#if 1 /* tdu */
  {
#ifndef WIN32
    /* ensure that SIGINT is not blocked */
    sigset_t inset;
    sigaddset( &inset,SIGINT );
    sigprocmask( SIG_UNBLOCK, &inset, NULL );
#endif

    /* set signal handler for SIGINT */
    signal( SIGINT, signal_handler );
  }
#endif
  
  sock = socket( AF_INET, SOCK_STREAM, 0 );
  if ( sock < 0 )
    {
      perror( "opening stream socket" );
      exit( 1 );
    }

  server.sin_family = AF_INET;
  server.sin_addr.s_addr = INADDR_ANY;
  server.sin_port = htons( MY_SERVER_PORT );

  if ( bind( sock, (struct sockaddr *)&server, sizeof( server ) ) )
    {
      perror( "binding stream socket" );
      exit( 1 );
    }
  length = sizeof( server );
  if ( getsockname( sock, (struct sockaddr *)&server, &length ) )
    {
      perror( "getting socket name" );
      exit( 1 );
    }
  fprintf( stderr, "Socket has port #%d\n", ntohs( server.sin_port ) );

  listen( sock, 5 );
  signal( SIGCHLD, sigChldHndlr );
  
  time( &last_time );

  /*start infinite while loop*/
  /*and check for activity on sockets*/

  /*set up the select sytem call parameters*/  
  /*zero out the readfds and writefds lists, then add*/
  /*the file descriptors of interest*/

  /* maxfds should be one more than largest fd */
  maxfds = 0;
  maxfds = set_maxfds( s, maxfds );
  maxfds++;

  FD_ZERO( &web_masterfds );
  FD_ZERO( &web_readfds );
  web_maxfds = sock;
  FD_SET( sock, &web_masterfds );
  
  while ( 1 )
    { 
      web_readfds = web_masterfds;
      tv.tv_sec = 0;
      tv.tv_usec = 0;
      debug( 9, "About to select( ) web socket.\n" );
      if ( select( web_maxfds + 1, &web_readfds, NULL, NULL, &tv ) == -1 )
	{
	  perror( "select" );
	  signal( SIGCHLD, sigChldHndlr );
	}
      for ( i = 0; i <= web_maxfds; i++ )
	{
	  if ( FD_ISSET( i, &web_readfds ) )
	    {
	      debug( 4, "socket( ) ready\n" );
	      length = sizeof( client );
	      if ( ( msgsock = accept( i, (struct sockaddr *)&client, &length ) ) == -1 )
		{
		  perror( "accept" );
		}
	      else
		{
		  FD_SET( msgsock, &web_masterfds );
		  if ( msgsock > web_maxfds )
		    {
		      web_maxfds = msgsock;
		    }
		  debug( 2, "Connection accepted.\n" );
		  debug( 4, "File descriptor for accepted socket: %d\n", msgsock );
		  debug( 6, "Client IP: %s\n", inet_ntoa( client.sin_addr ) );
		  debug( 2, "Adding fixed IP\n" );
		  insert_fixed( s, client.sin_addr.s_addr );
		  chid = fork( );
		  if ( chid == 0 )
		    {
		      signal( SIGALRM, sigAlrmHndlr );
		      signal( SIGPIPE, sigPipeHndlr );
		      debug( 4, "Child startring.\n" );
		      alarm( timeOutVal );
		      debug( 8, "Alarm set: Time out at %d sec.\n", timeOutVal );
		      stat = handleTransaction( msgsock );
		      alarm( 0 );
		      debug( 8, "Alarm cancelled.\n" );
		      debug( 3, "Child exiting. Exit code: %d.\n", stat );
		      exit( stat );
		    }
		  else
		    {
		      debug( 4, "Closing msgsock (%d) in parent.\n", msgsock );
		      close( msgsock );
		      FD_CLR( msgsock, &web_masterfds );
		    }
		}
	    }
	}
    
      FD_ZERO( &readfds );
      session_set( s, &readfds );

      /*check for activity and processor accordingly*/
      /*
       * We add a timeout when there are active unicast
       * sessions so that we can detect when the last client
       * leaves. Without this we would need a multicast
       * packet to come in and trigger clearup.  some OS will
       * change the timerval struct so make a new one each
       * time.  If we have fixed sessions the list will never
       * be empty so block.
       */
      tv.tv_sec = 0;
      tv.tv_usec = 0; 
      nfds = select( maxfds, &readfds, NULL, NULL, &tv );

      process_session( s, &readfds, myip );

      time( &now );

      if( now - last_time > TIMEOUTSECS )
	{
	  timeoutchk( s );
	  do_group_membership( s );
	
	  printf( "current unicast members are now:\n" );
	  printmembers( s );
	  time( &last_time );
	}
    } //end of while loop

#ifdef _WIN32
  WSACleanup( );
#endif
} //end of main

static int handleTransaction( int sock )
{
  FILE *fsock;

  char buf[2048];
  char cmd[2048];
  int status = -1;
  char *method;
  char *url;
  char *lasts;
  char *ret;

  debug( 9, "Entering handleTransaction( )\n" );

  if ( ( fsock = fdopen( sock, "r+b" ) ) == NULL )
    {
      perror( "fdopen" );
      return( -1 );
    }

  debug( 9, "fdopen( ) for msgsock successful\n" );

  ret = fgets( cmd, sizeof( cmd ), fsock );
  if ( ret != NULL )
    {
      method = strtok( cmd, " " );
      url = strtok( NULL, " " );

      if ( method == NULL || url == NULL )
	{
	  debug( 4, "handleTransaction( ) got bogus request line\n" );
	  return( -1 );
	}
      debug( 5, "method: '%s', url: '%s'\n", method, url );
    }

  ret = fgets( buf, sizeof( buf ), fsock );
  while ( ret != NULL && buf[0] != '\r' && buf[0] != '\n' )
    {
      debug( 9, "Got input data line: '%s'\n", buf );
      ret = fgets( buf, sizeof( buf ), fsock );
    }
  debug( 9, "Header complete\n" );

  if ( ! strcmp( method, "HEAD" ) )
    {
      debug( 7, "HEAD processing selected\n" );
      status = sendHeader( fsock, url );
      if ( ! status )
	{
	  status = 1;
	}
      else
	{
	  status = -1;
	}
    }
  else if ( ! strcmp( method, "GET" ) )
    {
      debug( 7, "GET processing selected\n" );
      status = reqGet( fsock, url );
      if ( ! status )
	{
	  status = 2;
	}
      else
	{
	  status = -1;
	}
    }
  else
    {
      status = 3;
    }

  fflush( fsock );
  debug( 4, "Closing msgsock (%d) in child\n", sock );
  fclose( fsock );
  return( status );
}

static int sendHeader( FILE *fwsock, char *url )
{
  debug( 9, "Entering sendHeader( )\n" );
  fprintf( fwsock, "HTTP/1.0 200 OK\r\n" );
  fprintf( fwsock, "Content-Type: application/sdp\r\n" );
  fprintf( fwsock, "Connection: close\r\n" );
  fprintf( fwsock, "\r\n" );
  debug( 9, "Leaving sendHeader( )\n" );
  return( 0 );
}

static int reqGet( FILE *file, char *url )
{
  int status;

  debug( 9, "Entering reqGet( )\n" );

  if ( ( status = sendHeader( file, url ) ) != 0 )
    {
      return( status );
    }
  debug( 9, "Leaving reqGet( )\n" );
  return( sendBody( file, url ) );
}

static int sendBody( FILE *fwsock, char *url )
{
  FILE *inFile;
  char fileBuf[4096];
  size_t numRead;

  char fullPath[PATH_SIZE];
  struct stat MyStat;

  debug( 9, "Entering sendBody( )\n" );
  strcpy( fullPath, documentRoot );
  debug( 5, "Final filename: %s\n", fullPath );

  if ( ( inFile = fopen( fullPath, "rb" ) ) == NULL )
    {
      debug( 4, "Error opening file: %s\n", fullPath );
      debug( 9, "Leaving sendBody( ) with return: 1\n" );
      return( 1 );
    }

  while ( ! feof( inFile ) )
    {
      numRead = fread( fileBuf, 1, 4096, inFile );
      fwrite( fileBuf, 1, numRead, fwsock );
    }

  debug( 9, "Leaving sendBody( ) with return: 0\n" );
  return( 0 );
}

static void debug(int level,char *format, ...)
{
  va_list ap;
  if (debugFlag && (debugFlag >= level))
    {
      va_start(ap, format);
      (void) vfprintf(stderr, format, ap);
      va_end(ap);
    }
  return;
}

void sigChldHndlr( int sigRecv )
{
  int waitStatus = 0;
  wait( &waitStatus );
  waitStatus = WEXITSTATUS( waitStatus );

  switch ( waitStatus )
    {
    case 1:
      debug(2,"Child returned with valid HEAD request\n");
      debug(8,"Child exit status: 1\n");
      break;
    case 2:
      debug(2,"Child returned with valid GET request\n");
      debug(8,"Child exit status: 2\n");
      break;
    case 3:
      debug(2,"Child returned with 'valid' BOGUS request\n");
      debug(8,"Child exit status: 3\n");
      break;
    case 101:
      debug(2,"Child returned from SIGALRM signal!\n");
      debug(8,"Child exit status: 101\n");
      break;
    case 102:
      debug(2,"Child returned from SIGPIPE signal!\n");
      debug(8,"Child exit status: 102\n");
      break;
    default:
      debug(2,"Child exited with UNKNOWN STATUS!\n");
      debug(8,"Child exit status: %d\n",waitStatus);
    }
}

/*****************************************************************************
 *
 * This function is the signal handler for SIGALRM signals (should only occur
 * in the various child processes).  It simply exits with the appropriate
 * return code.
 *
 * sigRecv:	The signal that got us here, should ALWAYS be SIGALRM
 *
 ******************************************************************************/
void sigAlrmHndlr(int sigRecv){
  exit(101);
}

/*****************************************************************************
 *
 * This function is the signal handler for SIGPIPE signals (should only occur
 * in the various child processes).  It simply exits with the appropriate
 * return code.
 *
 * sigRecv:	The signal that got us here, should ALWAYS be SIGPIPE
 *
 ******************************************************************************/
void sigPipeHndlr(int sigRecv){
  exit(102);
}
