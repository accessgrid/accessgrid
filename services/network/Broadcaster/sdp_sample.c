/*****************************************************************************
*
* Name: John Winans
*
* Modified: Justin Binns
*
* Class: CS480
*
* Assignment 3
*
* SIMPLE WEB SERVER
*
* This web server intercepts all hits to the URL  /status  and processes them
* internally by sending a status report of the web server.
*
* REVISION:
* This web server intercepts all hits to the URL '/status' and processes them
* internally by sending a status report to the client.  It also processes all
* other valid GET and/or HEAD requests, providing the file specified on the
* URL.
*
* Usage:  <prog> -r <sdp file> [-d <debug level>]
*
*  -r	SDP file to serve in response to *ANY* get request
*
*  -d   Specify that debug statements should be printed.  The "debug level"
*               specifies the level of detail in the reporting, from 0
*               (no debug - same as not specifying the option) to 9 (most 
*               detailed).
*
*****************************************************************************/

#include <sys/types.h>
#include <sys/uio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <sys/resource.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdarg.h>
#include <limits.h>
#include <errno.h>
#include <signal.h>
#include <regex.h>

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

#define MY_SERVER_PORT		0	/* Set this for a static port number */

/*****************************************************************************
*
* SIMPLE WEB SERVER
*
*****************************************************************************/

int main(int argc, char **argv)
{
	int			sock;
	int			length;
	struct sockaddr_in	server;
	int 			chid;
	int			stat;
	int			c;

	/* The following are for getopt(3C) */
	extern char		*optarg;
	extern int		optind;
	extern int		opterr;
	extern int		optopt;

	startTime=time(NULL);
	
	while ((c = getopt(argc, argv, "d:f:r:t:")) != EOF)
	{
		switch (c) 
		{
		case 'd':
			debugFlag = atoi(optarg);
			break;
		case 'r':
			documentRoot = optarg;
			break;
		}
	}
	if(timeOutVal == 0) timeOutVal = 20;

	/* Make sure that we have a document root directory, or gripe & croak */
	if (documentRoot == NULL)
	{
		fprintf(stderr, "Usage: %s -r <document root> [-d <debug level>]\n", argv[0]);
		fprintf(stderr, "          [-f <type file>] [-t <timeout delay>]\n");
		exit(2);
	}

	debug(1,"Debugging enabled, Level: %d\n",debugFlag);

	/* Create socket to listen on */
	sock = socket(AF_INET, SOCK_STREAM, 0);
	if (sock < 0) 
	{
		perror("opening stream socket");
		exit(1);
	}
	
	debug(4,"File Discriptor for Socket: %d\n",sock);
	
	/* Name socket */
	server.sin_family = AF_INET;			/* Use Internet TCP/IP protocols */
	server.sin_addr.s_addr = INADDR_ANY;	/* Use any attached addresses. */
	server.sin_port = htons(MY_SERVER_PORT);

	/* bind() tells the O/S to map the above server values to the socket */
	if (bind(sock, (struct sockaddr *)&server, sizeof(server))) 
	{
		perror("binding stream socket");
		exit(1);
	}

	/* Find out assigned port number and print it out */
	length = sizeof(server);
	if (getsockname(sock, (struct sockaddr *)&server, &length)) 
	{
		perror("getting socket name");
		exit(1);
	}
	fprintf(stderr, "Socket has port #%d\n", ntohs(server.sin_port));

	/* Tell the O/S that we are willing to accept connections */
	listen(sock, 5);
	signal(SIGCHLD,sigChldHndlr);

	while(1)
	{
		/* Wait for, and accept any connections from clients */
		while(((msgsock = accept(sock, 0, 0))==(-1))&&(errno == EINTR))
		  signal(SIGCHLD,sigChldHndlr);
		debug(2,"Connection accepted.\n");
		debug(4,"File Discriptor for Accepted Socket: %d\n",msgsock);
		if (msgsock == -1)
		{
			/* Something bad happened in accept() */
			perror("accept");
		}
		else
		{
			chid=fork();
			if(chid==0){
			  signal(SIGALRM,sigAlrmHndlr);
			  signal(SIGPIPE,sigPipeHndlr);
			  debug(3,"Child starting.\n");
			  alarm(timeOutVal);
			  debug(8,"Alarm set: Time Out at %d sec.\n",timeOutVal);
			  stat = handleTransaction(msgsock);
			  alarm(0);
			  debug(8,"Alarm cancelled.\n");
			  debug(3,"Child exiting.  Exit code: %d\n",stat);
			  exit(stat);
			}
			else{
			  debug(4,"Closing msgsock (%d) in parent.\n",msgsock);
			  close(msgsock);
			}
		}
	}
	/*
	 * Since this program has an infinite loop, the socket "sock" is
	 * never explicitly closed.  However, all sockets will be closed
	 * automatically when a process is killed or terminates normally. 
	 */
}


