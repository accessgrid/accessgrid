
/*MBONE UNICAST/MUTLICAST Gateway/reflector program.*/
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
 * $Id: QuickBridge.c,v 1.1 2003-08-13 19:26:27 turam Exp $
 */


#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/signal.h>
#include <errno.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#define MSGBUFSIZE 8192 
#ifndef MAXHOSTNAMELEN
#define MAXHOSTNAMELEN 64
#endif
#define MAXUNICASTMEMBERS 32 
/*#define TIMEOUTSECS 300  */
#define TIMEOUTSECS 60 
#define ACLFILE "bridge.acl"

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

int numunicastmem = 0;  /* number of current unicast members */
int max_unicast_mem = MAXUNICASTMEMBERS;

void zero_stats(){
  int i;
  for(i=0;i<nchan;i++){
    uctotalbytesrecv[i]=0;
    uctotalbytessent[i]=0;
    ucrecvfromcalls[i]=0;
    ucsendtocalls[i]=0;
    mctotalbytesrecv[i]=0;
    mctotalbytessent[i]=0;
    mcrecvfromcalls[i]=0;
    mcsendtocalls[i]=0;
  }
}

void printstats(){
printf ("\n");


/*print out debug information*/
printf("number of uc data bytes received = %d\n", uctotalbytesrecv[data]);
printf("number of uc data recvfromcalls = %d\n", ucrecvfromcalls[data]);
printf("number of mc data bytes sent = %d\n", mctotalbytessent[data]);
printf("number of mc data sendtocalls = %d\n", mcsendtocalls[data]);
printf("--------------------------------\n");
printf("number of uc rtcp bytes received = %d\n", uctotalbytesrecv[rtcp]);
printf("number of uc rtcp recvfromcalls = %d\n", ucrecvfromcalls[rtcp]);
printf("number of mc rtcp bytes sent = %d\n", mctotalbytessent[rtcp]);
printf("number of mc rtcp sendtocalls = %d\n", mcsendtocalls[rtcp]);
printf("--------------------------------\n");
printf("number of mc data bytes received = %d\n", mctotalbytesrecv[data]);
printf("number of mc data recvfromcalls = %d\n", mcrecvfromcalls[data]);
printf("number of uc data bytes sent = %d\n", uctotalbytessent[data]);
printf("number of uc data sendtocalls = %d\n", ucsendtocalls[data]);
printf("--------------------------------\n");
printf("number of mc rtcp bytes received = %d\n", mctotalbytesrecv[rtcp]);
printf("number of mc rtcp recvfromcalls = %d\n", mcrecvfromcalls[rtcp]);
printf("number of uc rtcp bytes sent = %d\n", uctotalbytessent[rtcp]);
printf("number of uc rtcp sendtocalls = %d\n", ucsendtocalls[rtcp]);

}
 
int programshutdown () {
printstats();
exit(0);
}

long addr_lookup(char *s){

long res;
struct hostent *host;
struct in_addr *a;
 res = inet_addr(s);
 if( res != -1 ){
   return res;
 }
 if(host = gethostbyname(s)){
   a = (struct in_addr *)host->h_addr_list[0];
   res = a->s_addr;
   return res;
 }
 return -1;
}

int findentrymatch(uctable_t *array, struct in_addr *address)  {
int stopcond = 0;

/*figure out if address is in array*/
for (stopcond=0; stopcond<numunicastmem; stopcond++) {
  if (array[stopcond].addr.s_addr == address->s_addr) {
     return( stopcond );
  }
}//end of for
return (numunicastmem + 1);
}

int printmembers(uctable_t *array)  {
int stopcond = 0;
for (stopcond=0; stopcond<numunicastmem; stopcond++) {
         printf("%d: %s",stopcond,inet_ntoa(array[stopcond].addr));
         printf("\t%s",array[stopcond].active ? "active" : "inactive");
         printf("\t%s",array[stopcond].fixed ? "fixed" : "dynamic");
         printf("\n");
}
}

int zeroarray(uctable_t *array)  {

 bzero((char *) array, max_unicast_mem * sizeof(uctable_t));
}

