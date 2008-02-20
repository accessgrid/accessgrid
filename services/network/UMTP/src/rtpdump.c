#include "config_unix.h"
#include "config_win32.h"
#include "memory.h"
#include "debug.h"
#include "net_udp.h"
#include "crypt_random.h"
#include "rijndael-api-fst.h"
#include "drand48.h"
#include "gettimeofday.h"
#include "qfDES.h"
#include "md5.h"
#include "ntp.h"
#include "rtp.h"

#include "rtpdump.h"

/*
* Write a header to the current output file.
* The header consists of an identifying string, followed
* by a binary structure.
*/
int RD_write_header(FILE *out, struct in_addr *address, int port, 
		    struct timeval start)
{
  RD_hdr_t hdr;

  fprintf(out, "#!rtpplay%s %s/%d\n", RTPDUMP_VERSION, 
	  inet_ntoa(*address), port);
  hdr.start.tv_sec  = htonl(start.tv_sec);
  hdr.start.tv_usec = htonl(start.tv_usec);
  hdr.source = address->s_addr;
  hdr.port   = htons(port);
  if (fwrite((char *)&hdr, sizeof(hdr), 1, out) < 1) {
    perror("fwrite");
    return -1;
  } 

  return 0;
} /* rtpdump_header */


/*
 * Read header. Return -1 if not valid, 0 if ok.
 */
int RD_read_header(FILE *in, struct in_addr *address, int *port, 
		   struct timeval *start)
{
  RD_hdr_t hdr;
  char line[80], magic[80];

  if (fgets(line, sizeof(line), in) == NULL) return -1;
  sprintf(magic, "#!rtpplay%s ", RTPDUMP_VERSION);
  if (strncmp(line, magic, strlen(magic)) != 0) return -1;

  if (fread((char *)&hdr, sizeof(hdr), 1, in) == 0) return -1;

  start->tv_sec  = ntohl(hdr.start.tv_sec);
  start->tv_usec = ntohl(hdr.start.tv_usec);
  address->s_addr   = ntohl(hdr.source);
  *port              = ntohs(hdr.port);

  return 0;
} /* RD_header */

/*
 * Write next record to output file.
 */
int RD_write(FILE *out, RD_buffer_t *b)
{
  /* write packet header to file */
  if (fwrite((char *)b->byte, sizeof(b->p.hdr), 1, out) == 0) {
    /* we are done */
    return 0;
  }

  /* convert to network byte order */
  b->p.hdr.length = htons(b->p.hdr.length) - sizeof(b->p.hdr);
  b->p.hdr.offset = htonl(b->p.hdr.offset);
  b->p.hdr.plen   = htons(b->p.hdr.plen);

  /* write actual packet */
  if (fwrite(b->p.data, b->p.hdr.length, 1, out) == 0) {
    perror("fwrite body");
  } 

  return(b->p.hdr.length);
}

/*
 * Read next record from input file.
 */
int RD_read(FILE *in, RD_buffer_t *b)
{
  /* read packet header from file */
  if (fread((char *)b->byte, sizeof(b->p.hdr), 1, in) == 0) {
    /* we are done */
    return 0;
  }

  /* convert to host byte order */
  b->p.hdr.length = ntohs(b->p.hdr.length) - sizeof(b->p.hdr);
  b->p.hdr.offset = ntohl(b->p.hdr.offset);
  b->p.hdr.plen   = ntohs(b->p.hdr.plen);

  /* read actual packet */
  if (fread(b->p.data, b->p.hdr.length, 1, in) == 0) {
    perror("fread body");
  } 
  return b->p.hdr.length; 
} /* RD_read */

void
RD_read_pt_map(char *pt_map_file_name, RD_payload_t pt_map[256])
{
  FILE *f;
  int pt, r, c, i;
  char encoding [4];

  /* Initialize the table */
  for (i = 0; i < RD_NUMBER_OF_PAYLOAD_TYPES; i++) {
    pt_map[i].encoding   = xstrdup("????");
    pt_map[i].rate       = 0;
    pt_map[i].period     = 0.0;
    pt_map[i].channels   = 0;
  }
  
  if(pt_map_file_name != NULL) {
    if (!(f = fopen(pt_map_file_name, "r"))) {
      perror(pt_map_file_name);
      exit(1);
    }
    
    while (fscanf(f, "%d %s %d %d", &pt, encoding, &r, &c) != EOF) {
      if (pt >= 0 && pt < 128 && r > 0 && r < 100000) {
	pt_map[pt].encoding = xstrdup(encoding);
	pt_map[pt].rate = r;
	pt_map[pt].period = 1/(double)r;
	pt_map[pt].channels = c;
      } else {
	fprintf(stderr, "PT=%d or rate=%d is invalid.\n", pt, r);
      }
    }
    
    fclose(f);
  }
}