/*****************************************************************************
*
* Handle one single socket connection request.
*
* RETURNS:
*	-1		Error handling transaction
*	1               Successfull HEAD transaction
*	2		Successfull GET transaction
*	3		Successfull BOGUS transaction (no error, but bogus)
*
*****************************************************************************/
static int handleTransaction(int sock)
{
	FILE	*fsock;

	char	buf[2048];
	char	cmd[2048];
	int	status = -1;
	char	*method;
	char	*url;
	char	*lasts;
	char	*ret;

    debug(9,"Entering handleTransaction()\n");
    
	/* Create a stream for reading AND writing */
    if ((fsock = fdopen(sock, "r+b")) == NULL)
    {
        perror("fdopen");
        return(-1);
    }
    
    debug(9,"fdopen() for msgsock successfull.\n");

	/* Read the request phase request line */
	ret = fgets(cmd, sizeof(cmd), fsock);
	if (ret != NULL)
	{	/* Got the command line of the request... grab the good stuff */

		method = strtok(cmd, " ");
		url = strtok(NULL, " ");

		if (method==NULL || url==NULL)
		{
			debug(4,"handleTransaction() got bogus request line\n");
			return(-1);
		}
		debug(5,"method: '%s', url: '%s'\n", method, url);
	}

	/* Read rest of the request phase header lines and toss them */
	ret = fgets(buf, sizeof(buf), fsock);
	while (ret!=NULL && buf[0]!='\r' && buf[0]!='\n')
	{
		debug(9,"Got input data line: '%s'\n", buf);
		ret = fgets(buf, sizeof(buf), fsock);
	}
	debug(9,"Header complete.\n");

	if (!strcmp(method, "HEAD")){
		debug(7,"HEAD processing selected.\n");
		status = sendHeader(fsock, url);
		if(!status)
		  status=1;
		else
		  status=-1;
	}
	else if (!strcmp(method, "GET")){
		debug(7,"GET processing selected.\n");
		status = reqGet(fsock, url);
		if(!status)
		  status=2;
		else
		  status=-1;
	}
	else{
		status=3;
	}

	fflush(fsock);	/* force the stream to write any buffered data */
	debug(4,"Closing msgsock (%d) in child.\n",sock);
	fclose(fsock);	/* closes the stream AND the file descriptor(socket) */
	return(status);
}

/*****************************************************************************
*
* A custom version of printf() that only prints stuff if debugFlag is 
* not zero.
*
*****************************************************************************/
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

/*****************************************************************************
*
* Handle the processing of a GET request type.
*
* file:		client socket stream 
* url:		unverified url requested in the GET request
*
*****************************************************************************/
static int reqGet(FILE *file, char *url)
{
	int	status;

	debug(9,"Entering reqGet()\n");
	
	if ((status = sendHeader(file, url)) != 0)
	{
		return(status);
	}
	debug(9,"Return from reqGet()\n");
	return(sendBody(file, url));
}

/*****************************************************************************
*
* Send the appropriate header data for the requested URL.
*
* fwsock:	client socket stream 
* url:		unverified url requested in the GET request
*
*****************************************************************************/
static int sendHeader(FILE *fwsock, char *url)
{
	fprintf(fwsock, "HTTP/1.0 200 OK\r\n");
	fprintf(fwsock, "Content-Type: application/sdp\r\n");
	fprintf(fwsock, "Connection: close\r\n");
	fprintf(fwsock, "\r\n");
	debug(9,"Return from sendHeader()\n");
	return(0);
}

/*****************************************************************************
*
* Send the body of the specified URL to the client.
* Assume that the request-phase headers have alrealy been verified as 
* valid and that the response phase headers have already been sent.
*
* fwsock:	Client socket stream 
* url:		Clean, but unverified url requested in the GET request
*
*****************************************************************************/
static int sendBody(FILE *fwsock, char *url)
{
	FILE *inFile;
	char fileBuf[4096];
	size_t numRead;
	
	char fullPath[PATH_SIZE];
	struct stat MyStat;

	debug(9,"Entering sendBody()\n");
	
	strcpy(fullPath,documentRoot);
	
	debug(5,"Final filename: %s\n",fullPath);
	
	if((inFile=fopen(fullPath,"rb"))==NULL){
	  debug(4,"Error opening file: %s\n",fullPath);
	  return(1);
	}
	
	while(!feof(inFile)){
	  numRead=fread(fileBuf,1,4096,inFile);
	  fwrite(fileBuf,1,numRead,fwsock);
	}
	
	debug(9,"Return from sendBody()\n");
	return(0);
}

/*****************************************************************************
*
* This function is the signal handler for SIGCHLD signals.  These signals
* should be recieved only by the parent process after the death of each child.
* This function wait()s for the exit code, then increments the appropriate
* counters.
*
* sigRecv:	The signal recieved - should ALWAYS be SIGCHLD.
*
******************************************************************************/
void sigChldHndlr(int sigRecv){
  int waitStatus=0;
  wait(&waitStatus);
  waitStatus=WEXITSTATUS(waitStatus);
  
  switch(waitStatus){
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