int timeoutchk(uctable_t *array)  {
  int stopcond = 0;
   //printf("checking for inactive unicast members\n");
  for (stopcond=0; stopcond<numunicastmem; stopcond++) {
    /*if activityflag=0, delete member*/ 
    while((array[stopcond].active == 0) && 
	  (array[stopcond].fixed == 0) && 
	  (stopcond < numunicastmem)) {
         printf("deleting an inactive unicast member=%s\n",inet_ntoa(array[stopcond].addr));
         /* reduce count and copy down */
         numunicastmem--;
         array[stopcond] = array[numunicastmem];
	 /*
	  * The following are necessary for the case where 
	  * stopcond == numunicastmem
	  */
         bzero((char *) (array+numunicastmem),sizeof(uctable_t));
     }
    if (stopcond < numunicastmem){ // don't over index array if array full 
      array[stopcond].active = 0; // reset flag for next pass
    }
  }//end of for
}
int is_auth(u_long a){
int result=0;
struct acl *p;
  if( ! list){
    return 1;
  }
  for(p=list;p;p=p->next){
    if( (a & p->mask) == p->addr ){
      return 1;
    }
  }
  return 0;
}

void set_acl(char *file){
  FILE *in;
  char line[160],*a=NULL,*m=NULL;
  acl_t *new;
  char *s;
  int skip;
  in = fopen(file,"r");
  if( ! in ){
    printf("No %s file found, no ACL set\n",file);
    return;
  }
 printf("ACL is:\n");
 while( fgets(line,160,in) ){
   a=NULL;
   m=NULL;
   skip=0;
   for(s=line;*s;s++){
     /* remove comments */
     if( *s == '#' ){
       *s='\0';
       break;
     }
     if( *s == ' ' || *s == '\t' ){
       *s='\0';
       skip=0;
     }else{
       if( ! a ){
	 a = s;
	 skip=1;
       }else{
	 if( ! m && (skip == 0 )){
	   m=s;
	 }
       }
     }
   }

   if( a && m ){
     /* found a line with 2 strings */
     printf("%s\t%s\n",a,m);
     new = (acl_t *) malloc(sizeof(acl_t));
     if( ! new ){
       perror("malloc failed\n");
       exit(1);
     }
     new->addr=inet_addr(a);
     if( new->addr == -1 ){
       printf("bad address in acl file %s\n",a);
       exit(1);
     }
     new->mask=inet_addr(m);
     if( new->mask == -1 ){
       printf("bad mask in acl file %s\n",m);
       exit(1);
     }
     /*
      * There are no deny rules only permit so its fine to 
      * build list in reverse order
      */

     new->next=list;
     list=new;
   }
   
 }
 fclose(in);

}

void print_usage(char * name){
  printf("usage: %s [-g <multicast-group>] [-m mcast port] [-u ucast port] [-t ttl] [-a <fixed ucast peer>]\n",name);
  printf("\n\nAccess list for dynamic unicast session defined in %s file\nad address netmask pairs\n",ACLFILE);
}

#if 1
/* tdu */
void signal_handler(int signum) {
	printf( "* * QUICKBRIDGE caught signal %d\n", signum);
	exit(2);
}
#endif

main (argc, argv)
int argc;
char **argv;


