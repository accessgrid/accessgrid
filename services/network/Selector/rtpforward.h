
struct participant {
  unsigned long ssrc;
  char* name;
};

struct address{
  char* fromAddr;
  int fport;
  char* toAddr;
  int tport;
};

int
GetParticipants(struct participant*);

void
SetAllowedParticipant(unsigned long allowedParticipant);

//void start(char* fromAddr, int fport, char* toAddr, int tport);
void* start(void* address);
