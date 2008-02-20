/*
* rtpdump file format
*
* The file starts with the tool to be used for playing this file,
* the multicast/unicast receive address and the port.
*
* #!rtpplay1.0 224.2.0.1/3456\n
*
* This is followed by one binary header (RD_hdr_t) and one RD_packet_t
* structure for each received packet.  All fields are in network byte
* order.  We don't need the source IP address since we can do mapping
* based on SSRC.  This saves (a little) space, avoids non-IPv4
* problems and privacy/security concerns. The header is followed by
* the RTP/RTCP header and (optionally) the actual payload.
*/

#define RTPDUMP_VERSION "1.0"
#define RD_MAX_FORMAT_LENGTH 16
#define RD_NUMBER_OF_PAYLOAD_TYPES  128

typedef struct {
	char *encoding;     /* Encoding name      */
	int rate;           /* Sample rate        */
	double period;      /* Timestamp period   */
	int channels;       /* Number of channels */
} RD_payload_t;

RD_payload_t pt_map[RD_NUMBER_OF_PAYLOAD_TYPES];

typedef struct {
	struct timeval start;  /* start of recording (GMT) */
	uint32_t source;        /* network source (multicast address) */
	uint16_t port;          /* UDP port */
} RD_hdr_t;

typedef struct {
	uint16_t length;    /* length of packet, including this header (may 
						be smaller than plen if not whole packet recorded) */
	uint16_t plen;      /* actual header+payload length for RTP, 0 for RTCP */
	uint32_t offset;    /* milliseconds since the start of recording */
} RD_packet_t;

typedef union {
	struct {
		RD_packet_t hdr;
		char data[8000];
	} p;
	char byte[8192];
} RD_buffer_t;

typedef enum {
	F_invalid = 0,
	F_dump = 1,
	F_header = 2,
	F_hex = 3,
	F_rtcp = 4,
	F_short = 5,
	F_payload = 6,
	F_ascii = 7,
} RD_format_type;

typedef struct RD_format {
	const char *name;
	RD_format_type format;
} RD_format;

RD_format RD_formats[] = {
	{ "dump",    F_dump     },
	{ "header",  F_header   },
	{ "hex",     F_hex      },
	{ "rtcp",    F_rtcp     },
	{ "short",   F_short    },
	{ "payload", F_payload  },
	{ "ascii",   F_ascii    },
};

void RD_read_pt_map(char *pt_map_file_name, RD_payload_t pt_map[256]);

int RD_write_header(FILE *in, struct in_addr *address, int port, 
struct timeval start);
int RD_write(FILE *out, RD_buffer_t *b);
int RD_read_header(FILE *in, struct in_addr *address, int *port, 
struct timeval *start);
int RD_read(FILE *in, RD_buffer_t *b);