{
  /*define variables*/
  int has_fixed=0;
  int ucrecvfd[nchan];    //unicast receive sockets
  int mcrecvfd[nchan];    //multicast receive socket
  int sendfd;    //local send socket
  u_char ttl;
  struct sockaddr_in ucrecvaddr[nchan];
  struct sockaddr_in mcaddr[nchan];
  struct sockaddr_in ucsendaddr[nchan];
  struct sockaddr_in localsendaddr;
  struct sockaddr_in sourceaddr;
  struct ip_mreq mcreq;
  int sourceaddrlen;
  char recvbuf[MSGBUFSIZE];
  int mcport[nchan];
  int ucport[nchan];
  u_long multicastaddress;
  u_long remoteunicastaddress;

  int i;
  int do_send;
  int stopcond = 0;
  int arrayindex = 0;
  fd_set readfds;
  int maxfds;
  int nfds;
  int nr;
  int ns;
  int chksrc;
  char myhostname[MAXHOSTNAMELEN];
  char *myhostnameipaddress;
  struct hostent  *host;
  int debugon = 0;
  char addressreadbuf[16];
  uctable_t *ucmemarray=NULL;
  int group_member=0;     /* are we a member of the multicast group */
  int foundindex;
  int n2;
  int timeoutsecs = TIMEOUTSECS;
  char input;
  char inputbuf[32];
  int timerstatus;
  struct itimerval timerval, chktimerval;
  struct timeval tv;
  char *progname;
  char *tmp;
  int c, arg_err=0;


  /* don't want this as a command line flag as we want the array in place
   * before processing flags (the -a flag uses it 
   */
  if( tmp = getenv("MAX_UNICAST_MEM")){
    i = atoi(tmp);
    if( i > 0 ){
      max_unicast_mem = i;
    }
  }
  printf("max_unicast_mem is %d\n",max_unicast_mem);
  ucmemarray = calloc(sizeof(uctable_t),max_unicast_mem);
  if( ! ucmemarray ){
    perror("unicast table malloc failed");
    exit(1);
  }
  /*zero out ucmemarray*/
  zeroarray(ucmemarray);


  zero_stats();

  progname=argv[0];
  /* default values */
  ttl = 1;
  mcport[data]=0;
  ucport[data]=0;
  mcport[rtcp]=0;
  ucport[rtcp]=0;
  multicastaddress = -1;
 
  while((c = getopt(argc,argv,"g:t:u:m:a:d:")) != EOF){
    switch(c) {
    case 'g':
      multicastaddress = addr_lookup(optarg);
      break;
    case 'm':
      if (atoi(optarg) % 2 == 0) {
	mcport[data] = atoi(optarg);
	mcport[rtcp] = atoi(optarg) + 1;
      } else {
	mcport[data] = atoi(optarg) - 1;
	mcport[rtcp] = atoi(optarg);
      }
      break;
    case 'u':
      if (atoi(optarg) % 2 == 0) {
	ucport[data] = atoi(optarg);
	ucport[rtcp] = atoi(optarg) + 1;
      } else {
	ucport[data] = atoi(optarg) - 1;
	ucport[rtcp] = atoi(optarg);
      }
      break;
    case 't':
      ttl = atoi(optarg);
      break;
    case 'd':
      debugon = atoi(optarg);
      break;

    case 'a':
      has_fixed=1;
      remoteunicastaddress = addr_lookup(optarg);
      if( remoteunicastaddress == -1 ){
	printf("Bad remote unicast address\n");
	exit(1);
      }
      /* now insert into list */
      if (numunicastmem < max_unicast_mem){
	ucmemarray[numunicastmem].addr.s_addr = remoteunicastaddress;
	ucmemarray[numunicastmem].active = 0;
	ucmemarray[numunicastmem].fixed = 1;
	numunicastmem++;
      }else{
	printf("Too many fixed addresses\n");
	exit(1);
      }
      break;
    default:
      printf("Unknown flag %c\n",c);
      arg_err=1;
      break;
    }

  }
  /* check values */
  if( multicastaddress == -1 ){
    printf("Bad multicast address\n");
    arg_err=1;
  }
  if( mcport[data] == 0 ){
    printf("Bad multicast port\n");
    arg_err=1;
  }
  if( ucport[data] == 0 ){
    printf("Bad unicast port\n");
    arg_err=1;
  }
  if( ttl < 1 ){
    printf("Bad TTL value\n");
    arg_err=1;
  }
  if( max_unicast_mem < 1 ){
    printf("Bad TTL value\n");
    arg_err=1;
  }
  if( arg_err ){
    print_usage(progname);
    exit(1);
  }



  printf("ucport[data]=%d  ",ucport[data]);
  printf("ucport[rtcp]=%d\n",ucport[rtcp]);
  printf("mcport[data]=%d  ",mcport[data]);
  printf("mcport[rtcp]=%d\n",mcport[rtcp]);
 
  //printf("multicastaddress=%d\n",multicastaddress);

  for(i=0;i<nchan;i++){
    /*enter the address/port data into the ucrecvaddr[i] structure*/
    bzero((char *) &ucrecvaddr[i], sizeof(ucrecvaddr[i]));
    ucrecvaddr[i].sin_family = AF_INET;
    ucrecvaddr[i].sin_addr.s_addr = htonl(INADDR_ANY);
    ucrecvaddr[i].sin_port = htons(ucport[i]);

    /*enter the address/port data into the ucsendaddr[i] structure*/
    bzero((char *) &ucsendaddr[i], sizeof(ucsendaddr[i]));
    ucsendaddr[i].sin_family = AF_INET;
    ucsendaddr[i].sin_addr.s_addr = remoteunicastaddress;
    ucsendaddr[i].sin_port = htons(ucport[i]);

    /*enter the address/port data into the mcaddr[data] structure*/
    bzero((char *) &mcaddr[i], sizeof(mcaddr[i]));
    mcaddr[i].sin_family=AF_INET;
    mcaddr[i].sin_addr.s_addr = multicastaddress;
    mcaddr[i].sin_port = htons(mcport[i]);

  }

  /*figure out the hostname and get a local ip address*/
  if (gethostname(myhostname, MAXHOSTNAMELEN) < 0){
    perror("gethostname error");
    exit(1);
  }
  printf("myhostname=%s\n", myhostname);
  
  if((host = gethostbyname(myhostname)) == NULL){
    perror("gethostbyname failure!");
    exit(1);
  }
  myhostnameipaddress = (char *) inet_ntoa(*((struct in_addr *)host->h_addr_list[0]));
  printf("myhostipaddress=%s\n\n", myhostnameipaddress);

  /*enter the address/port data into the localsendaddr structure*/
  bzero((char *) &localsendaddr, sizeof(localsendaddr));
  localsendaddr.sin_family=AF_INET;
  localsendaddr.sin_addr.s_addr = inet_addr(myhostnameipaddress);
  localsendaddr.sin_port = htons(0);
  //printf("localsendaddr=%s\n",inet_ntoa(localsendaddr.sin_addr));

  /*enter the address/port data into the mcreq structure*/
  bzero((char *) &mcreq, sizeof(mcreq));
  mcreq.imr_multiaddr.s_addr=multicastaddress;
  mcreq.imr_interface.s_addr=htonl(INADDR_ANY);

  /*get the ucrecvfd[data] socket, bind to address*/
  if ((ucrecvfd[data] = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("can't open ucrecvfd[data] socket!");
    exit (1);
  }
  if (bind(ucrecvfd[data], (struct sockaddr *) &ucrecvaddr[data], \
	   sizeof(ucrecvaddr[data])) < 0) {
    perror("can't bind ucrecvaddr[data] to socket!");
    exit(1);
  }

  /*get the sendfd socket*/
  if ((sendfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("can't open sendfd socket!");
    exit (1);
  }
  if (bind(sendfd, (struct sockaddr *) &localsendaddr, \
	   sizeof(localsendaddr)) < 0) {
    perror("can't bind localsendaddr to socket!");
    exit(1);
  }

  /*get the ucrecvfd[rtcp] socket, bind to address*/
  if ((ucrecvfd[rtcp] = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("can't open ucrecvfd[rtcp] socket!");
    exit (1);
  }
  if (bind(ucrecvfd[rtcp], (struct sockaddr *) &ucrecvaddr[rtcp], \
	   sizeof(ucrecvaddr[rtcp])) < 0) {
    perror("can't bind ucrecvaddr[rtcp] to socket!");
    exit(1);
  }

  /*get a mcrecvfd[data] socket, bind to address */
  if ((mcrecvfd[data] = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("can't open mcrecvfd[data] socket!");
    exit(1);
  }
  if (bind(mcrecvfd[data], (struct sockaddr *) &mcaddr[data], \
	   sizeof(mcaddr[data])) < 0) {
    perror("can't bind mcaddr[data] to socket!");
    exit(1);
  }

  /*get a mcrecvfd[rtcp] socket, bind to address */
  if ((mcrecvfd[rtcp] = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("can't open mcrecvfd[rtcp] socket!");
    exit(1);
  }
  if (bind(mcrecvfd[rtcp], (struct sockaddr *) &mcaddr[rtcp], \
	   sizeof(mcaddr[rtcp])) < 0) {
    perror("can't bind mcaddr[rtcp] to socket!");
    exit(1);
  }


  /*now set multicast socket TTL option*/
  /*setsocketopt (int filedescriptor, int level, in optname),*/
  /*charpointer optvalue, intpointer optlen)*/
  if (setsockopt(sendfd, IPPROTO_IP, IP_MULTICAST_TTL, \
		 &ttl, sizeof(ttl)) < 0){
    perror("can't set multicast ttl socket option!");
    exit(1);
  }

  
  if( has_fixed ){
    printf("joining multicast group\n");
    /*set socket options to join multicast group*/
    /*setsockopt (int filedescriptor, int level, int optname,*/  
    /*            charpointer optvalue, intpointer optlen)*/
    if (setsockopt(mcrecvfd[data], IPPROTO_IP, IP_ADD_MEMBERSHIP, &mcreq,\
		   sizeof(mcreq)) < 0) {
      perror("can't set socket options to join multicast group!");
      exit(1);
    } 
    if (setsockopt(mcrecvfd[rtcp], IPPROTO_IP, IP_ADD_MEMBERSHIP, &mcreq,\
		   sizeof(mcreq)) < 0) {
      perror("can't set socket options to join multicast group!");
      exit(1);
    } 
    group_member=1;
  }

  /* code for gateway mode */
  set_acl(ACLFILE);
  /*set up timer timeout values, call setitimer*/
  /*set interval to 0, will not restart timer as part of timeout processing*/
  timerval.it_interval.tv_sec = 0; 
  timerval.it_interval.tv_usec = 0; 
  timerval.it_value.tv_sec = timeoutsecs; 
  timerval.it_value.tv_usec = 0; 

  signal(SIGALRM,SIG_IGN);
#if 1
  signal(SIGINT,signal_handler); /* tdu */
#endif

  timerstatus = setitimer(ITIMER_REAL, &timerval, (struct itimerval *)0);
 

  /*start infinite while loop*/
  /*and check for activity on sockets*/

  /*set up the select sytem call parameters*/  
  /*zero out the readfds and writefds lists, then add*/
  /*the file descriptors of interest*/
 
  /* maxfds should be one more than largest fd */
  maxfds = 0;
  if(ucrecvfd[data]>maxfds) maxfds = ucrecvfd[data];
  if(mcrecvfd[data]>maxfds) maxfds = mcrecvfd[data];
  if(ucrecvfd[rtcp]>maxfds) maxfds = ucrecvfd[rtcp];
  if(mcrecvfd[rtcp]>maxfds) maxfds = mcrecvfd[rtcp];
  maxfds++;


  while(1) { 
    FD_ZERO(&readfds);
    FD_SET(ucrecvfd[data], &readfds);
    FD_SET(mcrecvfd[data], &readfds);
    FD_SET(ucrecvfd[rtcp], &readfds);
    FD_SET(mcrecvfd[rtcp], &readfds);
    if (debugon >= 1) {
      FD_SET(0, &readfds);
    }

    /*check for activity and processor accordingly*/
    /*
     * We add a timeout when there are active unicast sessions so that we
     * can detect when the last client leaves. Without this we would 
     * need a multicast packet to come in and trigger clearup.
     * some OS will change the timerval struct so make a new one each time.
     * If we have fixed sessions the list will never be empty so block.
     */
    if( numunicastmem > 0 && ! has_fixed){
      tv.tv_sec = timeoutsecs; 
      tv.tv_usec = 0; 
      nfds = select(maxfds, &readfds, NULL, NULL, &tv);
    }else{
      nfds = select(maxfds, &readfds, NULL, NULL, NULL);
    }

    if (!strcmp(inputbuf,"pa")) {
      printf("unicast members array output:\n");
      printmembers(ucmemarray);
    } 

    /*if specified on the command line, check for input on stdin*/
    if (debugon >= 1) {
      if (FD_ISSET(0, &readfds)) {
	n2 = read(0,inputbuf, sizeof(inputbuf));
	//printf("inputbuf=%s\n",inputbuf);
	inputbuf[n2>0? n2-1: 0] = '\0';
	//input = inputbuf[data]; 
	//printf("stdin input!=%d\n",input);
	if (!strcmp(inputbuf,"p")) {
	  printf("current unicast members:\n");
	  printmembers(ucmemarray);
	} 
	if (!strcmp(inputbuf,"s")) {
	  printstats();
	} 
	if (!strcmp(inputbuf,"z")) {
	  zero_stats();
	} 
	if (!strcmp(inputbuf,"q")) {
	  programshutdown();
	} 
	//fflush(stdin); 
	//fflush(stdout); 
      }
      fflush(stdout); 
    }


    /*1:receive from unicast, send on multicast and other unicast participants */ 
    for(i=0;i<nchan;i++){
      do_send=1;
      if (FD_ISSET(ucrecvfd[i], &readfds)) {
	//printf("\nready to receive data on ucrecvfd[%d]!\n",i);
	nr = recvfrom(ucrecvfd[i], recvbuf, MSGBUFSIZE, 0, (struct sockaddr *) \
		      &sourceaddr, &sourceaddrlen);
	if (debugon >= 2) {
	  printf("\nreading from ucrecvfd[%d], got data from %s\n", i,inet_ntoa(sourceaddr.sin_addr));
	}
	if( debugon > 0 ){
	  ucrecvfromcalls[i] = ucrecvfromcalls[i] + 1;
	  uctotalbytesrecv[i] = uctotalbytesrecv[i] + nr;
	}

	if (nr < 0){
	  perror("ucrecvfd[i]:recvfrom over unicast address error!(1)\n");
	  do_send=0;
	}else{
	  /*send to all unicast (execpt the one it came from)*/ 
	  /*first figure out if sourceaddress is in ucmemarray*/
	  /*if sourceaddress if local host address, do not update the ucmemarray*/
	  if (sourceaddr.sin_addr.s_addr != localsendaddr.sin_addr.s_addr) {
	    foundindex = findentrymatch(ucmemarray, &sourceaddr.sin_addr);
	    //printf("sourceaddr=%d\n",sourceaddr.sin_addr.s_addr);
	    //printf("foundindex=%d\n",foundindex);
	    if (foundindex < numunicastmem) {
	      //printf("found address at ucmemarray[%d]\n",foundindex);
	      /*update activity flag*/ 
	      ucmemarray[foundindex].active = 1; 
	    } else {
	      if (debugon >= 2) printf("did not find address in ucmemarray\n");
	      /*add entry to array*/
	      if ((numunicastmem < max_unicast_mem) && 
		  is_auth(sourceaddr.sin_addr.s_addr)) {
		ucmemarray[numunicastmem].addr.s_addr = sourceaddr.sin_addr.s_addr;
		ucmemarray[numunicastmem].active = 1;
		ucmemarray[numunicastmem].fixed = 0; 
		numunicastmem++;
		printf("\nadding an entry, unicast members are now:\n");
		printmembers(ucmemarray);
		if( ! group_member ){
		  printf("joining multicast group\n");
		  /*set socket options to join multicast group*/
		  /*setsockopt (int filedescriptor, int level, int optname,*/  
		  /*            charpointer optvalue, intpointer optlen)*/
		  if (setsockopt(mcrecvfd[data], IPPROTO_IP, IP_ADD_MEMBERSHIP, &mcreq,\
				 sizeof(mcreq)) < 0) {
		    perror("can't set socket options to join multicast group!");
		    exit(1);
		  } 
		  if (setsockopt(mcrecvfd[rtcp], IPPROTO_IP, IP_ADD_MEMBERSHIP, &mcreq,\
				 sizeof(mcreq)) < 0) {
		    perror("can't set socket options to join multicast group!");
		    exit(1);
		  } 
		  group_member=1;
		}else{
		  printf("already in multicast group\n");
		}
	      } else {
		if(debugon >= 1 ){
		  printf("Not auth or too many unicast members, can't add another!\n");
		}
		do_send=0;
	      }
	    }//end of else
	  } //end of updating ucmemarray values

	  /*now step thru array and send to all unicast members, except current source*/
	  if( do_send ){
	    for (stopcond=0; stopcond<numunicastmem; stopcond++) {
	      remoteunicastaddress = ucmemarray[stopcond].addr.s_addr;
	      if (remoteunicastaddress != sourceaddr.sin_addr.s_addr ) {
		ucsendaddr[i].sin_addr.s_addr = remoteunicastaddress;
		if (debugon >= 2) printf("sending to %s\n", inet_ntoa(ucmemarray[stopcond].addr));
		ns = sendto(sendfd, recvbuf, nr, 0, (struct sockaddr *)&ucsendaddr[i], \
			    sizeof(ucsendaddr[i]));
	      } else {
		if (debugon >= 4) printf("not resending to ORIGINATOR! or array entry = 0\n"); 
	      }
	    }//end of for (stopcond=0;....


	    /*sent to the multicast group*/
	    if (debugon >= 2) printf("sending to %s\n", inet_ntoa(mcaddr[i].sin_addr));
	    ns = sendto(sendfd, recvbuf, nr, 0, (struct sockaddr *)&mcaddr[i], \
			sizeof(mcaddr[i]));
	    if( debugon > 0 ){
	      mcsendtocalls[i] = mcsendtocalls[i] + 1;
	      mctotalbytessent[i] = mctotalbytessent[i] + ns;
	    }
	    if (ns < 0)
	      perror("sendfd:sendto over multicast address error!(2)\n");
	  } /* do send */
	} /* recv failed */
      } /* FD_ISSET */
    } /* nchan loop */


    /*3:receive from multicast, send on unicast to all unicast participants */ 
    for(i=0;i<nchan;i++){
      if (FD_ISSET(mcrecvfd[i], &readfds)) {
	//printf("ready to receive data on mcrecvfd[%d]!\n",i);
	nr = recvfrom(mcrecvfd[i], recvbuf, MSGBUFSIZE, 0, (struct sockaddr *) \
		      &sourceaddr, &sourceaddrlen);
	if (nr < 0){
	  printf ("mcrecvfd[%d]:recvfrom over multicast address error!(5)\n",i);
	}else{
	  if (debugon >= 2)  {
	    printf("\nreading from mcrecvfd[%d], got data from=%s\n",i,inet_ntoa(sourceaddr.sin_addr));
	    printf("localsendaddr=%s\n",inet_ntoa(localsendaddr.sin_addr));
	  }
	  if (sourceaddr.sin_addr.s_addr == localsendaddr.sin_addr.s_addr){
	    chksrc = 0;
	    if (debugon >= 2) 
	      printf("don't retransmit multicast sourced from gateway machine\n");
	  } else {
	    chksrc = 1;
	    if (debugon >= 2) 
	      printf("retransmit to unicast addresses\n");
	  }
	  //printf("chksrc=%d\n", chksrc);

	  if (chksrc != 0 ) {
	    if( debugon > 0 ){
	      mcrecvfromcalls[i] = mcrecvfromcalls[i] + 1;
	      mctotalbytesrecv[i] = mctotalbytesrecv[i] + nr;
	    }

	    /*now step thru array and send to all unicast members*/
	    for (stopcond=0; stopcond<numunicastmem; stopcond++) {
	      if(ucmemarray[stopcond].addr.s_addr  == sourceaddr.sin_addr.s_addr){
		printf("ERROR detected multicast packet from a unicst peer\n");
		printf("possible feedback configuration\n");
		/*exit(2);*/
		printf("* * offending unicast member will be dropped");
	        /* drop offending unicast member
		 * - set unicast member state to inactive
		 * - force timeoutchk, so offending unicast member will be dropped                 
		 */
	        ucmemarray[stopcond].active = 0;
		timeoutchk(ucmemarray);
	        
	      }

	      remoteunicastaddress = ucmemarray[stopcond].addr.s_addr;
	      ucsendaddr[i].sin_addr.s_addr = remoteunicastaddress;
	      if (debugon >= 2) printf("sending to %s\n", inet_ntoa(ucmemarray[stopcond].addr));
	      ns = sendto(sendfd, recvbuf, nr, 0, (struct sockaddr *)&ucsendaddr[i], \
			  sizeof(ucsendaddr[i]));
	      if( debugon > 0 ) {
		ucsendtocalls[i] = ucsendtocalls[i] + 1;
		uctotalbytessent[i] = uctotalbytessent[i] + 1;
	      }
	    }//end of for (stopcond=0;....
	  }//end of if (chksrc == 0)
	}// end of if *nr < 0 )
      }
    }

    /*5:check for unicast members in array, that may have timed out*/
    /*first see i timer has expired*/
    getitimer(ITIMER_REAL, &chktimerval);
    timerstatus = chktimerval.it_value.tv_sec;
    if (timerstatus  == 0) {
      printf("\ntime to check to see if any unicast members are inactive\n");
      timeoutchk(ucmemarray);
      /*reset timer*/
      timerval.it_value.tv_sec = timeoutsecs;;
      timerstatus = setitimer(ITIMER_REAL, &timerval, (struct itimerval *)0);
      getitimer(ITIMER_REAL, &chktimerval);
      timerstatus = chktimerval.it_value.tv_sec;
      printf("just reset the timer to %d sec\n",timerstatus);
      printf("current unicast members are now:\n");
      printmembers(ucmemarray);
      if( numunicastmem == 0 && group_member ){
	printf("leaving multicast group\n");
	if (setsockopt(mcrecvfd[data], IPPROTO_IP, IP_DROP_MEMBERSHIP, &mcreq,\
		       sizeof(mcreq)) < 0) {
	  perror("can't set socket options to leave multicast group!");
	  exit(1);
	} 
	if (setsockopt(mcrecvfd[rtcp], IPPROTO_IP, IP_DROP_MEMBERSHIP, &mcreq,\
		       sizeof(mcreq)) < 0) {
	  perror("can't set socket options to leave multicast group!");
	  exit(1);
	} 
	group_member=0;
      }
    } 

  } //end of while loop
} //end of main







